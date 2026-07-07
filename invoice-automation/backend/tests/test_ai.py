import pytest
from ai_model import categorizer

def test_categorizer_transport():
    text = "Uber ride from airport"
    cat, conf = categorizer.predict_with_confidence(text)
    assert cat == "Transport"
    assert conf["Transport"] > 0.25

def test_categorizer_software():
    text = "AWS monthly cloud hosting subscription"
    cat, conf = categorizer.predict_with_confidence(text)
    assert cat == "Software"
    assert conf["Software"] > 0.25

def test_categorizer_food():
    text = "Lunch at Starbucks coffee"
    cat, conf = categorizer.predict_with_confidence(text)
    assert cat == "Food"
    assert conf["Food"] > 0.25

def test_categorizer_empty():
    cat, conf = categorizer.predict_with_confidence("")
    assert cat == "Supplies"
