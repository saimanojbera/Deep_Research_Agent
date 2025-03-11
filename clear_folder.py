import os
import shutil
import time

def clear_folder(folder_path: str):
    """Deletes all files in the specified folder but keeps the folder itself."""
    try:
        if not os.path.exists(folder_path):
            print(f"Folder '{folder_path}' does not exist.")
            return

        # Close all file handles before deletion
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)

            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)  # Delete file
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # Delete subdirectory
            except PermissionError:
                print(f"⚠️ File {file_path} is in use. Retrying...")
                time.sleep(1)  # Wait and try again
                os.remove(file_path)

        print(f"✅ All files in '{folder_path}' have been removed.")

    except Exception as e:
        print(f"❌ Error clearing the folder: {e}")

# Example usage:
# clear_folder("C:/Users/YourName/Documents/target")
