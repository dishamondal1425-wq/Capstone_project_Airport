import pandas as pd
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score


# ==========================================
# LOAD DATASET
# ==========================================

data = pd.read_csv(
    "airport_announcements_dataset.csv"
)

print(data.head())


# ==========================================
# INPUT AND OUTPUT
# ==========================================

X = data["text"]
y = data["category"]


# ==========================================
# TEXT VECTORIZATION
# ==========================================

vectorizer = TfidfVectorizer()

X_vectorized = vectorizer.fit_transform(X)


# ==========================================
# TRAIN TEST SPLIT
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X_vectorized,
    y,
    test_size=0.2,
    random_state=42
)


# ==========================================
# MODEL TRAINING
# ==========================================

model = MultinomialNB()

model.fit(X_train, y_train)


# ==========================================
# MODEL TESTING
# ==========================================

predictions = model.predict(X_test)

accuracy = accuracy_score(
    y_test,
    predictions
)

print(
    f"Model Accuracy: {accuracy * 100:.2f}%"
)


# ==========================================
# SAVE MODEL
# ==========================================

joblib.dump(
    model,
    "airport_model.pkl"
)

joblib.dump(
    vectorizer,
    "vectorizer.pkl"
)

print(
    "Model and Vectorizer Saved Successfully!"
)