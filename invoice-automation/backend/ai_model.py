from config import Config  # pyre-ignore[21]

try:
    from sklearn.pipeline import Pipeline  # pyre-ignore[21]
    from sklearn.feature_extraction.text import TfidfVectorizer  # pyre-ignore[21]
    from sklearn.naive_bayes import MultinomialNB  # pyre-ignore[21]
    HAS_AI_DEPS = True
except ImportError:
    HAS_AI_DEPS = False

class InvoiceCategorizer:
    """AI service to classify invoices into expense categories."""
    CATEGORIES = ["Transport", "Food", "Supplies", "Software"]
    TRAINING_DATA = [
        ("uber ride taxi taxi cab fare trip lyft", "Transport"),
        ("delta airline flight ticket boarding pass", "Transport"),
        ("gas station petrol fuel shell bp", "Transport"),
        ("restaurant dinner lunch breakfast meal cafe", "Food"),
        ("grocery market whole foods food drinks", "Food"),
        ("coffee starbucks espresso latte drink", "Food"),
        ("office supplies paper pens folders staples", "Supplies"),
        ("amazon order purchase product equipment", "Supplies"),
        ("software license subscription saas cloud", "Software"),
        ("aws azure google cloud hosting dev", "Software")
    ]

    def __init__(self):
        self.has_deps = HAS_AI_DEPS
        self.model = None
        self._initialize()

    def _initialize(self):
        if not self.has_deps: return
        model = Pipeline([('tfidf', TfidfVectorizer(stop_words='english')), ('clf', MultinomialNB(alpha=0.1))])
        model.fit([d[0] for d in self.TRAINING_DATA], [d[1] for d in self.TRAINING_DATA])  # type: ignore
        self.model = model

    def predict_with_confidence(self, text):
        if not text or not text.strip(): return "Supplies", {cat: 0.0 for cat in self.CATEGORIES}
        if not self.has_deps or self.model is None: return self._fallback(text)
        prediction = self.model.predict([text.lower()])[0]  # type: ignore
        probs = self.model.predict_proba([text.lower()])[0]  # type: ignore
        confidence = {str(cls): float(f"{prob:.4f}") for cls, prob in zip(getattr(self.model, 'classes_', []), probs)}  # type: ignore
        return str(prediction), confidence

    def _fallback(self, text):
        text_lower = text.lower()
        for keywords, category in self.TRAINING_DATA:
            if any(word in text_lower for word in keywords.split()):
                return category, {cat: (1.0 if cat == category else 0.0) for cat in self.CATEGORIES}
        return "Supplies", {cat: 0.0 for cat in self.CATEGORIES}

categorizer = InvoiceCategorizer()
