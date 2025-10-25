"""Sparv plugin for annotating sentences with sentiment analysis."""

import warnings

from sparv import api as sparv_api  # type: ignore [import-untyped]

from sbx_sentence_sentiment_kb_sent.annotations import annotate_sentence_sentiment
from sbx_sentence_sentiment_kb_sent.constants import PROJECT_NAME

__all__ = ["annotate_sentence_sentiment"]

__description__ = "Annotate sentence with sentiment analysis."
__version__ = "0.3.1"

__config__ = [
    sparv_api.Config(
        f"{PROJECT_NAME}.num_decimals",
        description="The number of decimals to round the score to",
        default=3,
    ),
]
warnings.warn(
    "This package has changed name to sparv-sbx-sentiment-kb-sent, please install https://pypi.org/project/sparv-sbx-sentiment-kb-sent instead",  # noqa: E501
    UserWarning,
    stacklevel=1,
)
