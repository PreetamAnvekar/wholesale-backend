from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.session import get_db
from app.models.categories import Category
from app.models.products import Product
from app.models.cart import Cart
from app.models.enquiries import Enquiry
from app.models.enquiry_items import EnquiryItem

router = APIRouter(prefix="/user", tags=["User"])



# ================= CATEGORIES =================

@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    categories = (
        db.query(Category)
        .filter(Category.is_active == True)
        .order_by(Category.name.asc())
        .all()
    )

    return [
        {
            "category_id": c.category_id,
            "name": c.name,
            "description": c.description,
            "image": f"/static/category_images/{c.image}"
        }
        for c in categories
    ]


@router.get("/categories/{category_id}/products")
def get_products_by_category(category_id: str, db: Session = Depends(get_db)):
    products = (
        db.query(Product)
        .filter(
            Product.category_id == category_id,
            Product.is_active == True
        )
        .order_by(Product.name.asc())
        .all()
    )

    return [
        {
            "product_id": p.product_id,
            "name": p.name,
            "description": p.description,
            "price": float(p.price),
            "min_order_qty": p.min_order_qty,
            "stock": p.stock,
            "image": f"/static/product_images/{p.image}"
        }
        for p in products
    ]


# ================= SEARCH & FILTER =================

@router.get("/products/search")
def search_products(q: str, db: Session = Depends(get_db)):
    products = (
        db.query(Product)
        .filter(
            Product.is_active == True,
            or_(
                Product.name.ilike(f"%{q}%"),
                Product.description.ilike(f"%{q}%")
            )
        )
        .all()
    )

    return [
        {
            "product_id": p.product_id,
            "name": p.name,
            "price": float(p.price),
            "stock": p.stock,
            "image": f"/static/product_images/{p.image}"
        }
        for p in products
    ]


@router.post("/products/filter")
def filter_products(filters: dict, db: Session = Depends(get_db)):
    query = db.query(Product).filter(Product.is_active == True)

    if filters.get("category_ids"):
        query = query.filter(Product.category_id.in_(filters["category_ids"]))

    if filters.get("min_price") is not None:
        query = query.filter(Product.price >= filters["min_price"])

    if filters.get("max_price") is not None:
        query = query.filter(Product.price <= filters["max_price"])

    if filters.get("in_stock"):
        query = query.filter(Product.stock > 0)

    products = query.all()

    return [
        {
            "product_id": p.product_id,
            "name": p.name,
            "price": float(p.price),
            "stock": p.stock,
            "image": f"/static/product_images/{p.image}"
        }
        for p in products
    ]


# ================= CART =================

@router.post("/cart/add")
def add_to_cart(product_id: str, quantity: int, session_id: str, db: Session = Depends(get_db)):
    item = db.query(Cart).filter(
        Cart.session_id == session_id,
        Cart.product_id == product_id
    ).first()

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

    all_total_price = sum(item["total_price"] for item in cart_items)

    return {
        "items": cart_items,
        "all_total_price": all_total_price
    }



@router.delete("/cart/remove")
def remove_cart_item(product_id: str, session_id: str, db: Session = Depends(get_db)):
    db.query(Cart).filter(
        Cart.session_id == session_id,
        Cart.product_id == product_id
    ).delete()
    db.commit()
    return {"message": "Item removed"}


# ================= ENQUIRY =================

@router.post("/enquiry")
def submit_enquiry(customer_name: str, phone: str, session_id: str, db: Session = Depends(get_db)):
    enquiry = Enquiry(customer_name=customer_name, phone=phone)
    db.add(enquiry)
    db.commit()
    db.refresh(enquiry)

    cart_items = db.query(Cart).filter(Cart.session_id == session_id).all()

    for item in cart_items:
        db.add(
            EnquiryItem(
                enquiry_id=enquiry.id,
                product_id=item.product_id,
                quantity=item.quantity
            )
        )

    db.query(Cart).filter(Cart.session_id == session_id).delete()
    db.commit()

    return {"message": "Enquiry submitted"}
