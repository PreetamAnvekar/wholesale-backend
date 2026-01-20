from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.routes.user_routes import router as user_router
from app.routes.admin_routes import router as admin_router

app = FastAPI(title="Wholesale Stationery API")

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local + future GitHub Pages
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= ROUTES =================
app.include_router(user_router)
app.include_router(admin_router)

# ================= STATIC (IMAGES + JS) =================
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ================= HEALTH =================
@app.get("/")
def health():
    return {"status": "API running"}
