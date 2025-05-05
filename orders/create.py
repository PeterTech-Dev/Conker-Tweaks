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
from models.order_items import OrderItem
from models.users import User
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
stripe.api_key = os.getenv("STRIPE_API_KEY")
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
async def stripe_create_session(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stripe.api_key = os.getenv("STRIPE_API_KEY")

    try:
        body = await request.json()
        print("Cart payload:", body)

        cart = body.get("cart", [])
        if not cart:
            raise HTTPException(status_code=400, detail="Cart is empty")

        email = current_user.email  # Use the authenticated user's email

        line_items = []
        total_amount = 0

        for item in cart:
            print("➡️  Item:", item)
            total_price = float(item['price']) * int(item['quantity'])
            total_amount += total_price

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

        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url="https://conker-tweaks-production.up.railway.app/static/Checkout/thankyou.html?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://conker-tweaks-production.up.railway.app/static/Checkout/Checkout.html",
            customer_email=email,
        )

        # Save order to DB
        new_order = Order(
            user_id=current_user.id,
            email=email,
            price=float(cart[0]['price']),
            amount_paid=total_amount,
            product_id=cart[0]['id'],
            stripe_session_id=session.id
        )
        db.add(new_order)
        db.flush()  # So new_order.id is available

        for item in cart:
            db.add(OrderItem(
                order_id=new_order.id,
                product_id=item['id'],
                quantity=item['quantity'],
                price=item['price']
            ))

        db.commit()

        print("Session URL:", session.url)
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
            
            product.stock -= item.quantity

            license_key = db.query(LicenseKey).filter(
                LicenseKey.product_id == item.product_id,
                LicenseKey.is_used == False
            ).first()

            if not license_key:
                continue

            license_key.is_used = True
            license_key.assigned_to_email = order.email
            db.commit()

            assigned_keys.append({
                "product_id": item.product_id,
                "license_key": license_key.key,
                "download_link": product.download_link
            })
            
            if user:
                user.current_package = product.name
                user.license_key = license_keys[-1].key if license_keys else None
                user.download_link = product.download_link

        return JSONResponse(content={
            "transaction_id": transaction_id,
            "status": order_data.get("status"),
            "licenses": assigned_keys,
            "order": order_data
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@stripe_router.get("/stripe/session/{session_id}")
async def get_stripe_checkout_details(session_id: str, db: Session = Depends(get_db)):
    try:
        session = stripe.checkout.Session.retrieve(
            session_id,
            expand=["customer_details"]
        )

        customer_email = session.customer_details.email
        if not customer_email:
            raise HTTPException(status_code=400, detail="Missing customer email")

        order = db.query(Order).filter(Order.email == customer_email).order_by(Order.id.desc()).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        licenses = []
        for item in order.order_items:
            available_keys = db.query(LicenseKey).filter(
                LicenseKey.product_id == item.product_id,
                LicenseKey.is_used == False
            ).limit(item.quantity).all()

            if len(available_keys) < item.quantity:
                raise HTTPException(status_code=500, detail="Not enough license keys")

            for key in available_keys:
                key.is_used = True
                key.assigned_to_email = order.email
                licenses.append({
                    "license": key.key,
                    "download": item.product.download_link
                })

        db.commit()

        return {
            "transaction_id": session.id,
            "status": session.payment_status,
            "licenses": licenses,
            "order": {
                "email": order.email,
                "amount_paid": order.amount_paid,
            }
        }

    except Exception as e:
        print("❌ Stripe session fetch error:", e)
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


