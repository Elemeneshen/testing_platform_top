import { Server } from '@hocuspocus/server'
import { Redis } from '@hocuspocus/extension-redis'
import jwt from 'jsonwebtoken'
import pg from 'pg'
import * as Y from 'yjs'

const { Pool } = pg
const port = Number(process.env.REALTIME_PORT ?? 1234)
const redisHost = process.env.REDIS_HOST ?? 'redis'
const redisPort = Number(process.env.REDIS_PORT ?? 6379)
const jwtSecret = process.env.JWT_SECRET ?? 'your-super-secret-jwt-key-change-this-in-production'
const jwtAlgorithm = process.env.JWT_ALGORITHM ?? 'HS256'
const databaseUrl = (process.env.DATABASE_URL ?? 'postgresql://postgres:postgres@postgres:5432/test_db')
  .replace('postgresql+asyncpg://', 'postgresql://')

const pool = new Pool({ connectionString: databaseUrl })
const roomPattern = /^task-(\d+)-student-(\d+)$/

const parseRoom = documentName => {
  const match = roomPattern.exec(documentName)
  if (!match) throw new Error('Invalid collaboration room')
  return { taskId: Number(match[1]), studentId: Number(match[2]) }
}

const readCookie = (headers, name) => {
  const cookie = headers.get('cookie') ?? ''
  const item = cookie.split(';').map(part => part.trim()).find(part => part.startsWith(`${name}=`))
  return item ? decodeURIComponent(item.slice(name.length + 1)) : null
}

const taskAccess = async (taskId, studentId) => {
  const { rows } = await pool.query(
    `SELECT t.created_by, t.is_visible, crt.student_mode
       FROM tasks t
       JOIN code_review_tasks crt ON crt.task_id = t.id
      WHERE t.id = $1
        AND (
          EXISTS (
            SELECT 1 FROM task_student_assignment tsa
             WHERE tsa.task_id = t.id AND tsa.student_id = $2
          )
          OR EXISTS (
            SELECT 1
              FROM task_group_assignment tga
              JOIN students s ON s.group_id = tga.group_id
             WHERE tga.task_id = t.id AND s.id = $2
          )
        )`,
    [taskId, studentId],
  )
  return rows[0] ?? null
}

const server = new Server({
  port,
  debounce: 1200,
  maxDebounce: 5000,
  extensions: [new Redis({ host: redisHost, port: redisPort })],

  async onAuthenticate(data) {
    const token = readCookie(data.requestHeaders, 'token') ?? data.token
    if (!token) throw new Error('Not authenticated')

    let user
    try {
      user = jwt.verify(token, jwtSecret, { algorithms: [jwtAlgorithm] })
    } catch {
      throw new Error('Invalid or expired session')
    }

    const { taskId, studentId } = parseRoom(data.documentName)
    const access = await taskAccess(taskId, studentId)
    if (!access) throw new Error('Task or student is not assigned')

    const userId = Number(user.sub)
    if (user.role === 'teacher') {
      if (userId !== access.created_by) throw new Error('Not authorized for this task')
    } else if (user.role === 'student') {
      if (userId !== studentId || !access.is_visible) throw new Error('Not authorized for this session')
      if (access.student_mode !== 'live') data.connection.readOnly = true
    } else {
      throw new Error('Unknown user role')
    }

    return { userId, role: user.role, taskId, studentId }
  },

  async onLoadDocument({ documentName }) {
    const { taskId, studentId } = parseRoom(documentName)
    const { rows } = await pool.query(
      `SELECT scs.source_code, scs.ydoc_state, crt.source_code AS template_code
         FROM code_review_tasks crt
         LEFT JOIN student_code_sessions scs
           ON scs.task_id = crt.task_id AND scs.student_id = $2
        WHERE crt.task_id = $1`,
      [taskId, studentId],
    )
    if (!rows[0]) throw new Error('Code review task not found')

    const document = new Y.Doc()
    if (rows[0].ydoc_state) {
      Y.applyUpdate(document, new Uint8Array(rows[0].ydoc_state))
    } else {
      document.getText('code').insert(0, rows[0].source_code ?? rows[0].template_code ?? '')
    }
    return document
  },

  async onStoreDocument({ documentName, document }) {
    const { taskId, studentId } = parseRoom(documentName)
    const sourceCode = document.getText('code').toString()
    const state = Buffer.from(Y.encodeStateAsUpdate(document))
    await pool.query(
      `INSERT INTO student_code_sessions (task_id, student_id, source_code, ydoc_state, updated_at)
       VALUES ($1, $2, $3, $4, NOW())
       ON CONFLICT (task_id, student_id)
       DO UPDATE SET source_code = EXCLUDED.source_code,
                     ydoc_state = EXCLUDED.ydoc_state,
                     updated_at = NOW()`,
      [taskId, studentId, sourceCode, state],
    )
  },
})

server.listen()
console.log(`Realtime collaboration server listening on :${port}`)

const shutdown = async () => {
  await server.destroy()
  await pool.end()
  process.exit(0)
}

process.on('SIGINT', shutdown)
process.on('SIGTERM', shutdown)
