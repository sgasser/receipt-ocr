#!/usr/bin/env python3
"""Extract structured data from receipts/invoices using Gemini Vision API."""

import base64
import json
import os
import sys
from pathlib import Path

import requests

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

PROMPT = """Extract all information from this receipt/invoice image.

Rules:
- date: Convert to YYYY-MM-DD (e.g. "20/11/25" becomes 2025-11-20)
- card_last_4: Extract last 4 digits from masked card numbers like ****1234
- tax rate: Percentage as integer (19 not 0.19)
- currency: ISO 4217 code (e.g. EUR, USD, CHF)
- country: ISO 3166-1 alpha-2 code (e.g. DE, AT, US)"""

SCHEMA = {
    "type": "object",
    "properties": {
        "receipt": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Date in ISO format YYYY-MM-DD"},
                "number": {"type": "string", "nullable": True},
                "type": {"type": "string", "enum": ["invoice", "receipt", "cash_register", "credit_note"]}
            }
        },
        "amounts": {
            "type": "object",
            "properties": {
                "gross": {"type": "number"},
                "net": {"type": "number", "nullable": True},
                "currency": {"type": "string", "description": "ISO 4217 code (EUR, USD, PEN, CHF)"}
            }
        },
        "taxes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "rate": {"type": "number", "description": "Tax rate as percentage (e.g. 19 not 0.19)"},
                    "amount": {"type": "number"}
                }
            }
        },
        "issuer": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string", "nullable": True},
                        "postal_code": {"type": "string", "nullable": True},
                        "city": {"type": "string", "nullable": True},
                        "country": {"type": "string", "description": "ISO 3166-1 alpha-2 code (DE, AT, US, PE)"}
                    }
                },
                "vat_id": {"type": "string", "nullable": True},
                "tax_number": {"type": "string", "nullable": True}
            }
        },
        "payment": {
            "type": "object",
            "properties": {
                "method": {"type": "string", "enum": ["card", "cash", "transfer", "paypal", "unknown"]},
                "card_last_4": {"type": "string", "nullable": True}
            }
        },
        "raw_text": {"type": "string", "description": "Complete OCR text"}
    }
}


def get_api_key():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("GEMINI_API_KEY="):
                os.environ.setdefault("GEMINI_API_KEY", line.split("=", 1)[1])
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("Error: GEMINI_API_KEY not set. Get one at https://aistudio.google.com/apikey")
    return key


def process(path: Path):
    if not path.exists():
        sys.exit(f"Error: File not found: {path}")

    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "pdf": "application/pdf"}

    resp = requests.post(
        f"{GEMINI_URL}?key={get_api_key()}",
        json={
            "contents": [{"parts": [
                {"text": PROMPT},
                {"inline_data": {
                    "mime_type": mime.get(path.suffix[1:].lower(), "image/jpeg"),
                    "data": base64.b64encode(path.read_bytes()).decode()
                }}
            ]}],
            "generationConfig": {"response_mime_type": "application/json", "response_schema": SCHEMA}
        },
        timeout=60
    )
    resp.raise_for_status()
    return json.loads(resp.json()["candidates"][0]["content"]["parts"][0]["text"])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(f"Usage: {sys.argv[0]} <image> [image...]")

    results = [process(Path(f)) for f in sys.argv[1:]]
    print(json.dumps(results[0] if len(results) == 1 else results, indent=2, ensure_ascii=False))
