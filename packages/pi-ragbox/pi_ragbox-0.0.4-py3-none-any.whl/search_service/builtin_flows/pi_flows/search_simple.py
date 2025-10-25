from __future__ import annotations

import json

from data_model import (
    Params,
    PiPrompt,
    SearchQuery,
    SearchResults,
    pi_parallel_retrieval,
)
from data_model.piragbox_model import piragbox


@piragbox(params={"corpus_name": "monday"})
async def search_simple(
    query: SearchQuery,
    ranking_params: Params,
) -> SearchResults:

    search_results = await pi_parallel_retrieval(
        query,
        query_param_list=[
            {"kind": "keyword", "corpus": ranking_params.corpus_name},
            {"kind": "dense", "corpus": ranking_params.corpus_name},
        ],
        require_success=True,
    )

    base_prompts = [
        PiPrompt(
            name="relevance",
            prompt="Is the response relevant to the input search query?",
        ),
    ]

    # ADD PI SIGNALS
    await search_results.add_pi_features(
        prompts=base_prompts,
        pi_input_builder=lambda doc, query: json.dumps(
            {"input": query, "response": doc.content}, indent=2
        ),
        pi_input_builder_kwargs={"query": query.query},
    )

    search_results.score(scoring_fn=lambda doc: doc.features["relevance"])

    return search_results
