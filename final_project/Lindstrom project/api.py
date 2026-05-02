from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from warehouse import (
    build_dashboard_data,
    build_multi_dashboard_data,
    warehouse,
    start_position,
    get_all_products,
    get_product_by_id,
    get_products_by_ids
)

app = FastAPI(title="Smart Warehouse Navigation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Smart Warehouse Navigation API is running"}

@app.get("/products")
def get_products():
    return {"products": get_all_products()}

@app.get("/dashboard")
def get_dashboard(
    product_id: str = Query("C1"),
    mode: str = Query("smart")
):
    selected_product = get_product_by_id(product_id)

    if selected_product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    if mode not in ["basic", "smart"]:
        raise HTTPException(status_code=400, detail="Mode must be 'basic' or 'smart'")

    return build_dashboard_data(warehouse, start_position, selected_product, mode=mode)

@app.get("/multi-dashboard")
def get_multi_dashboard(
    product_ids: str = Query("C1,C2"),
):
    product_id_list = [item.strip() for item in product_ids.split(",") if item.strip()]
    selected_products = get_products_by_ids(product_id_list)

    if len(selected_products) < 2 or len(selected_products) > 4:
        raise HTTPException(status_code=400, detail="Select between 2 and 4 valid products")

    return build_multi_dashboard_data(warehouse, start_position, selected_products)