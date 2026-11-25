"""One-time local OAuth 2.0 helper to generate a Google Drive refresh token.

Run once locally with your OAuth Desktop client JSON (`client_secret.json`)
from Google Cloud Console:
    python scripts/auth_gdrive.py
"""

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def main() -> None:
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    print("\nAdd these to GitHub Actions Secrets:")
    print(f"GOOGLE_DRIVE_CLIENT_ID={creds.client_id}")
    print(f"GOOGLE_DRIVE_CLIENT_SECRET={creds.client_secret}")
    print(f"GOOGLE_DRIVE_REFRESH_TOKEN={creds.refresh_token}")


if __name__ == "__main__":
    main()
