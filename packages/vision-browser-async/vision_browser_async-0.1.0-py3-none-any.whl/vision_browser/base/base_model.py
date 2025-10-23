from typing import Self

from pydantic import BaseModel as _BaseModel

class BaseModel(_BaseModel):
    pass

    @classmethod
    def load(cls, data: dict) -> Self:
        return cls.model_validate(data)

    @classmethod
    def load_list(cls, data: list[dict]) -> list[Self]:
        return [cls.load(item) for item in data]