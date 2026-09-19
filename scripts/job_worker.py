"""Worker kolejki zadań webowego interfejsu (Etap 8, Krok 2, Faza 3).

Odpytuje tabelę `jobs` w MariaDB (wstawianą przez Symfony, patrz
web/backend/src/Controller/Api/JobController.php) i uruchamia dokładnie te
same skrypty CLI z scripts/, które dotąd uruchamiało się ręcznie
(transcribe.py, identify_speakers.py, clean_transcript.py,
init_meeting_info.py, generate_report.py) — subprocess, bez żadnej dodatkowej
logiki biznesowej. Log procesu (stdout+stderr) dopisywany jest do wiersza na
bieżąco, żeby UI mógł go pokazywać "na żywo" przez odpytywanie.

Działa jako drugi proces w tym samym kontenerze `app`, obok
`sleep infinity` (patrz docker-compose.web.yml, usługa `app`) — restart
web UI (php-fpm/nuxt) nie dotyka tego procesu, a jego ewentualna awaria nie
zabiera dostępu do kontenera przez `docker compose exec app ...`.
"""

import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

import pymysql
import pymysql.cursors

REPO_ROOT = Path(__file__).resolve().parent.parent
POLL_INTERVAL_SECONDS = 2
DB_RETRY_SECONDS = 5


def db_connect() -> pymysql.connections.Connection:
    return pymysql.connect(
        host=os.environ["SMDM_DB_HOST"],
        port=int(os.environ.get("SMDM_DB_PORT", "3306")),
        user=os.environ["SMDM_DB_USER"],
        password=os.environ["SMDM_DB_PASSWORD"],
        database=os.environ["SMDM_DB_NAME"],
        autocommit=True,
        charset="utf8mb4",
    )


def build_command(job_type: str, params: dict) -> list[str]:
    if job_type == "transcribe":
        cmd = [sys.executable, "scripts/transcribe.py", params["audio_path"]]
        if params.get("diarize") is False:
            cmd.append("--no-diarize")
        if params.get("min_speakers"):
            cmd += ["--min-speakers", str(params["min_speakers"])]
        if params.get("max_speakers"):
            cmd += ["--max-speakers", str(params["max_speakers"])]
        return cmd
    if job_type == "identify_speakers":
        return [sys.executable, "scripts/identify_speakers.py", params["transcript_path"]]
    if job_type == "clean_transcript":
        return [sys.executable, "scripts/clean_transcript.py", params["transcript_path"]]
    if job_type == "init_meeting_info":
        return [sys.executable, "scripts/init_meeting_info.py", params["transcript_path"]]
    if job_type == "generate_report":
        return [sys.executable, "scripts/generate_report.py", params["clean_transcript_path"]]
    raise ValueError(f"Nieznany typ zadania: {job_type}")


def append_log(conn: pymysql.connections.Connection, job_id: int, text: str) -> None:
    with conn.cursor() as cur:
        cur.execute("UPDATE jobs SET log = CONCAT(log, %s) WHERE id = %s", (text, job_id))


def fetch_pending(conn: pymysql.connections.Connection) -> dict | None:
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("SELECT id, type, params FROM jobs WHERE status = 'pending' ORDER BY id ASC LIMIT 1")
        return cur.fetchone()


def mark_running(conn: pymysql.connections.Connection, job_id: int) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE jobs SET status = 'running', started_at = NOW() WHERE id = %s AND status = 'pending'",
            (job_id,),
        )
        return cur.rowcount == 1


def finish(conn: pymysql.connections.Connection, job_id: int, status: str, exit_code: int | None) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE jobs SET status = %s, exit_code = %s, finished_at = NOW() WHERE id = %s",
            (status, exit_code, job_id),
        )


def run_job(conn: pymysql.connections.Connection, job: dict) -> None:
    job_id = job["id"]
    raw_params = job["params"]
    params = json.loads(raw_params) if isinstance(raw_params, (str, bytes)) else raw_params

    try:
        cmd = build_command(job["type"], params)
    except Exception as exc:
        append_log(conn, job_id, f"Błąd budowania polecenia: {exc}\n")
        finish(conn, job_id, "failed", None)
        return

    append_log(conn, job_id, f"$ {' '.join(cmd)}\n")

    try:
        process = subprocess.Popen(
            cmd,
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            append_log(conn, job_id, line)
        process.wait()
        finish(conn, job_id, "success" if process.returncode == 0 else "failed", process.returncode)
    except Exception:
        append_log(conn, job_id, "Błąd workera:\n" + traceback.format_exc())
        finish(conn, job_id, "failed", None)


def main() -> None:
    print("job_worker: start, oczekiwanie na zadania...", flush=True)
    while True:
        try:
            conn = db_connect()
            print("job_worker: połączono z bazą.", flush=True)
            while True:
                job = fetch_pending(conn)
                if job and mark_running(conn, job["id"]):
                    print(f"job_worker: uruchamiam zadanie #{job['id']} ({job['type']})", flush=True)
                    run_job(conn, job)
                    print(f"job_worker: zadanie #{job['id']} zakończone.", flush=True)
                else:
                    time.sleep(POLL_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            break
        except Exception:
            print(f"job_worker: błąd połączenia z bazą, ponawiam za {DB_RETRY_SECONDS}s:", flush=True)
            traceback.print_exc()
            time.sleep(DB_RETRY_SECONDS)


if __name__ == "__main__":
    main()
