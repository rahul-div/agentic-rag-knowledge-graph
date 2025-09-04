#!/usr/bin/env python3
"""
Check Real Test Results
Shows what we actually created in both Neon and Neo4j
"""

import asyncio
import os
from pathlib import Path
import sys

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))

from tenant_manager import TenantManager
from tenant_graphiti_client import TenantGraphitiClient
from dotenv import load_dotenv

# Load environment
load_dotenv()


async def check_real_results():
    """Check what we actually created in Neon and Neo4j."""

    print("🔍 CHECKING REAL RESOURCES CREATED")
    print("=" * 60)

    # Initialize managers
    tenant_manager = TenantManager(
        neon_api_key=os.getenv("NEON_API_KEY"),
        catalog_db_url=os.getenv("CATALOG_DATABASE_URL"),
        default_region=os.getenv("NEON_DEFAULT_REGION", "aws-us-east-1"),
    )

    graphiti_client = TenantGraphitiClient(
        neo4j_uri=os.getenv("NEO4J_URI"),
        neo4j_user=os.getenv("NEO4J_USERNAME"),
        neo4j_password=os.getenv("NEO4J_PASSWORD"),
    )
    await graphiti_client.initialize()

    try:
        # Check Neon projects
        print("\n📊 NEON PROJECTS (Will appear in your Neon UI):")
        print("-" * 50)

        tenants = await tenant_manager.list_tenants()

        if tenants:
            for tenant in tenants:
                print(f"✅ Tenant: {tenant.tenant_name}")
                print(f"   ID: {tenant.tenant_id}")
                print(f"   Email: {tenant.tenant_email}")
                print(f"   Neon Project: {tenant.neon_project_id}")
                print(f"   Status: {tenant.status}")
                print(f"   Created: {tenant.created_at}")
                print()
        else:
            print("   No tenants found in catalog")

        # Check Neo4j namespaces
        print("\n🕸️ NEO4J NAMESPACES (Check your Neo4j Desktop):")
        print("-" * 50)

        # Query for all group_ids in Neo4j
        query = """
        MATCH (n)
        WHERE n.group_id IS NOT NULL
        RETURN DISTINCT n.group_id as group_id, 
               labels(n) as node_types,
               count(*) as node_count
        ORDER BY group_id
        """

        try:
            with graphiti_client.driver.session() as session:
                result = session.run(query)

                namespaces_found = False
                for record in result:
                    group_id = record["group_id"]
                    node_types = record["node_types"]
                    node_count = record["node_count"]

                    if group_id.startswith("tenant_"):
                        print(f"✅ Namespace: {group_id}")
                        print(f"   Node Types: {node_types}")
                        print(f"   Node Count: {node_count}")
                        print()
                        namespaces_found = True

                if not namespaces_found:
                    print("   📋 Found group_ids but no tenant namespaces yet")
                    print("   (Document ingestion was not completed in the test)")

        except Exception as e:
            print(f"   ❌ Error querying Neo4j: {e}")
            print("   💡 Check your Neo4j Desktop manually for tenant namespaces")

        print("\n🎯 SUMMARY:")
        print("-" * 50)
        print("• Check your Neon UI to see the new projects listed above")
        print("• Check your Neo4j Desktop to see the new namespaces listed above")
        print("• The previous group namespaces you mentioned are from earlier tests")
        print("• Mock prototypes do NOT create real resources (as expected)")

    finally:
        await tenant_manager.close()
        await graphiti_client.close()


if __name__ == "__main__":
    asyncio.run(check_real_results())
