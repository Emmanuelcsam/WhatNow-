"""
Enhanced Location Detection Service

This module provides comprehensive location detection using multiple methods:
- IP-based location detection with multiple providers
- Browser geolocation API integration
- Address geocoding with fallback providers
- Location validation and accuracy scoring
- Privacy-focused implementation with opt-in features
"""

import requests
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class LocationResult:
    """Structured location data with confidence scoring"""
    latitude: float
    longitude: float
    city: str
    state: str
    country: str
    country_code: str
    zip_code: str
    timezone: str
    accuracy: float  # 0.0 to 1.0 confidence score
    source: str
    ip_address: str = ""
    continent: str = ""
    region_code: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'country_code': self.country_code,
            'zip_code': self.zip_code,
            'timezone': self.timezone,
            'accuracy': self.accuracy,
            'source': self.source,
            'ip_address': self.ip_address,
            'continent': self.continent,
            'region_code': self.region_code
        }


class IPLocationProvider:
    """Base class for IP-based location providers"""

    def __init__(self, name: str, timeout: int = 5):
        self.name = name
        self.timeout = timeout
        self.last_request_time = 0
        self.min_delay = 1.0  # Rate limiting

    def get_location(self, ip_address: str) -> Optional[LocationResult]:
        """Get location from IP address"""
        raise NotImplementedError

    def _rate_limit(self):
        """Simple rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_delay:
            time.sleep(self.min_delay - time_since_last)
        self.last_request_time = time.time()


class IPStackProvider(IPLocationProvider):
    """IPStack API provider (most accurate for the example given)"""

    def __init__(self, api_key: str, timeout: int = 5):
        super().__init__("IPStack", timeout)
        self.api_key = api_key
        self.base_url = "http://api.ipstack.com"

    def get_location(self, ip_address: str) -> Optional[LocationResult]:
        """Get location using IPStack API"""
        try:
            self._rate_limit()

            url = f"{self.base_url}/{ip_address}"
            params = {
                'access_key': self.api_key,
                'fields': 'country_name,country_code,region_name,region_code,city,zip,latitude,longitude,time_zone,continent_name'
            }

            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if data.get('success', True) and data.get('latitude') is not None:
                return LocationResult(
                    latitude=float(data.get('latitude', 0)),
                    longitude=float(data.get('longitude', 0)),
                    city=data.get('city', ''),
                    state=data.get('region_name', ''),
                    country=data.get('country_name', ''),
                    country_code=data.get('country_code', ''),
                    zip_code=data.get('zip', ''),
                    timezone=data.get('time_zone', {}).get('id', '') if isinstance(data.get('time_zone'), dict) else str(data.get('time_zone', '')),
                    accuracy=0.85,  # IPStack is generally very accurate
                    source='ipstack',
                    ip_address=ip_address,
                    continent=data.get('continent_name', ''),
                    region_code=data.get('region_code', '')
                )

            return None

        except Exception as e:
            logger.warning(f"IPStack provider failed: {e}")
            return None


class IP2LocationProvider(IPLocationProvider):
    """ip-api.com provider (free, no API key required)"""

    def __init__(self, timeout: int = 5):
        super().__init__("IP2Location", timeout)
        self.base_url = "http://ip-api.com/json"
        self.min_delay = 2.0  # ip-api has stricter rate limits

    def get_location(self, ip_address: str) -> Optional[LocationResult]:
        """Get location using ip-api.com"""
        try:
            self._rate_limit()

            url = f"{self.base_url}/{ip_address}"
            params = {
                'fields': 'status,country,countryCode,region,regionName,city,zip,lat,lon,timezone,continent,query'
            }

            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if data.get('status') == 'success':
                return LocationResult(
                    latitude=float(data.get('lat', 0)),
                    longitude=float(data.get('lon', 0)),
                    city=data.get('city', ''),
                    state=data.get('regionName', ''),
                    country=data.get('country', ''),
                    country_code=data.get('countryCode', ''),
                    zip_code=data.get('zip', ''),
                    timezone=data.get('timezone', ''),
                    accuracy=0.75,  # Generally good accuracy
                    source='ip-api',
                    ip_address=ip_address,
                    continent=data.get('continent', ''),
                    region_code=data.get('region', '')
                )

            return None

        except Exception as e:
            logger.warning(f"IP-API provider failed: {e}")
            return None


class FreeGeoIPProvider(IPLocationProvider):
    """freegeoip.app provider (free backup)"""

    def __init__(self, timeout: int = 5):
        super().__init__("FreeGeoIP", timeout)
        self.base_url = "https://freegeoip.app/json"

    def get_location(self, ip_address: str) -> Optional[LocationResult]:
        """Get location using freegeoip.app"""
        try:
            self._rate_limit()

            url = f"{self.base_url}/{ip_address}"

            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if data.get('latitude') is not None:
                return LocationResult(
                    latitude=float(data.get('latitude', 0)),
                    longitude=float(data.get('longitude', 0)),
                    city=data.get('city', ''),
                    state=data.get('region_name', ''),
                    country=data.get('country_name', ''),
                    country_code=data.get('country_code', ''),
                    zip_code=data.get('zip_code', ''),
                    timezone=data.get('time_zone', ''),
                    accuracy=0.65,  # Lower accuracy but good fallback
                    source='freegeoip',
                    ip_address=ip_address,
                    continent='',
                    region_code=data.get('region_code', '')
                )

            return None

        except Exception as e:
            logger.warning(f"FreeGeoIP provider failed: {e}")
            return None


class EnhancedLocationService:
    """Comprehensive location detection service with multiple providers and validation"""

    def __init__(self, ipstack_key: str = None):
        """
        Initialize location service with API keys

        Args:
            ipstack_key: Optional IPStack API key for enhanced accuracy
        """
        self.providers = []

        # Initialize providers in order of preference
        if ipstack_key:
            self.providers.append(IPStackProvider(ipstack_key))

        self.providers.extend([
            IP2LocationProvider(),
            FreeGeoIPProvider()
        ])

        self.cache = {}
        self.cache_ttl = timedelta(hours=1)  # Cache IP locations for 1 hour

        logger.info(f"Enhanced location service initialized with {len(self.providers)} providers")

    def get_user_ip(self) -> Optional[str]:
        """Get user's public IP address using multiple services"""
        ip_services = [
            "https://api.ipify.org?format=json",
            "https://ipapi.co/json/",
            "https://httpbin.org/ip",
            "https://api.myip.com"
        ]

        for service in ip_services:
            try:
                response = requests.get(service, timeout=3)
                response.raise_for_status()

                data = response.json()

                # Different services return IP in different formats
                ip = (data.get('ip') or
                      data.get('origin') or
                      data.get('ipAddress'))

                if ip and self._is_valid_ip(ip):
                    logger.info(f"Got IP {ip} from {service}")
                    return ip

            except Exception as e:
                logger.warning(f"IP service {service} failed: {e}")
                continue

        logger.error("Failed to get user IP from all services")
        return None

    def _is_valid_ip(self, ip: str) -> bool:
        """Basic IP validation"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False

            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False

            # Reject local/private IPs
            if ip.startswith(('127.', '10.', '192.168.')) or ip.startswith('172.'):
                return False

            return True
        except:
            return False

    def get_location_from_ip(self, ip_address: str = None) -> Optional[LocationResult]:
        """
        Get location from IP address using multiple providers

        Args:
            ip_address: IP address to lookup, or None to detect automatically

        Returns:
            LocationResult with highest confidence, or None if all providers fail
        """
        if not ip_address:
            ip_address = self.get_user_ip()
            if not ip_address:
                return None

        # Check cache first
        cache_key = f"ip_{ip_address}"
        if cache_key in self.cache:
            cached_result, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_ttl:
                logger.info(f"Using cached location for IP {ip_address}")
                return cached_result

        # Try all providers concurrently
        results = []

        with ThreadPoolExecutor(max_workers=len(self.providers)) as executor:
            future_to_provider = {
                executor.submit(provider.get_location, ip_address): provider
                for provider in self.providers
            }

            for future in as_completed(future_to_provider, timeout=10):
                provider = future_to_provider[future]
                try:
                    result = future.result(timeout=3)
                    if result:
                        results.append(result)
                        logger.info(f"Provider {provider.name} returned location: {result.city}, {result.state}")
                except Exception as e:
                    logger.warning(f"Provider {provider.name} failed: {e}")

        if not results:
            logger.error("All location providers failed")
            return None

        # Select best result based on accuracy and validate consistency
        best_result = self._select_best_location(results)

        # Cache the result
        self.cache[cache_key] = (best_result, datetime.now())

        logger.info(f"Selected location: {best_result.city}, {best_result.state} (accuracy: {best_result.accuracy:.2f})")
        return best_result

    def _select_best_location(self, results: List[LocationResult]) -> LocationResult:
        """
        Select the best location result from multiple providers

        Args:
            results: List of location results from different providers

        Returns:
            Best location result based on accuracy and consistency
        """
        if len(results) == 1:
            return results[0]

        # Sort by accuracy
        results.sort(key=lambda x: x.accuracy, reverse=True)

        # Validate consistency between top results
        best = results[0]

        if len(results) > 1:
            # Check if top results agree on country and major location
            for result in results[1:]:
                if (result.country_code == best.country_code and
                    result.city == best.city):
                    # Results agree, boost confidence
                    best.accuracy = min(0.95, best.accuracy + 0.1)
                    break
                elif result.country_code != best.country_code:
                    # Country disagreement, reduce confidence
                    best.accuracy = max(0.3, best.accuracy - 0.2)

        return best

    def get_comprehensive_location(self, ip_address: str = None,
                                  lat: float = None, lon: float = None) -> Dict[str, Any]:
        """
        Get comprehensive location information using all available methods

        Args:
            ip_address: Optional IP address to lookup
            lat: Optional latitude from browser geolocation
            lon: Optional longitude from browser geolocation

        Returns:
            Comprehensive location dictionary with multiple data sources
        """
        result = {
            'ip_location': None,
            'browser_location': None,
            'primary_location': None,
            'confidence': 0.0,
            'timestamp': datetime.now().isoformat(),
            'methods_used': []
        }

        # Get IP-based location
        try:
            ip_location = self.get_location_from_ip(ip_address)
            if ip_location:
                result['ip_location'] = ip_location.to_dict()
                result['methods_used'].append('ip_geolocation')
                result['primary_location'] = ip_location.to_dict()
                result['confidence'] = ip_location.accuracy
        except Exception as e:
            logger.error(f"IP location failed: {e}")

        # If browser coordinates are provided, use reverse geocoding for validation
        if lat is not None and lon is not None:
            try:
                browser_location = self._reverse_geocode_coordinates(lat, lon)
                if browser_location:
                    result['browser_location'] = browser_location
                    result['methods_used'].append('browser_geolocation')

                    # Browser location is typically more accurate, use as primary
                    result['primary_location'] = browser_location
                    result['confidence'] = 0.9  # High confidence for browser geolocation
            except Exception as e:
                logger.error(f"Browser location processing failed: {e}")

        # Validate and merge data if we have both sources
        if result['ip_location'] and result['browser_location']:
            ip_loc = result['ip_location']
            browser_loc = result['browser_location']

            # Check if locations are reasonably close (same city/region)
            if (ip_loc['country_code'] == browser_loc.get('country_code') and
                ip_loc['city'] == browser_loc.get('city')):
                result['confidence'] = 0.95  # Very high confidence when sources agree
            else:
                # Use browser location but note the discrepancy
                result['confidence'] = 0.8
                result['location_discrepancy'] = True

        return result

    def _reverse_geocode_coordinates(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Reverse geocode coordinates to get address information

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Location dictionary or None if failed
        """
        try:
            # Use Nominatim for reverse geocoding
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'format': 'json',
                'lat': lat,
                'lon': lon,
                'zoom': 18,
                'addressdetails': 1
            }

            headers = {'User-Agent': 'WhatNowAI/1.0 Enhanced Location Service'}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            address = data.get('address', {})

            return {
                'latitude': lat,
                'longitude': lon,
                'city': (address.get('city') or address.get('town') or
                        address.get('village') or address.get('suburb') or ''),
                'state': (address.get('state') or address.get('county') or ''),
                'country': address.get('country', ''),
                'country_code': address.get('country_code', '').upper(),
                'zip_code': address.get('postcode', ''),
                'accuracy': 0.9,
                'source': 'browser_nominatim',
                'full_address': data.get('display_name', '')
            }

        except Exception as e:
            logger.error(f"Reverse geocoding failed: {e}")
            return None

    def validate_location(self, location_data: Dict[str, Any]) -> bool:
        """
        Validate location data for completeness and accuracy

        Args:
            location_data: Location dictionary to validate

        Returns:
            True if location data appears valid
        """
        required_fields = ['latitude', 'longitude', 'city', 'country']

        # Check required fields
        for field in required_fields:
            if not location_data.get(field):
                return False

        # Validate coordinate ranges
        lat = location_data.get('latitude', 0)
        lon = location_data.get('longitude', 0)

        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return False

        return True

    def get_location_for_address(self, address: str) -> Optional[LocationResult]:
        """
        Geocode an address to get location information

        Args:
            address: Address string to geocode

        Returns:
            LocationResult or None if geocoding failed
        """
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': address,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }

            headers = {'User-Agent': 'WhatNowAI/1.0 Enhanced Location Service'}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data:
                result = data[0]
                address_details = result.get('address', {})

                return LocationResult(
                    latitude=float(result['lat']),
                    longitude=float(result['lon']),
                    city=(address_details.get('city') or address_details.get('town') or
                          address_details.get('village') or ''),
                    state=(address_details.get('state') or address_details.get('county') or ''),
                    country=address_details.get('country', ''),
                    country_code=address_details.get('country_code', '').upper(),
                    zip_code=address_details.get('postcode', ''),
                    timezone='',  # Not provided by Nominatim
                    accuracy=0.8,
                    source='nominatim_geocoding',
                    continent='',
                    region_code=''
                )

            return None

        except Exception as e:
            logger.error(f"Address geocoding failed for '{address}': {e}")
            return None


# Global instance with configurable API key
def create_location_service(ipstack_key: str = None) -> EnhancedLocationService:
    """
    Create enhanced location service instance

    Args:
        ipstack_key: Optional IPStack API key for enhanced accuracy

    Returns:
        EnhancedLocationService instance
    """
    return EnhancedLocationService(ipstack_key=ipstack_key)
