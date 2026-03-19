"""
Google Places API helper functions for restaurant search and details.
"""
import googlemaps
from django.conf import settings
from typing import List, Dict, Optional


def get_google_maps_client():
    """Initialize and return Google Maps client."""
    api_key = settings.GOOGLE_MAPS_API_KEY
    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY not configured in settings")
    return googlemaps.Client(key=api_key)


def search_restaurants(query: str, location: Optional[str] = None) -> List[Dict]:
    """
    Search for restaurants using Google Places API.
    
    Args:
        query: Search query (restaurant name, cuisine type, etc.)
        location: Optional location to bias search results (city, coordinates, etc.)
    
    Returns:
        List of restaurant results with place_id, name, address, and rating
    """
    try:
        gmaps = get_google_maps_client()
        
        # Build search query
        search_query = f"{query} restaurant"
        
        # Perform nearby search or text search
        if location:
            search_query = f"{query} restaurant in {location}"
        
        # Use Places API text search
        places_result = gmaps.places(query=search_query)
        
        restaurants = []
        for place in places_result.get('results', [])[:10]:  # Limit to first 10
            restaurants.append({
                'place_id': place.get('place_id'),
                'name': place.get('name', ''),
                'address': place.get('formatted_address', ''),
                'rating': place.get('rating'),
                'types': place.get('types', []),
                'lat': place.get('geometry', {}).get('location', {}).get('lat'),
                'lng': place.get('geometry', {}).get('location', {}).get('lng'),
            })
        
        return restaurants
    
    except Exception as e:
        print(f"Error searching restaurants: {str(e)}")
        return []


def get_restaurant_details(place_id: str) -> Optional[Dict]:
    """
    Get detailed information about a restaurant from Google Places.
    
    Args:
        place_id: Google Places place_id
    
    Returns:
        Dictionary with restaurant details including name, address components, 
        lat/lng, phone, website, hours, and rating
    """
    try:
        gmaps = get_google_maps_client()
        
        place_details = gmaps.place(place_id=place_id)
        result = place_details.get('result', {})
        
        # Extract address components
        address_components = {}
        for component in result.get('address_components', []):
            types = component.get('types', [])
            value = component.get('long_name', '')
            
            if 'street_number' in types:
                address_components['street_number'] = value
            elif 'route' in types:
                address_components['route'] = value
            elif 'locality' in types:
                address_components['city'] = value
            elif 'administrative_area_level_1' in types:
                address_components['province'] = value
            elif 'postal_code' in types:
                address_components['postal_code'] = value
            elif 'country' in types:
                address_components['country'] = value
        
        # Build address line 1 (street number + route)
        address_line1 = ""
        if address_components.get('street_number'):
            address_line1 += address_components['street_number']
        if address_components.get('route'):
            if address_line1:
                address_line1 += " "
            address_line1 += address_components['route']
        
        # Determine cuisine type from types
        cuisine_type = map_google_types_to_cuisine(result.get('types', []))
        
        return {
            'name': result.get('name', ''),
            'address_line1': address_line1,
            'city': address_components.get('city', ''),
            'province': address_components.get('province', ''),
            'postal_code': address_components.get('postal_code', ''),
            'country': address_components.get('country', 'Canada'),  # Default to Canada
            'lat': result.get('geometry', {}).get('location', {}).get('lat'),
            'lng': result.get('geometry', {}).get('location', {}).get('lng'),
            'phone': result.get('formatted_phone_number', ''),
            'website': result.get('website', ''),
            'rating': result.get('rating'),
            'types': result.get('types', []),
            'cuisine_type': cuisine_type,
            'place_name': result.get('formatted_address', ''),
        }
    
    except Exception as e:
        print(f"Error getting restaurant details: {str(e)}")
        return None


def map_google_types_to_cuisine(google_types: List[str]) -> str:
    """
    Map Google Places types to BiteBook cuisine types.
    
    Args:
        google_types: List of types from Google Places API
    
    Returns:
        Cuisine type matching Restaurant model choices:
        - Italian
        - Chinese
        - Indian
        - Mexican
        - Japanese
        - American
        - Thai
        - Other
    """
    # Comprehensive mapping of Google Places types to BiteBook cuisine types
    type_to_cuisine = {
        # Italian
        'italian_restaurant': 'Italian',
        'pizzeria': 'Italian',
        'pasta_restaurant': 'Italian',
        
        # Chinese
        'chinese_restaurant': 'Chinese',
        'dim_sum_restaurant': 'Chinese',
        'noodle_restaurant': 'Chinese',
        
        # Indian
        'indian_restaurant': 'Indian',
        'curry_restaurant': 'Indian',
        
        # Mexican
        'mexican_restaurant': 'Mexican',
        'taco_restaurant': 'Mexican',
        'taqueria': 'Mexican',
        
        # Japanese
        'japanese_restaurant': 'Japanese',
        'sushi_restaurant': 'Japanese',
        'ramen_restaurant': 'Japanese',
        'izakaya': 'Japanese',
        
        # Thai
        'thai_restaurant': 'Thai',
        
        # American
        'american_restaurant': 'American',
        'burger_restaurant': 'American',
        'steakhouse': 'American',
        'barbecue_restaurant': 'American',
        'diner': 'American',
        'breakfast_restaurant': 'American',
        'sandwich_shop': 'American',
        'cafe': 'American',
        'deli': 'American',
    }
    
    # Debug: print what types we're receiving from Google
    if google_types:
        print(f"DEBUG: Google types received: {google_types}")
    
    # Check each type returned by Google (in order of priority)
    for google_type in google_types:
        clean_type = google_type.lower().strip()
        if clean_type in type_to_cuisine:
            result = type_to_cuisine[clean_type]
            print(f"DEBUG: Matched '{clean_type}' to '{result}'")
            return result
    
    # Fallback: try to match partial keywords in the types
    for google_type in google_types:
        clean_type = google_type.lower().strip()
        if 'italian' in clean_type or 'pizza' in clean_type:
            return 'Italian'
        elif 'chinese' in clean_type or 'dim_sum' in clean_type:
            return 'Chinese'
        elif 'indian' in clean_type or 'curry' in clean_type:
            return 'Indian'
        elif 'mexican' in clean_type or 'taco' in clean_type:
            return 'Mexican'
        elif 'japanese' in clean_type or 'sushi' in clean_type or 'ramen' in clean_type:
            return 'Japanese'
        elif 'thai' in clean_type:
            return 'Thai'
        elif 'burger' in clean_type or 'steak' in clean_type or 'american' in clean_type or 'breakfast' in clean_type or 'diner' in clean_type:
            return 'American'
    
    # If no match found, log it for debugging
    print(f"DEBUG: No cuisine match found for types: {google_types}. Defaulting to 'Other'")
    # Default to Other if no specific match found
    return 'Other'
