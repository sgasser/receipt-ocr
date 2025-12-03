# Receipt OCR

Minimal receipt/invoice OCR using Google Gemini Vision API. ~100 lines of Python.

> Vibe coded with [Claude Code](https://claude.ai/code)

## Features

- Extracts structured JSON from receipt images
- Supports JPG, PNG, PDF
- Works with any language/country
- ~$0.001 per image (free tier: 1,500/day)

## Setup

```bash
pip install requests

# Get API key at https://aistudio.google.com/apikey
echo "GEMINI_API_KEY=your-key" > .env
```

## Usage

```bash
python3 receipt_ocr.py invoice.jpg
python3 receipt_ocr.py receipt.png > result.json
```

## Output

```json
{
  "receipt": {
    "date": "2025-12-03",
    "number": "RE-2025-004521",
    "type": "invoice"
  },
  "amounts": {
    "gross": 100.00,
    "net": 84.03,
    "currency": "EUR"
  },
  "taxes": [
    {"rate": 19, "amount": 15.97}
  ],
  "issuer": {
    "name": "TechShop Berlin GmbH",
    "address": {
      "street": "Friedrichstraße 123",
      "postal_code": "10117",
      "city": "Berlin",
      "country": "DE"
    },
    "vat_id": "DE298456712",
    "tax_number": "30/123/45678"
  },
  "payment": {
    "method": "card",
    "card_last_4": "4829"
  },
  "raw_text": "..."
}
```

## Extracted Fields

| Field | Description |
|-------|-------------|
| `receipt.date` | ISO 8601 date (YYYY-MM-DD) |
| `receipt.number` | Invoice/receipt number |
| `receipt.type` | invoice, receipt, cash_register, credit_note |
| `amounts.gross` | Total amount incl. tax |
| `amounts.net` | Amount excl. tax |
| `amounts.currency` | ISO 4217 (EUR, USD, CHF) |
| `taxes[].rate` | Tax percentage (19, not 0.19) |
| `taxes[].amount` | Tax amount |
| `issuer.name` | Company name |
| `issuer.address` | Street, postal code, city, country |
| `issuer.vat_id` | VAT ID (DE123456789) |
| `issuer.tax_number` | Local tax number |
| `payment.method` | card, cash, transfer, paypal |
| `payment.card_last_4` | Last 4 digits of card |

## Testing

```bash
python3 test_receipt_ocr.py
```

Example images in `examples/` are AI-generated with Google Gemini.

## License

MIT
