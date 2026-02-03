import json
import os
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from sqlalchemy.orm import Session

from app.core.storage import BRAND_DIR, CATEGORY_DIR, PRODUCT_DIR
from app.db.session import get_db
from app.models.admin_users import AdminUser
from app.core.security import verify_password
from app.core.jwt import create_access_token
from app.core.security import hash_password
from app.core.dependencies import admin_only, get_current_admin, super_admin_only
from app.models.admin_activity_logs import AdminActivityLog
from app.models.brand import Brand
from app.models.categories import Category
from app.models.products import Product
from app.core.config import settings
import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/admin", tags=["Admin"])

def get_client_ip(request: Request):
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else None

# def get_api_key(request: Request):
#     return request.headers.get("api-key")


def log_admin_activity(
    db,
    admin,
    request: Request,
    action,
    module,
    endpoint,
    method,
    description,
    payload=None
):
    try:
        db.add(AdminActivityLog(
            admin_id=admin.admin_id,
            action=action,
            module=module,
            endpoint=endpoint,
            method=method,
            description=description,
            ip_address=get_client_ip(request),
            payload=json.dumps(payload) if payload else None
        ))
        # db.commit()
    except Exception as e:
        logger.error(f"Error logging admin activity: {e}")
        pass

def snapshot(model, fields: list[str]):
    return {field: getattr(model, field) for field in fields}

def image_extension_valid(filename):
    return filename.split('.')[-1] in ['jpg', 'jpeg', 'png', 'webp', 'avif']



# @router.post("/login")
# def admin_login(
#     username: str,
#     password: str,
#     db: Session = Depends(get_db)
# ):
#     admin = db.query(AdminUser).filter(
#         AdminUser.username == username,
#         AdminUser.is_active == True
#     ).first()

#     if not admin or not verify_password(password, admin.password):
#         raise HTTPException(status_code=401, detail="Invalid credentials")

#     token = create_access_token({
#         "sub": admin.admin_id,
#         "role": "super_admin" if admin.role == 'super_admin' else "admin"
#     })

#     return {
#         "access_token": token,
#         "token_type": "bearer",
#         "admin": {
#             "admin_id": admin.admin_id,
#             "username": admin.username,
#             "email": admin.email,
#             "is_super_admin": admin.is_super_admin
#         }
#     }

@router.post("/login")
def admin_login(
    request: Request,
    username: str,
    password: str,
    response: Response,
    db: Session = Depends(get_db)
):
    print("Admin login")
    admin = db.query(AdminUser).filter(
        AdminUser.username == username,
        AdminUser.is_active == True
    ).first()

    if not admin or not verify_password(password, admin.password_hash):
        raise HTTPException(401, "Invalid credentials")

    token = create_access_token({
        "sub": admin.admin_id,
        "role": "super_admin" if admin.is_super_admin else "admin"
    })
    admin.last_login_at = func.now()

    response.set_cookie(
        key="admin_token",
        value=token,
        httponly=True,
        secure=settings.ENV == "production",       # False only for localhost
        samesite="strict" if settings.ENV == "production" else "lax",
        max_age=60 * 60
    )
    try:
        log_admin_activity(
            db=db,
            admin=admin,
            action="LOGIN",
            module="Auth",
            request=request,
            endpoint="/admin/login",
            method="POST",
            description="Admin logged in",
            
        )
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error logging admin activity: {e}")
        pass

    return {"message": "Login successful","expires_in": 3600}

@router.post("/admins", status_code=201)
def create_admin(
    request: Request,
    username: str,
    email: str,
    password: str,
    role: str,
    is_super_admin: bool = False,
    db: Session = Depends(get_db),
    # current_admin: AdminUser = Depends(super_admin_only)
):
    # Only super admin
    # if not current_admin.is_super_admin:
    #     raise HTTPException(403, "Super admin access required")

    # Duplicate check
    exists = db.query(AdminUser).filter(
        (AdminUser.username == username) |
        (AdminUser.email == email)
    ).first()

    
    if exists:
        raise HTTPException(400, "Admin already exists")
    
    try:
    # 1Create admin (WITHOUT admin_id)
        
        admin = AdminUser(
            username=username,
            password_hash=hash_password(password),
            email=email,
            role=role,
            is_super_admin=is_super_admin,
            is_active=True
        )
        db.add(admin)
        db.flush()  

        # Generate SEQUENTIAL admin_id
        admin.admin_id = f"ADM{str(admin.id).zfill(4)}"
        after = snapshot(admin, ["admin_id", "username", "email", "is_super_admin", "is_active"])

        log_admin_activity(
            db = db,
            admin='preetam',
            action="CREATE",
            module="Admin",
            request=request,
            endpoint="/admin/admins",
            method="POST",
            description=f"Created admin {admin.admin_id}",
            payload={
                'after': after
            },
            

        )

        db.commit()
    except Exception as e:
        db.rollback()
        # if image and os.path.exists(path):
        #     os.remove(path)
        raise HTTPException(500, str(e))

    return {
        "message": "Admin created successfully",
        "admin_id": admin.admin_id
    }

@router.get("/admins")
def get_admins(
    request: Request,
    db: Session = Depends(get_db),
    current_admin=Depends(super_admin_only)
):
    print("Admins")
    return db.query(AdminUser).filter(AdminUser.is_active == True).all()

@router.put("/admins/{admin_id}")
def update_admin(
    request: Request,
    admin_id: str,
    username: str,
    email: str,
    password: str,
    role: str,
    is_active: bool,
    is_super_admin: bool,
    db: Session = Depends(get_db),
    current_admin=Depends(super_admin_only)
):
    admin = db.query(AdminUser).filter(AdminUser.admin_id == admin_id).first()
    if not admin:
        raise HTTPException(404, "Admin not found")
    before = snapshot(admin, ['admin_id', 'username', 'email', 'is_super_admin', 'is_active'])
    try:
        admin.username = username
        admin.email = email
        admin.password = hash_password(password)
        admin.role = role
        admin.is_active = is_active
        admin.is_super_admin = is_super_admin
        after = snapshot(admin, ['admin_id', 'username', 'email', 'is_super_admin', 'is_active'])
        log_admin_activity(
            db = db,
            admin=current_admin,
            action="UPDATE",
            module="Admin",
            endpoint=f"/admin/admins/{admin_id}",
            method="PUT",
            request=request,
            description=f"Updated admin {admin.admin_id}",
            payload={
                'before': before,
                'after': after
            }
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    return {"message": "Admin updated"}



@router.put("/admins/{admin_id}/disable")
def disable_admin(
    request: Request,
    admin_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(super_admin_only)
):
    admin = db.query(AdminUser).filter(AdminUser.admin_id == admin_id).first()
    if not admin:
        raise HTTPException(404, "Admin not found")

    admin.is_active = False
    log_admin_activity(
        db = db,
        admin=current_admin,
        action="UPDATE",
        module="Admin",
        request=request,
        endpoint=f"/admin/admins/{admin_id}/disable",
        method="POST",
        description=f"Disabled admin {admin.admin_id}",
    )
    db.commit()
    return {"message": "Admin disabled"}

@router.put("/admins/{admin_id}/enable")
def enable_admin(
    request: Request,
    admin_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(super_admin_only)
):
    admin = db.query(AdminUser).filter(AdminUser.admin_id == admin_id).first()
    admin.is_active = True
    log_admin_activity(
        db = db,
        admin=current_admin,
        action="UPDATE",
        module="Admin",
        request=request,
        endpoint=f"/admin/admins/{admin_id}/enable",
        method="POST",
        description=f"Enabled admin {admin.admin_id}",
    )
    db.commit()
    return {"message": "Admin enabled"}

@router.delete("/admins/{admin_id}")
def delete_admin(
    request: Request,
    admin_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(super_admin_only)
):
    admin = db.query(AdminUser).filter(AdminUser.admin_id == admin_id).first()
    if not admin:
        raise HTTPException(404, "Admin not found")

    log_admin_activity(
        db = db,
        admin=current_admin,
        action="DELETE",
        module="Admin",
        request=request,
        endpoint=f"/admin/admins/{admin_id}",
        method="POST",
        description=f"Deleted admin {admin.admin_id}",
        payload={
            'deleted': snapshot(admin, ['admin_id', 'username', 'email', 'is_super_admin', 'is_active'])
        }
    )
    db.delete(admin)
    db.commit()
    return {"message": "Admin deleted"}

@router.post("/logout")
def admin_logout(response: Response, admin=Depends(admin_only)):
    response.delete_cookie("admin_token")
    return {"message": "Logged out"}


def assign_category_id(
    db: Session, category: Category):
    db.commit()
    db.refresh(category)
    category.category_id = f"CAT{str(category.id).zfill(4)}"
    db.commit()
    
def assign_brand_id(db: Session, brand: Brand):
    db.commit()
    db.refresh(brand)
    brand.brand_id = f"BRD{str(brand.id).zfill(4)}"
    db.commit()


@router.post("/categories", status_code=201)
def create_category(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    parent_id: str | None = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    # Validate image
    if not image_extension_valid(image.filename):
        raise HTTPException(
           400,
            detail="Invalid image format"
        )

    # Validate parent category
    if parent_id:
        parent = db.query(Category).filter(
            Category.category_id == parent_id,
            Category.is_active.is_(True)
        ).first()
        if not parent:
            raise HTTPException(
                400,
                detail="Invalid parent category"
            )

    filename = f"{uuid.uuid4()}.{image.filename.split('.')[-1]}"
    path = os.path.join(CATEGORY_DIR, filename)

    try:
        # Save image
        with open(path, "wb") as f:
            f.write(image.file.read())

        category = Category(
            name=name.strip(),
            description=description.strip(),
            parent_id=parent_id,
            image=filename
        )

        db.add(category)
        db.flush()

        category.category_id = f"CAT{str(category.id).zfill(4)}"

        after = snapshot(
            category,
            ["category_id", "name", "description", "parent_id", "image", "is_active"]
        )

        log_admin_activity(
            db=db,
            admin=admin,
            action="CREATE",
            module="Category",
            endpoint="/admin/categories",
            request=request,
            method="POST",
            description=f"Created category {category.category_id}",
            payload={"after": after}
        )

        db.commit()

    except IntegrityError:
        db.rollback()
        if os.path.exists(path):
            os.remove(path)
        raise HTTPException(
            500,
            detail="Category already exists"
        )

    except Exception as e:
        db.rollback()
        print(e)
        if os.path.exists(path):
            os.remove(path)
        raise HTTPException(
            500,
            detail="Failed to create category"
        )

    return {
        "message": "Category created successfully",
        "category_id": category.category_id
    }

@router.get("/categories")
def list_categories(
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    return db.query(Category).order_by(Category.created_at.desc()).all()


@router.put("/categories/{category_id}")
def update_category(
    request: Request,
    category_id: str,
    name: str | None = None,
    description: str | None = None,
    parent_id: str | None = None,
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    category = db.query(Category).filter(Category.category_id == category_id).first()
    old = None
    if not category:
        raise HTTPException(404, "Category not found")
    if image and not image_extension_valid(image.filename):
        raise HTTPException(400, "Invalid image format")
    try:
        before = snapshot(category, ["category_id", "name", "description", "parent_id", "image", "is_active"])
        if name:
            category.name = name
        if description:
            category.description = description
        if parent_id is not None:
            parent = db.query(Category).filter(
                Category.category_id == parent_id,
                Category.is_active == True
            ).first()
            if not parent:
                raise HTTPException(400, "Invalid parent category")
            category.parent_id = parent_id

        if image:
            if category.image:
                old = os.path.join(CATEGORY_DIR, category.image)
            filename = f"{uuid.uuid4()}.{image.filename.split('.')[-1]}"
            path = os.path.join(CATEGORY_DIR, filename)

            with open(path, "wb") as f:
                f.write(image.file.read())

            category.image = filename

        after = snapshot(category, ["category_id", "name", "description", "parent_id", "image", "is_active"])
        log_admin_activity(
            db = db,
            admin=admin,
            action="UPDATE",
            module="Category",
            endpoint=f"/admin/categories/{category_id}",
            request=request,
            method="POST",
            description=f"Updated category {category.category_id}",
            payload={
                "before": before,
                "after": after
            }

        )
        db.commit()
        if old:
            if os.path.exists(old):
                os.remove(old)
        

    except IntegrityError:
        db.rollback()
        if os.path.exists(path):
            os.remove(path)
        raise HTTPException(400, "Category already exists")

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    
    return {"message": "Category updated"}

@router.put("/categories/{category_id}/disable")
def disable_category(
    request: Request,
    category_id: str,
    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(404, "Category not found")

    category.is_active = False
    log_admin_activity(
        db = db,
        admin=admin,
        action="UPDATE",
        module="Category",
        request=request,
        endpoint=f"/admin/categories/{category_id}/disable",
        method="POST",
        description=f"Disabled category {category.category_id}",
    )
    db.commit()
    return {"message": "Category disabled"}

@router.put("/categories/{category_id}/enable")
def enable_category(
    request: Request,
    category_id: str,
    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    category = db.query(Category).filter(Category.category_id == category_id).first()
    category.is_active = True
    log_admin_activity(
        db = db,
        admin=admin,
        action="UPDATE",
        module="Category",
        request=request,
        endpoint=f"/admin/categories/{category_id}/enable",
        method="POST",
        description=f"Enabled category {category.category_id}",
    )
    db.commit()
    return {"message": "Category enabled"}

@router.delete("/categories/{category_id}")
def delete_category(
    request: Request,
    category_id: str,
    db: Session = Depends(get_db),
    admin=Depends(super_admin_only)
):
    if not admin.is_super_admin:
        raise HTTPException(403, "Only super admin can delete")

    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(404, "Category not found")
    try:
        img = None
        if category.image:
            img = os.path.join(CATEGORY_DIR, category.image)
        

        delete_cat = snapshot(category, ["category_id", "name", "description", "parent_id", "image", "is_active"])

        db.delete(category)
        log_admin_activity(
            db = db,
            admin=admin,
            action="DELETE",
            module="Category",
            request=request,
            endpoint=f"/admin/categories/{category_id}",
            method="POST",
            description=f"Deleted category {category.category_id}",
            payload={
                "deleted": delete_cat
            }
        )
        db.commit()
        if img and os.path.exists(img):
            os.remove(img)
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    return {"message": "Category permanently deleted"}







@router.post("/brands", status_code=201)
def create_brand(
    request: Request,
    name: str,
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    if db.query(Brand).filter(Brand.name == name).first():
        raise HTTPException(400, "Brand already exists")
    if image and not image_extension_valid(image.filename):
        raise HTTPException(400, "Invalid image format")

    filename = None
    if image:
        filename = f"{uuid.uuid4()}.{image.filename.split('.')[-1]}"
        path = os.path.join(BRAND_DIR, filename)
        with open(path, "wb") as f:
            f.write(image.file.read())
    try:
        brand = Brand(name=name, image=filename)
        db.add(brand)
        
        db.flush()

        brand.brand_id = f"BRD{str(brand.id).zfill(4)}"
        after = snapshot(brand, ["brand_id", "name", "image"])
        log_admin_activity(
            db = db,
            admin=admin,
            action="CREATE",
            module="Brand",
            request=request,
            endpoint=f"/admin/brands",
            method="POST",
            description=f"Created brand {brand.brand_id}",
            payload={
                "after": after
            }
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        if image:
            if os.path.exists(path):
                os.remove(path)
        raise HTTPException(400, "Brand already exists")

    except Exception as e:
        db.rollback()
        if image:
            if os.path.exists(path):
                os.remove(path)
        raise HTTPException(500, str(e))

    return {"message": "Brand created", "brand_id": brand.brand_id}

@router.get("/brands")
def list_brands(
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    return db.query(Brand).order_by(Brand.created_at.desc()).all()

@router.put("/brands/{brand_id}")
def update_brand(
    request: Request,
    brand_id: str,
    name: str | None = None,
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    brand = db.query(Brand).filter(Brand.brand_id == brand_id).first()
    old = None
    if not brand:
        raise HTTPException(404, "Brand not found")
    if image and not image_extension_valid(image.filename):
        raise HTTPException(400, "Invalid image format")
    try:
        before = snapshot(brand, ["brand_id", "name", "image"])
        if name:
            brand.name = name

        if image:
            if brand.image:
                old = os.path.join(BRAND_DIR, brand.image)

            filename = f"{uuid.uuid4()}.{image.filename.split('.')[-1]}"
            path = os.path.join(BRAND_DIR, filename)
            with open(path, "wb") as f:
                f.write(image.file.read())

            brand.image = filename
        after = snapshot(brand, ["brand_id", "name", "image"])

        log_admin_activity(
            db = db,
            admin=admin,
            action="UPDATE",
            module="Brand",
            request=request,
            endpoint=f"/admin/brands/{brand_id}",
            method="PUT",
            description=f"Updated brand {brand.brand_id}",
            payload={
                "before": before,
                "after": after
            }
        )

        db.commit()
        if old:
            if os.path.exists(old):
                os.remove(old)
    except IntegrityError:
        db.rollback()
        if image:
            if os.path.exists(path):
                os.remove(path)
        raise HTTPException(400, "Brand already exists")

    except Exception as e:
        db.rollback()
        if image:
            if os.path.exists(path):
                os.remove(path)
        raise HTTPException(500, str(e))
    return {"message": "Brand updated"}

@router.put("/brands/{brand_id}/disable")
def disable_brand(
    request: Request,
    brand_id: str,
    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    brand = db.query(Brand).filter(Brand.brand_id == brand_id).first()
    if not brand:
        raise HTTPException(404, "Brand not found")

    brand.is_active = False
    log_admin_activity(
        db = db,
        admin=admin,
        action="UPDATE",
        module="Brand",
        request=request,
        endpoint=f"/admin/brands/{brand_id}",
        method="PUT",
        description=f"Disabled brand {brand.brand_id}"
    )
    db.commit()
    return {"message": "Brand disabled"}

@router.put("/brands/{brand_id}/enable")
def enable_brand(
    request: Request,
    brand_id: str,
    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    brand = db.query(Brand).filter(Brand.brand_id == brand_id).first()
    brand.is_active = True
    log_admin_activity(
        db = db,
        admin=admin,
        action="UPDATE",
        module="Brand",
        request=request,
        endpoint=f"/admin/brands/{brand_id}",
        method="PUT",
        description=f"Enabled brand {brand.brand_id}",
    )
    db.commit()
    return {"message": "Brand enabled"}

@router.delete("/brands/{brand_id}")
def delete_brand(
    request: Request,
    brand_id: str,
    db: Session = Depends(get_db),
    admin=Depends(super_admin_only)
):
    if not admin.is_super_admin:
        raise HTTPException(403, "Only super admin can delete")

    brand = db.query(Brand).filter(Brand.brand_id == brand_id).first()
    img = None
    if not brand:
        raise HTTPException(404, "Brand not found")
    try:
        if brand.image:
            img = os.path.join(BRAND_DIR, brand.image)
            

        db.delete(brand)
        delete_brd = snapshot(brand, ["brand_id", "name", "image"])
        log_admin_activity(
            db = db,
            admin=admin,
            action="DELETE",
            module="Brand",
            request=request,
            endpoint=f"/admin/brands/{brand_id}",
            method="POST",
            description=f"Deleted brand {brand.brand_id}",
            payload={
                "deleted": delete_brd
            }
        )
        db.commit()
        if img and os.path.exists(img):
            os.remove(img)

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    return {"message": "Brand permanently deleted"}


def assign_product_id(db: Session, product: Product):
    db.commit()
    db.refresh(product)
    product.product_id = f"PRD{str(product.id).zfill(6)}"
    db.commit()

@router.post("/products", status_code=201)
def create_product(
    request: Request,
    category_id: str,
    brand_id: str,
    name: str,
    description: str | None = None,
    mrp: float | None = None,
    price: float = None,
    min_order_qty: int = 1,
    pack_size: str | None = None,
    uom: str | None = None,
    stock: int = 0,
    image: UploadFile = File(...),

    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    
    if not db.query(Category).filter(
        Category.category_id == category_id,
        Category.is_active == True
    ).first():
        raise HTTPException(400, "Invalid category")
    
    if image and not image_extension_valid(image.filename):
        raise HTTPException(400, "Invalid image format")

    if not db.query(Brand).filter(
        Brand.brand_id == brand_id,
        Brand.is_active == True
    ).first():
        raise HTTPException(400, "Invalid brand")
    if price is not None and mrp is not None and price > mrp:
        raise HTTPException(400, "Price cannot exceed MRP")

    if min_order_qty is not None and min_order_qty <= 0:
        raise HTTPException(400, "Invalid minimum order quantity")

    if stock is not None and stock < 0:
        raise HTTPException(400, "Stock cannot be negative")


    # save image
    filename = f"{uuid.uuid4()}.{image.filename.split('.')[-1]}"
    path = os.path.join(PRODUCT_DIR, filename)

    with open(path, "wb") as f:
        f.write(image.file.read())
    try:
        product = Product(
            category_id=category_id,
            brand_id=brand_id,
            name=name,
            description=description,
            mrp=mrp,
            price=price,
            min_order_qty=min_order_qty,
            pack_size=pack_size,
            uom=uom,
            stock=stock,
            image=filename
        )

        db.add(product)
        db.flush()

        product.product_id = f"PRD{str(product.id).zfill(6)}"
        after = snapshot(product, [
            "product_id",
            "category_id",
            "brand_id",
            "name",
            "description",
            "mrp",
            "price",
            "min_order_qty",
            "pack_size",
            "uom",
            "stock",
            "image",
            "is_active"
        ])  
        log_admin_activity(
            db = db,
            admin=admin,
            action="CREATE",
            module="Product",
            request=request,
            endpoint=f"/admin/products",
            method="POST",
            description=f"Created product {product.product_id}",
            payload={
                "after": after
            }
        )
        db.commit()
                                            

    except Exception as e:
        db.rollback()
        if os.path.exists(path):
            os.remove(path)
        raise HTTPException(400, str(e))

    return {
        "message": "Product created",
        "product_id": product.product_id
    }


# @router.get("/products")
# def list_products(
#     db: Session = Depends(get_db),
#     admin=Depends(admin_only)
# ):
#     return db.query(Product).order_by(Product.created_at.desc()).all()

@router.get("/products")
def list_products( request: Request,db: Session = Depends(get_db), limit: int = 20, offset: int = 0,admin=Depends(admin_only)):
    return db.query(Product).offset(offset).limit(limit).all()


@router.get("/products/{product_id}")
def get_product(
    request: Request,
    product_id: str,
    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")

    return product

@router.put("/products/{product_id}")
def update_product(
    request: Request,
    product_id: str,

    name: str | None = None,
    description: str | None = None,
    mrp: float | None = None,
    price: float | None = None,
    min_order_qty: int | None = None,
    pack_size: str | None = None,
    uom: str | None = None,
    stock: int | None = None,
    category_id: str | None = None,
    brand_id: str | None = None,

    image: UploadFile | None = File(None),

    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if image and not image_extension_valid(image.filename):
        raise HTTPException(400, "Invalid image format")
    old = None
    if not product:
        raise HTTPException(404, "Product not found")
        
    # if price is not None and mrp is not None and price > mrp:
    #         raise HTTPException(400, "Price cannot exceed MRP")

    try:
        before = snapshot(product,['product_id', 'category_id', 'brand_id', 'name', 'description', 'mrp', 'price', 'min_order_qty', 'pack_size', 'uom', 'stock', 'image', 'is_active'])
        # text updates
        if name is not None: product.name = name
        if description is not None: product.description = description
        if mrp is not None and mrp>0:
            if product.price >mrp:
                raise HTTPException(400, "Price cannot exceed MRP")
            product.mrp = mrp
        if price is not None and price>0:
            if price >product.mrp:
                raise HTTPException(400, "Price cannot exceed MRP") 
            product.price = price
        if min_order_qty is not None: 
            if min_order_qty is not None and min_order_qty <= 0:
                raise HTTPException(400, "Invalid minimum order quantity")
            else:
                product.min_order_qty = min_order_qty
        if pack_size is not None: product.pack_size = pack_size
        if uom is not None: product.uom = uom
        if stock is not None:
            if stock is not None and stock < 0:
                raise HTTPException(400, "Stock cannot be negative")
            else:
                product.stock = stock
        if category_id is not None:
            if not db.query(Category).filter(
                Category.category_id == category_id,
                Category.is_active == True
            ).first():
                raise HTTPException(400, "Invalid category")
            product.category_id = category_id
        if brand_id is not None: 
            if not db.query(Brand).filter(
                Brand.brand_id == brand_id,
                Brand.is_active == True
            ).first():
                raise HTTPException(400, "Invalid brand")

            product.brand_id = brand_id

        # image update
        if image:
            old = os.path.join(PRODUCT_DIR, product.image)

            filename = f"{uuid.uuid4()}.{image.filename.split('.')[-1]}"
            path = os.path.join(PRODUCT_DIR, filename)
            with open(path, "wb") as f:
                f.write(image.file.read())

            product.image = filename
        after = snapshot(product, ["product_id", "name", "description", "mrp", "price", "min_order_qty", "pack_size", "uom", "stock", "category_id", "brand_id", "image", "is_active"])
        log_admin_activity(
            db = db,
            admin=admin,
            action="UPDATE",
            module="Product",
            request=request,
            endpoint=f"/admin/products/{product_id}",
            method="PUT",
            description=f"Updated product {product_id}",
            payload={
                'before': before,
                'after': after
                
            }
        )
        db.commit()
        # if product.image:
        if old:
            if os.path.exists(old):
                os.remove(old)
    
        
    except IntegrityError:
        db.rollback()
        if os.path.exists(path):
            os.remove(path)
        raise HTTPException(400, "Product already exists")
    except Exception as e:
        db.rollback()
        if os.path.exists(path):
            os.remove(path)
        raise HTTPException(500, str(e))
    
    return {"message": "Product updated"}

@router.put("/products/{product_id}/disable")
def disable_product(
    request: Request,
    product_id: str,
    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    product.is_active = False
    log_admin_activity(
        db = db,
        admin=admin,
        action="UPDATE",
        module="Product",
        request=request,
        endpoint=f"/admin/products/{product_id}/disable",
        method="PUT",
        description=f"Disabled product {product_id}"
    )
    db.commit()
    return {"message": "Product disabled"}

@router.put("/products/{product_id}/enable")
def enable_product(
    request: Request,
    product_id: str,
    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    product.is_active = True
    log_admin_activity(
        db = db,
        admin=admin,
        action="UPDATE",
        module="Product",
        request=request,
        endpoint=f"/admin/products/{product_id}/enable",
        method="PUT",
        description=f"Enabled product {product_id}"
    )
    db.commit()
    return {"message": "Product enabled"}

@router.delete("/products/{product_id}")
def delete_product(
    request: Request,
    product_id: str,
    db: Session = Depends(get_db),
    admin=Depends(super_admin_only)
):
    if not admin.is_super_admin:
        raise HTTPException(403, "Only super admin can delete")

    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")
    try:
        img = None
        if product.image:
            img = os.path.join(PRODUCT_DIR, product.image)
            
        delete_prd = snapshot(product,["product_id","name","description","price","mrp","min_order_qty","pack_size","uom","stock","category_id","brand_id","image","is_active"])

        db.delete(product)
        log_admin_activity(
            db = db,
            admin=admin,
            action="DELETE",
            module="Product",
            request=request,
            endpoint=f"/admin/products/{product_id}",
            method="POST",
            description=f"Deleted product {product_id}",
            payload={
                "deleted": delete_prd
            }
        )
        db.commit()
        if img and os.path.exists(img):
                os.remove(img)
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    return {"message": "Product permanently deleted"}


@router.get("/dashboard")
def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    return {
        "counts": {
            "admins": db.query(AdminUser).count(),
            "categories": db.query(Category).count(),
            "brands": db.query(Brand).count(),
            "products": db.query(Product).count(),
            "low_stock": db.query(Product).filter(Product.stock < 10).count()
        },
        "active": {
            "categories": db.query(Category).filter(Category.is_active == True).count(),
            "brands": db.query(Brand).filter(Brand.is_active == True).count(),
            "products": db.query(Product).filter(Product.is_active == True).count(),
        },
        "recent_activity": db.query(AdminActivityLog)
            .order_by(AdminActivityLog.created_at.desc())
            .limit(10)
            .all()
    }


@router.get("/activity-logs")
def list_admin_activity_logs(
    request: Request,
    admin_id: str | None = None,
    module: str | None = None,
    action: str | None = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    query = db.query(AdminActivityLog)

    if admin_id:
        query = query.filter(AdminActivityLog.admin_id == admin_id)

    if module:
        query = query.filter(AdminActivityLog.module == module)

    if action:
        query = query.filter(AdminActivityLog.action == action)

    total = query.count()

    logs = (
        query.order_by(AdminActivityLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "logs": logs
    }

