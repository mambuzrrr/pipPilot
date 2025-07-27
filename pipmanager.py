# pipmanager.py
import subprocess, json

def get_installed_packages(interpreter):
    result = subprocess.run(
        [interpreter, "-m", "pip", "list", "--format=json", "--disable-pip-version-check", "--no-cache-dir"],
        capture_output=True, text=True
    )
    try:
        return {pkg['name']: pkg['version'] for pkg in json.loads(result.stdout)}
    except:
        return {}
