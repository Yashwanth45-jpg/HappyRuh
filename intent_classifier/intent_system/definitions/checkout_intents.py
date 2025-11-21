"""
Checkout Intent Definitions

This module defines all checkout and purchase related intents.
"""

from ..models import IntentDefinition
from ..enums import IntentCategory, ActionCode, IntentPriority, EntityType

checkout_intent_definitions = {
    "checkout": IntentDefinition(
        category=IntentCategory.CHECKOUT,
        action_code=ActionCode.INITIATE_CHECKOUT,
        description="User wants to proceed to checkout",
        example_phrases=[
            "I'm ready to checkout",
            "Proceed to payment",
            "Buy now",
            "Complete purchase",
            "Checkout"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.9,
        priority=IntentPriority.CRITICAL
    ),
    
    "apply_coupon": IntentDefinition(
        category=IntentCategory.APPLY_COUPON,
        action_code=ActionCode.APPLY_DISCOUNT_CODE,
        description="User wants to apply a discount code or coupon",
        example_phrases=[
            "Apply coupon code SAVE20",
            "Use my discount code",
            "Apply promo code",
            "I have a coupon",
            "Enter discount code"
        ],
        required_entities=[EntityType.COUPON_CODE],
        optional_entities=[],
        confidence_threshold=0.8,
        priority=IntentPriority.HIGH
    ),
    
    "remove_coupon": IntentDefinition(
        category=IntentCategory.REMOVE_COUPON,
        action_code=ActionCode.REMOVE_DISCOUNT_CODE,
        description="User wants to remove an applied discount code",
        example_phrases=[
            "Remove the coupon",
            "Take off the discount",
            "Remove discount code",
            "Cancel the coupon"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.8,
        priority=IntentPriority.MEDIUM
    ),
    
    "select_payment": IntentDefinition(
        category=IntentCategory.SELECT_PAYMENT,
        action_code=ActionCode.SELECT_PAYMENT_METHOD,
        description="User wants to select or change payment method",
        example_phrases=[
            "I want to pay with credit card",
            "Use PayPal",
            "Pay with Apple Pay",
            "Change payment method",
            "Select payment option"
        ],
        required_entities=[EntityType.PAYMENT_METHOD],
        optional_entities=[],
        confidence_threshold=0.9,
        priority=IntentPriority.CRITICAL
    ),
    
    "select_shipping": IntentDefinition(
        category=IntentCategory.SELECT_SHIPPING,
        action_code=ActionCode.SELECT_SHIPPING_METHOD,
        description="User wants to select shipping method",
        example_phrases=[
            "I want standard shipping",
            "Use express delivery",
            "Select shipping method",
            "Change shipping option",
            "Free shipping please"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.8,
        priority=IntentPriority.HIGH
    )
}
