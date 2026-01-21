import os
import uuid
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db

from app.models.admin_users import AdminUser
from app.models.categories import Category
from app.models.brand import Brand
from app.models.products import Product
from app.models.enquiries import Enquiry
from app.models.enquiry_items import EnquiryItem

router = APIRouter(prefix="/admin", tags=["Admin"])

# =====================================================
# 🔐 ADMIN LOGIN
# =====================================================

@router.post("/login")
def admin_login(username: str, password: str, db: Session = Depends(get_db)):
    admin = db.query(AdminUser).filter(
        AdminUser.username == username,
        AdminUser.password == password,
        AdminUser.is_active == True
    ).first()

    if not admin:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "admin_id": admin.id,
        "username": admin.username,
        "email": admin.email,
        "is_super_admin": admin.is_super_admin
    }

# =====================================================
# 📊 DASHBOARD
# =====================================================

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return {
        "categories": db.query(Category).count(),
        "brands": db.query(Brand).count(),
        "products": db.query(Product).count(),
        "enquiries": db.query(Enquiry).count()
    }

# =====================================================
# 📦 CATEGORY CRUD
# =====================================================

def generate_category_id(db):
    last = db.query(Category).order_by(Category.id.desc()).first()
    return f"CAT{str((last.id if last else 0)+1).zfill(4)}"

def get_product_id(db) -> str:
    prd_id_max = db.query(Product).order_by(Product.product_id.desc()).first()
    if not prd_id_max: 
        return f"PRD0001"

    prd_id_max = int(prd_id_max.category_id[3:]) + 1
    return f"PRD{str(prd_id_max).zfill(4)}"


@router.post("/categories", status_code=201)
def create_category(
    name: str,
    description: str,
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    filename = f"{uuid.uuid4()}.{image.filename.split('.')[-1]}"
    path = f"app/static/category_images/{filename}"

    with open(path, "wb") as f:
        f.write(image.file.read())

    category = Category(
        category_id=generate_category_id(db),
        name=name,
        description=description,
        image=filename
    )
    db.add(category)
    db.commit()
    return {"message": "Category created"}

@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.created_at.desc()).all()

@router.put("/categories/{category_id}")
def update_category(
    category_id: str,
    name: str | None = None,
    description: str | None = None,
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(404, "Category not found")

    if name:
        category.name = name
    if description:
        category.description = description

    if image:
        if category.image:
            old = f"app/static/category_images/{category.image}"
            if os.path.exists(old):
                os.remove(old)

        filename = f"{uuid.uuid4()}.{image.filename.split('.')[-1]}"
        path = f"app/static/category_images/{filename}"
        with open(path, "wb") as f:
            f.write(image.file.read())
        category.image = filename

    db.commit()
    return {"message": "Category updated"}

@router.put("/categories/{category_id}/enable")
def enable_category(category_id: str, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.category_id == category_id).first()
    category.is_active = True
    db.commit()
    return {"message": "Category enabled"}

@router.put("/categories/{category_id}/disable")
def disable_category(category_id: str, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.category_id == category_id).first()
    category.is_active = False
    db.commit()
    return {"message": "Category disabled"}

@router.delete("/categories/{category_id}")
def delete_category(category_id: str, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if category.image:
        img = f"app/static/category_images/{category.image}"
        if os.path.exists(img):
            os.remove(img)
    db.delete(category)
    db.commit()
    return {"message": "Category deleted"}

# =====================================================
# 🏷 BRAND CRUD
# =====================================================

def generate_brand_id(db):
    last = db.query(Brand).order_by(Brand.id.desc()).first()
    return f"BRD{str((last.id if last else 0)+1).zfill(4)}"

@router.post("/brands", status_code=201)
def create_brand(
    name: str,
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db)
):
    filename = None
    if image:
        filename = f"{uuid.uuid4()}.{image.filename.split('.')[-1]}"
        path = f"app/static/brand_images/{filename}"
        with open(path, "wb") as f:
            f.write(image.file.read())

    brand = Brand(
        brand_id=generate_brand_id(db),
        name=name,
        image=filename
    )
    db.add(brand)
    db.commit()
    return {"message": "Brand created"}

@router.get("/brands")
def list_brands(db: Session = Depends(get_db)):
    return db.query(Brand).all()

@router.put("/brands/{brand_id}")
def update_brand(
    brand_id: str,
    name: str | None = None,
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db)
):
    brand = db.query(Brand).filter(Brand.brand_id == brand_id).first()
    if name:
        brand.name = name

    if image:
        if brand.image:
            old = f"app/static/brand_images/{brand.image}"
            if os.path.exists(old):
                os.remove(old)

        filename = f"{uuid.uuid4()}.{image.filename.split('.')[-1]}"
        path = f"app/static/brand_images/{filename}"
        with open(path, "wb") as f:
            f.write(image.file.read())
        brand.image = filename

    db.commit()
    return {"message": "Brand updated"}

@router.put("/brands/{brand_id}/enable")
def enable_brand(brand_id: str, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.brand_id == brand_id).first()
    brand.is_active = True
    db.commit()
    return {"message": "Brand enabled"}

@router.put("/brands/{brand_id}/disable")
def disable_brand(brand_id: str, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.brand_id == brand_id).first()
    brand.is_active = False
    db.commit()
    return {"message": "Brand disabled"}

# =====================================================
# 📦 PRODUCT CRUD
# =====================================================

@router.post("/products", status_code=201)
def add_product(
    product_id: str,
    category_id: str,
    brand_id: str,
    name: str,
    description: str,
    mrp: float,
    price: float,
    min_order_qty: int,
    stock: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    filename = f"{uuid.uuid4()}.{image.filename.split('.')[-1]}"
    path = f"app/static/product_images/{filename}"

    with open(path, "wb") as f:
        f.write(image.file.read())

    product = Product(
        product_id=get_product_id(db),
        category_id=category_id,
        brand_id=brand_id,
        name=name,
        description=description,
        mrp=mrp,
        price=price,
        min_order_qty=min_order_qty,
        stock=stock,
        image=filename
    )
    db.add(product)
    db.commit()
    return {"message": "Product created"}

@router.put("/products/{product_id}")
def update_product(
    product_id: str,
    name: str | None = None,
    price: float | None = None,
    stock: int | None = None,
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.product_id == product_id).first()

    if name:
        product.name = name
    if price is not None:
        product.price = price
    if stock is not None:
        product.stock = stock

    if image:
        if product.image:
            old = f"app/static/product_images/{product.image}"
            if os.path.exists(old):
                os.remove(old)

        filename = f"{uuid.uuid4()}.{image.filename.split('.')[-1]}"
        path = f"app/static/product_images/{filename}"
        with open(path, "wb") as f:
            f.write(image.file.read())
        product.image = filename

    db.commit()
    return {"message": "Product updated"}

@router.put("/products/{product_id}/enable")
def enable_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    product.is_active = True
    db.commit()
    return {"message": "Product enabled"}

@router.put("/products/{product_id}/disable")
def disable_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    product.is_active = False
    db.commit()
    return {"message": "Product disabled"}

# =====================================================
# 📞 ENQUIRIES
# =====================================================

@router.get("/enquiries")
def list_enquiries(db: Session = Depends(get_db)):
    return db.query(Enquiry).order_by(Enquiry.created_at.desc()).all()

@router.get("/enquiries/{enquiry_id}")
def enquiry_details(enquiry_id: int, db: Session = Depends(get_db)):
    enquiry = db.query(Enquiry).filter(Enquiry.id == enquiry_id).first()

    items = (
        db.query(EnquiryItem, Product)
        .join(Product, EnquiryItem.product_id == Product.product_id)
        .filter(EnquiryItem.enquiry_id == enquiry_id)
        .all()
    )

    return {
        "enquiry": enquiry,
        "items": [
            {
                "product_id": p.product_id,
                "name": p.name,
                "qty": i.quantity,
                "price": float(p.price),
                "total": float(i.quantity * p.price)
            }
            for i, p in items
        ]
    }
