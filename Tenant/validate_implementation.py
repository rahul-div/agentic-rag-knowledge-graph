#!/usr/bin/env python3
"""
Implementation Validation Script for Multi-Tenant RAG System
Validates compliance with official Neon and Graphiti patterns.
"""

import os
import sys
import importlib.util
from pathlib import Path
from typing import List, Dict, Any


class ImplementationValidator:
    """Validates the multi-tenant implementation against official patterns."""

    def __init__(self, tenant_dir: str):
        self.tenant_dir = Path(tenant_dir)
        self.issues = []
        self.successes = []

    def validate_file_structure(self) -> bool:
        """Validate that all required files exist."""
        required_files = [
            "__init__.py",
            "main.py",
            "requirements.txt",
            "catalog_schema.sql",
            "tenant_schema.sql",
            "tenant_manager.py",
            "tenant_graphiti_client.py",
            "multi_tenant_agent.py",
            "multi_tenant_api.py",
            "auth_middleware.py",
            "README.md",
            "deployment_guide.md",
            "testing_guide.md",
        ]

        missing_files = []
        for file in required_files:
            if not (self.tenant_dir / file).exists():
                missing_files.append(file)

        if missing_files:
            self.issues.append(f"Missing required files: {missing_files}")
            return False
        else:
            self.successes.append("✅ All required files present")
            return True

    def validate_architecture_compliance(self) -> bool:
        """Validate compliance with official Neon and Graphiti patterns."""
        issues_found = []

        # Check for old RLS references
        rls_files = list(self.tenant_dir.glob("*_old_rls.py"))
        if rls_files:
            self.successes.append(
                f"✅ Old RLS files preserved: {[f.name for f in rls_files]}"
            )

        # Check schema files
        catalog_schema = self.tenant_dir / "catalog_schema.sql"
        tenant_schema = self.tenant_dir / "tenant_schema.sql"

        if catalog_schema.exists():
            content = catalog_schema.read_text()
            if "tenant_projects" in content and "neon_project_id" in content:
                self.successes.append(
                    "✅ Catalog schema follows project-per-tenant pattern"
                )
            else:
                issues_found.append(
                    "Catalog schema missing project-per-tenant structure"
                )

        if tenant_schema.exists():
            content = tenant_schema.read_text()
            # Check for tenant_id columns (not in comments)
            lines = [
                line.strip()
                for line in content.split("\n")
                if line.strip() and not line.strip().startswith("--")
            ]
            has_tenant_id_columns = any("tenant_id" in line for line in lines)

            if not has_tenant_id_columns and "pgvector" in content:
                self.successes.append(
                    "✅ Tenant schema correctly excludes tenant_id columns"
                )
            else:
                issues_found.append("Tenant schema still contains tenant_id references")

        if issues_found:
            self.issues.extend(issues_found)
            return False
        return True

    def validate_imports_and_dependencies(self) -> bool:
        """Validate that imports are consistent and correct."""
        import_issues = []

        # Check __init__.py exports
        init_file = self.tenant_dir / "__init__.py"
        if init_file.exists():
            content = init_file.read_text()
            if "tenant_manager" in content and "tenant_project_manager" not in content:
                self.successes.append(
                    "✅ __init__.py uses correct tenant_manager imports"
                )
            else:
                import_issues.append(
                    "__init__.py still references old tenant_project_manager"
                )

        # Check main component files
        components = ["multi_tenant_agent.py", "multi_tenant_api.py"]

        for component in components:
            file_path = self.tenant_dir / component
            if file_path.exists():
                content = file_path.read_text()
                # Check for import statements specifically
                import_lines = [
                    line.strip()
                    for line in content.split("\n")
                    if line.strip().startswith("from") and "import" in line
                ]

                has_correct_import = any(
                    "tenant_manager" in line for line in import_lines
                )
                has_old_import = any(
                    "tenant_project_manager" in line for line in import_lines
                )

                if has_correct_import and not has_old_import:
                    self.successes.append(f"✅ {component} uses correct imports")
                else:
                    import_issues.append(f"{component} has incorrect imports")

        if import_issues:
            self.issues.extend(import_issues)
            return False
        return True

    def validate_documentation(self) -> bool:
        """Validate that documentation reflects the correct architecture."""
        doc_issues = []

        readme = self.tenant_dir / "README.md"
        if readme.exists():
            content = readme.read_text()
            if "project-per-tenant" in content and "RLS" not in content:
                self.successes.append(
                    "✅ README.md uses correct architecture terminology"
                )
            else:
                doc_issues.append("README.md contains outdated architecture references")

        if doc_issues:
            self.issues.extend(doc_issues)
            return False
        return True

    def validate_configuration(self) -> bool:
        """Validate configuration files and environment setup."""
        config_issues = []

        requirements = self.tenant_dir / "requirements.txt"
        if requirements.exists():
            content = requirements.read_text()
            required_packages = [
                "fastapi",
                "asyncpg",
                "graphiti-core",
                "pydantic-ai",
                "python-jose",
                "pgvector",
            ]
            missing_packages = [pkg for pkg in required_packages if pkg not in content]
            if missing_packages:
                config_issues.append(f"Missing required packages: {missing_packages}")
            else:
                self.successes.append("✅ All required packages in requirements.txt")

        main_py = self.tenant_dir / "main.py"
        if main_py.exists():
            content = main_py.read_text()
            if "CATALOG_DATABASE_URL" in content and "NEON_API_KEY" in content:
                self.successes.append("✅ Main.py has correct environment variables")
            else:
                config_issues.append("Main.py missing required environment variables")

        if config_issues:
            self.issues.extend(config_issues)
            return False
        return True

    def run_validation(self) -> Dict[str, Any]:
        """Run all validation checks."""
        print("🔍 Validating Multi-Tenant RAG Implementation...")
        print("=" * 60)

        validations = [
            ("File Structure", self.validate_file_structure),
            ("Architecture Compliance", self.validate_architecture_compliance),
            ("Imports & Dependencies", self.validate_imports_and_dependencies),
            ("Documentation", self.validate_documentation),
            ("Configuration", self.validate_configuration),
        ]

        results = {}
        all_passed = True

        for name, validator in validations:
            print(f"\n📋 {name}:")
            try:
                passed = validator()
                results[name] = {"passed": passed, "issues": []}
                if passed:
                    print(f"  ✅ PASSED")
                else:
                    print(f"  ❌ FAILED")
                    all_passed = False
            except Exception as e:
                print(f"  ⚠️  ERROR: {e}")
                results[name] = {"passed": False, "issues": [str(e)]}
                all_passed = False

        # Print summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)

        print("\n✅ SUCCESSES:")
        for success in self.successes:
            print(f"  {success}")

        if self.issues:
            print("\n❌ ISSUES:")
            for issue in self.issues:
                print(f"  ❌ {issue}")

        print(f"\n🎯 OVERALL STATUS: {'✅ PASSED' if all_passed else '❌ FAILED'}")

        if all_passed:
            print("🚀 Implementation is ready for testing and deployment!")
        else:
            print("🔧 Please address the issues above before proceeding.")

        return {
            "overall_passed": all_passed,
            "detailed_results": results,
            "successes": self.successes,
            "issues": self.issues,
        }


def main():
    """Main function to run validation."""
    if len(sys.argv) > 1:
        tenant_dir = sys.argv[1]
    else:
        tenant_dir = "."

    if not os.path.exists(tenant_dir):
        print(f"❌ Directory not found: {tenant_dir}")
        return 1

    validator = ImplementationValidator(tenant_dir)
    results = validator.run_validation()

    return 0 if results["overall_passed"] else 1


if __name__ == "__main__":
    exit(main())
