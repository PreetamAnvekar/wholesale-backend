from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.routes.user_routes import router as user_router
from app.routes.admin_routes import router as admin_router

from app.db.session import engine
from app.db.base import Base

app = FastAPI(title="Wholesale Stationery API")

# ================= CREATE TABLES =================
@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= ROUTES =================
app.include_router(user_router)
app.include_router(admin_router)

# ================= STATIC =================
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ================= HEALTH =================
@app.get("/")
def health():
    return {"status": "API running"}
