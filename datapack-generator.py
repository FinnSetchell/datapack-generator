import os
import shutil
import requests
import zipfile
import io
import json
from tqdm import tqdm

# Configuration
GITHUB_REPO_URL = 'https://github.com/FinnSetchell/MoogsEndStructures'
BRANCH_NAME = '1.21.4'
DOWNLOADED_REPO_PATH = 'downloaded_repo'
DATAPACK_OUTPUT_PATH = 'datapack_output'
FOLDER_PATH = 'common/src/main/resources'
ICON_PATH = 'resources/assets/mes/icon.png'
PACK_MCMETA_PATH = 'resources/pack.mcmeta'
DATA_FOLDER_PATH = 'resources/data'
REPLACEMENTS_FILE = 'replacements.json'

def clear_folder(path):
    if os.path.exists(path):
        for root, dirs, files in os.walk(path):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                shutil.rmtree(os.path.join(root, dir))

def download_data_folder(repo_url, branch_name, local_path, folder_path):
    clear_folder(local_path)

    api_url = f"{repo_url}/archive/refs/heads/{branch_name}.zip"
    response = requests.get(api_url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 Kilobyte
    t = tqdm(total=total_size, unit='iB', unit_scale=True)
    
    if response.status_code == 200:
        with io.BytesIO() as file_buffer:
            for data in response.iter_content(block_size):
                t.update(len(data))
                file_buffer.write(data)
            t.close()
            with zipfile.ZipFile(file_buffer) as zip_ref:
                zip_ref.extractall(local_path)
        extracted_folder_name = os.path.join(local_path, f"{repo_url.split('/')[-1]}-{branch_name}")
        data_folder = os.path.join(extracted_folder_name, folder_path)
        if os.path.exists(data_folder):
            shutil.move(data_folder, local_path)
            shutil.rmtree(extracted_folder_name)
        else:
            print(f"No data folder found in {data_folder}")
    else:
        t.close()
        print(f"Failed to download data folder: {response.status_code}")

def load_replacements(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading replacements file: {e}")
        return {}

def apply_replacements(content, replacements):
    for placeholder, new_value in replacements.items():
        content = content.replace(placeholder, new_value)
    return content

def apply_replacements_to_file(file_path, replacements):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        if file_path.endswith('.json'):
            data = json.loads(content)
            data = apply_replacements(json.dumps(data), replacements)
            content = json.dumps(json.loads(data), indent=4)
        else:
            content = apply_replacements(content, replacements)
        
        with open(file_path, 'w') as file:
            file.write(content)
        print(f"Applied replacements to {file_path}")
    except Exception as e:
        print(f"Error applying replacements to {file_path}: {e}")
        print(f"Replacements: {replacements}")

def apply_replacements(replacements):
    for path, path_replacements in replacements.items():
        if path == "global":
            continue
        full_path = os.path.join(DOWNLOADED_REPO_PATH, path)
        if os.path.isfile(full_path):
            apply_replacements_to_file(full_path, path_replacements)
        elif os.path.isdir(full_path):
            for root, dirs, files in os.walk(full_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    apply_replacements_to_file(file_path, path_replacements)
        else:
            print(f"Path not found: {full_path}")

def create_datapack_structure(output_path, repo_name, icon_path, pack_mcmeta_path, data_folder_path):
    repo_folder = os.path.join(output_path, repo_name)
    
    clear_folder(repo_folder)

    if not os.path.exists(repo_folder):
        os.makedirs(repo_folder)
    
    # Copy pack.mcmeta
    pack_mcmeta_dest = os.path.join(repo_folder, 'pack.mcmeta')
    shutil.copyfile(pack_mcmeta_path, pack_mcmeta_dest)
    
    # Copy icon.png
    shutil.copyfile(icon_path, os.path.join(repo_folder, 'icon.png'))

    # Copy data folder
    shutil.copytree(data_folder_path, os.path.join(repo_folder, 'data'))

def main():
    replacements = load_replacements(REPLACEMENTS_FILE)
    print(json.dumps(replacements, indent=4))
    repo_name = os.path.basename(GITHUB_REPO_URL)
    
    download_data_folder(GITHUB_REPO_URL, BRANCH_NAME, DOWNLOADED_REPO_PATH, FOLDER_PATH)

    create_datapack_structure(DATAPACK_OUTPUT_PATH, repo_name, os.path.join(DOWNLOADED_REPO_PATH, ICON_PATH), os.path.join(DOWNLOADED_REPO_PATH, PACK_MCMETA_PATH), os.path.join(DOWNLOADED_REPO_PATH, DATA_FOLDER_PATH))
    
    apply_replacements(replacements)
    print(f"Datapack created at {DATAPACK_OUTPUT_PATH}")

if __name__ == '__main__':
    main()