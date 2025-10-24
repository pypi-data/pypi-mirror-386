from __future__ import annotations
import static_refl as sr
from dataclasses import dataclass, asdict
import datetime

@dataclass(frozen=True)
class Sample:
    id: int
    name: str

@sr.refl_options(rename_all="kebab-case")
@dataclass
class Sample2:
    id: int
    full_name: str

@dataclass
class Sample3[T]:
    id: int
    elements: list[datetime.datetime | T]

@dataclass
class Sample4[T]:
    id: int
    elements: tuple[T, ...]

@dataclass
class Sample5:
    id: int
    info: dict[str, tuple[int, Sample]]

d = asdict(Sample(id = 1, name = "Test"))
print(d)
assert(sr.json.Schema[Sample].to_typed(d) == Sample(id = 1, name = "Test"))

d2 = sr.json.Schema[Sample2].to_untyped(Sample2(id = 2, full_name = "Example"))
print(d2)
assert d2['full-name'] == "Example"

d3 = asdict(Sample3[int](id = 3, elements = [1, 2, 3, datetime.datetime.now()]))
print(d3)
v3 = sr.json.Schema[Sample3[int]].to_typed(d3)
assert v3.elements[:3] == [1, 2, 3]
assert isinstance(v3.elements[-1], datetime.datetime)

d4 = asdict(Sample4[str](id = 4, elements = ("a", "b", "c")))
print(d4)
assert sr.json.Schema[Sample4[str]].to_typed(d4).elements == ("a", "b", "c")

d5 = asdict(Sample5(id = 5, info = {"first": (10, Sample(id=100, name="Nested"))}))
print(d5)
v5 = sr.json.Schema[Sample5].to_typed(d5)
assert v5.info["first"][0] == 10
assert v5.info["first"][1] == Sample(id=100, name="Nested")