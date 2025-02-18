import pandas as pd

# Read the CSV file
file_name = "cotracker_pts.csv"
data = pd.read_csv(file_name)

data['f1_upper_y'] += 1
data['f2_upper_y'] += 1
data['f1_lower_y'] += 1
data['f2_lower_y'] += 1

# Save the modified data back to the same file
data.to_csv(file_name, index=False)

print(f"Updated the file '{file_name}' successfully.")
