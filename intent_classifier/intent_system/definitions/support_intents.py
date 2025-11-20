"""
Support Intent Definitions

This module defines all customer support and help related intents.
"""

from ..models import IntentDefinition
from ..enums import IntentCategory, ActionCode, IntentPriority, EntityType

support_intent_definitions = {
    "faq": IntentDefinition(
        category=IntentCategory.FAQ,
        action_code=ActionCode.GET_FAQ_ANSWER,
        description="User has a frequently asked question",
        example_phrases=[
            "How do I return an item?",
            "What's your return policy?",
            "How long does shipping take?",
            "Do you offer free shipping?",
            "What payment methods do you accept?"
        ],
        required_entities=[EntityType.QUESTION],
        optional_entities=[EntityType.TOPIC],
        confidence_threshold=0.7,
        priority=IntentPriority.MEDIUM
    ),
    
    "contact_support": IntentDefinition(
        category=IntentCategory.CONTACT_SUPPORT,
        action_code=ActionCode.CONTACT_CUSTOMER_SUPPORT,
        description="User wants to contact customer support",
        example_phrases=[
            "I need help",
            "Contact support",
            "Speak to someone",
            "I have a problem",
            "Customer service"
        ],
        required_entities=[],
        optional_entities=[EntityType.ISSUE_TYPE, EntityType.URGENCY],
        confidence_threshold=0.7,
        priority=IntentPriority.HIGH
    ),
    
    "complaint": IntentDefinition(
        category=IntentCategory.COMPLAINT,
        action_code=ActionCode.SUBMIT_COMPLAINT,
        description="User wants to submit a complaint",
        example_phrases=[
            "I want to complain",
            "Submit a complaint",
            "I'm not satisfied",
            "This is unacceptable",
            "File a complaint"
        ],
        required_entities=[],
        optional_entities=[EntityType.REASON, EntityType.URGENCY],
        confidence_threshold=0.8,
        priority=IntentPriority.HIGH
    ),
    
    "return_item": IntentDefinition(
        category=IntentCategory.RETURN_ITEM,
        action_code=ActionCode.INITIATE_RETURN,
        description="User wants to return a purchased item",
        example_phrases=[
            "I want to return this",
            "How do I return an item?",
            "Return policy",
            "I need to send this back",
            "Return request"
        ],
        required_entities=[EntityType.ORDER_ID],
        optional_entities=[EntityType.REASON],
        confidence_threshold=0.8,
        priority=IntentPriority.HIGH
    ),
    
    "refund": IntentDefinition(
        category=IntentCategory.REFUND,
        action_code=ActionCode.REQUEST_REFUND,
        description="User wants to request a refund",
        example_phrases=[
            "I want a refund",
            "Request refund",
            "Give me my money back",
            "Refund this purchase",
            "Cancel and refund"
        ],
        required_entities=[EntityType.ORDER_ID],
        optional_entities=[EntityType.REASON],
        confidence_threshold=0.8,
        priority=IntentPriority.HIGH
    )
}
