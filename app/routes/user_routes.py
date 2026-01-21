from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.db.session import get_db
from app.models.brand import Brand
from app.models.categories import Category
from app.models.products import Product
from app.models.cart import Cart
from app.models.enquiries import Enquiry
from app.models.enquiry_items import EnquiryItem

router = APIRouter(prefix="/user", tags=["User"])


# ================= CATEGORIES =================
@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category)\
        .filter(Category.is_active == True)\
        .order_by(Category.name.asc())\
        .all()

    return [
        {
            "category_id": c.category_id,
            "name": c.name,
            "description": c.description,
            "image": f"/static/category_images/{c.image}"
        }
        for c in categories
    ]


# ================= BRANDS =================
@router.get("/brands")
def list_brands(db: Session = Depends(get_db)):
    brands = db.query(Brand)\
        .filter(Brand.is_active == True)\
        .order_by(Brand.name.asc())\
        .all()

    return [
        {
            "brand_id": b.brand_id,
            "name": b.name,
            "image": f"/static/brand_images/{b.image}" if b.image else None
        }
        for b in brands
    ]


# ================= PRODUCTS (CATEGORY / BRAND) =================
@router.get("/products")
def get_products(
    category_id: str | None = None,
    brand_id: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product)\
        .filter(Product.is_active == True)

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if brand_id:
        query = query.filter(Product.brand_id == brand_id)

    products = query.order_by(Product.name.asc()).all()

    return format_products(products)


# ================= ADVANCED SEARCH =================
@router.get("/products/search")
def search_products(q: str, db: Session = Depends(get_db)):
    products = (
        db.query(Product)
        .join(Category, Product.category_id == Category.category_id)
        .join(Brand, Product.brand_id == Brand.brand_id)
        .filter(
            Product.is_active == True,
            or_(
                Product.name.ilike(f"%{q}%"),
                Product.description.ilike(f"%{q}%"),
                Category.name.ilike(f"%{q}%"),
                Brand.name.ilike(f"%{q}%")
            )
        )
        .all()
    )

    return format_products(products)


# ================= ADVANCED FILTER =================
@router.post("/products/filter")
def filter_products(filters: dict, db: Session = Depends(get_db)):
    query = db.query(Product)\
        .filter(Product.is_active == True)

    if filters.get("category_ids"):
        query = query.filter(Product.category_id.in_(filters["category_ids"]))

    if filters.get("brand_ids"):
        query = query.filter(Product.brand_id.in_(filters["brand_ids"]))

    if filters.get("min_price") is not None:
        query = query.filter(Product.price >= filters["min_price"])

    if filters.get("max_price") is not None:
        query = query.filter(Product.price <= filters["max_price"])

    if filters.get("min_order_qty") is not None:
        query = query.filter(Product.min_order_qty >= filters["min_order_qty"])

    if filters.get("in_stock"):
        query = query.filter(Product.stock > 0)

    products = query.order_by(Product.name.asc()).all()
    return format_products(products)


# ================= CART =================
@router.post("/cart/add")
def add_to_cart(product_id: str, quantity: int, session_id: str, db: Session = Depends(get_db)):
    item = db.query(Cart)\
        .filter(Cart.session_id == session_id, Cart.product_id == product_id)\
        .first()

    if item:
        item.quantity += quantity
    else:
        db.add(Cart(session_id=session_id, product_id=product_id, quantity=quantity))

    db.commit()
    return {"message": "Added to cart"}


@router.get("/cart")
def view_cart(session_id: str, db: Session = Depends(get_db)):
    items = (
        db.query(Cart, Product)
        .join(Product, Cart.product_id == Product.product_id)
        .filter(Cart.session_id == session_id)
        .all()
    )

    cart_items = [
        {
            "product_id": p.product_id,
            "name": p.name,
            "quantity": c.quantity,
            "price": float(p.price),
            "total_price": float(c.quantity * p.price),
            "image": f"/static/product_images/{p.image}"
        }
        for c, p in items
    ]

    return {
        "items": cart_items,
        "all_total_price": sum(i["total_price"] for i in cart_items)
    }


@router.delete("/cart/remove")
def remove_cart_item(product_id: str, session_id: str, db: Session = Depends(get_db)):
    db.query(Cart)\
        .filter(Cart.session_id == session_id, Cart.product_id == product_id)\
        .delete()

    db.commit()
    return {"message": "Item removed"}


# ================= ENQUIRY =================
@router.post("/enquiry")
def submit_enquiry(customer_name: str, address: str, phone: str, session_id: str, db: Session = Depends(get_db)):
    enquiry = Enquiry(customer_name=customer_name, address=address, phone=phone)
    db.add(enquiry)
    db.commit()
    db.refresh(enquiry)

    cart_items = db.query(Cart).filter(Cart.session_id == session_id).all()

    for item in cart_items:
        db.add(EnquiryItem(
            enquiry_id=enquiry.id,
            product_id=item.product_id,
            quantity=item.quantity
        ))

    db.query(Cart).filter(Cart.session_id == session_id).delete()
    db.commit()

    return {"message": "Enquiry submitted successfully"}


# ================= COMMON FORMATTER =================
def format_products(products):
    return [
        {
            "product_id": p.product_id,
            "name": p.name,
            "description": p.description,
            "price": float(p.price),
            "min_order_qty": p.min_order_qty,
            "stock": p.stock,
            "category_id": p.category_id,
            "brand_id": p.brand_id,
            "image": f"/static/product_images/{p.image}"
        }
        for p in products
    ]
