from fastapi import FastAPI, APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
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
from models.products import Product
import stripe
import httpx
from dotenv import load_dotenv
load_dotenv()

order_router = APIRouter()

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
environment = SandboxEnvironment(client_id=PAYPAL_CLIENT_ID, client_secret=PAYPAL_CLIENT_SECRET)
paypal_client = PayPalHttpClient(environment)
PAYPAL_API_BASE = "https://api-m.sandbox.paypal.com"

async def get_paypal_access_token():
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
        body = await request.json()
        print("Received PayPal order creation request:", body)

        access_token = await get_paypal_access_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        items = body.get("cart", [])
        if not items:
            raise ValueError("Cart is empty or missing.")

        total_amount = sum(float(item["price"]) * int(item["quantity"]) for item in items)

        order_payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": "USD",
                        "value": f"{total_amount:.2f}"
                    }
                }
            ]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PAYPAL_API_BASE}/v2/checkout/orders",
                json=order_payload,
                headers=headers
            )

        if response.status_code != 201:
            print("PayPal response error:", response.status_code, response.text)
            raise HTTPException(status_code=response.status_code, detail="Failed to create PayPal order")

        return response.json()

    except Exception as e:
        print("💥 PayPal order creation error:", e)
        raise HTTPException(status_code=500, detail=str(e))


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

        print(f"Looking for order with PayPal ID: {order_id}")
        order = db.query(Order).filter(Order.paypal_order_id == order_id).first()
        print(f"Found order: {order}")
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Get product info
        product = db.query(Product).filter(Product.id == order.product_id).first()
        if not product:
            raise HTTPException(status_code=500, detail="Product not found")

        # Assign license key
        existing_license = db.query(LicenseKey).filter(
            LicenseKey.product_id == order.product_id,
            LicenseKey.is_used == False
        ).first()

        if not existing_license:
            raise HTTPException(status_code=500, detail="No license keys available")

        existing_license.is_used = True
        existing_license.assigned_to_email = order.email
        db.commit()

        return JSONResponse(
            content={
                "transaction_id": transaction_id,
                "status": status,
                "license_key": existing_license.key,
                "download_link": product.download_link,
                "order": order_data,
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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