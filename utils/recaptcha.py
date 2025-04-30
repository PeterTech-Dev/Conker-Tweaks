# recaptcha.py
from google.cloud import recaptchaenterprise_v1
from google.cloud.recaptchaenterprise_v1 import Assessment

def create_assessment(project_id: str, recaptcha_key: str, token: str, recaptcha_action: str) -> Assessment:
    client = recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient()

    event = recaptchaenterprise_v1.Event()
    event.site_key = recaptcha_key
    event.token = token

    assessment = recaptchaenterprise_v1.Assessment()
    assessment.event = event

    request = recaptchaenterprise_v1.CreateAssessmentRequest(
        assessment=assessment,
        parent=f"projects/{project_id}"
    )

    response = client.create_assessment(request)

    if not response.token_properties.valid:
        raise ValueError("Invalid reCAPTCHA token: " + str(response.token_properties.invalid_reason))

    if response.token_properties.action != recaptcha_action:
        raise ValueError("Unexpected reCAPTCHA action")

    return response
