import os
import shutil
import requests
import zipfile
import io
import json
from tqdm import tqdm
import re

# Configuration
GITHUB_REPO_URL = input("Enter the GitHub repository URL: ")
BRANCH_NAME = input("Enter the branch name: ")
MODID = input("Enter the mod ID: ")
DOWNLOADED_REPO_PATH = 'downloaded_repo'
DATAPACK_OUTPUT_PATH = 'datapack_output'
FOLDER_PATH = 'common/src/main/resources'
ICON_PATH = f'resources/assets/{MODID}/icon.png'
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
    print()
    print(f"Downloading data folder from {repo_url}...")
    clear_folder(local_path)

    api_url = f"{repo_url}/archive/refs/heads/{branch_name}.zip"
    response = requests.get(api_url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 Kilobyte
    t = tqdm(total=total_size, unit='iB', unit_scale=True, colour='green')
    
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

def apply_replacements(replacements, base_path):
    for path, changes in replacements.items():
        full_path = os.path.join(base_path, path)
        if os.path.isdir(full_path):
            for root, _, files in os.walk(full_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        content = f.read()
                    for old_text, new_text in changes.items():
                        if '->' in old_text:
                            pattern = rf'^\s*{re.escape(old_text.replace("->", ""))}.*$'
                            content = re.sub(pattern, new_text, content, flags=re.MULTILINE)
                        else:
                            content = content.replace(old_text, new_text)
                    with open(file_path, 'w') as f:
                        f.write(content)
        elif os.path.isfile(full_path):
            with open(full_path, 'r') as f:
                content = f.read()
            for old_text, new_text in changes.items():
                if '->' in old_text:
                    pattern = rf'^\s*{re.escape(old_text.replace("->", ""))}.*$'
                    content = re.sub(pattern, new_text, content, flags=re.MULTILINE)
                else:
                    content = content.replace(old_text, new_text)
            with open(full_path, 'w') as f:
                f.write(content)

def remove_trailing_commas(json_content):
    # Remove trailing commas before closing braces and brackets
    json_content = re.sub(r',\s*([}\]])', r'\1', json_content)
    return json_content

def clean_json_files(base_path):
    print()
    print("Cleaning JSON files...")
    json_files = []
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    
    with tqdm(total=len(json_files), unit='file', colour='red') as pbar:
        for file_path in json_files:
            with open(file_path, 'r') as f:
                content = f.read()
            cleaned_content = remove_trailing_commas(content)
            cleaned_content = '\n'.join([line for line in cleaned_content.splitlines() if line.strip() != ''])
            with open(file_path, 'w') as f:
                f.write(cleaned_content)
            pbar.update(1)

def create_datapack_structure(output_path, repo_name, branch_name, icon_path, pack_mcmeta_path, data_folder_path, replacements):
    print()
    print(f"Creating datapack structure for {repo_name} on branch {branch_name}...")
    repo_folder = os.path.join(output_path, f"{repo_name}-{branch_name}")
    
    clear_folder(repo_folder)

    if not os.path.exists(repo_folder):
        os.makedirs(repo_folder)
    
    # Copy pack.mcmeta
    pack_mcmeta_dest = os.path.join(repo_folder, 'pack.mcmeta')
    shutil.copyfile(pack_mcmeta_path, pack_mcmeta_dest)
    
    # Copy icon.png
    shutil.copyfile(icon_path, os.path.join(repo_folder, 'icon.png'))
    # rename icon.png to pack.png
    os.rename(os.path.join(repo_folder, 'icon.png'), os.path.join(repo_folder, 'pack.png'))

    # Copy data folder
    data_folder_dest = os.path.join(repo_folder, 'data')
    os.makedirs(data_folder_dest)
    total_files = sum([len(files) for _, _, files in os.walk(data_folder_path)])
    with tqdm(total=total_files, unit='file', colour='blue') as pbar:
        for root, _, files in os.walk(data_folder_path):
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(data_folder_dest, os.path.relpath(src_file, data_folder_path))
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                shutil.copyfile(src_file, dest_file)
                pbar.update(1)

    # Apply replacements
    apply_replacements(replacements, repo_folder)

    # Clean JSON files
    clean_json_files(repo_folder)

def zip_datapack(output_path, repo_name, branch_name):
    repo_folder = os.path.join(output_path, f"{repo_name}-{branch_name}")
    zip_filename = os.path.join(repo_folder, f"{repo_name}-{branch_name}.zip")
    shutil.make_archive(zip_filename.replace('.zip', ''), 'zip', repo_folder)
    print(f"Zipped datapack created at {zip_filename}")

def main():
    repo_name = os.path.basename(GITHUB_REPO_URL)
    replacements_file = f"{repo_name}-replacements.json"
    replacements = load_replacements(replacements_file)
    
    download_data_folder(GITHUB_REPO_URL, BRANCH_NAME, DOWNLOADED_REPO_PATH, FOLDER_PATH)

    create_datapack_structure(DATAPACK_OUTPUT_PATH, repo_name, BRANCH_NAME, os.path.join(DOWNLOADED_REPO_PATH, ICON_PATH), os.path.join(DOWNLOADED_REPO_PATH, PACK_MCMETA_PATH), os.path.join(DOWNLOADED_REPO_PATH, DATA_FOLDER_PATH), replacements)
    
    zip_datapack(DATAPACK_OUTPUT_PATH, repo_name, BRANCH_NAME)
    
    print(f"Datapack created in {DATAPACK_OUTPUT_PATH} folder")

if __name__ == '__main__':
    main()