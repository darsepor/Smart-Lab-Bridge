import pandas as pd
import json

# Read the JSON file
with open("archive/data_20241118.json", encoding="utf-8") as file:
    data = json.load(file)

# Create DataFrame
df = pd.json_normalize(data)

# Filter for active organizations
df_active = df[df["status"] == "2"]

# Create filtered copy with selected columns
df_filtered = df_active[["names", "website.url", "mainBusinessLine.descriptions"]].copy()

def extract_first_name(names):
    if isinstance(names, list) and len(names) > 0:
        return names[0].get('name', None)
    return None

def extract_english_description(descriptions):
    if isinstance(descriptions, list):
        for desc in descriptions:
            if desc.get("languageCode") == "3":
                return desc.get("description", None)
    return None

# Apply transformations
df_filtered["mainBusinessLine.descriptions"] = df_filtered["mainBusinessLine.descriptions"].apply(extract_english_description)
df_filtered["name"] = df_filtered["names"].apply(extract_first_name)
df_filtered = df_filtered.drop("names", axis=1)  # Remove the old names column

# Filter out rows with no websites or no English description
df_filtered = df_filtered[
    df_filtered["website.url"].notna() & 
    (df_filtered["website.url"].str.strip() != "") &
    df_filtered["mainBusinessLine.descriptions"].notna() &
    df_filtered["name"].notna()
]

# Remove duplicates
df_filtered = df_filtered.drop_duplicates(subset=["website.url", "mainBusinessLine.descriptions"])

# Save to CSV
df_filtered.to_csv("filtered_active_companies_cleaned.csv", index=False)