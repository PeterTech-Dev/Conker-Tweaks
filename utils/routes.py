from utils.recaptcha import create_assessment
import os

RECAPTCHA_PROJECT_ID = os.getenv("RECAPTCHA_PROJECT_ID")
RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY")
RECAPTCHA_MIN_SCORE = os.getenv("RECAPTCHA_MIN_SCORE")

