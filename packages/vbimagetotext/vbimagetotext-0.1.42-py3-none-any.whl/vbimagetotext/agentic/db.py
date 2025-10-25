import os
import sqlite3
from contextlib import contextmanager


DEFAULT_WORKSPACE = os.path.join("workspace")
DEFAULT_DB_PATH = os.path.join(DEFAULT_WORKSPACE, "state.db")


SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS batches (
  id TEXT PRIMARY KEY,
  name TEXT,
  created_at INTEGER,
  total_items INTEGER DEFAULT 0,
  completed_items INTEGER DEFAULT 0,
  failed_items INTEGER DEFAULT 0,
  status TEXT
);

CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  batch_id TEXT,
  stage TEXT,
  input_ref TEXT,
  status TEXT,
  attempts INTEGER DEFAULT 0,
  started_at INTEGER,
  finished_at INTEGER,
  duration_ms INTEGER,
  model TEXT,
  prompt_version TEXT,
  seed INTEGER,
  error TEXT,
  FOREIGN KEY(batch_id) REFERENCES batches(id)
);

CREATE TABLE IF NOT EXISTS artifacts (
  id TEXT PRIMARY KEY,
  job_id TEXT,
  kind TEXT,
  path TEXT,
  bytes INTEGER,
  checksum TEXT,
  created_at INTEGER,
  FOREIGN KEY(job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS metrics (
  id TEXT PRIMARY KEY,
  job_id TEXT,
  input_tokens INTEGER,
  output_tokens INTEGER,
  cost_usd REAL,
  provider TEXT,
  model TEXT,
  latency_ms INTEGER,
  FOREIGN KEY(job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id TEXT,
  ts INTEGER,
  level TEXT,
  message TEXT,
  FOREIGN KEY(job_id) REFERENCES jobs(id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_batch_stage ON jobs(batch_id, stage);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_artifacts_job ON artifacts(job_id);
CREATE INDEX IF NOT EXISTS idx_metrics_job ON metrics(job_id);
"""


def ensure_workspace(path: str = DEFAULT_WORKSPACE) -> None:
    os.makedirs(path, exist_ok=True)


def init_db(db_path: str = DEFAULT_DB_PATH) -> str:
    ensure_workspace(os.path.dirname(db_path) or ".")
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
    return db_path


@contextmanager
def connect(db_path: str = DEFAULT_DB_PATH):
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()

