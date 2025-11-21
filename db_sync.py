# db_sync.py
import os, sqlite3, shutil, tempfile, git, datetime as dt

REPO_URL = f"https://{os.getenv('GITHUB_TOKEN')}@github.com/{os.getenv('REPO_OWNER')}/{os.getenv('REPO')}.git"
DB_FILE  = "jugadores.db"
CLONE_DIR= tempfile.mkdtemp()

def pull_db():
    """Descarga la BD del repo (si existe) y la deja en disco local."""
    repo = git.Repo.clone_from(REPO_URL, CLONE_DIR, branch='main', depth=1)
    src  = os.path.join(CLONE_DIR, DB_FILE)
    if os.path.exists(src):
        shutil.copy(src, DB_FILE)
    return repo, CLONE_DIR

def push_db(repo, dir):
    """Sube la BD local al repo."""
    if os.path.exists(DB_FILE):
        shutil.copy(DB_FILE, os.path.join(dir, DB_FILE))
    repo.index.add([DB_FILE])
    repo.index.commit(f"auto-save {dt.datetime.utcnow().isoformat()}")
    repo.remotes.origin.push()

def close_repo(repo, dir):
    shutil.rmtree(dir)