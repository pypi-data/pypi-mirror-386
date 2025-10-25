import os
import json
import base64
import requests
import yaml
from batre.aggregate import aggregate
from batre.utils import update_repo
from rich import print


def upload_file(api_url, token, project_id, output_path, base_path):
    """Upload aggregated.json to Batre Translator API encoded as Base64."""
    language = os.path.basename(base_path)  # e.g. en-GB
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Read and encode file to Base64
    with open(output_path, "rb") as f:
        file_bytes = f.read()
        encoded = base64.b64encode(file_bytes).decode("utf-8")

    payload = {
        "project_id": project_id,
        "language": language,
        "payload_base64": encoded
    }

    print(f"[cyan]🌍 Sending {language} translation data to {api_url} (Base64 mode)...[/cyan]")
    r = requests.post(f"{api_url}/translations/upload", json=payload, headers=headers)

    if r.status_code == 200:
        print(f"[green]✅ Upload successful![/green]")
        try:
            print(json.dumps(r.json(), indent=2))
        except Exception:
            print(r.text)
    else:
        print(f"[red]❌ Upload failed ({r.status_code})[/red]")
        print(r.text)

    return r


def main():
    config_path = ".batre.yml"
    if not os.path.exists(config_path):
        print("[red]❌ Config file .batre.yml not found[/red]")
        return

    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    project_id = cfg["project_id"]
    repo_path = cfg.get("repo_path", ".")
    base_path = os.path.join(repo_path, cfg["base_path"])
    api_url = cfg["api_url"]
    token = cfg["api_token"]

    print(f"[cyan]🔄 Updating repo at {repo_path}...[/cyan]")
    update_repo(repo_path)

    print(f"[cyan]📦 Aggregating translations from {base_path}...[/cyan]")
    data = aggregate(base_path)

    output_path = os.path.join(base_path, "aggregated.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[cyan]🚀 Uploading aggregated file to Batre Translator...[/cyan]")
    r = upload_file(api_url, token, project_id, output_path, base_path)  # ✅ fixed argument

    if r.status_code == 200:
        print(f"[green]✅ Upload successful![/green] Response: {r.text}")
    else:
        print(f"[red]❌ Upload failed ({r.status_code})[/red] {r.text}")


if __name__ == "__main__":
    main()
