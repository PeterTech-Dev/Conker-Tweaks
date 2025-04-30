from fastapi import APIRouter, Request
import stripe
import json
import os

router = APIRouter()

# Make sure you load your Stripe secret key if needed
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Example Stripe webhook
@router.post("/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except ValueError as e:
        # Invalid payload
        return {"status": "invalid payload"}
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return {"status": "invalid signature"}

    # Handle event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        print("Payment successful:", session)
        # Here you can mark order as paid in your database

    return {"status": "success"}

# Example PayPal webhook
@router.post("/paypal")
async def paypal_webhook(request: Request):
    body = await request.json()
    print("PayPal Webhook received:", json.dumps(body, indent=2))

    # Handle PayPal events, for example:
    if body.get('event_type') == "CHECKOUT.ORDER.APPROVED":
        order_id = body.get('resource', {}).get('id')
        print(f"PayPal order approved: {order_id}")

    return {"status": "success"}
