"""Debug script to check registered routes"""
from app.main import app

print("\n" + "="*60)
print("ALL REGISTERED ROUTES")
print("="*60)

for route in app.routes:
    if hasattr(route, 'path'):
        methods = getattr(route, 'methods', set())
        methods_str = ', '.join(sorted(methods)) if methods else 'N/A'
        name = getattr(route, 'name', 'unnamed')
        print(f"{methods_str:10} {route.path:40} ({name})")

print("="*60)
print(f"Total routes: {len(app.routes)}")
print("="*60 + "\n")
