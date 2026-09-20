from app.services.execution_resolution_service import ExecutionResolutionService


def test_group_resolution_updates_all_synthetic_blockers(vault, blockers) -> None:
    result = ExecutionResolutionService(vault).resolve_group(
        blockers, "location", "Synthetic City", "YES"
    )
    assert result.resolved_ids == ("synthetic-1", "synthetic-2")
    assert vault.load()["location"] == "Synthetic City"


def test_invalid_confirmation_does_not_write(vault, blockers) -> None:
    try:
        ExecutionResolutionService(vault).resolve_group(
            blockers, "location", "Synthetic City", "yes"
        )
    except ValueError as error:
        assert "exact YES" in str(error)
    else:
        raise AssertionError("invalid confirmation unexpectedly succeeded")
    assert not (vault.path).exists()
