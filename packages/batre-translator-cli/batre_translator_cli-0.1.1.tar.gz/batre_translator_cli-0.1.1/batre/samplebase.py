import json, base64

with open("resources/locales/en-GB/aggregated.json", "r", encoding="utf-8") as f:
    data = f.read()

encoded = base64.b64encode(data.encode("utf-8")).decode("utf-8")

print(encoded[:200] + "...")
