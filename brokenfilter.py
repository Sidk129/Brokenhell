import pandas as pd

# Read the file
file_path = '$PATH to targeted file'

with open(file_path, 'r') as file:
    lines = file.readlines()

# Initialize lists to store the data
links = []
statuses = []

# Process each line to extract the link and status code
for line in lines:
    if ' - HTTP status code: ' in line:
        parts = line.split(' - HTTP status code: ')
        link = parts[0].replace('Broken link found: ', '').strip()
        status_code = int(parts[1].strip())
        if status_code not in [0, 999]:  # Filter out status codes 0 and 999
            links.append(link)
            statuses.append(status_code)

# Create a DataFrame
df = pd.DataFrame({'Link': links, 'HTTP Status Code': statuses})

# Create a section column based on the URL domain
df['Page URL'] = df['Link'].apply(lambda x: x.split('/')[2])

# Add a numbering column
df['No.'] = range(1, len(df) + 1)

# Reorder the columns
df = df[['No.', 'Page URL', 'Link', 'HTTP Status Code']]

# Save the DataFrame to a CSV file
output_file_path = '$PATH for Output/name of file.csv'
df.to_csv(output_file_path, index=False)

print(f"Filtered data saved to {output_file_path}")
