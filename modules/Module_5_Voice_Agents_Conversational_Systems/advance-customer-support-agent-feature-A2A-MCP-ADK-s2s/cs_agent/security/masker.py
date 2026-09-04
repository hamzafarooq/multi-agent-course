import os
import logging

from google.cloud import dlp_v2

logger = logging.getLogger(__name__)

PII_INFO_TYPES = [
    {"name": "EMAIL_ADDRESS"},
    {"name": "PHONE_NUMBER"},
    {"name": "CREDIT_CARD_NUMBER"},
    {"name": "US_SOCIAL_SECURITY_NUMBER"},
    {"name": "PERSON_NAME"},
    {"name": "IP_ADDRESS"},
    {"name": "DATE_OF_BIRTH"},
    {"name": "STREET_ADDRESS"},
    {"name": "PASSWORD"},
    {"name": "URL"},
    {"name": "AGE"},
    {"name": "VEHICLE_IDENTIFICATION_NUMBER"},
    {"name": "IBAN_CODE"},
    {"name": "MAC_ADDRESS"},
    {"name": "US_EMPLOYER_IDENTIFICATION_NUMBER"},
    {"name": "LOCATION_COORDINATES"},
]


def mask_sensitive_data(project_id: str | None, text: str) -> str:
    """Detect and mask PII in *text* using Google Cloud DLP.

    Each finding is replaced with asterisks of the same byte length so that
    positional offsets remain stable during reverse-order replacement.
    """
    project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "")
    if not project_id:
        logger.warning("No GOOGLE_CLOUD_PROJECT set; returning text unmasked")
        return text

    client = dlp_v2.DlpServiceClient()
    parent = f"projects/{project_id}"

    request = {
        "parent": parent,
        "inspect_config": {"info_types": PII_INFO_TYPES},
        "item": {
            "byte_item": {
                "type": "TEXT_UTF8",
                "data": text.encode("utf-8"),
            }
        },
    }

    response = client.inspect_content(request=request)
    masked_text = text

    findings = sorted(
        response.result.findings,
        key=lambda f: f.location.byte_range.start,
        reverse=True,
    )

    for finding in findings:
        start = finding.location.byte_range.start
        end = finding.location.byte_range.end
        masked_text = masked_text[:start] + "*" * (end - start) + masked_text[end:]

    return masked_text
