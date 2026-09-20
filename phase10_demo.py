"""Run a disposable synthetic grouped-resolution demonstration."""

from tempfile import TemporaryDirectory
from pathlib import Path

from app.services.application_answer_vault import ApplicationAnswerVault
from app.services.execution_resolution_service import ExecutionResolutionService


def main() -> None:
    blockers = [
        {"id": "synthetic-1", "group_id": "salary", "answer_key": "salary_expectation", "kind": "SCREENING"},
        {"id": "synthetic-2", "group_id": "salary", "answer_key": "salary_expectation", "kind": "SCREENING"},
    ]
    with TemporaryDirectory(prefix="synthetic-phase10-") as directory:
        vault = ApplicationAnswerVault(Path(directory) / "vault.json")
        result = ExecutionResolutionService(vault).resolve_group(
            blockers, "salary", "MANUAL_REVIEW", "YES"
        )
        print("SYNTHETIC DEMO ONLY")
        print(result)


if __name__ == "__main__":
    main()
