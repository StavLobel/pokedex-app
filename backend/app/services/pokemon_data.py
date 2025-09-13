"""
Pokemon data service for fetching and caching Pokemon information from PokéAPI.
"""
import asyncio
import json
import logging
from typing import Optional, Dict, Any
from urllib.parse import urljoin

import httpx
from app.models.pokemon import (
    PokemonData,
    PokemonSummary,
    PokemonNotFoundError,
    PokemonAPIError
)

logger = logging.getLogger(__name__)


class PokemonDataService:
    """Service for fetching Pokemon data from PokéAPI with caching and retry logic."""
    
    def __init__(
        self,
        base_url: str = "https://pokeapi.co/api/v2/",
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        cache_ttl: int = 3600  # 1 hour in seconds
    ):
        """
        Initialize the Pokemon data service.
        
        Args:
            base_url: Base URL for PokéAPI
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            cache_ttl: Cache time-to-live in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.cache_ttl = cache_ttl
        
        # In-memory cache for Pokemon data
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # HTTP client configuration
        self._client_config = {
            "timeout": httpx.Timeout(timeout),
            "limits": httpx.Limits(max_keepalive_connections=20, max_connections=100),
            "headers": {
                "User-Agent": "Pokemon-Recognition-App/1.0",
                "Accept": "application/json"
            }
        }
    
    async def get_pokemon_by_id(self, pokemon_id: int) -> PokemonData:
        """
        Fetch Pokemon data by ID.
        
        Args:
            pokemon_id: Pokemon ID (1-1010+)
            
        Returns:
            PokemonData: Complete Pokemon information
            
        Raises:
            PokemonNotFoundError: If Pokemon with given ID doesn't exist
            PokemonAPIError: If there's an API error
        """
        if pokemon_id <= 0:
            raise ValueError("Pokemon ID must be positive")
        
        cache_key = f"pokemon_id_{pokemon_id}"
        
        # Check cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for Pokemon ID {pokemon_id}")
            return PokemonData(**cached_data)
        
        # Fetch from API
        url = urljoin(self.base_url, f"pokemon/{pokemon_id}")
        data = await self._fetch_with_retry(url)
        
        # Cache the result
        self._set_cache(cache_key, data)
        
        logger.info(f"Fetched Pokemon data for ID {pokemon_id}")
        return PokemonData(**data)
    
    async def get_pokemon_by_name(self, pokemon_name: str) -> PokemonData:
        """
        Fetch Pokemon data by name.
        
        Args:
            pokemon_name: Pokemon name (case-insensitive)
            
        Returns:
            PokemonData: Complete Pokemon information
            
        Raises:
            PokemonNotFoundError: If Pokemon with given name doesn't exist
            PokemonAPIError: If there's an API error
        """
        if not pokemon_name or not pokemon_name.strip():
            raise ValueError("Pokemon name cannot be empty")
        
        # Normalize name (lowercase, strip whitespace)
        normalized_name = pokemon_name.lower().strip()
        cache_key = f"pokemon_name_{normalized_name}"
        
        # Check cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for Pokemon name {normalized_name}")
            return PokemonData(**cached_data)
        
        # Fetch from API
        url = urljoin(self.base_url, f"pokemon/{normalized_name}")
        data = await self._fetch_with_retry(url)
        
        # Cache the result with both name and ID keys
        self._set_cache(cache_key, data)
        self._set_cache(f"pokemon_id_{data['id']}", data)
        
        logger.info(f"Fetched Pokemon data for name {normalized_name}")
        return PokemonData(**data)
    
    async def get_pokemon_summary_by_id(self, pokemon_id: int) -> PokemonSummary:
        """
        Get a simplified Pokemon summary by ID.
        
        Args:
            pokemon_id: Pokemon ID
            
        Returns:
            PokemonSummary: Simplified Pokemon information
        """
        pokemon_data = await self.get_pokemon_by_id(pokemon_id)
        return PokemonSummary.from_pokemon_data(pokemon_data)
    
    async def get_pokemon_summary_by_name(self, pokemon_name: str) -> PokemonSummary:
        """
        Get a simplified Pokemon summary by name.
        
        Args:
            pokemon_name: Pokemon name
            
        Returns:
            PokemonSummary: Simplified Pokemon information
        """
        pokemon_data = await self.get_pokemon_by_name(pokemon_name)
        return PokemonSummary.from_pokemon_data(pokemon_data)
    
    async def cache_pokemon_data(self, pokemon_data: PokemonData) -> None:
        """
        Manually cache Pokemon data.
        
        Args:
            pokemon_data: Pokemon data to cache
        """
        data_dict = pokemon_data.model_dump()
        self._set_cache(f"pokemon_id_{pokemon_data.id}", data_dict)
        self._set_cache(f"pokemon_name_{pokemon_data.name}", data_dict)
        logger.debug(f"Manually cached Pokemon data for {pokemon_data.name} (ID: {pokemon_data.id})")
    
    def clear_cache(self) -> None:
        """Clear all cached Pokemon data."""
        self._cache.clear()
        logger.info("Pokemon data cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "total_entries": len(self._cache),
            "pokemon_by_id": len([k for k in self._cache.keys() if k.startswith("pokemon_id_")]),
            "pokemon_by_name": len([k for k in self._cache.keys() if k.startswith("pokemon_name_")])
        }
    
    async def _fetch_with_retry(self, url: str) -> Dict[str, Any]:
        """
        Fetch data from URL with retry logic.
        
        Args:
            url: URL to fetch
            
        Returns:
            Dict containing the JSON response
            
        Raises:
            PokemonNotFoundError: If Pokemon is not found (404)
            PokemonAPIError: If there's an API error
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(**self._client_config) as client:
                    response = await client.get(url)
                    
                    if response.status_code == 404:
                        raise PokemonNotFoundError(f"Pokemon not found at {url}")
                    
                    if response.status_code == 200:
                        return response.json()
                    
                    # Handle other HTTP errors
                    response.raise_for_status()
                    
            except httpx.HTTPStatusError as e:
                last_exception = e
                if e.response.status_code == 404:
                    raise PokemonNotFoundError(f"Pokemon not found at {url}")
                logger.warning(f"HTTP error on attempt {attempt + 1}: {e}")
                
            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_exception = e
                logger.warning(f"Request error on attempt {attempt + 1}: {e}")
                
            except json.JSONDecodeError as e:
                last_exception = e
                logger.warning(f"JSON decode error on attempt {attempt + 1}: {e}")
            
            # Wait before retrying (except on last attempt)
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
        
        # All retries failed
        raise PokemonAPIError(f"Failed to fetch data from {url} after {self.max_retries + 1} attempts: {last_exception}")
    
    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache if not expired."""
        if key not in self._cache:
            return None
        
        cache_entry = self._cache[key]
        
        # Check if cache entry has expired
        import time
        if time.time() - cache_entry["timestamp"] > self.cache_ttl:
            del self._cache[key]
            return None
        
        return cache_entry["data"]
    
    def _set_cache(self, key: str, data: Dict[str, Any]) -> None:
        """Set data in cache with timestamp."""
        import time
        self._cache[key] = {
            "data": data,
            "timestamp": time.time()
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Clean up resources if needed
        pass


# Global service instance
_pokemon_service: Optional[PokemonDataService] = None


def get_pokemon_service() -> PokemonDataService:
    """Get or create the global Pokemon data service instance."""
    global _pokemon_service
    if _pokemon_service is None:
        _pokemon_service = PokemonDataService()
    return _pokemon_service


async def set_pokemon_service(service: PokemonDataService) -> None:
    """Set a custom Pokemon data service instance (useful for testing)."""
    global _pokemon_service
    _pokemon_service = service