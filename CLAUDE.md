Windows Process Management

The project runs on Windows with Git Bash.

CRITICAL: Do not mix Linux and Windows process management

Do NOT use Linux process-management commands to manage Windows Python/Uvicorn processes:

pkill
kill
killall

Do NOT use:

sleep

for long-running server management when a Windows-native or Python-based approach is more appropriate.

Do NOT repeatedly start and kill Uvicorn processes without first checking whether the server is already running.

Uvicorn

When starting the development server, use the project's virtual environment:

./venv/Scripts/python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Remember that --reload creates a reloader process and may result in multiple Python processes.

Do NOT assume that every Python process is an independent server process.

Before starting Uvicorn

First check whether port 8000 is already occupied:

netstat -ano | grep ':8000'

If the server is already running and responding correctly, DO NOT start another instance.

Check:

curl -s http://localhost:8000/health

If the health endpoint responds successfully, reuse the existing server.

If port 8000 is occupied

Do not blindly execute:

taskkill /F /IM python.exe

This can terminate unrelated Python processes.

Instead:

Find the PID listening on port 8000.
Determine which process owns that PID.
Only terminate the relevant Uvicorn/Python process.
Then verify that port 8000 is free.
Start Uvicorn once.

Use Windows-native commands when terminating a specific process:

taskkill //F //PID <PID>

When using Git Bash, remember that command arguments may require Git Bash-compatible syntax.

Do not repeatedly retry

If Uvicorn starts in the background but a health check fails:

Read server.log.
Check whether port 8000 is listening.
Check the process/PID.
Inspect the actual Uvicorn error.
Fix the underlying problem.

Do NOT repeatedly:

start Uvicorn
kill Python
start Uvicorn again
kill Python again

without inspecting the server log.

Server startup troubleshooting

When starting Uvicorn for debugging, prefer running it in the foreground first:

./venv/Scripts/python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000

This makes startup errors immediately visible.

Only use background execution when it is actually necessary for automated API testing.

If background execution is required, redirect logs:

./venv/Scripts/python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &

Then inspect:

cat server.log

before attempting repeated restarts.

Health check

After starting the server, verify it with:

curl -s http://localhost:8000/health

Do not use an arbitrary long sleep followed by a health check.

If the server does not respond, inspect server.log immediately.

Important

The goal is NOT to keep restarting the server until the health check works.

The goal is:

Check whether a server already exists.
If it exists and works, reuse it.
If it exists but is broken, identify the correct process.
Stop only that process.
Start exactly one Uvicorn instance.
Verify /health.
Read logs if verification fails.

Never kill all python.exe processes just to restart the backend.