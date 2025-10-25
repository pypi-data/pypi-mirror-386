from __future__ import annotations

import os
from collections.abc import Mapping
from contextlib import AbstractAsyncContextManager
from typing import Any, List

import httpx

DEFAULT_PI_SCORER_URL = "https://api.withpi.ai/v1/scoring_system/score"


class PiScorerClient(AbstractAsyncContextManager["PiScorerClient"]):
    _score_url: str
    _api_key: str
    _timeout: float | httpx.Timeout | None
    _client: httpx.AsyncClient | None

    def __init__(
        self,
        score_url: str | None = None,
        api_key: str | None = None,
        timeout: float | httpx.Timeout | None = 10.0,
    ) -> None:
        self._score_url = score_url or DEFAULT_PI_SCORER_URL
        self._api_key = api_key or os.getenv("WITHPI_API_KEY", "")
        self._timeout = timeout
        self._client = None

    async def score(
        self,
        llm_input: str,
        llm_output: str,
        scoring_spec: List[Mapping[str, Any]],
        hotswaps: str | None = None,
        model_override: str | None = None,
    ) -> dict[str, float]:
        if self._client is None:
            raise RuntimeError(
                "PiScorerClient must be used as an async context manager. "
                "Use 'async with PiScorerClient(...) as client:'"
            )

        headers = {
            "x-api-key": self._api_key,
        }
        if hotswaps:
            headers["x-hotswaps"] = hotswaps
        if model_override:
            headers["x-model-override"] = model_override

        response = await self._client.post(
            self._score_url,
            headers=headers,
            json={
                "llm_input": llm_input,
                "llm_output": llm_output,
                "scoring_spec": scoring_spec,
            },
        )
        response.raise_for_status()
        result = response.json()
        question_scores = result["question_scores"]
        question_scores["total_score"] = result
        return question_scores

    async def __aenter__(self) -> PiScorerClient:
        self._client = httpx.AsyncClient(timeout=self._timeout, http2=True, limits=httpx.Limits(max_connections=200, keepalive_expiry=60, max_keepalive_connections=200))
        return self

    async def __aexit__(self, *exc_info) -> None:
        if self._client is not None:
            await self._client.aclose()
