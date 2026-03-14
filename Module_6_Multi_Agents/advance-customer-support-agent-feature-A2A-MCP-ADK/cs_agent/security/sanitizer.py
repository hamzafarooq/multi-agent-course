import os
import re
import logging

import requests
from google.auth.transport.requests import Request
from google.auth import default

logger = logging.getLogger(__name__)

ALLOWED_CHARS = set(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-'"
)

MAX_INPUT_LENGTH = 300


def _get_access_token() -> str:
    """Obtain a GCP access token via Application Default Credentials."""
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    credentials, _ = default(scopes=scopes)
    credentials.refresh(Request())
    return credentials.token


def sanitize_input(
    text: str,
    project_id: str | None = None,
    location: str | None = None,
    template_id: str | None = None,
) -> str:
    """Validate and sanitize input text through multiple security layers.

    Layers:
      1. Length limit (MAX_INPUT_LENGTH chars)
      2. Character whitelisting
      3. Google Model Armor API (optional, when project/location/template are set)
      4. Final regex validation

    Returns the sanitized text.
    Raises ValueError on invalid input.
    """
    project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "")
    location = location or os.getenv("GOOGLE_CLOUD_LOCATION", "")
    template_id = template_id or os.getenv("MODEL_ARMOR_TEMPLATE_ID", "")

    if len(text) > MAX_INPUT_LENGTH:
        raise ValueError(f"Text exceeds {MAX_INPUT_LENGTH} characters")

    sanitized = "".join(char for char in text if char in ALLOWED_CHARS)

    if project_id and location and template_id:
        try:
            url = (
                f"https://modelarmor.{location}.rep.googleapis.com/v1/"
                f"projects/{project_id}/locations/{location}/"
                f"templates/{template_id}:sanitizeUserPrompt"
            )
            headers = {
                "Authorization": f"Bearer {_get_access_token()}",
                "Content-Type": "application/json",
            }
            payload = {"user_prompt_data": {"text": sanitized}}
            response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                sanitized_result = response.json()
                sanitized = sanitized_result.get("sanitizedText", sanitized)
            else:
                logger.warning(
                    "Model Armor API returned %s: %s",
                    response.status_code,
                    response.text,
                )
        except Exception as exc:
            logger.warning("Model Armor call failed, continuing without it: %s", exc)

    if not re.match(r"^[a-zA-Z0-9\s.,!?()\'-]*$", sanitized):
        raise ValueError("Invalid characters detected after sanitization")

    return sanitized
