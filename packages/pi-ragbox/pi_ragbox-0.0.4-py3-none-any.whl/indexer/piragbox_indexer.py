from __future__ import annotations

from data_model import DeleteCorpusRequest, IndexDocument, IndexingRequest
from clients import IndexingClient
from tqdm import tqdm

BATCH_SIZE = 100


class PiRagBoxIndexer:
    def __init__(self) -> None:
        self._client = IndexingClient()
        self._has_active_client = False

    async def __aenter__(self) -> PiRagBoxIndexer:
        await self._client.__aenter__()
        self._has_active_client = True
        return self

    async def __aexit__(self, *exc_info) -> None:
        if self._has_active_client:
            await self._client.__aexit__(*exc_info)
            self._has_active_client = False

    def _get_client(self) -> IndexingClient:
        if not self._has_active_client:
            raise RuntimeError(
                "PiRagBoxIndexer must be used as an async context manager. "
                "Use 'async with PiRagBoxIndexer() as indexer:'"
            )
        return self._client

    async def index(self, document: IndexDocument, corpus_name: str) -> None:
        client = self._get_client()
        await client.index(
            IndexingRequest(
                documents=[document],
                corpus_name=corpus_name,
            )
        )

    async def index_batch(
        self, documents: list[IndexDocument], corpus_name: str
    ) -> None:
        client = self._get_client()
        if not documents:
            return

        with tqdm(
            total=len(documents),
            desc=f"Indexing corpus {corpus_name}",
            unit="doc",
        ) as progress:
            for start in range(0, len(documents), BATCH_SIZE):
                batch = documents[start : start + BATCH_SIZE]
                await client.index(
                    IndexingRequest(
                        documents=batch,
                        corpus_name=corpus_name,
                    )
                )
                progress.update(len(batch))

    async def index_corpus(
        self, documents: list[IndexDocument], corpus_name: str
    ) -> None:
        """
        Create index for the given corpus and index all provided documents.

        Args:
            documents: Iterable of index documents to index
            corpus_name: Name of the corpus (used as index name)
        """
        client = self._get_client()
        await client.delete_corpus(DeleteCorpusRequest(corpus_name=corpus_name))

        await self.index_batch(documents, corpus_name)

    async def delete_index(self, corpus_name: str) -> None:
        """
        Delete the OpenSearch index associated with the provided corpus name.

        Args:
            corpus_name: Name of the corpus (used as index name)
        """
        client = self._get_client()
        await client.delete_corpus(DeleteCorpusRequest(corpus_name=corpus_name))

    async def list_corpora(self) -> list[str]:
        client = self._get_client()
        return await client.list_corpora()
