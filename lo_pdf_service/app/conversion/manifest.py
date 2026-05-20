from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.models import OutputKind


@dataclass(frozen=True)
class AttachmentRecord:
    original_filename: str
    output_filename: str | None
    status: str
    reason: str | None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "original_filename": self.original_filename,
            "output_filename": self.output_filename,
            "status": self.status,
            "reason": self.reason,
        }


@dataclass
class ConversionManifest:
    source_filename: str
    output_kind: OutputKind
    outputs: list[dict[str, str]] = field(default_factory=list)
    attachments: list[AttachmentRecord] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_output(self, name: str, path: Path) -> None:
        self.outputs.append({"name": name, "path": path.as_posix()})

    def add_attachment(self, record: AttachmentRecord) -> None:
        self.attachments.append(record)

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)

    def to_dict(self) -> dict[str, object]:
        return {
            "source_filename": self.source_filename,
            "output_kind": self.output_kind.value,
            "outputs": self.outputs,
            "attachments": [record.to_dict() for record in self.attachments],
            "warnings": self.warnings,
        }
