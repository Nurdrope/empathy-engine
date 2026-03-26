import atexit
import os
import shutil
import tempfile


def _configure_joblib_temp_dir() -> None:
    """Ensure joblib uses a writable temp dir during tests."""
    os.environ.setdefault("JOBLIB_MULTIPROCESSING", "0")
    if os.environ.get("JOBLIB_TEMP_FOLDER"):
        return
    path = tempfile.mkdtemp(prefix="empathy_engine_joblib_")
    os.environ["JOBLIB_TEMP_FOLDER"] = path
    atexit.register(shutil.rmtree, path, ignore_errors=True)


_configure_joblib_temp_dir()
