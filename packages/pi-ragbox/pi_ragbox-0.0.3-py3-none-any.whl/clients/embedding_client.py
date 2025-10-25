import os
from typing import Any

from openai import AsyncAzureOpenAI
from pydantic import BaseModel


class Embedder(BaseModel):
    dimensions: int

    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError()


class OpenAIEmbedder(Embedder):
    model: str

    def model_post_init(self, __context: Any) -> None:
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        if not azure_endpoint or not azure_api_key:
            raise ValueError(
                "AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set"
            )

        self._client = AsyncAzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=azure_api_key,
            api_version="2024-10-21",
        )

    async def embed(self, text: str) -> list[float]:
        response = await self._client.embeddings.create(
            input=text,
            model=self.model,
            dimensions=self.dimensions,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        response = await self._client.embeddings.create(
            input=texts,
            model=self.model,
            dimensions=self.dimensions,
        )
        return [item.embedding for item in response.data]
