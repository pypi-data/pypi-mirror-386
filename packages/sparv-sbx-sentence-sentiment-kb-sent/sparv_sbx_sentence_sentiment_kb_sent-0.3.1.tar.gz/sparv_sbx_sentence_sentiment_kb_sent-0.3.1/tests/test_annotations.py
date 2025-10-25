import pytest
from sbx_sentence_sentiment_kb_sent.annotations import annotate_sentence_sentiment
from sparv import api as sparv_api  # type: ignore [import-untyped]
from sparv_testing import MemoryOutput, MockAnnotation


def test_annotate_sentence_sentiment(snapshot) -> None:  # noqa: ANN001
    output: MemoryOutput = MemoryOutput()
    word = MockAnnotation(
        name="<token>",
        values=[
            "Han",
            "var",
            "glad",
            ".",
            "Rihanna",
            "uppges",
            "gravid",
            ".",
            "Jag",
            "har",
            "ätit",
            "sämre",
            ".",
        ],
    )
    sentence = MockAnnotation(
        name="<sentence>", children={"<token>": [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11, 12]]}
    )

    annotate_sentence_sentiment(output, word, sentence, num_decimals_str="1")

    assert output.values == snapshot


def test_annotate_sentence_sentiment_raises_on_bad_config() -> None:
    with pytest.raises(sparv_api.SparvErrorMessage):
        annotate_sentence_sentiment(None, None, None, num_decimals_str="not an int")
