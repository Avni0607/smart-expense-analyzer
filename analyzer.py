import os
from dotenv import load_dotenv
from supabase import create_client, Client
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(URL, KEY)

# 1. Training Data: Examples to teach our AI model patterns
training_descriptions = [
    "gulab jamun","chicken roll", "coffee at cafe", "lunch", "pizza",
    "auto to college", "metro ticket", "uber cab ride", "bus pass", "petrol refill",
    "mobile recharge", "wifi broadband bill", "electricity bill", "house rent", "water bill"
]
training_labels = [
    "Food", "Food", "Food", "Food", "Food",
    "Travel", "Travel", "Travel", "Travel", "Travel",
    "Bills & Utilities", "Bills & Utilities", "Bills & Utilities", "Bills & Utilities", "Bills & Utilities"
]

# 2. Build and Train the NLP Pipeline
model = make_pipeline(TfidfVectorizer(), MultinomialNB())
model.fit(training_descriptions, training_labels)

# 3. Fetch 'Pending' rows from Supabase
response = supabase.table("expenses").select("*").eq("category", "Pending").execute()
pending_expenses = response.data

# 4. Predict categories using our trained ML model!
for expense in pending_expenses:
    description_text = expense["description"]
    expense_id = expense["id"]
    
    # Ask the AI for its confidence score (between 0 and 1)
    probabilities = model.predict_proba([description_text])[0]
    highest_confidence = max(probabilities)
    
    # Only trust the AI if it is at least 45% confident; otherwise use "Other"
    if highest_confidence >= 0.45:
        predicted_category = model.predict([description_text])[0]
    else:
        predicted_category = "Other"
        
    supabase.table("expenses").update({"category": predicted_category}).eq("id", expense_id).execute()
    print(f"🤖 AI Predicted: '{description_text}' -> '{predicted_category}' (Confidence: {highest_confidence:.0%})")


# --- Terminal Spending Summary ---
print("\n--- 📊 EXPENSE SUMMARY BY CATEGORY ---")
all_data = supabase.table("expenses").select("*").execute().data
category_totals = {}
grand_total = 0

for item in all_data:
    cat = item["category"]
    amt = float(item["amount"])
    category_totals[cat] = category_totals.get(cat, 0) + amt
    grand_total += amt

for category, total in category_totals.items():
    print(f"{category}: ₹{total:.2f}")

print("--------------------------------------")
print(f"💰 Total Spent: ₹{grand_total:.2f}\n")
