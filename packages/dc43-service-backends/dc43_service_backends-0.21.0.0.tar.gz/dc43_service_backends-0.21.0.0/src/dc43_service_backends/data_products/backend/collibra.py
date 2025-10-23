"""Collibra-backed data product backend implementations."""

from __future__ import annotations

import tempfile
from typing import Dict, Mapping, Optional, Protocol, Sequence

from dc43_service_clients.odps import (
    DataProductInputPort,
    DataProductOutputPort,
    OpenDataProductStandard,
    as_odps_dict,
    evolve_to_draft,
    to_model,
)

from .interface import DataProductRegistrationResult, DataProductServiceBackend
from .local import FilesystemDataProductServiceBackend


def _as_custom_properties(data: Optional[Mapping[str, object]]) -> list[dict[str, object]]:
    if not data:
        return []
    props: list[dict[str, object]] = []
    for key, value in data.items():
        props.append({"property": str(key), "value": value})
    return props


class CollibraDataProductAdapter(Protocol):
    """Minimal abstraction for Collibra data product operations."""

    def list_versions(self, data_product_id: str) -> Sequence[str]:
        """Return the known versions for ``data_product_id``."""

    def get_data_product(self, data_product_id: str, version: str) -> Mapping[str, object]:
        """Return the ODPS payload for ``data_product_id`` at ``version``."""

    def latest_data_product(self, data_product_id: str) -> Optional[Mapping[str, object]]:
        """Return the latest ODPS payload for ``data_product_id`` when available."""

    def upsert_data_product(
        self,
        product: Mapping[str, object],
        *,
        status: Optional[str] = None,
    ) -> None:
        """Persist ``product`` in Collibra with the desired lifecycle ``status``."""


class CollibraDataProductServiceBackend(DataProductServiceBackend):
    """Expose Collibra-managed data products through the backend interface."""

    def __init__(
        self,
        adapter: CollibraDataProductAdapter,
        *,
        default_status: str = "Draft",
    ) -> None:
        self._adapter = adapter
        self._default_status = default_status

    # ------------------------------------------------------------------
    # Base persistence helpers
    # ------------------------------------------------------------------
    def put(self, product: OpenDataProductStandard) -> None:  # noqa: D401 - short docstring
        if not product.version:
            raise ValueError("Data product version is required")
        payload = as_odps_dict(product)
        status = payload.get("status") or product.status or self._default_status
        if status:
            payload["status"] = status
        self._adapter.upsert_data_product(payload, status=status)

    def get(self, data_product_id: str, version: str) -> OpenDataProductStandard:  # noqa: D401
        payload = self._adapter.get_data_product(data_product_id, version)
        return to_model(payload)

    def latest(self, data_product_id: str) -> Optional[OpenDataProductStandard]:  # noqa: D401
        payload = self._adapter.latest_data_product(data_product_id)
        if payload is None:
            return None
        return to_model(payload)

    def list_versions(self, data_product_id: str) -> Sequence[str]:  # noqa: D401
        versions = self._adapter.list_versions(data_product_id)
        return sorted(str(value) for value in versions)

    # ------------------------------------------------------------------
    # Port registration helpers
    # ------------------------------------------------------------------
    def _existing_versions(self, data_product_id: str) -> Sequence[str]:
        return self.list_versions(data_product_id)

    def _ensure_product(self, data_product_id: str) -> OpenDataProductStandard:
        product = self.latest(data_product_id)
        if product is not None:
            return product.clone()
        status = self._default_status.lower() if self._default_status else "draft"
        return OpenDataProductStandard(id=data_product_id, status=status)

    def _store_updated(
        self,
        product: OpenDataProductStandard,
        *,
        bump: str,
        data_product_id: str,
    ) -> OpenDataProductStandard:
        evolve_to_draft(
            product,
            existing_versions=self._existing_versions(data_product_id),
            bump=bump,
        )
        self.put(product)
        return product

    def register_input_port(
        self,
        *,
        data_product_id: str,
        port: DataProductInputPort,
        bump: str = "minor",
        custom_properties: Optional[Mapping[str, object]] = None,
        source_data_product: Optional[str] = None,
        source_output_port: Optional[str] = None,
    ) -> DataProductRegistrationResult:
        product = self._ensure_product(data_product_id)
        did_change = product.ensure_input_port(port)
        if not did_change:
            return DataProductRegistrationResult(product=product, changed=False)

        props = _as_custom_properties(custom_properties)
        if source_data_product:
            props.append(
                {
                    "property": "dc43.input.source_data_product",
                    "value": source_data_product,
                }
            )
        if source_output_port:
            props.append(
                {
                    "property": "dc43.input.source_output_port",
                    "value": source_output_port,
                }
            )
        if props:
            existing = list(port.custom_properties)
            for item in props:
                if item not in existing:
                    existing.append(item)
            port.custom_properties = existing

        updated = self._store_updated(product, bump=bump, data_product_id=data_product_id)
        return DataProductRegistrationResult(product=updated, changed=True)

    def register_output_port(
        self,
        *,
        data_product_id: str,
        port: DataProductOutputPort,
        bump: str = "minor",
        custom_properties: Optional[Mapping[str, object]] = None,
    ) -> DataProductRegistrationResult:
        product = self._ensure_product(data_product_id)
        did_change = product.ensure_output_port(port)
        if not did_change:
            return DataProductRegistrationResult(product=product, changed=False)

        props = _as_custom_properties(custom_properties)
        if props:
            existing = list(port.custom_properties)
            for item in props:
                if item not in existing:
                    existing.append(item)
            port.custom_properties = existing

        updated = self._store_updated(product, bump=bump, data_product_id=data_product_id)
        return DataProductRegistrationResult(product=updated, changed=True)

    def resolve_output_contract(
        self,
        *,
        data_product_id: str,
        port_name: str,
    ) -> Optional[tuple[str, str]]:
        product = self.latest(data_product_id)
        if product is None:
            return None
        port = product.find_output_port(port_name)
        if port is None or not port.contract_id:
            return None
        return port.contract_id, port.version


class StubCollibraDataProductAdapter(CollibraDataProductAdapter):
    """Filesystem-backed stub adapter used for tests and demos."""

    def __init__(self, base_path: Optional[str] = None) -> None:
        if base_path is None:
            self._temp_dir = tempfile.TemporaryDirectory(prefix="dc43-collibra-dp-")
            base_path = self._temp_dir.name
        else:
            self._temp_dir = None
        self._backend = FilesystemDataProductServiceBackend(base_path)

    def close(self) -> None:
        if getattr(self, "_temp_dir", None) is not None:
            self._temp_dir.cleanup()
            self._temp_dir = None

    def __del__(self) -> None:  # pragma: no cover - best effort cleanup
        try:
            self.close()
        except Exception:
            pass

    def list_versions(self, data_product_id: str) -> Sequence[str]:  # noqa: D401
        return self._backend.list_versions(data_product_id)

    def get_data_product(self, data_product_id: str, version: str) -> Mapping[str, object]:  # noqa: D401
        model = self._backend.get(data_product_id, version)
        return as_odps_dict(model)

    def latest_data_product(self, data_product_id: str) -> Optional[Mapping[str, object]]:  # noqa: D401
        model = self._backend.latest(data_product_id)
        if model is None:
            return None
        return as_odps_dict(model)

    def upsert_data_product(
        self,
        product: Mapping[str, object],
        *,
        status: Optional[str] = None,
    ) -> None:
        model = to_model(product)
        if status:
            model.status = status
        self._backend.put(model)


class HttpCollibraDataProductAdapter(CollibraDataProductAdapter):
    """HTTP adapter aligned with Collibra Data Product endpoints."""

    def __init__(
        self,
        base_url: str,
        *,
        token: Optional[str] = None,
        timeout: float = 10.0,
        client=None,
        products_endpoint_template: str = "/rest/2.0/dataproducts/{data_product}",
    ) -> None:
        try:
            import httpx  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency guard
            raise RuntimeError("httpx is required to use HttpCollibraDataProductAdapter") from exc

        self._httpx = httpx
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._products_endpoint_template = products_endpoint_template.rstrip("/")
        if client is None:
            self._client = httpx.Client(base_url=self._base_url, timeout=timeout)
            self._owns_client = True
        else:
            self._client = client
            self._owns_client = False

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "HttpCollibraDataProductAdapter":  # pragma: no cover - trivial
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        self.close()

    # ------------------------------------------------------------------
    # Request helpers
    # ------------------------------------------------------------------
    def _headers(self) -> Dict[str, str]:
        headers = {"accept": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _product_url(self, data_product: str, suffix: str = "") -> str:
        base = self._products_endpoint_template.format(data_product=data_product)
        return f"{base}{suffix}"

    def list_versions(self, data_product_id: str) -> Sequence[str]:  # noqa: D401
        resp = self._client.get(
            self._product_url(data_product_id, "/versions"),
            headers=self._headers(),
        )
        resp.raise_for_status()
        payload = resp.json()
        if isinstance(payload, Mapping):
            values = payload.get("data") or payload.get("results") or payload.get("versions")
            if isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
                return [str(item) for item in values]
        if isinstance(payload, Sequence) and not isinstance(payload, (str, bytes)):
            return [str(item) for item in payload]
        return []

    def get_data_product(self, data_product_id: str, version: str) -> Mapping[str, object]:  # noqa: D401
        resp = self._client.get(
            self._product_url(data_product_id, f"/versions/{version}"),
            headers=self._headers(),
        )
        resp.raise_for_status()
        payload = resp.json()
        if isinstance(payload, Mapping):
            if "dataProduct" in payload and isinstance(payload["dataProduct"], Mapping):
                return payload["dataProduct"]
            if "data" in payload and isinstance(payload["data"], Mapping):
                return payload["data"]
        return payload

    def latest_data_product(self, data_product_id: str) -> Optional[Mapping[str, object]]:  # noqa: D401
        resp = self._client.get(
            self._product_url(data_product_id, "/latest"),
            headers=self._headers(),
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        payload = resp.json()
        if isinstance(payload, Mapping):
            if "dataProduct" in payload and isinstance(payload["dataProduct"], Mapping):
                return payload["dataProduct"]
            if "data" in payload and isinstance(payload["data"], Mapping):
                return payload["data"]
        return payload

    def upsert_data_product(
        self,
        product: Mapping[str, object],
        *,
        status: Optional[str] = None,
    ) -> None:
        data_product_id = str(product.get("id") or "").strip()
        version = str(product.get("version") or "").strip()
        if not data_product_id or not version:
            raise ValueError("Collibra data product payload requires id and version")
        payload: Dict[str, object] = dict(product)
        if status and not payload.get("status"):
            payload["status"] = status
        resp = self._client.put(
            self._product_url(data_product_id, f"/versions/{version}"),
            headers=self._headers(),
            json={"dataProduct": payload},
        )
        resp.raise_for_status()


__all__ = [
    "CollibraDataProductAdapter",
    "CollibraDataProductServiceBackend",
    "HttpCollibraDataProductAdapter",
    "StubCollibraDataProductAdapter",
]

