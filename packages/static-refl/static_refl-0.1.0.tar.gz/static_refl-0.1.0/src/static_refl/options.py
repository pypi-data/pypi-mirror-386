import typing

_OPTIONS_FILED = "__srefl_class_options__"
_DONE_FIELD = "__srefl_class_done__"


class SerdeOptions(typing.TypedDict):
    rename_map: dict[str, str]
    rename_all: (
        typing.Literal[
            "kebab-case", "snake_case", "lowercase", "UPPERCASE", "camelCase"
        ]
        | None
    )


def _assure_options(cls) -> SerdeOptions:
    if isinstance(cls, type):
        if not hasattr(cls, _OPTIONS_FILED):
            setattr(
                cls,
                _OPTIONS_FILED,
                {
                    "rename_map": {},
                    "rename_all": None,
                },
            )
        return getattr(cls, _OPTIONS_FILED)
    return cls


def refl_options(
    rename_all: typing.Literal[
        "kebab-case", "snake_case", "lowercase", "UPPERCASE", "camelCase"
    ]
    | None = None,
):
    def wrapper(cls):
        if hasattr(cls, _DONE_FIELD):
            raise RuntimeError("Cannot apply refl_options() on a finalized class")

        opts = _assure_options(cls)
        if rename_all is not None:
            opts["rename_all"] = rename_all
        return cls

    return wrapper


def refl_rename(**kwargs: str):
    """Rename the fields when used in serialization context."""

    def wrapper(cls):
        if hasattr(cls, _DONE_FIELD):
            raise RuntimeError("Cannot apply refl_rename() on a finalized class")
        options = _assure_options(cls)
        options["rename_map"].update(kwargs)
        return cls

    return wrapper


def get_refl_options(cls) -> SerdeOptions:
    if not hasattr(cls, _DONE_FIELD):
        setattr(cls, _DONE_FIELD, True)

    opts = _assure_options(cls)
    return typing.cast(SerdeOptions, opts)
