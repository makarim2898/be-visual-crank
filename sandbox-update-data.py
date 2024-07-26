import pandas as pd

# Sample data as a list of dictionaries
df = pd.read_csv('camera_parameters.csv')
# Convert data to a pandas DataFrame
df = pd.DataFrame(df)

# New data to update or add
new_data = {
    'id_camera': 12,
    'focus_value': 0,
    'zoom_level': 900,
}

new_df = pd.DataFrame([new_data])

# Check if id_camera exists
id_camera_exists = df['id_camera'] == new_data['id_camera']

if id_camera_exists.any():
    # Update data if id_camera is found
    df.loc[df['id_camera'] == new_data['id_camera'], ['focus_value', 'zoom_level']] = new_data['focus_value'], new_data['zoom_level']
    print('Data diperbarui!')  # More descriptive message
else:
    # Add new data if id_camera is not found
    df = pd.concat([df, new_df], ignore_index=True)
    print('Data baru ditambahkan!')  # More descriptive message

df.to_csv('camera_parameters.csv', index=False)
# Print the updated DataFrame
print(df)
