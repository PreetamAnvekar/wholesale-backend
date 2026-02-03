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
from app.models.email_logs import EmailLog
from app.models.products import Product
from app.models.cart import Cart
from app.models.enquiries import Enquiry
from app.models.enquiry_items import EnquiryItem
from app.core.send_mail import send_email
from app.core.config import settings
from app.core.storage import CATEGORY_DIR, PRODUCT_DIR, BRAND_DIR
from app.models.user_visits import UserVisit

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
            "description": c.description,
            "image": os.path.join(CATEGORY_DIR, c.image)
        }
        for c in db.query(Category).filter(Category.is_active == True).all()
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

    products = db.query(Product).filter(Product.category_id == category_id, Product.is_active == True).all()

    return [
        {
            "product_id": p.product_id,
            "name": p.name,
            "description": p.description,
            "mrp": float(p.mrp),
            "price": float(p.price),
            "min_order_qty": p.min_order_qty,
            "stock": p.stock,
            "image": os.path.join(PRODUCT_DIR, p.image)
        }
        for p in products
    ]

@router.get("/brands")
def list_brands(db: Session = Depends(get_db)):
    brands = db.query(Brand).filter(Brand.is_active == True).all()
    return [
        {
            "brand_id": b.brand_id,
            "name": b.name,
            "image": os.path.join(BRAND_DIR, b.image) if b.image else None
        }
        for b in brands
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
    products_by_brand = db.query(Product).filter(Product.brand_id == brand_id, Product.is_active == True).all()

    return [
        {
            "product_id": p.product_id,
            "name": p.name,
            "description": p.description,
            "mrp": float(p.mrp),
            "price": float(p.price),
            "stock": p.stock,
            "image": os.path.join(PRODUCT_DIR, p.image)
        }for p in products_by_brand
    ]

@router.get("/products/{product_id}")
def product_details(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(
        Product.product_id == product_id,
        Product.is_active == True
    ).first()

    if not product:
        raise HTTPException(404, "Product not found")

    return {
        "product_id": product.product_id,
        "name": product.name,
        "description": product.description,
        "price": float(product.price),
        "mrp": float(product.mrp),
        "min_order_qty": product.min_order_qty,
        "stock": product.stock,
        "category_id": product.category_id,
        "brand_id": product.brand_id,
        "image": os.path.join(PRODUCT_DIR, product.image)
    }


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
            "stock": p.stock,
            "category_id": db.query(Category).filter(Category.category_id == p.category_id).first().name if p.category_id else p.category_id,
            "brand_id": db.query(Brand).filter(Brand.brand_id == p.brand_id).first().name if p.brand_id else p.brand_id,
            "price": float(p.price),
            "image": os.path.join(PRODUCT_DIR, p.image)
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
            "image": os.path.join(PRODUCT_DIR, p.image)
        }
        for p in products
    ]

@router.post("/products/filter")
def filter_products(filters: dict, db: Session = Depends(get_db)):
    query = db.query(Product).filter(Product.is_active == True)

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

    products = query.all()

    return [
        {
            "product_id": p.product_id,
            "name": p.name,
            "price": float(p.price),
            "min_order_qty": p.min_order_qty,
            "image": os.path.join(PRODUCT_DIR, p.image)
        }
        for p in products
    ]

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

    items = (
        db.query(Cart, Product)
        .join(Product, Cart.product_id == Product.product_id)
        .filter(Cart.session_id == session_id)
        .all()
    )

    cart = []
    subtotal = 0.0

    for c, p in items:
        total = float(p.price) * c.quantity
        subtotal += total

        cart.append({
            "product_id": p.product_id,
            "name": p.name,
            "qty": c.quantity,
            "price": float(p.price),
            "total_price": total,
            "image": os.path.join(PRODUCT_DIR, p.image)
        })

    delivery = 50.0 if subtotal > 0 else 0.0  # example logic

    return {
        "items": cart,
        "subtotal": round(subtotal, 2),
        "delivery": delivery,
        "grand_total": round(subtotal + delivery, 2)
    }
 
# ==========================================================
# ✅ CHECKOUT
# ==========================================================
@router.post("/enquiry", status_code=201)
def submit_enquiry(
    customer_name: str,
    email: str,
    phone: str,
    address: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    session_id = get_user_session(request, response)

    items = (
        db.query(Cart, Product)
        .join(Product, Cart.product_id == Product.product_id)
        .filter(Cart.session_id == session_id)
        .all()
    )

    if not items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    subtotal = sum(float(p.price) * c.quantity for c, p in items)
    delivery = calculate_delivery(subtotal)
    grand_total = subtotal + delivery

    if grand_total < 1200:
        raise HTTPException(status_code=400, detail="Minimum order value is ₹1200")

    # Build items HTML
    items_html = ""
    for c, p in items:
        items_html += f"""
        <tr>
            <td>{p.name}</td>
            <td>{c.quantity}</td>
            <td>₹{float(p.price)}</td>
            <td>₹{float(p.price) * c.quantity}</td>
        </tr>
        """

    try:
        enquiry = Enquiry(
            customer_name=customer_name,
            email=email,
            phone=phone,
            address=address,
            subtotal=subtotal,
            delivery=delivery,
            grand_total=grand_total
        )
        db.add(enquiry)
        db.flush()  # get enquiry.id

        for c, p in items:
            if p.stock < c.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"{p.name} out of stock"
                )

            p.stock -= c.quantity

            db.add(EnquiryItem(
                enquiry_id=enquiry.id,
                product_id=p.product_id,
                quantity=c.quantity,
                price=p.price
            ))

        db.query(Cart).filter(
            Cart.session_id == session_id
        ).delete()

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    # ---------- EMAIL TEMPLATES ----------
    admin_html = f"""
    <h2>New Enquiry Received</h2>
    <p><b>Name:</b> {customer_name}</p>
    <p><b>Email:</b> {email}</p>
    <p><b>Phone:</b> {phone}</p>
    <p><b>Address:</b> {address}</p>

    <table border="1" cellpadding="8">
        <tr><th>Product</th><th>Qty</th><th>Price</th><th>Total</th></tr>
        {items_html}
    </table>

    <h3>Subtotal: ₹{subtotal}</h3>
    <h3>Delivery: ₹{delivery}</h3>
    <h2>Grand Total: ₹{grand_total}</h2>
    """

    user_html = f"""
    <h2>Enquiry Submitted Successfully</h2>
    <p>Dear {customer_name},</p>

    <table border="1" cellpadding="8">
        <tr><th>Product</th><th>Qty</th><th>Price</th><th>Total</th></tr>
        {items_html}
    </table>

    <h3>Grand Total: ₹{grand_total}</h3>
    """

    # ---------- ADMIN EMAIL ----------
    try:
        send_email(settings.ADMIN_EMAIL, "New Enquiry", admin_html)
        admin_sent = True
    except Exception:
        admin_sent = False

    db.add(EmailLog(
        enquiry_id=enquiry.id,
        email_to=settings.ADMIN_EMAIL,
        sent_status=admin_sent
    ))
    db.commit()

    # ---------- USER EMAIL ----------
    try:
        send_email(email, "Enquiry Received", user_html)
        user_sent = True
    except Exception:
        user_sent = False

    db.add(EmailLog(
        enquiry_id=enquiry.id,
        email_to=email,
        sent_status=user_sent
    ))
    db.commit()

    return {
        "message": "Enquiry submitted successfully",
        "enquiry_id": enquiry.id,
        "grand_total": grand_total
    }

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
            "image": os.path.join(PRODUCT_DIR, p.image)
        }
        for p in products
    ]
