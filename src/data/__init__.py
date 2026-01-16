"""
Lelock Data Module
Contains game data definitions: classes, daemons, items, crops.
"""

from data.classes import (
    ClassSystem,
    CharacterClass,
    ClassAbility,
    PrimaryStat,
    create_class_system,
    get_class_by_id,
    get_all_class_ids,
    CLASS_QUICK_REF,
)

__all__ = [
    # Classes
    'ClassSystem',
    'CharacterClass',
    'ClassAbility',
    'PrimaryStat',
    'create_class_system',
    'get_class_by_id',
    'get_all_class_ids',
    'CLASS_QUICK_REF',
]
