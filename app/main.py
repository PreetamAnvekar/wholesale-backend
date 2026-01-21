from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes.user_routes import router as user_router
from app.routes.admin_routes import router as admin_router

from app.db.init_db import reset_database

app = FastAPI(title="Wholesale Stationery API")

# ⚠️ RUN ONLY ON FIRST DEPLOY
reset_database()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(admin_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def health():
    return {"status": "API running"}
