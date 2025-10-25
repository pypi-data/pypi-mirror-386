import logging
from typing import Awaitable, Callable

from fastapi import APIRouter, Depends, HTTPException, Request, Response, params
from fastapi.params import Query
from fastapi.responses import StreamingResponse
from llama_deploy.core import schema
from typing_extensions import Annotated

from ._abstract_deployments_service import (
    AbstractDeploymentsService,
    AbstractPublicDeploymentsService,
)
from ._exceptions import DeploymentNotFoundError, ReplicaSetNotFoundError

logger = logging.getLogger(__name__)


async def get_project_id(project_id: Annotated[str, Query()]) -> str:
    return project_id


def create_v1beta1_deployments_router(
    deployments_service: AbstractDeploymentsService,
    public_service: AbstractPublicDeploymentsService,
    get_project_id: Callable[..., Awaitable[str]] = get_project_id,
    dependencies: list[params.Depends] | None = None,
    public_dependencies: list[params.Depends] | None = None,
    include_in_schema: bool = True,
) -> APIRouter:
    base_router = APIRouter(prefix="/api/v1beta1", include_in_schema=include_in_schema)
    public_router = APIRouter(
        tags=["v1beta1-deployments-public"],
        dependencies=public_dependencies,
        include_in_schema=include_in_schema,
    )
    router = APIRouter(
        tags=["v1beta1-deployments"],
        dependencies=dependencies,
        include_in_schema=include_in_schema,
    )

    @public_router.get("/version")
    async def get_version() -> schema.VersionResponse:
        return await public_service.get_version()

    @router.get("/list-projects")
    async def get_projects() -> schema.ProjectsListResponse:
        """Get all unique projects with their deployment counts"""
        return await deployments_service.get_projects()

    @router.post("/validate-repository")
    async def validate_repository(
        project_id: Annotated[str, Depends(get_project_id)],
        request: schema.RepositoryValidationRequest,
    ) -> schema.RepositoryValidationResponse:
        """Validate repository access and return unified response."""
        return await deployments_service.validate_repository(
            project_id=project_id,
            request=request,
        )

    @router.post("", response_model=schema.DeploymentResponse)
    async def create_deployment(
        project_id: Annotated[str, Depends(get_project_id)],
        deployment_data: schema.DeploymentCreate,
    ) -> Response:
        deployment_response = await deployments_service.create_deployment(
            project_id=project_id,
            deployment_data=deployment_data,
        )
        # Return deployment response with warning header if there are git issues

        response = Response(
            content=deployment_response.model_dump_json(),
            status_code=201,
            media_type="application/json",
        )
        return response

    @router.get("")
    async def get_deployments(
        project_id: Annotated[str, Depends(get_project_id)],
    ) -> schema.DeploymentsListResponse:
        return await deployments_service.get_deployments(project_id=project_id)

    @router.get("/{deployment_id}")
    async def get_deployment(
        project_id: Annotated[str, Depends(get_project_id)],
        deployment_id: str,
        include_events: Annotated[bool, Query()] = False,
    ) -> schema.DeploymentResponse:
        deployment = await deployments_service.get_deployment(
            project_id=project_id,
            deployment_id=deployment_id,
            include_events=include_events,
        )
        if deployment is None:
            raise HTTPException(
                status_code=404,
                detail=f"Deployment with id {deployment_id} not found",
            )

        return deployment

    @router.get("/{deployment_id}/history")
    async def get_deployment_history(
        project_id: Annotated[str, Depends(get_project_id)],
        deployment_id: str,
    ) -> schema.DeploymentHistoryResponse:
        return await deployments_service.get_deployment_history(
            project_id=project_id, deployment_id=deployment_id
        )

    @router.post("/{deployment_id}/rollback")
    async def rollback_deployment(
        project_id: Annotated[str, Depends(get_project_id)],
        deployment_id: str,
        request: schema.RollbackRequest,
    ) -> schema.DeploymentResponse:
        return await deployments_service.rollback_deployment(
            project_id=project_id, deployment_id=deployment_id, request=request
        )

    @router.delete("/{deployment_id}")
    async def delete_deployment(
        project_id: Annotated[str, Depends(get_project_id)],
        deployment_id: str,
    ) -> None:
        await deployments_service.delete_deployment(
            project_id=project_id, deployment_id=deployment_id
        )

    @router.patch("/{deployment_id}", response_model=schema.DeploymentResponse)
    async def update_deployment(
        project_id: Annotated[str, Depends(get_project_id)],
        deployment_id: str,
        update_data: schema.DeploymentUpdate,
    ) -> Response:
        """Update an existing deployment with patch-style changes

        Args:
            project_id: The project ID
            deployment_id: The deployment ID to update
            update_data: The patch-style update data
        """

        deployment_response = await deployments_service.update_deployment(
            project_id=project_id,
            deployment_id=deployment_id,
            update_data=update_data,
        )

        response = Response(
            content=deployment_response.model_dump_json(),
            status_code=200,
            media_type="application/json",
        )
        return response

    @router.get("/{deployment_id}/logs")
    async def stream_deployment_logs(
        request: Request,
        project_id: Annotated[str, Depends(get_project_id)],
        deployment_id: str,
        include_init_containers: Annotated[bool, Query()] = False,
        since_seconds: Annotated[int | None, Query()] = None,
        tail_lines: Annotated[int | None, Query()] = None,
    ):
        """Stream logs for the latest ReplicaSet of a deployment.

        The stream ends when the latest ReplicaSet changes (e.g., a new rollout occurs).
        """

        try:
            inner = deployments_service.stream_deployment_logs(
                project_id=project_id,
                deployment_id=deployment_id,
                include_init_containers=include_init_containers,
                since_seconds=since_seconds,
                tail_lines=tail_lines,
            )

            async def sse_lines():
                async for data in inner:
                    yield "event: log\n"
                    yield f"data: {data.model_dump_json()}\n\n"

            return StreamingResponse(
                sse_lines(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        except DeploymentNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ReplicaSetNotFoundError as e:
            # Deployment exists but hasn't created a ReplicaSet yet
            raise HTTPException(status_code=409, detail=str(e))

    base_router.include_router(public_router, prefix="/deployments-public")
    base_router.include_router(router, prefix="/deployments")
    return base_router
