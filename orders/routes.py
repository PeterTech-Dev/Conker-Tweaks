from fastapi import FastAPI, APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from create import create_order
import requests
import os
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest
from paypalhttp import HttpError
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment
from datetime import datetime
from sqlalchemy.orm import Session
from auth.auth_utils import get_current_user
from database import SessionLocal, get_db
from models.users import User
from models.licenses import LicenseKey
from models.orders import Order
import stripe
import httpx
from dotenv import load_dotenv
load_dotenv()

order_router = APIRouter(prefix="/order/api")

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
environment = SandboxEnvironment(client_id=PAYPAL_CLIENT_ID, client_secret=PAYPAL_CLIENT_SECRET)
paypal_client = PayPalHttpClient(environment)

def get_paypal_access_token():
    url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
    response = requests.post(
        url,
        auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
    )
    response.raise_for_status()
    return response.json()["access_token"]

@order_router.post("/orders")
async def create_order(request: Request):
    try:
        access_token = await get_paypal_access_token()
        body = await request.json()
        cart = body.get("cart", [])

        total_amount = sum(item['price'] * item['quantity'] for item in cart)
        total_amount = format(total_amount, '.2f')

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": "USD",
                        "value": total_amount
                    }
                }
            ]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api-m.sandbox.paypal.com/v2/checkout/orders",
                headers=headers,
                json=order_data
            )
            if response.status_code >= 400:
                raise HTTPException(status_code=500, detail="Failed to create PayPal order")
            
            paypal_order = response.json()
            # ✨ ONLY return the PayPal order ID
            return {"id": paypal_order["id"]}

    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"error": str(e)})

@order_router.post("/orders/{order_id}/capture")
async def capture_order(order_id: str, db: Session = Depends(get_db)):
    capture_request = OrdersCaptureRequest(order_id)
    capture_request.request_body({})

    try:
        response = paypal_client.execute(capture_request)
        order_data = response.result.__dict__["_dict"]

        transaction_id = order_data.get("id")
        status = order_data.get("status")

        if not transaction_id:
            raise HTTPException(status_code=400, detail="Transaction ID not found")

        # 🧠 Find the order in your database if you saved it during createOrder()
        # If you don't have a database order, you can skip this
        order = db.query(Order).filter(Order.order_id == order_id).first()

        assigned_email = None
        if order:
            assigned_email = order.email  # If you stored email during createOrder

        # 🔥 Generate a license key based on transaction ID
        license_key_value = f"LICENSE-{transaction_id[-8:]}"
        new_license = LicenseKey(
            key=license_key_value,
            product_id=1,  # Assuming product_id=1 is valid
            is_used=False,
            assigned_to_email=assigned_email,
        )
        db.add(new_license)
        db.commit()

        return JSONResponse(
            content={
                "transaction_id": transaction_id,
                "status": status,
                "license_key": license_key_value,
                "order": order_data,
            }
        )

    except HttpError as e:
        return JSONResponse(status_code=e.status_code, content={"error": str(e)})
    
@order_router.post("/create-stripe-checkout")
async def create_stripe_checkout(cart: list):
    line_items = []

    for item in cart:
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

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url='https://yourdomain.com/Checkout/thankyou.html?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://yourdomain.com/Pricing/Pricing.html',
        )
        return {"checkout_url": session.url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))