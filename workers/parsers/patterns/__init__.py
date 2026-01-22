"""Signal parsing patterns for different signal providers."""

from workers.parsers.patterns.standard import StandardPatterns
from workers.parsers.patterns.gold_signals import GoldSignalsPatterns

__all__ = ["StandardPatterns", "GoldSignalsPatterns"]
