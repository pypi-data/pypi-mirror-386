#!/usr/bin/env python3
import json
import os
import re

import quickjs
import yaml


def parse_js_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        # znajdź wnętrze const messages = { ... }
        match = re.search(
            r"const\s+messages\s*=\s*(\{[\s\S]*?\})\s*export\s+default", content
        )
        if not match:
            print(f"⚠️ No 'messages' object found in {file_path}")
            return None

        js_object = match.group(1).strip()

        # usuń końcowe przecinki i komentarze
        js_object = re.sub(r",(\s*[}\]])", r"\1", js_object)
        js_object = re.sub(r"//.*", "", js_object)
        js_object = re.sub(r"/\*[\s\S]*?\*/", "", js_object)

        # silnik JS — QuickJS
        ctx = quickjs.Context()
        result = ctx.eval(f"JSON.stringify({js_object})")
        return json.loads(result)

    except Exception as e:
        print(f"⚠️ Error parsing {file_path}: {e}")
        return None


def aggregate(base_path):
    aggregated = {}
    parsed_files = 0

    print(f"🔍 Searching in: {os.path.abspath(base_path)}")

    for root, _, files in os.walk(base_path):
        for file in files:
            # pomiń własny output
            if file == "aggregated.json":
                continue

            if file.endswith(".js") or file.endswith(".json"):
                path = os.path.join(root, file)
                rel = os.path.relpath(path, base_path)
                parts = rel.replace("\\", "/").split("/")
                parts[-1] = os.path.splitext(parts[-1])[0]

                data = parse_js_file(path)
                if not data:
                    continue

                node = aggregated
                for p in parts[:-1]:
                    node = node.setdefault(p, {})
                node[parts[-1]] = data
                parsed_files += 1
                print(f"✅ Parsed: {rel}")

    print(f"\n💾 Writing aggregated.json ({parsed_files} files combined)")
    return aggregated


def load_config():
    """Wczytaj .batre.yml i zwróć config."""
    cfg_path = os.path.join(os.getcwd(), ".batre.yml")
    if not os.path.exists(cfg_path):
        print("❌ Config file .batre.yml not found")
        return None
    with open(cfg_path, "r") as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    # 1️⃣ wczytaj konfigurację
    cfg = load_config()
    if not cfg or "base_path" not in cfg:
        print("❌ base_path not defined in .batre.yml")
        exit(1)

    base_path = os.path.abspath(cfg["base_path"])
    print(f"📁 Using base path from .batre.yml: {base_path}")

    # 2️⃣ agregacja
    data = aggregate(base_path)

    # 3️⃣ zapis wyników
    output_path = os.path.join(base_path, "aggregated.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Aggregated file saved to: {output_path}")
