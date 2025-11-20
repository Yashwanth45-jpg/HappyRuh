"""
Intent Classification Enums

This module defines all enums used in the intent classification system.
Separated for better organization and reusability.
"""

from enum import Enum


class IntentCategory(Enum):
    """Main intent categories for the shopping assistant."""
    
    # Product Discovery & Search
    SEARCH = "SEARCH"
    PRODUCT_INFO = "PRODUCT_INFO"
    BROWSE = "BROWSE"
    FILTER = "FILTER"
    SORT = "SORT"
    COMPARE = "COMPARE"
    
    # Shopping Cart Operations
    ADD_TO_CART = "ADD_TO_CART"
    REMOVE_FROM_CART = "REMOVE_FROM_CART"
    UPDATE_CART = "UPDATE_CART"
    VIEW_CART = "VIEW_CART"
    CLEAR_CART = "CLEAR_CART"
    
    # Checkout & Purchase
    CHECKOUT = "CHECKOUT"
    APPLY_COUPON = "APPLY_COUPON"
    REMOVE_COUPON = "REMOVE_COUPON"
    SELECT_PAYMENT = "SELECT_PAYMENT"
    SELECT_SHIPPING = "SELECT_SHIPPING"
    
    # User Account & Preferences
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    REGISTER = "REGISTER"
    VIEW_PROFILE = "VIEW_PROFILE"
    UPDATE_PROFILE = "UPDATE_PROFILE"
    VIEW_ORDERS = "VIEW_ORDERS"
    TRACK_ORDER = "TRACK_ORDER"
    
    # Customer Support & Help
    FAQ = "FAQ"
    CONTACT_SUPPORT = "CONTACT_SUPPORT"
    COMPLAINT = "COMPLAINT"
    RETURN_ITEM = "RETURN_ITEM"
    REFUND = "REFUND"
    
    # Recommendations & Personalization
    RECOMMENDATIONS = "RECOMMENDATIONS"
    WISHLIST_ADD = "WISHLIST_ADD"
    WISHLIST_REMOVE = "WISHLIST_REMOVE"
    WISHLIST_VIEW = "WISHLIST_VIEW"
    
    # General Interaction
    GREETING = "GREETING"
    GOODBYE = "GOODBYE"
    THANKS = "THANKS"
    CLARIFICATION = "CLARIFICATION"
    UNKNOWN = "UNKNOWN"


class ActionCode(Enum):
    """Standardized action codes for each intent."""
    
    # Product Discovery & Search Actions
    SEARCH_PRODUCTS = "SEARCH_PRODUCTS"
    SEARCH_BY_CATEGORY = "SEARCH_BY_CATEGORY"
    SEARCH_BY_BRAND = "SEARCH_BY_BRAND"
    SEARCH_BY_PRICE_RANGE = "SEARCH_BY_PRICE_RANGE"
    GET_PRODUCT_DETAILS = "GET_PRODUCT_DETAILS"
    GET_PRODUCT_REVIEWS = "GET_PRODUCT_REVIEWS"
    GET_PRODUCT_AVAILABILITY = "GET_PRODUCT_AVAILABILITY"
    BROWSE_CATEGORIES = "BROWSE_CATEGORIES"
    BROWSE_DEALS = "BROWSE_DEALS"
    BROWSE_NEW_ARRIVALS = "BROWSE_NEW_ARRIVALS"
    APPLY_FILTERS = "APPLY_FILTERS"
    CLEAR_FILTERS = "CLEAR_FILTERS"
    SORT_PRODUCTS = "SORT_PRODUCTS"
    COMPARE_PRODUCTS = "COMPARE_PRODUCTS"
    
    # Shopping Cart Actions
    ADD_ITEM_TO_CART = "ADD_ITEM_TO_CART"
    REMOVE_ITEM_FROM_CART = "REMOVE_ITEM_FROM_CART"
    UPDATE_CART_QUANTITY = "UPDATE_CART_QUANTITY"
    VIEW_CART_CONTENTS = "VIEW_CART_CONTENTS"
    CLEAR_CART_CONTENTS = "CLEAR_CART_CONTENTS"
    GET_CART_SUBTOTAL = "GET_CART_SUBTOTAL"
    GET_CART_TOTAL = "GET_CART_TOTAL"
    
    # Checkout & Purchase Actions
    INITIATE_CHECKOUT = "INITIATE_CHECKOUT"
    APPLY_DISCOUNT_CODE = "APPLY_DISCOUNT_CODE"
    REMOVE_DISCOUNT_CODE = "REMOVE_DISCOUNT_CODE"
    SELECT_PAYMENT_METHOD = "SELECT_PAYMENT_METHOD"
    SELECT_SHIPPING_METHOD = "SELECT_SHIPPING_METHOD"
    CONFIRM_ORDER = "CONFIRM_ORDER"
    CANCEL_ORDER = "CANCEL_ORDER"
    
    # User Account Actions
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    USER_REGISTER = "USER_REGISTER"
    VIEW_USER_PROFILE = "VIEW_USER_PROFILE"
    UPDATE_USER_PROFILE = "UPDATE_USER_PROFILE"
    VIEW_ORDER_HISTORY = "VIEW_ORDER_HISTORY"
    TRACK_ORDER_STATUS = "TRACK_ORDER_STATUS"
    GET_ORDER_DETAILS = "GET_ORDER_DETAILS"
    
    # Customer Support Actions
    GET_FAQ_ANSWER = "GET_FAQ_ANSWER"
    CONTACT_CUSTOMER_SUPPORT = "CONTACT_CUSTOMER_SUPPORT"
    SUBMIT_COMPLAINT = "SUBMIT_COMPLAINT"
    INITIATE_RETURN = "INITIATE_RETURN"
    REQUEST_REFUND = "REQUEST_REFUND"
    GET_SUPPORT_HOURS = "GET_SUPPORT_HOURS"
    
    # Recommendations & Personalization Actions
    GET_PERSONALIZED_RECOMMENDATIONS = "GET_PERSONALIZED_RECOMMENDATIONS"
    ADD_TO_WISHLIST = "ADD_TO_WISHLIST"
    REMOVE_FROM_WISHLIST = "REMOVE_FROM_WISHLIST"
    VIEW_WISHLIST = "VIEW_WISHLIST"
    GET_SIMILAR_PRODUCTS = "GET_SIMILAR_PRODUCTS"
    GET_FREQUENTLY_BOUGHT_TOGETHER = "GET_FREQUENTLY_BOUGHT_TOGETHER"
    
    # General Interaction Actions
    SEND_GREETING = "SEND_GREETING"
    SEND_GOODBYE = "SEND_GOODBYE"
    SEND_THANKS = "SEND_THANKS"
    REQUEST_CLARIFICATION = "REQUEST_CLARIFICATION"
    HANDLE_UNKNOWN_INTENT = "HANDLE_UNKNOWN_INTENT"


class IntentPriority(Enum):
    """Priority levels for intent processing."""
    CRITICAL = 1    # Checkout, payment, critical actions
    HIGH = 2        # Search, cart operations
    MEDIUM = 3      # Browsing, recommendations
    LOW = 4         # General interaction
    FALLBACK = 5    # Unknown intents


class EntityType(Enum):
    """Types of entities that can be extracted from user input."""
    PRODUCT_QUERY = "product_query"
    PRODUCT_ID = "product_id"
    CATEGORY = "category"
    BRAND = "brand"
    PRICE_RANGE = "price_range"
    QUANTITY = "quantity"
    ORDER_ID = "order_id"
    COUPON_CODE = "coupon_code"
    PAYMENT_METHOD = "payment_method"
    FILTER_CRITERIA = "filter_criteria"
    SORT_CRITERIA = "sort_criteria"
    SIZE = "size"
    COLOR = "color"
    DATE_RANGE = "date_range"
    REASON = "reason"
    URGENCY = "urgency"
    QUESTION = "question"
    TOPIC = "topic"
    ISSUE_TYPE = "issue_type"
    BUDGET = "budget"
    PREFERENCES = "preferences"
