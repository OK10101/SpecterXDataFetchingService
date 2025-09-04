Adding here a Python code that changes a policy (by policy_id) for a specific file (by file_id)
#!/usr/bin/env python3
import os
import sys
import argparse
import json
import requests
import warnings
import urllib3
# Suppress only the specific InsecureRequestWarning for staging certs
warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)
# ===== Hardcoded credentials (as requested) =====
SPECTERX_API_KEY = "OcEWgYAKcn7jjN6jz7qMh2I6VZkYQ0Qo4UPnVt2R"
SPECTERX_USER_ID = "user_specterxstagingmsonmicrosoftcom_40bf5870"
# Default to staging API base (override with env var if needed)
SPECTERX_API_BASE = os.getenv("SPECTERX_API_BASE", "https://staging-api.specterx.com")
# Confirmed working endpoint:
# PUT {SPECTERX_API_BASE}/access/ext/files/{file_id}/policy
def set_file_policy(file_id: str, policy_id: str, timeout: int = 60) -> dict:
    url = f"{SPECTERX_API_BASE}/access/ext/files/{file_id}/policy"
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json; charset=UTF-8",
        "origin": "https://staging-app.specterx.com",
        "referer": "https://staging-app.specterx.com/",
        "user-agent": "SpecterX-PolicySetter/2.0",
        "X-API-Key": SPECTERX_API_KEY,
        "SpecterxUserId": SPECTERX_USER_ID,
    }
    payload = {"policy_id": policy_id}
    resp = requests.put(url, headers=headers, json=payload, verify=False, timeout=timeout)
    # Raise for non-2xx to surface errors clearly
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        raise SystemExit(
            f":x: Failed to set policy (HTTP {resp.status_code}).\nURL: {url}\nBody: {resp.text}"
        ) from e
    # Some routes may return empty body on success
    try:
        return resp.json()
    except ValueError:
        return {"raw": resp.text}
def main():
    parser = argparse.ArgumentParser(description="Set a SpecterX policy on a file.")
    parser.add_argument("-file_id", required=True, help="SpecterX file_id to update")
    parser.add_argument("-policy_id", required=True, help="Policy ID to assign")
    parser.add_argument("--timeout", type=int, default=60, help="HTTP timeout (s), default 60")
    args = parser.parse_args()
    if not SPECTERX_API_KEY or not SPECTERX_USER_ID:
        print(":x: Missing hardcoded credentials.", file=sys.stderr)
        sys.exit(2)
    print(f"→ API Base: {SPECTERX_API_BASE}")
    print(f"→ File ID : {args.file_id}")
    print(f"→ Policy ID: {args.policy_id}")
    result = set_file_policy(args.file_id, args.policy_id, timeout=args.timeout)
    print(":white_check_mark: Policy set successfully.")
    print(json.dumps(result, indent=2, ensure_ascii=False))
if __name__ == "__main__":
    main()
please make sure that the file is owned by the user_id that is in the code.
for the file sharing, here is another sample code:
#!/usr/bin/env python3
import os
import sys
import argparse
import json
import requests
import warnings
import urllib3
# Suppress only the specific InsecureRequestWarning for staging certs
warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)
# ===== Hardcoded credentials (as requested) =====
SPECTERX_API_KEY = "OcEWgYAKcn7jjN6jz7qMh2I6VZkYQ0Qo4UPnVt2R"
SPECTERX_USER_ID = "user_specterxstagingmsonmicrosoftcom_40bf5870"
# Default to staging API base (override with env var if needed)
SPECTERX_API_BASE = os.getenv("SPECTERX_API_BASE", "https://staging-api.specterx.com")
# Confirmed staging style uses the "ext" namespace:
# POST {SPECTERX_API_BASE}/access/ext/share
SHARE_PATH = "/access/ext/share"
def build_headers() -> dict:
    return {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json; charset=UTF-8",
        "origin": "https://staging-app.specterx.com",
        "referer": "https://staging-app.specterx.com/",
        "user-agent": "SpecterX-Share/1.0",
        "X-API-Key": SPECTERX_API_KEY,
        "SpecterxUserId": SPECTERX_USER_ID,
    }
def build_payload(
    file_id: str,
    recipient: str,
    policy_id: str | None,
    notify: bool,
    protect_message: bool,
    message_id: str | None,
    read_only: bool,
    actions: list[str] | None,
    phone: str | None,
    prefix: str | None,
) -> dict:
    files_entry = {"file_id": file_id}
    if policy_id:
        files_entry["policy_id"] = policy_id
    user_entry = {
        "readOnly": read_only,
        "actions": actions or [],
        "email": recipient,
    }
    if phone or prefix:
        user_entry["phoneNumber"] = {"phone": phone or "", "prefix": prefix or ""}
    payload = {
        "files": [files_entry],
        "notify_recipients": notify,
        "message_id": message_id or "",
        "protect_message": protect_message,
        "users": [user_entry],
        "groups": [],
    }
    return payload
def share_file(
    file_id: str,
    recipient: str,
    policy_id: str | None,
    notify: bool,
    protect_message: bool,
    message_id: str | None,
    read_only: bool,
    actions: list[str] | None,
    phone: str | None,
    prefix: str | None,
    timeout: int = 60,
) -> dict:
    url = f"{SPECTERX_API_BASE}{SHARE_PATH}"
    payload = build_payload(
        file_id=file_id,
        recipient=recipient,
        policy_id=policy_id,
        notify=notify,
        protect_message=protect_message,
        message_id=message_id,
        read_only=read_only,
        actions=actions,
        phone=phone,
        prefix=prefix,
    )
    resp = requests.post(
        url,
        headers=build_headers(),
        json=payload,
        verify=False,  # staging certs
        timeout=timeout,
    )
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        raise SystemExit(
            f":x: Share request failed (HTTP {resp.status_code}).\nURL: {url}\nBody: {resp.text}"
        ) from e
    try:
        return resp.json()
    except ValueError:
        return {"raw": resp.text}
def parse_actions(actions_csv: str | None) -> list[str] | None:
    if not actions_csv:
        return None
    return [a.strip() for a in actions_csv.split(",") if a.strip()]
def main():
    p = argparse.ArgumentParser(description="Share a SpecterX file with a recipient (staging).")
    p.add_argument("--file-id", required=True, help="SpecterX file_id to share")
    p.add_argument("--recipient", required=True, help="Recipient email")
    p.add_argument("--policy-id", help="Optional policy_id to apply for this share")
    p.add_argument("--notify", action="store_true", default=True, help="Notify recipients (default: true)")
    p.add_argument("--no-notify", dest="notify", action="store_false", help="Do not notify recipients")
    p.add_argument("--protect-message", action="store_true", default=True, help="Protect message (default: true)")
    p.add_argument("--no-protect-message", dest="protect_message", action="store_false", help="Do not protect message")
    p.add_argument("--message-id", default="", help="Optional message_id to correlate (default empty)")
    p.add_argument("--read-only", action="store_true", default=False, help="Grant read-only access (default: false)")
    p.add_argument("--actions", help="Comma-separated actions (e.g. 'download,print')")
    p.add_argument("--phone", help="Recipient phone number (optional)")
    p.add_argument("--prefix", help="Phone prefix/country code (optional)")
    p.add_argument("--timeout", type=int, default=60, help="HTTP timeout seconds (default 60)")
    args = p.parse_args()
    # Basic sanity checks
    if not SPECTERX_API_KEY or not SPECTERX_USER_ID:
        print(":x: Missing hardcoded credentials.", file=sys.stderr)
        sys.exit(2)
    print(f"→ API Base: {SPECTERX_API_BASE}")
    print(f"→ Endpoint: {SHARE_PATH}")
    print(f"→ File ID : {args.file_id}")
    print(f"→ Recipient: {args.recipient}")
    actions = parse_actions(args.actions)
    result = share_file(
        file_id=args.file_id,
        recipient=args.recipient,
        policy_id=args.policy_id,
        notify=args.notify,
        protect_message=args.protect_message,
        message_id=args.message_id,
        read_only=args.read_only,
        actions=actions,
        phone=args.phone,
        prefix=args.prefix,
        timeout=args.timeout,
    )
    print(":white_check_mark: Share request sent successfully.")
    print(json.dumps(result, indent=2, ensure_ascii=False))
if __name__ == "__main__":
    main()
you can call the second script by:
python3 share_a_file.py \
  --file-id 8fab29ed-de04-44e1-95b6-3dbe676294fe \
  --recipient bandss@gmail.com