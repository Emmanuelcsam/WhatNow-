"""
DNS Resolver Module with Fallback Support
"""
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Try to import DNS module with fallback
DNS_AVAILABLE = False
try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    logger.warning("dnspython not available, using fallback DNS resolution")

def resolve_domain(domain: str) -> Optional[List[str]]:
    """
    Resolve domain to IP addresses with fallback support
    
    Args:
        domain: Domain name to resolve
        
    Returns:
        List of IP addresses or None if resolution fails
    """
    if DNS_AVAILABLE:
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 5
            resolver.lifetime = 5
            
            answers = resolver.resolve(domain, 'A')
            return [str(rdata) for rdata in answers]
        except Exception as e:
            logger.debug(f"DNS resolution failed for {domain}: {e}")
            return None
    else:
        # Fallback: Use socket for basic resolution
        import socket
        try:
            return [socket.gethostbyname(domain)]
        except socket.gaierror:
            return None

def is_dns_available() -> bool:
    """Check if DNS module is available"""
    return DNS_AVAILABLE