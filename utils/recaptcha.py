import requests
from fastapi import HTTPException

RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
RECAPTCHA_MIN_SCORE = 0.7  # or adjust based on how strict you want it

def verify_recaptcha(token: str, secret_key: str, expected_action: str):
    data = {
        'secret': secret_key,
        'response': token
    }

    response = requests.post(RECAPTCHA_VERIFY_URL, data=data)
    result = response.json()

    if not result.get("success"):
        raise HTTPException(status_code=400, detail="Invalid reCAPTCHA token.")

    if result.get("action") != expected_action:
        raise HTTPException(status_code=400, detail="reCAPTCHA action mismatch.")

    if result.get("score", 0) < RECAPTCHA_MIN_SCORE:
        raise HTTPException(status_code=400, detail="Low reCAPTCHA score — suspected bot.")

    return True
