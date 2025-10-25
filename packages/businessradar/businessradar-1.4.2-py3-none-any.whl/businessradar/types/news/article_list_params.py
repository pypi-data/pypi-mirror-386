# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import datetime
from typing_extensions import Literal, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = ["ArticleListParams"]


class ArticleListParams(TypedDict, total=False):
    category: SequenceNotStr[str]
    """Category ID to filter articles"""

    company: SequenceNotStr[str]
    """Company ID's"""

    country: SequenceNotStr[str]
    """ISO 2-letter Country Code"""

    disable_company_article_deduplication: bool
    """
    By default companies with the same trade names are grouped and the best one is
    picked, the other ones are not included. By disabling this the amount of company
    articles will grow significantly.
    """

    duns_number: SequenceNotStr[str]
    """9-digit Dun And Bradstreet Number"""

    global_ultimate: SequenceNotStr[str]
    """9-digit Dun And Bradstreet Number"""

    include_clustered_articles: bool
    """Include clustered articles"""

    language: SequenceNotStr[str]
    """ISO 2-letter Language Code"""

    max_creation_date: Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]
    """Filter articles created before this date"""

    max_publication_date: Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]
    """Filter articles published before this date"""

    min_creation_date: Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]
    """Filter articles created after this date"""

    min_publication_date: Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]
    """Filter articles published after this date"""

    next_key: str
    """
    The next_key is an cursor used to make it possible to paginate to the next
    results, pass the next_key from the previous request to retrieve next results.
    """

    portfolio_id: SequenceNotStr[str]
    """Portfolio ID to filter articles"""

    query: str
    """Custom search filters to text search all articles."""

    registration_number: SequenceNotStr[str]
    """Local Registration Number"""

    saved_article_filter_id: str
    """Filter articles on already saved article filter id"""

    sentiment: bool
    """Filter articles with sentiment"""

    sorting: Literal[
        "creation_date",
        "publication_date_clustering",
        "publication_date_priority",
        "publication_date_source_references",
        "publication_datetime",
    ]
    """Sort articles"""

    sorting_order: Literal["asc", "desc"]
    """Sort order"""
