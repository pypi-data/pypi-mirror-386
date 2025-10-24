"""Tests for webhook validation."""

import hashlib
import hmac
import json
import time

import pytest

from pierre_storage.webhook import (
    parse_push_event,
    parse_signature_header,
    validate_webhook,
    validate_webhook_signature,
)


class TestWebhookValidation:
    """Tests for webhook validation."""

    def test_parse_signature_header(self) -> None:
        """Test parsing signature header."""
        signature = "t=1234567890,s=abcdef123456"
        parsed = parse_signature_header(signature)

        assert parsed["timestamp"] == "1234567890"
        assert parsed["signature"] == "abcdef123456"

    def test_parse_signature_header_invalid(self) -> None:
        """Test parsing invalid signature header."""
        with pytest.raises(ValueError, match="Invalid signature header format"):
            parse_signature_header("invalid")

    def test_validate_webhook_signature(self) -> None:
        """Test validating webhook signature."""
        secret = "test-secret"
        payload = json.dumps({"test": "data"})
        timestamp = int(time.time())

        # Create valid signature
        signed_payload = f"{timestamp}.{payload}"
        signature = hmac.new(
            secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        signature_header = f"t={timestamp},s={signature}"

        # Validate
        result = validate_webhook_signature(
            payload,
            signature_header,
            secret,
            max_age_seconds=300,
        )
        assert result is True

    def test_validate_webhook_signature_invalid(self) -> None:
        """Test validating invalid webhook signature."""
        secret = "test-secret"
        payload = json.dumps({"test": "data"})
        timestamp = int(time.time())

        signature_header = f"t={timestamp},s=invalid_signature"

        result = validate_webhook_signature(
            payload,
            signature_header,
            secret,
            max_age_seconds=300,
        )
        assert result is False

    def test_validate_webhook_signature_expired(self) -> None:
        """Test validating expired webhook signature."""
        secret = "test-secret"
        payload = json.dumps({"test": "data"})
        timestamp = int(time.time()) - 400  # 400 seconds ago

        # Create valid signature
        signed_payload = f"{timestamp}.{payload}"
        signature = hmac.new(
            secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        signature_header = f"t={timestamp},s={signature}"

        # Validate with 300 second max age
        result = validate_webhook_signature(
            payload,
            signature_header,
            secret,
            max_age_seconds=300,
        )
        assert result is False

    def test_validate_webhook(self) -> None:
        """Test full webhook validation."""
        secret = "test-secret"
        payload_data = {
            "repository": {"id": "repo-123", "url": "https://test.git"},
            "ref": "refs/heads/main",
            "before": "abc123",
            "after": "def456",
            "customer_id": "cust-123",
            "pushed_at": "2024-01-15T10:30:00Z",
        }
        payload = json.dumps(payload_data)
        timestamp = int(time.time())

        # Create valid signature
        signed_payload = f"{timestamp}.{payload}"
        signature = hmac.new(
            secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        signature_header = f"t={timestamp},s={signature}"

        # Validate
        result = validate_webhook(payload, signature_header, secret)
        assert result["valid"] is True
        assert result["event_type"] == "push"
        assert result["timestamp"] == timestamp
        assert result["error"] is None

    def test_parse_push_event(self) -> None:
        """Test parsing push event."""
        payload = {
            "repository": {"id": "repo-123", "url": "https://test.git"},
            "ref": "refs/heads/main",
            "before": "abc123",
            "after": "def456",
            "customer_id": "cust-123",
            "pushed_at": "2024-01-15T10:30:00Z",
        }

        event = parse_push_event(payload)

        assert event["type"] == "push"
        assert event["repository"]["id"] == "repo-123"
        assert event["ref"] == "refs/heads/main"
        assert event["before"] == "abc123"
        assert event["after"] == "def456"
        assert event["customer_id"] == "cust-123"
        assert event["raw_pushed_at"] == "2024-01-15T10:30:00Z"
        assert event["pushed_at"].year == 2024
        assert event["pushed_at"].month == 1
        assert event["pushed_at"].day == 15

    def test_parse_push_event_invalid(self) -> None:
        """Test parsing invalid push event."""
        with pytest.raises(ValueError, match="Invalid push event payload"):
            parse_push_event({"invalid": "data"})
