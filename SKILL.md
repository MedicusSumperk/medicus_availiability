# Medicus Server Operations Notes

Use these notes before touching the Medicus Windows server from Codex.

## Server Basics

- SSH host alias: `medicus`
- Server repo: `C:\db_bridge\medicus_availiability`
- Stable public API base: `https://medicus-api.kreli.org`
- Local API bind: `http://127.0.0.1:8000`
- Python executable on the server: `C:\python\python.exe`
- Do not assume `python` is available in `PATH`.

## Git Safety

Before switching branches on the server, always inspect the worktree:

```cmd
ssh medicus "cd /d C:\db_bridge\medicus_availiability && git status --short --branch"
```

If the server has local changes, preserve them before switching:

```cmd
ssh medicus "cd /d C:\db_bridge\medicus_availiability && git stash push -u -m server-before-branch-switch"
```

Do not restore, reset, or delete unknown local server changes unless explicitly requested.

## Reliable API Restart

Starting the FastAPI process with plain `Start-Process` inside a non-interactive SSH command may not keep the process alive after the SSH session exits. The reliable observed workaround is to start it through a one-time Windows Scheduled Task that runs a local `.cmd` file, then delete the task after the API is confirmed listening.

1. Stop the process currently bound to port `8000`:

```cmd
ssh medicus "powershell -NoProfile -Command ""$p=(Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue).OwningProcess; if ($p) { Stop-Process -Id $p -Force }"""
```

2. Create or update `logs\start_api_server.cmd` on the server:

```cmd
@echo off
cd /d C:\db_bridge\medicus_availiability
C:\python\python.exe scripts\api_server.py >> logs\api_server.stdout.log 2>> logs\api_server.stderr.log
```

3. Create and run a one-time scheduled task:

```cmd
ssh medicus "schtasks /Create /TN MedicusApiStartOnce /TR C:\db_bridge\medicus_availiability\logs\start_api_server.cmd /SC ONCE /ST 23:59 /F && schtasks /Run /TN MedicusApiStartOnce"
```

4. Verify that the API is listening and responding:

```cmd
ssh medicus "netstat -ano | findstr :8000"
curl https://medicus-api.kreli.org/health
```

5. Delete the one-time task after the API is confirmed running:

```cmd
ssh medicus "schtasks /Delete /TN MedicusApiStartOnce /F"
```

The API process should remain running after the task is deleted. If it does not, inspect:

```cmd
ssh medicus "cd /d C:\db_bridge\medicus_availiability && type logs\api_server.stderr.log"
```

## Deployment Smoke Checks

After pulling a branch and restarting the API, run:

```cmd
ssh medicus "cd /d C:\db_bridge\medicus_availiability && C:\python\python.exe -m unittest discover -s tests"
ssh medicus "cd /d C:\db_bridge\medicus_availiability && C:\python\python.exe scripts\render_business_rules.py --check"
curl https://medicus-api.kreli.org/health
```

For the production-hardening rules branch, also verify:

- `/handoff-summary` returns `ok: true`.
- `/doctor-availability` before `08:00` without `emergency=true` returns no normal slots.
- Bednar availability resolves to `doctor_id=2`.
- Afternoon options keep exact `start_time`/`technical_start_time` and include `spoken_time_label`.
