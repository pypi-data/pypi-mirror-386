import typing
import casefy

if typing.TYPE_CHECKING:
    def cache(func):
        return func
else:
    from functools import lru_cache

    cache = lru_cache(maxsize=64)


@cache
def transform_case(
    x: str,
    case: typing.Literal[
        "kebab-case", "snake_case", "lowercase", "UPPERCASE", "camelCase"
    ]
    | None,
):
    if case is None:
        return x
    match case:
        case "kebab-case":
            return casefy.kebabcase(x)
        case "snake_case":
            return casefy.snakecase(x)
        case "lowercase":
            return casefy.lowercase(x)
        case "UPPERCASE":
            return casefy.uppercase(x)
        case "camelCase":
            return casefy.camelcase(x)
    raise ValueError(f"Unknown case: {case}")
