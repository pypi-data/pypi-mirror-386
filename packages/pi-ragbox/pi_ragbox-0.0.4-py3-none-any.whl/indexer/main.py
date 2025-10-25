"""Main entry point for the indexer service."""

import argparse
import os
import sys
import asyncio
from datasets import load_dataset, Dataset
from data_model import IndexDocument
from .piragbox_indexer import PiRagBoxIndexer
from dotenv import load_dotenv

load_dotenv()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Index data into OpenSearch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--corpus",
        type=str,
        required=True,
        help="The name of the corpus that you want to index",
    )

    parser.add_argument(
        "--hf_dataset",
        type=str,
        required=True,
        help="",
    )

    parser.add_argument(
        "--id",
        type=str,
        help="Id column name in the HF dataset",
    )

    parser.add_argument(
        "--text",
        type=str,
        help="Text column name in the HF dataset",
        required=True,
    )

    parser.add_argument(
        "--embedding",
        type=str,
        help="Embedding column name in the HF dataset",
    )

    parser.add_argument(
        "--aws-profile",
        type=str,
        default=os.getenv("AWS_PROFILE", "ragbox"),
        help="AWS profile name to use (default: 'ragbox' or AWS_PROFILE env var)",
    )

    return parser.parse_args()


def main():
    """Main entry point for the indexer binary."""
    args = parse_args()

    print(f"Loaded HF dataset: {args.hf_dataset}")
    ds: Dataset = load_dataset(args.hf_dataset, split="train")  # type: ignore

    documents = [
        IndexDocument(
            id=str(ex[args.id]) if args.id else None,
            text=str(ex[args.text]),
            embedding=ex[args.embedding] if args.embedding else None,
        )
        for ex in ds
    ]

    async def _run() -> None:
        async with PiRagBoxIndexer() as indexer:
            await indexer.index_corpus(documents=documents, corpus_name=args.corpus)
            corpora = await indexer.list_corpora()
            print(f"Here are current available corpora: {', '.join(corpora)}")

    asyncio.run(_run())


if __name__ == "__main__":
    sys.exit(main())
