"""
location_service.py - Location detection and management service
"""
import logging
import requests
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import geocoder
import ipinfo
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import pytz
from timezonefinder import TimezoneFinder

logger = logging.getLogger(__name__)

@dataclass
class LocationData:
    """User location information"""
    ip_address: str
    country: str
    country_code: str
    region: str
    city: str
    latitude: float
    longitude: float
    timezone: str
    postal_code: Optional[str] = None
    isp: Optional[str] = None
    accuracy_radius: Optional[int] = None
    detected_at: datetime = None
    
    def __post_init__(self):
        if self.detected_at is None:
            self.detected_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "ip_address": self.ip_address,
            "country": self.country,
            "country_code": self.country_code,
            "region": self.region,
            "city": self.city,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timezone": self.timezone,
            "postal_code": self.postal_code,
            "isp": self.isp,
            "accuracy_radius": self.accuracy_radius,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None
        }
    
    def get_coordinates(self) -> Tuple[float, float]:
        """Get coordinates as tuple"""
        return (self.latitude, self.longitude)
    
    def get_local_time(self) -> datetime:
        """Get current time in user's timezone"""
        tz = pytz.timezone(self.timezone)
        return datetime.now(tz)

class LocationService:
    """Service for detecting and managing user location"""
    
    def __init__(self, ipinfo_token: Optional[str] = None):
        self.ipinfo_token = ipinfo_token
        self.geolocator = Nominatim(user_agent="event-discovery-app")
        self.tf = TimezoneFinder()
        
        # Initialize IPInfo handler if token provided
        self.ipinfo_handler = None
        if ipinfo_token:
            try:
                self.ipinfo_handler = ipinfo.getHandler(ipinfo_token)
            except Exception as e:
                logger.warning(f"Failed to initialize IPInfo handler: {e}")
    
    def get_location_from_ip(self, ip_address: Optional[str] = None) -> Optional[LocationData]:
        """
        Get location data from IP address
        
        Args:
            ip_address: IP address to lookup (None for current IP)
            
        Returns:
            LocationData object or None if failed
        """
        try:
            # Try IPInfo first (most accurate)
            if self.ipinfo_handler:
                try:
                    details = self.ipinfo_handler.getDetails(ip_address)
                    
                    # Parse coordinates
                    if hasattr(details, 'loc'):
                        lat, lon = map(float, details.loc.split(','))
                    else:
                        lat, lon = 0.0, 0.0
                    
                    # Get timezone
                    timezone = details.timezone if hasattr(details, 'timezone') else 'UTC'
                    
                    return LocationData(
                        ip_address=details.ip,
                        country=details.country_name if hasattr(details, 'country_name') else details.country,
                        country_code=details.country if hasattr(details, 'country') else '',
                        region=details.region if hasattr(details, 'region') else '',
                        city=details.city if hasattr(details, 'city') else '',
                        latitude=lat,
                        longitude=lon,
                        timezone=timezone,
                        postal_code=details.postal if hasattr(details, 'postal') else None,
                        isp=details.org if hasattr(details, 'org') else None
                    )
                except Exception as e:
                    logger.error(f"IPInfo lookup failed: {e}")
            
            # Fallback to free services
            return self._fallback_ip_lookup(ip_address)
            
        except Exception as e:
            logger.error(f"Failed to get location from IP: {e}")
            return None
    
    def _fallback_ip_lookup(self, ip_address: Optional[str] = None) -> Optional[LocationData]:
        """Fallback IP lookup using free services"""
        services = [
            ("http://ip-api.com/json/", self._parse_ip_api),
            ("https://ipapi.co/json/", self._parse_ipapi_co),
            ("https://freegeoip.app/json/", self._parse_freegeoip)
        ]
        
        for url, parser in services:
            try:
                if ip_address:
                    url = f"{url}{ip_address}"
                
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    location_data = parser(data)
                    if location_data:
                        return location_data
            except Exception as e:
                logger.debug(f"Failed to use {url}: {e}")
                continue
        
        return None
    
    def _parse_ip_api(self, data: Dict) -> Optional[LocationData]:
        """Parse ip-api.com response"""
        if data.get('status') != 'success':
            return None
        
        timezone = data.get('timezone', 'UTC')
        if not timezone:
            # Calculate timezone from coordinates
            timezone = self.tf.timezone_at(lat=data['lat'], lng=data['lon']) or 'UTC'
        
        return LocationData(
            ip_address=data.get('query', ''),
            country=data.get('country', ''),
            country_code=data.get('countryCode', ''),
            region=data.get('regionName', ''),
            city=data.get('city', ''),
            latitude=data.get('lat', 0.0),
            longitude=data.get('lon', 0.0),
            timezone=timezone,
            postal_code=data.get('zip'),
            isp=data.get('isp')
        )
    
    def _parse_ipapi_co(self, data: Dict) -> Optional[LocationData]:
        """Parse ipapi.co response"""
        if 'error' in data:
            return None
        
        return LocationData(
            ip_address=data.get('ip', ''),
            country=data.get('country_name', ''),
            country_code=data.get('country_code', ''),
            region=data.get('region', ''),
            city=data.get('city', ''),
            latitude=data.get('latitude', 0.0),
            longitude=data.get('longitude', 0.0),
            timezone=data.get('timezone', 'UTC'),
            postal_code=data.get('postal'),
            isp=data.get('org')
        )
    
    def _parse_freegeoip(self, data: Dict) -> Optional[LocationData]:
        """Parse freegeoip.app response"""
        timezone = data.get('time_zone', '')
        if not timezone:
            timezone = self.tf.timezone_at(
                lat=data.get('latitude', 0), 
                lng=data.get('longitude', 0)
            ) or 'UTC'
        
        return LocationData(
            ip_address=data.get('ip', ''),
            country=data.get('country_name', ''),
            country_code=data.get('country_code', ''),
            region=data.get('region_name', ''),
            city=data.get('city', ''),
            latitude=data.get('latitude', 0.0),
            longitude=data.get('longitude', 0.0),
            timezone=timezone,
            postal_code=data.get('zip_code')
        )
    
    def get_location_from_coordinates(self, latitude: float, longitude: float) -> Optional[LocationData]:
        """
        Get location data from coordinates (reverse geocoding)
        
        Args:
            latitude: Latitude
            longitude: Longitude
            
        Returns:
            LocationData object or None if failed
        """
        try:
            # Use Nominatim for reverse geocoding
            location = self.geolocator.reverse(f"{latitude}, {longitude}", language='en')
            
            if location and location.raw:
                address = location.raw.get('address', {})
                
                # Get timezone
                timezone = self.tf.timezone_at(lat=latitude, lng=longitude) or 'UTC'
                
                # Try to get current IP
                ip_address = self._get_current_ip()
                
                return LocationData(
                    ip_address=ip_address or '',
                    country=address.get('country', ''),
                    country_code=address.get('country_code', '').upper(),
                    region=address.get('state', address.get('region', '')),
                    city=address.get('city', address.get('town', address.get('village', ''))),
                    latitude=latitude,
                    longitude=longitude,
                    timezone=timezone,
                    postal_code=address.get('postcode')
                )
        except Exception as e:
            logger.error(f"Failed to reverse geocode: {e}")
        
        return None
    
    def get_location_from_address(self, address: str) -> Optional[LocationData]:
        """
        Get location data from address string
        
        Args:
            address: Address string to geocode
            
        Returns:
            LocationData object or None if failed
        """
        try:
            location = self.geolocator.geocode(address)
            
            if location:
                return self.get_location_from_coordinates(
                    location.latitude,
                    location.longitude
                )
        except Exception as e:
            logger.error(f"Failed to geocode address: {e}")
        
        return None
    
    def _get_current_ip(self) -> Optional[str]:
        """Get current public IP address"""
        try:
            response = requests.get('https://api.ipify.org', timeout=5)
            return response.text.strip()
        except:
            return None
    
    def calculate_distance(self, loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """
        Calculate distance between two locations in miles
        
        Args:
            loc1: (latitude, longitude) tuple
            loc2: (latitude, longitude) tuple
            
        Returns:
            Distance in miles
        """
        return geodesic(loc1, loc2).miles
    
    def is_within_radius(self, center: Tuple[float, float], point: Tuple[float, float], 
                        radius_miles: float) -> bool:
        """
        Check if a point is within radius of center
        
        Args:
            center: Center point (latitude, longitude)
            point: Point to check (latitude, longitude)
            radius_miles: Radius in miles
            
        Returns:
            True if within radius
        """
        distance = self.calculate_distance(center, point)
        return distance <= radius_miles
    
    def get_timezone_offset(self, timezone_str: str) -> int:
        """
        Get current UTC offset for timezone in hours
        
        Args:
            timezone_str: Timezone string (e.g., 'America/New_York')
            
        Returns:
            UTC offset in hours
        """
        try:
            tz = pytz.timezone(timezone_str)
            now = datetime.now(tz)
            offset = now.utcoffset()
            return int(offset.total_seconds() / 3600)
        except Exception as e:
            logger.error(f"Failed to get timezone offset: {e}")
            return 0
    
    def enrich_location_data(self, location: LocationData) -> LocationData:
        """
        Enrich location data with additional information
        
        Args:
            location: LocationData object to enrich
            
        Returns:
            Enriched LocationData object
        """
        try:
            # Add accuracy radius based on detection method
            if not location.accuracy_radius:
                if location.postal_code:
                    location.accuracy_radius = 1  # 1 mile for postal code
                elif location.city:
                    location.accuracy_radius = 5  # 5 miles for city
                elif location.region:
                    location.accuracy_radius = 50  # 50 miles for region
                else:
                    location.accuracy_radius = 100  # 100 miles for country
            
            # Ensure timezone is set
            if not location.timezone or location.timezone == 'UTC':
                tz = self.tf.timezone_at(lat=location.latitude, lng=location.longitude)
                if tz:
                    location.timezone = tz
            
        except Exception as e:
            logger.error(f"Failed to enrich location data: {e}")
        
        return location
