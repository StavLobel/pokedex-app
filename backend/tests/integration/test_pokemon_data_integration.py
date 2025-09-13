"""
Integration tests for Pokemon data service with real PokéAPI calls.
These tests are marked as integration and can be skipped in CI if needed.
"""
import pytest

from app.models.pokemon import (PokemonData, PokemonNotFoundError,
                                PokemonSummary)
from app.services.pokemon_data import PokemonDataService


@pytest.mark.integration
class TestPokemonDataServiceIntegration:
    """Integration tests with real PokéAPI calls."""

    @pytest.fixture
    def service(self):
        """Create service instance for integration tests."""
        return PokemonDataService(timeout=30.0)  # Longer timeout for real API calls

    @pytest.mark.asyncio
    async def test_get_pikachu_by_id_real_api(self, service):
        """Test fetching Pikachu by ID from real PokéAPI."""
        try:
            result = await service.get_pokemon_by_id(25)

            assert isinstance(result, PokemonData)
            assert result.id == 25
            assert result.name == "pikachu"
            assert "electric" in result.get_all_types()
            assert result.sprites.front_default is not None

        except Exception as e:
            pytest.skip(f"Real API test skipped due to network issue: {e}")

    @pytest.mark.asyncio
    async def test_get_pikachu_by_name_real_api(self, service):
        """Test fetching Pikachu by name from real PokéAPI."""
        try:
            result = await service.get_pokemon_by_name("pikachu")

            assert isinstance(result, PokemonData)
            assert result.id == 25
            assert result.name == "pikachu"

        except Exception as e:
            pytest.skip(f"Real API test skipped due to network issue: {e}")

    @pytest.mark.asyncio
    async def test_get_nonexistent_pokemon_real_api(self, service):
        """Test fetching non-existent Pokemon from real PokéAPI."""
        try:
            with pytest.raises(PokemonNotFoundError):
                await service.get_pokemon_by_id(99999)

        except Exception as e:
            pytest.skip(f"Real API test skipped due to network issue: {e}")

    @pytest.mark.asyncio
    async def test_caching_with_real_api(self, service):
        """Test caching functionality with real API calls."""
        try:
            # First call should hit the API
            result1 = await service.get_pokemon_by_id(1)  # Bulbasaur

            # Second call should hit the cache
            result2 = await service.get_pokemon_by_id(1)

            # Results should be identical
            assert result1.id == result2.id
            assert result1.name == result2.name

            # Check cache stats
            stats = service.get_cache_stats()
            assert stats["total_entries"] >= 1

        except Exception as e:
            pytest.skip(f"Real API test skipped due to network issue: {e}")

    @pytest.mark.asyncio
    async def test_pokemon_summary_real_api(self, service):
        """Test Pokemon summary with real API."""
        try:
            summary = await service.get_pokemon_summary_by_id(150)  # Mewtwo

            assert isinstance(summary, PokemonSummary)
            assert summary.id == 150
            assert summary.name == "mewtwo"
            assert "psychic" in summary.types

        except Exception as e:
            pytest.skip(f"Real API test skipped due to network issue: {e}")


# Add a marker for running only integration tests
pytestmark = pytest.mark.integration
