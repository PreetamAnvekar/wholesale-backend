import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.db.session import get_db

from app.models.admin_users import AdminUser
from app.models.categories import Category
from app.models.products import Product
from app.models.enquiries import Enquiry
from app.models.enquiry_items import EnquiryItem

router = APIRouter(prefix="/admin", tags=["Admin"])


# =====================================================
# ADMIN LOGIN
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
# ADMIN DASHBOARD
# =====================================================

@router.get("/dashboard")
def admin_dashboard(db: Session = Depends(get_db)):
    return {
        "total_categories": db.query(Category).count(),
        "total_products": db.query(Product).count(),
        "total_enquiries": db.query(Enquiry).count()
    }


# =====================================================
# CATEGORY MANAGEMENT
# =====================================================

def get_category_id(db) -> str:
    cat_id_max = db.query(Category).order_by(Category.category_id.desc()).first()
    if not cat_id_max: 
        return f"CAT0001"

    cat_id_max = int(cat_id_max.category_id[3:]) + 1
    return f"CAT{str(cat_id_max).zfill(4)}"

@router.post("/categories", status_code=201)
def add_category(
    name: str,
    description: str,
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # create filename
    ext = image.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"

    save_path = f"app/static/category_images/{filename}"

    with open(save_path, "wb") as f:
        f.write(image.file.read())

    category = Category(
        category_id=get_category_id(db),
        name=name,
        description=description,
        image=filename
    )
    db.add(category)
    db.commit()

    return {"message": "Category added successfully"}



@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.created_at.desc()).all()


@router.put("/categories/{category_id}/disable")
def disable_category(category_id: str, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    category.is_active = False
    db.commit()
    return {"message": "Category disabled"}

@router.put("/categories/{category_id}/enable")
def disable_category(category_id: str, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.category_id == category_id & Category.is_active == False).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    category.is_active = True
    db.commit()
    return {"message": "Category disabled"}

# =====================================================
# PRODUCT MANAGEMENT
# =====================================================

@router.post("/products", status_code=201)
def add_product(
    product_id: str,
    category_id: str,
    name: str,
    description: str,
    price: float,
    min_order_qty: int,
    stock: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    ext = image.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"

    save_path = f"app/static/product_images/{filename}"

    with open(save_path, "wb") as f:
        f.write(image.file.read())

    product = Product(
        product_id=product_id,
        category_id=category_id,
        name=name,
        description=description,
        price=price,
        min_order_qty=min_order_qty,
        stock=stock,
        image=filename
    )

    db.add(product)
    db.commit()

    return {"message": "Product added successfully"}



@router.get("/products")
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.created_at.desc()).all()


@router.put("/products/{product_id}/disable")
def disable_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_active = False
    db.commit()
    return {"message": "Product disabled"}


# =====================================================
# ENQUIRY MANAGEMENT
# =====================================================

@router.get("/enquiries")
def list_enquiries(db: Session = Depends(get_db)):
    return db.query(Enquiry).order_by(Enquiry.created_at.desc()).all()


@router.get("/enquiries/{enquiry_id}")
def enquiry_details(enquiry_id: int, db: Session = Depends(get_db)):
    enquiry = db.query(Enquiry).filter(Enquiry.id == enquiry_id).first()
    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found")

    items = (
        db.query(EnquiryItem, Product)
        .join(Product, EnquiryItem.product_id == Product.product_id)
        .filter(EnquiryItem.enquiry_id == enquiry_id)
        .all()
    )

    return {
        "enquiry": {
            "id": enquiry.id,
            "customer_name": enquiry.customer_name,
            "phone": enquiry.phone,
            "status": enquiry.status,
            "created_at": enquiry.created_at
        },
        "items": [
            {
                "product_id": p.product_id,
                "name": p.name,
                "quantity": i.quantity,
                "price": float(p.price),
                "total": float(i.quantity * p.price)
            }
            for i, p in items
        ]
    }
