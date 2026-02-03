from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.categories import Category
from app.models.products import Product
from app.models.cart import Cart
from app.models.enquiries import Enquiry
from app.models.enquiry_items import EnquiryItem
from app.models.admin_users import AdminUser
from app.models.admin_details import AdminDetail
from app.models.email_logs import EmailLog
from app.models.user_visits import UserVisit
from app.models.admin_activity_logs import AdminActivityLog

def seed():
    db: Session = SessionLocal()

    try:
        # ----------------------------
        # ADMIN USERS
        # ----------------------------
        admin1 = AdminUser(
            username="admin",
            password="admin123",
            email="admin@test.com",
            is_super_admin=True
        )
        admin2 = AdminUser(
            username="",
            password="vendor123",
            email="vendor@test.com",
            is_super_admin=False
        )
        db.add_all([admin1, admin2])
        db.commit()

        # ----------------------------
        # ADMIN DETAILS
        # ----------------------------
        db.add_all([
            AdminDetail(admin_id=admin1.id, detail_type="address", detail_value="Pune, India"),
            AdminDetail(admin_id=admin1.id, detail_type="phone", detail_value="+919999999999")
        ])
        db.commit()

        # ----------------------------
        # CATEGORIES
        # ----------------------------
        cat1 = Category(
            category_id="CAT001",
            name="Notebooks",
            description="School & office notebooks",
            image="notebooks.jpg"
        )
        cat2 = Category(
            category_id="CAT002",
            name="Pens",
            description="Ball pens & gel pens",
            image="pens.jpg"
        )
        db.add_all([cat1, cat2])
        db.commit()

        # ----------------------------
        # PRODUCTS
        # ----------------------------
        prod1 = Product(
            product_id="PRD001",
            category_id="CAT001",
            name="Classmate Notebook",
            description="200 pages notebook",
            price=120,
            min_order_qty=10,
            stock=500,
            image="classmate.jpg"
        )
        prod2 = Product(
            product_id="PRD002",
            category_id="CAT002",
            name="Reynolds Pen",
            description="Blue ball pen",
            price=10,
            min_order_qty=50,
            stock=2000,
            image="reynolds.jpg"
        )
        db.add_all([prod1, prod2])
        db.commit()

        # ----------------------------
        # CART
        # ----------------------------
        cart1 = Cart(session_id="sess123", product_id="PRD001", quantity=20)
        cart2 = Cart(session_id="sess123", product_id="PRD002", quantity=100)
        db.add_all([cart1, cart2])
        db.commit()

        # ----------------------------
        # ENQUIRIES
        # ----------------------------
        enquiry = Enquiry(customer_name="ABC Stationery", phone="9876543210")
        db.add(enquiry)
        db.commit()
        db.refresh(enquiry)

        # ----------------------------
        # ENQUIRY ITEMS
        # ----------------------------
        db.add_all([
            EnquiryItem(enquiry_id=enquiry.id, product_id="PRD001", quantity=20),
            EnquiryItem(enquiry_id=enquiry.id, product_id="PRD002", quantity=100)
        ])
        db.commit()

        # ----------------------------
        # EMAIL LOGS
        # ----------------------------
        db.add_all([
            EmailLog(enquiry_id=enquiry.id, email_to="admin@test.com", sent_status=True),
            EmailLog(enquiry_id=enquiry.id, email_to="vendor@test.com", sent_status=True)
        ])
        db.commit()

        # ----------------------------
        # USER VISITS
        # ----------------------------
        db.add_all([
            UserVisit(session_id="sess123", ip_address="127.0.0.1", visited_page="/"),
            UserVisit(session_id="sess123", ip_address="127.0.0.1", visited_page="/categories")
        ])
        db.commit()

        # ----------------------------
        # ADMIN ACTIVITY LOGS
        # ----------------------------
        db.add_all([
            AdminActivityLog(
                admin_id=admin1.id,
                action="CREATE",
                module="CATEGORY",
                description="Added Notebooks category",
                ip_address="127.0.0.1"
            ),
            AdminActivityLog(
                admin_id=admin1.id,
                action="CREATE",
                module="PRODUCT",
                description="Added Classmate Notebook",
                ip_address="127.0.0.1"
            )
        ])
        db.commit()

        print("✅ Dummy data inserted successfully")

    except Exception as e:
        db.rollback()
        print("❌ Error inserting dummy data:", e)

    finally:
        db.close()


if __name__ == "__main__":
    seed()
