"""
Keyword Loader

This module loads and manages all keyword dictionaries for intent classification.
It provides a unified interface to access keywords from all intent categories.
"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path


class KeywordLoader:
    """Loads and manages keyword dictionaries for all intent categories."""
    
    def __init__(self):
        """Initialize the keyword loader."""
        self.keywords_dir = Path(__file__).parent
        self._loaded_keywords = {}
        self._load_all_keywords()
    
    def _load_all_keywords(self) -> None:
        """Load all keyword files."""
        keyword_files = [
            "search_keywords.json",
            "cart_keywords.json", 
            "product_keywords.json",
            "checkout_keywords.json",
            "account_keywords.json",
            "support_keywords.json",
            "recommendation_keywords.json",
            "general_keywords.json"
        ]
        
        for filename in keyword_files:
            file_path = self.keywords_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self._loaded_keywords.update(data)
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
    
    def get_keywords_for_intent(self, intent_name: str) -> Optional[Dict[str, Any]]:
        """Get keywords for a specific intent."""
        # Map intent names to keyword categories and specific intent sections
        intent_mapping = {
            # Search intents
            "search_products": ("search_intent_keywords", "search_products"),
            "search_by_category": ("search_intent_keywords", "search_by_category"),
            "browse_products": ("search_intent_keywords", "browse_products"),
            "filter_products": ("search_intent_keywords", "filter_products"),
            "sort_products": ("search_intent_keywords", "sort_products"),
            
            # Product intents
            "get_product_info": ("product_intent_keywords", "product_info"),
            "compare_products": ("product_intent_keywords", "product_comparison"),
            
            # Cart intents
            "add_to_cart": ("cart_intent_,keywords", "add_to_cart"),
            "remove_from_cart": ("cart_intent_keywords", "remove_from_cart"),
            "update_cart": ("cart_intent_keywords", "update_cart"),
            "view_cart": ("cart_intent_keywords", "view_cart"),
            "clear_cart": ("cart_intent_keywords", "clear_cart"),
            
            # Checkout intents
            "checkout": ("checkout_intent_keywords", "checkout"),
            "apply_coupon": ("checkout_intent_keywords", "apply_coupon"),
            "remove_coupon": ("checkout_intent_keywords", "remove_coupon"),
            "select_payment": ("checkout_intent_keywords", "select_payment"),
            "select_shipping": ("checkout_intent_keywords", "select_shipping"),
            
            # Account intents
            "login": ("account_intent_keywords", "login"),
            "logout": ("account_intent_keywords", "logout"),
            "register": ("account_intent_keywords", "register"),
            "view_profile": ("account_intent_keywords", "view_profile"),
            "update_profile": ("account_intent_keywords", "update_profile"),
            "view_orders": ("account_intent_keywords", "view_orders"),
            "track_order": ("account_intent_keywords", "track_order"),
            
            # Support intents
            "faq": ("support_intent_keywords", "faq"),
            "contact_support": ("support_intent_keywords", "contact_support"),
            "complaint": ("support_intent_keywords", "complaint"),
            "return_item": ("support_intent_keywords", "return_item"),
            "refund": ("support_intent_keywords", "refund"),
            
            # Recommendation intents
            "get_recommendations": ("recommendation_intent_keywords", "get_recommendations"),
            "add_to_wishlist": ("recommendation_intent_keywords", "add_to_wishlist"),
            "remove_from_wishlist": ("recommendation_intent_keywords", "remove_from_wishlist"),
            "view_wishlist": ("recommendation_intent_keywords", "view_wishlist"),
            
            # General intents
            "greeting": ("general_intent_keywords", "greeting"),
            "goodbye": ("general_intent_keywords", "goodbye"),
            "thanks": ("general_intent_keywords", "thanks"),
            "clarification": ("general_intent_keywords", "clarification"),
            "unknown": ("general_intent_keywords", "unknown")
        }
        
        mapping = intent_mapping.get(intent_name)
        if mapping:
            keyword_category, intent_section = mapping
            if keyword_category in self._loaded_keywords:
                category_data = self._loaded_keywords[keyword_category]
                if intent_section in category_data:
                    return category_data[intent_section]
        
        return None
    
    def get_primary_keywords(self, intent_name: str) -> List[str]:
        """Get primary keywords for an intent."""
        keywords = self.get_keywords_for_intent(intent_name)
        if keywords and "primary_keywords" in keywords:
            return keywords["primary_keywords"]
        return []
    
    def get_action_phrases(self, intent_name: str) -> List[str]:
        """Get action phrases for an intent."""
        keywords = self.get_keywords_for_intent(intent_name)
        if keywords and "action_phrases" in keywords:
            return keywords["action_phrases"]
        return []
    
    def get_misspellings(self, intent_name: str) -> List[str]:
        """Get common misspellings for an intent."""
        keywords = self.get_keywords_for_intent(intent_name)
        if keywords and "misspellings" in keywords:
            return keywords["misspellings"]
        return []
    
    def get_uk_variations(self, intent_name: str) -> List[str]:
        """Get UK spelling variations for an intent."""
        keywords = self.get_keywords_for_intent(intent_name)
        if keywords and "uk_variations" in keywords:
            return keywords["uk_variations"]
        return []
    
    def get_priority_weights(self, intent_name: str) -> Dict[str, float]:
        """Get priority weights for keywords in an intent."""
        keywords = self.get_keywords_for_intent(intent_name)
        if keywords and "priority_weights" in keywords:
            return keywords["priority_weights"]
        return {}
    
    def get_all_keywords_for_intent(self, intent_name: str) -> List[str]:
        """Get all keywords (primary, misspellings, UK variations) for an intent."""
        all_keywords = []
        
        # Add primary keywords
        all_keywords.extend(self.get_primary_keywords(intent_name))
        
        # Add action phrases
        all_keywords.extend(self.get_action_phrases(intent_name))
        
        # Add misspellings
        all_keywords.extend(self.get_misspellings(intent_name))
        
        # Add UK variations
        all_keywords.extend(self.get_uk_variations(intent_name))
        
        return list(set(all_keywords))  # Remove duplicates
    
    def search_keywords(self, query: str) -> Dict[str, List[str]]:
        """Search for keywords containing the query."""
        results = {}
        query_lower = query.lower()
        
        for category, keywords in self._loaded_keywords.items():
            matching_keywords = []
            
            if isinstance(keywords, dict):
                for key, value in keywords.items():
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, str) and query_lower in item.lower():
                                matching_keywords.append(item)
                    elif isinstance(value, str) and query_lower in value.lower():
                        matching_keywords.append(value)
            
            if matching_keywords:
                results[category] = matching_keywords
        
        return results
    
    def get_keyword_statistics(self) -> Dict[str, Any]:
        """Get statistics about the keyword dictionaries."""
        total_keywords = 0
        categories = {}
        
        for category, keywords in self._loaded_keywords.items():
            if isinstance(keywords, dict):
                category_count = 0
                for key, value in keywords.items():
                    if isinstance(value, list):
                        category_count += len(value)
                    elif isinstance(value, str):
                        category_count += 1
                
                categories[category] = category_count
                total_keywords += category_count
        
        return {
            "total_keywords": total_keywords,
            "total_categories": len(categories),
            "keywords_by_category": categories,
            "average_keywords_per_category": total_keywords / len(categories) if categories else 0
        }
    
    def get_all_intent_keywords(self) -> Dict[str, Dict[str, Any]]:
        """Get all intent keywords organized by intent name."""
        all_intents = {}
        
        # Map all intents from the loaded keywords
        intent_mapping = {
            # Search intents
            "search_products": ("search_intent_keywords", "search_products"),
            "search_by_category": ("search_intent_keywords", "search_by_category"),
            "browse_products": ("search_intent_keywords", "browse_products"),
            "filter_products": ("search_intent_keywords", "filter_products"),
            "sort_products": ("search_intent_keywords", "sort_products"),
            
            # Product intents
            "get_product_info": ("product_intent_keywords", "product_info"),
            "compare_products": ("product_intent_keywords", "product_comparison"),
            
            # Cart intents
            "add_to_cart": ("cart_intent_keywords", "add_to_cart"),
            "remove_from_cart": ("cart_intent_keywords", "remove_from_cart"),
            "update_cart": ("cart_intent_keywords", "update_cart"),
            "view_cart": ("cart_intent_keywords", "view_cart"),
            "clear_cart": ("cart_intent_keywords", "clear_cart"),
            
            # Checkout intents
            "checkout": ("checkout_intent_keywords", "checkout"),
            "apply_coupon": ("checkout_intent_keywords", "apply_coupon"),
            "remove_coupon": ("checkout_intent_keywords", "remove_coupon"),
            "select_payment": ("checkout_intent_keywords", "select_payment"),
            "select_shipping": ("checkout_intent_keywords", "select_shipping"),
            
            # Account intents
            "login": ("account_intent_keywords", "login"),
            "logout": ("account_intent_keywords", "logout"),
            "register": ("account_intent_keywords", "register"),
            "view_profile": ("account_intent_keywords", "view_profile"),
            "update_profile": ("account_intent_keywords", "update_profile"),
            "view_orders": ("account_intent_keywords", "view_orders"),
            "track_order": ("account_intent_keywords", "track_order"),
            
            # Support intents
            "faq": ("support_intent_keywords", "faq"),
            "contact_support": ("support_intent_keywords", "contact_support"),
            "complaint": ("support_intent_keywords", "complaint"),
            "return_item": ("support_intent_keywords", "return_item"),
            "refund": ("support_intent_keywords", "refund"),
            
            # Recommendation intents
            "get_recommendations": ("recommendation_intent_keywords", "get_recommendations"),
            "add_to_wishlist": ("recommendation_intent_keywords", "add_to_wishlist"),
            "remove_from_wishlist": ("recommendation_intent_keywords", "remove_from_wishlist"),
            "view_wishlist": ("recommendation_intent_keywords", "view_wishlist"),
            
            # General intents
            "greeting": ("general_intent_keywords", "greeting"),
            "goodbye": ("general_intent_keywords", "goodbye"),
            "thanks": ("general_intent_keywords", "thanks"),
            "clarification": ("general_intent_keywords", "clarification"),
            "unknown": ("general_intent_keywords", "unknown")
        }
        
        for intent_name, (category, section) in intent_mapping.items():
            if category in self._loaded_keywords:
                category_data = self._loaded_keywords[category]
                if section in category_data:
                    all_intents[intent_name] = category_data[section]
        
        return all_intents

    def export_keywords(self, format: str = "dict") -> Any:
        """Export all keywords in various formats."""
        if format == "dict":
            return self._loaded_keywords
        elif format == "json":
            return json.dumps(self._loaded_keywords, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global instance for easy access
keyword_loader = KeywordLoader()


def get_keyword_loader() -> KeywordLoader:
    """Get the global keyword loader instance."""
    return keyword_loader


def get_keywords_for_intent(intent_name: str) -> Optional[Dict[str, Any]]:
    """Get keywords for a specific intent."""
    return keyword_loader.get_keywords_for_intent(intent_name)


def get_primary_keywords(intent_name: str) -> List[str]:
    """Get primary keywords for an intent."""
    return keyword_loader.get_primary_keywords(intent_name)


def get_action_phrases(intent_name: str) -> List[str]:
    """Get action phrases for an intent."""
    return keyword_loader.get_action_phrases(intent_name)


def get_misspellings(intent_name: str) -> List[str]:
    """Get common misspellings for an intent."""
    return keyword_loader.get_misspellings(intent_name)


def get_uk_variations(intent_name: str) -> List[str]:
    """Get UK spelling variations for an intent."""
    return keyword_loader.get_uk_variations(intent_name)


def get_priority_weights(intent_name: str) -> Dict[str, float]:
    """Get priority weights for keywords in an intent."""
    return keyword_loader.get_priority_weights(intent_name)


def get_all_keywords_for_intent(intent_name: str) -> List[str]:
    """Get all keywords for an intent."""
    return keyword_loader.get_all_keywords_for_intent(intent_name)


# Export main classes and functions
__all__ = [
    'KeywordLoader',
    'keyword_loader',
    'get_keyword_loader',
    'get_keywords_for_intent',
    'get_primary_keywords',
    'get_action_phrases',
    'get_misspellings',
    'get_uk_variations',
    'get_priority_weights',
    'get_all_keywords_for_intent'
]
