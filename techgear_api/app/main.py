from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, status
from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from app.config import settings
from app.database import create_mongo_client, get_database
from app.schemas import (
    OrderCreate,
    OrderItemOut,
    OrderOut,
    ProductCreate,
    ProductOut,
    ProductUpdate,
)
from app.security import require_admin, require_client


@asynccontextmanager
async def lifespan(application: FastAPI):
    client = create_mongo_client()
    application.state.mongo_client = client
    application.state.database = client[settings.mongodb_database]
    try:
        await client.admin.command("ping")
        yield
    finally:
        await client.close()


app = FastAPI(
    title="UNDERGRAWN | JOSE_DM API",
    description="API de prendas, variantes e pedidos.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["health"])
async def health(
    database: AsyncDatabase = Depends(get_database),
) -> dict[str, str]:
    await database.command("ping")
    return {"status": "ok"}


@app.get("/products", response_model=list[ProductOut], tags=["products"])
async def list_products(
    category: str | None = Query(default=None, min_length=1),
    database: AsyncDatabase = Depends(get_database),
) -> list[dict]:
    query: dict = {"active": True}
    if category:
        query["category"] = category
    return await database.products.find(query).sort("name", 1).to_list(500)


@app.get("/products/{product_id}", response_model=ProductOut, tags=["products"])
async def get_product(
    product_id: str,
    database: AsyncDatabase = Depends(get_database),
) -> dict:
    product = await database.products.find_one({"_id": product_id, "active": True})
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post(
    "/products",
    response_model=ProductOut,
    status_code=status.HTTP_201_CREATED,
    tags=["products"],
    dependencies=[Depends(require_admin)],
)
async def create_product(
    product: ProductCreate,
    database: AsyncDatabase = Depends(get_database),
) -> dict:
    document = product.model_dump(mode="json")
    document["_id"] = str(uuid4())
    await database.products.insert_one(document)
    return document


@app.patch(
    "/products/{product_id}",
    response_model=ProductOut,
    tags=["products"],
    dependencies=[Depends(require_admin)],
)
async def update_product(
    product_id: str,
    product: ProductUpdate,
    database: AsyncDatabase = Depends(get_database),
) -> dict:
    updates = product.model_dump(exclude_unset=True, mode="json")
    if not updates:
        raise HTTPException(status_code=422, detail="At least one field is required")
    if any(value is None for key, value in updates.items() if key != "image_url"):
        raise HTTPException(status_code=422, detail="Fields cannot be set to null")
    result = await database.products.update_one({"_id": product_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return await database.products.find_one({"_id": product_id})


@app.delete(
    "/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["products"],
    dependencies=[Depends(require_admin)],
)
async def delete_product(
    product_id: str,
    database: AsyncDatabase = Depends(get_database),
) -> None:
    result = await database.products.update_one(
        {"_id": product_id}, {"$set": {"active": False}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")


@app.post(
    "/orders",
    response_model=OrderOut,
    status_code=status.HTTP_201_CREATED,
    tags=["orders"],
    dependencies=[Depends(require_client)],
)
async def create_order(
    order: OrderCreate,
    customer: str = Query(min_length=1, max_length=150),
    database: AsyncDatabase = Depends(get_database),
) -> dict:
    quantities: dict[tuple[str, str, str], int] = {}
    for item in order.items:
        key = (item.product_id, item.size, item.color)
        quantities[key] = quantities.get(key, 0) + item.quantity

    products: list[dict] = []
    try:
        for (product_id, size, color), quantity in quantities.items():
            product = await database.products.find_one_and_update(
                {
                    "_id": product_id,
                    "active": True,
                    "variants": {
                        "$elemMatch": {
                            "size": size,
                            "color": color,
                            "stock": {"$gte": quantity},
                        }
                    },
                },
                {"$inc": {"variants.$.stock": -quantity}},
                return_document=ReturnDocument.AFTER,
            )
            if product is None:
                raise HTTPException(
                    status_code=409,
                    detail=f"Variant {size}/{color} is unavailable or has insufficient stock",
                )
            products.append(
                {
                    "product": product,
                    "size": size,
                    "color": color,
                    "quantity": quantity,
                }
            )
    except Exception:
        for reserved in products:
            await database.products.update_one(
                {
                    "_id": reserved["product"]["_id"],
                    "variants": {
                        "$elemMatch": {
                            "size": reserved["size"],
                            "color": reserved["color"],
                        }
                    },
                },
                {"$inc": {"variants.$.stock": reserved["quantity"]}},
            )
        raise

    items = [
        OrderItemOut(
            product_id=reservation["product"]["_id"],
            name=reservation["product"]["name"],
            size=reservation["size"],
            color=reservation["color"],
            quantity=reservation["quantity"],
            unit_price=reservation["product"]["price"],
            subtotal=round(
                reservation["product"]["price"] * reservation["quantity"], 2
            ),
        )
        for reservation in products
    ]
    document = {
        "_id": str(uuid4()),
        "customer": customer,
        "items": [item.model_dump() for item in items],
        "total": round(sum(item.subtotal for item in items), 2),
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
    }
    try:
        await database.orders.insert_one(document)
    except Exception:
        for (product_id, size, color), quantity in quantities.items():
            await database.products.update_one(
                {
                    "_id": product_id,
                    "variants": {"$elemMatch": {"size": size, "color": color}},
                },
                {"$inc": {"variants.$.stock": quantity}},
            )
        raise
    document["id"] = document.pop("_id")
    return document


@app.get("/orders", response_model=list[OrderOut], tags=["orders"])
async def list_orders(
    customer: str = Query(min_length=1, max_length=150),
    _: None = Depends(require_client),
    database: AsyncDatabase = Depends(get_database),
) -> list[dict]:
    orders = await database.orders.find({"customer": customer}).sort(
        "created_at", -1
    ).to_list(100)
    for order in orders:
        order["id"] = order.pop("_id")
    return orders
