from __future__ import annotations
from static_refl.core import (
    TypeId,
    TypeIdPrim,
    TypeIdArray,
    TypeIdDataClass,
    TypeIdTypedDict,
    TypeIdTuple,
    TypeIdMap,
    TypeIdSet,
    TypeIdUnion,
    TypeIdLit,
    TypeIdAny,
    TypeIdOption,
    PrimTag,
    ANY_TYPE_ID,
    refl,
)
from static_refl.serde_common import orthogonal_split, SplitFastTell
from dataclasses import is_dataclass
from dataclasses import dataclass
import base64
import datetime
import json
import typing
import uuid
import io
import enum
import reprlib

SFT_ALL_DC = SplitFastTell.all_dataclass
SFT_ALL_OTHER = SplitFastTell.all_other
SFT_ALL_LIT = SplitFastTell.all_lit

__all__ = [
    "Schema",
    "JsonSerdeOptions",
    "JsonSerializer",
    "JsonDeserializer",
    "UUIDEncoding",
]

if typing.TYPE_CHECKING:

    class Schema[T]:
        tid: TypeId

        @staticmethod
        def to_untyped(
            obj: T, options: JsonSerdeOptions | None = None
        ) -> typing.Any: ...
        @staticmethod
        def to_typed(obj: typing.Any, options: JsonSerdeOptions | None = None) -> T: ...
else:

    class _SchemaRt:
        def __init__(self, t: typing.Type):
            self.tid = refl(t)

        def to_untyped(self, obj, options: JsonSerdeOptions | None = None):
            serializer = JsonSerializer(options)
            return serializer.serialize(self.tid, obj)

        def to_typed(self, obj, options: JsonSerdeOptions | None = None):
            deserializer = JsonDeserializer(options)
            return deserializer.deserialize(self.tid, obj)

    class Schema:
        def __class_getitem__(cls, item):
            if isinstance(item, str):
                return item
            return _SchemaRt(item)


class UUIDEncoding(enum.Enum):
    object = 0
    hex = 1
    bytes = 2


@dataclass
class JsonSerdeOptions:
    keep_bytes: bool = False
    keep_complex: bool = False
    uuid_encoding: UUIDEncoding = UUIDEncoding.hex


def _internal_jsonify(x) -> str:
    return json.dumps(x)


def _internal_parse_json(s: str):
    return json.loads(s)


class JsonSerializer:
    def __init__(self, options: JsonSerdeOptions | None):
        self.options = options or JsonSerdeOptions()

    def serialize(self, tid: TypeId, obj):
        return self.serialize_impl(tid, obj)

    def serialize_impl(self, tid: TypeId, obj):
        return SER_DISPATCH[tid.__class__](self, tid, obj)

    def serialize_prim(self, tid: TypeIdPrim, obj):
        match tid.tag:
            case PrimTag.int:
                return int(obj)
            case PrimTag.float:
                return float(obj)
            case PrimTag.str:
                return str(obj)
            case PrimTag.bool:
                return obj
            case PrimTag.bytes:
                if self.options.keep_bytes:
                    return obj
                return {"base64": base64.b64encode(obj).decode("utf-8")}
            case PrimTag.complex:
                if self.options.keep_complex:
                    return obj
                return {"real": obj.real, "imag": obj.imag}
            case PrimTag.datetime:
                return obj.isoformat()
            case PrimTag.date:
                return obj.isoformat()
            case PrimTag.uuid:
                match self.options.uuid_encoding:
                    case UUIDEncoding.bytes:
                        return obj.bytes
                    case UUIDEncoding.hex:
                        return obj.hex
                    case UUIDEncoding.object:
                        return obj
                    case _:
                        raise ValueError(
                            f"Unknown UUID encoding: {self.options.uuid_encoding}"
                        )

    def serialize_typeddict(self, tid: TypeIdTypedDict, obj: dict):
        fields = tid.structure.fields
        res = {}
        for field in fields:
            fvalue = obj.get(field.name)
            if fvalue is None:
                continue
            json_value = self.serialize_impl(field.type, fvalue)
            res[field.serde_name] = json_value
        return res

    def serialize_dataclass(self, tid: TypeIdDataClass, obj):
        fields = tid.structure.fields
        res = {}
        for field in fields:
            fvalue = getattr(obj, field.name, None)
            if fvalue is None:
                continue
            json_value = self.serialize_impl(field.type, fvalue)
            res[field.serde_name] = json_value
        return res

    def serialize_lit(self, tid: TypeIdLit, obj):
        return obj

    def serialize_any(self, tid: TypeIdAny, obj):
        return obj

    def serialize_array(self, tid: TypeIdArray, obj):
        res = []
        for item in obj:
            res.append(self.serialize_impl(tid.element, item))
        return res

    def serialize_tuple(self, tid: TypeIdTuple, obj):
        res = []
        if not obj:
            return res

        if not tid.variadic_tail:
            if len(tid.elements) != len(obj):
                raise ValueError(
                    f"Expected tuple of length {len(tid.elements)}, got {len(obj)}"
                )
            for etid, item in zip(tid.elements, obj):
                res.append(self.serialize_impl(etid, item))
        else:
            if len(obj) < len(tid.elements):
                raise ValueError(
                    f"Expected tuple of length at least {len(tid.elements)}, got {len(obj)}"
                )
            obj_iter = iter(obj)
            for elt_tid in tid.elements:
                res.append(self.serialize_impl(elt_tid, next(obj)))
            for item in obj_iter:
                res.append(self.serialize_impl(tid.variadic_tail, item))
        return res

    def serialize_set(self, tid: TypeIdSet, obj):
        res = []
        for item in obj:
            res.append(self.serialize_impl(tid.element, item))
        return res

    def serialize_map(self, tid: TypeIdMap, obj):
        if not obj:
            return {}

        keys = []
        values = []

        if tid.key.pytype is str:
            for k, v in obj.items():
                keys.append(self.serialize_impl(tid.key, k))
                values.append(self.serialize_impl(tid.value, v))
        else:
            for k, v in obj.items():
                ko = self.serialize_impl(tid.key, k)
                keys.append(_internal_jsonify(ko))
                values.append(self.serialize_impl(tid.value, v))
        return dict(zip(keys, values))

    def serialize_option(self, tid: TypeIdOption, obj):
        if obj is None:
            return None
        else:
            return self.serialize_impl(tid.element, obj)

    def serialize_union(self, tid: TypeIdUnion, obj):
        split = orthogonal_split(tid)
        fast_tell = split.fast_tell

        if fast_tell is SFT_ALL_OTHER:
            ser = split.others.get(obj.__class__)
            if ser is not None:
                return self.serialize_impl(ser, obj)
            # TODO better error message
            raise ValueError(f"Cannot serialize object: {obj}")
        elif fast_tell is SFT_ALL_LIT:
            if lit_def := split.literals.get(obj):
                return self.serialize_lit(lit_def, obj)
            else:
                # TODO better error message
                raise ValueError(f"Cannot serialize literal: {obj}")
        elif fast_tell is SFT_ALL_DC:
            if not is_dataclass(obj):
                raise ValueError(f"Cannot serialize non-dataclass: {obj}")
            tagname = split.dataclass_tagname
            if tagname is None:
                raise ValueError(f"Cannot serialize dataclass: {obj}")
            tagvalue = getattr(obj, tagname, None)
            if type_id := split.dataclasses.get(tagvalue):  # type: ignore
                return self.serialize_dataclass(type_id, obj)
            raise ValueError(f"Cannot serialize dataclass: {obj}")

        if isinstance(obj, dict):
            tagname = split.typeddict_tagname
            if tagname is not None:
                tagvalue = obj.get(tagname)
                if type_id := split.typeddicts.get(tagvalue):  # type: ignore
                    return self.serialize_typeddict(type_id, obj)
            if dict_ser := split.others.get(dict):
                return self.serialize_impl(dict_ser, obj)
            raise ValueError(f"Cannot serialize dict: {obj}")
        elif is_dataclass(obj):
            tagname = split.dataclass_tagname
            if tagname is None:
                raise ValueError(f"Cannot serialize dataclass: {obj}")
            tagvalue = getattr(obj, tagname, None)
            if type_id := split.dataclasses.get(tagvalue):  # type: ignore
                return self.serialize_dataclass(type_id, obj)
            raise ValueError(f"Cannot serialize dataclass: {obj}")
        elif lit_def := split.literals.get(obj):
            return self.serialize_lit(lit_def, obj)
        elif split.has_any:
            return self.serialize_any(ANY_TYPE_ID, obj)
        else:
            ser = split.others.get(obj.__class__)
            if ser is not None:
                return self.serialize_impl(ser, obj)
            raise ValueError(f"Cannot serialize object: {obj}")


SER_DISPATCH = {
    TypeIdPrim: JsonSerializer.serialize_prim,
    TypeIdTypedDict: JsonSerializer.serialize_typeddict,
    TypeIdDataClass: JsonSerializer.serialize_dataclass,
    TypeIdArray: JsonSerializer.serialize_array,
    TypeIdTuple: JsonSerializer.serialize_tuple,
    TypeIdSet: JsonSerializer.serialize_set,
    TypeIdMap: JsonSerializer.serialize_map,
    TypeIdLit: JsonSerializer.serialize_lit,
    TypeIdAny: JsonSerializer.serialize_any,
    TypeIdOption: JsonSerializer.serialize_option,
    TypeIdUnion: JsonSerializer.serialize_union,
}

_FLT_OR_INT = (int, float)


def _render_path(path: list[str | int]) -> str:
    buf = io.StringIO()
    buf.write("$ROOT")
    for p in path:
        if isinstance(p, int):
            buf.write(f"[{p}]")
        else:
            if p.isidentifier():
                buf.write(f".{p}")
            else:
                buf.write(f".{p!r}")
    return buf.getvalue()


class DecodeError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


_LIST_AND_TUPLE = (list, tuple)
_LIST_AND_SET = (list, set)


class JsonDeserializer:
    def __init__(self, options: JsonSerdeOptions | None):
        self.options = options or JsonSerdeOptions()
        self.path: list[int | str] = []

    def deserialize(self, tid: TypeId, obj):
        try:
            return self.deserialize_impl(tid, obj)
        except DecodeError as e:
            path = _render_path(self.path)
            raise ValueError(f"{e.message} (path: {path})")
        except Exception as e:
            path = _render_path(self.path)
            raise Exception(f"Deserialization failed (path: {path}): {e}") from e

    def deserialize_impl(self, tid: TypeId, obj):
        return DESER_DISPATCH[tid.__class__](self, tid, obj)

    def deserialize_prim(self, tid: TypeIdPrim, obj):
        match tid.tag:
            case PrimTag.int:
                return int(obj)
            case PrimTag.float:
                return float(obj)
            case PrimTag.str:
                return str(obj)
            case PrimTag.bool:
                return bool(obj)
            case PrimTag.bytes:
                if isinstance(obj, bytes):
                    return obj
                if isinstance(obj, dict):
                    base64_data = obj.get("base64")
                    if isinstance(base64_data, str):
                        return base64.b64decode(base64_data)
                raise ValueError(f"Cannot deserialize bytes from {obj}")
            case PrimTag.complex:
                if isinstance(obj, complex):
                    return obj
                if isinstance(obj, dict):
                    real = obj.get("real")
                    imag = obj.get("imag")
                    if isinstance(real, _FLT_OR_INT) and isinstance(imag, _FLT_OR_INT):
                        return complex(real, imag)
                raise ValueError(f"Cannot deserialize complex from {obj}")
            case PrimTag.datetime:
                if isinstance(obj, str):
                    return datetime.datetime.fromisoformat(obj)
                if isinstance(obj, datetime.datetime):
                    return obj
                raise ValueError(f"Expected datetime, got {type(obj)}")
            case PrimTag.date:
                if isinstance(obj, str):
                    return datetime.date.fromisoformat(obj)
                if isinstance(obj, datetime.date):
                    return obj
                raise ValueError(f"Expected date, got {type(obj)}")
            case PrimTag.uuid:
                if isinstance(obj, uuid.UUID):
                    return obj
                if isinstance(obj, bytes):
                    return uuid.UUID(bytes=obj)
                if isinstance(obj, str):
                    return uuid.UUID(obj)
                raise ValueError(f"Cannot deserialize uuid from {obj}")

    def deserialize_typeddict(self, tid: TypeIdTypedDict, obj) -> dict:
        if not isinstance(obj, dict):
            raise DecodeError(
                f"Expected a dict to deserialize {tid.class_obj.__name__}, got {type(obj)}"
            )
        fields = tid.structure.fields
        res = {}
        for field in fields:
            fvalue = obj.get(field.serde_name)
            if fvalue is None:
                if field.nullable:
                    if not field.not_required:
                        # assure we can use 'dict[key]'
                        res[field.name] = None
                    continue
                else:
                    raise DecodeError(f"Missing required field {field.serde_name!r}")
            self.path.append(field.serde_name)
            py_value = self.deserialize_impl(field.type, fvalue)
            self.path.pop()
            res[field.name] = py_value
        return res

    def deserialize_dataclass(self, tid: TypeIdDataClass, obj):
        if not isinstance(obj, dict):
            raise DecodeError(
                f"Expected a dict to deserialize {tid.class_obj.__name__}, got {type(obj)}"
            )
        fields = tid.structure.fields
        res = object.__new__(tid.pytype)
        for field in fields:
            fvalue = obj.get(field.serde_name)
            if fvalue is None:
                if field.nullable:
                    object.__setattr__(res, field.name, None)
                    continue
                else:
                    raise DecodeError(f"Missing required field {field.serde_name!r}")
            self.path.append(field.serde_name)
            py_value = self.deserialize_impl(field.type, fvalue)
            self.path.pop()
            object.__setattr__(res, field.name, py_value)
        return res

    def deserialize_lit(self, tid: TypeIdLit, obj):
        if obj != tid.literal:
            raise ValueError(
                f"Expected literal {reprlib.repr(tid.literal)}, got {reprlib.repr(obj)}"
            )
        return obj

    def deserialize_any(self, tid: TypeIdAny, obj) -> typing.Any:
        return obj

    def deserialize_array(self, tid: TypeIdArray, obj) -> list:
        if not isinstance(obj, list):
            raise DecodeError(f"Expected list for array, got {type(obj)}")
        res = []
        for i, item in enumerate(obj):
            self.path.append(i)
            res.append(self.deserialize_impl(tid.element, item))
            self.path.pop()
        return res

    def deserialize_tuple(self, tid: TypeIdTuple, obj) -> tuple:
        if not isinstance(obj, _LIST_AND_TUPLE):
            raise DecodeError(f"Expected list for tuple, got {type(obj)}")

        res = []
        if not tid.variadic_tail:
            if len(tid.elements) != len(obj):
                raise DecodeError(
                    f"Expected tuple of length {len(tid.elements)}, got {len(obj)}"
                )
            for i, (etid, item) in enumerate(zip(tid.elements, obj)):
                self.path.append(i)
                res.append(self.deserialize_impl(etid, item))
                self.path.pop()
            return tuple(res)
        else:
            if len(obj) < len(tid.elements):
                raise DecodeError(
                    f"Expected tuple of length at least {len(tid.elements)}, got {len(obj)}"
                )
            obj_iter: enumerate[typing.Any] = iter(enumerate(obj))
            for elt_tid in tid.elements:
                i, item = next(obj_iter)
                self.path.append(i)
                res.append(self.deserialize_impl(elt_tid, next(obj_iter)))
                self.path.pop()
            for i, item in obj_iter:
                self.path.append(i)
                res.append(self.deserialize_impl(tid.variadic_tail, item))
                self.path.pop()
        return tuple(res)  # type: ignore

    def deserialize_set(self, tid: TypeIdSet, obj):
        if not isinstance(obj, _LIST_AND_SET):
            raise DecodeError(f"Expected list for set, got {type(obj)}")
        res = []
        for i, item in enumerate(obj):
            self.path.append(i)
            res.append(self.deserialize_impl(tid.element, item))
            self.path.pop()
        return set(res)

    def deserialize_map(self, tid: TypeIdMap, obj):
        if not isinstance(obj, dict):
            raise DecodeError(f"Expected dict for map, got {type(obj)}")
        res = {}
        if tid.key.pytype is str:
            for k, v in obj.items():
                key = k
                self.path.append(k)
                value = self.deserialize_impl(tid.value, v)
                self.path.pop()
                res[key] = value
        else:
            for k, v in obj.items():
                self.path.append(k)
                ko = self.deserialize_impl(tid.key, _internal_parse_json(k))
                key = ko
                value = self.deserialize_impl(tid.value, v)
                self.path.pop()
                res[key] = value
        return res

    def deserialize_option(self, tid: TypeIdOption, obj):
        if obj is None:
            return None
        else:
            return self.deserialize_impl(tid.element, obj)

    def deserialize_union(self, tid: TypeIdUnion, obj):
        split = orthogonal_split(tid)
        fast_tell = split.fast_tell
        if fast_tell is SFT_ALL_OTHER:
            ser = split.others.get(type(obj))
            if ser is not None:
                return self.deserialize_impl(ser, obj)
            # TODO better error message
            raise DecodeError(f"Cannot deserialize object: {reprlib.repr(obj)}")
        elif fast_tell is SFT_ALL_LIT:
            if lit_def := split.literals.get(obj):
                return self.deserialize_lit(lit_def, obj)
            else:
                # TODO better error message
                raise DecodeError(f"Cannot deserialize literal: {reprlib.repr(obj)}")
        elif fast_tell is SFT_ALL_DC:
            tagname = split.dataclass_tagname
            if tagname is not None:
                tagvalue = obj.get(tagname)
                if type_id := split.dataclasses.get(tagvalue):  # type: ignore
                    return self.deserialize_dataclass(type_id, obj)
            # TODO better error message
            raise DecodeError(f"Cannot deserialize dataclass: {reprlib.repr(obj)}")

        if isinstance(obj, dict):
            tagname = split.typeddict_tagname
            if tagname is not None:
                tagvalue = obj.get(tagname)
                if type_id := split.typeddicts.get(tagvalue):  # type: ignore
                    return self.deserialize_typeddict(type_id, obj)
            tagname = split.dataclass_tagname
            if tagname is not None:
                tagvalue = obj.get(tagname)
                if type_id := split.dataclasses.get(tagvalue):  # type: ignore
                    return self.deserialize_dataclass(type_id, obj)

            if dict_ser := split.others.get(dict):
                return self.deserialize_impl(dict_ser, obj)
            raise DecodeError(f"Cannot deserialize dict: {reprlib.repr(obj)}")

        elif lit_def := split.literals.get(obj):
            return self.deserialize_lit(lit_def, obj)
        else:
            ser = split.others.get(type(obj))
            if ser is not None:
                return self.deserialize_impl(ser, obj)
            if split.has_any:
                return self.deserialize_any(ANY_TYPE_ID, obj)
            raise DecodeError(f"Cannot deserialize object: {reprlib.repr(obj)}")


DESER_DISPATCH = {
    TypeIdPrim: JsonDeserializer.deserialize_prim,
    TypeIdTypedDict: JsonDeserializer.deserialize_typeddict,
    TypeIdDataClass: JsonDeserializer.deserialize_dataclass,
    TypeIdArray: JsonDeserializer.deserialize_array,
    TypeIdLit: JsonDeserializer.deserialize_lit,
    TypeIdAny: JsonDeserializer.deserialize_any,
    TypeIdOption: JsonDeserializer.deserialize_option,
    TypeIdUnion: JsonDeserializer.deserialize_union,
    TypeIdTuple: JsonDeserializer.deserialize_tuple,
    TypeIdSet: JsonDeserializer.deserialize_set,
    TypeIdMap: JsonDeserializer.deserialize_map,
}
