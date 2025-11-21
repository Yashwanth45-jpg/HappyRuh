"""
Intent Definitions Package

This package contains all intent definitions organized by category.
Each module focuses on a specific domain of intents.
"""

from .search_intents import search_intent_definitions
from .cart_intents import cart_intent_definitions
from .checkout_intents import checkout_intent_definitions
from .account_intents import account_intent_definitions
from .support_intents import support_intent_definitions
from .recommendation_intents import recommendation_intent_definitions
from .general_intents import general_intent_definitions

# Combine all intent definitions
ALL_INTENT_DEFINITIONS = {
    **search_intent_definitions,
    **cart_intent_definitions,
    **checkout_intent_definitions,
    **account_intent_definitions,
    **support_intent_definitions,
    **recommendation_intent_definitions,
    **general_intent_definitions
}

__all__ = [
    'search_intent_definitions',
    'cart_intent_definitions', 
    'checkout_intent_definitions',
    'account_intent_definitions',
    'support_intent_definitions',
    'recommendation_intent_definitions',
    'general_intent_definitions',
    'ALL_INTENT_DEFINITIONS'
]
