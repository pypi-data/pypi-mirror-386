from static_refl.core import (
    TypeId,
    TypeIdDataClass,
    TypeIdTypedDict,
    TypeIdUnion,
    TypeIdLit,
    TypeIdAny,
)
import dataclasses
import typing
import enum

if typing.TYPE_CHECKING:

    def cache(f):
        return f
else:
    from functools import cache


@dataclasses.dataclass(frozen=True)
class TagInfo:
    name: str
    value: typing.Any


class SplitFastTell(enum.Enum):
    mixed = 1
    all_dataclass = 2
    all_lit = 3
    all_other = 4


@dataclasses.dataclass(frozen=True)
class OrthogonalSplit:
    dataclasses: dict[str | int, TypeIdDataClass]
    typeddicts: dict[str | int, TypeIdTypedDict]
    literals: dict[typing.Any, TypeIdLit]
    others: dict[type, TypeId]
    fast_tell: SplitFastTell

    typeddict_tagname: str | None = None
    dataclass_tagname: str | None = None
    has_any: bool = False


@cache
def orthogonal_split(tid: TypeIdUnion):
    dataclass_cases: dict[str | int, TypeIdDataClass] = {}
    typeddict_cases: dict[str | int, TypeIdTypedDict] = {}
    literal_cases: dict[typing.Any, TypeIdLit] = {}
    other_cases: dict[type, TypeId] = {}

    typeddict_tagname: str | None = None
    dataclass_tagname: str | None = None
    has_any = False
    for utid in tid.choices:
        if isinstance(utid, TypeIdDataClass):
            tag_info = _get_tag_info(utid)
            if not dataclass_tagname:
                dataclass_tagname = tag_info.name
            else:
                if dataclass_tagname != tag_info.name:
                    raise ValueError(
                        f"All dataclasses in a union must have the same tag field name, got {dataclass_tagname} and {tag_info.name}"
                    )
            dataclass_cases[tag_info.value] = utid
        elif isinstance(utid, TypeIdTypedDict):
            tag_info = _get_tag_info(utid)
            if not typeddict_tagname:
                typeddict_tagname = tag_info.name
            else:
                if typeddict_tagname != tag_info.name:
                    raise ValueError(
                        f"All typeddicts in a union must have the same tag field name and value, got {typeddict_tagname} and {tag_info.name}"
                    )
            typeddict_cases[tag_info.value] = utid
        elif isinstance(utid, TypeIdLit):
            literal_cases[utid.literal] = utid
        elif isinstance(utid, TypeIdAny):
            has_any = True
        else:
            other_cases[utid.pytype] = utid

    fast_tell = SplitFastTell.mixed
    if not has_any:
        count_all_cases = (
            len(dataclass_cases)
            + len(typeddict_cases)
            + len(literal_cases)
            + len(other_cases)
        )
        if count_all_cases == len(dataclass_cases):
            fast_tell = SplitFastTell.all_dataclass
        elif count_all_cases == len(literal_cases):
            fast_tell = SplitFastTell.all_lit
        elif count_all_cases == len(other_cases):
            fast_tell = SplitFastTell.all_other

    return OrthogonalSplit(
        dataclasses=dataclass_cases,
        typeddicts=typeddict_cases,
        literals=literal_cases,
        others=other_cases,
        typeddict_tagname=typeddict_tagname,
        dataclass_tagname=dataclass_tagname,
        has_any=has_any,
        fast_tell=fast_tell,
    )


@cache
def _get_tag_info(tp: TypeIdDataClass | TypeIdTypedDict):
    fields = tp.structure.fields
    if not fields:
        raise ValueError(
            f"Data types with empty fields cannot be used in union serialization: {tp.class_obj.__qualname__}"
        )
    first_field = fields[0]
    first_field_type = first_field.type
    if not isinstance(first_field_type, TypeIdLit):
        raise ValueError(
            f"Data types supporting union serialization must have a first field with literal type: {tp.class_obj.__qualname__}.{first_field.name}"
        )

    lit = first_field_type.literal
    if not isinstance(lit, (str, int)):
        raise ValueError(
            f"Data types supporting union serialization must have a first field with int or str literal type: {tp.class_obj.__qualname__}.{first_field.name}"
        )
    return TagInfo(first_field.name, lit)
