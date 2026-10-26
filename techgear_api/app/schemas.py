from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints
from pydantic import computed_field, model_validator

NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UserCreate(Schema):
    username: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=3, max_length=150)
    ]
    email: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=3, max_length=254)
    ]
    role: Literal["customer", "admin"] = "customer"


class UserOut(Schema):
    id: str
    username: str
    email: str
    role: Literal["customer", "admin"]


class Variant(Schema):
    size: NonEmptyString
    color: NonEmptyString
    stock: int = Field(ge=0)


class ProductCreate(Schema):
    name: NonEmptyString
    description: NonEmptyString
    price: float = Field(gt=0, allow_inf_nan=False)
    category: NonEmptyString
    variants: list[Variant] = Field(min_length=1)
    image_url: HttpUrl | None = None
    active: bool = True

    @model_validator(mode="after")
    def variants_are_unique(self):
        keys = [(v.size.casefold(), v.color.casefold()) for v in self.variants]
        if len(keys) != len(set(keys)):
            raise ValueError("Each size and color combination must be unique")
        return self


class ProductUpdate(Schema):
    name: NonEmptyString | None = None
    description: NonEmptyString | None = None
    price: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    category: NonEmptyString | None = None
    variants: list[Variant] | None = Field(default=None, min_length=1)
    image_url: HttpUrl | None = None
    active: bool | None = None

    @model_validator(mode="after")
    def variants_are_unique(self):
        if self.variants is not None:
            keys = [(v.size.casefold(), v.color.casefold()) for v in self.variants]
            if len(keys) != len(set(keys)):
                raise ValueError("Each size and color combination must be unique")
        return self


class ProductOut(ProductCreate):
    id: str = Field(validation_alias="_id")

    @computed_field
    @property
    def stock(self) -> int:
        return sum(variant.stock for variant in self.variants)


class OrderItemCreate(Schema):
    product_id: NonEmptyString
    size: NonEmptyString
    color: NonEmptyString
    quantity: int = Field(gt=0)


class OrderCreate(Schema):
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderItemOut(Schema):
    product_id: str
    name: str
    size: str
    color: str
    quantity: int
    unit_price: float
    subtotal: float


class OrderOut(Schema):
    id: str
    customer: NonEmptyString
    items: list[OrderItemOut]
    total: float
    status: str = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
