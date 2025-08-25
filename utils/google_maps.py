import requests
import os
import streamlit as st
from typing import Optional, Tuple

def get_google_maps_api_key():
    """
    Get Google Maps API key from environment variables or Streamlit secrets
    """
    # First try environment variable
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    # If not found, try Streamlit secrets
    if not api_key:
        try:
            api_key = st.secrets.get("GOOGLE_MAPS_API_KEY")
        except:
            pass
    
    return api_key

def calculate_distance_google_maps(from_coords: str, to_coords: str) -> Optional[float]:
    """
    Calculate distance between two coordinates using Google Maps Distance Matrix API
    
    Args:
        from_coords: String in format "lat,lng"
        to_coords: String in format "lat,lng"
    
    Returns:
        Distance in kilometers or None if calculation fails
    """
    api_key = get_google_maps_api_key()
    
    if not api_key:
        st.warning("Google Maps API key not found. Set GOOGLE_MAPS_API_KEY environment variable.")
        return None
    
    try:
        # Google Maps Distance Matrix API endpoint
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        
        params = {
            'origins': from_coords,
            'destinations': to_coords,
            'units': 'metric',
            'mode': 'driving',
            'key': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Check if API returned valid results
        if data['status'] == 'OK':
            element = data['rows'][0]['elements'][0]
            
            if element['status'] == 'OK':
                # Distance is returned in meters, convert to kilometers
                distance_km = element['distance']['value'] / 1000
                return round(distance_km, 2)
            else:
                st.warning(f"Google Maps API: {element['status']}")
                return None
        else:
            st.error(f"Google Maps API error: {data['status']}")
            return None
    
    except requests.exceptions.RequestException as e:
        st.error(f"Network error calling Google Maps API: {str(e)}")
        return None
    except KeyError as e:
        st.error(f"Unexpected response format from Google Maps API: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error calculating distance: {str(e)}")
        return None

def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Convert an address to coordinates using Google Maps Geocoding API
    
    Args:
        address: Street address or location name
    
    Returns:
        Tuple of (latitude, longitude) or None if geocoding fails
    """
    api_key = get_google_maps_api_key()
    
    if not api_key:
        return None
    
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        
        params = {
            'address': address,
            'key': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            location = data['results'][0]['geometry']['location']
            return (location['lat'], location['lng'])
        else:
            return None
    
    except Exception as e:
        st.error(f"Error geocoding address: {str(e)}")
        return None

def reverse_geocode(lat: float, lng: float) -> Optional[str]:
    """
    Convert coordinates to an address using Google Maps Reverse Geocoding API
    
    Args:
        lat: Latitude
        lng: Longitude
    
    Returns:
        Formatted address string or None if reverse geocoding fails
    """
    api_key = get_google_maps_api_key()
    
    if not api_key:
        return None
    
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        
        params = {
            'latlng': f"{lat},{lng}",
            'key': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            return data['results'][0]['formatted_address']
        else:
            return None
    
    except Exception as e:
        st.error(f"Error reverse geocoding: {str(e)}")
        return None

def calculate_route_info(from_coords: str, to_coords: str) -> Optional[dict]:
    """
    Get detailed route information including distance, duration, and waypoints
    
    Args:
        from_coords: String in format "lat,lng"
        to_coords: String in format "lat,lng"
    
    Returns:
        Dictionary with route information or None if calculation fails
    """
    api_key = get_google_maps_api_key()
    
    if not api_key:
        return None
    
    try:
        url = "https://maps.googleapis.com/maps/api/directions/json"
        
        params = {
            'origin': from_coords,
            'destination': to_coords,
            'mode': 'driving',
            'units': 'metric',
            'key': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == 'OK' and data['routes']:
            route = data['routes'][0]
            leg = route['legs'][0]
            
            return {
                'distance_km': leg['distance']['value'] / 1000,
                'duration_minutes': leg['duration']['value'] / 60,
                'start_address': leg['start_address'],
                'end_address': leg['end_address'],
                'overview_polyline': route['overview_polyline']['points']
            }
        else:
            return None
    
    except Exception as e:
        st.error(f"Error getting route information: {str(e)}")
        return None

def validate_api_key() -> bool:
    """
    Validate that the Google Maps API key is working
    
    Returns:
        True if API key is valid, False otherwise
    """
    api_key = get_google_maps_api_key()
    
    if not api_key:
        return False
    
    try:
        # Test with a simple geocoding request
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': 'New York, NY',
            'key': api_key
        }
        
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        return data['status'] == 'OK'
    
    except:
        return False

# Fallback distance calculation using Haversine formula
def calculate_haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the great circle distance between two points on the earth (specified in decimal degrees)
    
    Returns distance in kilometers
    """
    import math
    
    # Convert decimal degrees to radians
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return round(c * r, 2)

def calculate_distance_fallback(from_coords: str, to_coords: str) -> Optional[float]:
    """
    Calculate distance using Haversine formula as fallback when Google Maps API is not available
    
    Args:
        from_coords: String in format "lat,lng"
        to_coords: String in format "lat,lng"
    
    Returns:
        Distance in kilometers or None if calculation fails
    """
    try:
        from_lat, from_lng = map(float, from_coords.split(','))
        to_lat, to_lng = map(float, to_coords.split(','))
        
        return calculate_haversine_distance(from_lat, from_lng, to_lat, to_lng)
    
    except Exception as e:
        st.error(f"Error calculating fallback distance: {str(e)}")
        return None
