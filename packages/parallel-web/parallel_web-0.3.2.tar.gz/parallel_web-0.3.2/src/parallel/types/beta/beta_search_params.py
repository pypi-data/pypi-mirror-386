# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Optional
from typing_extensions import Literal, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo
from .parallel_beta_param import ParallelBetaParam
from ..shared_params.source_policy import SourcePolicy

__all__ = ["BetaSearchParams"]


class BetaSearchParams(TypedDict, total=False):
    max_chars_per_result: Optional[int]
    """
    Upper bound on the number of characters to include in excerpts for each search
    result.
    """

    max_results: Optional[int]
    """Upper bound on the number of results to return.

    May be limited by the processor. Defaults to 10 if not provided.
    """

    objective: Optional[str]
    """Natural-language description of what the web search is trying to find.

    May include guidance about preferred sources or freshness. At least one of
    objective or search_queries must be provided.
    """

    processor: Optional[Literal["base", "pro"]]
    """Search processor."""

    search_queries: Optional[SequenceNotStr[str]]
    """Optional list of traditional keyword search queries to guide the search.

    May contain search operators. At least one of objective or search_queries must
    be provided.
    """

    source_policy: Optional[SourcePolicy]
    """Source policy for web search results.

    This policy governs which sources are allowed/disallowed in results.
    """

    betas: Annotated[List[ParallelBetaParam], PropertyInfo(alias="parallel-beta")]
    """Optional header to specify the beta version(s) to enable."""
