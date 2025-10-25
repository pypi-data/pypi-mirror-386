#!/usr/bin/env python3
import os, json, base64, yaml
from rich import print

def write_locale_files(export_path, language, payload):
    """Recreate locale folder structure for a given language (2-level depth only)."""
    lang_path = os.path.join(export_path, language)
    os.makedirs(lang_path, exist_ok=True)

    for top_key, top_val in payload.items():
        # First level → folder (e.g. auth, dashboard)
        folder_path = os.path.join(lang_path, top_key)
        os.makedirs(folder_path, exist_ok=True)

        if not isinstance(top_val, dict):
            print(f"[yellow]⚠️ Skipping non-dict section: {top_key}[/yellow]")
            continue

        for file_key, file_val in top_val.items():
            if not isinstance(file_val, dict):
                print(f"[yellow]⚠️ Skipping {top_key}/{file_key} (not a dict)[/yellow]")
                continue

            file_path = os.path.join(folder_path, f"{file_key}.js")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("const messages = ")
                json.dump(file_val, f, indent=2, ensure_ascii=False)
                f.write(";\nexport default { messages };")

            print(f"[green]✅ Wrote {language}/{top_key}/{file_key}.js[/green]")


def main():
    cfg_path = ".batre.yml"
    if not os.path.exists(cfg_path):
        print("[red]❌ Config file .batre.yml not found[/red]")
        return

    with open(cfg_path, "r") as f:
        cfg = yaml.safe_load(f)

    project_id = cfg["project_id"]
    repo_path = cfg.get("repo_path", ".")
    base_path = os.path.join(repo_path, cfg["base_path"])
    export_path = os.path.join(repo_path, cfg.get("export_path", "src/locales/dist"))

    print(f"[cyan]⬇️  Reading mock export_all.json for {project_id}...[/cyan]")
    with open("mock/export_all.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    translations = data.get("translations", {})
    if not translations:
        print("[yellow]⚠️ No translations found.[/yellow]")
        return

    os.makedirs(export_path, exist_ok=True)

    for lang, lang_data in translations.items():
        print(f"[cyan]📦 Processing {lang}...[/cyan]")
        decoded_raw = base64.b64decode(lang_data["payload_base64"]).decode("utf-8").strip()

        # Remove invisible BOM if present
        if decoded_raw.startswith("\ufeff"):
            decoded_raw = decoded_raw.encode().decode("utf-8-sig")

        try:
            decoded = json.loads(decoded_raw)
        except json.JSONDecodeError as e:
            print(f"[red]❌ JSON parse error in {lang}: {e}[/red]")
            with open("mock/debug_failed.json", "w", encoding="utf-8") as dbg:
                dbg.write(decoded_raw)
            print("[cyan]💾 Raw content saved to mock/debug_failed.json for inspection.[/cyan]")
            return

        write_locale_files(export_path, lang, decoded)

    print(f"[bold green]✅ Folder reconstruction complete in:[/bold green] {export_path}")


if __name__ == "__main__":
    main()
