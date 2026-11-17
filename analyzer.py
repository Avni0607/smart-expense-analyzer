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

# 1. Load base CSV dataset using Pandas
base_df = pd.read_csv("expenses_dataset.csv")

# 2. Fetch already-categorized expenses from live Supabase history
live_response = supabase.table("expenses").select("description, category").neq("category", "Pending").neq("category", "Other").execute()
live_df = pd.DataFrame(live_response.data)

# 3. Combine CSV + Live History so the AI learns from your real usage
if not live_df.empty:
    full_df = pd.concat([base_df, live_df], ignore_index=True)
else:
    full_df = base_df

# 4. Train the NLP Model on the combined dataset
model = make_pipeline(TfidfVectorizer(), MultinomialNB())
model.fit(full_df["description"], full_df["category"])

print(f"🚀 AI Watcher LIVE! Trained on {len(full_df)} total examples ({len(live_df)} learned from your live history).\n")



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
