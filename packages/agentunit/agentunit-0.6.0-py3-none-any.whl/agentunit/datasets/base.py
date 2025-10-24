"""Dataset abstraction for AgentUnit scenarios."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Callable, Optional, Dict, List
import json
import csv

from ..core.exceptions import AgentUnitError


@dataclass(slots=True)
class DatasetCase:
    """Represents a single test case for an agent scenario."""

    id: str
    query: str
    expected_output: Optional[str] = None
    tools: Optional[List[str]] = None
    context: Optional[List[str]] = None
    metadata: Dict[str, object] = field(default_factory=dict)


class DatasetSource:
    """Container that produces dataset cases on demand."""

    def __init__(self, name: str, loader: Callable[[], Iterable[DatasetCase]]) -> None:
        self._name = name
        self._loader = loader

    @property
    def name(self) -> str:
        return self._name

    def iter_cases(self) -> Iterator[DatasetCase]:
        for case in self._loader():
            yield case

    @classmethod
    def single(cls, case: DatasetCase) -> "DatasetSource":
        return cls(name=f"single:{case.id}", loader=lambda: [case])

    @classmethod
    def from_list(cls, cases: List[DatasetCase], name: str = "from_list") -> "DatasetSource":
        return cls(name=name, loader=lambda: cases)

    @classmethod
    def empty(cls, name: str = "empty") -> "DatasetSource":
        return cls(name=name, loader=lambda: [])

    def __repr__(self) -> str:  # pragma: no cover - debug only
        return f"DatasetSource(name={self._name!r})"


def load_local_json(path: str | Path) -> DatasetSource:
    file_path = Path(path)
    if not file_path.exists():
        raise AgentUnitError(f"Dataset file not found: {file_path}")

    def _loader() -> Iterable[DatasetCase]:
        content = json.loads(file_path.read_text())
        if isinstance(content, dict):
            items = content.get("items", [])
        else:
            items = content
        for idx, row in enumerate(items):
            yield DatasetCase(
                id=row.get("id") or f"case-{idx}",
                query=row["query"],
                expected_output=row.get("expected_output"),
                tools=row.get("tools"),
                context=row.get("context"),
                metadata=row.get("metadata", {}),
            )

    return DatasetSource(name=str(file_path.stem), loader=_loader)


def load_local_csv(path: str | Path) -> DatasetSource:
    file_path = Path(path)
    if not file_path.exists():
        raise AgentUnitError(f"Dataset file not found: {file_path}")

    def _loader() -> Iterable[DatasetCase]:
        with file_path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for idx, row in enumerate(reader):
                yield DatasetCase(
                    id=row.get("id") or f"case-{idx}",
                    query=row["query"],
                    expected_output=row.get("expected_output"),
                    tools=row.get("tools", "").split(";") if row.get("tools") else None,
                    context=row.get("context", "").split("||") if row.get("context") else None,
                    metadata={k: v for k, v in row.items() if k not in {"id", "query", "expected_output", "tools", "context"}},
                )

    return DatasetSource(name=str(file_path.stem), loader=_loader)
