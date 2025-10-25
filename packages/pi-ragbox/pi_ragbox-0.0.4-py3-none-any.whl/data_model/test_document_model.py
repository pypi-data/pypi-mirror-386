from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest
from data_model import Document, PiPrompt, SearchQuery, SearchResults, set_ctx
from pydantic import ValidationError


def make_doc(docid: str, score: float = 0.0, **content: object) -> Document:
    if not content:
        content = {"field": docid}
    return Document(
        docid=docid,  # type: ignore
        content=content,
        score=score,
    )


def test_document_is_frozen():
    doc = make_doc("doc-1")
    with pytest.raises(ValidationError):
        doc.docid = "mutated"  # type: ignore


def test_results_property_returns_copy():
    doc = make_doc("doc-1")
    results = SearchResults(results=[doc])

    returned = results.results
    returned.append(make_doc("doc-2"))

    assert len(results.results) == 1
    assert results.results[0].docid == "doc-1"


def test_results_assignment_is_blocked():
    results = SearchResults(results=[make_doc("doc-1")])

    with pytest.raises(AttributeError):
        results.results = []  # type: ignore

    with pytest.raises(AttributeError):
        results.results_data = [make_doc("doc-2")]


def test_search_results_add_trace_applies_to_all_documents():
    docs = [make_doc("doc-1", score=0.1), make_doc("doc-2", score=0.2)]
    results = SearchResults(results=docs)

    returned = results.add_trace(None)
    assert returned is results
    assert all(doc.traces == [] for doc in docs)

    results.add_trace("initial trace")
    results.add_trace(lambda doc: f"score={doc.score}")

    assert docs[0].traces == ["initial trace", "score=0.1"]
    assert docs[1].traces == ["initial trace", "score=0.2"]


def test_filter_applies_predicate_and_kwargs():
    docs = [
        make_doc("doc-low", score=0.1),
        make_doc("doc-high", score=0.9),
    ]
    results = SearchResults(results=docs)

    def above_threshold(document: Document, threshold: float) -> bool:
        return document.score >= threshold

    filtered = results.filter(
        above_threshold,  # type: ignore
        fn_kwargs={"threshold": 0.5},
    )

    assert filtered is results
    assert [doc.docid for doc in results.results] == ["doc-high"]
    assert results.results[0].docid == "doc-high"


def test_score_creates_new_documents_and_sorts():
    doc_low = make_doc("doc-low", score=0.1)
    doc_high = make_doc("doc-high", score=0.9)
    results = SearchResults(results=[doc_low, doc_high])

    def boost_low(document: Document, boost: float) -> float:
        if document.docid == "doc-low":
            return document.score + boost
        return document.score

    scored = results.score(
        boost_low,  # type: ignore
        fn_kwargs={"boost": 1.0},
    )

    assert scored is results
    assert [doc.docid for doc in results.results] == ["doc-low", "doc-high"]
    assert results.results[0] is not doc_low
    assert results.results[1] is not doc_high
    assert next(doc for doc in results.results if doc.docid == "doc-low").score == 1.1
    assert next(doc for doc in results.results if doc.docid == "doc-high").score == 0.9
    assert doc_low.score == 0.1
    assert doc_high.score == 0.9


def test_merge_deduplicates_and_preserves_order():
    doc_a_first = make_doc("doc-a", score=0.1)
    doc_b = make_doc("doc-b", score=0.2)
    doc_a_second = make_doc("doc-a", score=1.0)
    doc_c = make_doc("doc-c", score=0.3)

    left = SearchResults(results=[doc_a_first, doc_b])
    right = SearchResults(results=[doc_a_second, doc_c])

    merged = left.merge(right)

    assert [doc.docid for doc in merged.results] == ["doc-a", "doc-b", "doc-c"]
    assert merged.results[0] is doc_a_first
    assert merged.results[1] is doc_b
    assert merged.results[2] is doc_c


def test_merge_combines_features_and_retrievals():
    left_query = SearchQuery(query="left-query", limit=3)
    right_query = SearchQuery(query="right-query", limit=5)

    doc_left = Document(
        docid="doc-a",  # type: ignore
        content={"field": "left"},
        score=0.1,
        features={"left": 0.1, "shared": 0.2},
        retrievals=[left_query],
    )
    doc_right = Document(
        docid="doc-a",  # type: ignore
        content={"field": "right"},
        score=0.9,
        features={"shared": 0.9, "right": 0.3},
        retrievals=[left_query, right_query],
    )

    merged = SearchResults(results=[doc_left]).merge(SearchResults(results=[doc_right]))

    assert merged.results[0] is doc_left
    assert doc_left.features == {"left": 0.1, "shared": 0.9, "right": 0.3}
    assert doc_left.retrievals == [left_query, right_query]


def test_add_pi_features_updates_documents_with_client_scores():
    docs = [make_doc("doc-1"), make_doc("doc-2")]
    results = SearchResults(results=docs)

    builder_calls: list[tuple[str, str]] = []

    def builder(document: Document, suffix: str) -> str:
        builder_calls.append((document.docid, suffix))
        return f"{document.docid}{suffix}"

    prompts = [
        PiPrompt(name="quality", prompt="Rate the document quality."),
        PiPrompt(name="relevance", prompt="Rate the document relevance.", weight=0.7),
    ]

    class StubPiClient:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []
            self.next_score = 0.1

        async def score(
            self,
            *,
            llm_input: str,
            llm_output: str,
            scoring_spec: list[dict[str, object]],
            hotswaps: str | None = None,
            model_override: str | None = None,
        ) -> dict[str, float]:
            self.calls.append(
                {
                    "llm_input": llm_input,
                    "llm_output": llm_output,
                    "scoring_spec": scoring_spec,
                    "hotswaps": hotswaps,
                    "model_override": model_override,
                }
            )
            score = self.next_score
            self.next_score += 0.1
            return {
                **{
                    prompt.name: score + (index + 1) * 0.01
                    for index, prompt in enumerate(prompts)
                },
            }

    client = StubPiClient()

    @dataclass
    class MockAppStateHolder:
        pi_scorer_client: object = None

    set_ctx(MockAppStateHolder(pi_scorer_client=client))

    updated = asyncio.run(
        results.add_pi_features(
            prompts=prompts,
            pi_input_builder=builder,  # type: ignore
            pi_input_builder_kwargs={"suffix": "-payload"},
            hotswaps="hotswap-setting",
            model_override="pi-model",
        )
    )

    assert updated is results
    assert builder_calls == [("doc-1", "-payload"), ("doc-2", "-payload")]
    assert len(client.calls) == 2
    assert all(call["llm_input"] == "" for call in client.calls)
    assert [call["llm_output"] for call in client.calls] == [
        "doc-1-payload",
        "doc-2-payload",
    ]
    print(list(call["scoring_spec"] for call in client.calls))
    print(
        [
            {"question": prompt.prompt, "label": prompt.name, "weight": prompt.weight}
            for prompt in prompts
        ]
    )
    assert all(
        call["scoring_spec"]
        == [
            {"question": prompt.prompt, "label": prompt.name, "weight": prompt.weight}
            for prompt in prompts
        ]
        for call in client.calls
    )
    assert all(call["hotswaps"] == "hotswap-setting" for call in client.calls)
    assert all(call["model_override"] == "pi-model" for call in client.calls)

    annotated_docs = results.results
    assert [doc.features[prompts[0].name] for doc in annotated_docs] == pytest.approx(
        [0.11, 0.21]
    )
    assert [doc.features[prompts[1].name] for doc in annotated_docs] == pytest.approx(
        [0.12, 0.22]
    )
    assert annotated_docs[0] is not docs[0]
    assert annotated_docs[1] is not docs[1]
    for prompt in prompts:
        assert all(prompt.name not in original.features for original in docs)
