import urllib.request

try:
    vite_res = urllib.request.urlopen("http://localhost:5173/")
    print(f"Vite Frontend Server: Status {vite_res.getcode()} OK")
except Exception as e:
    print(f"Vite Error: {e}")

try:
    api_res = urllib.request.urlopen("http://127.0.0.1:8000/api/health")
    print(f"FastAPI Backend Health: Status {api_res.getcode()} OK")
except Exception as e:
    print(f"FastAPI Error: {e}")
