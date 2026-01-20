from app.db.session import engine, Base

from app.models.admin_users import AdminUser
from app.models.admin_details import AdminDetail
from app.models.categories import Category
from app.models.products import Product
from app.models.enquiries import Enquiry
from app.models.enquiry_items import EnquiryItem
from app.models.cart import Cart
from app.models.email_logs import EmailLog
from app.models.user_visits import UserVisit
from app.models.admin_activity_logs import AdminActivityLog


def migrate():
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully")

if __name__ == "__main__":
    migrate()
