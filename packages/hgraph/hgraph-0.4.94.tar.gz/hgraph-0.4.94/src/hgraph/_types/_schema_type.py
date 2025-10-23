from collections import defaultdict
import operator
from dataclasses import KW_ONLY, Field, InitVar, dataclass
from functools import reduce
from hashlib import shake_256
from inspect import get_annotations
import sys
from typing import (
    TYPE_CHECKING,
    ForwardRef,
    List,
    Set,
    Type,
    TypeVar,
    KeysView,
    ItemsView,
    ValuesView,
    get_type_hints,
    ClassVar,
    Generic,
    Mapping,
)

from frozendict import frozendict

if TYPE_CHECKING:
    from hgraph._types._type_meta_data import HgTypeMetaData


__all__ = ("AbstractSchema", "Base")


class AbstractSchema:
    """
    The base class for the two schema-based types supported by HGraph, namely: ``CompoundScalar`` and
    ``TimeSeriesSchema``.

    This class provides the key meta-data describing the schema which is extracted from the class type annotations.
    The information is tracked at class level and is stored in the attribute ``__meta_data_schema__``.
    This attribute contains the name of the property, and it's ``HgTypeMetaData`` representation.

    Schemas can also contain unresolved generic types. The resolution and any partial information is also tracked
    on class level attributes in this class. These make use of the attributes: ``__resolved__``,
    ``__partial_resolution__`` and ``__partial_resolution_parent__``.
    """

    __meta_data_schema__: frozendict[str, "HgTypeMetaData"] = {}
    __resolved__: dict[str, Type["AbstractSchema"]] = {}  # Cache of resolved classes
    __forward_refs__: dict[str, Set[Type]] = defaultdict(
        set
    )  # Cache of classes pending resolution of forward references
    __partial_resolution__: frozendict[TypeVar, Type]
    __partial_resolution_parent__: Type["AbstractSchema"]
    __serialise_discriminator_field__: str = None
    __serialise_children__: Mapping[str, type] = None
    __serialise_base__: bool = False

    @classmethod
    def _schema_index_of(cls, key: str) -> int:
        return list(cls.__meta_data_schema__.keys()).index(key)

    @classmethod
    def _schema_get(cls, key: str) -> "HgTypeMetaData":
        return cls.__meta_data_schema__.get(key)

    @classmethod
    def _schema_items(cls) -> ItemsView[str, "HgTypeMetaData"]:
        return cls.__meta_data_schema__.items()

    @classmethod
    def _schema_values(cls) -> ValuesView["HgTypeMetaData"]:
        return cls.__meta_data_schema__.values()

    @classmethod
    def _schema_keys(cls) -> KeysView[str]:
        return cls.__meta_data_schema__.keys()

    @classmethod
    def _schema_is_resolved(cls):
        return not getattr(cls, "__parameters__", False)

    @classmethod
    def _schema_convert_base(cls, base_py):
        return base_py

    @classmethod
    def _parse_type(cls, tp: Type) -> "HgTypeMetaData":
        """
        Parse the type using the appropriate HgTypeMetaData instance.
        By default, we use the top level parser.
        """
        from hgraph._types._type_meta_data import HgTypeMetaData

        return HgTypeMetaData.parse_type(tp)

    @classmethod
    def _build_resolution_dict(cls, resolution_dict: dict[TypeVar, "HgTypeMetaData"], resolved: "AbstractSchema"):
        """
        Build the resolution dictionary for the resolved class.
        """
        for k, v in cls.__meta_data_schema__.items():
            if r := resolved._schema_get(k):
                v.do_build_resolution_dict(resolution_dict, r)
        if (base := getattr(cls, "__base_typevar_meta__", None)) is not None:
            if r := getattr(resolved, "__base_resolution_meta__", None):
                base.do_build_resolution_dict(resolution_dict, r)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        AbstractSchema.__build_schema__(cls)

    def __build_schema__(cls) -> None:
        from hgraph._types._type_meta_data import ParseError

        schema = dict(reduce(operator.or_, [getattr(c, "__meta_data_schema__", {}) for c in cls.__bases__]))
        for k, v in get_annotations(cls).items():
            if isinstance(v, str):
                try:
                    v = eval(
                        v,
                        getattr(sys.modules.get(getattr(cls, "__module__", None), None), "__dict__", None),
                        dict(vars(cls)),
                    )
                except Exception:
                    if v == cls.__name__:  # self reference
                        v = cls
                    elif isinstance(AbstractSchema.__forward_refs__.get(v), type):
                        v = AbstractSchema.__forward_refs__[v]
                    elif "." not in v and isinstance(
                        AbstractSchema.__forward_refs__.get(cls.__qualname__.replace(cls.__name__, v)), type
                    ):
                        v = AbstractSchema.__forward_refs__.get(cls.__qualname__.replace(cls.__name__, v))
                    else:
                        v = cls.__qualname__.replace(cls.__name__, v) if "." not in v else v
                        AbstractSchema.__forward_refs__[v].add(cls)
                        from hgraph._types._scalar_type_meta_data import HgCompoundScalarTypeForwardRef

                        v = HgCompoundScalarTypeForwardRef(v)
            if getattr(v, "__origin__", None) == ClassVar:
                continue
            if v is KW_ONLY:
                continue
            if isinstance(v, InitVar):
                if getattr(getattr(cls, k, None), "__get__", None):  # property
                    v = v.type
                else:
                    continue
            if isinstance(f := getattr(cls, k, None), Field) and f.metadata.get("hidden"):
                continue

            from hgraph._types._type_meta_data import HgTypeMetaData

            s = cls._parse_type(v) if not isinstance(v, HgTypeMetaData) else v

            if s is None:
                raise ParseError(f"When parsing '{cls}', unable to parse item {k} with value {v}")
            if k in schema and not (s_p := schema[k]).matches(s):
                raise ParseError(
                    f"Attribute: '{k}' in '{cls}' is already defined in a parent as '{str(s_p)}'"
                    f" but attempted to be redefined as '{str(s)}"
                )

            schema[k] = s

        if getattr(cls, "__build_meta_data__", True):
            cls.__meta_data_schema__ = frozendict(schema)

        if (params := getattr(cls, "__parameters__", None)) is not None:
            cls.__parameters_meta_data__ = {v: cls._parse_type(v) for v in params}
        elif any(not v.is_resolved for v in schema.values()):
            raise ParseError(f"Schema '{cls}' has unresolved types while not being generic class")

        if cls.__qualname__ in AbstractSchema.__forward_refs__:
            subs = AbstractSchema.__forward_refs__[cls.__qualname__]
            if isinstance(subs, set):
                AbstractSchema.__forward_refs__[cls.__qualname__] = cls
                for t in subs:
                    AbstractSchema.__build_schema__(t)
        else:
            AbstractSchema.__forward_refs__[cls.__qualname__] = cls

        if (s_c := getattr(cls, "__serialise_children__", None)) is not None:
            d_f = getattr(cls, "__serialise_discriminator_field__", None)
            nm = getattr(cls, d_f, cls.__name__)
            s_c[nm] = cls
            cls.__serialise_base__ = False
        elif getattr(cls, "__serialise_base__", True):
            cls.__serialise_children__ = {}
            if getattr(cls, "__serialise_discriminator_field__", None) is None:
                cls.__serialise_discriminator_field__ = "__type__"

    @classmethod
    def _root_cls(cls) -> Type["AbstractSchema"]:
        """This class or the __partial_resolution_parent__ if this is a partially resolved class"""
        return getattr(cls, "__partial_resolution_parent__", None) or getattr(cls, "__root__", cls)

    @classmethod
    def _create_resolved_class(cls, schema: dict[str, "HgTypeMetaData"]) -> Type["AbstractSchema"]:
        """Create a 'resolved' instance class and cache as appropriate"""
        suffix = ",".join(f"{k}:{str(schema[k])}" for k in schema)
        root_cls = cls._root_cls()
        cls_name = f"{root_cls.__name__}_{shake_256(bytes(suffix, 'utf8')).hexdigest(6)}"
        r_cls: Type["AbstractSchema"]
        if (r_cls := cls.__resolved__.get(cls_name)) is None:
            r_cls = type(cls_name, (root_cls,), {})
            r_cls.__meta_data_schema__ = frozendict(schema)
            r_cls.__root__ = root_cls
            r_cls.__name__ = f"{root_cls.__name__}[{suffix}]"
            cls.__resolved__[cls_name] = r_cls
        return r_cls

    @classmethod
    def _create_partial_resolved_class(cls, resolution_dict) -> Type["AbstractSchema"]:
        suffix = ",".join(f"{str(resolution_dict.get(k, k))}" for k in cls.__parameters__)
        cls_name = f"{cls._root_cls().__qualname__}[{suffix}]"
        r_cls: Type["AbstractSchema"]
        if (r_cls := cls.__resolved__.get(cls_name)) is None:
            r_cls = type(cls_name, (cls,), {})
            r_cls.__partial_resolution__ = frozendict(resolution_dict)
            r_cls.__parameters__ = cls.__parameters__
            r_cls.__parameters_meta_data__ = cls.__parameters_meta_data__
            r_cls.__args__ = tuple(resolution_dict.get(k, k) for k in cls.__parameters__)
            r_cls.__partial_resolution_parent__ = cls._root_cls()
            cls.__resolved__[cls_name] = r_cls
        return r_cls

    @classmethod
    def _resolve(cls, resolution_dict) -> Type["AbstractSchema"]:
        if not resolution_dict:
            return cls

        for b in reversed(cls.mro()):
            if b == cls._root_cls():
                suffix_map = b.__parameters_meta_data__
            elif issubclass(b, cls._root_cls()):
                arg_map = {k: cls._parse_type(v) for k, v in zip(suffix_map.keys(), b.__args__)}
                suffix_map = {k: cls._parse_type(v).resolve(arg_map, weak=True).py_type for k, v in suffix_map.items()}

        suffix_map = {k: cls._parse_type(v).resolve(resolution_dict, weak=True).py_type for k, v in suffix_map.items()}
        if all(k is v for k, v in suffix_map.items()):
            # class Schema[T, T1]; t = Schema[T1, T2]; is a noop
            return cls

        suffix = ",".join(str(v) for v in suffix_map.values())
        cls_name = f"{cls._root_cls().__qualname__}[{suffix}]"

        if SchemaRecurseContext.is_in_context(cls_name):
            from hgraph._types._scalar_type_meta_data import HgCompoundScalarTypeForwardRef

            fwd = HgCompoundScalarTypeForwardRef(cls_name)
            SchemaRecurseContext.attach_cb(cls_name, lambda: setattr(fwd, "py_type", cls.__resolved__.get(cls_name)))
            return fwd

        r_cls: Type["AbstractSchema"]
        if (r_cls := cls.__resolved__.get(cls_name)) is None:
            bases = (cls,)
            type_dict = {}

            if base_py := getattr(cls, "__base_typevar__", None):
                base = cls._parse_type(base_py)
                if (base := base.resolve(resolution_dict, weak=True)).is_resolved:
                    base_py = cls._schema_convert_base(base.py_type)
                    cls = base_py._schema_convert_base(cls)
                    bases = (cls, base_py)
                    type_dict["__base_meta_data_schema__"] = base_py.__meta_data_schema__
                    type_dict["__base_resolution_meta__"] = cls._parse_type(base_py)
                else:
                    type_dict["__base_typevar_meta__"] = base
                    type_dict["__base_typevar__"] = base.py_type

            parameters = []
            for p in cls.__parameters__:
                r = resolution_dict.get(p, cls.__parameters_meta_data__.get(p))
                if not r.is_resolved:
                    parameters.extend(r.type_vars)

            r_cls = type(cls_name, bases, type_dict)
            r_cls.__root__ = cls._root_cls()
            r_cls.__parameters__ = tuple(parameters)
            r_cls.__parameters_meta_data__ = {p: cls._parse_type(p) for p in parameters}
            r_cls.__args__ = tuple(suffix_map[k] for k in cls._root_cls().__parameters__)

            with SchemaRecurseContext(cls_name):
                r_cls.__meta_data_schema__ = frozendict(
                    {k: v.resolve(resolution_dict, weak=True) for k, v in r_cls.__meta_data_schema__.items()}
                )

                if base_py and hasattr(r_cls, "__dataclass_fields__"):
                    p = r_cls.__dataclass_params__
                    r_cls = dataclass(r_cls, frozen=p.frozen, init=p.init, eq=p.eq, repr=p.repr)

                cls.__resolved__[cls_name] = r_cls
        return r_cls

    @classmethod
    def _matches(cls, other):
        return issubclass(other, cls)

    @classmethod
    def _matches_schema(cls, other):
        return len(cls._schema_keys() - other._schema_keys()) == 0 and all(
            cls._schema_get(k).matches(other._schema_get(k)) for k in cls._schema_keys()
        )

    @classmethod
    def __class_getitem__(cls, items):
        from hgraph._types._type_meta_data import ParseError

        resolution_dict = dict(getattr(cls, "__partial_resolution__", {}))
        if type(items) is not tuple:
            items = (items,)
        if len(items) > len(cls.__parameters__):
            raise ParseError(f"'{cls} was provided more elements then generic parameters")
        has_slice = False
        for item, parm in zip(items, cls.__parameters__):
            if isinstance(item, slice):
                has_slice = True
                k = item.start
                v = item.stop
            elif has_slice:
                raise ParseError(
                    f"'{cls}' has supplied slice parameters already, non-slice parameters are no longer accepted"
                )
            else:
                k = parm
                v = item
            if not isinstance(k, TypeVar):
                raise ParseError(f"'{cls}' type '{k}' is not an instance of TypeVar as required")
            if k in resolution_dict:
                raise ParseError(f"'{cls}' has already defined '{k}'")
            if parsed_v := cls._parse_type(v):
                resolution_dict[k] = parsed_v
            else:
                raise ParseError(f"In '{cls}' type '{k}': '{v}' was unable to parse as a valid type")

        if len(resolution_dict) < len(cls.__parameters__) or any(not v.is_resolved for v in resolution_dict.values()):
            # Only a partial resolution is place
            if all(v.is_resolved for v in resolution_dict.values()):
                # simple case - just fixing some of the parameters
                tp = cls._create_partial_resolved_class(resolution_dict)
            elif all(k == v.py_type for k, v in resolution_dict.items()):
                # all values are the same, no real resolution going on here
                return cls
            else:
                # resolution values are not all resolved hence there will be a need to reassign the typevars
                tp = cls._resolve(resolution_dict)
        else:
            v: HgTypeMetaData
            tp = cls._resolve(resolution_dict)

        return tp


AbstractSchema.__annotations__ = {}


class Base:
    def __init__(self, item):
        self.item = item

    def __class_getitem__(cls, item):
        if cls is Base and isinstance(item, TypeVar):
            assert item.__bound__ is not None
            return cls(item)
        else:
            return super().__class_getitem__(item)

    def __mro_entries__(self, bases):
        return (type(f"Base_{self.item.__name__}", (Base,), {"__base_typevar__": self.item}), Base, self.item.__bound__)


class SchemaRecurseContext:
    __tp_stack__: List[type] = []
    __stack__: List[type] = []

    def __init__(self, tp):
        self.tp = tp
        self.cb = None

    @classmethod
    def is_in_context(cls, tp):
        return len(cls.__tp_stack__) > 0 and tp in cls.__tp_stack__

    @classmethod
    def attach_cb(cls, tp, cb):
        if len(cls.__tp_stack__) > 0 and tp in cls.__tp_stack__:
            context = cls.__stack__[cls.__tp_stack__.index(tp)]
            context.cb = lambda prev=context.cb: (cb(), prev() if prev else None)

    def __enter__(self):
        self.__tp_stack__.append(self.tp)
        self.__stack__.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__tp_stack__.pop()
        self.__stack__.pop()
        if self.cb:
            self.cb()
        return False
