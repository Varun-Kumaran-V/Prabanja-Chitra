"""Test script to verify routes work"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("\n" + "="*60)
print("TESTING ROUTES")
print("="*60 + "\n")

# Test 1: /test
response = client.get("/test")
print(f"GET /test")
print(f"  Status: {response.status_code}")
print(f"  Response: {response.json()}\n")

# Test 2: /api/health
response = client.get("/api/health")
print(f"GET /api/health")
print(f"  Status: {response.status_code}")
print(f"  Response: {response.json()}\n")

# Test 3: /api/visualization/snapshot
response = client.get("/api/visualization/snapshot")
print(f"GET /api/visualization/snapshot")
print(f"  Status: {response.status_code}")
print(f"  Response: {response.json()}\n")

print("="*60)
print("All routes working correctly!" if all([
    client.get("/test").status_code == 200,
    client.get("/api/health").status_code == 200,
    client.get("/api/visualization/snapshot").status_code == 200
]) else "Some routes failed!")
print("="*60 + "\n")
