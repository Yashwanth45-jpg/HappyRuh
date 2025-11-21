"""
General Intent Definitions

This module defines all general interaction related intents.
"""

from ..models import IntentDefinition
from ..enums import IntentCategory, ActionCode, IntentPriority, EntityType

general_intent_definitions = {
    "greeting": IntentDefinition(
        category=IntentCategory.GREETING,
        action_code=ActionCode.SEND_GREETING,
        description="User is greeting the assistant",
        example_phrases=[
            "Hello",
            "Hi there",
            "Good morning",
            "Hey",
            "Greetings"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.6,
        priority=IntentPriority.LOW
    ),
    
    "goodbye": IntentDefinition(
        category=IntentCategory.GOODBYE,
        action_code=ActionCode.SEND_GOODBYE,
        description="User is saying goodbye",
        example_phrases=[
            "Goodbye",
            "See you later",
            "Bye",
            "Thanks, that's all",
            "Have a good day"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.6,
        priority=IntentPriority.LOW
    ),
    
    "thanks": IntentDefinition(
        category=IntentCategory.THANKS,
        action_code=ActionCode.SEND_THANKS,
        description="User is expressing gratitude",
        example_phrases=[
            "Thank you",
            "Thanks",
            "Much appreciated",
            "Great, thanks",
            "Perfect, thank you"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.6,
        priority=IntentPriority.LOW
    ),
    
    "clarification": IntentDefinition(
        category=IntentCategory.CLARIFICATION,
        action_code=ActionCode.REQUEST_CLARIFICATION,
        description="User is requesting clarification",
        example_phrases=[
            "Can you explain that?",
            "I don't understand",
            "What do you mean?",
            "Can you clarify?",
            "I'm confused"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.6,
        priority=IntentPriority.MEDIUM
    ),
    
    "unknown": IntentDefinition(
        category=IntentCategory.UNKNOWN,
        action_code=ActionCode.HANDLE_UNKNOWN_INTENT,
        description="User intent could not be determined",
        example_phrases=[
            "I don't understand",
            "What?",
            "Huh?",
            "Can you repeat that?",
            "I'm confused"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.3,
        priority=IntentPriority.FALLBACK
    )
}
