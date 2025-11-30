from fastapi.testclient import TestClient
from app_main import app

client = TestClient(app)

for path in ["/", "/pcp", "/oncologist", "/patient"]:
    r = client.get(path)
    print(path, "->", r.status_code)
