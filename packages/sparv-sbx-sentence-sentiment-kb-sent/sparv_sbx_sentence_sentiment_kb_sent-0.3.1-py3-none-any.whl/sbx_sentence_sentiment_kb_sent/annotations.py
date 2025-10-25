"""Sparv annotator for sentiment analysis on sentences."""

from sparv import api as sparv_api  # type: ignore [import-untyped]

from sbx_sentence_sentiment_kb_sent.constants import PROJECT_NAME

logger = sparv_api.get_logger(__name__)


@sparv_api.annotator("Sentiment analysis of sentences", language=["swe"])
def annotate_sentence_sentiment(
    out_sentence_sentiment: sparv_api.Output = sparv_api.Output(
        f"<sentence>:{PROJECT_NAME}.sentence-sentiment--kb-sent",
        # cls="sbx_sentence_sentiment_kb_sent",
        description="Sentiment analysis of sentence with KBLab/robust-swedish-sentiment-multiclass",  # noqa: E501
    ),
    word: sparv_api.Annotation = sparv_api.Annotation("<token:word>"),
    sentence: sparv_api.Annotation = sparv_api.Annotation("<sentence>"),
    num_decimals_str: str = sparv_api.Config(f"{PROJECT_NAME}.num_decimals"),
) -> None:
    """Sentiment analysis of sentence with KBLab/robust-swedish-sentiment-multiclass."""
    from sbx_sentence_sentiment_kb_sent.sentiment_analyzer import (  # noqa: PLC0415
        SentimentAnalyzer,
    )

    try:
        num_decimals = int(num_decimals_str)
    except ValueError as exc:
        raise sparv_api.SparvErrorMessage(
            f"'{PROJECT_NAME}.num_decimals' must contain an 'int' got: '{num_decimals_str}'"
        ) from exc
    sentences, _orphans = sentence.get_children(word)
    token_word = list(word.read())
    out_sentence_sentiment_annotation = sentence.create_empty_attribute()

    analyzer = SentimentAnalyzer(num_decimals=num_decimals)

    logger.progress(total=len(sentences))  # type: ignore
    for sent_i, sent in enumerate(sentences):
        sent_to_tag = [token_word[token_index] for token_index in sent]
        out_sentence_sentiment_annotation[sent_i] = analyzer.analyze_sentence(sent_to_tag)
        logger.debug("annotation[%d]=%s", sent_i, out_sentence_sentiment_annotation[sent_i])

    out_sentence_sentiment.write(out_sentence_sentiment_annotation)
