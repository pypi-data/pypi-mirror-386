from typing import cast, TYPE_CHECKING, Any, Mapping

from frozendict import frozendict

from hgraph._types._scalar_type_meta_data import HgScalarTypeMetaData
from hgraph._types._scalar_types import SCALAR
from hgraph._types._time_series_types import TIME_SERIES_TYPE
from hgraph._wiring._decorators import pull_source_node
from hgraph._wiring._wiring_node_class._wiring_node_class import BaseWiringNodeClass
from hgraph._wiring._wiring_node_class._wiring_node_class import WiringNodeClass
from hgraph._wiring._wiring_node_instance import create_wiring_node_instance, WiringNodeInstanceContext

if TYPE_CHECKING:
    from hgraph._builder._node_builder import NodeBuilder
    from hgraph._wiring._wiring_node_class import WiringNodeSignature
    from hgraph._runtime._node import NodeSignature

__all__ = ("last_value_source_node",)


@pull_source_node
def _source_node_signature() -> TIME_SERIES_TYPE: ...


def last_value_source_node(name: str, tp: type[TIME_SERIES_TYPE], default: SCALAR = None) -> TIME_SERIES_TYPE:
    changes = {"name": name}
    inputs = {}
    if default is not None:
        default_type = HgScalarTypeMetaData.parse_value(default)
        changes["args"] = tuple(["default"])
        changes["input_types"] = frozendict({"default": default_type})
        inputs["default"] = default
    signature = (
        cast(WiringNodeClass, _source_node_signature[TIME_SERIES_TYPE:tp]).resolve_signature().copy_with(**changes)
    )
    # Source node need to be unique, use an object instance as the fn arg to ensure uniqueness
    from hgraph._wiring._context_wiring import TimeSeriesContextTracker

    return create_wiring_node_instance(
        node=PythonLastValuePullWiringNodeClass(signature, object()),
        resolved_signature=signature,
        inputs=frozendict(inputs),
    )


class PythonLastValuePullWiringNodeClass(BaseWiringNodeClass):

    def create_node_builder_instance(
        self,
        resolved_wiring_signature: "WiringNodeSignature",
        node_signature: "NodeSignature",
        scalars: Mapping[str, Any],
    ) -> "NodeBuilder":
        if PythonLastValuePullWiringNodeClass.BUILDER_CLASS is None:
            from hgraph._impl._builder._node_builder import PythonLastValuePullNodeBuilder

            PythonLastValuePullWiringNodeClass.BUILDER_CLASS = PythonLastValuePullNodeBuilder

        from hgraph import TimeSeriesBuilderFactory

        factory: TimeSeriesBuilderFactory = TimeSeriesBuilderFactory.instance()
        output_type = node_signature.time_series_output
        assert output_type is not None, "PythonLastValuePullWiringNodeClass must have a time series output"
        return PythonLastValuePullWiringNodeClass.BUILDER_CLASS(
            signature=node_signature,
            scalars=scalars,
            input_builder=None,
            output_builder=factory.make_output_builder(output_type),
            error_builder=(
                factory.make_error_builder(self.error_output_type) if node_signature.capture_exception else None
            ),
        )
