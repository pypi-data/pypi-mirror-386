"""
Database schemas for DocVault.

This package contains Pydantic models for all database entities.
"""

from .acl import DocumentACL, DocumentACLBase, DocumentACLCreate, DocumentACLUpdate
from .agent import Agent, AgentBase, AgentCreate, AgentUpdate
from .document import Document, DocumentBase, DocumentCreate, DocumentUpdate
from .organization import (
    Organization,
    OrganizationBase,
    OrganizationCreate,
    OrganizationUpdate,
)
from .version import (
    DocumentVersion,
    DocumentVersionBase,
    DocumentVersionCreate,
    DocumentVersionUpdate,
)

__all__ = [
    # Organization schemas
    "Organization",
    "OrganizationBase",
    "OrganizationCreate",
    "OrganizationUpdate",
    # Agent schemas
    "Agent",
    "AgentBase",
    "AgentCreate",
    "AgentUpdate",
    # Document schemas
    "Document",
    "DocumentBase",
    "DocumentCreate",
    "DocumentUpdate",
    # DocumentVersion schemas
    "DocumentVersion",
    "DocumentVersionBase",
    "DocumentVersionCreate",
    "DocumentVersionUpdate",
    # DocumentACL schemas
    "DocumentACL",
    "DocumentACLBase",
    "DocumentACLCreate",
    "DocumentACLUpdate",
]
