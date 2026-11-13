import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(URL, KEY)

# 1. Fetch only the rows where category is 'Pending'
response = supabase.table("expenses").select("*").eq("category", "Pending").execute()
pending_expenses = response.data

# 2. Define specialized keyword lists for different areas of life
food_keywords = ["jamun", "papdi", "toffee", "sweet", "dinner", "burger", "roll", "cafe", "food"]
travel_keywords = ["auto", "uber", "ola", "train", "bus", "metro", "petrol", "cab"]
bill_keywords = ["recharge", "wifi", "broadband", "electricity", "bill", "rent", "mobile"]

# 3. Loop through each pending item and route it correctly
for expense in pending_expenses:
    description_text = expense["description"].lower()
    expense_id = expense["id"]
    
    # Initialize the target category
    final_category = "Other"
    
    # Check for matches across our lists
    if any(keyword in description_text for keyword in food_keywords):
        final_category = "Food"
    elif any(keyword in description_text for keyword in travel_keywords):
        final_category = "Travel"
    elif any(keyword in description_text for keyword in bill_keywords):
        final_category = "Bills & Utilities"

    # 4. Tell Supabase to update this specific row with its real category
    supabase.table("expenses").update({"category": final_category}).eq("id", expense_id).execute()
    print(f"Successfully processed: '{expense['description']}' -> Categorized as '{final_category}'")

# --- NEW FEATURE: Terminal Spending Summary ---
print("\n--- 📊 EXPENSE SUMMARY BY CATEGORY ---")

# 1. Fetch ALL expenses from the table now that they are updated
all_data = supabase.table("expenses").select("*").execute().data

# 2. Use a dictionary to add up totals per category
category_totals = {}
grand_total = 0

for item in all_data:
    cat = item["category"]
    amt = float(item["amount"])
    
    # Add to category total (if category isn't in dict yet, start at 0)
    category_totals[cat] = category_totals.get(cat, 0) + amt
    grand_total += amt

# 3. Print each category's total neatly
for category, total in category_totals.items():
    print(f"{category}: ₹{total:.2f}")

print("--------------------------------------")
print(f"💰 Total Spent: ₹{grand_total:.2f}\n")
