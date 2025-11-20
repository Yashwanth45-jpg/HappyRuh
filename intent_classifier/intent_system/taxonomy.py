"""
Intent Taxonomy

This module provides the main IntentTaxonomy class that manages all intent definitions
and provides methods for intent classification and management.
"""

from typing import Dict, List, Optional, Any
from .models import IntentDefinition, IntentResult, ClassificationRequest, ClassificationResponse
from .enums import IntentCategory, ActionCode, IntentPriority
from .definitions import ALL_INTENT_DEFINITIONS


class IntentTaxonomy:
    """Comprehensive intent taxonomy for the shopping assistant."""
    
    def __init__(self):
        """Initialize the intent taxonomy with all definitions."""
        self.intents = ALL_INTENT_DEFINITIONS
        self.intent_mappings = self._create_intent_mappings()
        self._validate_intents()
    
    def _create_intent_mappings(self) -> Dict[str, str]:
        """Create mappings from example phrases to action codes."""
        mappings = {}
        for intent_name, intent_def in self.intents.items():
            for phrase in intent_def.example_phrases:
                mappings[phrase.lower()] = intent_def.action_code.value
        return mappings
    
    def _validate_intents(self) -> None:
        """Validate all intent definitions."""
        for intent_name, intent_def in self.intents.items():
            if not isinstance(intent_def, IntentDefinition):
                raise ValueError(f"Invalid intent definition for '{intent_name}'")
            
            # Check for duplicate action codes
            action_codes = [def_.action_code for def_ in self.intents.values()]
            if len(action_codes) != len(set(action_codes)):
                raise ValueError("Duplicate action codes found in intent definitions")
    
    def get_intent_by_action_code(self, action_code: str) -> Optional[IntentDefinition]:
        """Get intent definition by action code."""
        for intent_def in self.intents.values():
            if intent_def.action_code.value == action_code:
                return intent_def
        return None
    
    def get_intents_by_category(self, category: IntentCategory) -> List[IntentDefinition]:
        """Get all intents for a specific category."""
        return [intent_def for intent_def in self.intents.values() 
                if intent_def.category == category]
    
    def get_intents_by_priority(self, priority: IntentPriority) -> List[IntentDefinition]:
        """Get all intents for a specific priority level."""
        return [intent_def for intent_def in self.intents.values() 
                if intent_def.priority == priority]
    
    def get_all_categories(self) -> List[IntentCategory]:
        """Get all available intent categories."""
        return list(IntentCategory)
    
    def get_all_action_codes(self) -> List[ActionCode]:
        """Get all available action codes."""
        return list(ActionCode)
    
    def get_example_phrases_for_action(self, action_code: str) -> List[str]:
        """Get example phrases for a specific action code."""
        intent_def = self.get_intent_by_action_code(action_code)
        return intent_def.example_phrases if intent_def else []
    
    def validate_intent(self, intent_name: str) -> bool:
        """Validate if an intent name exists in the taxonomy."""
        return intent_name in self.intents
    
    def get_intent_definition(self, intent_name: str) -> Optional[IntentDefinition]:
        """Get intent definition by name."""
        return self.intents.get(intent_name)
    
    def get_intent_statistics(self) -> Dict[str, Any]:
        """Get statistics about the intent taxonomy."""
        total_intents = len(self.intents)
        categories = {}
        priorities = {}
        
        for intent_def in self.intents.values():
            # Count by category
            category_name = intent_def.category.value
            categories[category_name] = categories.get(category_name, 0) + 1
            
            # Count by priority
            priority_name = intent_def.priority.name
            priorities[priority_name] = priorities.get(priority_name, 0) + 1
        
        return {
            "total_intents": total_intents,
            "total_categories": len(categories),
            "total_action_codes": len(set(def_.action_code for def_ in self.intents.values())),
            "intents_by_category": categories,
            "intents_by_priority": priorities,
            "average_confidence_threshold": sum(def_.confidence_threshold for def_ in self.intents.values()) / total_intents
        }
    
    def search_intents(self, query: str) -> List[IntentDefinition]:
        """Search intents by description or example phrases."""
        query_lower = query.lower()
        matching_intents = []
        
        for intent_def in self.intents.values():
            # Search in description
            if query_lower in intent_def.description.lower():
                matching_intents.append(intent_def)
                continue
            
            # Search in example phrases
            for phrase in intent_def.example_phrases:
                if query_lower in phrase.lower():
                    matching_intents.append(intent_def)
                    break
        
        return matching_intents
    
    def get_related_intents(self, intent_name: str) -> List[IntentDefinition]:
        """Get intents related to the given intent (same category or similar entities)."""
        if intent_name not in self.intents:
            return []
        
        target_intent = self.intents[intent_name]
        related_intents = []
        
        for name, intent_def in self.intents.items():
            if name == intent_name:
                continue
            
            # Same category
            if intent_def.category == target_intent.category:
                related_intents.append(intent_def)
                continue
            
            # Similar entities
            common_entities = set(intent_def.required_entities) & set(target_intent.required_entities)
            if common_entities:
                related_intents.append(intent_def)
        
        return related_intents
    
    def export_intent_definitions(self, format: str = "dict") -> Any:
        """Export intent definitions in various formats."""
        if format == "dict":
            return {
                name: {
                    "category": def_.category.value,
                    "action_code": def_.action_code.value,
                    "description": def_.description,
                    "example_phrases": def_.example_phrases,
                    "required_entities": [e.value for e in def_.required_entities],
                    "optional_entities": [e.value for e in def_.optional_entities],
                    "confidence_threshold": def_.confidence_threshold,
                    "priority": def_.priority.name
                }
                for name, def_ in self.intents.items()
            }
        elif format == "json":
            import json
            return json.dumps(self.export_intent_definitions("dict"), indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global instance for easy access
intent_taxonomy = IntentTaxonomy()


def get_intent_taxonomy() -> IntentTaxonomy:
    """Get the global intent taxonomy instance."""
    return intent_taxonomy


def get_action_code_for_phrase(phrase: str) -> Optional[str]:
    """Get action code for a given phrase."""
    return intent_taxonomy.intent_mappings.get(phrase.lower())


def get_all_intent_categories() -> List[str]:
    """Get all intent category names."""
    return [category.value for category in IntentCategory]


def get_all_action_codes() -> List[str]:
    """Get all action code names."""
    return [action.value for action in ActionCode]


# Export main classes and functions
__all__ = [
    'IntentTaxonomy',
    'intent_taxonomy',
    'get_intent_taxonomy',
    'get_action_code_for_phrase',
    'get_all_intent_categories',
    'get_all_action_codes'
]
