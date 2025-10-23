from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from dc43_service_backends.contracts.backend.local import LocalContractServiceBackend
from dc43_service_backends.contracts.backend.stores.interface import ContractStore


@dataclass
class _StoredContract:
    contract_id: str
    version: str


class InMemoryStore(ContractStore):
    def __init__(self) -> None:
        self._data: Dict[tuple[str, str], _StoredContract] = {}

    def put(self, contract: _StoredContract) -> None:  # type: ignore[override]
        self._data[(contract.contract_id, contract.version)] = contract

    def get(self, contract_id: str, version: str) -> _StoredContract:  # type: ignore[override]
        return self._data[(contract_id, version)]

    def list_contracts(self) -> List[str]:  # type: ignore[override]
        return sorted({contract_id for contract_id, _ in self._data})

    def list_versions(self, contract_id: str) -> List[str]:  # type: ignore[override]
        return sorted(version for (cid, version) in self._data if cid == contract_id)


def make_contract(contract_id: str, version: str) -> _StoredContract:
    return _StoredContract(contract_id=contract_id, version=version)


def test_local_backend_delegates_to_store():
    store = InMemoryStore()
    backend = LocalContractServiceBackend(store)
    contract = make_contract("orders", "1.0.0")
    store.put(contract)

    assert backend.get("orders", "1.0.0") == contract
    assert backend.list_versions("orders") == ["1.0.0"]
    assert backend.latest("orders") == contract


def test_link_dataset_contract_keeps_contract_available():
    store = InMemoryStore()
    backend = LocalContractServiceBackend(store)
    store.put(make_contract("orders", "1.0.0"))

    backend.link_dataset_contract(
        dataset_id="table.orders",
        dataset_version="current",
        contract_id="orders",
        contract_version="1.0.0",
    )

    assert backend.get("orders", "1.0.0").contract_id == "orders"
    assert backend.get_linked_contract_version(dataset_id="table.orders") is None
