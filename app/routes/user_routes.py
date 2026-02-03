# ==========================================================
# USER API – SINGLE FILE (CART + CHECKOUT) – FIXED
# ==========================================================

import os
import uuid
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response
)
from sqlalchemy.orm import Session
from sqlalchemy import or_

# ================= DB =================
from app.db.session import get_db

# ================= MODELS =================
from app.models.categories import Category
from app.models.brand import Brand
from app.models.products import Product
from app.models.cart import Cart
from app.models.enquiries import Enquiry
from app.models.enquiry_items import EnquiryItem
from app.models.user_visits import UserVisit

# ================= CONFIG =================
from app.core.config import settings
from app.core.storage import CATEGORY_DIR, PRODUCT_DIR, BRAND_DIR

router = APIRouter(prefix="/user", tags=["User"])

# ==========================================================
# 🔐 COOKIE BASED SESSION (1 DAY)
# ==========================================================

def get_user_session(request: Request, response: Response):
    session_id = request.cookies.get("session_id")

    if not session_id:
        session_id = str(uuid.uuid4())
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            max_age=60 * 60 * 24,
            samesite="lax", 
            secure=settings.ENV == "production"
        )
    return session_id

# ==========================================================
# USER VISIT LOGGER (UserVisit TABLE)
# ==========================================================

def log_user_visit(db: Session, request: Request, session_id: str):
    try:
        db.add(UserVisit(
            session_id=session_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            visited_page=request.url.path,
            referer=request.headers.get("referer"),
            device_type="mobile" if "Mobile" in (request.headers.get("user-agent") or "") else "desktop",
            browser=request.headers.get("user-agent"),
            os=request.headers.get("user-agent")
        ))
        print(
            session_id,
            request.client.host if request.client else None,
            request.headers.get("user-agent"),
            request.url.path,
            request.headers.get("referer"),
            "mobile" if "Mobile" in (request.headers.get("user-agent") or "") else "desktop",
            request.headers.get("user-agent"),
            request.headers.get("user-agent")
        )
        print("User visit logged successfully")
        db.commit()
    except Exception:
        print("Error logging user visit")
        db.rollback()

# ==========================================================
# DELIVERY RULE
# ==========================================================

def calculate_delivery(subtotal: float):
    if subtotal >= 1500:
        return 0
    elif subtotal >= 1200:
        return 30
    return 60

def img(path, image):
    return os.path.join(path, image).split("app/")[-1] if image else None

# ==========================================================
# 📂 CATEGORY & BRAND
# ==========================================================

@router.get("/categories")
def list_categories(request: Request, response: Response, db: Session = Depends(get_db)):
    session_id = get_user_session(request, response)
    log_user_visit(db, request, session_id)

    return [
        {
            "category_id": c.category_id,
            "name": c.name,
            "image": img(CATEGORY_DIR, c.image)
        }
        for c in db.query(Category).filter(Category.is_active == True).all()
    ]

@router.get("/brands")
def list_brands(request: Request, response: Response, db: Session = Depends(get_db)):
    session_id = get_user_session(request, response)
    log_user_visit(db, request, session_id)

    return [
        {
            "brand_id": b.brand_id,
            "name": b.name,
            "image": img(BRAND_DIR, b.image)
        }
        for b in db.query(Brand).filter(Brand.is_active == True).all()
    ]

@router.get("/categories/{category_id}/products")
def products_by_category(
    category_id: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    session_id = get_user_session(request, response)
    log_user_visit(db, request, session_id)

    return [
        {
            "product_id": p.product_id,
            "name": p.name,
            "description": p.description,
            "mrp": float(p.mrp),
            "price": float(p.price),
            "min_order_qty": p.min_order_qty,
            "pack_size": p.pack_size,
            "category": db.query(Category).filter(Category.category_id == p.category_id).first().name if p.category_id else p.category_id,
            "brand": db.query(Brand).filter(Brand.brand_id == p.brand_id).first().name if p.brand_id else p.brand_id,
            "image": img(PRODUCT_DIR, p.image)
        }
        for p in db.query(Product).filter(
            Product.category_id == category_id,
            Product.is_active == True
        ).all()
    ]

@router.get("/brands/{brand_id}/products")
def products_by_brand(
    brand_id: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    session_id = get_user_session(request, response)
    log_user_visit(db, request, session_id)

    return [
        {
            "product_id": p.product_id,
            "name": p.name,
            "description": p.description,
            "mrp": float(p.mrp),
            "price": float(p.price),
            "min_order_qty": p.min_order_qty,
            "pack_size": p.pack_size,
            "category": db.query(Category).filter(Category.category_id == p.category_id).first().name if p.category_id else p.category_id,
            "brand": db.query(Brand).filter(Brand.brand_id == p.brand_id).first().name if p.brand_id else p.brand_id,
            "image": img(PRODUCT_DIR, p.image)
        }
        for p in db.query(Product).filter(
            Product.brand_id == brand_id,
            Product.is_active == True
        ).all()
    ]

# ==========================================================
# 📦 PRODUCTS
# ==========================================================

@router.get("/products")
def list_products(request: Request, response: Response, db: Session = Depends(get_db)):
    session_id = get_user_session(request, response)
    log_user_visit(db, request, session_id)

    return [
        {
            "product_id": p.product_id,
            "name": p.name,
            "description": p.description,
            "mrp": float(p.mrp),
            "price": float(p.price),
            "min_order_qty": p.min_order_qty,
            "pack_size": p.pack_size,
            "category": db.query(Category).filter(Category.category_id == p.category_id).first().name if p.category_id else p.category_id,
            "brand": db.query(Brand).filter(Brand.brand_id == p.brand_id).first().name if p.brand_id else p.brand_id,
            "image": img(PRODUCT_DIR, p.image)
        }
        for p in db.query(Product).filter(Product.is_active == True).all()
    ]

@router.get("/products/search")
def search_products(
    q: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    session_id = get_user_session(request, response)
    log_user_visit(db, request, session_id)

    products = (
        db.query(Product)
        .join(Category)
        .join(Brand)
        .filter(
            Product.is_active == True,
            or_(
                Product.name.ilike(f"%{q}%"),
                Product.description.ilike(f"%{q}%"),
                Category.name.ilike(f"%{q}%"),
                Brand.name.ilike(f"%{q}%")
            )
        ).all()
    )

    return [
        {
            "product_id": p.product_id,
            "name": p.name,
            "description": p.description,
            "mrp": float(p.mrp),
            "price": float(p.price),
            "min_order_qty": p.min_order_qty,
            "pack_size": p.pack_size,
            "category": db.query(Category).filter(Category.category_id == p.category_id).first().name if p.category_id else p.category_id,
            "brand": db.query(Brand).filter(Brand.brand_id == p.brand_id).first().name if p.brand_id else p.brand_id,
            "image": img(PRODUCT_DIR, p.image)
        }
        for p in products
    ]

@router.get("/products/{product_id}")
def product_details(
    product_id: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    session_id = get_user_session(request, response)
    log_user_visit(db, request, session_id)

    p = db.query(Product).filter(
        Product.product_id == product_id,
        Product.is_active == True
    ).first()

    if not p:
        raise HTTPException(404, "Product not found")

    return {
        "product_id": p.product_id,
        "name": p.name,
        "description": p.description,
        "price": float(p.price),
        "mrp": float(p.mrp),
        "min_order_qty": p.min_order_qty,
        "stock": p.stock,
        "image": img(PRODUCT_DIR, p.image)
    }

# ==========================================================
# 🛒 CART CRUD
# ==========================================================

@router.post("/cart/add")
def add_to_cart(
    product_id: str,
    qty: int = 1,
    request: Request = None,
    response: Response = None,
    db: Session = Depends(get_db)
):
    session_id = get_user_session(request, response)

    if qty <= 0:
        raise HTTPException(400, "Invalid quantity")

    product = db.query(Product).filter(
        Product.product_id == product_id,
        Product.is_active == True
    ).first()

    if not product:
        raise HTTPException(404, "Product not found")

    if qty < product.min_order_qty:
        raise HTTPException(400, "Minimum order quantity not met")

    item = db.query(Cart).filter(
        Cart.session_id == session_id,
        Cart.product_id == product_id
    ).first()

    if item:
        if item.quantity + qty > product.stock:
            raise HTTPException(400, "Stock exceeded")
        item.quantity += qty
    else:
        if qty > product.stock:
            raise HTTPException(400, "Stock exceeded")
        db.add(Cart(
            session_id=session_id,
            product_id=product_id,
            quantity=qty
        ))

    db.commit()
    log_user_visit(db, request, session_id)

    return {"message": "Item added to cart"}

@router.put("/cart/decrease")
def decrease_cart_item(
    product_id: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    session_id = get_user_session(request, response)

    item = db.query(Cart).filter(
        Cart.session_id == session_id,
        Cart.product_id == product_id
    ).first()

    if not item:
        raise HTTPException(404, "Item not in cart")

    item.quantity -= 1
    if item.quantity <= 0:
        db.delete(item)

    db.commit()
    log_user_visit(db, request, session_id)

    return {"message": "Quantity updated"}

@router.delete("/cart/remove")
def remove_cart_item(
    product_id: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    session_id = get_user_session(request, response)

    db.query(Cart).filter(
        Cart.session_id == session_id,
        Cart.product_id == product_id
    ).delete()

    db.commit()
    log_user_visit(db, request, session_id)

    return {"message": "Item removed"}

@router.get("/cart")
def view_cart(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    session_id = get_user_session(request, response)

    items = db.query(Cart, Product).join(Product).filter(
        Cart.session_id == session_id
    ).all()

    cart = []
    subtotal = 0

    for c, p in items:
        total = p.price * c.quantity
        subtotal += total
        cart.append({
            "product_id": p.product_id,
            "name": p.name,
            "qty": c.quantity,
            "price": float(p.price),
            "total": float(total)
        })

    delivery = calculate_delivery(subtotal)

    return {
        "items": cart,
        "subtotal": subtotal,
        "delivery": delivery,
        "grand_total": subtotal + delivery
    }

# ==========================================================
# ✅ CHECKOUT
# ==========================================================

@router.post("/enquiry", status_code=201)
def checkout(
    customer_name: str,
    email: str,
    phone: str,
    address: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    session_id = get_user_session(request, response)

    items = db.query(Cart, Product).join(Product).filter(
        Cart.session_id == session_id
    ).all()

    if not items:
        raise HTTPException(400, "Cart is empty")

    subtotal = sum(p.price * c.quantity for c, p in items)
    delivery = calculate_delivery(subtotal)
    grand_total = subtotal + delivery

    if grand_total < 1200:
        raise HTTPException(400, "Minimum order value is ₹1200")

    try:
        enquiry = Enquiry(
            customer_name=customer_name,
            email=email,
            phone=phone,
            address=address
        )
        db.add(enquiry)
        db.flush()

        for c, p in items:
            if p.stock < c.quantity:
                raise HTTPException(400, f"{p.name} out of stock")

            p.stock -= c.quantity

            db.add(EnquiryItem(
                enquiry_id=enquiry.id,
                product_id=p.product_id,
                quantity=c.quantity
            ))

        db.query(Cart).filter(Cart.session_id == session_id).delete()
        db.commit()

    except Exception:
        db.rollback()
        raise

    log_user_visit(db, request, session_id)

    return {
        "message": "Enquiry placed successfully",
        "enquiry_id": enquiry.id,
        "subtotal": subtotal,
        "delivery": delivery,
        "grand_total": grand_total
    }
