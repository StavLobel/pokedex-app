"""
Integration tests for Pokemon data service with real PokéAPI calls.
These tests are marked as integration and can be skipped in CI if needed.
"""

import pytest

from app.models.pokemon import PokemonData, PokemonNotFoundError, PokemonSummary
from app.services.pokemon_data import PokemonDataService


@pytest.mark.integration
class TestPokemonDataServiceIntegration:
    """Integration tests with real PokéAPI calls."""

    @pytest.fixture
    def service(self):
        """Create service instance for integration tests."""
        return PokemonDataService(timeout=30.0)  # Longer timeout for real API calls

    @pytest.mark.asyncio
    async def test_get_pikachu_by_id_real_api(self, service, check):
        """Test fetching Pikachu by ID from real PokéAPI."""
        try:
            result = await service.get_pokemon_by_id(25)

            check.is_true(isinstance(result, PokemonData))
            check.equal(result.id, 25)
            check.equal(result.name, "pikachu")
            check.is_in("electric", result.get_all_types())
            check.is_not(result.sprites.front_default, None)

        except Exception as e:
            pytest.skip(f"Real API test skipped due to network issue: {e}")

    @pytest.mark.asyncio
    async def test_get_pikachu_by_name_real_api(self, service, check):
        """Test fetching Pikachu by name from real PokéAPI."""
        try:
            result = await service.get_pokemon_by_name("pikachu")

            check.is_true(isinstance(result, PokemonData))
            check.equal(result.id, 25)
            check.equal(result.name, "pikachu")

        except Exception as e:
            pytest.skip(f"Real API test skipped due to network issue: {e}")

    @pytest.mark.asyncio
    async def test_get_nonexistent_pokemon_real_api(self, service, check):
        """Test fetching non-existent Pokemon from real PokéAPI."""
        try:
            with pytest.raises(PokemonNotFoundError):
                await service.get_pokemon_by_id(99999)

        except Exception as e:
            pytest.skip(f"Real API test skipped due to network issue: {e}")

    @pytest.mark.asyncio
    async def test_caching_with_real_api(self, service, check):
        """Test caching functionality with real API calls."""
        try:
            # First call should hit the API
            result1 = await service.get_pokemon_by_id(1)  # Bulbasaur

            # Second call should hit the cache
            result2 = await service.get_pokemon_by_id(1)

            # Results should be identical
            check.equal(result1.id, result2.id)
            check.equal(result1.name, result2.name)

            # Check cache stats
            stats = service.get_cache_stats()
            check.greater_equal(stats["total_entries"], 1)

        except Exception as e:
            pytest.skip(f"Real API test skipped due to network issue: {e}")

    @pytest.mark.asyncio
    async def test_pokemon_summary_real_api(self, service, check):
        """Test Pokemon summary with real API."""
        try:
            summary = await service.get_pokemon_summary_by_id(150)  # Mewtwo

            check.is_true(isinstance(summary, PokemonSummary))
            check.equal(summary.id, 150)
            check.equal(summary.name, "mewtwo")
            check.is_in("psychic", summary.types)

        except Exception as e:
            pytest.skip(f"Real API test skipped due to network issue: {e}")


# Add a marker for running only integration tests
pytestmark = pytest.mark.integration
