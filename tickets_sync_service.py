import os
import json
import csv
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
from dotenv import load_dotenv


load_dotenv()
# Build creds_info from individual env vars (for TOML or .env with flat keys)
creds_info = {
    "type": os.environ.get("type"),
    "project_id": os.environ.get("project_id"),
    "private_key_id": os.environ.get("private_key_id"),
    "private_key": os.environ.get("private_key"),
    "client_email": os.environ.get("client_email"),
    "client_id": os.environ.get("client_id"),
    "auth_uri": os.environ.get("auth_uri"),
    "token_uri": os.environ.get("token_uri"),
    "auth_provider_x509_cert_url": os.environ.get("auth_provider_x509_cert_url"),
    "client_x509_cert_url": os.environ.get("client_x509_cert_url"),
    "universe_domain": os.environ.get("universe_domain"),
}
# Load variables from environment (or st.secrets, if in Streamlit Cloud)
REMOTE_CSV_ID = os.environ.get("REMOTE_CSV_ID")
LOCAL_CSV_ID = os.environ.get("LOCAL_CSV_ID", "tickets.csv")  # fallback default
SCOPES = ["https://www.googleapis.com/auth/drive"]

credentials = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)

# Setup Drive client
service = build("drive", "v3", credentials=credentials)

def read_csv_rows(path):
    if not os.path.exists(path):
        return [], []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        rows = list(reader)
        if not rows:
            return [], []
        return rows[0], rows[1:]

def write_csv_rows(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(header)
        writer.writerows(rows)

def download_remote_csv(temp_path, remote_file_id=REMOTE_CSV_ID):
    file_data = service.files().get_media(fileId=remote_file_id).execute()
    with open(temp_path, "wb") as f:
        f.write(file_data)

def safe_merge_csv(local_path=LOCAL_CSV_ID, remote_file_id=REMOTE_CSV_ID):
    # Download remote to temp
    temp_remote = local_path + ".remote"
    try:
        download_remote_csv(temp_remote, remote_file_id)
    except Exception:
        temp_remote = None  # Remote may not exist yet

    # Read both CSVs
    local_header, local_rows = read_csv_rows(local_path)
    remote_header, remote_rows = read_csv_rows(temp_remote) if temp_remote else ([], [])

    # Use local header if present, else remote
    header = local_header or remote_header
    if not header:
        return header, []  # No data to merge

    # Find the index of the hashed_token column
    try:
        token_idx = header.index("hashed_token")
    except ValueError:
        raise ValueError("CSV must have a 'hashed_token' column in the header.")

    # Build dicts keyed by hashed_token
    merged_dict = {}
    for row in remote_rows:
        if len(row) > token_idx:
            merged_dict[row[token_idx]] = row
    for row in local_rows:
        if len(row) > token_idx:
            merged_dict[row[token_idx]] = row  # Local takes precedence

    merged_rows = [merged_dict[key] for key in sorted(merged_dict.keys())]

    # Clean up temp file
    if temp_remote and os.path.exists(temp_remote):
        os.remove(temp_remote)

    return header, merged_rows

def upload_csv(local_path=LOCAL_CSV_ID, remote_file_id=REMOTE_CSV_ID):
    """Safely merge and upload local and remote CSVs to Google Drive."""
    header, merged_rows = safe_merge_csv(local_path, remote_file_id)
    if not header:
        raise ValueError("No header found in either local or remote CSV.")
    write_csv_rows(local_path, header, merged_rows)
    media = MediaFileUpload(local_path, mimetype="text/csv")
    service.files().update(fileId=remote_file_id, media_body=media).execute()

def download_csv(local_path=LOCAL_CSV_ID, remote_file_id=REMOTE_CSV_ID):
    """Safely merge and save the merged CSV locally."""
    header, merged_rows = safe_merge_csv(local_path, remote_file_id)
    if not header:
        raise ValueError("No header found in either local or remote CSV.")
    write_csv_rows(local_path, header, merged_rows)