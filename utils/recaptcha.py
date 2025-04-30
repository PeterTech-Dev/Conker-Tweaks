# utils/recaptcha.py
import requests

def verify_recaptcha(token: str, secret_key: str, expected_action: str = None, min_score: float = 0.7):
    url = "https://www.google.com/recaptcha/api/siteverify"
    payload = {
        "secret": secret_key,
        "response": token,
    }

    r = requests.post(url, data=payload)
    result = r.json()
    print("🔎 Recaptcha result:", result)
    
    if not result.get("success"):
        raise ValueError("Invalid reCAPTCHA token")

    if expected_action and result.get("action") != expected_action:
        raise ValueError(f"Unexpected reCAPTCHA action: {result.get('action')}")

    if result.get("score", 0) < min_score:
        raise ValueError("Low reCAPTCHA score")

    return True
