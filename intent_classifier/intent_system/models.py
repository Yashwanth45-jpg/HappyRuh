"""
Intent Classification Models

This module defines data models and structures used in the intent classification system.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from .enums import IntentCategory, ActionCode, IntentPriority, EntityType


@dataclass
class IntentDefinition:
    """Data class for intent definitions with metadata."""
    
    category: IntentCategory
    action_code: ActionCode
    description: str
    example_phrases: List[str]
    required_entities: List[EntityType]
    optional_entities: List[EntityType]
    confidence_threshold: float = 0.7
    priority: IntentPriority = IntentPriority.MEDIUM
    
    def __post_init__(self):
        """Validate the intent definition after initialization."""
        if not self.example_phrases:
            raise ValueError("Intent definition must have at least one example phrase")
        
        if self.confidence_threshold < 0.0 or self.confidence_threshold > 1.0:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")


@dataclass
class IntentResult:
    """Result of intent classification."""
    
    intent_name: str
    action_code: ActionCode
    confidence_score: float
    extracted_entities: Dict[str, Any]
    processing_time_ms: float
    metadata: Optional[Dict[str, Any]] = None
    
    def is_confident(self, threshold: float = 0.7) -> bool:
        """Check if the result meets the confidence threshold."""
        return self.confidence_score >= threshold
    
    def get_required_entities(self) -> List[str]:
        """Get list of required entities that were extracted."""
        return list(self.extracted_entities.keys())


@dataclass
class EntityExtraction:
    """Result of entity extraction from user input."""
    
    entity_type: EntityType
    value: Any
    confidence: float
    start_position: int
    end_position: int
    original_text: str
    
    def __post_init__(self):
        """Validate entity extraction result."""
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("Entity confidence must be between 0.0 and 1.0")
        
        if self.start_position < 0 or self.end_position < self.start_position:
            raise ValueError("Invalid position range")


@dataclass
class ClassificationRequest:
    """Request for intent classification."""
    
    user_input: str
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        """Validate classification request."""
        if not self.user_input or not self.user_input.strip():
            raise ValueError("User input cannot be empty")


@dataclass
class ClassificationResponse:
    """Response from intent classification."""
    
    primary_intent: IntentResult
    alternative_intents: List[IntentResult]
    entities: List[EntityExtraction]
    requires_clarification: bool
    clarification_message: Optional[str] = None
    processing_metadata: Optional[Dict[str, Any]] = None
    
    def get_best_intent(self, threshold: float = 0.7) -> Optional[IntentResult]:
        """Get the best intent that meets the confidence threshold."""
        if self.primary_intent.is_confident(threshold):
            return self.primary_intent
        
        for alt_intent in self.alternative_intents:
            if alt_intent.is_confident(threshold):
                return alt_intent
        
        return None
    
    def get_all_confident_intents(self, threshold: float = 0.7) -> List[IntentResult]:
        """Get all intents that meet the confidence threshold."""
        confident_intents = []
        
        if self.primary_intent.is_confident(threshold):
            confident_intents.append(self.primary_intent)
        
        for alt_intent in self.alternative_intents:
            if alt_intent.is_confident(threshold):
                confident_intents.append(alt_intent)
        
        return confident_intents


@dataclass
class IntentMetrics:
    """Metrics for intent classification performance."""
    
    total_requests: int
    successful_classifications: int
    average_confidence: float
    average_processing_time_ms: float
    most_common_intents: Dict[str, int]
    error_rate: float
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate of classifications."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_classifications / self.total_requests
