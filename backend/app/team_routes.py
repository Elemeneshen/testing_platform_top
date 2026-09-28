from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from . import auth, models, schemas
from .database import get_session


router = APIRouter(prefix="/teams", tags=["teams"])


def team_options():
    return (
        selectinload(models.Team.members),
        selectinload(models.Team.board),
    )


def session_options():
    return (
        selectinload(models.TeamSession.group),
        selectinload(models.TeamSession.teams).selectinload(models.Team.members),
        selectinload(models.TeamSession.teams).selectinload(models.Team.board),
    )


def team_read(team: models.Team) -> schemas.TeamRead:
    return schemas.TeamRead(
        id=team.id,
        name=team.name,
        members=[schemas.TeamMemberRead(id=item.id, full_name=item.full_name, username=item.username) for item in team.members],
        board_id=team.board.id if team.board else None,
    )


def session_read(item: models.TeamSession, student_id: int | None = None) -> schemas.TeamSessionRead:
    teams = item.teams if student_id is None else [
        team for team in item.teams
        if any(member.id == student_id for member in team.members)
    ]
    return schemas.TeamSessionRead(
        id=item.id,
        group_id=item.group_id,
        group_name=item.group.name,
        title=item.title,
        description=item.description,
        is_active=item.is_active,
        created_at=item.created_at,
        teams=[team_read(team) for team in teams],
    )


async def owned_session(db: AsyncSession, session_id: int, teacher_id: int) -> models.TeamSession:
    result = await db.execute(
        select(models.TeamSession).options(*session_options()).where(
            models.TeamSession.id == session_id,
            models.TeamSession.teacher_id == teacher_id,
        )
    )
    item = result.scalars().unique().first()
    if not item:
        raise HTTPException(status_code=404, detail="Team session not found")
    return item


async def accessible_team(db: AsyncSession, team_id: int, user) -> models.Team:
    result = await db.execute(
        select(models.Team)
        .options(
            selectinload(models.Team.members),
            selectinload(models.Team.session),
            selectinload(models.Team.board).selectinload(models.KanbanBoard.columns).selectinload(models.KanbanColumn.cards).selectinload(models.KanbanCard.assignee),
            selectinload(models.Team.board).selectinload(models.KanbanBoard.columns).selectinload(models.KanbanColumn.cards).selectinload(models.KanbanCard.created_by_student),
        )
        .where(models.Team.id == team_id)
    )
    team = result.scalars().unique().first()
    allowed = team and (
        isinstance(user, models.Teacher) and team.session.teacher_id == user.id
        or isinstance(user, models.Student) and any(member.id == user.id for member in team.members)
    )
    if not allowed:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


def board_read(team: models.Team) -> schemas.KanbanBoardRead:
    return schemas.KanbanBoardRead(
        id=team.board.id,
        team_id=team.id,
        team_name=team.name,
        session_title=team.session.title,
        members=[schemas.TeamMemberRead(id=item.id, full_name=item.full_name, username=item.username) for item in team.members],
        columns=[schemas.KanbanColumnRead(
            id=column.id,
            title=column.title,
            position=column.position,
            cards=[schemas.KanbanCardRead(
                id=card.id,
                column_id=card.column_id,
                title=card.title,
                description=card.description,
                assignee_id=card.assignee_id,
                assignee_name=card.assignee.full_name if card.assignee else None,
                created_by_student_id=card.created_by_student_id,
                created_by_name=card.created_by_student.full_name if card.created_by_student else None,
                priority=card.priority,
                position=card.position,
                updated_at=card.updated_at,
            ) for card in column.cards],
        ) for column in team.board.columns],
    )


@router.get("/sessions", response_model=list[schemas.TeamSessionRead])
async def list_sessions(user=Depends(auth.get_current_user), db: AsyncSession = Depends(get_session)):
    query = select(models.TeamSession).options(*session_options()).order_by(models.TeamSession.created_at.desc())
    if isinstance(user, models.Teacher):
        query = query.where(models.TeamSession.teacher_id == user.id)
    else:
        query = query.join(models.Team).join(models.team_membership).where(
            models.team_membership.c.student_id == user.id,
            models.TeamSession.is_active.is_(True),
        )
    result = await db.execute(query)
    student_id = user.id if isinstance(user, models.Student) else None
    return [session_read(item, student_id=student_id) for item in result.scalars().unique().all()]


@router.post("/sessions", response_model=schemas.TeamSessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(payload: schemas.TeamSessionCreate, teacher: models.Teacher = Depends(auth.get_current_teacher), db: AsyncSession = Depends(get_session)):
    group = (await db.execute(select(models.StudentGroup).where(models.StudentGroup.id == payload.group_id, models.StudentGroup.teacher_id == teacher.id))).scalars().first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    item = models.TeamSession(teacher_id=teacher.id, group_id=group.id, title=payload.title.strip(), description=payload.description)
    db.add(item)
    await db.commit()
    return session_read(await owned_session(db, item.id, teacher.id))


@router.post("/sessions/{session_id}/teams", response_model=schemas.TeamRead, status_code=status.HTTP_201_CREATED)
async def create_team(session_id: int, payload: schemas.TeamCreate, teacher: models.Teacher = Depends(auth.get_current_teacher), db: AsyncSession = Depends(get_session)):
    session = await owned_session(db, session_id, teacher.id)
    member_ids = list(dict.fromkeys(payload.member_ids))
    members = []
    if member_ids:
        result = await db.execute(select(models.Student).where(models.Student.id.in_(member_ids), models.Student.group_id == session.group_id))
        members = result.scalars().all()
        if len(members) != len(member_ids):
            raise HTTPException(status_code=400, detail="Every team member must belong to the selected group")
        occupied = await db.execute(
            select(models.team_membership.c.student_id).join(models.Team).where(
                models.Team.session_id == session_id,
                models.team_membership.c.student_id.in_(member_ids),
            )
        )
        if occupied.first():
            raise HTTPException(status_code=409, detail="A student can belong to only one team in this session")
    duplicate = await db.execute(select(models.Team.id).where(models.Team.session_id == session_id, func.lower(models.Team.name) == payload.name.strip().lower()))
    if duplicate.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="A team with this name already exists")
    team = models.Team(session_id=session_id, name=payload.name.strip(), members=members)
    board = models.KanbanBoard(team=team)
    for position, title in enumerate(("Идеи", "Нужно сделать", "В работе", "Готово")):
        board.columns.append(models.KanbanColumn(title=title, position=position))
    db.add(team)
    await db.commit()
    result = await db.execute(select(models.Team).options(*team_options()).where(models.Team.id == team.id))
    return team_read(result.scalars().unique().one())


@router.patch("/{team_id}/members", response_model=schemas.TeamRead)
async def update_members(team_id: int, payload: schemas.TeamMembersUpdate, teacher: models.Teacher = Depends(auth.get_current_teacher), db: AsyncSession = Depends(get_session)):
    team = await accessible_team(db, team_id, teacher)
    member_ids = list(dict.fromkeys(payload.member_ids))
    result = await db.execute(select(models.Student).where(models.Student.id.in_(member_ids), models.Student.group_id == team.session.group_id)) if member_ids else None
    members = result.scalars().all() if result else []
    if len(members) != len(member_ids):
        raise HTTPException(status_code=400, detail="Every team member must belong to the selected group")
    if member_ids:
        occupied = await db.execute(
            select(models.team_membership.c.student_id).join(models.Team).where(
                models.Team.session_id == team.session_id,
                models.Team.id != team.id,
                models.team_membership.c.student_id.in_(member_ids),
            )
        )
        if occupied.first():
            raise HTTPException(status_code=409, detail="A student can belong to only one team in this session")
    team.members = members
    await db.commit()
    result = await db.execute(select(models.Team).options(*team_options()).where(models.Team.id == team.id))
    return team_read(result.scalars().unique().one())


@router.get("/{team_id}/board", response_model=schemas.KanbanBoardRead)
async def get_board(team_id: int, user=Depends(auth.get_current_user), db: AsyncSession = Depends(get_session)):
    return board_read(await accessible_team(db, team_id, user))


@router.post("/{team_id}/cards", response_model=schemas.KanbanCardRead, status_code=status.HTTP_201_CREATED)
async def create_card(team_id: int, payload: schemas.KanbanCardCreate, user=Depends(auth.get_current_user), db: AsyncSession = Depends(get_session)):
    team = await accessible_team(db, team_id, user)
    column = next((item for item in team.board.columns if item.id == payload.column_id), None)
    if not column:
        raise HTTPException(status_code=400, detail="Column does not belong to this board")
    if payload.assignee_id and not any(item.id == payload.assignee_id for item in team.members):
        raise HTTPException(status_code=400, detail="Assignee must be a team member")
    position = max((item.position for item in column.cards), default=-1) + 1
    creator_id = user.id if isinstance(user, models.Student) else None
    card = models.KanbanCard(column_id=column.id, title=payload.title.strip(), description=payload.description, assignee_id=payload.assignee_id, created_by_student_id=creator_id, priority=payload.priority, position=position)
    db.add(card)
    await db.commit()
    await db.refresh(card)
    assignee_name = next((item.full_name for item in team.members if item.id == card.assignee_id), None)
    creator_name = next((item.full_name for item in team.members if item.id == card.created_by_student_id), None)
    return schemas.KanbanCardRead(id=card.id, column_id=card.column_id, title=card.title, description=card.description, assignee_id=card.assignee_id, assignee_name=assignee_name, created_by_student_id=card.created_by_student_id, created_by_name=creator_name, priority=card.priority, position=card.position, updated_at=card.updated_at)


@router.patch("/{team_id}/cards/{card_id}", response_model=schemas.KanbanCardRead)
async def update_card(team_id: int, card_id: int, payload: schemas.KanbanCardUpdate, user=Depends(auth.get_current_user), db: AsyncSession = Depends(get_session)):
    team = await accessible_team(db, team_id, user)
    cards = [card for column in team.board.columns for card in column.cards]
    card = next((item for item in cards if item.id == card_id), None)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    changes = payload.model_dump(exclude_unset=True)
    if "column_id" in changes and not any(item.id == changes["column_id"] for item in team.board.columns):
        raise HTTPException(status_code=400, detail="Column does not belong to this board")
    if changes.get("assignee_id") and not any(item.id == changes["assignee_id"] for item in team.members):
        raise HTTPException(status_code=400, detail="Assignee must be a team member")
    for key, value in changes.items():
        setattr(card, key, value)
    await db.commit()
    await db.refresh(card)
    assignee_name = next((item.full_name for item in team.members if item.id == card.assignee_id), None)
    creator_name = next((item.full_name for item in team.members if item.id == card.created_by_student_id), None)
    return schemas.KanbanCardRead(id=card.id, column_id=card.column_id, title=card.title, description=card.description, assignee_id=card.assignee_id, assignee_name=assignee_name, created_by_student_id=card.created_by_student_id, created_by_name=creator_name, priority=card.priority, position=card.position, updated_at=card.updated_at)
