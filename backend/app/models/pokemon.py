"""
Pydantic models for Pokemon data structures matching PokéAPI response format.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class PokemonType(BaseModel):
    """Pokemon type information."""

    slot: int
    type: Dict[str, str]  # {"name": "electric", "url": "..."}


class PokemonAbility(BaseModel):
    """Pokemon ability information."""

    is_hidden: bool
    slot: int
    ability: Dict[str, str]  # {"name": "static", "url": "..."}


class PokemonStat(BaseModel):
    """Pokemon base stat information."""

    base_stat: int
    effort: int
    stat: Dict[str, str]  # {"name": "hp", "url": "..."}


class PokemonSprites(BaseModel):
    """Pokemon sprite URLs."""

    front_default: Optional[str] = None
    front_shiny: Optional[str] = None
    front_female: Optional[str] = None
    front_shiny_female: Optional[str] = None
    back_default: Optional[str] = None
    back_shiny: Optional[str] = None
    back_female: Optional[str] = None
    back_shiny_female: Optional[str] = None
    other: Optional[Dict[str, Any]] = None
    versions: Optional[Dict[str, Any]] = None


class PokemonSpecies(BaseModel):
    """Pokemon species information."""

    name: str
    url: str


class PokemonData(BaseModel):
    """Complete Pokemon data model matching PokéAPI response."""

    id: int
    name: str
    base_experience: Optional[int] = None
    height: int  # in decimeters
    is_default: bool = True
    order: int
    weight: int  # in hectograms
    abilities: List[PokemonAbility]
    forms: List[Dict[str, str]]
    game_indices: List[Dict[str, Any]]
    held_items: List[Dict[str, Any]]
    location_area_encounters: str
    moves: List[Dict[str, Any]]
    species: PokemonSpecies
    sprites: PokemonSprites
    stats: List[PokemonStat]
    types: List[PokemonType]
    past_types: List[Dict[str, Any]] = []

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Ensure name is not empty."""
        if not v or not v.strip():
            raise ValueError("Pokemon name cannot be empty")
        return v.lower().strip()

    @field_validator("id")
    @classmethod
    def validate_id(cls, v):
        """Ensure ID is positive."""
        if v <= 0:
            raise ValueError("Pokemon ID must be positive")
        return v

    def get_primary_type(self) -> str:
        """Get the primary type of the Pokemon."""
        if not self.types:
            return "unknown"
        return self.types[0].type["name"]

    def get_all_types(self) -> List[str]:
        """Get all types of the Pokemon."""
        return [ptype.type["name"] for ptype in self.types]

    def get_abilities_list(self) -> List[str]:
        """Get list of ability names."""
        return [ability.ability["name"] for ability in self.abilities]

    def get_base_stats_dict(self) -> Dict[str, int]:
        """Get base stats as a dictionary."""
        return {stat.stat["name"]: stat.base_stat for stat in self.stats}


class PokemonSummary(BaseModel):
    """Simplified Pokemon data for quick responses."""

    id: int
    name: str
    types: List[str]
    sprite_url: Optional[str] = None
    height: int
    weight: int

    @classmethod
    def from_pokemon_data(cls, pokemon_data: PokemonData) -> "PokemonSummary":
        """Create summary from full Pokemon data."""
        return cls(
            id=pokemon_data.id,
            name=pokemon_data.name,
            types=pokemon_data.get_all_types(),
            sprite_url=pokemon_data.sprites.front_default,
            height=pokemon_data.height,
            weight=pokemon_data.weight,
        )


class PokemonNotFoundError(Exception):
    """Raised when a Pokemon is not found."""

    pass


class PokemonAPIError(Exception):
    """Raised when there's an error with the PokéAPI."""

    pass
