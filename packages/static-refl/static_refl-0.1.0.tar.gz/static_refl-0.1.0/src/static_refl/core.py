from __future__ import annotations
from static_refl.options import get_refl_options
from static_refl.utils import transform_case
import sys
import typing
import datetime
import dataclasses
import enum
import types
import uuid
import functools

__all__ = [
    "PrimTag",
    "TypeId",
    "TypeIdPrim",
    "TypeIdArray",
    "TypeIdMap",
    "TypeIdSet",
    "TypeIdDataClass",
    "TypeIdTypedDict",
    "TypeIdOption",
    "TypeIdUnion",
    "TypeIdTuple",
    "TypeIdAny",
    "TypeIdLit",
    "StructDef",
    "FieldDef",
    "NONE_TYPE_ID",
    "ANY_TYPE_ID",
    "refl",
]

_TYPE_ID_CACHE: dict[tuple[typing.Any, ...], TypeId] = {}


def _type_id_cache(func):
    def wrapper(*args):
        key = (func, args)
        if got := _TYPE_ID_CACHE.get(key):
            return got
        result = func(*args)
        _TYPE_ID_CACHE[key] = result
        return result

    return wrapper


class PrimTag(enum.Enum):
    int = 1
    float = 2
    str = 3
    bool = 4
    bytes = 5
    complex = 6
    datetime = 7
    date = 8
    uuid = 9


type TypeId = (
    TypeIdPrim
    | TypeIdArray
    | TypeIdMap
    | TypeIdSet
    | TypeIdDataClass
    | TypeIdTypedDict
    | TypeIdOption
    | TypeIdUnion
    | TypeIdTuple
    | TypeIdAny
    | TypeIdLit
)


class TypeIdMixin:
    @property
    def is_none_type(self) -> bool:
        return False

    @property
    def is_primitive(self) -> bool:
        return False


class TypeIdPrim(TypeIdMixin):
    it: type
    tag: PrimTag

    @classmethod
    def _new(cls, type_obj: type, tag: PrimTag) -> TypeIdPrim:
        self = object.__new__(cls)
        self.it = type_obj
        self.tag = tag
        return self

    def __repr__(self) -> str:
        return f"!{self.it.__qualname__}"

    @property
    def is_primitive(self) -> bool:
        return True

    @property
    def pytype(self) -> type:
        return self.it


class TypeIdLit(TypeIdMixin):
    literal: str | int | None

    @classmethod
    def _new(cls, literal: str | int | None) -> TypeIdLit:
        self = object.__new__(cls)
        self.literal = literal
        return self

    def __repr__(self) -> str:
        return f"lit[{self.literal!r}]"

    @property
    def is_primitive(self) -> bool:
        return True

    @property
    def is_none_type(self) -> bool:
        return self is NONE_TYPE_ID

    @property
    def pytype(self) -> type:
        return type(self.literal)


class TypeIdArray(TypeIdMixin):
    element: TypeId

    @classmethod
    def _new(cls, type_obj: TypeId) -> TypeIdArray:
        self = object.__new__(cls)
        self.element = type_obj
        return self

    def __repr__(self) -> str:
        return f"array[{self.element!r}]"

    @property
    def pytype(self) -> type:
        return list


class TypeIdTuple(TypeIdMixin):
    elements: tuple[TypeId, ...]
    variadic_tail: TypeId | None = None

    @classmethod
    def _new(
        cls, elements: tuple[TypeId, ...], variadic_tail: TypeId | None = None
    ) -> TypeIdTuple:
        self = object.__new__(cls)
        self.elements = elements
        self.variadic_tail = variadic_tail
        return self

    def __repr__(self) -> str:
        if self.variadic_tail:
            return f"tuple[{', '.join(repr(e) for e in self.elements)}, {self.variadic_tail!r}, ...]"
        else:
            return f"tuple[{', '.join(repr(e) for e in self.elements)}]"

    @property
    def pytype(self) -> type:
        return tuple


class TypeIdMap(TypeIdMixin):
    key: TypeId
    value: TypeId

    @classmethod
    def _new(cls, key: TypeId, value: TypeId) -> TypeIdMap:
        self = object.__new__(cls)
        self.key = key
        self.value = value
        return self

    def __repr__(self) -> str:
        return f"map[{self.key!r}, {self.value!r}]"

    @property
    def pytype(self) -> type:
        return dict


class TypeIdSet(TypeIdMixin):
    element: TypeId

    @classmethod
    def _new(cls, type_obj: TypeId) -> TypeIdSet:
        self = object.__new__(cls)
        self.element = type_obj
        return self

    def __repr__(self) -> str:
        return f"set[{self.element!r}]"

    @property
    def pytype(self) -> type:
        return set


class TypeIdDataClass(TypeIdMixin):
    class_obj: type
    type_params: tuple[TypeId, ...]
    _structure: StructDef | None

    @classmethod
    def _new(
        cls, type_obj: type, type_params: tuple[TypeId, ...] = ()
    ) -> TypeIdDataClass:
        self = object.__new__(cls)
        self.class_obj = type_obj
        self.type_params = type_params
        self._structure = None
        return self

    def __repr__(self) -> str:
        if self.type_params:
            return f"{self.class_obj.__qualname__}[{', '.join(repr(tp) for tp in self.type_params)}]"
        else:
            return f"{self.class_obj.__qualname__}"

    @property
    def structure(self):
        if self._structure is None:
            self._structure = _dataclass_structure(self)
        return self._structure

    @property
    def pytype(self) -> type:
        return self.class_obj


class TypeIdTypedDict(TypeIdMixin):
    class_obj: type
    type_params: tuple[TypeId, ...]
    _structure: StructDef | None

    @classmethod
    def _new(
        cls, type_obj: type, type_params: tuple[TypeId, ...] = ()
    ) -> TypeIdTypedDict:
        self = object.__new__(cls)
        self.class_obj = type_obj
        self.type_params = type_params
        self._structure = None
        return self

    def __repr__(self) -> str:
        if self.type_params:
            return f"record {self.class_obj.__qualname__}[{', '.join(repr(tp) for tp in self.type_params)}]"
        else:
            return f"record {self.class_obj.__qualname__}"

    @property
    def structure(self):
        if self._structure is None:
            self._structure = _typeddict_structure(self)
        return self._structure

    @property
    def pytype(self) -> type:
        return dict


class TypeIdOption(TypeIdMixin):
    element: TypeId

    @classmethod
    def _new(cls, type_obj: TypeId) -> TypeIdOption:
        if isinstance(type_obj, TypeIdOption):
            return type_obj  # type: ignore
        self = object.__new__(cls)
        self.element = type_obj
        return self

    def __repr__(self) -> str:
        return f"option[{self.element!r}]"

    @property
    def pytype(self) -> type:
        raise Exception(
            f"({self.element.pytype.__qualname__} | None) has no specific Python type"
        )


class TypeIdUnion(TypeIdMixin):
    choices: tuple[TypeId, ...]

    @classmethod
    def _new(cls, choices: tuple[TypeId, ...]) -> TypeIdUnion:
        self = object.__new__(cls)
        self.choices = choices
        return self

    def __repr__(self) -> str:
        return f"union[{', '.join(repr(c) for c in self.choices)}]"

    @property
    def pytype(self) -> type:
        return dict


class TypeIdAny(TypeIdMixin):
    @classmethod
    def _new(cls) -> TypeIdAny:
        self = object.__new__(cls)
        return self

    def __repr__(self) -> str:
        return "any"

    @property
    def pytype(self) -> type:
        raise Exception("Any has no specific Python type")


@dataclasses.dataclass
class StructDef:
    fields: tuple[FieldDef, ...]
    type_params: tuple[str, ...] = ()


@dataclasses.dataclass
class FieldDef:
    name: str
    serde_name: str
    type: TypeId
    nullable: bool
    not_required: bool = False


NONE_TYPE_ID = TypeIdLit._new(None)
ANY_TYPE_ID = TypeIdAny._new()
_PRIM_TYPE_IDS: dict[type | types.UnionType | typing.TypeAliasType, TypeId] = {
    float: TypeIdPrim._new(float, PrimTag.float),
    str: TypeIdPrim._new(str, PrimTag.str),
    int: TypeIdPrim._new(int, PrimTag.int),
    bool: TypeIdPrim._new(bool, PrimTag.bool),
    bytes: TypeIdPrim._new(bytes, PrimTag.bytes),
    datetime.datetime: TypeIdPrim._new(datetime.datetime, PrimTag.datetime),
    datetime.date: TypeIdPrim._new(datetime.date, PrimTag.date),
    complex: TypeIdPrim._new(complex, PrimTag.complex),
    uuid.UUID: TypeIdPrim._new(uuid.UUID, PrimTag.uuid),
}


_ALLOWED_LITERAL_TYPES = (int, str, type(None))


def _mk_literal(value: typing.Any) -> TypeId:
    if not isinstance(value, _ALLOWED_LITERAL_TYPES):
        raise ValueError(
            f"Unsupported literal value type: got {type(value).__name__} value '{value}'. "
            f"Only int, str and None are supported."
        )
    key = (typing.cast("typing.Any", _mk_literal), value)
    if got := _TYPE_ID_CACHE.get(key):
        return got
    res = TypeIdLit._new(value)
    _TYPE_ID_CACHE[key] = res
    return res


@_type_id_cache
def _mk_union(type_ids: frozenset[TypeId] | tuple[TypeId, ...]) -> TypeId:
    flattened: list[TypeId] = []
    nullable = False
    for tp in type_ids:
        if isinstance(tp, TypeIdUnion):
            choices = tp.choices
        else:
            choices = (tp,)
        del tp
        for each in choices:
            if isinstance(each, TypeIdOption):
                flattened.append(each.element)
                nullable = True
            elif isinstance(each, TypeIdLit) and each.is_none_type:
                nullable = True
            else:
                flattened.append(each)

    if not flattened:
        return NONE_TYPE_ID

    match flattened:
        case []:
            return NONE_TYPE_ID
        case [only] if nullable:
            return _mk_optional(only)
        case [only]:
            return only
        case _:
            normalized_keys = frozenset(flattened)  # deduplicate
            if got := _TYPE_ID_CACHE.get((_mk_union, normalized_keys)):
                return got
            got = TypeIdUnion._new(tuple(normalized_keys))
            if nullable:
                got = _mk_optional(got)

            _TYPE_ID_CACHE[(_mk_union, normalized_keys)] = got
            return got


@_type_id_cache
def _mk_optional(type_id: TypeId) -> TypeId:
    if isinstance(type_id, TypeIdOption):
        return type_id
    return TypeIdOption._new(type_id)


@_type_id_cache
def _mk_array(element: TypeId) -> TypeId:
    return TypeIdArray._new(element)


@_type_id_cache
def _mk_tuple_struct(elements: tuple[TypeId, ...], variadic_tail: TypeId | None) -> TypeId:
    return TypeIdTuple._new(elements, variadic_tail)


@_type_id_cache
def _mk_dictionary(key: TypeId, value: TypeId) -> TypeId:
    return TypeIdMap._new(key, value)


@_type_id_cache
def _mk_mutable_set(element: TypeId) -> TypeId:
    return TypeIdSet._new(element)


@_type_id_cache
def _user_class(origin: type, args: tuple[TypeId, ...]) -> TypeId:
    if dataclasses.is_dataclass(origin):
        return TypeIdDataClass._new(origin, args)
    if typing.is_typeddict(origin):
        return TypeIdTypedDict._new(origin, args)
    raise ValueError(f"Unsupported user-defined class type: {origin.__qualname__}")


def _evaluate_forward_ref(
    fr: typing.ForwardRef, globalns: dict, localns: dict
) -> typing.Any:
    return fr._evaluate(globalns, localns, recursive_guard=frozenset())


def _class_to_type_id(
    tp,
    origin: type | None,
    type_args: tuple[typing.Any, ...],
    *,
    context: dict,
    instantiation: dict[str, TypeId] | None = None,
) -> TypeId:
    if tp is typing.Any:
        return ANY_TYPE_ID

    if origin is not None:
        # generic alias
        if not isinstance(origin, type):
            raise ValueError(f"Unsupported origin type: {origin} in {tp}")
        tp_args_normalized: list[TypeId] = []
        for tp_arg in type_args:
            tp_args_normalized.append(
                _type_param_to_type_id(context, tp_arg, instantiation)
            )
    else:
        origin = tp
        if not isinstance(origin, type):
            raise ValueError(f"Unsupported type: {tp}")
        tp_args_normalized = []
    return _user_class(origin, tuple(tp_args_normalized))


def _type_param_to_type_id(
    context: dict,
    tp_arg,
    scope: dict[str, TypeId] | None,
) -> TypeId:
    if isinstance(tp_arg, typing.TypeVar):
        if scope is not None and (found := scope.get(tp_arg.__name__)):
            return found
        raise ValueError(f"Unbound type variable in {tp_arg}")
    if isinstance(tp_arg, typing.TypeVarTuple):
        raise ValueError(f"Unpacked type variable not supported in {tp_arg}")
    if isinstance(tp_arg, typing.ForwardRef):
        tp_arg = _evaluate_forward_ref(tp_arg, context, {})
    return _type_obj_to_type_id(context, tp_arg, scope)


@functools.cache
def _simple_refl(tp: type) -> TypeId:
    context = sys.modules[tp.__module__].__dict__
    return _type_obj_to_type_id(context, tp, {})


def refl(tp: type | types.UnionType | typing.TypeAliasType) -> TypeId:
    if isinstance(tp, type):
        return _simple_refl(tp)
    else:
        return _type_obj_to_type_id({}, tp, {})


def _create_scope(
    parameters: tuple[typing.TypeVar, ...] | None,
    args: tuple[TypeId, ...] | None,
):
    if not parameters:
        return None
    parameters = parameters or ()
    args = args or ()
    scope = {}
    for i, param in enumerate(parameters):
        if i < len(args):
            scope[param.__name__] = args[i]
        else:
            scope[param.__name__] = ANY_TYPE_ID
    return scope


_NONE_TYPE = type(None)


def _type_obj_to_type_id(
    context: dict,
    tp: type | types.UnionType | typing.TypeAliasType,
    scope: dict[str, TypeId] | None,
) -> TypeId:
    if tp is None or tp is _NONE_TYPE:
        return NONE_TYPE_ID

    if got := _PRIM_TYPE_IDS.get(tp):
        return got

    if isinstance(tp, typing.TypeVar):
        if scope is not None and (found := scope.get(tp.__name__)):
            return found
        raise ValueError(f"Unbound type variable in {tp}")

    if isinstance(tp, type):
        if tp.__module__ == "builtins":
            raise ValueError(f"Unsupported built-in type: {tp.__qualname__}")
        return _class_to_type_id(tp, None, (), context=context, instantiation=scope)

    origin = typing.get_origin(tp)
    if isinstance(origin, typing.TypeAliasType):
        tp_args = typing.get_args(tp)
        type_ids = tuple(_type_obj_to_type_id(context, arg, scope) for arg in tp_args)
        scope = _create_scope(origin.__parameters__, type_ids)
        return _type_param_to_type_id(context, origin.__value__, scope)

    if origin is types.UnionType or origin is typing.Union:
        tp_args = typing.get_args(tp)
        type_ids = frozenset(
            _type_obj_to_type_id(context, arg, scope) for arg in tp_args
        )
        r = _mk_union(type_ids)
        return r

    if origin is typing.Literal:
        type_args = typing.get_args(tp)
        if not type_args:
            return NONE_TYPE_ID
        if len(type_args) == 1:
            return _mk_literal(type_args[0])
        return _mk_union(frozenset(_mk_literal(arg) for arg in type_args))

    if origin is list or origin is typing.List:
        type_args = typing.get_args(tp)
        if not type_args:
            return _mk_array(ANY_TYPE_ID)
        if len(type_args) != 1:
            raise ValueError(f"List must have exactly one type argument: {tp}")
        element_type = _type_param_to_type_id(context, type_args[0], scope)
        return _mk_array(element_type)

    if origin is tuple or origin is typing.Tuple:
        type_args = typing.get_args(tp)
        if type_args:
            if type_args[-1] is Ellipsis:
                assert len(type_args) >= 2
                tail = _type_param_to_type_id(context, type_args[-2], scope)
                element_types = tuple(
                    _type_param_to_type_id(context, t, scope) for t in type_args[:-2]
                )
                return _mk_tuple_struct(element_types, tail)
            else:
                element_types = tuple(
                    _type_param_to_type_id(context, t, scope) for t in type_args
                )
                return _mk_tuple_struct(element_types, None)
        else:
            return _mk_tuple_struct((), None)

    if origin is set or origin is typing.Set:
        type_args = typing.get_args(tp)
        if not type_args:
            return _mk_mutable_set(ANY_TYPE_ID)
        if len(type_args) != 1:
            raise ValueError(f"Set must have exactly one type argument: {tp}")
        element_type = _type_param_to_type_id(context, type_args[0], scope)
        return _mk_mutable_set(element_type)

    if origin is dict or origin is typing.Dict:
        type_args = typing.get_args(tp)

        match type_args:
            case []:
                key_type = ANY_TYPE_ID
                value_type = ANY_TYPE_ID
            case [key_t, value_t]:
                key_type = _type_param_to_type_id(context, key_t, scope)
                value_type = _type_param_to_type_id(context, value_t, scope)
            case [key_t]:
                key_type = _type_param_to_type_id(context, key_t, scope)
                value_type = ANY_TYPE_ID
            case _:
                raise ValueError(f"Dict must have at most two type arguments: {tp}")
        return _mk_dictionary(key_type, value_type)

    if isinstance(origin, type):
        type_args = typing.get_args(tp)
        return _class_to_type_id(
            tp, origin, type_args, context=context, instantiation=scope
        )

    if isinstance(tp, typing.TypeAliasType):
        return _type_param_to_type_id(context, tp.__value__, {})

    raise ValueError(f"Unsupported type: {tp}")


def _dataclass_structure(cp: TypeIdDataClass) -> StructDef:
    if cp._structure:
        return cp._structure

    annotations = typing.get_type_hints(cp.class_obj)
    refl_options = get_refl_options(cp.class_obj)
    type_var_parameters = getattr(cp.class_obj, "__type_params__", None)
    if type_var_parameters is None:
        type_var_parameters = getattr(cp.class_obj, "__parameters__", None)
    if type_var_parameters is None:
        type_var_parameters = ()

    type_params: list[str] = []
    for param in type_var_parameters:
        param = typing.cast("typing.TypeVar", param)
        type_params.append(param.__name__)
    del type_var_parameters
    scope = {}
    for i, name in enumerate(type_params):
        if i < len(cp.type_params):
            scope[name] = cp.type_params[i]
        else:
            scope[name] = ANY_TYPE_ID
    field_meta: list[FieldDef] = []
    context = sys.modules[cp.class_obj.__module__].__dict__

    for field_name, field_ann in annotations.items():
        if typing.get_origin(field_ann) is typing.ClassVar:
            continue
        field_type_id = _type_obj_to_type_id(context=context, tp=field_ann, scope=scope)
        serde_name = refl_options["rename_map"].get(field_name)
        if serde_name is None:
            serde_name = transform_case(field_name, refl_options["rename_all"])
        field_meta.append(
            FieldDef(
                name=field_name,
                serde_name=serde_name,
                nullable=isinstance(field_type_id, TypeIdOption),
                not_required=False,
                type=field_type_id,
            )
        )
    cp._structure = StructDef(
        fields=tuple(field_meta),
        type_params=tuple(type_params),
    )
    return cp._structure


def _typeddict_structure(cp: TypeIdTypedDict) -> StructDef:
    annotations = typing.get_type_hints(cp.class_obj)
    refl_options = get_refl_options(cp.class_obj)
    type_var_parameters = getattr(cp.class_obj, "__type_params__", None)
    if type_var_parameters is None:
        type_var_parameters = getattr(cp.class_obj, "__parameters__", None)
    if type_var_parameters is None:
        type_var_parameters = ()
    type_params: list[str] = []
    for param in type_var_parameters:
        param = typing.cast("typing.TypeVar", param)
        type_params.append(param.__name__)
    del type_var_parameters
    scope = {}
    for i, name in enumerate(type_params):
        if i < len(cp.type_params):
            scope[name] = cp.type_params[i]
        else:
            scope[name] = ANY_TYPE_ID
    field_meta: list[FieldDef] = []
    context = sys.modules[cp.class_obj.__module__].__dict__

    required_keys = getattr(cp.class_obj, "__required_keys__", set())

    for field_name, field_ann in annotations.items():
        if typing.get_origin(field_ann) is typing.ClassVar:
            continue
        field_type_id = _type_obj_to_type_id(context=context, tp=field_ann, scope=scope)
        serde_name = refl_options["rename_map"].get(field_name)
        if serde_name is None:
            serde_name = transform_case(field_name, refl_options["rename_all"])
        field_meta.append(
            FieldDef(
                name=field_name,
                serde_name=serde_name,
                nullable=isinstance(field_type_id, TypeIdOption),
                not_required=field_name not in required_keys,
                type=field_type_id,
            )
        )
    return StructDef(
        fields=tuple(field_meta),
        type_params=tuple(type_params),
    )
