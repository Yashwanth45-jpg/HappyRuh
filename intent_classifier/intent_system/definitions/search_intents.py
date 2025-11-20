"""
Search Intent Definitions

This module defines all search and product discovery related intents.
"""

from ..models import IntentDefinition
from ..enums import IntentCategory, ActionCode, IntentPriority, EntityType

search_intent_definitions = {
    "search_products": IntentDefinition(
        category=IntentCategory.SEARCH,
        action_code=ActionCode.SEARCH_PRODUCTS,
        description="User wants to search for products",
        example_phrases=[
            "I'm looking for a laptop",
            "Show me smartphones",
            "Find me running shoes",
            "Search for wireless headphones",
            "I need a coffee maker"
        ],
        required_entities=[EntityType.PRODUCT_QUERY],
        optional_entities=[EntityType.CATEGORY, EntityType.BRAND, EntityType.PRICE_RANGE],
        confidence_threshold=0.7,
        priority=IntentPriority.HIGH
    ),
    
    "search_by_category": IntentDefinition(
        category=IntentCategory.SEARCH,
        action_code=ActionCode.SEARCH_BY_CATEGORY,
        description="User wants to search within a specific category",
        example_phrases=[
            "Show me electronics",
            "I want to see clothing",
            "Browse home and garden",
            "What's in the sports section?",
            "Show me beauty products"
        ],
        required_entities=[EntityType.CATEGORY],
        optional_entities=[EntityType.BRAND, EntityType.PRICE_RANGE],
        confidence_threshold=0.7,
        priority=IntentPriority.HIGH
    ),
    
    "get_product_info": IntentDefinition(
        category=IntentCategory.PRODUCT_INFO,
        action_code=ActionCode.GET_PRODUCT_DETAILS,
        description="User wants detailed information about a specific product",
        example_phrases=[
            "Tell me about this iPhone",
            "What are the specs of this laptop?",
            "Show me product details",
            "What's the warranty on this?",
            "Is this product in stock?"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[],
        confidence_threshold=0.8,
        priority=IntentPriority.HIGH
    ),
    
    "browse_products": IntentDefinition(
        category=IntentCategory.BROWSE,
        action_code=ActionCode.BROWSE_CATEGORIES,
        description="User wants to browse products without specific search criteria",
        example_phrases=[
            "What's new?",
            "Show me what's popular",
            "Browse deals",
            "What's trending?",
            "Show me featured products"
        ],
        required_entities=[],
        optional_entities=[EntityType.CATEGORY],
        confidence_threshold=0.6,
        priority=IntentPriority.MEDIUM
    ),
    
    "filter_products": IntentDefinition(
        category=IntentCategory.FILTER,
        action_code=ActionCode.APPLY_FILTERS,
        description="User wants to apply filters to product results",
        example_phrases=[
            "Filter by price under $100",
            "Show only red items",
            "Filter by brand Apple",
            "Show items with free shipping",
            "Filter by rating 4+ stars"
        ],
        required_entities=[EntityType.FILTER_CRITERIA],
        optional_entities=[],
        confidence_threshold=0.7,
        priority=IntentPriority.MEDIUM
    ),
    
    "sort_products": IntentDefinition(
        category=IntentCategory.SORT,
        action_code=ActionCode.SORT_PRODUCTS,
        description="User wants to sort product results",
        example_phrases=[
            "Sort by price low to high",
            "Show cheapest first",
            "Sort by newest",
            "Sort by rating",
            "Sort by popularity"
        ],
        required_entities=[EntityType.SORT_CRITERIA],
        optional_entities=[],
        confidence_threshold=0.7,
        priority=IntentPriority.MEDIUM
    ),
    
    "compare_products": IntentDefinition(
        category=IntentCategory.COMPARE,
        action_code=ActionCode.COMPARE_PRODUCTS,
        description="User wants to compare multiple products",
        example_phrases=[
            "Compare these two laptops",
            "Show me differences between these phones",
            "Which is better between these options?",
            "Compare features",
            "Side by side comparison"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[],
        confidence_threshold=0.8,
        priority=IntentPriority.MEDIUM
    )
}
