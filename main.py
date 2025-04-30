from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer

from auth.routes import auth_router
from products.routes import products_router
from admin.routes import admin_router
from orders.routes import order_router
from orders.webhooks import router as webhook_router

from database import Base, engine
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse

import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_html(full_path: str):
    file_path = f"static/{full_path}"
    if os.path.exists(file_path) and file_path.endswith(".html"):
        return FileResponse(file_path)
    else:
        return FileResponse("static/Landing/Landing.html")

print("🔨 Checking database tables...")
Base.metadata.create_all(bind=engine)

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(products_router, prefix="/products", tags=["Products"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(order_router)
app.include_router(webhook_router, prefix="/webhooks")

origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "https://yourfrontenddomain.com",
    "https://www.yourfrontenddomain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
