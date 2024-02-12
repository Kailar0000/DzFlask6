from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import starlette.status as status
from typing import List
from hashlib import sha256

from data_model import User, Product, Order
from db import database, users, products, orders



app = FastAPI()


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.api_route("/", methods=['GET', 'HEAD'], response_class=RedirectResponse)
async def main_page():
    return RedirectResponse(url="/docs", status_code=status.HTTP_302_FOUND)


@app.api_route("/user/", methods=['GET', 'HEAD'], response_model=List[User])
async def get_all_users():
    return await database.fetch_all(users.select())


@app.api_route("/product/", methods=['GET', 'HEAD'], response_model=List[Product])
async def get_all_products():
    return await database.fetch_all(products.select())


@app.api_route("/order/", methods=['GET', 'HEAD'], response_model=List[Order])
async def get_all_orders():
    return await database.fetch_all(orders.select())


@app.api_route("/user/{user_id}", methods=['GET', 'HEAD'], response_model=User)
async def get_user(user_id: int):
    user = await database.fetch_one(users.select().where(users.c.id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id '{user_id}' not found")
    return user


@app.api_route("/product/{product_id}", methods=['GET', 'HEAD'], response_model=Product)
async def get_product(product_id: int):
    product = await database.fetch_one(products.select().where(products.c.id == product_id))
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with id '{product_id}' not found")
    return product


@app.api_route("/order/{order_id}", methods=['GET', 'HEAD'], response_model=Order)
async def get_order(order_id: int):
    order = await database.fetch_one(orders.select().where(orders.c.id == order_id))
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order with id '{order_id}' not found")
    return order


@app.post("/user/", response_model=User)
async def create_user(user: User):
    del user.id
    user.password = sha256(user.password.encode("utf-8")).hexdigest()
    query = users.insert().values(
        **user.model_dump())
    user.id = await database.execute(query)
    return user


@app.post("/product/", response_model=Product)
async def create_product(product: Product):
    del product.id
    query = products.insert().values(
        **product.model_dump())
    product.id = await database.execute(query)
    return product


@app.post("/order/", response_model=Order)
async def create_order(order: Order):
    del order.id
    user = await database.fetch_one(users.select().where(users.c.id == order.user_id))
    product = await database.fetch_one(products.select().where(products.c.id == order.product_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"User with id '{order.user_id}' not exist")
    if not product:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Product with id '{order.product_id}' not exist")
    query = orders.insert().values(
        **order.model_dump())
    order.id = await database.execute(query)
    return order


@app.put("/user/{user_id}", response_model=User)
async def update_user(user_id: int, new_user: User):
    user = await database.fetch_one(users.select().where(users.c.id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id '{user_id}' not found")
    new_user.id = user_id
    new_user.password = sha256(new_user.password.encode("utf-8")).hexdigest()
    query = users.update().where(users.c.id == user_id).values(**new_user.model_dump())
    await database.execute(query)
    return new_user


@app.put("/product/{product_id}", response_model=Product)
async def update_product(product_id: int, new_product: Product):
    product = await database.fetch_one(products.select().where(products.c.id == product_id))
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with id '{product_id}' not found")
    new_product.id = product_id
    query = products.update().where(products.c.id == product_id).values(**new_product.model_dump())
    await database.execute(query)
    return new_product


@app.put("/order/{order_id}", response_model=Order)
async def update_order(order_id: int, new_order: Order):
    order = await database.fetch_one(orders.select().where(orders.c.id == order_id))
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order with id '{order_id}' not found")
    user = await database.fetch_one(users.select().where(users.c.id == order.user_id))
    product = await database.fetch_one(products.select().where(products.c.id == order.product_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"User with id '{order.user_id}' not exist")
    if not product:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Product with id '{order.product_id}' not exist")
    new_order.id = order_id
    query = orders.update().where(orders.c.id == order_id).values(**new_order.model_dump())
    await database.execute(query)
    return new_order


@app.delete("/user/{user_id}")
async def delete_user(user_id: int):
    # TODO: add 404 if trying to delete not existing element
    user_orders = await database.fetch_one(orders.select().where(orders.c.user_id == user_id))
    if user_orders:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"User has Orders, delete Orders first")
    await database.execute(users.delete().where(users.c.id == user_id))
    return {"message": "User deleted"}


@app.delete("/product/{product_id}")
async def delete_product(product_id: int):
    # TODO: add 404 if trying to delete not existing element
    product_orders = await database.fetch_one(orders.select().where(orders.c.product_id == product_id))
    if product_orders:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"This product included in Orders, delete Orders first")
    await database.execute(products.delete().where(products.c.id == product_id))
    return {"message": "Product deleted"}


@app.delete("/order/{order_id}")
async def delete_order(order_id: int):
    # TODO: add 404 if trying to delete not existing element
    await database.execute(orders.delete().where(orders.c.id == order_id))
    return {"message": "Order deleted"}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
