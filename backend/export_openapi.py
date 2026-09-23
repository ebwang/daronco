# backend/export_openapi.py
"""
Utility script that exports the OpenAPI (Swagger) specification of the API as JSON.
"""

import json
import os
import sys

# Makes sure the backend directory is on the path
sys.path.insert(0, os.path.dirname(__file__))

from main import app

def export_openapi():
    openapi_data = app.openapi()
    
    # Saves the file inside the backend directory
    backend_path = os.path.join(os.path.dirname(__file__), "openapi.json")
    with open(backend_path, "w", encoding="utf-8") as f:
        json.dump(openapi_data, f, indent=2, ensure_ascii=False)
    print(f"✅ OpenAPI specification successfully saved to: {backend_path}")

    # Saves the file at the repository root
    root_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "openapi.json")
    with open(root_path, "w", encoding="utf-8") as f:
        json.dump(openapi_data, f, indent=2, ensure_ascii=False)
    print(f"✅ OpenAPI specification successfully saved to: {root_path}")

if __name__ == "__main__":
    export_openapi()
