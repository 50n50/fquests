import os
import json
import urllib.request
import urllib.error
import time

API_URL = "https://discord.com/api/v9/applications/detectable"
CACHE_FILE = "detectable_apps.json"

def fetch_detectable_apps(force_refresh=False):
    if not force_refresh and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception:
            pass

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    req = urllib.request.Request(API_URL, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status == 200:
                raw_data = response.read().decode("utf-8")
                data = json.loads(raw_data)
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    f.write(raw_data)
                return data
            else:
                raise Exception(f"HTTP {response.status}")
    except Exception as e:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        raise e

def parse_app_executables(app):
    execs = app.get("executables", [])
    win_execs = []
    for ex in execs:
        os_type = ex.get("os", "").lower()
        if os_type in ["win32", "win64", "windows", ""] or not os_type:
            name = ex.get("name", "").strip()
            if name:
                win_execs.append({
                    "name": name,
                    "is_launcher": ex.get("is_launcher", False),
                    "arguments": ex.get("arguments", ""),
                    "os": os_type or "win32"
                })
    return win_execs

def search_apps(apps_list, query, limit=50):
    if not query or not query.strip():
        return apps_list[:limit]

    q = query.strip().lower()
    results = []

    for app in apps_list:
        app_name = app.get("name", "")
        app_id = str(app.get("id", ""))
        aliases = [a.lower() for a in app.get("aliases", [])]
        win_execs = parse_app_executables(app)
        exec_names = [e["name"].lower() for e in win_execs]

        score = 0

        if app_name.lower() == q:
            score += 100
        elif any(ex == q for ex in exec_names):
            score += 90
        elif app_id == q:
            score += 85
        elif app_name.lower().startswith(q):
            score += 70
        elif any(ex.startswith(q) for ex in exec_names):
            score += 65
        elif q in app_name.lower():
            score += 50
        elif any(q in ex for ex in exec_names):
            score += 45
        elif any(q in alias for alias in aliases):
            score += 30

        if score > 0:
            results.append((score, app))

    results.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in results[:limit]]

if __name__ == "__main__":
    apps = fetch_detectable_apps()
    print(f"Loaded {len(apps)} apps.")
