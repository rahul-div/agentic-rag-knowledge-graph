"""
Custom Entity and Edge Types for Project Management Knowledge Graph

This file defines Pydantic models for project management entities and relationships,
following Graphiti best practices from the official documentation.
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
from enum import Enum

# =============================================================================
# ENUMS FOR VALIDATION
# =============================================================================


class ProjectStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    BLOCKED = "blocked"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TechnologyCategory(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    DEVOPS = "devops"
    MOBILE = "mobile"
    AI_ML = "ai_ml"
    TESTING = "testing"


# =============================================================================
# CUSTOM ENTITY TYPES
# =============================================================================


class Client(BaseModel):
    """A client or customer organization."""

    industry: Optional[str] = Field(None, description="Primary industry sector")
    company_size: Optional[str] = Field(
        None, description="Company size (startup, small, medium, large, enterprise)"
    )
    location: Optional[str] = Field(
        None, description="Primary location or headquarters"
    )
    contract_value: Optional[float] = Field(
        None, description="Total contract value in USD"
    )
    client_since: Optional[datetime] = Field(
        None, description="Date when client relationship started"
    )
    primary_contact: Optional[str] = Field(
        None, description="Name of primary contact person"
    )

    @validator("contract_value")
    def validate_contract_value(cls, v):
        if v is not None and v < 0:
            raise ValueError("Contract value must be non-negative")
        return v


class Project(BaseModel):
    """A software development project."""

    status: Optional[ProjectStatus] = Field(None, description="Current project status")
    budget: Optional[float] = Field(None, description="Project budget in USD")
    start_date: Optional[datetime] = Field(None, description="Project start date")
    end_date: Optional[datetime] = Field(
        None, description="Project end date or deadline"
    )
    project_type: Optional[str] = Field(
        None, description="Type of project (web app, mobile app, API, etc.)"
    )
    methodology: Optional[str] = Field(
        None, description="Development methodology (agile, waterfall, etc.)"
    )
    team_size: Optional[int] = Field(None, description="Number of team members")
    complexity_score: Optional[int] = Field(
        None, description="Project complexity on scale 1-10"
    )

    @validator("budget")
    def validate_budget(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Budget must be positive")
        return v

    @validator("complexity_score")
    def validate_complexity(cls, v):
        if v is not None and (v < 1 or v > 10):
            raise ValueError("Complexity score must be between 1 and 10")
        return v


class TeamMember(BaseModel):
    """A team member working on projects."""

    role: Optional[str] = Field(
        None, description="Primary role (developer, designer, PM, etc.)"
    )
    experience_years: Optional[int] = Field(
        None, description="Years of professional experience"
    )
    hourly_rate: Optional[float] = Field(None, description="Hourly billing rate in USD")
    availability: Optional[float] = Field(
        None, description="Availability percentage (0.0 to 1.0)"
    )
    location: Optional[str] = Field(None, description="Team member location")
    employment_type: Optional[str] = Field(
        None, description="Employment type (full-time, part-time, contractor)"
    )
    skills: Optional[str] = Field(
        None, description="Comma-separated list of key skills"
    )

    @validator("experience_years")
    def validate_experience(cls, v):
        if v is not None and (v < 0 or v > 50):
            raise ValueError("Experience years must be between 0 and 50")
        return v

    @validator("availability")
    def validate_availability(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError("Availability must be between 0.0 and 1.0")
        return v


class Technology(BaseModel):
    """A technology, framework, or tool used in projects."""

    category: Optional[TechnologyCategory] = Field(
        None, description="Technology category"
    )
    version: Optional[str] = Field(None, description="Specific version if applicable")
    learning_curve: Optional[str] = Field(
        None, description="Learning difficulty (easy, medium, hard)"
    )
    popularity_score: Optional[int] = Field(None, description="Popularity score 1-10")
    license_type: Optional[str] = Field(
        None, description="License type (open source, commercial, etc.)"
    )
    last_updated: Optional[datetime] = Field(
        None, description="When technology was last updated"
    )

    @validator("popularity_score")
    def validate_popularity(cls, v):
        if v is not None and (v < 1 or v > 10):
            raise ValueError("Popularity score must be between 1 and 10")
        return v


class Task(BaseModel):
    """A specific task within a project."""

    status: Optional[TaskStatus] = Field(None, description="Current task status")
    priority: Optional[Priority] = Field(None, description="Task priority level")
    estimated_hours: Optional[float] = Field(
        None, description="Estimated hours to complete"
    )
    actual_hours: Optional[float] = Field(None, description="Actual hours spent")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    completed_date: Optional[datetime] = Field(
        None, description="Date when task was completed"
    )
    story_points: Optional[int] = Field(None, description="Agile story points")
    epic: Optional[str] = Field(
        None, description="Epic or feature this task belongs to"
    )

    @validator("estimated_hours", "actual_hours")
    def validate_hours(cls, v):
        if v is not None and v < 0:
            raise ValueError("Hours must be non-negative")
        return v

    @validator("story_points")
    def validate_story_points(cls, v):
        if v is not None and (v < 1 or v > 21):
            raise ValueError("Story points must be between 1 and 21")
        return v


class Requirement(BaseModel):
    """A project requirement specification."""

    requirement_type: Optional[str] = Field(
        None, description="Type (functional, non-functional, business)"
    )
    priority: Optional[Priority] = Field(None, description="Requirement priority")
    status: Optional[str] = Field(
        None, description="Status (draft, approved, implemented, tested)"
    )
    acceptance_criteria: Optional[str] = Field(
        None, description="Acceptance criteria description"
    )
    estimated_effort: Optional[float] = Field(
        None, description="Estimated effort in story points"
    )
    source: Optional[str] = Field(
        None, description="Source of requirement (client, stakeholder, etc.)"
    )


class Module(BaseModel):
    """A software module or component."""

    module_type: Optional[str] = Field(
        None, description="Type (frontend, backend, API, database, etc.)"
    )
    complexity: Optional[str] = Field(
        None, description="Complexity level (low, medium, high)"
    )
    dependencies: Optional[str] = Field(
        None, description="Comma-separated list of dependencies"
    )
    estimated_dev_time: Optional[float] = Field(
        None, description="Estimated development time in weeks"
    )
    testing_effort: Optional[float] = Field(
        None, description="Testing effort as percentage of dev time"
    )
    documentation_status: Optional[str] = Field(
        None, description="Documentation status"
    )


# =============================================================================
# CUSTOM EDGE TYPES (RELATIONSHIPS)
# =============================================================================


class ProjectAssignment(BaseModel):
    """Assignment of team member to project."""

    role_in_project: Optional[str] = Field(
        None, description="Specific role in this project"
    )
    allocation_percentage: Optional[float] = Field(
        None, description="Percentage of time allocated (0.0 to 1.0)"
    )
    start_date: Optional[datetime] = Field(None, description="Assignment start date")
    end_date: Optional[datetime] = Field(None, description="Assignment end date")
    hourly_rate: Optional[float] = Field(
        None, description="Project-specific hourly rate"
    )

    @validator("allocation_percentage")
    def validate_allocation(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError("Allocation percentage must be between 0.0 and 1.0")
        return v


class TaskAssignment(BaseModel):
    """Assignment of task to team member."""

    assigned_date: Optional[datetime] = Field(
        None, description="Date when task was assigned"
    )
    estimated_completion: Optional[datetime] = Field(
        None, description="Estimated completion date"
    )
    assignment_notes: Optional[str] = Field(
        None, description="Additional notes about assignment"
    )


class TechnologyUsage(BaseModel):
    """Usage of technology in project or module."""

    usage_type: Optional[str] = Field(
        None, description="How technology is used (primary, secondary, optional)"
    )
    implementation_date: Optional[datetime] = Field(
        None, description="When technology was implemented"
    )
    performance_rating: Optional[int] = Field(
        None, description="Performance rating 1-10"
    )
    maintenance_effort: Optional[str] = Field(
        None, description="Maintenance effort (low, medium, high)"
    )

    @validator("performance_rating")
    def validate_performance(cls, v):
        if v is not None and (v < 1 or v > 10):
            raise ValueError("Performance rating must be between 1 and 10")
        return v


class ClientProject(BaseModel):
    """Relationship between client and project."""

    contract_type: Optional[str] = Field(
        None, description="Contract type (fixed price, time & material, etc.)"
    )
    payment_schedule: Optional[str] = Field(
        None, description="Payment schedule description"
    )
    satisfaction_score: Optional[int] = Field(
        None, description="Client satisfaction score 1-10"
    )
    renewal_probability: Optional[float] = Field(
        None, description="Probability of contract renewal (0.0 to 1.0)"
    )

    @validator("satisfaction_score")
    def validate_satisfaction(cls, v):
        if v is not None and (v < 1 or v > 10):
            raise ValueError("Satisfaction score must be between 1 and 10")
        return v


class Dependency(BaseModel):
    """Dependency relationship between tasks, modules, or projects."""

    dependency_type: Optional[str] = Field(
        None, description="Type (blocks, requires, follows, etc.)"
    )
    criticality: Optional[str] = Field(
        None, description="Criticality level (low, medium, high, critical)"
    )
    created_date: Optional[datetime] = Field(
        None, description="When dependency was identified"
    )
    resolved_date: Optional[datetime] = Field(
        None, description="When dependency was resolved"
    )


# =============================================================================
# ENTITY AND EDGE TYPE MAPPINGS FOR GRAPHITI
# =============================================================================

# Entity types dictionary for Graphiti
ENTITY_TYPES = {
    "Client": Client,
    "Project": Project,
    "TeamMember": TeamMember,
    "Technology": Technology,
    "Task": Task,
    "Requirement": Requirement,
    "Module": Module,
}

# Edge types dictionary for Graphiti
EDGE_TYPES = {
    "ProjectAssignment": ProjectAssignment,
    "TaskAssignment": TaskAssignment,
    "TechnologyUsage": TechnologyUsage,
    "ClientProject": ClientProject,
    "Dependency": Dependency,
}

# Edge type mapping - defines which relationships can exist between entity types
EDGE_TYPE_MAP = {
    # Client relationships
    ("Client", "Project"): ["ClientProject"],
    ("Client", "TeamMember"): [
        "ProjectAssignment"
    ],  # Client can work directly with team members
    # Project relationships
    ("Project", "TeamMember"): ["ProjectAssignment"],
    ("Project", "Technology"): ["TechnologyUsage"],
    ("Project", "Task"): ["Dependency"],  # Projects contain tasks
    ("Project", "Requirement"): ["Dependency"],  # Projects implement requirements
    ("Project", "Module"): ["Dependency"],  # Projects contain modules
    ("Project", "Project"): ["Dependency"],  # Project dependencies
    # Team member relationships
    ("TeamMember", "Task"): ["TaskAssignment"],
    ("TeamMember", "Technology"): ["TechnologyUsage"],  # Team members have tech skills
    ("TeamMember", "Module"): ["ProjectAssignment"],  # Team members work on modules
    # Task relationships
    ("Task", "Task"): ["Dependency"],
    ("Task", "Technology"): ["TechnologyUsage"],
    ("Task", "Module"): ["Dependency"],  # Tasks belong to modules
    ("Task", "Requirement"): ["Dependency"],  # Tasks implement requirements
    # Module relationships
    ("Module", "Module"): ["Dependency"],
    ("Module", "Technology"): ["TechnologyUsage"],
    ("Module", "Requirement"): ["Dependency"],  # Modules implement requirements
    # Technology relationships
    ("Technology", "Technology"): ["Dependency"],  # Tech dependencies
    # Requirement relationships
    ("Requirement", "Requirement"): ["Dependency"],
    # Generic fallback for any entity relationships not explicitly defined
    ("Entity", "Entity"): ["Dependency"],
}

# Excluded entity types (things we don't want to extract as separate entities)
# Since we have custom entities, we only include what we specifically want
# If we want to exclude any of our custom entities, we can list them here
EXCLUDED_ENTITY_TYPES = [
    # "Entity",  # Generic entity type - uncomment to exclude if needed
    # "Module",  # Software modules - uncomment to exclude if needed
]
