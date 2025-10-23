from typing import Generic

from hgraph._operators._operators import CmpResult
from hgraph._types._ref_type import REF
from hgraph._types._scalar_types import SIZE
from hgraph._types._time_series_types import TIME_SERIES_TYPE, OUT
from hgraph._types._ts_type import TS
from hgraph._types._tsb_type import TSB, TimeSeriesSchema
from hgraph._types._tsl_type import TSL
from hgraph._types._type_meta_data import AUTO_RESOLVE
from hgraph._wiring._decorators import operator

__all__ = ("merge", "all_", "any_", "race", "BoolResult", "if_", "route_by_index", "if_true", "if_then_else", "if_cmp")


@operator
def merge(*tsl: TSL[TIME_SERIES_TYPE, SIZE], **kwargs) -> TIME_SERIES_TYPE:
    """
    Selects and returns the first of the values that tick (are modified) in the list provided.
    If more than one input is modified in the engine-cycle, it will return the first one that ticked in order of the
    list.
    if the inputs are TSDs:
    * If keys from multiple of the TSDs tick in the same cycle, the output will contain all the unique keys.
    * If the ticking keys are the same, the first value is returned in order of the list.
    * If `disjoint` is set True, the TSDs are assumed to have non-overlapping keys.  This parameter should be set
        True to optimise performance when merging disjoint TSDs.
    """


@operator
def race(*tsl: TSL[TIME_SERIES_TYPE, SIZE]) -> TIME_SERIES_TYPE:
    """
    Forwards the first of the values that are valid in the list provided.  If the first item becomes invalid
    then the next item to be valid is forwarded.
    """


@operator
def all_(*args: TSL[TS[bool], SIZE]) -> TS[bool]:
    """
    Graph version of python `all` operator
    """


@operator
def any_(*args: TSL[TS[bool], SIZE]) -> TS[bool]:
    """
    Graph version of python `any` operator
    """


class BoolResult(TimeSeriesSchema, Generic[TIME_SERIES_TYPE]):
    true: REF[TIME_SERIES_TYPE]
    false: REF[TIME_SERIES_TYPE]


@operator
def if_(condition: TS[bool], ts: TIME_SERIES_TYPE = AUTO_RESOLVE) -> TSB[BoolResult[TIME_SERIES_TYPE]]:
    """
    Forwards a timeseries value to one of two bundle outputs: "true" or "false", according to whether
    the condition is true or false
    """


@operator
def route_by_index(index_ts: TS[int], ts: TIME_SERIES_TYPE) -> TSL[TIME_SERIES_TYPE, SIZE]:
    """
    Forwards a timeseries value to the 'nth' output according to the value of index_ts
    """


@operator
def if_true(condition: TS[bool], tick_once_only: bool = False) -> TS[bool]:
    """
    Emits a tick with value True when the input condition ticks with True.
    If tick_once_only is True then this will only tick once, otherwise this will tick with every tick of the condition,
    when the condition is True.
    """


@operator
def if_then_else(condition: TS[bool], true_value: TIME_SERIES_TYPE, false_value: TIME_SERIES_TYPE) -> TIME_SERIES_TYPE:
    """
    If the condition is true the output ticks with the true_value, otherwise it ticks with the false_value.
    """


@operator
def if_cmp(cmp: TS[CmpResult], lt: OUT, eq: OUT, gt: OUT) -> OUT:
    """
    Performs a comparison between two time series values (``lhs`` and ``rhs``), then depending on the result
    will select the time-series of interest. That is:
    ::
        if lhs < rhs:
            return lt
        if lhs == rhs:
            return eq
        if lhs > rhs:
            return gt
    """
