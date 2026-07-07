import requests

# 1. Login
url = "http://localhost:5000/api/auth/login"
data = {"email": "admin@example.com", "password": "YourPassword123"}
r = requests.post(url, json=data)
print("Login status:", r.status_code)
if r.status_code != 200:
    print(r.text)
    # try to register
    r = requests.post("http://localhost:5000/api/auth/register", json={
        "email": "admin@example.com",
        "name": "Admin",
        "password": "YourPassword123",
        "roles": ["admin"]
    })
    print("Register status:", r.status_code)
    r = requests.post(url, json=data)
    print("Login status after register:", r.status_code)

token = r.json().get("access_token")
print("Token:", token)

# 2. Access dashboard
r2 = requests.get("http://localhost:5000/dashboard", headers={"Authorization": f"Bearer {token}"})
print("Dashboard status:", r2.status_code)
print("Dashboard response:", r2.text)
