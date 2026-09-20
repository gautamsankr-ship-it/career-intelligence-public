"""Safe defaults for the public synthetic demonstration."""

from pathlib import Path
import tempfile


def temporary_runtime_dir() -> Path:
    """Return a caller-owned temporary directory for disposable state."""
    return Path(tempfile.mkdtemp(prefix="synthetic-career-portfolio-"))


SYNTHETIC_EMAIL = "candidate@example.test"
SYNTHETIC_CANDIDATE_NAME = "Synthetic Candidate"
