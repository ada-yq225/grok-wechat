import subprocess

for name in ("Narrator", "Weixin"):
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         f"(Get-Process -Name {name} -ErrorAction SilentlyContinue | Measure-Object).Count"],
        capture_output=True, text=True, check=False,
    )
    print(f"{name}={r.stdout.strip()}")