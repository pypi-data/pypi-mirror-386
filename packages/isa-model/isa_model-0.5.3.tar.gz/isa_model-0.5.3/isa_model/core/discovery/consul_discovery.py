#!/usr/bin/env python3
"""
Consul Service Discovery Client for Model Service
Provides service discovery capabilities to find other services via Consul
"""

import logging
import os
from typing import Optional, List, Dict, Any
import consul
import random

logger = logging.getLogger(__name__)


class ConsulServiceDiscovery:
    """Consul service discovery client for Model service"""
    
    def __init__(self, consul_host: str = None, consul_port: int = None):
        """Initialize Consul client for service discovery"""
        self.consul_host = consul_host or os.getenv("CONSUL_HOST", "localhost")
        self.consul_port = consul_port or int(os.getenv("CONSUL_PORT", "8500"))
        
        try:
            self._consul = consul.Consul(host=self.consul_host, port=self.consul_port)
            # Test connection
            self._consul.agent.self()
            logger.info(f"Connected to Consul at {self.consul_host}:{self.consul_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Consul: {e}")
            self._consul = None
    
    def get_service_url(self, service_name: str, default_url: Optional[str] = None) -> Optional[str]:
        """
        Get service URL from Consul by service name
        
        Args:
            service_name: Name of the service to discover (e.g., 'mcp', 'agent')
            default_url: Fallback URL if service not found or Consul unavailable
            
        Returns:
            Service URL (http://host:port) or default_url if not found
        """
        if not self._consul:
            logger.warning(f"Consul not available, using default URL for {service_name}")
            return default_url
            
        try:
            # Get healthy service instances
            _, services = self._consul.health.service(service_name, passing=True)
            
            if not services:
                logger.warning(f"No healthy instances found for service '{service_name}'")
                return default_url
            
            # Use random selection for load balancing
            service = random.choice(services)
            service_info = service['Service']
            address = service_info.get('Address', 'localhost')
            port = service_info.get('Port', 80)
            
            # Build service URL
            service_url = f"http://{address}:{port}"
            logger.info(f"Discovered service '{service_name}' at {service_url}")
            return service_url
            
        except Exception as e:
            logger.error(f"Failed to discover service '{service_name}': {e}")
            return default_url
    
    def discover_all_instances(self, service_name: str) -> List[Dict[str, Any]]:
        """
        Discover all healthy instances of a service
        
        Args:
            service_name: Name of the service to discover
            
        Returns:
            List of service instances with their details
        """
        if not self._consul:
            return []
            
        try:
            _, services = self._consul.health.service(service_name, passing=True)
            
            instances = []
            for service in services:
                service_info = service['Service']
                instances.append({
                    'id': service_info.get('ID'),
                    'name': service_info.get('Service'),
                    'address': service_info.get('Address'),
                    'port': service_info.get('Port'),
                    'tags': service_info.get('Tags', []),
                    'url': f"http://{service_info.get('Address')}:{service_info.get('Port')}"
                })
            
            return instances
            
        except Exception as e:
            logger.error(f"Failed to discover instances for '{service_name}': {e}")
            return []
    
    def resolve_service_url(self, url: str) -> str:
        """
        Resolve service URL - supports consul:// URLs for service discovery
        
        Args:
            url: URL to resolve (can be consul://service_name/path or regular URL)
            
        Returns:
            Resolved URL with actual service address
        """
        if not url or not url.startswith("consul://"):
            return url
        
        # Parse consul URL: consul://service_name/path
        parts = url.replace("consul://", "").split("/", 1)
        service_name = parts[0]
        path = "/" + parts[1] if len(parts) > 1 else ""
        
        # Default URLs for common services
        defaults = {
            "mcp": os.getenv("MCP_BASE_URL", "http://localhost:8081"),
            "agent": os.getenv("AGENT_URL", "http://localhost:8080"),
            "auth": os.getenv("AUTH_SERVICE_URL", "http://localhost:8202"),
            "storage": os.getenv("STORAGE_SERVICE_URL", "http://localhost:8109"),
            "redis": os.getenv("REDIS_URL", "redis://localhost:6379")
        }
        
        # Discover service URL
        discovered_url = self.get_service_url(service_name, defaults.get(service_name))
        if discovered_url:
            return discovered_url + path
        
        # Fallback to original URL if discovery fails
        return url
    
    def is_available(self) -> bool:
        """Check if Consul connection is available"""
        if not self._consul:
            return False
        
        try:
            self._consul.agent.self()
            return True
        except:
            return False


# Global instance for singleton pattern
_discovery_instance = None


def get_consul_discovery() -> ConsulServiceDiscovery:
    """Get global Consul discovery instance (singleton)"""
    global _discovery_instance
    if _discovery_instance is None:
        _discovery_instance = ConsulServiceDiscovery()
    return _discovery_instance


def discover_service(service_name: str, default_url: Optional[str] = None) -> Optional[str]:
    """
    Convenient function to discover service URL
    
    Args:
        service_name: Name of the service to discover
        default_url: Fallback URL if discovery fails
        
    Returns:
        Service URL or default_url
    """
    discovery = get_consul_discovery()
    return discovery.get_service_url(service_name, default_url)


def resolve_url(url: str) -> str:
    """
    Resolve URL with Consul service discovery support
    
    Args:
        url: URL to resolve (supports consul:// prefix)
        
    Returns:
        Resolved URL with actual service address
    """
    discovery = get_consul_discovery()
    return discovery.resolve_service_url(url)