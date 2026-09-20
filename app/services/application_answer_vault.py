"""Minimal synthetic answer vault with explicit, testable persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SYNTHETIC_DEFAULTS: dict[str, Any] = {
    "full_name": "Synthetic Candidate",
    "email_address": "candidate@example.test",
    "location": "Synthetic City",
    "work_authorization": "MANUAL_REVIEW",
}


class ApplicationAnswerVault:
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return dict(SYNTHETIC_DEFAULTS)
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, answers: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(answers, indent=2) + "\n", encoding="utf-8")

    def update(self, key: str, value: Any) -> dict[str, Any]:
        answers = self.load()
        answers[key] = value
        self.save(answers)
        return answers
