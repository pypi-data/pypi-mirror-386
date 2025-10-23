import dataclasses
import json

import pydantic
import typing_extensions as typing


@dataclasses.dataclass
class Nested:
    value: int = -1


@dataclasses.dataclass
class Base:
    __pydantic_config__ = pydantic.ConfigDict(
        validate_assignment=True,
        revalidate_instances="always",
        use_attribute_docstrings=True,
    )
    value: str = ""
    nested: Nested = dataclasses.field(default_factory=Nested)

    @classmethod
    def to_pydantic_dataclass(cls) -> type[typing.Self]:
        """Create a pydantic dataclass from the Config."""
        subclass = type(cls.__name__, (cls,), {})
        return pydantic.dataclasses.dataclass(subclass)

    @staticmethod
    def get_default() -> dict:
        """Get the default dictionary representation of the config."""
        configs = [b for b in Base.__subclasses__() if b.__name__ != "Base"]
        if not configs:
            raise ValueError
        config = configs[0]
        type_adapter = pydantic.TypeAdapter(config)
        return json.loads(type_adapter.dump_json(config()))

    @classmethod
    def load(cls, data: dict) -> typing.Self:
        """This docstring breaks everything ?

        Args:
          data: the data to load into the cls.
        """
        return cls.to_pydantic_dataclass()(**data)


# data = {"value": "a", "nested": {"value": 0}}
try:

    @dataclasses.dataclass
    class Derived(Base):
        more: str = "yes"

        @pydantic.field_validator("simple")
        @classmethod
        def must_be_true(cls, value: bool) -> bool:
            if not value:
                msg = "simple must be True."
                raise ValueError(msg)
            return value

    data = Derived.get_default()
    loaded = Derived.load(data)
    print(loaded)
except SyntaxError:
    print("how?")
else:
    print("alles gut.")
