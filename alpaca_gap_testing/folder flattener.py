import os
import shutil

# Define the source folder containing subfolders
source_folder = os.path.join(os.getcwd(), "charts")
# Define the destination folder
destination_folder = os.path.join(os.getcwd(), "destination_folder")

# Ensure the destination folder exists
os.makedirs(destination_folder, exist_ok=True)

# Ensure the destination folder exists
os.makedirs(destination_folder, exist_ok=True)

# Iterate through the subfolders in the source folder
for subfolder_name in os.listdir(source_folder):
    subfolder_path = os.path.join(source_folder, subfolder_name)

    # Check if it is a directory
    if os.path.isdir(subfolder_path):
        
        # Iterate through the files in the subfolder
        for file_name in os.listdir(subfolder_path):
            file_path = os.path.join(subfolder_path, file_name)

            # Check if it is a file
            if os.path.isfile(file_path):

                # Create a new file name with the subfolder name and original file name as a prefix
                new_file_name = f"{subfolder_name}_{file_name}"
                new_file_path = os.path.join(destination_folder, new_file_name)

                # Move and rename the file
                shutil.move(file_path, new_file_path)

print("Files moved and renamed successfully!")
