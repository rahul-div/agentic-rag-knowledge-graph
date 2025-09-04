#!/usr/bin/env python3
"""
Fix Catalog Database Connection
Find the correct connection string for ep-little-art-a1cz16pj
"""

print("🔧 FIXING CATALOG DATABASE CONNECTION")
print("=" * 50)

print("\n📋 ISSUE IDENTIFIED:")
print("• Reconciliation script uses CATALOG_DATABASE_URL")
print("• Current CATALOG_DATABASE_URL points to 'ep-catalog' (placeholder)")
print("• Real catalog project is 'ep-little-art-a1cz16pj' (from successful validation)")
print("• Need to update .env with correct connection string")

print("\n🎯 SOLUTION STEPS:")
print("1. Get the connection string for project 'ep-little-art-a1cz16pj' from Neon UI")
print("2. Update CATALOG_DATABASE_URL in your .env file")
print("3. Re-run the reconciliation script")

print("\n📝 HOW TO GET THE CORRECT CONNECTION STRING:")
print("1. Go to your Neon Console: https://console.neon.tech/app/projects")
print("2. Find project 'ep-little-art-a1cz16pj' in your project list")
print("3. Click on the project")
print("4. Go to 'Connection Details' or 'Connect' tab")
print("5. Copy the PostgreSQL connection string")
print("6. It should look like:")
print(
    "   postgresql://username:password@ep-little-art-a1cz16pj-pooler.us-east-1.aws.neon.tech/neondb"
)

print("\n🔧 UPDATE YOUR .env FILE:")
print("Replace this line:")
print(
    "CATALOG_DATABASE_URL=postgresql://username:password@ep-catalog.us-east-2.aws.neon.tech/neondb"
)
print("\nWith the real connection string from step 5 above.")

print("\n✅ VERIFICATION:")
print("After updating, run this to test:")
print("cd /Users/rahul/Desktop/Graphiti/agentic-rag-knowledge-graph/Tenant")
print(
    "python3 -c \"import asyncio, asyncpg, os; from dotenv import load_dotenv; load_dotenv(); asyncio.run(asyncpg.connect(os.getenv('CATALOG_DATABASE_URL')).then(lambda c: print('✅ Connection works!')))\""
)

print("\n🚀 THEN RUN RECONCILIATION:")
print("python3 tenant_reconciliation_complete.py --mode=reconcile")
