#!/usr/bin/env python3
"""
Comprehensive Coverage Test for Intent Classification System

This script tests the system with a wide variety of user queries to measure
coverage and accuracy for 98-99% target.
"""

import sys
import time
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from keyword_matcher import create_keyword_matcher

def test_coverage():
    """Test the system with comprehensive user queries."""
    
    # Create matcher
    matcher = create_keyword_matcher()
    
    # Comprehensive test cases organized by intent
    test_cases = {
        # Search & Discovery
        "search_products": [
            "I'm looking for a laptop",
            "Find me running shoes",
            "Search for wireless headphones",
            "Show me smartphones",
            "I need a coffee maker",
            "Find red Nike shoes",
            "Looking for a gift",
            "What do you have in electronics?",
            "Browse laptops",
            "Show me what's available"
        ],
        
        "search_by_category": [
            "Show me electronics",
            "I want to see clothing",
            "Browse home and garden",
            "What's in the sports section?",
            "Show me beauty products",
            "Electronics please",
            "Clothing section",
            "Home decor items"
        ],
        
        "browse_products": [
            "What's new?",
            "Show me what's popular",
            "Browse deals",
            "What's trending?",
            "Show me featured products",
            "What's on sale?",
            "New arrivals",
            "Popular items"
        ],
        
        "filter_products": [
            "Filter by price under $100",
            "Show only red items",
            "Filter by brand Apple",
            "Show items with free shipping",
            "Filter by rating 4+ stars",
            "Under $50 please",
            "Only Nike products",
            "Free shipping only"
        ],
        
        "sort_products": [
            "Sort by price low to high",
            "Show cheapest first",
            "Sort by newest",
            "Sort by rating",
            "Sort by popularity",
            "Price ascending",
            "Newest first",
            "Best rated"
        ],
        
        # Cart Operations
        "add_to_cart": [
            "Add this to my cart",
            "Add to cart",
            "Put this in my basket",
            "I'll take this one",
            "Buy this",
            "Add to shopping cart",
            "I want this",
            "Purchase this"
        ],
        
        "remove_from_cart": [
            "Remove this from my cart",
            "Take this out of my basket",
            "I don't want this anymore",
            "Delete this item",
            "Remove from cart",
            "Get rid of this",
            "Don't want this"
        ],
        
        "update_cart": [
            "Change quantity to 2",
            "I want 3 of these",
            "Update quantity",
            "Make it 5 instead",
            "Change to 1",
            "Update to 4",
            "Quantity 2 please"
        ],
        
        "view_cart": [
            "Show my cart",
            "What's in my basket?",
            "View cart",
            "Show cart contents",
            "What did I add?",
            "My shopping cart",
            "Cart summary"
        ],
        
        "clear_cart": [
            "Clear my cart",
            "Empty my basket",
            "Remove everything",
            "Start over",
            "Clear all items",
            "Delete all",
            "Empty cart"
        ],
        
        # Checkout & Payment
        "checkout": [
            "I'm ready to checkout",
            "Proceed to payment",
            "Buy now",
            "Complete purchase",
            "Checkout",
            "Place order",
            "Finalize order"
        ],
        
        "apply_coupon": [
            "Apply coupon code SAVE20",
            "Use my discount code",
            "Apply promo code",
            "I have a coupon",
            "Enter discount code",
            "Use coupon SAVE20",
            "Apply discount"
        ],
        
        "select_payment": [
            "I want to pay with credit card",
            "Use PayPal",
            "Pay with Apple Pay",
            "Change payment method",
            "Select payment option",
            "Credit card payment",
            "PayPal please"
        ],
        
        "select_shipping": [
            "I want standard shipping",
            "Use express delivery",
            "Select shipping method",
            "Change shipping option",
            "Free shipping please",
            "Express shipping",
            "Standard delivery"
        ],
        
        # Account Management
        "login": [
            "I want to login",
            "Sign me in",
            "Log into my account",
            "Access my account",
            "Login please",
            "Sign in",
            "Log in"
        ],
        
        "logout": [
            "I want to logout",
            "Sign me out",
            "Log out of my account",
            "Exit my account",
            "Logout please",
            "Sign out",
            "Log out"
        ],
        
        "register": [
            "I want to register",
            "Create an account",
            "Sign up for an account",
            "Join the site",
            "New account",
            "Register please",
            "Sign up"
        ],
        
        "view_profile": [
            "Show my profile",
            "View my account",
            "My profile information",
            "Account details",
            "Personal information",
            "My info",
            "Profile page"
        ],
        
        "update_profile": [
            "Update my profile",
            "Edit my information",
            "Change my details",
            "Modify my account",
            "Update personal info",
            "Edit contact info",
            "Change my address"
        ],
        
        "view_orders": [
            "Show my orders",
            "View order history",
            "My past purchases",
            "Previous orders",
            "Recent orders",
            "All my orders",
            "Order list"
        ],
        
        "track_order": [
            "Where is my order",
            "Track my package",
            "Order status",
            "Tracking information",
            "Package location",
            "Delivery status",
            "Order progress"
        ],
        
        # Support & Help
        "faq": [
            "I need help",
            "What's your return policy?",
            "How do I return an item?",
            "What are your shipping options?",
            "Help me",
            "I have a question",
            "Need assistance"
        ],
        
        "contact_support": [
            "I need to contact support",
            "Get me customer service",
            "I want to speak to someone",
            "Contact support",
            "Customer service please",
            "Help desk",
            "Support team"
        ],
        
        "return_item": [
            "I want to return this",
            "Return this item",
            "I need to return something",
            "Return policy",
            "How to return",
            "Return process",
            "Send back"
        ],
        
        "refund": [
            "I want a refund",
            "Request refund",
            "Refund this purchase",
            "Money back",
            "Cancel and refund",
            "Refund please",
            "Get my money back"
        ],
        
        # Recommendations & Wishlist
        "get_recommendations": [
            "What do you recommend?",
            "Suggest something for me",
            "What would you suggest?",
            "Recommend products",
            "What's good?",
            "Any recommendations?",
            "Suggest items"
        ],
        
        "add_to_wishlist": [
            "Add to wishlist",
            "Save for later",
            "Add to favorites",
            "Wishlist this",
            "Save this item",
            "Add to my list",
            "Bookmark this"
        ],
        
        "remove_from_wishlist": [
            "Remove from wishlist",
            "Delete from favorites",
            "Remove from my list",
            "Unsave this",
            "Remove from saved",
            "Delete from wishlist"
        ],
        
        "view_wishlist": [
            "Show my wishlist",
            "View my favorites",
            "My saved items",
            "Wishlist items",
            "Saved for later",
            "My list",
            "Favorites list"
        ],
        
        # General Interaction
        "greeting": [
            "Hello",
            "Hi there",
            "Good morning",
            "Hey",
            "Greetings",
            "Hi",
            "Good afternoon"
        ],
        
        "goodbye": [
            "Goodbye",
            "See you later",
            "Bye",
            "Thanks, that's all",
            "Have a good day",
            "See you",
            "Farewell"
        ],
        
        "thanks": [
            "Thank you",
            "Thanks",
            "Much appreciated",
            "Great, thanks",
            "Perfect, thank you",
            "Thanks a lot",
            "Appreciate it"
        ],
        
        "clarification": [
            "Can you explain that?",
            "I don't understand",
            "What do you mean?",
            "Can you clarify?",
            "I'm confused",
            "Explain please",
            "What does that mean?"
        ]
    }
    
    print("🧪 Comprehensive Coverage Test")
    print("=" * 60)
    
    total_tests = 0
    correct_matches = 0
    incorrect_matches = []
    performance_times = []
    
    # Test each intent category
    for expected_intent, queries in test_cases.items():
        print(f"\n📋 Testing {expected_intent}:")
        
        for query in queries:
            total_tests += 1
            start_time = time.time()
            
            result = matcher.match_intent(query)
            processing_time = (time.time() - start_time) * 1000
            performance_times.append(processing_time)
            
            if result:
                if result.intent_name == expected_intent:
                    correct_matches += 1
                    print(f"  ✅ '{query}' -> {result.intent_name} (Confidence: {result.confidence_score:.3f}, Time: {processing_time:.2f}ms)")
                else:
                    incorrect_matches.append({
                        'query': query,
                        'expected': expected_intent,
                        'actual': result.intent_name,
                        'confidence': result.confidence_score
                    })
                    print(f"  ❌ '{query}' -> Expected: {expected_intent}, Got: {result.intent_name} (Confidence: {result.confidence_score:.3f})")
            else:
                incorrect_matches.append({
                    'query': query,
                    'expected': expected_intent,
                    'actual': 'NO_MATCH',
                    'confidence': 0.0
                })
                print(f"  ❌ '{query}' -> Expected: {expected_intent}, Got: NO_MATCH")
    
    # Calculate statistics
    accuracy = (correct_matches / total_tests) * 100 if total_tests > 0 else 0
    avg_processing_time = sum(performance_times) / len(performance_times) if performance_times else 0
    queries_under_50ms = sum(1 for t in performance_times if t < 50)
    performance_percentage = (queries_under_50ms / len(performance_times)) * 100 if performance_times else 0
    
    print(f"\n📊 Coverage Test Results:")
    print(f"=" * 60)
    print(f"Total test queries: {total_tests}")
    print(f"Correct matches: {correct_matches}")
    print(f"Incorrect matches: {len(incorrect_matches)}")
    print(f"Accuracy: {accuracy:.1f}%")
    print(f"Average processing time: {avg_processing_time:.2f}ms")
    print(f"Queries under 50ms: {performance_percentage:.1f}%")
    
    # Show incorrect matches
    if incorrect_matches:
        print(f"\n❌ Incorrect Matches ({len(incorrect_matches)}):")
        for i, match in enumerate(incorrect_matches[:10]):  # Show first 10
            print(f"  {i+1}. '{match['query']}' -> Expected: {match['expected']}, Got: {match['actual']}")
        if len(incorrect_matches) > 10:
            print(f"  ... and {len(incorrect_matches) - 10} more")
    
    # Coverage assessment
    print(f"\n🎯 Coverage Assessment:")
    if accuracy >= 98:
        print(f"✅ EXCELLENT: {accuracy:.1f}% coverage - Target achieved!")
    elif accuracy >= 95:
        print(f"✅ VERY GOOD: {accuracy:.1f}% coverage - Close to target")
    elif accuracy >= 90:
        print(f"⚠️  GOOD: {accuracy:.1f}% coverage - Needs improvement")
    else:
        print(f"❌ POOR: {accuracy:.1f}% coverage - Significant issues")
    
    return accuracy, len(incorrect_matches)

if __name__ == "__main__":
    test_coverage()
