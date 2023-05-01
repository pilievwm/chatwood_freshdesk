import csv
import os
from collections import defaultdict

def normalize_title(title):
    return title.rstrip('0123456789 ()')

data_dir = 'data'
input_file = os.path.join(data_dir, 'all_count.csv')
output_file = os.path.join(data_dir, 'output.txt')

merged_data = defaultdict(str)

with open(input_file, "r") as csv_file:
    csv_reader = csv.DictReader(csv_file)

    for row in csv_reader:
        title = row["title"]
        description = row["description"]

        normalized_title = normalize_title(title)

        if not merged_data[normalized_title]:
            merged_data[normalized_title] = description
        else:
            merged_data[normalized_title] += " " + description

with open(output_file, "w") as txt_file:
    for title, description in merged_data.items():
        # txt_file.write(f"Title: {title}\n")
        txt_file.write(f"{description}\n")
        txt_file.write("\n")
