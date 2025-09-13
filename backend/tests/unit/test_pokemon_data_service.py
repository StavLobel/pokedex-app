"""
Unit tests for Pokemon data service with mocked PokéAPI responses.
"""
import json
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.pokemon_data import PokemonDataService, get_pokemon_service, set_pokemon_service
from app.models.pokemon import PokemonData, PokemonSummary, PokemonNotFoundError, PokemonAPIError


class TestPokemonDataService:
    """Test cases for PokemonDataService."""
    
    @pytest.fixture
    def service(self):
        """Create a fresh service instance for each test."""
        return PokemonDataService(cache_ttl=1)  # Short TTL for testing
    
    @pytest.fixture
    def mock_pikachu_response(self):
        """Mock PokéAPI response for Pikachu."""
        return {
            "id": 25,
            "name": "pikachu",
            "base_experience": 112,
            "height": 4,
            "is_default": True,
            "order": 35,
            "weight": 60,
            "abilities": [
                {
                    "is_hidden": False,
                    "slot": 1,
                    "ability": {
                        "name": "static",
                        "url": "https://pokeapi.co/api/v2/ability/9/"
                    }
                },
                {
                    "is_hidden": True,
                    "slot": 3,
                    "ability": {
                        "name": "lightning-rod",
                        "url": "https://pokeapi.co/api/v2/ability/31/"
                    }
                }
            ],
            "forms": [
                {
                    "name": "pikachu",
                    "url": "https://pokeapi.co/api/v2/pokemon-form/25/"
                }
            ],
            "game_indices": [],
            "held_items": [],
            "location_area_encounters": "https://pokeapi.co/api/v2/pokemon/25/encounters",
            "moves": [],
            "species": {
                "name": "pikachu",
                "url": "https://pokeapi.co/api/v2/pokemon-species/25/"
            },
            "sprites": {
                "back_default": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/25.png",
                "back_female": None,
                "back_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/shiny/25.png",
                "back_shiny_female": None,
                "front_default": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png",
                "front_female": None,
                "front_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/25.png",
                "front_shiny_female": None,
                "other": {},
                "versions": {}
            },
            "stats": [
                {
                    "base_stat": 35,
                    "effort": 0,
                    "stat": {
                        "name": "hp",
                        "url": "https://pokeapi.co/api/v2/stat/1/"
                    }
                },
                {
                    "base_stat": 55,
                    "effort": 0,
                    "stat": {
                        "name": "attack",
                        "url": "https://pokeapi.co/api/v2/stat/2/"
                    }
                },
                {
                    "base_stat": 40,
                    "effort": 0,
                    "stat": {
                        "name": "defense",
                        "url": "https://pokeapi.co/api/v2/stat/3/"
                    }
                },
                {
                    "base_stat": 50,
                    "effort": 0,
                    "stat": {
                        "name": "special-attack",
                        "url": "https://pokeapi.co/api/v2/stat/4/"
                    }
                },
                {
                    "base_stat": 50,
                    "effort": 0,
                    "stat": {
                        "name": "special-defense",
                        "url": "https://pokeapi.co/api/v2/stat/5/"
                    }
                },
                {
                    "base_stat": 90,
                    "effort": 2,
                    "stat": {
                        "name": "speed",
                        "url": "https://pokeapi.co/api/v2/stat/6/"
                    }
                }
            ],
            "types": [
                {
                    "slot": 1,
                    "type": {
                        "name": "electric",
                        "url": "https://pokeapi.co/api/v2/type/13/"
                    }
                }
            ],
            "past_types": []
        }
    
    @pytest.mark.asyncio
    async def test_get_pokemon_by_id_success(self, service, mock_pikachu_response):
        """Test successful Pokemon fetch by ID."""
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_pikachu_response
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Test the service
            result = await service.get_pokemon_by_id(25)
            
            # Assertions
            assert isinstance(result, PokemonData)
            assert result.id == 25
            assert result.name == "pikachu"
            assert result.get_primary_type() == "electric"
            assert len(result.abilities) == 2
            assert result.sprites.front_default is not None
    
    @pytest.mark.asyncio
    async def test_get_pokemon_by_name_success(self, service, mock_pikachu_response):
        """Test successful Pokemon fetch by name."""
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_pikachu_response
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Test the service
            result = await service.get_pokemon_by_name("Pikachu")  # Test case insensitive
            
            # Assertions
            assert isinstance(result, PokemonData)
            assert result.id == 25
            assert result.name == "pikachu"
    
    @pytest.mark.asyncio
    async def test_get_pokemon_by_id_not_found(self, service):
        """Test Pokemon not found by ID."""
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock 404 response
            mock_response = MagicMock()
            mock_response.status_code = 404
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Test the service
            with pytest.raises(PokemonNotFoundError):
                await service.get_pokemon_by_id(99999)
    
    @pytest.mark.asyncio
    async def test_get_pokemon_by_name_not_found(self, service):
        """Test Pokemon not found by name."""
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock 404 response
            mock_response = MagicMock()
            mock_response.status_code = 404
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Test the service
            with pytest.raises(PokemonNotFoundError):
                await service.get_pokemon_by_name("nonexistent")
    
    @pytest.mark.asyncio
    async def test_caching_functionality(self, service, mock_pikachu_response):
        """Test that caching works correctly."""
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_pikachu_response
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # First call should hit the API
            result1 = await service.get_pokemon_by_id(25)
            
            # Second call should hit the cache (no additional API call)
            result2 = await service.get_pokemon_by_id(25)
            
            # Verify only one API call was made
            assert mock_client.return_value.__aenter__.return_value.get.call_count == 1
            
            # Results should be identical
            assert result1.id == result2.id
            assert result1.name == result2.name
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, service, mock_pikachu_response):
        """Test that cache expires correctly."""
        import time
        
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_pikachu_response
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # First call
            await service.get_pokemon_by_id(25)
            
            # Wait for cache to expire (TTL is 1 second in fixture)
            time.sleep(1.1)
            
            # Second call should hit the API again
            await service.get_pokemon_by_id(25)
            
            # Verify two API calls were made
            assert mock_client.return_value.__aenter__.return_value.get.call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_logic_success_after_failure(self, service, mock_pikachu_response):
        """Test retry logic succeeds after initial failure."""
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock responses: first fails, second succeeds
            mock_responses = [
                MagicMock(side_effect=httpx.RequestError("Connection failed")),
                MagicMock()
            ]
            mock_responses[1].status_code = 200
            mock_responses[1].json.return_value = mock_pikachu_response
            
            mock_client.return_value.__aenter__.return_value.get.side_effect = mock_responses
            
            # Test the service
            result = await service.get_pokemon_by_id(25)
            
            # Should succeed after retry
            assert result.id == 25
            assert result.name == "pikachu"
    
    @pytest.mark.asyncio
    async def test_retry_logic_max_retries_exceeded(self, service):
        """Test retry logic fails after max retries."""
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock to always fail
            mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.RequestError("Connection failed")
            
            # Test the service
            with pytest.raises(PokemonAPIError):
                await service.get_pokemon_by_id(25)
    
    @pytest.mark.asyncio
    async def test_get_pokemon_summary_by_id(self, service, mock_pikachu_response):
        """Test getting Pokemon summary by ID."""
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_pikachu_response
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Test the service
            result = await service.get_pokemon_summary_by_id(25)
            
            # Assertions
            assert isinstance(result, PokemonSummary)
            assert result.id == 25
            assert result.name == "pikachu"
            assert result.types == ["electric"]
            assert result.sprite_url is not None
    
    @pytest.mark.asyncio
    async def test_get_pokemon_summary_by_name(self, service, mock_pikachu_response):
        """Test getting Pokemon summary by name."""
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_pikachu_response
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Test the service
            result = await service.get_pokemon_summary_by_name("pikachu")
            
            # Assertions
            assert isinstance(result, PokemonSummary)
            assert result.id == 25
            assert result.name == "pikachu"
    
    @pytest.mark.asyncio
    async def test_cache_pokemon_data_manually(self, service, mock_pikachu_response):
        """Test manual caching of Pokemon data."""
        # Create Pokemon data object
        pokemon_data = PokemonData(**mock_pikachu_response)
        
        # Cache it manually
        await service.cache_pokemon_data(pokemon_data)
        
        # Verify it's in cache by checking cache stats
        stats = service.get_cache_stats()
        assert stats["total_entries"] >= 2  # Should have both ID and name entries
        assert stats["pokemon_by_id"] >= 1
        assert stats["pokemon_by_name"] >= 1
    
    def test_clear_cache(self, service):
        """Test cache clearing functionality."""
        # Add some data to cache
        service._set_cache("test_key", {"test": "data"})
        
        # Verify cache has data
        assert len(service._cache) > 0
        
        # Clear cache
        service.clear_cache()
        
        # Verify cache is empty
        assert len(service._cache) == 0
    
    def test_get_cache_stats(self, service):
        """Test cache statistics."""
        # Add some test data
        service._set_cache("pokemon_id_1", {"test": "data"})
        service._set_cache("pokemon_name_test", {"test": "data"})
        service._set_cache("other_key", {"test": "data"})
        
        stats = service.get_cache_stats()
        
        assert stats["total_entries"] == 3
        assert stats["pokemon_by_id"] == 1
        assert stats["pokemon_by_name"] == 1
    
    @pytest.mark.asyncio
    async def test_invalid_pokemon_id(self, service):
        """Test validation of Pokemon ID."""
        with pytest.raises(ValueError, match="Pokemon ID must be positive"):
            await service.get_pokemon_by_id(-1)
        
        with pytest.raises(ValueError, match="Pokemon ID must be positive"):
            await service.get_pokemon_by_id(0)
    
    @pytest.mark.asyncio
    async def test_invalid_pokemon_name(self, service):
        """Test validation of Pokemon name."""
        with pytest.raises(ValueError, match="Pokemon name cannot be empty"):
            await service.get_pokemon_by_name("")
        
        with pytest.raises(ValueError, match="Pokemon name cannot be empty"):
            await service.get_pokemon_by_name("   ")
    
    @pytest.mark.asyncio
    async def test_http_status_error_handling(self, service):
        """Test handling of various HTTP status errors."""
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock 500 response
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Server Error", request=MagicMock(), response=mock_response
            )
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Test the service
            with pytest.raises(PokemonAPIError):
                await service.get_pokemon_by_id(25)
    
    @pytest.mark.asyncio
    async def test_json_decode_error_handling(self, service):
        """Test handling of JSON decode errors."""
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock response with invalid JSON
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Test the service
            with pytest.raises(PokemonAPIError):
                await service.get_pokemon_by_id(25)


class TestGlobalServiceFunctions:
    """Test global service management functions."""
    
    def test_get_pokemon_service_singleton(self):
        """Test that get_pokemon_service returns the same instance."""
        service1 = get_pokemon_service()
        service2 = get_pokemon_service()
        
        assert service1 is service2
        assert isinstance(service1, PokemonDataService)
    
    @pytest.mark.asyncio
    async def test_set_pokemon_service(self):
        """Test setting a custom service instance."""
        custom_service = PokemonDataService(base_url="https://custom.api/")
        
        await set_pokemon_service(custom_service)
        
        retrieved_service = get_pokemon_service()
        assert retrieved_service is custom_service
        assert retrieved_service.base_url == "https://custom.api/"


class TestPokemonDataModel:
    """Test Pokemon data model methods."""
    
    @pytest.fixture
    def sample_pokemon_data(self):
        """Sample Pokemon data for testing."""
        return {
            "id": 25,
            "name": "pikachu",
            "base_experience": 112,
            "height": 4,
            "is_default": True,
            "order": 35,
            "weight": 60,
            "abilities": [
                {
                    "is_hidden": False,
                    "slot": 1,
                    "ability": {"name": "static", "url": "https://pokeapi.co/api/v2/ability/9/"}
                }
            ],
            "forms": [{"name": "pikachu", "url": "https://pokeapi.co/api/v2/pokemon-form/25/"}],
            "game_indices": [],
            "held_items": [],
            "location_area_encounters": "https://pokeapi.co/api/v2/pokemon/25/encounters",
            "moves": [],
            "species": {"name": "pikachu", "url": "https://pokeapi.co/api/v2/pokemon-species/25/"},
            "sprites": {
                "front_default": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png",
                "front_shiny": None,
                "back_default": None,
                "other": {},
                "versions": {}
            },
            "stats": [
                {"base_stat": 35, "effort": 0, "stat": {"name": "hp", "url": "https://pokeapi.co/api/v2/stat/1/"}},
                {"base_stat": 90, "effort": 2, "stat": {"name": "speed", "url": "https://pokeapi.co/api/v2/stat/6/"}}
            ],
            "types": [
                {"slot": 1, "type": {"name": "electric", "url": "https://pokeapi.co/api/v2/type/13/"}}
            ],
            "past_types": []
        }
    
    def test_pokemon_data_creation(self, sample_pokemon_data):
        """Test Pokemon data model creation."""
        pokemon = PokemonData(**sample_pokemon_data)
        
        assert pokemon.id == 25
        assert pokemon.name == "pikachu"
        assert pokemon.height == 4
        assert pokemon.weight == 60
    
    def test_pokemon_data_validation(self):
        """Test Pokemon data validation."""
        # Test invalid ID
        with pytest.raises(ValueError, match="Pokemon ID must be positive"):
            PokemonData(
                id=-1, name="test", height=1, weight=1, order=1,
                abilities=[], forms=[], game_indices=[], held_items=[],
                location_area_encounters="", moves=[], 
                species={"name": "test", "url": ""}, sprites={},
                stats=[], types=[], past_types=[]
            )
        
        # Test empty name
        with pytest.raises(ValueError, match="Pokemon name cannot be empty"):
            PokemonData(
                id=1, name="", height=1, weight=1, order=1,
                abilities=[], forms=[], game_indices=[], held_items=[],
                location_area_encounters="", moves=[],
                species={"name": "test", "url": ""}, sprites={},
                stats=[], types=[], past_types=[]
            )
    
    def test_pokemon_helper_methods(self, sample_pokemon_data):
        """Test Pokemon data helper methods."""
        pokemon = PokemonData(**sample_pokemon_data)
        
        # Test type methods
        assert pokemon.get_primary_type() == "electric"
        assert pokemon.get_all_types() == ["electric"]
        
        # Test abilities method
        assert pokemon.get_abilities_list() == ["static"]
        
        # Test stats method
        stats_dict = pokemon.get_base_stats_dict()
        assert stats_dict["hp"] == 35
        assert stats_dict["speed"] == 90
    
    def test_pokemon_summary_creation(self, sample_pokemon_data):
        """Test Pokemon summary creation from full data."""
        pokemon = PokemonData(**sample_pokemon_data)
        summary = PokemonSummary.from_pokemon_data(pokemon)
        
        assert summary.id == 25
        assert summary.name == "pikachu"
        assert summary.types == ["electric"]
        assert summary.height == 4
        assert summary.weight == 60
        assert summary.sprite_url == "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png"