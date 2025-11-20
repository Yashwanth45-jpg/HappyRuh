"""
Cart Intent Definitions

This module defines all shopping cart related intents.
"""

from ..models import IntentDefinition
from ..enums import IntentCategory, ActionCode, IntentPriority, EntityType

cart_intent_definitions = {
    "add_to_cart": IntentDefinition(
        category=IntentCategory.ADD_TO_CART,
        action_code=ActionCode.ADD_ITEM_TO_CART,
        description="User wants to add a product to their shopping cart",
        example_phrases=[
            "Add this to my cart",
            "I want to buy this",
            "Add to cart",
            "Put this in my basket",
            "I'll take this one"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[EntityType.QUANTITY, EntityType.SIZE, EntityType.COLOR],
        confidence_threshold=0.8,
        priority=IntentPriority.HIGH
    ),
    
    "remove_from_cart": IntentDefinition(
        category=IntentCategory.REMOVE_FROM_CART,
        action_code=ActionCode.REMOVE_ITEM_FROM_CART,
        description="User wants to remove a product from their cart",
        example_phrases=[
            "Remove this from my cart",
            "Take this out of my basket",
            "I don't want this anymore",
            "Delete this item",
            "Remove from cart"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[],
        confidence_threshold=0.8,
        priority=IntentPriority.HIGH
    ),
    
    "update_cart": IntentDefinition(
        category=IntentCategory.UPDATE_CART,
        action_code=ActionCode.UPDATE_CART_QUANTITY,
        description="User wants to update quantity of items in cart",
        example_phrases=[
            "Change quantity to 2",
            "I want 3 of these",
            "Update quantity",
            "Make it 5 instead",
            "Change to 1"
        ],
        required_entities=[EntityType.PRODUCT_ID, EntityType.QUANTITY],
        optional_entities=[],
        confidence_threshold=0.8,
        priority=IntentPriority.HIGH
    ),
    
    "view_cart": IntentDefinition(
        category=IntentCategory.VIEW_CART,
        action_code=ActionCode.VIEW_CART_CONTENTS,
        description="User wants to view their shopping cart",
        example_phrases=[
            "Show my cart",
            "What's in my basket?",
            "View cart",
            "Show cart contents",
            "What did I add?"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.7,
        priority=IntentPriority.HIGH
    ),
    
    "clear_cart": IntentDefinition(
        category=IntentCategory.CLEAR_CART,
        action_code=ActionCode.CLEAR_CART_CONTENTS,
        description="User wants to clear all items from their cart",
        example_phrases=[
            "Clear my cart",
            "Empty my basket",
            "Remove everything",
            "Start over",
            "Clear all items"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.8,
        priority=IntentPriority.MEDIUM
    )
}
