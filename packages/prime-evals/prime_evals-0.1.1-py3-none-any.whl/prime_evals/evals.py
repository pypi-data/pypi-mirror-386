import asyncio
import re
from typing import Any, Dict, List, Optional

from prime_core import APIClient, APIError, AsyncAPIClient

from .exceptions import EvalsAPIError, InvalidEvaluationError


class EvalsClient:
    """
    Client for the Prime Evals API
    """

    def __init__(self, api_client: APIClient) -> None:
        self.client = api_client

    def _resolve_environment_id(self, env_name: str) -> str:
        """
        Resolve environment ID to owner/name format.

        Raises:
            EvalsAPIError: If the environment does not exist (404)
        """
        if re.match(r"^[^/]+/[^/]+$", env_name):
            env_name = env_name.split("/", 1)[1]

        try:
            resolve_data: Dict[str, Any] = {"name": env_name}

            if self.client.config.team_id:
                resolve_data["team_id"] = self.client.config.team_id

            response = self.client.post("/environmentshub/resolve", json=resolve_data)
            return response["data"]["id"]

        except APIError as e:
            raise EvalsAPIError(
                f"Environment '{env_name}' does not exist in the hub. "
                f"Please push the environment first with: prime env push {env_name}"
            ) from e

    def create_evaluation(
        self,
        name: str,
        environments: Optional[List[Dict[str, str]]] = None,
        suite_id: Optional[str] = None,
        run_id: Optional[str] = None,
        model_name: Optional[str] = None,
        dataset: Optional[str] = None,
        framework: Optional[str] = None,
        task_type: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new evaluation

        Either run_id or environments must be provided.
        Environments should be a list of dicts with 'id' and optional 'version_id'.

        Example: [{"id": "simpleqa", "version_id": "v1"}]

        Raises:
            InvalidEvaluationError: If neither run_id nor environments is provided
        """
        if not run_id and not environments:
            raise InvalidEvaluationError(
                "Either 'run_id' or 'environments' must be provided. "
                "For environment evals, provide environments=[{'id': 'env-id', 'version_id': 'v1'}]"
            )

        resolved_environments = None
        if environments:
            resolved_environments = [
                {**env, "id": self._resolve_environment_id(env["id"])} if "id" in env else env
                for env in environments
            ]

        payload = {
            "name": name,
            "environments": resolved_environments,
            "suite_id": suite_id,
            "run_id": run_id,
            "model_name": model_name,
            "dataset": dataset,
            "framework": framework,
            "task_type": task_type,
            "description": description,
            "tags": tags or [],
            "metadata": metadata,
            "metrics": metrics,
        }
        payload = {k: v for k, v in payload.items() if v is not None or k in ["tags"]}

        response = self.client.request("POST", "/evaluations/", json=payload)
        return response

    def push_samples(self, evaluation_id: str, samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Push evaluation samples"""
        payload = {"samples": samples}
        response = self.client.request(
            "POST", f"/evaluations/{evaluation_id}/samples", json=payload
        )
        return response

    def finalize_evaluation(
        self, evaluation_id: str, metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Finalize an evaluation with final metrics"""
        payload = {"metrics": metrics} if metrics else {}
        response = self.client.request(
            "POST", f"/evaluations/{evaluation_id}/finalize", json=payload
        )
        return response

    def list_evaluations(
        self,
        environment_id: Optional[str] = None,
        suite_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """List evaluations with optional filters"""
        params: Dict[str, Any] = {"skip": skip, "limit": limit}
        if environment_id:
            params["environment_id"] = environment_id
        if suite_id:
            params["suite_id"] = suite_id

        response = self.client.request("GET", "/evaluations/", params=params)
        return response

    def get_evaluation(self, evaluation_id: str) -> Dict[str, Any]:
        """Get evaluation details by ID"""
        response = self.client.request("GET", f"/evaluations/{evaluation_id}")
        return response

    def get_samples(self, evaluation_id: str, page: int = 1, limit: int = 100) -> Dict[str, Any]:
        """Get samples for an evaluation"""
        params: Dict[str, Any] = {"page": page, "limit": limit}
        response = self.client.request(
            "GET", f"/evaluations/{evaluation_id}/samples", params=params
        )
        return response


class AsyncEvalsClient:
    """Async client for Prime Evals API"""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.client = AsyncAPIClient(api_key=api_key)

    async def _resolve_environment_id(self, env_name: str) -> str:
        """
        Resolve environment ID to owner/name format.

        Raises:
            EvalsAPIError: If the environment does not exist (404)
        """
        if re.match(r"^[^/]+/[^/]+$", env_name):
            env_name = env_name.split("/", 1)[1]

        try:
            resolve_data: Dict[str, Any] = {"name": env_name}

            if self.client.config.team_id:
                resolve_data["team_id"] = self.client.config.team_id

            response = await self.client.post("/environmentshub/resolve", json=resolve_data)
            return response["data"]["id"]

        except APIError as e:
            raise EvalsAPIError(
                f"Environment '{env_name}' does not exist in the hub. "
                f"Please push the environment first with: prime env push {env_name}"
            ) from e

    async def create_evaluation(
        self,
        name: str,
        environments: Optional[List[Dict[str, str]]] = None,
        suite_id: Optional[str] = None,
        run_id: Optional[str] = None,
        model_name: Optional[str] = None,
        dataset: Optional[str] = None,
        framework: Optional[str] = None,
        task_type: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new evaluation

        Either run_id or environments must be provided.
        Environments should be a list of dicts with 'id' and optional 'version_id'.

        Example: [{"id": "simpleqa", "version_id": "v1"}]

        Raises:
            InvalidEvaluationError: If neither run_id nor environments is provided
        """
        if not run_id and not environments:
            raise InvalidEvaluationError(
                "Either 'run_id' or 'environments' must be provided. "
                "For environment evals, provide environments=[{'id': 'env-id', 'version_id': 'v1'}]"
            )

        resolved_environments = None
        if environments:

            async def resolve_env(env: Dict[str, str]) -> Dict[str, str]:
                resolved_env = env.copy()
                if "id" in resolved_env:
                    resolved_env["id"] = await self._resolve_environment_id(resolved_env["id"])
                return resolved_env

            resolved_environments = await asyncio.gather(
                *[resolve_env(env) for env in environments]
            )

        payload = {
            "name": name,
            "environments": resolved_environments,
            "suite_id": suite_id,
            "run_id": run_id,
            "model_name": model_name,
            "dataset": dataset,
            "framework": framework,
            "task_type": task_type,
            "description": description,
            "tags": tags or [],
            "metadata": metadata,
            "metrics": metrics,
        }
        payload = {k: v for k, v in payload.items() if v is not None or k in ["tags"]}

        response = await self.client.request("POST", "/evaluations/", json=payload)
        return response

    async def push_samples(
        self, evaluation_id: str, samples: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Push evaluation samples"""
        payload = {"samples": samples}
        response = await self.client.request(
            "POST", f"/evaluations/{evaluation_id}/samples", json=payload
        )
        return response

    async def finalize_evaluation(
        self, evaluation_id: str, metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Finalize an evaluation with final metrics"""
        payload = {"metrics": metrics} if metrics else {}
        response = await self.client.request(
            "POST", f"/evaluations/{evaluation_id}/finalize", json=payload
        )
        return response

    async def list_evaluations(
        self,
        environment_id: Optional[str] = None,
        suite_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """List evaluations with optional filters"""
        params: Dict[str, Any] = {"skip": skip, "limit": limit}
        if environment_id:
            params["environment_id"] = environment_id
        if suite_id:
            params["suite_id"] = suite_id

        response = await self.client.request("GET", "/evaluations/", params=params)
        return response

    async def get_evaluation(self, evaluation_id: str) -> Dict[str, Any]:
        """Get evaluation details by ID"""
        response = await self.client.request("GET", f"/evaluations/{evaluation_id}")
        return response

    async def get_samples(
        self, evaluation_id: str, page: int = 1, limit: int = 100
    ) -> Dict[str, Any]:
        """Get samples for an evaluation"""
        params: Dict[str, Any] = {"page": page, "limit": limit}
        response = await self.client.request(
            "GET", f"/evaluations/{evaluation_id}/samples", params=params
        )
        return response

    async def aclose(self) -> None:
        """Close the async client"""
        await self.client.aclose()

    async def __aenter__(self) -> "AsyncEvalsClient":
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        await self.aclose()
