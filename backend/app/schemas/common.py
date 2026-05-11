from pydantic import BaseModel, ConfigDict


class Page(BaseModel):
    items: list
    total: int
    page: int = 1
    page_size: int = 20


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
