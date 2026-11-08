import os
from dotenv import load_dotenv
from supabase import create_client, Client

# 1. Look right next door for the hidden .env file and read it
load_dotenv()

# 2. Grab the keys dynamically using os.getenv
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

# 3. Create the secure client connection
supabase: Client = create_client(URL, KEY)

# 4. Fetch only the rows where category is 'Pending'
response = supabase.table("expenses").select("*").eq("category", "Pending").execute()
pending_expenses = response.data

# 5. Simple list of keywords to identify food items
food_keywords = ["jamun", "papdi", "toffee", "sweet", "dinner", "burger", "roll", "cafe"]

# 6. Loop through each pending item and update it in the cloud!
for expense in pending_expenses:
    description_text = expense["description"].lower()
    expense_id = expense["id"]
    
    is_food = any(keyword in description_text for keyword in food_keywords)
    
    if is_food:
        new_category = "Food"
        supabase.table("expenses").update({"category": new_category}).eq("id", expense_id).execute()
        print(f"Updated: '{expense['description']}' is now categorized as {new_category}!")
