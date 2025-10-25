from typing import List

from pydantic import BaseModel

from bpkio_api.models.common import BaseResource, NamedModel


class SubCategory(BaseModel):
    key: str
    value: str


class CategoryIn(NamedModel):
    subcategories: List[SubCategory] = []

    @property
    def subcategories_list(self):
        return ", ".join(f"{sc.key}:{sc.value}" for sc in self.subcategories)


class Category(BaseResource, CategoryIn):
    pass
