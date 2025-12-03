#!/usr/bin/env python3
"""
Integration tests for receipt_ocr with real API calls.
Uses AI-generated example images with known values.
"""

import subprocess
import json
import sys

EXAMPLES = {
    "examples/ai_invoice_01.jpg": {
        "description": "EDEKA supermarket receipt",
        "expected": {
            "issuer_name": "EDEKA Müller",
            "address_city": "München",
            "address_country": "DE",
            "vat_id": "DE123456789",
            "receipt_number": "0847",
            "receipt_date": "2025-12-03",
            "receipt_type": ["cash_register", "receipt"],  # Both valid for supermarket
            "amounts_gross": 50.00,
            "amounts_net": 41.93,
            "amounts_currency": "EUR",
            "tax_rates": [19, 7],
            "payment_method": "card",
            "card_last_4": "1234",
        }
    },
    "examples/ai_receipt_02.jpg": {
        "description": "TechShop Berlin invoice",
        "expected": {
            "issuer_name": "TechShop Berlin GmbH",
            "address_city": "Berlin",
            "address_country": "DE",
            "vat_id": "DE298456712",
            "tax_number": "30/123/45678",
            "receipt_number": "RE-2025-004521",
            "receipt_date": "2025-12-03",
            "receipt_type": "invoice",
            "amounts_gross": 100.00,
            "amounts_net": 84.03,
            "amounts_currency": "EUR",
            "tax_rates": [19],
            "payment_method": "card",
            "card_last_4": "4829",
        }
    }
}


def run_ocr(image_path: str) -> dict:
    """Run receipt_ocr.py and return parsed JSON."""
    result = subprocess.run(
        ["python3", "receipt_ocr.py", image_path],
        capture_output=True,
        text=True,
        timeout=120
    )
    if result.returncode != 0:
        raise RuntimeError(f"OCR failed: {result.stderr}")
    return json.loads(result.stdout)


def test_image(image_path: str, config: dict) -> tuple[int, int, list]:
    """Test a single image. Returns (passed, failed, errors)."""
    expected = config["expected"]
    passed = 0
    failed = 0
    errors = []

    print(f"\n{'='*60}")
    print(f"Testing: {image_path}")
    print(f"Description: {config['description']}")
    print(f"{'='*60}")

    try:
        result = run_ocr(image_path)
    except Exception as e:
        print(f"FATAL: {e}")
        return 0, 1, [str(e)]

    # Test each expected field
    checks = [
        ("issuer.name", result.get("issuer", {}).get("name"), expected.get("issuer_name")),
        ("issuer.address.city", result.get("issuer", {}).get("address", {}).get("city"), expected.get("address_city")),
        ("issuer.address.country", result.get("issuer", {}).get("address", {}).get("country"), expected.get("address_country")),
        ("issuer.vat_id", result.get("issuer", {}).get("vat_id"), expected.get("vat_id")),
        ("receipt.number", result.get("receipt", {}).get("number"), expected.get("receipt_number")),
        ("receipt.date", result.get("receipt", {}).get("date"), expected.get("receipt_date")),
        ("receipt.type", result.get("receipt", {}).get("type"), expected.get("receipt_type")),
        ("amounts.gross", result.get("amounts", {}).get("gross"), expected.get("amounts_gross")),
        ("amounts.net", result.get("amounts", {}).get("net"), expected.get("amounts_net")),
        ("amounts.currency", result.get("amounts", {}).get("currency"), expected.get("amounts_currency")),
        ("payment.method", result.get("payment", {}).get("method"), expected.get("payment_method")),
        ("payment.card_last_4", result.get("payment", {}).get("card_last_4"), expected.get("card_last_4")),
    ]

    # Optional tax_number check
    if expected.get("tax_number"):
        checks.append(("issuer.tax_number", result.get("issuer", {}).get("tax_number"), expected.get("tax_number")))

    for field, actual, exp in checks:
        if exp is None:
            continue

        # List of acceptable values
        if isinstance(exp, list):
            match = actual in exp
        # Flexible matching for strings (contains check for names)
        elif isinstance(exp, str) and isinstance(actual, str):
            match = exp.lower() in actual.lower() or actual.lower() in exp.lower()
        # Numeric tolerance
        elif isinstance(exp, (int, float)) and isinstance(actual, (int, float)):
            match = abs(actual - exp) < 0.02
        else:
            match = actual == exp

        status = "✓" if match else "✗"
        if match:
            passed += 1
            print(f"  {status} {field}: {actual}")
        else:
            failed += 1
            errors.append(f"{field}: expected '{exp}', got '{actual}'")
            print(f"  {status} {field}: expected '{exp}', got '{actual}'")

    # Check tax rates
    actual_rates = [t.get("rate") for t in result.get("taxes", [])]
    expected_rates = expected.get("tax_rates", [])
    rates_match = all(any(abs(ar - er) < 1 for ar in actual_rates) for er in expected_rates)
    if rates_match:
        passed += 1
        print(f"  ✓ taxes.rates: {actual_rates}")
    else:
        failed += 1
        errors.append(f"taxes.rates: expected {expected_rates}, got {actual_rates}")
        print(f"  ✗ taxes.rates: expected {expected_rates}, got {actual_rates}")

    return passed, failed, errors


def main():
    total_passed = 0
    total_failed = 0
    all_errors = []

    print("\n" + "="*60)
    print("Receipt OCR Integration Tests")
    print("="*60)

    for image_path, config in EXAMPLES.items():
        passed, failed, errors = test_image(image_path, config)
        total_passed += passed
        total_failed += failed
        all_errors.extend(errors)

    print("\n" + "="*60)
    print(f"RESULTS: {total_passed} passed, {total_failed} failed")
    print("="*60)

    if total_failed > 0:
        print("\nFailed checks:")
        for err in all_errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
