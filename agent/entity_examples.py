"""
Real-World Examples: Using Custom Entity Models with Graphiti

This file demonstrates practical examples of how to use custom entity models
with different data types (text, JSON, YAML) for project management.
"""

import asyncio
import json
from datetime import datetime
from graphiti_core import GraphitiClient
from graphiti_core.utils import EpisodeType

# Import our custom entity models
from custom_entities import (
    ENTITY_TYPES,
    EDGE_TYPES,
    EDGE_TYPE_MAP,
    EXCLUDED_ENTITY_TYPES,
)

# =============================================================================
# EXAMPLE 1: TEXT EPISODE WITH CUSTOM ENTITIES
# =============================================================================


async def example_text_episode_with_custom_entities():
    """Example: Adding a text episode that extracts custom project management entities."""

    # Initialize Graphiti client (you'd use your actual client)
    graphiti = GraphitiClient()  # Configure with your settings

    # Text from a project meeting
    meeting_notes = """
    Meeting with TechCorp client on January 15, 2024:
    
    Sarah Johnson (CTO at TechCorp) discussed the Phoenix E-commerce Platform project.
    The project has a $500,000 budget and needs to be completed by March 2024.
    
    Key requirements:
    - React frontend with TypeScript
    - Python Django backend
    - PostgreSQL database
    - Stripe payment integration
    - AWS deployment
    
    Team assignments:
    - Alex Chen (Senior Developer) - Lead backend development - 80% allocation
    - Maria Rodriguez (Frontend Developer) - React components - 100% allocation  
    - David Kim (DevOps Engineer) - AWS infrastructure - 40% allocation
    
    High priority task: Set up development environment by January 20, 2024
    Medium priority task: Complete user authentication module by February 1, 2024
    """

    # Add episode with custom entity types
    await graphiti.add_episode(
        name="techcorp_phoenix_project_kickoff",
        episode_body=meeting_notes,
        source=EpisodeType.text,
        source_description="Project kickoff meeting notes",
        reference_time=datetime(2024, 1, 15, 14, 30),
        # Use our custom entity and edge types
        entity_types=ENTITY_TYPES,
        edge_types=EDGE_TYPES,
        edge_type_map=EDGE_TYPE_MAP,
        excluded_entity_types=EXCLUDED_ENTITY_TYPES,
        # Optional: namespace for multi-client setup
        group_id="techcorp_projects",
    )

    print("✅ Text episode added with custom entities")
    print("Graphiti will automatically extract:")
    print("- Client: TechCorp (industry, company_size, primary_contact)")
    print("- Project: Phoenix E-commerce Platform (budget, end_date, project_type)")
    print("- TeamMembers: Sarah Johnson, Alex Chen, Maria Rodriguez, David Kim")
    print("- Technologies: React, TypeScript, Python, Django, PostgreSQL, Stripe, AWS")
    print("- Tasks: Setup dev environment, User authentication module")
    print("- Relationships: ProjectAssignments, TechnologyUsage, TaskAssignments")


# =============================================================================
# EXAMPLE 2: JSON EPISODE WITH STRUCTURED PROJECT DATA
# =============================================================================


async def example_json_episode_with_project_data():
    """Example: Adding structured project data as JSON episode."""

    graphiti = GraphitiClient()

    # Structured project data (from project management tool export)
    project_data = {
        "project": {
            "id": "PROJ-2024-001",
            "name": "Phoenix E-commerce Platform",
            "client": "TechCorp",
            "status": "in_progress",
            "budget": 500000,
            "start_date": "2024-01-15T00:00:00Z",
            "end_date": "2024-03-30T00:00:00Z",
            "project_type": "web application",
            "methodology": "agile",
            "team_size": 4,
            "complexity_score": 8,
        },
        "team_members": [
            {
                "name": "Alex Chen",
                "role": "Senior Backend Developer",
                "experience_years": 8,
                "hourly_rate": 120,
                "availability": 0.8,
                "location": "San Francisco, CA",
                "employment_type": "full-time",
                "skills": "Python, Django, PostgreSQL, AWS, Docker",
            },
            {
                "name": "Maria Rodriguez",
                "role": "Frontend Developer",
                "experience_years": 5,
                "hourly_rate": 95,
                "availability": 1.0,
                "location": "Austin, TX",
                "employment_type": "contractor",
                "skills": "React, TypeScript, CSS, Figma",
            },
        ],
        "technologies": [
            {
                "name": "React",
                "category": "frontend",
                "version": "18.2.0",
                "learning_curve": "medium",
                "popularity_score": 9,
                "license_type": "MIT",
            },
            {
                "name": "Django",
                "category": "backend",
                "version": "4.2",
                "learning_curve": "medium",
                "popularity_score": 8,
                "license_type": "BSD",
            },
        ],
        "tasks": [
            {
                "name": "Setup Development Environment",
                "status": "done",
                "priority": "high",
                "estimated_hours": 16,
                "actual_hours": 12,
                "due_date": "2024-01-20T00:00:00Z",
                "completed_date": "2024-01-19T00:00:00Z",
                "story_points": 5,
                "epic": "Project Setup",
            },
            {
                "name": "User Authentication Module",
                "status": "in_progress",
                "priority": "medium",
                "estimated_hours": 40,
                "actual_hours": 18,
                "due_date": "2024-02-01T00:00:00Z",
                "story_points": 13,
                "epic": "Core Backend Features",
            },
        ],
    }

    # Add JSON episode
    await graphiti.add_episode(
        name="phoenix_project_structured_data",
        episode_body=project_data,  # Pass Python dict directly
        source=EpisodeType.json,
        source_description="Project management tool export",
        reference_time=datetime.now(),
        entity_types=ENTITY_TYPES,
        edge_types=EDGE_TYPES,
        edge_type_map=EDGE_TYPE_MAP,
        group_id="techcorp_projects",
    )

    print("✅ JSON episode added with structured project data")
    print("Graphiti will create entities with validated attributes:")
    print("- Project entity with budget validation, complexity score 1-10")
    print("- TeamMember entities with experience and availability validation")
    print("- Technology entities with popularity scores and categories")
    print("- Task entities with story points and status validation")


# =============================================================================
# EXAMPLE 3: YAML EPISODE (YOUR CURRENT WORKFLOW)
# =============================================================================


async def example_yaml_episode_with_requirements():
    """Example: Adding YAML requirements document (from your current workflow)."""

    graphiti = GraphitiClient()

    # Sample YAML content (this would come from your ingestion pipeline)
    yaml_content = """
    project: Phoenix E-commerce Platform
    client: TechCorp
    
    requirements:
      functional:
        - id: REQ-001
          type: functional
          priority: high
          status: approved
          description: User registration and login system
          acceptance_criteria: Users can create accounts, login, and reset passwords
          estimated_effort: 8
          source: client
          
        - id: REQ-002
          type: functional
          priority: medium
          status: draft
          description: Product catalog browsing
          acceptance_criteria: Users can view products, filter by category, search by name
          estimated_effort: 13
          source: stakeholder
          
      non_functional:
        - id: REQ-003
          type: non-functional
          priority: high
          status: approved
          description: System performance requirements
          acceptance_criteria: Page load times under 2 seconds, handle 1000 concurrent users
          estimated_effort: 5
          source: technical_team
    
    modules:
      - name: Authentication Module
        type: backend
        complexity: medium
        dependencies: Django, PostgreSQL, JWT
        estimated_dev_time: 2.5
        testing_effort: 0.3
        documentation_status: in_progress
        
      - name: Product Catalog UI
        type: frontend
        complexity: high
        dependencies: React, TypeScript, Material-UI
        estimated_dev_time: 4.0
        testing_effort: 0.25
        documentation_status: pending
    """

    # Add YAML episode (your ingestion pipeline converts YAML to text)
    await graphiti.add_episode(
        name="phoenix_requirements_specification",
        episode_body=yaml_content,  # Your pipeline would convert YAML to this text
        source=EpisodeType.text,
        source_description="Requirements specification document",
        reference_time=datetime.now(),
        entity_types=ENTITY_TYPES,
        edge_types=EDGE_TYPES,
        edge_type_map=EDGE_TYPE_MAP,
        group_id="techcorp_projects",
    )

    print("✅ YAML-derived episode added")
    print("Graphiti extracts from your YAML documents:")
    print("- Requirement entities with priority, status, effort validation")
    print("- Module entities with complexity levels and dev time estimates")
    print("- Dependency relationships between modules and technologies")


# =============================================================================
# EXAMPLE 4: SEARCHING WITH CUSTOM ENTITY FILTERS
# =============================================================================


async def example_search_with_custom_filters():
    """Example: How to search using custom entity and edge type filters."""

    from graphiti_core.search.search_filters import SearchFilters

    graphiti = GraphitiClient()

    # Search for only specific entity types
    print("\n🔍 SEARCH EXAMPLE 1: Find only team members and their skills")
    team_filter = SearchFilters(
        node_labels=["TeamMember", "Technology"]  # Only return these entity types
    )

    results = await graphiti.search(
        query="Who are the developers working on React components?",
        search_filter=team_filter,
        group_id="techcorp_projects",  # Search within specific namespace
    )

    print("Results will only include TeamMember and Technology entities")

    # Search for specific relationship types
    print("\n🔍 SEARCH EXAMPLE 2: Find project assignments and technology usage")
    relationship_filter = SearchFilters(
        edge_types=["ProjectAssignment", "TechnologyUsage"]  # Only these relationships
    )

    results = await graphiti.search(
        query="Show me team allocation and technology choices for the project",
        search_filter=relationship_filter,
        group_id="techcorp_projects",
    )

    print("Results will focus on assignment and technology relationships")

    # Complex query combining multiple filters
    print("\n🔍 SEARCH EXAMPLE 3: Complex query with validation")
    results = await graphiti.search(
        query="What are the high priority tasks assigned to senior developers?",
        group_id="techcorp_projects",
    )

    print("Graphiti can reason about:")
    print("- Task entities with priority='high' validation")
    print("- TeamMember entities with role matching 'senior'")
    print("- TaskAssignment relationships connecting them")


# =============================================================================
# EXAMPLE 5: INCREMENTAL UPDATES WITH CUSTOM ENTITIES
# =============================================================================


async def example_incremental_project_updates():
    """Example: How custom entities handle incremental project updates."""

    graphiti = GraphitiClient()

    # Initial project status
    initial_update = """
    Project Phoenix Update - Week 1:
    
    Alex Chen completed the development environment setup ahead of schedule.
    Task status changed from 'in_progress' to 'done' on January 19, 2024.
    Actual hours: 12 (estimated was 16 hours).
    
    Maria Rodriguez started working on the user authentication module.
    Her allocation increased from 80% to 100% due to project priority.
    """

    await graphiti.add_episode(
        name="phoenix_week1_update",
        episode_body=initial_update,
        source=EpisodeType.text,
        source_description="Weekly project status update",
        reference_time=datetime(2024, 1, 19, 17, 0),
        entity_types=ENTITY_TYPES,
        edge_types=EDGE_TYPES,
        edge_type_map=EDGE_TYPE_MAP,
        group_id="techcorp_projects",
    )

    # Follow-up update
    followup_update = """
    Project Phoenix Update - Week 2:
    
    New requirement added: REQ-004 - Payment integration with Stripe API.
    Priority: critical, estimated effort: 21 story points.
    
    David Kim joined the project as DevOps Engineer with 40% allocation.
    He will work on AWS infrastructure setup using Docker and Kubernetes.
    
    Technology decision: Switched from Material-UI to Tailwind CSS for frontend.
    Reason: Better performance and smaller bundle size.
    """

    await graphiti.add_episode(
        name="phoenix_week2_update",
        episode_body=followup_update,
        source=EpisodeType.text,
        source_description="Weekly project status update",
        reference_time=datetime(2024, 1, 26, 17, 0),
        entity_types=ENTITY_TYPES,
        edge_types=EDGE_TYPES,
        edge_type_map=EDGE_TYPE_MAP,
        group_id="techcorp_projects",
    )

    print("✅ Incremental updates added")
    print("Graphiti automatically:")
    print("- Updates existing Task entity status and actual_hours")
    print("- Modifies ProjectAssignment allocation_percentage for Maria")
    print("- Creates new TeamMember entity for David Kim")
    print("- Adds new Requirement entity with priority validation")
    print("- Updates Technology relationships (removes Material-UI, adds Tailwind)")
    print("- Maintains temporal history of all changes")


# =============================================================================
# MAIN DEMONSTRATION
# =============================================================================


async def main():
    """Run all examples to demonstrate custom entity usage."""

    print("🚀 GRAPHITI CUSTOM ENTITY EXAMPLES")
    print("=" * 50)

    print("\n1. TEXT EPISODE WITH CUSTOM ENTITIES")
    await example_text_episode_with_custom_entities()

    print("\n2. JSON EPISODE WITH STRUCTURED DATA")
    await example_json_episode_with_project_data()

    print("\n3. YAML-DERIVED EPISODE")
    await example_yaml_episode_with_requirements()

    print("\n4. SEARCHING WITH CUSTOM FILTERS")
    await example_search_with_custom_filters()

    print("\n5. INCREMENTAL UPDATES")
    await example_incremental_project_updates()

    print("\n" + "=" * 50)
    print("✅ All examples completed!")
    print("\nKey Benefits of Custom Entities:")
    print("• Structured data validation with Pydantic")
    print("• Domain-specific attributes (budget, priority, skills)")
    print("• Rich relationship modeling (assignments, dependencies)")
    print("• Temporal tracking of project changes")
    print("• Multi-client isolation with group_ids")
    print("• Powerful filtered search capabilities")


if __name__ == "__main__":
    # Run examples (you'd configure your actual Graphiti client)
    # asyncio.run(main())
    print("Examples ready to run - configure your Graphiti client first!")
