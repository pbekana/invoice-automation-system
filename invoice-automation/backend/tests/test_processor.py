import pytest
from invoice_processor import InvoiceProcessor

def test_extract_company_keywords():
    processor = InvoiceProcessor()
    text = "Uber Technologies Inc.\nSan Francisco, CA"
    assert processor._extract_company(text) == "Uber Technologies Inc."

def test_extract_company_capitalization():
    processor = InvoiceProcessor()
    text = "Acme Corp Solutions\n123 Main St"
    assert "Acme Corp Solutions" in processor._extract_company(text)

def test_extract_date_standard():
    processor = InvoiceProcessor()
    text = "Date: 2026-03-15"
    assert processor._extract_date(text) == "2026-03-15"

def test_extract_date_wordy():
    processor = InvoiceProcessor()
    text = "Invoice Date: March 10, 2026"
    assert processor._extract_date(text) == "2026-03-10"

def test_extract_total_keyword():
    processor = InvoiceProcessor()
    text = "Subtotal: 100.00\nTax: 10.00\nTotal: $110.00"
    assert processor._extract_total(text) == 110.00

def test_extract_total_amount_due():
    processor = InvoiceProcessor()
    text = "Amount Due: 45.20"
    assert processor._extract_total(text) == 45.20
