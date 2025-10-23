from collections import deque
from typing import Mapping, Type, Tuple

from frozendict import frozendict

from hgraph._types import (
    TS,
    SCALAR,
    STATE,
    OUT,
    KEYABLE_SCALAR,
    DEFAULT,
    TIME_SERIES_TYPE,
    SIGNAL,
    TS_OUT,
    TSB,
    V,
    SIZE,
    TSL,
    TSD,
    TS_SCHEMA,
)
from hgraph._operators import emit, convert, collect
from hgraph._wiring import compute_node
from hgraph._impl._operators._conversion_operators._conversion_operator_util import _BufferState, KeyValue
from hgraph._runtime._constants import MIN_TD
from hgraph._runtime._node import SCHEDULER

__all__ = ()


@compute_node(
    overloads=convert,
    requires=lambda m, s: m[OUT].py_type in (TS[Mapping], TS[dict], TS[frozendict])
    or m[OUT].matches_type(TS[Mapping[m[KEYABLE_SCALAR].py_type, m[SCALAR].py_type]]),
)
def convert_ts_to_mapping(
    key: TS[KEYABLE_SCALAR], ts: TS[SCALAR], to: Type[OUT] = DEFAULT[OUT]
) -> TS[Mapping[KEYABLE_SCALAR, SCALAR]]:
    return {key.value: ts.value}


@compute_node(
    overloads=convert,
    requires=lambda m, s: m[OUT].py_type in (TS[Mapping], TS[dict], TS[frozendict])
    or m[OUT].matches_type(TS[Mapping[m[KEYABLE_SCALAR].py_type, m[SCALAR].py_type]]),
)
def convert_tuples_to_mapping(
    key: TS[Tuple[KEYABLE_SCALAR, ...]], ts: TS[Tuple[SCALAR, ...]], to: Type[OUT] = DEFAULT[OUT]
) -> TS[Mapping[KEYABLE_SCALAR, SCALAR]]:
    if len(key.value) != len(ts.value):
        raise ValueError(f"Length mismatch: {len(key.value)} != {len(ts.value)}")

    return {k: v for k, v in zip(key.value, ts.value)}


@compute_node(
    overloads=convert,
    requires=lambda m, s: m[OUT].py_type in (TS[Mapping], TS[dict], TS[frozendict])
    or m[OUT].matches_type(TS[Mapping[m[KEYABLE_SCALAR].py_type, m[SCALAR].py_type]]),
    resolvers={KEYABLE_SCALAR: lambda m, s: int, SCALAR: lambda m, s: m[TIME_SERIES_TYPE].scalar_type()},
)
def convert_tsl_to_mapping(
    ts: TSL[TIME_SERIES_TYPE, SIZE], to: Type[OUT] = DEFAULT[OUT]
) -> TS[Mapping[KEYABLE_SCALAR, SCALAR]]:
    return {k: ts.value for k, ts in enumerate(ts)}


@compute_node(
    overloads=convert,
    requires=lambda m, s: m[OUT].py_type in (TS[Mapping], TS[dict], TS[frozendict])
    or m[OUT].matches_type(TS[Mapping[m[KEYABLE_SCALAR].py_type, m[SCALAR].py_type]]),
    resolvers={SCALAR: lambda m, s: m[TIME_SERIES_TYPE].scalar_type()},
)
def convert_tsd_to_mapping(
    ts: TSD[KEYABLE_SCALAR, TIME_SERIES_TYPE], to: Type[OUT] = DEFAULT[OUT]
) -> TS[Mapping[KEYABLE_SCALAR, SCALAR]]:
    return ts.value


@compute_node(
    overloads=convert,
    requires=lambda m, s: m[OUT].matches_type(TS[Mapping[str, m[SCALAR].py_type]])
    and all(m[SCALAR].matches(v.scalar_type()) for v in m[TS_SCHEMA].meta_data_schema.values()),
    resolvers={SCALAR: lambda m, s: m[OUT].value_scalar_tp.value_type},
    all_valid=lambda m, s: ("ts",) if s["__strict__"] else None,
)
def convert_tsb_to_mapping(
    ts: TSB[TS_SCHEMA], to: Type[OUT] = DEFAULT[OUT], __strict__: bool = False
) -> TS[Mapping[str, SCALAR]]:
    return ts.value


@compute_node(
    overloads=convert,
    requires=lambda m, s: m[OUT].matches_type(TS[Mapping[str, m[SCALAR].py_type]])
    and all(m[SCALAR].matches(v.scalar_type()) for v in m[TS_SCHEMA].meta_data_schema.values()),
    resolvers={SCALAR: lambda m, s: m[OUT].value_scalar_tp.value_type},
    all_valid=lambda m, s: ("ts",) if s["__strict__"] else None,
)
def convert_tsb_to_mapping(
    to: Type[OUT] = DEFAULT[OUT], __strict__: bool = False, **ts: TSB[TS_SCHEMA]
) -> TS[Mapping[str, SCALAR]]:
    return frozendict(ts.value)


@compute_node(
    overloads=collect,
    requires=lambda m, s: m[OUT].py_type in (TS[Mapping], TS[dict], TS[frozendict])
    or m[OUT].matches_type(TS[Mapping[m[KEYABLE_SCALAR].py_type, m[SCALAR].py_type]]),
    valid=("key", "ts"),
)
def collect_mapping(
    key: TS[KEYABLE_SCALAR],
    ts: TS[SCALAR],
    *,
    reset: SIGNAL = None,
    tp_: Type[OUT] = DEFAULT[OUT],
    _output: TS_OUT[Mapping[KEYABLE_SCALAR, SCALAR]] = None,
) -> TS[Mapping[KEYABLE_SCALAR, SCALAR]]:
    prev = _output.value if _output.valid and not reset.modified else {}
    new = {key.value: ts.value} if ts.modified else {}
    return prev | new


@compute_node(
    overloads=collect,
    requires=lambda m, s: m[OUT].py_type in (TS[Mapping], TS[dict], TS[frozendict])
    or m[OUT].matches_type(TS[Mapping[m[KEYABLE_SCALAR].py_type, m[SCALAR].py_type]]),
    valid=("key", "ts"),
)
def collect_mapping_from_tuples(
    key: TS[Tuple[KEYABLE_SCALAR, ...]],
    ts: TS[Tuple[SCALAR, ...]],
    *,
    reset: SIGNAL = None,
    tp_: Type[OUT] = DEFAULT[OUT],
    _output: TS_OUT[Mapping[KEYABLE_SCALAR, SCALAR]] = None,
) -> TS[Mapping[KEYABLE_SCALAR, SCALAR]]:
    prev = _output.value if _output.valid and not reset.modified else {}
    new = {k: v for k, v in zip(key.value, ts.value)} if ts.modified or key.modified else {}
    return prev | new


@compute_node(overloads=emit, resolvers={OUT: lambda m, s: TS[m[SCALAR].py_type]})
def emit_mapping(
    ts: TS[Mapping[KEYABLE_SCALAR, SCALAR]],
    v_: Type[V] = DEFAULT[OUT],
    _state: STATE[_BufferState] = None,
    _schedule: SCHEDULER = None,
) -> TSB[KeyValue[KEYABLE_SCALAR, V]]:
    """
    Converts a tuple of KeyValue values in a stream of individual SCALAR values.
    """
    if ts.modified:
        _state.buffer.extend(ts.value.items())

    if _state.buffer:
        d: deque[SCALAR] = _state.buffer
        k, v = d.popleft()
        if d:
            _schedule.schedule(MIN_TD)
        return {"key": k, "value": v}
