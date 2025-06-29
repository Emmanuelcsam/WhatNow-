"""
Advanced Location Detection Service

This service provides accurate location detection using multiple sources
including IP-based geolocation, browser geolocation APIs, and fallback methods.
"""

import requests
import logging
import json
from typing import Dict, Optional, List, Tuple
from urllib.parse import urljoin
import socket
import time

logger = logging.getLogger(__name__)


class LocationDetectionService:
    """Advanced location detection using multiple sources"""
    
    def __init__(self):
        """Initialize the location detection service"""
        self.timeout = 5
        self.user_agent = "WhatNowAI/1.0 (Location Detection Service)"
        
        # Multiple IP geolocation services as fallbacks
        self.ip_services = [
            {
                'name': 'ipapi',
                'url': 'http://ip-api.com/json/',
                'parser': self._parse_ipapi_response
            },
            {
                'name': 'ipinfo',
                'url': 'https://ipinfo.io/json',
                'parser': self._parse_ipinfo_response
            },
            {
                'name': 'freeipapi',
                'url': 'https://freeipapi.com/api/json/',
                'parser': self._parse_freeipapi_response
            }
        ]
    
    def get_user_location(self, request_ip: Optional[str] = None) -> Dict:
        """
        Get user location using multiple detection methods
        
        Args:
            request_ip: Optional IP address to geolocate
            
        Returns:
            Dictionary with location information
        """
        location_data = {
            'latitude': None,
            'longitude': None,
            'city': 'Unknown',
            'state': 'Unknown',
            'country': 'Unknown',
            'confidence': 0.0,
            'source': 'unknown',
            'accuracy': 'low'
        }
        
        # Try multiple detection methods
        methods = [
            ('ip_geolocation', self._detect_by_ip),
            ('public_ip_lookup', self._detect_by_public_ip),
            ('fallback_services', self._detect_fallback)
        ]
        
        for method_name, method_func in methods:
            try:
                logger.info(f"Trying location detection method: {method_name}")
                result = method_func(request_ip)
                
                if result and result.get('latitude') and result.get('longitude'):
                    # Validate coordinates are reasonable
                    lat, lon = result['latitude'], result['longitude']
                    if self._validate_coordinates(lat, lon):
                        result['source'] = method_name
                        result['accuracy'] = 'high' if method_name == 'ip_geolocation' else 'medium'
                        logger.info(f"Location detected via {method_name}: {result['city']}, {result['state']}")
                        return result
                        
            except Exception as e:
                logger.warning(f"Location detection method {method_name} failed: {e}")
                continue
        
        logger.warning("All location detection methods failed, using default")
        return location_data
    
    def _detect_by_ip(self, ip_address: Optional[str] = None) -> Optional[Dict]:
        """Detect location using IP geolocation services"""
        if not ip_address:
            ip_address = self._get_public_ip()
            
        if not ip_address or ip_address in ['127.0.0.1', 'localhost']:
            return None
            
        for service in self.ip_services:
            try:
                url = service['url']
                if service['name'] == 'ipapi':
                    url = f"{url}{ip_address}"
                elif service['name'] == 'freeipapi':
                    url = f"{url}{ip_address}"
                    
                response = requests.get(
                    url,
                    headers={'User-Agent': self.user_agent},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    location = service['parser'](data)
                    if location:
                        logger.info(f"Location detected via {service['name']}")
                        return location
                        
            except Exception as e:
                logger.warning(f"IP service {service['name']} failed: {e}")
                continue
                
        return None
    
    def _detect_by_public_ip(self, ip_address: Optional[str] = None) -> Optional[Dict]:
        """Alternative IP-based detection method"""
        try:
            # Get public IP if not provided
            if not ip_address:
                ip_response = requests.get('https://api.ipify.org', timeout=self.timeout)
                ip_address = ip_response.text.strip()
            
            # Use different service for geolocation
            geo_url = f"https://freegeoip.app/json/{ip_address}"
            response = requests.get(geo_url, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                    'city': data.get('city', 'Unknown'),
                    'state': data.get('region_name', 'Unknown'),
                    'country': data.get('country_name', 'Unknown'),
                    'confidence': 0.8
                }
                
        except Exception as e:
            logger.warning(f"Public IP detection failed: {e}")
            
        return None
    
    def _detect_fallback(self, ip_address: Optional[str] = None) -> Optional[Dict]:
        """Fallback detection using alternative services"""
        fallback_services = [
            'https://ipwho.is/',
            'https://ipgeolocation.abstractapi.com/v1/?api_key=free'
        ]
        
        for service_url in fallback_services:
            try:
                response = requests.get(service_url, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Generic parser for common response formats
                    lat = data.get('latitude') or data.get('lat')
                    lon = data.get('longitude') or data.get('lng') or data.get('lon')
                    city = data.get('city') or data.get('city_name')
                    state = data.get('region') or data.get('state') or data.get('region_name')
                    country = data.get('country') or data.get('country_name')
                    
                    if lat and lon:
                        return {
                            'latitude': float(lat),
                            'longitude': float(lon),
                            'city': city or 'Unknown',
                            'state': state or 'Unknown',
                            'country': country or 'Unknown',
                            'confidence': 0.6
                        }
                        
            except Exception as e:
                logger.warning(f"Fallback service failed: {e}")
                continue
                
        return None
    
    def _get_public_ip(self) -> Optional[str]:
        """Get the public IP address"""
        ip_services = [
            'https://api.ipify.org',
            'https://ipecho.net/plain',
            'https://myexternalip.com/raw'
        ]
        
        for service in ip_services:
            try:
                response = requests.get(service, timeout=self.timeout)
                if response.status_code == 200:
                    ip = response.text.strip()
                    if self._validate_ip(ip):
                        return ip
            except Exception:
                continue
                
        return None
    
    def _validate_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        try:
            socket.inet_aton(ip)
            return not ip.startswith(('127.', '192.168.', '10.', '172.'))
        except socket.error:
            return False
    
    def _validate_coordinates(self, lat: float, lon: float) -> bool:
        """Validate latitude and longitude values"""
        try:
            lat, lon = float(lat), float(lon)
            return -90 <= lat <= 90 and -180 <= lon <= 180
        except (ValueError, TypeError):
            return False
    
    def _parse_ipapi_response(self, data: Dict) -> Optional[Dict]:
        """Parse ip-api.com response"""
        if data.get('status') == 'success':
            return {
                'latitude': data.get('lat'),
                'longitude': data.get('lon'),
                'city': data.get('city', 'Unknown'),
                'state': data.get('regionName', 'Unknown'),
                'country': data.get('country', 'Unknown'),
                'confidence': 0.9
            }
        return None
    
    def _parse_ipinfo_response(self, data: Dict) -> Optional[Dict]:
        """Parse ipinfo.io response"""
        if 'loc' in data:
            lat, lon = data['loc'].split(',')
            return {
                'latitude': float(lat),
                'longitude': float(lon),
                'city': data.get('city', 'Unknown'),
                'state': data.get('region', 'Unknown'),
                'country': data.get('country', 'Unknown'),
                'confidence': 0.8
            }
        return None
    
    def _parse_freeipapi_response(self, data: Dict) -> Optional[Dict]:
        """Parse freeipapi.com response"""
        return {
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
            'city': data.get('cityName', 'Unknown'),
            'state': data.get('regionName', 'Unknown'),
            'country': data.get('countryName', 'Unknown'),
            'confidence': 0.7
        }
    
    def get_location_alternatives(self, primary_location: Dict) -> List[Dict]:
        """
        Get alternative location suggestions based on different methods
        
        Args:
            primary_location: Primary location data
            
        Returns:
            List of alternative location suggestions
        """
        alternatives = []
        
        # Try each service independently
        for service in self.ip_services:
            try:
                response = requests.get(
                    service['url'],
                    headers={'User-Agent': self.user_agent},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    location = service['parser'](data)
                    if location and location != primary_location:
                        location['source'] = service['name']
                        alternatives.append(location)
                        
            except Exception as e:
                logger.debug(f"Alternative service {service['name']} failed: {e}")
                continue
        
        return alternatives[:3]  # Return top 3 alternatives