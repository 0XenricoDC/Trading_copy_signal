"""Regex-based signal parser for trading signals."""

import re
import logging
from typing import Any

from backend.app.models.signal import SignalDirection

logger = logging.getLogger(__name__)


class SignalParser:
    """Parser for trading signals using regex patterns."""

    # Common forex/crypto symbols
    KNOWN_SYMBOLS = {
        # Forex majors
        "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
        # Forex crosses
        "EURJPY", "GBPJPY", "EURGBP", "AUDNZD", "AUDJPY", "CADJPY", "CHFJPY",
        "EURAUD", "EURCAD", "EURCHF", "EURNZD", "GBPAUD", "GBPCAD", "GBPCHF",
        "GBPNZD", "NZDCAD", "NZDCHF", "NZDJPY", "AUDCAD", "AUDCHF",
        # Metals
        "XAUUSD", "XAGUSD", "GOLD", "SILVER",
        # Indices
        "US30", "US100", "US500", "DJ30", "NAS100", "SPX500",
        "GER40", "DAX", "UK100", "FTSE100", "JPN225",
        # Crypto
        "BTCUSD", "ETHUSD", "XRPUSD", "LTCUSD", "BCHUSD",
        # Oil
        "USOIL", "UKOIL", "WTI", "BRENT",
    }

    # Symbol aliases
    SYMBOL_ALIASES = {
        "GOLD": "XAUUSD",
        "SILVER": "XAGUSD",
        "DJ30": "US30",
        "NAS100": "US100",
        "SPX500": "US500",
        "DAX": "GER40",
        "FTSE100": "UK100",
        "WTI": "USOIL",
        "BRENT": "UKOIL",
    }

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for parsing."""
        # Direction patterns
        self.direction_patterns = [
            # Standard: BUY EURUSD or SELL EURUSD
            re.compile(r'\b(BUY|SELL|LONG|SHORT)\s+([A-Z]{3,10})\b', re.IGNORECASE),
            # Symbol first: EURUSD BUY or GOLD SELL
            re.compile(r'\b([A-Z]{3,10})\s+(BUY|SELL|LONG|SHORT)\b', re.IGNORECASE),
            # With @ symbol: BUY EURUSD @ 1.0850
            re.compile(r'\b(BUY|SELL|LONG|SHORT)\s+([A-Z]{3,10})\s*@?\s*([\d.]+)?', re.IGNORECASE),
        ]

        # Entry price patterns
        self.entry_patterns = [
            # Entry: 1.0850 or Entry @ 1.0850
            re.compile(r'(?:Entry|Open|Price|@)\s*[:@]?\s*([\d.]+)', re.IGNORECASE),
            # Entry zone: 1.0840 - 1.0860
            re.compile(r'(?:Entry|Zone|Range)\s*[:@]?\s*([\d.]+)\s*[-–to]+\s*([\d.]+)', re.IGNORECASE),
            # CMP/Current Market Price
            re.compile(r'(?:CMP|Current\s*(?:Market\s*)?Price)\s*[:@]?\s*([\d.]+)', re.IGNORECASE),
        ]

        # Stop loss patterns
        self.sl_patterns = [
            re.compile(r'(?:SL|Stop\s*Loss|S/L|STOPLOSS)\s*[:@]?\s*([\d.]+)', re.IGNORECASE),
            re.compile(r'([\d.]+)\s*(?:SL|Stop\s*Loss)', re.IGNORECASE),
        ]

        # Take profit patterns (multiple TPs)
        self.tp_patterns = [
            # TP1: 1.0900, TP2: 1.0950, etc.
            re.compile(r'TP\s*(\d)\s*[:@]?\s*([\d.]+)', re.IGNORECASE),
            # Take Profit 1: 1.0900
            re.compile(r'Take\s*Profit\s*(\d)\s*[:@]?\s*([\d.]+)', re.IGNORECASE),
            # T/P 1: 1.0900
            re.compile(r'T/P\s*(\d)\s*[:@]?\s*([\d.]+)', re.IGNORECASE),
            # Single TP: 1.0900
            re.compile(r'(?:TP|Take\s*Profit|T/P)\s*[:@]?\s*([\d.]+)', re.IGNORECASE),
        ]

        # Partial close patterns
        self.partial_patterns = [
            re.compile(r'(?:Close|Take)\s*(\d+)%?\s*(?:at|@)?\s*([\d.]+)?', re.IGNORECASE),
            re.compile(r'(?:TP|Hit)\s*(\d+)\s*[:@]?\s*([\d.]+)?', re.IGNORECASE),
        ]

    def parse(self, text: str) -> dict | None:
        """Parse a signal from text.

        Returns:
            dict with parsed signal data or None if parsing failed
        """
        try:
            # Clean text
            text = self._clean_text(text)

            # Extract direction and symbol
            direction, symbol = self._extract_direction_symbol(text)
            if not direction or not symbol:
                logger.debug(f"Could not extract direction/symbol from: {text[:100]}")
                return None

            # Normalize symbol
            symbol = self._normalize_symbol(symbol)

            # Extract stop loss
            stop_loss = self._extract_stop_loss(text)
            if not stop_loss:
                logger.debug(f"Could not extract stop loss from: {text[:100]}")
                return None

            # Extract entry price(s)
            entry_price, entry_low, entry_high = self._extract_entry_price(text)

            # Extract take profits
            take_profits = self._extract_take_profits(text)

            # Validate price levels
            if not self._validate_prices(direction, entry_price or entry_low, stop_loss, take_profits):
                logger.debug(f"Price validation failed for: {text[:100]}")
                return None

            # Calculate confidence score
            confidence = self._calculate_confidence(
                direction, symbol, entry_price, stop_loss, take_profits
            )

            result = {
                "symbol": symbol,
                "direction": SignalDirection.BUY if direction.upper() in ("BUY", "LONG") else SignalDirection.SELL,
                "entry_price": entry_price,
                "entry_price_low": entry_low,
                "entry_price_high": entry_high,
                "stop_loss": stop_loss,
                "take_profits": take_profits,
                "confidence": confidence,
                "notes": self._generate_notes(text),
            }

            logger.info(f"Parsed signal: {direction} {symbol} @ {entry_price}, SL: {stop_loss}, TPs: {take_profits}")
            return result

        except Exception as e:
            logger.error(f"Error parsing signal: {e}", exc_info=True)
            return None

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove emojis and special characters (keep basic punctuation)
        text = re.sub(r'[^\w\s@:.\-/]+', ' ', text)
        # Normalize whitespace
        text = ' '.join(text.split())
        return text

    def _extract_direction_symbol(self, text: str) -> tuple[str | None, str | None]:
        """Extract direction (buy/sell) and symbol from text."""
        for pattern in self.direction_patterns:
            match = pattern.search(text)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    # Check which group is direction
                    g1, g2 = groups[0].upper(), groups[1].upper()
                    if g1 in ("BUY", "SELL", "LONG", "SHORT"):
                        return g1, g2
                    elif g2 in ("BUY", "SELL", "LONG", "SHORT"):
                        return g2, g1

        # Try to find symbol and direction separately
        direction = None
        symbol = None

        # Find direction
        dir_match = re.search(r'\b(BUY|SELL|LONG|SHORT)\b', text, re.IGNORECASE)
        if dir_match:
            direction = dir_match.group(1).upper()

        # Find symbol
        for known_symbol in self.KNOWN_SYMBOLS:
            if re.search(rf'\b{known_symbol}\b', text, re.IGNORECASE):
                symbol = known_symbol
                break

        return direction, symbol

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to standard format."""
        symbol = symbol.upper()
        return self.SYMBOL_ALIASES.get(symbol, symbol)

    def _extract_entry_price(self, text: str) -> tuple[float | None, float | None, float | None]:
        """Extract entry price or entry zone from text."""
        entry_price = None
        entry_low = None
        entry_high = None

        # Check for entry zone first
        for pattern in self.entry_patterns:
            match = pattern.search(text)
            if match:
                groups = match.groups()
                if len(groups) == 2 and groups[1]:
                    # Entry zone
                    entry_low = float(groups[0])
                    entry_high = float(groups[1])
                    entry_price = (entry_low + entry_high) / 2
                elif len(groups) >= 1:
                    # Single entry price
                    entry_price = float(groups[0])
                break

        return entry_price, entry_low, entry_high

    def _extract_stop_loss(self, text: str) -> float | None:
        """Extract stop loss from text."""
        for pattern in self.sl_patterns:
            match = pattern.search(text)
            if match:
                for group in match.groups():
                    if group:
                        try:
                            return float(group)
                        except ValueError:
                            continue
        return None

    def _extract_take_profits(self, text: str) -> list[float]:
        """Extract take profit levels from text."""
        take_profits = {}

        for pattern in self.tp_patterns:
            for match in pattern.finditer(text):
                groups = match.groups()
                if len(groups) == 2:
                    # TP with number (TP1, TP2, etc.)
                    tp_num = int(groups[0])
                    tp_price = float(groups[1])
                    take_profits[tp_num] = tp_price
                elif len(groups) == 1:
                    # Single TP without number
                    if 1 not in take_profits:
                        take_profits[1] = float(groups[0])

        # Sort by TP number and return as list
        if take_profits:
            return [take_profits[k] for k in sorted(take_profits.keys())]

        return []

    def _validate_prices(
        self,
        direction: str,
        entry_price: float | None,
        stop_loss: float,
        take_profits: list[float],
    ) -> bool:
        """Validate that price levels make sense."""
        if not stop_loss:
            return False

        if entry_price:
            if direction.upper() in ("BUY", "LONG"):
                # For buy: SL should be below entry, TPs above
                if stop_loss >= entry_price:
                    return False
                for tp in take_profits:
                    if tp <= entry_price:
                        return False
            else:
                # For sell: SL should be above entry, TPs below
                if stop_loss <= entry_price:
                    return False
                for tp in take_profits:
                    if tp >= entry_price:
                        return False

        return True

    def _calculate_confidence(
        self,
        direction: str | None,
        symbol: str | None,
        entry_price: float | None,
        stop_loss: float | None,
        take_profits: list[float],
    ) -> float:
        """Calculate confidence score for the parsed signal."""
        score = 0.0
        max_score = 5.0

        if direction:
            score += 1.0
        if symbol and symbol in self.KNOWN_SYMBOLS:
            score += 1.0
        elif symbol:
            score += 0.5
        if stop_loss:
            score += 1.0
        if entry_price:
            score += 1.0
        if take_profits:
            score += min(len(take_profits), 3) / 3.0  # Up to 1.0 for 3+ TPs

        return round(score / max_score, 2)

    def _generate_notes(self, text: str) -> str | None:
        """Generate notes about the parsing."""
        notes = []

        # Check for market order indicators
        if re.search(r'\b(market|now|immediately|cmp)\b', text, re.IGNORECASE):
            notes.append("Market order indicated")

        # Check for pending order indicators
        if re.search(r'\b(pending|limit|stop)\s*(order)?\b', text, re.IGNORECASE):
            notes.append("Pending order indicated")

        # Check for risk warnings
        if re.search(r'\b(risky|volatile|caution|careful)\b', text, re.IGNORECASE):
            notes.append("Risk warning in signal")

        return "; ".join(notes) if notes else None
