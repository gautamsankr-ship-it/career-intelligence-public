import pytest

from app.services.execution_resolution_service import ExecutionResolutionService


def test_security_blocker_cannot_be_grouped(vault) -> None:
    blockers = [{"id": "synthetic-security", "group_id": "security", "answer_key": "security", "kind": "SECURITY"}]
    with pytest.raises(ValueError, match="unsafe"):
        ExecutionResolutionService(vault).resolve_group(
            blockers, "security", "MANUAL_REVIEW", "YES"
        )


def test_conflicting_answer_keys_are_rejected(vault) -> None:
    blockers = [
        {"id": "synthetic-a", "group_id": "mixed", "answer_key": "one", "kind": "SCREENING"},
        {"id": "synthetic-b", "group_id": "mixed", "answer_key": "two", "kind": "SCREENING"},
    ]
    with pytest.raises(ValueError, match="conflicting"):
        ExecutionResolutionService(vault).resolve_group(
            blockers, "mixed", "MANUAL_REVIEW", "YES"
        )
