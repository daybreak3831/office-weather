"""Fetch Korea Space Weather Center observations for a static GitHub Pages site."""

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


BASE = "https://spaceweather.kasa.go.kr/api"
TARGET = Path(__file__).resolve().parents[1] / "spaceweather.json"
ENDPOINTS = {"warn": "/warn", "kindex": "/kindex", "solarWind": "/ace/sw"}


def fetch(path):
    request = Request(
        BASE + path,
        headers={"User-Agent": "office-weather-spaceweather/1.0", "Accept": "application/json"},
    )
    with urlopen(request, timeout=20) as response:
        data = json.load(response)
    if not isinstance(data, dict) or data.get("Error") is True or data.get("error") is True:
        raise ValueError(f"Invalid API result: {data.get('ErrorCode', 'unknown') if isinstance(data, dict) else 'not JSON object'}")
    return data


def main():
    result = {"generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "source": "KASA Korea Space Weather Center"}
    errors = {}
    for name, path in ENDPOINTS.items():
        try:
            result[name] = fetch(path)
        except Exception as exc:
            result[name] = None
            errors[name] = str(exc)
            print(f"{name}: {exc}", file=sys.stderr)

    # Do not publish an empty or misleading update. Keep the previous JSON if all fail.
    if len(errors) == len(ENDPOINTS):
        raise SystemExit("All upstream APIs failed; the previous data file was kept.")

    result["errors"] = errors
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=TARGET.parent, delete=False, suffix=".tmp") as output:
        json.dump(result, output, ensure_ascii=False, separators=(",", ":"))
        temporary = output.name
    os.replace(temporary, TARGET)
    print(f"Saved {TARGET} ({len(ENDPOINTS) - len(errors)}/{len(ENDPOINTS)} endpoints)")


if __name__ == "__main__":
    main()
