"""
Intent System Module

This module contains all intent definitions, taxonomy, and related components
for the ChatNShop intent classification system.

Components:
- enums: Intent categories, action codes, and entity types
- models: Data structures for intent definitions and classification
- taxonomy: Main intent taxonomy class and business logic
- definitions: Intent definitions organized by domain
- keywords: Keyword data for intent classification
"""

from .enums import IntentCategory, ActionCode, IntentPriority, EntityType
from .models import (
    IntentDefinition,
    IntentResult,
    ClassificationRequest,
    ClassificationResponse,
    EntityExtraction,
    IntentMetrics
)
from .taxonomy import (
    IntentTaxonomy,
    intent_taxonomy,
    get_intent_taxonomy,
    get_action_code_for_phrase,
    get_all_intent_categories,
    get_all_action_codes
)
from .definitions import ALL_INTENT_DEFINITIONS

__all__ = [
    # Enums
    'IntentCategory',
    'ActionCode',
    'IntentPriority',
    'EntityType',
    
    # Models
    'IntentDefinition',
    'IntentResult',
    'ClassificationRequest',
    'ClassificationResponse',
    'EntityExtraction',
    'IntentMetrics',
    
    # Taxonomy
    'IntentTaxonomy',
    'intent_taxonomy',
    'get_intent_taxonomy',
    'get_action_code_for_phrase',
    'get_all_intent_categories',
    'get_all_action_codes',
    
    # Definitions
    'ALL_INTENT_DEFINITIONS'
]

__version__ = "2.0.0"
__author__ = "AI Development Team"
