from app.db.session import engine
from app.db.base import Base

def reset_database():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)

    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    print("Database reset complete")
