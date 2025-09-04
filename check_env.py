#!/usr/bin/env python3
"""
Quick environment check for the multi-tenant workflow
"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Check required environment variables
required_vars = [
    "NEON_API_KEY",
    "CATALOG_DATABASE_URL",
    "NEO4J_URI",
    "NEO4J_USER",
    "NEO4J_PASSWORD",
    "GOOGLE_API_KEY",
]

print("🔍 Checking Environment Variables:")
print("=" * 50)

all_present = True
for var in required_vars:
    value = os.getenv(var)
    if value:
        # Mask sensitive values
        if "KEY" in var or "PASSWORD" in var:
            masked_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            print(f"✅ {var}: {masked_value}")
        else:
            print(f"✅ {var}: {value[:50]}{'...' if len(value) > 50 else ''}")
    else:
        print(f"❌ {var}: Not set")
        all_present = False

print("\n" + "=" * 50)
if all_present:
    print("🎉 All required environment variables are set!")
    print("Ready to run the complete workflow.")
else:
    print("⚠️ Some environment variables are missing.")
    print("Please set them before running the workflow.")

# Check if documents exist
from pathlib import Path

documents_folder = Path("documents")
if documents_folder.exists():
    print(f"\n📁 Documents folder: {documents_folder}")
    for subfolder in ["Tenant 1", "Tenant 2"]:
        subfolder_path = documents_folder / subfolder
        if subfolder_path.exists():
            docs = list(subfolder_path.glob("*.md"))
            print(f"   {subfolder}: {len(docs)} documents")
            for doc in docs:
                print(f"      - {doc.name}")
        else:
            print(f"   {subfolder}: Folder not found")
else:
    print("\n❌ Documents folder not found")
