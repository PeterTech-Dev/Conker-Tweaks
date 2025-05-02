from fastapi import APIRouter, Request, HTTPException, FastAPI
from fastapi.responses import JSONResponse
import httpx
import os
import base64
from dotenv import load_dotenv
from database import SessionLocal
from models.products import Product
from models.licenses import LicenseKey
import stripe

order_router = APIRouter()
router = APIRouter(
    prefix="/order/api",   # same as your other router
)

load_dotenv()

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
stripe.api_key = os.getenv("STRIPE_API_KEY")
PAYPAL_OAUTH_API = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
PAYPAL_ORDERS_API = "https://api-m.sandbox.paypal.com/v2/checkout/orders"

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

@order_router.post("/create/stripe")
async def create_stripe_checkout(request: Request):
    body = await request.json()
    amount = body.get("amount")

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': 'Conker Tweaks Purchase',
                },
                'unit_amount': int(float(amount) * 100),  # Stripe needs cents
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url="http://https://conker-tweaks-production.up.railway.app/Checkout/thankyou.html",
        cancel_url="http://https://conker-tweaks-production.up.railway.app/Checkout/Checkout.html",
    )

    return JSONResponse(content={"checkout_url": session.url}) 

@router.post("/orders/{order_id}/capture")
async def create_paypal_order(cart):
    access_token = await get_paypal_access_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    items = []
    for item in cart["cart"]:
        items.append({
            "name": item["name"],
            "unit_amount": {
                "currency_code": "USD",
                "value": str(item["price"])
            },
            "quantity": str(item["quantity"]),
        })

    data = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "items": items,
            "amount": {
                "currency_code": "USD",
                "value": str(sum(float(i["unit_amount"]["value"]) * int(i["quantity"]) for i in items))
            }
        }]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(PAYPAL_ORDERS_API, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["id"]

