"""
Account Intent Definitions

This module defines all user account and profile related intents.
"""

from ..models import IntentDefinition
from ..enums import IntentCategory, ActionCode, IntentPriority, EntityType

account_intent_definitions = {
    "login": IntentDefinition(
        category=IntentCategory.LOGIN,
        action_code=ActionCode.USER_LOGIN,
        description="User wants to log into their account",
        example_phrases=[
            "I want to login",
            "Sign me in",
            "Log into my account",
            "Access my account",
            "Login"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.8,
        priority=IntentPriority.HIGH
    ),
    
    "logout": IntentDefinition(
        category=IntentCategory.LOGOUT,
        action_code=ActionCode.USER_LOGOUT,
        description="User wants to log out of their account",
        example_phrases=[
            "I want to logout",
            "Sign me out",
            "Log out of my account",
            "Exit my account",
            "Logout"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.8,
        priority=IntentPriority.MEDIUM
    ),
    
    "register": IntentDefinition(
        category=IntentCategory.REGISTER,
        action_code=ActionCode.USER_REGISTER,
        description="User wants to create a new account",
        example_phrases=[
            "I want to register",
            "Create an account",
            "Sign up",
            "Register new account",
            "Join"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.8,
        priority=IntentPriority.HIGH
    ),
    
    "view_profile": IntentDefinition(
        category=IntentCategory.VIEW_PROFILE,
        action_code=ActionCode.VIEW_USER_PROFILE,
        description="User wants to view their profile information",
        example_phrases=[
            "Show my profile",
            "View my account",
            "My profile information",
            "Account details",
            "Profile"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.7,
        priority=IntentPriority.MEDIUM
    ),
    
    "update_profile": IntentDefinition(
        category=IntentCategory.UPDATE_PROFILE,
        action_code=ActionCode.UPDATE_USER_PROFILE,
        description="User wants to update their profile information",
        example_phrases=[
            "Update my profile",
            "Change my information",
            "Edit my account",
            "Modify profile",
            "Update account"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.8,
        priority=IntentPriority.MEDIUM
    ),
    
    "view_orders": IntentDefinition(
        category=IntentCategory.VIEW_ORDERS,
        action_code=ActionCode.VIEW_ORDER_HISTORY,
        description="User wants to view their order history",
        example_phrases=[
            "Show my orders",
            "View order history",
            "What did I buy before?",
            "My past purchases",
            "Order history"
        ],
        required_entities=[],
        optional_entities=[EntityType.DATE_RANGE],
        confidence_threshold=0.7,
        priority=IntentPriority.MEDIUM
    ),
    
    "track_order": IntentDefinition(
        category=IntentCategory.TRACK_ORDER,
        action_code=ActionCode.TRACK_ORDER_STATUS,
        description="User wants to track the status of an order",
        example_phrases=[
            "Where is my order?",
            "Track my package",
            "Order status",
            "When will it arrive?",
            "Shipping status"
        ],
        required_entities=[EntityType.ORDER_ID],
        optional_entities=[],
        confidence_threshold=0.8,
        priority=IntentPriority.HIGH
    )
}
