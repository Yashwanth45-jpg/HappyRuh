"""
Recommendation Intent Definitions

This module defines all recommendation and personalization related intents.
"""

from ..models import IntentDefinition
from ..enums import IntentCategory, ActionCode, IntentPriority, EntityType

recommendation_intent_definitions = {
    "get_recommendations": IntentDefinition(
        category=IntentCategory.RECOMMENDATIONS,
        action_code=ActionCode.GET_PERSONALIZED_RECOMMENDATIONS,
        description="User wants personalized product recommendations",
        example_phrases=[
            "What do you recommend?",
            "Show me suggestions",
            "What's popular?",
            "Recommend something for me",
            "What would I like?"
        ],
        required_entities=[],
        optional_entities=[EntityType.CATEGORY, EntityType.BUDGET, EntityType.PREFERENCES],
        confidence_threshold=0.6,
        priority=IntentPriority.MEDIUM
    ),
    
    "add_to_wishlist": IntentDefinition(
        category=IntentCategory.WISHLIST_ADD,
        action_code=ActionCode.ADD_TO_WISHLIST,
        description="User wants to add a product to their wishlist",
        example_phrases=[
            "Add to wishlist",
            "Save for later",
            "I want to remember this",
            "Add to favorites",
            "Wishlist this"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[],
        confidence_threshold=0.7,
        priority=IntentPriority.MEDIUM
    ),
    
    "remove_from_wishlist": IntentDefinition(
        category=IntentCategory.WISHLIST_REMOVE,
        action_code=ActionCode.REMOVE_FROM_WISHLIST,
        description="User wants to remove a product from their wishlist",
        example_phrases=[
            "Remove from wishlist",
            "Delete from favorites",
            "Don't save this",
            "Remove from saved",
            "Unwishlist this"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[],
        confidence_threshold=0.7,
        priority=IntentPriority.MEDIUM
    ),
    
    "view_wishlist": IntentDefinition(
        category=IntentCategory.WISHLIST_VIEW,
        action_code=ActionCode.VIEW_WISHLIST,
        description="User wants to view their wishlist",
        example_phrases=[
            "Show my wishlist",
            "View saved items",
            "My favorites",
            "Saved for later",
            "Wishlist"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.7,
        priority=IntentPriority.MEDIUM
    )
}
