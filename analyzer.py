import os
import time
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(URL, KEY)

# 1. Load external CSV dataset using Pandas
df = pd.read_csv("expenses_dataset.csv")
training_descriptions = df["description"]
training_labels = df["category"]

# 2. Train the NLP Model once at startup
model = make_pipeline(TfidfVectorizer(), MultinomialNB())
model.fit(training_descriptions, training_labels)

print(f"🚀 AI Expense Watcher is LIVE! Trained on {len(df)} examples across {df['category'].nunique()} categories.\n")


# 3. Continuous Background Loop
while True:
    try:
        # Check Supabase for 'Pending' rows
        response = supabase.table("expenses").select("*").eq("category", "Pending").execute()
        pending_expenses = response.data

        # Only run classification and summary if new items were found!
        if pending_expenses:
            for expense in pending_expenses:
                description_text = expense["description"]
                expense_id = expense["id"]

                probabilities = model.predict_proba([description_text])[0]
                highest_confidence = max(probabilities)

                if highest_confidence >= 0.30:
                    predicted_category = model.predict([description_text])[0]
                else:
                    predicted_category = "Other"

                supabase.table("expenses").update({"category": predicted_category}).eq("id", expense_id).execute()
                print(f"🤖 AI Predicted: '{description_text}' -> '{predicted_category}' (Confidence: {highest_confidence:.0%})")

            # Print updated spending summary whenever new expenses get processed
            print("\n--- 📊 UPDATED EXPENSE SUMMARY ---")
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
            print("----------------------------------")
            print(f"💰 Total Spent: ₹{grand_total:.2f}\n")

    except Exception as e:
        print(f"⚠️ Temporary connection hiccup: {e}")

    # Wait 5 seconds before checking again
    time.sleep(5)
