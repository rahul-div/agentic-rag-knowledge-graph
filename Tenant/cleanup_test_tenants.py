#!/usr/bin/env python3
"""
Clean up test tenants from the catalog database.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from agent.db_utils import CatalogDatabase

load_dotenv()


async def cleanup_test_tenants():
    """Clean up test tenants from catalog database."""
    try:
        catalog_db = CatalogDatabase()

        # List existing test tenants
        print("\n🔍 Checking for existing test tenants...")
        async with catalog_db.get_connection() as conn:
            test_tenants = await conn.fetch("""
                SELECT tenant_id, tenant_name, tenant_email, neon_project_id, created_at
                FROM tenant_projects 
                WHERE tenant_email LIKE '%test%' OR tenant_name LIKE '%Test%' OR tenant_name LIKE '%Real%'
                ORDER BY created_at DESC
            """)

            if not test_tenants:
                print("✅ No test tenants found")
                return

            print(f"\nFound {len(test_tenants)} test tenant(s):")
            for tenant in test_tenants:
                print(
                    f"  - {tenant['tenant_name']} ({tenant['tenant_email']}) - Project: {tenant['neon_project_id']}"
                )

            # Ask for confirmation
            response = (
                input(f"\n⚠️  Delete all {len(test_tenants)} test tenant(s)? (y/N): ")
                .strip()
                .lower()
            )
            if response != "y":
                print("❌ Cleanup cancelled")
                return

            # Delete test tenants
            deleted_count = await conn.fetchval("""
                DELETE FROM tenant_projects 
                WHERE tenant_email LIKE '%test%' OR tenant_name LIKE '%Test%' OR tenant_name LIKE '%Real%'
                RETURNING count(*)
            """)

            print(f"✅ Deleted {deleted_count} test tenant(s) from catalog")
            print("\n⚠️  Note: This only removes the catalog entries.")
            print(
                "   The Neon projects themselves may still exist and need manual cleanup."
            )

    except Exception as e:
        print(f"❌ Failed to cleanup test tenants: {e}")

    finally:
        await catalog_db.close()


if __name__ == "__main__":
    asyncio.run(cleanup_test_tenants())
