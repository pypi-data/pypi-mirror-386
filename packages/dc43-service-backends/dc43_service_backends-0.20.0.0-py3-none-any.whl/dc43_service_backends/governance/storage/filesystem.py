"""Filesystem-backed governance persistence implementation."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Optional, Sequence

from dc43_service_clients.data_quality import ValidationResult, coerce_details

from .interface import GovernanceStore


@dataclass(slots=True)
class _StatusRecord:
    contract_id: str
    contract_version: str
    dataset_id: str
    dataset_version: str
    status: str
    reason: str | None
    details: Mapping[str, object]
    recorded_at: str


class FilesystemGovernanceStore(GovernanceStore):
    """Persist governance artefacts to JSON files on disk."""

    def __init__(self, base_path: str | os.PathLike[str]) -> None:
        self.base_path = Path(base_path).expanduser()
        self.base_path.mkdir(parents=True, exist_ok=True)
        for subdir in ("status", "links", "pipeline_activity"):
            (self.base_path / subdir).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _safe(self, value: str) -> str:
        return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in value)

    def _status_path(self, dataset_id: str, dataset_version: str) -> Path:
        folder = self.base_path / "status" / self._safe(dataset_id)
        folder.mkdir(parents=True, exist_ok=True)
        return folder / f"{self._safe(dataset_version)}.json"

    def _links_path(self, dataset_id: str) -> Path:
        folder = self.base_path / "links"
        folder.mkdir(parents=True, exist_ok=True)
        return folder / f"{self._safe(dataset_id)}.json"

    def _activity_path(self, dataset_id: str) -> Path:
        folder = self.base_path / "pipeline_activity"
        folder.mkdir(parents=True, exist_ok=True)
        return folder / f"{self._safe(dataset_id)}.json"

    def _read_json(self, path: Path) -> Mapping[str, object] | None:
        if not path.exists():
            return None
        try:
            payload = path.read_text("utf-8")
            data = json.loads(payload)
        except (OSError, json.JSONDecodeError):
            return None
        if isinstance(data, Mapping):
            return data
        return None

    def _write_json(self, path: Path, payload: Mapping[str, object]) -> None:
        tmp = path.with_suffix(".tmp")
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), "utf-8")
        tmp.replace(path)

    # ------------------------------------------------------------------
    # Status persistence
    # ------------------------------------------------------------------
    def save_status(
        self,
        *,
        contract_id: str,
        contract_version: str,
        dataset_id: str,
        dataset_version: str,
        status: ValidationResult | None,
    ) -> None:
        path = self._status_path(dataset_id, dataset_version)
        if status is None:
            try:
                path.unlink()
            except FileNotFoundError:
                return
            return

        record = _StatusRecord(
            contract_id=contract_id,
            contract_version=contract_version,
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            status=status.status,
            reason=status.reason,
            details=status.details,
            recorded_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        self._write_json(path, asdict(record))

    def load_status(
        self,
        *,
        contract_id: str,
        contract_version: str,
        dataset_id: str,
        dataset_version: str,
    ) -> ValidationResult | None:
        path = self._status_path(dataset_id, dataset_version)
        payload = self._read_json(path)
        if not payload:
            return None
        linked = payload.get("contract_id"), payload.get("contract_version")
        if linked != (contract_id, contract_version):
            reason = (
                f"dataset linked to contract {linked[0]}:{linked[1]}"
                if all(linked)
                else "dataset linked to a different contract"
            )
            return ValidationResult(status="block", reason=reason, details=payload)
        return ValidationResult(
            status=str(payload.get("status", "unknown")),
            reason=str(payload.get("reason")) if payload.get("reason") else None,
            details=coerce_details(payload.get("details")),
        )

    # ------------------------------------------------------------------
    # Dataset links
    # ------------------------------------------------------------------
    def link_dataset_contract(
        self,
        *,
        dataset_id: str,
        dataset_version: str,
        contract_id: str,
        contract_version: str,
    ) -> None:
        path = self._links_path(dataset_id)
        payload = self._read_json(path) or {"versions": {}}
        versions = payload.get("versions")
        if not isinstance(versions, dict):
            versions = {}
        entry = {
            "contract_id": contract_id,
            "contract_version": contract_version,
            "dataset_version": dataset_version,
            "linked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        versions[str(dataset_version)] = entry
        payload["versions"] = versions
        payload["latest"] = entry
        self._write_json(path, payload)

    def get_linked_contract_version(
        self,
        *,
        dataset_id: str,
        dataset_version: Optional[str] = None,
    ) -> str | None:
        payload = self._read_json(self._links_path(dataset_id))
        if not payload:
            return None
        versions = payload.get("versions")
        if isinstance(versions, Mapping) and dataset_version is not None:
            entry = versions.get(str(dataset_version))
            if isinstance(entry, Mapping):
                cid = entry.get("contract_id")
                cver = entry.get("contract_version")
                if cid and cver:
                    return f"{cid}:{cver}"
        latest = payload.get("latest")
        if isinstance(latest, Mapping):
            cid = latest.get("contract_id")
            cver = latest.get("contract_version")
            if cid and cver:
                return f"{cid}:{cver}"
        return None

    # ------------------------------------------------------------------
    # Pipeline activity
    # ------------------------------------------------------------------
    def record_pipeline_event(
        self,
        *,
        contract_id: str,
        contract_version: str,
        dataset_id: str,
        dataset_version: str,
        event: Mapping[str, object],
    ) -> None:
        path = self._activity_path(dataset_id)
        payload = self._read_json(path) or {"dataset_id": dataset_id, "versions": {}}
        versions = payload.get("versions")
        if not isinstance(versions, dict):
            versions = {}
        version_key = str(dataset_version)
        record = versions.get(version_key)
        if not isinstance(record, dict):
            record = {
                "dataset_id": dataset_id,
                "dataset_version": dataset_version,
                "contract_id": contract_id,
                "contract_version": contract_version,
                "events": [],
            }
        events = list(record.get("events") or [])
        events.append(dict(event))
        record["events"] = events
        record["contract_id"] = contract_id
        record["contract_version"] = contract_version
        versions[version_key] = record
        payload["versions"] = versions
        payload["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self._write_json(path, payload)

    def load_pipeline_activity(
        self,
        *,
        dataset_id: str,
        dataset_version: Optional[str] = None,
    ) -> Sequence[Mapping[str, object]]:
        payload = self._read_json(self._activity_path(dataset_id))
        if not payload:
            return []
        versions = payload.get("versions")
        if not isinstance(versions, Mapping):
            return []
        if dataset_version is not None:
            record = versions.get(str(dataset_version))
            if isinstance(record, Mapping):
                return [dict(record)]
            return []
        entries: list[Mapping[str, object]] = []
        for record in versions.values():
            if isinstance(record, Mapping):
                entries.append(dict(record))
        entries.sort(
            key=lambda item: (
                0,
                str(
                    (item.get("events") or [{}])[-1].get("recorded_at", "")
                    if isinstance(item.get("events"), list) and item["events"]
                    else ""
                ),
            )
        )
        return entries


__all__ = ["FilesystemGovernanceStore"]
