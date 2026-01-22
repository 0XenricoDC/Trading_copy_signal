"""Standard signal patterns."""

import re


class StandardPatterns:
    """Standard signal patterns that work for most providers."""

    @staticmethod
    def get_patterns() -> dict:
        """Get standard regex patterns."""
        return {
            # Direction + Symbol patterns
            "direction_symbol": [
                # BUY EURUSD @ 1.0850
                re.compile(r'\b(BUY|SELL)\s+([A-Z]{3,10})\s*[@at]?\s*([\d.]+)?', re.IGNORECASE),
                # EURUSD BUY NOW
                re.compile(r'\b([A-Z]{3,10})\s+(BUY|SELL)\s*(?:NOW|@|at)?\s*([\d.]+)?', re.IGNORECASE),
                # LONG GOLD or SHORT GOLD
                re.compile(r'\b(LONG|SHORT)\s+([A-Z]{3,10})', re.IGNORECASE),
            ],

            # Entry price patterns
            "entry": [
                re.compile(r'(?:Entry|Open|Price|EP)\s*[:=@]?\s*([\d.]+)', re.IGNORECASE),
                re.compile(r'(?:Buy|Sell)\s*(?:@|at)\s*([\d.]+)', re.IGNORECASE),
                re.compile(r'CMP\s*[:=]?\s*([\d.]+)', re.IGNORECASE),
            ],

            # Entry zone patterns
            "entry_zone": [
                re.compile(r'(?:Entry|Zone)\s*[:=]?\s*([\d.]+)\s*[-–]\s*([\d.]+)', re.IGNORECASE),
                re.compile(r'([\d.]+)\s*[-–]\s*([\d.]+)\s*(?:entry|zone)', re.IGNORECASE),
            ],

            # Stop loss patterns
            "stop_loss": [
                re.compile(r'(?:SL|Stop\s*Loss|S\.L\.|S/L)\s*[:=@]?\s*([\d.]+)', re.IGNORECASE),
                re.compile(r'([\d.]+)\s*(?:SL|Stop)', re.IGNORECASE),
            ],

            # Take profit patterns
            "take_profit": [
                re.compile(r'(?:TP|Take\s*Profit|T\.P\.|T/P)\s*[:=@]?\s*([\d.]+)', re.IGNORECASE),
                re.compile(r'TP\s*(\d)\s*[:=@]?\s*([\d.]+)', re.IGNORECASE),
            ],
        }
