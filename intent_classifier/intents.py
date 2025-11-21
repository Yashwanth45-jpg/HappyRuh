"""
Intent Classification Module for ChatNShop

This module provides the main interface for the intent classification system.
It imports and exposes all the necessary components from the modular structure.

Author: AI Development Team
Version: 2.0.0
"""

# Import all components from the intent_system module
from .intent_system.enums import IntentCategory, ActionCode, IntentPriority, EntityType
from .intent_system.models import IntentDefinition, IntentResult, ClassificationRequest, ClassificationResponse
from .intent_system.taxonomy import (
    IntentTaxonomy,
    intent_taxonomy,
    get_intent_taxonomy,
    get_action_code_for_phrase,
    get_all_intent_categories,
    get_all_action_codes
)

# Export all components for backward compatibility
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
    
    # Taxonomy
    'IntentTaxonomy',
    'intent_taxonomy',
    'get_intent_taxonomy',
    'get_action_code_for_phrase',
    'get_all_intent_categories',
    'get_all_action_codes'
]
