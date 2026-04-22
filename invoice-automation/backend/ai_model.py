import os
import joblib # type: ignore
from sklearn.pipeline import Pipeline # type: ignore
from sklearn.feature_extraction.text import TfidfVectorizer # type: ignore
from sklearn.linear_model import LogisticRegression # type: ignore
from config import Config # type: ignore
from logger_config import logger

try:
    HAS_AI_DEPS = True
except ImportError:
    HAS_AI_DEPS = False

class InvoiceCategorizer:
    """AI service to classify invoices with persistence and improved accuracy."""
    CATEGORIES = ["Transport", "Food", "Supplies", "Software"]
    
    # Expanded Training Data (Synthetic)
    TRAINING_DATA = [
        # Transport
        ("uber ride taxi fare lyft trip airport shuttle", "Transport"),
        ("delta airlines flight ticket boarding pass airfare", "Transport"),
        ("shell gas station petrol fuel refueling bp oil", "Transport"),
        ("parking garage fee valet toll express lane", "Transport"),
        ("amtrak train ticket subway metro pass rail", "Transport"),
        ("hertz car rental vehicle lease avis enterprise", "Transport"),
        ("chevron gas filling station pump fuel diesel", "Transport"),
        ("united airlines check-in luggage baggage fee", "Transport"),
        ("bus fare city transit commuter pass", "Transport"),
        ("lime bird scooter rental bike share", "Transport"),
        
        # Food
        ("restaurant dinner lunch breakfast meal cafe bistro", "Food"),
        ("starbucks coffee espresso latte drink tea bakery", "Food"),
        ("grocery market whole foods smiths kroger food", "Food"),
        ("pizza hut dominos fast food burger king mcdonalds", "Food"),
        ("catering service banquet snacks appetizers", "Food"),
        ("doordash ubereats food delivery takeout", "Food"),
        ("walmart grocery milk eggs produce cheese", "Food"),
        ("boulangerie patisserie sandwich salad menu", "Food"),
        ("pub bar drinks alcohol brewery winery", "Food"),
        ("chipotle mexican grill taco burrito bowl", "Food"),

        # Supplies
        ("office supplies paper pens folders staples depot", "Supplies"),
        ("amazon order purchase product equipment hardware", "Supplies"),
        ("furniture chair desk lamp bookshelf rug", "Supplies"),
        ("printer ink toner cartridge cable adapter usb", "Supplies"),
        ("cleaning supplies janitorial soap towels", "Supplies"),
        ("shipping labels bubble wrap boxes tape fedex ups", "Supplies"),
        ("industrial tools machinery parts maintenance", "Supplies"),
        ("uniforms workwear safety gear boots gloves", "Supplies"),
        ("stationary envelopes stamps mail postcards", "Supplies"),
        ("whiteboard markers eraser pins board", "Supplies"),

        # Software
        ("software license subscription saas cloud monthly", "Software"),
        ("aws amazon web services hosting s3 ec2", "Software"),
        ("google cloud gcp platform computing credits", "Software"),
        ("microsoft azure hosting billing subscription", "Software"),
        ("github copilot pro repository hosting git", "Software"),
        ("slack technology messaging communication pro", "Software"),
        ("zoom video conferencing webinar meeting room", "Software"),
        ("datadog monitoring logging analytics dashboard", "Software"),
        ("adobe creative cloud photoshop illustrator", "Software"),
        ("heroku platform deployment app hosting", "Software"),
        ("shopify e-commerce store subscription app", "Software"),
        ("atlassian jira confluence tivoli bitbucket", "Software"),
        ("mongo atlas database hosting cluster", "Software"),
        ("cloudflare dns security workers", "Software"),
        ("peters software yearly renewal key activation", "Software")
    ]

    def __init__(self):
        self.has_deps = HAS_AI_DEPS
        self.model = None
        self._initialize()

    def _initialize(self):
        """Lazy logic: Load existing model or train a new one."""
        if not self.has_deps:
            logger.warning("AI dependencies missing. Falling back to keyword matching.")
            return

        if os.path.exists(Config.MODEL_PATH):
            try:
                self.model = joblib.load(Config.MODEL_PATH)
                logger.info(f"Loaded AI model from {Config.MODEL_PATH}")
            except Exception as e:
                logger.error(f"Failed to load model: {e}. Retraining...")
                self._train_and_save()
        else:
            logger.info("No model found. Training new model...")
            self._train_and_save()

    def _train_and_save(self):
        """Train LogisticRegression model and persist to disk."""
        try:
            texts = [d[0].lower() for d in self.TRAINING_DATA]
            labels = [d[1] for d in self.TRAINING_DATA]

            pipeline = Pipeline([
                ('tfidf', TfidfVectorizer(
                    stop_words='english', 
                    ngram_range=(1, 2),
                    min_df=1
                )),
                ('clf', LogisticRegression(C=1.0, multi_class='multinomial', solver='lbfgs'))
            ])

            pipeline.fit(texts, labels)
            self.model = pipeline
            
            joblib.dump(pipeline, Config.MODEL_PATH)
            logger.info(f"Model trained and saved to {Config.MODEL_PATH}")
        except Exception as e:
            logger.error(f"Training failed: {e}")

    def predict_with_confidence(self, text):
        """Predict category with probability scores."""
        if not text or not text.strip():
            return "Supplies", {cat: 0.0 for cat in self.CATEGORIES}
        
        if not self.has_deps or self.model is None:
            return self._fallback(text)
        
        try:
            cleaned_text = text.lower().strip()
            prediction = self.model.predict([cleaned_text])[0]
            probs = self.model.predict_proba([cleaned_text])[0]
            
            classes = self.model.classes_
            confidence = {str(cls): float(f"{prob:.4f}") for cls, prob in zip(classes, probs)}
            
            return str(prediction), confidence
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return self._fallback(text)

    def _fallback(self, text):
        """Basic keyword matcher if AI model is unavailable."""
        text_lower = text.lower()
        for keywords, category in self.TRAINING_DATA:
            if any(word in text_lower for word in keywords.split()):
                return category, {cat: (1.0 if cat == category else 0.0) for cat in self.CATEGORIES}
        return "Supplies", {cat: 0.0 for cat in self.CATEGORIES}

# Singleton instance
categorizer = InvoiceCategorizer()
