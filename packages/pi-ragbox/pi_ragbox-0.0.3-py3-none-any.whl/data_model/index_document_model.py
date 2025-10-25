import hashlib
from typing import Any, Iterable, TYPE_CHECKING

from pydantic import BaseModel, model_validator

if TYPE_CHECKING:
    from clients.embedding_client import OpenAIEmbedder


class CorpusIndexDocument(BaseModel):
    id: str | None = None
    corpus_domain: str
    corpus_name: str

    @model_validator(mode="after")
    def _set_id(self) -> "CorpusIndexDocument":
        self.id = f"{self.corpus_domain}__%__{self.corpus_name}"
        return self


class IndexDocument(BaseModel):
    id: str | None = None
    text: str
    embedding: list[float] | None = None

    async def materialize(self, embedder: "OpenAIEmbedder") -> dict[str, Any]:
        """Return a fully populated document payload ready for indexing."""
        document_id = self.id or hashlib.sha256(self.text.encode("utf-8")).hexdigest()

        document_embedding = self.embedding
        if document_embedding is None:
            document_embedding = await embedder.embed(self.text)

        return {
            "id": document_id,
            "text": self.text,
            "embedding": document_embedding,
        }

    @classmethod
    async def materialize_many(
        cls,
        documents: Iterable["IndexDocument"],
        embedder: "OpenAIEmbedder",
    ) -> list[dict[str, Any]]:
        """Return fully populated document payloads ready for indexing."""
        docs = list(documents)
        if not docs:
            return []

        texts_to_embed: list[str] = []
        for document in docs:
            if document.embedding is None:
                texts_to_embed.append(document.text)

        embeddings: list[list[float]] = []
        if texts_to_embed:
            embeddings = await embedder.embed_batch(texts_to_embed)

        embedded_cursor = 0
        materialized: list[dict[str, Any]] = []
        for document in docs:
            embedding = document.embedding
            if embedding is None:
                embedding = embeddings[embedded_cursor]
                embedded_cursor += 1

            document_id = (
                document.id or hashlib.sha256(document.text.encode("utf-8")).hexdigest()
            )

            materialized.append(
                {
                    "id": document_id,
                    "text": document.text,
                    "embedding": embedding,
                }
            )

        if embedded_cursor != len(embeddings):
            raise RuntimeError("embed_batch returned unexpected number of embeddings")

        return materialized


class IndexingRequest(BaseModel):
    documents: list[IndexDocument]
    corpus_name: str


class DeleteCorpusRequest(BaseModel):
    corpus_name: str
