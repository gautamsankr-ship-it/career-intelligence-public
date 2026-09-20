from pathlib import Path

import pytest

from app.services.application_answer_vault import ApplicationAnswerVault


@pytest.fixture
def vault(tmp_path: Path) -> ApplicationAnswerVault:
    return ApplicationAnswerVault(tmp_path / "vault.json")


@pytest.fixture
def blockers() -> list[dict[str, str]]:
    return [
        {"id": "synthetic-1", "group_id": "location", "answer_key": "location", "kind": "SCREENING"},
        {"id": "synthetic-2", "group_id": "location", "answer_key": "location", "kind": "SCREENING"},
    ]
