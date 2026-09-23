"""Development-only reset for the task subsystem. Keeps users and groups intact."""
import asyncio

from app.database import engine
from app import models


TASK_TABLES = [
    models.task_group_assignment,
    models.task_student_assignment,
    models.StudentCodeSession.__table__,
    models.Grade.__table__,
    models.CodeComment.__table__,
    models.Submission.__table__,
    models.AutoCheckTask.__table__,
    models.CodeReviewTask.__table__,
    models.Task.__table__,
]


async def reset() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(lambda sync: models.Base.metadata.drop_all(sync, tables=TASK_TABLES, checkfirst=True))
        await connection.run_sync(lambda sync: models.Base.metadata.create_all(sync, tables=list(reversed(TASK_TABLES)), checkfirst=True))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reset())
