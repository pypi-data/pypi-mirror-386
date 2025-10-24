from enum import Enum


class DI(str, Enum):
    """Dependency injection provider names, for easier refactoring"""

    settings = "settings"
    brain = "brain"
    polarity_reasoner = "polarity_reasoner"
    causality_sequencer = "causality_sequencer"
    polarity_extractor = "polarity_extractor"
