import os
import shutil
from git import Repo

# Configuration
GITHUB_REPO_URL = 'https://github.com/FinnSetchell/MoogsEndStructures.git'
BRANCH_NAME = '1.21.4'
LOCAL_REPO_PATH = 'local_repo'
DATAPACK_OUTPUT_PATH = 'datapack_output'
DATA_FOLDER_PATH = 'common/src/main/resources/data'

def clone_repo(repo_url, branch_name, local_path):
    if os.path.exists(local_path):
        shutil.rmtree(local_path)
    Repo.clone_from(repo_url, local_path, branch=branch_name)

def process_data_folders(repo_path, output_path, data_folder_path):
    data_folder = os.path.join(repo_path, data_folder_path)
    if not os.path.exists(data_folder):
        print(f"No data folder found in {data_folder}")
        return

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    for root, dirs, files in os.walk(data_folder):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, data_folder)
            output_file_path = os.path.join(output_path, relative_path)

            # Create directories if they don't exist
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

            # Copy and modify files as needed
            shutil.copyfile(file_path, output_file_path)
            modify_file(output_file_path)

def modify_file(file_path):
    # Implement any modifications needed for the datapack version
    with open(file_path, 'r') as file:
        content = file.read()

    # Example modification: replace a placeholder text
    content = content.replace('PLACEHOLDER', 'new_value')

    with open(file_path, 'w') as file:
        file.write(content)

def main():
    clone_repo(GITHUB_REPO_URL, BRANCH_NAME, LOCAL_REPO_PATH)
    process_data_folders(LOCAL_REPO_PATH, DATAPACK_OUTPUT_PATH, DATA_FOLDER_PATH)
    print(f"Datapack created at {DATAPACK_OUTPUT_PATH}")

if __name__ == '__main__':
    main()