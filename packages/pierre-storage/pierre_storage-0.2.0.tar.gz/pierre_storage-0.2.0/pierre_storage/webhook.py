"""Webhook validation utilities for Pierre Git Storage SDK."""

import hashlib
import hmac
import json
import time
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from pierre_storage.types import (
    ParsedWebhookSignature,
    WebhookPushEvent,
    WebhookValidationOptions,
    WebhookValidationResult,
)

__all__ = [
    "WebhookPushEvent",
    "parse_signature_header",
    "validate_webhook",
    "validate_webhook_signature",
]


def parse_signature_header(signature: str) -> ParsedWebhookSignature:
    """Parse the X-Pierre-Signature header.

    Args:
        signature: The signature header value (format: "t=timestamp,s=signature")

    Returns:
        Parsed signature with timestamp and signature components

    Raises:
        ValueError: If signature format is invalid
    """
    parts = signature.split(",")
    timestamp = None
    sig = None

    for part in parts:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        if key == "t":
            timestamp = value
        elif key == "s":
            sig = value

    if not timestamp or not sig:
        raise ValueError("Invalid signature header format")

    return {"timestamp": timestamp, "signature": sig}


def validate_webhook_signature(
    payload: str,
    signature: str,
    secret: str,
    max_age_seconds: int = 300,
) -> bool:
    """Validate a webhook signature.

    Args:
        payload: Raw webhook payload (JSON string)
        signature: Signature header value
        secret: Webhook secret for HMAC validation
        max_age_seconds: Maximum age of webhook in seconds (default: 5 minutes)

    Returns:
        True if signature is valid and not expired, False otherwise
    """
    try:
        parsed = parse_signature_header(signature)
        timestamp = int(parsed["timestamp"])
        expected_sig = parsed["signature"]

        # Check timestamp to prevent replay attacks
        if max_age_seconds > 0:
            current_time = int(time.time())
            if abs(current_time - timestamp) > max_age_seconds:
                return False

        # Compute expected signature
        signed_payload = f"{timestamp}.{payload}"
        computed_sig = hmac.new(
            secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Compare signatures using constant-time comparison
        return hmac.compare_digest(computed_sig, expected_sig)

    except (ValueError, KeyError):
        return False


def validate_webhook(
    payload: str,
    signature: str,
    secret: str,
    options: Optional[WebhookValidationOptions] = None,
) -> WebhookValidationResult:
    """Validate a webhook and parse its payload.

    Args:
        payload: Raw webhook payload (JSON string)
        signature: Signature header value
        secret: Webhook secret for HMAC validation
        options: Validation options (max_age_seconds, etc.)

    Returns:
        Validation result with status and parsed data
    """
    max_age = 300
    if options and "max_age_seconds" in options:
        max_age = options["max_age_seconds"]

    result: WebhookValidationResult = {
        "valid": False,
        "error": None,
        "event_type": None,
        "timestamp": None,
    }

    try:
        parsed_sig = parse_signature_header(signature)
        timestamp = int(parsed_sig["timestamp"])
        result["timestamp"] = timestamp

        # Validate signature
        if not validate_webhook_signature(payload, signature, secret, max_age):
            result["error"] = "Invalid signature or expired webhook"
            return result

        # Parse payload
        data = json.loads(payload)

        # Determine event type
        if "ref" in data and "repository" in data:
            result["event_type"] = "push"

        result["valid"] = True
        return result

    except ValueError as e:
        result["error"] = f"Invalid webhook format: {e}"
        return result
    except Exception as e:
        result["error"] = f"Webhook validation failed: {e}"
        return result


def parse_push_event(payload: Dict[str, Any]) -> WebhookPushEvent:
    """Parse a push event webhook payload.

    Args:
        payload: Parsed JSON webhook payload

    Returns:
        Parsed push event

    Raises:
        ValueError: If payload is not a valid push event
    """
    try:
        pushed_at_str = payload.get("pushed_at", "")
        pushed_at = datetime.fromisoformat(pushed_at_str.replace("Z", "+00:00"))

        return {
            "type": "push",
            "repository": payload["repository"],
            "ref": payload["ref"],
            "before": payload["before"],
            "after": payload["after"],
            "customer_id": payload["customer_id"],
            "pushed_at": pushed_at,
            "raw_pushed_at": pushed_at_str,
        }
    except (KeyError, ValueError) as e:
        raise ValueError(f"Invalid push event payload: {e}") from e
