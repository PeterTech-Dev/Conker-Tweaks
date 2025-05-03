from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
import httpx
import os
import base64
from dotenv import load_dotenv
from database import SessionLocal
from models.products import Product
from models.licenses import LicenseKey
from models.order import Order
from auth.auth_utils import get_current_user
from sqlalchemy.orm import Session
from database import get_db
import stripe
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment
from paypalcheckoutsdk.orders import OrdersCaptureRequest

stripe_router = APIRouter()

load_dotenv()

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
stripe.api_key = STRIPE_API_KEY
PAYPAL_OAUTH_API = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
PAYPAL_ORDERS_API = "https://api-m.sandbox.paypal.com/v2/checkout/orders"
print("🔑 Stripe key loaded:", stripe.api_key)

environment = SandboxEnvironment(client_id=PAYPAL_CLIENT_ID, client_secret=PAYPAL_CLIENT_SECRET)
paypal_client = PayPalHttpClient(environment)

async def get_paypal_access_token():
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="PayPal credentials missing")

    auth = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api-m.sandbox.paypal.com/v1/oauth2/token",
            headers=headers,
            data={"grant_type": "client_credentials"},
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch PayPal access token")

        return response.json()["access_token"]

@stripe_router.post("/stripe/create-session")
async def stripe_create_session(request: Request):
    try:
        body = await request.json()
        print("Cart payload:", body)

        cart = body.get("cart", [])
        if not cart:
            print("Cart is empty or missing.")
            raise HTTPException(status_code=400, detail="Cart is empty")

        line_items = []
        for item in cart:
            print("Item:", item)
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item['name'],
                    },
                    'unit_amount': int(float(item['price']) * 100),
                },
                'quantity': item['quantity'],
            })

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url="https://conker-tweaks-production.up.railway.app/static/Checkout/thankyou.html?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://conker-tweaks-production.up.railway.app/static/Checkout/Checkout.html",
        )

        print("Stripe session created:", session.url)
        return JSONResponse(content={"checkout_url": session.url})

    except Exception as e:
        print("Stripe error:", e)
        raise HTTPException(status_code=500, detail=str(e))



@stripe_router.post("/orders/{order_id}/capture")
async def capture_order(order_id: str, db: Session = Depends(get_db)):
    capture_request = OrdersCaptureRequest(order_id)
    capture_request.request_body({})

    try:
        response = paypal_client.execute(capture_request)
        order_data = response.result.__dict__["_dict"]

        transaction_id = order_data.get("id")
        if not transaction_id:
            raise HTTPException(status_code=400, detail="Transaction ID not found")

        order = db.query(Order).filter(Order.paypal_order_id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        assigned_keys = []
        for item in order.order_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                continue

            license_key = db.query(LicenseKey).filter(
                LicenseKey.product_id == item.product_id,
                LicenseKey.is_used == False
            ).first()

            if not license_key:
                continue  # Or raise error if all items must have keys

            license_key.is_used = True
            license_key.assigned_to_email = order.email
            db.commit()

            assigned_keys.append({
                "product_id": item.product_id,
                "license_key": license_key.key,
                "download_link": product.download_link
            })

        return JSONResponse(content={
            "transaction_id": transaction_id,
            "status": order_data.get("status"),
            "licenses": assigned_keys,
            "order": order_data
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@stripe_router.post("/orders/create")
async def create_paypal_order(request: Request):
    cart = await request.json()
    access_token = await get_paypal_access_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    items = []
    total_amount = 0
    for item in cart["cart"]:
        total = float(item["price"]) * int(item["quantity"])
        total_amount += total
        items.append({
            "name": item["name"],
            "unit_amount": {
                "currency_code": "USD",
                "value": f"{item['price']:.2f}"
            },
            "quantity": str(item["quantity"]),
        })

    data = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {
                "currency_code": "USD",
                "value": f"{total_amount:.2f}",
                "breakdown": {
                    "item_total": {
                        "currency_code": "USD",
                        "value": f"{total_amount:.2f}"
                    }
                }
            },
            "items": items
        }]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(PAYPAL_ORDERS_API, headers=headers, json=data)
        response.raise_for_status()
        return response.json()


