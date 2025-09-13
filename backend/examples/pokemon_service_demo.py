#!/usr/bin/env python3
"""
Demo script showing how to use the Pokemon data service.
Run this script to test the service with real PokéAPI calls.
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.pokemon_data import PokemonDataService
from app.models.pokemon import PokemonNotFoundError, PokemonAPIError


async def demo_pokemon_service():
    """Demonstrate Pokemon data service functionality."""
    print("🔥 Pokemon Data Service Demo")
    print("=" * 40)
    
    # Create service instance
    service = PokemonDataService()
    
    try:
        # Test 1: Get Pokemon by ID
        print("\n1. Fetching Pikachu by ID (25)...")
        pikachu = await service.get_pokemon_by_id(25)
        print(f"   ✅ Found: {pikachu.name.title()} (ID: {pikachu.id})")
        print(f"   📊 Types: {', '.join(pikachu.get_all_types())}")
        print(f"   ⚡ Abilities: {', '.join(pikachu.get_abilities_list())}")
        print(f"   📏 Height: {pikachu.height/10}m, Weight: {pikachu.weight/10}kg")
        
        # Test 2: Get Pokemon by name
        print("\n2. Fetching Charizard by name...")
        charizard = await service.get_pokemon_by_name("charizard")
        print(f"   ✅ Found: {charizard.name.title()} (ID: {charizard.id})")
        print(f"   📊 Types: {', '.join(charizard.get_all_types())}")
        
        # Test 3: Get Pokemon summary
        print("\n3. Getting Mewtwo summary...")
        mewtwo_summary = await service.get_pokemon_summary_by_id(150)
        print(f"   ✅ Summary: {mewtwo_summary.name.title()}")
        print(f"   🖼️  Sprite: {mewtwo_summary.sprite_url}")
        
        # Test 4: Cache functionality
        print("\n4. Testing cache (fetching Pikachu again)...")
        pikachu_cached = await service.get_pokemon_by_id(25)
        print(f"   ✅ Cached result: {pikachu_cached.name.title()}")
        
        # Show cache stats
        stats = service.get_cache_stats()
        print(f"   📈 Cache stats: {stats['total_entries']} entries")
        
        # Test 5: Error handling
        print("\n5. Testing error handling (non-existent Pokemon)...")
        try:
            await service.get_pokemon_by_id(99999)
        except PokemonNotFoundError:
            print("   ✅ Correctly handled non-existent Pokemon")
        
        print("\n🎉 All tests completed successfully!")
        
    except PokemonAPIError as e:
        print(f"   ❌ API Error: {e}")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
    
    finally:
        # Show final cache stats
        final_stats = service.get_cache_stats()
        print(f"\n📊 Final cache stats: {final_stats}")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_pokemon_service())