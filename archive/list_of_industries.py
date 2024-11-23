import pandas as pd

df = pd.read_csv("filtered_active_companies_cleaned.csv")

unique_values = df["mainBusinessLine.descriptions"].unique()

unique_values_list = unique_values.tolist()

print(unique_values_list)

with open("list_of_industries.txt", "w", encoding="utf-8") as file:
    file.write("\n".join(unique_values_list))