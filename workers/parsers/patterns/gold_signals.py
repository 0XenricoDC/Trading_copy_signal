"""Gold/XAUUSD specific signal patterns."""

import re


class GoldSignalsPatterns:
    """Patterns optimized for gold/XAUUSD signals."""

    @staticmethod
    def get_patterns() -> dict:
        """Get gold-specific regex patterns."""
        return {
            # Gold symbol variations
            "symbol_aliases": {
                "GOLD": "XAUUSD",
                "XAU": "XAUUSD",
                "XAUUSD": "XAUUSD",
            },

            # Direction patterns for gold
            "direction": [
                # GOLD BUY NOW
                re.compile(r'(?:GOLD|XAU(?:USD)?)\s*(BUY|SELL)\s*(?:NOW)?', re.IGNORECASE),
                # BUY GOLD
                re.compile(r'(BUY|SELL)\s*(?:GOLD|XAU(?:USD)?)', re.IGNORECASE),
                # Gold Long/Short
                re.compile(r'(?:GOLD|XAU(?:USD)?)\s*(LONG|SHORT)', re.IGNORECASE),
            ],

            # Entry patterns (gold uses 4-5 digit prices like 1950.00)
            "entry": [
                re.compile(r'(?:Entry|Price|@)\s*[:=]?\s*(\d{4}(?:\.\d{1,2})?)', re.IGNORECASE),
                re.compile(r'(\d{4}(?:\.\d{1,2})?)\s*(?:entry|@)', re.IGNORECASE),
            ],

            # Stop loss patterns for gold
            "stop_loss": [
                re.compile(r'(?:SL|Stop)\s*[:=@]?\s*(\d{4}(?:\.\d{1,2})?)', re.IGNORECASE),
            ],

            # Take profit patterns for gold
            "take_profit": [
                re.compile(r'TP\s*(\d)?\s*[:=@]?\s*(\d{4}(?:\.\d{1,2})?)', re.IGNORECASE),
            ],
        }

    @staticmethod
    def is_gold_signal(text: str) -> bool:
        """Check if the signal is for gold/XAUUSD."""
        gold_indicators = ["GOLD", "XAU", "XAUUSD"]
        text_upper = text.upper()
        return any(indicator in text_upper for indicator in gold_indicators)
