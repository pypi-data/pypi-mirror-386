"""HTTP application exposing service backend capabilities."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

try:  # pragma: no cover - import guard exercised in packaging contexts
    from fastapi import APIRouter, FastAPI, HTTPException, Response
    from fastapi.responses import RedirectResponse
    from fastapi.encoders import jsonable_encoder
except ModuleNotFoundError as exc:  # pragma: no cover - raised when optional deps missing
    raise ModuleNotFoundError(
        "FastAPI is required to use the HTTP server utilities. Install "
        "'dc43-service-backends[http]' to enable them."
    ) from exc
from pydantic import BaseModel
from open_data_contract_standard.model import OpenDataContractStandard  # type: ignore

from dc43_service_clients.odps import (
    DataProductInputPort,
    DataProductOutputPort,
    as_odps_dict as as_odps_product_dict,
)
from dc43_service_clients.data_quality.transport import (
    decode_observation_payload,
    decode_validation_result,
    encode_validation_result,
)
from dc43_service_clients.governance.transport import (
    decode_contract,
    decode_credentials,
    decode_draft_context,
    encode_contract,
    encode_quality_assessment,
)
from dc43_service_clients.governance.models import QualityAssessment

from .contracts import ContractServiceBackend
from .data_products import DataProductServiceBackend
from .data_quality import DataQualityServiceBackend
from .governance.backend import GovernanceServiceBackend


class _LinkDatasetPayload(BaseModel):
    dataset_id: str
    dataset_version: str
    contract_id: str
    contract_version: str


class _DataProductInputPayload(BaseModel):
    port_name: str
    contract_id: str
    contract_version: str
    bump: str = "minor"
    custom_properties: Optional[Mapping[str, Any]] = None
    source_data_product: Optional[str] = None
    source_output_port: Optional[str] = None


class _DataProductOutputPayload(BaseModel):
    port_name: str
    contract_id: str
    contract_version: str
    bump: str = "minor"
    custom_properties: Optional[Mapping[str, Any]] = None


class _EvaluateDQPayload(BaseModel):
    contract: Mapping[str, Any]
    payload: Mapping[str, Any]


class _ExpectationsPayload(BaseModel):
    contract: Mapping[str, Any]


class _GovernanceEvaluatePayload(BaseModel):
    contract_id: str
    contract_version: str
    dataset_id: str
    dataset_version: str
    validation: Optional[Mapping[str, Any]] = None
    observations: Mapping[str, Any]
    bump: str = "minor"
    context: Optional[Mapping[str, Any]] = None
    pipeline_context: Optional[Mapping[str, Any]] = None
    operation: str = "read"
    draft_on_violation: bool = False


class _GovernanceReviewPayload(BaseModel):
    validation: Mapping[str, Any]
    base_contract: Mapping[str, Any]
    bump: str = "minor"
    dataset_id: Optional[str] = None
    dataset_version: Optional[str] = None
    data_format: Optional[str] = None
    dq_status: Optional[Mapping[str, Any]] = None
    dq_feedback: Optional[Mapping[str, Any]] = None
    context: Optional[Mapping[str, Any]] = None
    pipeline_context: Optional[Mapping[str, Any]] = None
    draft_requested: bool = False
    operation: Optional[str] = None


class _GovernanceDraftPayload(BaseModel):
    validation: Mapping[str, Any]
    base_contract: Mapping[str, Any]
    bump: str = "minor"
    context: Optional[Mapping[str, Any]] = None
    pipeline_context: Optional[Mapping[str, Any]] = None


class _AuthPayload(BaseModel):
    credentials: Optional[Mapping[str, Any]] = None


def _encode_assessment(assessment: QualityAssessment) -> Mapping[str, Any]:
    return encode_quality_assessment(assessment)


def build_app(
    *,
    contract_backend: ContractServiceBackend,
    dq_backend: DataQualityServiceBackend,
    governance_backend: GovernanceServiceBackend,
    data_product_backend: DataProductServiceBackend,
    dependencies: Sequence[object] | None = None,
) -> FastAPI:
    """Create a FastAPI app exposing the provided backend implementations."""

    app = FastAPI(title="dc43 service backends")
    router_dependencies = list(dependencies) if dependencies else None
    router = APIRouter(dependencies=router_dependencies)

    @app.get("/", include_in_schema=False)
    def docs_redirect() -> Response:
        """Expose the interactive API documentation at the application root."""

        if app.docs_url:
            return RedirectResponse(url=app.docs_url)
        if app.openapi_url:
            return RedirectResponse(url=app.openapi_url)
        return Response(status_code=204)

    # ------------------------------------------------------------------
    # Contract service endpoints
    # ------------------------------------------------------------------
    @router.get("/contracts/{contract_id}/versions/{contract_version}")
    def get_contract(contract_id: str, contract_version: str) -> Mapping[str, Any]:
        try:
            contract = contract_backend.get(contract_id, contract_version)
        except FileNotFoundError as exc:  # pragma: no cover - backend signals missing contract
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return contract.model_dump(by_alias=True, exclude_none=True)

    @router.get("/contracts/{contract_id}/latest")
    def latest_contract(contract_id: str) -> Mapping[str, Any]:
        contract = contract_backend.latest(contract_id)
        if contract is None:
            raise HTTPException(status_code=404, detail="contract not found")
        return contract.model_dump(by_alias=True, exclude_none=True)

    @router.get("/contracts/{contract_id}/versions")
    def list_contract_versions(contract_id: str) -> list[str]:
        versions = contract_backend.list_versions(contract_id)
        return [str(value) for value in versions]

    @router.post("/contracts/link")
    def link_contract(payload: _LinkDatasetPayload) -> None:
        contract_backend.link_dataset_contract(
            dataset_id=payload.dataset_id,
            dataset_version=payload.dataset_version,
            contract_id=payload.contract_id,
            contract_version=payload.contract_version,
        )

    @router.get("/contracts/datasets/{dataset_id}/linked")
    def get_linked_contract(dataset_id: str, dataset_version: str | None = None) -> Mapping[str, Any]:
        version = contract_backend.get_linked_contract_version(
            dataset_id=dataset_id,
            dataset_version=dataset_version,
        )
        if version is None:
            raise HTTPException(status_code=404, detail="no contract linked")
        return {"contract_version": version}

    # ------------------------------------------------------------------
    # Data product endpoints
    # ------------------------------------------------------------------
    @router.get("/data-products/{data_product_id}/versions/{version}")
    def get_data_product(data_product_id: str, version: str) -> Mapping[str, Any]:
        try:
            product = data_product_backend.get(data_product_id, version)
        except FileNotFoundError as exc:  # pragma: no cover - backend signals missing product
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return as_odps_product_dict(product)

    @router.get("/data-products/{data_product_id}/latest")
    def latest_data_product(data_product_id: str) -> Mapping[str, Any]:
        product = data_product_backend.latest(data_product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="data product not found")
        return as_odps_product_dict(product)

    @router.get("/data-products/{data_product_id}/versions")
    def list_data_product_versions(data_product_id: str) -> list[str]:
        versions = data_product_backend.list_versions(data_product_id)
        return [str(value) for value in versions]

    @router.post("/data-products/{data_product_id}/input-ports")
    def register_data_product_input(
        data_product_id: str, payload: _DataProductInputPayload
    ) -> Mapping[str, Any]:
        result = data_product_backend.register_input_port(
            data_product_id=data_product_id,
            port=DataProductInputPort(
                name=payload.port_name,
                version=payload.contract_version,
                contract_id=payload.contract_id,
            ),
            bump=payload.bump,
            custom_properties=payload.custom_properties,
            source_data_product=payload.source_data_product,
            source_output_port=payload.source_output_port,
        )
        return {
            "product": as_odps_product_dict(result.product),
            "changed": result.changed,
        }

    @router.post("/data-products/{data_product_id}/output-ports")
    def register_data_product_output(
        data_product_id: str, payload: _DataProductOutputPayload
    ) -> Mapping[str, Any]:
        result = data_product_backend.register_output_port(
            data_product_id=data_product_id,
            port=DataProductOutputPort(
                name=payload.port_name,
                version=payload.contract_version,
                contract_id=payload.contract_id,
            ),
            bump=payload.bump,
            custom_properties=payload.custom_properties,
        )
        return {
            "product": as_odps_product_dict(result.product),
            "changed": result.changed,
        }

    @router.get("/data-products/{data_product_id}/output-ports/{port_name}/contract")
    def resolve_data_product_output_contract(
        data_product_id: str, port_name: str
    ) -> Mapping[str, Any]:
        contract = data_product_backend.resolve_output_contract(
            data_product_id=data_product_id,
            port_name=port_name,
        )
        if contract is None:
            raise HTTPException(status_code=404, detail="output port not found")
        contract_id, contract_version = contract
        return {
            "contract_id": contract_id,
            "contract_version": contract_version,
        }

    # ------------------------------------------------------------------
    # Data-quality endpoints
    # ------------------------------------------------------------------
    @router.post("/data-quality/evaluate")
    def evaluate_quality(payload: _EvaluateDQPayload) -> Mapping[str, Any]:
        contract = OpenDataContractStandard.model_validate(dict(payload.contract))
        observations = decode_observation_payload(payload.payload)
        result = dq_backend.evaluate(contract=contract, payload=observations)
        return encode_validation_result(result) or {}

    @router.post("/data-quality/expectations")
    def describe_expectations(payload: _ExpectationsPayload) -> list[Mapping[str, Any]]:
        contract = OpenDataContractStandard.model_validate(dict(payload.contract))
        descriptors = dq_backend.describe_expectations(contract=contract)
        return [dict(item) for item in descriptors]

    # ------------------------------------------------------------------
    # Governance endpoints
    # ------------------------------------------------------------------
    @router.post("/governance/auth")
    def configure_auth(payload: _AuthPayload) -> None:
        credentials = decode_credentials(payload.credentials)
        governance_backend.configure_auth(credentials)

    @router.post("/governance/evaluate")
    def evaluate_dataset(payload: _GovernanceEvaluatePayload) -> Mapping[str, Any]:
        validation = decode_validation_result(payload.validation)
        observations = decode_observation_payload(payload.observations)
        context = decode_draft_context(payload.context)
        assessment = governance_backend.evaluate_dataset(
            contract_id=payload.contract_id,
            contract_version=payload.contract_version,
            dataset_id=payload.dataset_id,
            dataset_version=payload.dataset_version,
            validation=validation,
            observations=lambda: observations,
            bump=payload.bump,
            context=context,
            pipeline_context=payload.pipeline_context,
            operation=payload.operation,
            draft_on_violation=payload.draft_on_violation,
        )
        return _encode_assessment(assessment)

    @router.post("/governance/review")
    def review_validation(payload: _GovernanceReviewPayload) -> Mapping[str, Any] | None:
        validation = decode_validation_result(payload.validation)
        base_contract = OpenDataContractStandard.model_validate(dict(payload.base_contract))
        dq_status = decode_validation_result(payload.dq_status)
        context = decode_draft_context(payload.context)
        draft = governance_backend.review_validation_outcome(
            validation=validation,
            base_contract=base_contract,
            bump=payload.bump,
            dataset_id=payload.dataset_id,
            dataset_version=payload.dataset_version,
            data_format=payload.data_format,
            dq_status=dq_status,
            dq_feedback=payload.dq_feedback,
            context=context,
            pipeline_context=payload.pipeline_context,
            draft_requested=payload.draft_requested,
            operation=payload.operation,
        )
        return encode_contract(draft)

    @router.post("/governance/draft")
    def propose_draft(payload: _GovernanceDraftPayload) -> Mapping[str, Any]:
        validation = decode_validation_result(payload.validation)
        base_contract = OpenDataContractStandard.model_validate(dict(payload.base_contract))
        context = decode_draft_context(payload.context)
        draft = governance_backend.propose_draft(
            validation=validation,
            base_contract=base_contract,
            bump=payload.bump,
            context=context,
            pipeline_context=payload.pipeline_context,
        )
        return encode_contract(draft) or {}

    @router.get("/governance/status")
    def get_status(
        contract_id: str,
        contract_version: str,
        dataset_id: str,
        dataset_version: str,
    ) -> Mapping[str, Any]:
        status = governance_backend.get_status(
            contract_id=contract_id,
            contract_version=contract_version,
            dataset_id=dataset_id,
            dataset_version=dataset_version,
        )
        if status is None:
            raise HTTPException(status_code=404, detail="status unavailable")
        return encode_validation_result(status) or {}

    @router.post("/governance/link", status_code=204)
    def link_dataset(payload: _LinkDatasetPayload) -> None:
        governance_backend.link_dataset_contract(
            dataset_id=payload.dataset_id,
            dataset_version=payload.dataset_version,
            contract_id=payload.contract_id,
            contract_version=payload.contract_version,
        )

    @router.get("/governance/linked")
    def get_link(dataset_id: str, dataset_version: str | None = None) -> Mapping[str, Any]:
        version = governance_backend.get_linked_contract_version(
            dataset_id=dataset_id,
            dataset_version=dataset_version,
        )
        if version is None:
            raise HTTPException(status_code=404, detail="no contract linked")
        return {"contract_version": version}

    @router.get("/governance/activity")
    def pipeline_activity(dataset_id: str, dataset_version: str | None = None) -> list[Mapping[str, Any]]:
        records = governance_backend.get_pipeline_activity(
            dataset_id=dataset_id,
            dataset_version=dataset_version,
        )
        return list(jsonable_encoder(records))

    app.include_router(router)
    return app


__all__ = ["build_app"]
