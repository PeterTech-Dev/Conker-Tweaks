from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.routing import APIRoute

from auth.routes import auth_router
from products.routes import products_router
from owner.routes import owner_router
from orders.create import stripe_router
from orders.routes import order_router
from orders.webhooks import router as webhook_router

from database import Base, engine
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
import models

import os

app = FastAPI()

print("🔨 Checking database tables...")
Base.metadata.create_all(bind=engine)

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(products_router)
app.include_router(owner_router, prefix="/owner", tags=["Owner"])
app.include_router(order_router, prefix="/order/api", tags=["Orders"])
app.include_router(stripe_router, prefix="/order/api")
app.include_router(webhook_router, prefix="/webhooks")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_html(full_path: str):
    file_path = f"static/{full_path}"
    if full_path.endswith(".html") and os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse("static/Landing/Landing.html") if full_path == "" else HTMLResponse("<h1>404 Not Found</h1>", status_code=404)


origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "https://conkertweaks.com",
    "https://conker-tweaks-production.up.railway.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Debugger
for route in app.routes:
    if isinstance(route, APIRoute):
        print(f"Route: {route.path} [{route.methods}]")
