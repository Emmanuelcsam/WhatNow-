"""
Geocoding service for location handling

This module provides location services using OpenStreetMap's Nominatim API,
including reverse geocoding for converting coordinates to address information.
Privacy-focused implementation with configurable timeouts and user agents.
"""
import requests
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class GeocodingService:
    """Service for handling geocoding operations"""

    def __init__(self, user_agent: str = "WhatNowAI/1.0"):
        """
        Initialize geocoding service

        Args:
            user_agent: User agent string for API requests
        """
        self.user_agent = user_agent
        self.base_url = "https://nominatim.openstreetmap.org/reverse"

    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Dict]:
        """
        Reverse geocode coordinates to address information

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            Dictionary with location information or None if failed
        """
        try:
            params = {
                'format': 'json',
                'lat': latitude,
                'lon': longitude,
                'zoom': 18,
                'addressdetails': 1
            }

            headers = {
                'User-Agent': self.user_agent
            }

            response = requests.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                geo_data = response.json()
                return self._extract_location_info(geo_data, latitude, longitude)
            else:
                logger.error(f"Geocoding API returned status {response.status_code}")
                return None

        except requests.RequestException as e:
            logger.error(f"Geocoding request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            return None

    def _extract_location_info(self, geo_data: Dict, latitude: float, longitude: float) -> Dict:
        """
        Extract relevant location information from geocoding response

        Args:
            geo_data: Raw geocoding response
            latitude: Original latitude
            longitude: Original longitude

        Returns:
            Cleaned location information dictionary
        """
        address = geo_data.get('address', {})

        # Extract city with fallback options
        city = (address.get('city') or
                address.get('town') or
                address.get('village') or
                address.get('hamlet') or
                address.get('suburb') or
                address.get('neighbourhood') or
                'Unknown')
        
        # Extract state/region with fallback options
        state = (address.get('state') or
                address.get('county') or
                address.get('state_district') or
                '')

        return {
            'country': address.get('country', 'Unknown'),
            'city': city,
            'state': state,
            'zipcode': address.get('postcode', 'Unknown'),
            'latitude': latitude,
            'longitude': longitude,
            'full_address': geo_data.get('display_name', 'Unknown'),
            'neighbourhood': address.get('neighbourhood', ''),
            'road': address.get('road', '')
        }

    def geocode_address(self, address: str) -> Optional[Dict]:
        """
        Geocode an address to get coordinates and location information

        Args:
            address: Address string to geocode

        Returns:
            Dictionary with location information and coordinates, or None if failed
        """
        try:
            # Use Nominatim for forward geocoding
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': address,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }

            headers = {'User-Agent': self.user_agent}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data:
                result = data[0]
                return {
                    'latitude': float(result['lat']),
                    'longitude': float(result['lon']),
                    'city': result.get('address', {}).get('city',
                           result.get('address', {}).get('town',
                           result.get('address', {}).get('village', 'Unknown'))),
                    'state': result.get('address', {}).get('state', ''),
                    'country': result.get('address', {}).get('country', ''),
                    'display_name': result.get('display_name', address),
                    'source': 'nominatim'
                }

            return None

        except Exception as e:
            logger.error(f"Geocoding failed for address '{address}': {e}")
            return None
