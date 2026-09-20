"""Resolve reusable synthetic answer groups with a strict confirmation gate."""

from __future__ import annotations

from dataclasses import dataclass

from .application_answer_vault import ApplicationAnswerVault


@dataclass(frozen=True)
class ResolutionResult:
    resolved_ids: tuple[str, ...]
    answer: str


class ExecutionResolutionService:
    def __init__(self, vault: ApplicationAnswerVault):
        self.vault = vault

    def resolve_group(
        self,
        blockers: list[dict[str, str]],
        group_id: str,
        answer: str,
        confirmation: str,
    ) -> ResolutionResult:
        if confirmation != "YES":
            raise ValueError("exact YES confirmation is required")
        group = [b for b in blockers if b.get("group_id") == group_id]
        if not group:
            raise ValueError("unknown answer group")
        if any(b.get("kind") in {"SECURITY", "FINAL_SUBMIT"} for b in group):
            raise ValueError("unsafe blockers cannot be grouped")

        key = group[0]["answer_key"]
        if any(b.get("answer_key") != key for b in group):
            raise ValueError("group contains conflicting answer keys")
        self.vault.update(key, answer)
        return ResolutionResult(tuple(b["id"] for b in group), answer)
