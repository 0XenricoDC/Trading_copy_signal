"""Regex-based signal parser for trading signals."""

import re
import logging
from typing import Any
from dataclasses import dataclass

from backend.app.models.signal import SignalDirection

logger = logging.getLogger(__name__)


@dataclass
class ParsedSignalResult:
    """Result of signal parsing."""
    symbol: str | None
    direction: SignalDirection | None
    entry_price: float | None
    entry_price_low: float | None
    entry_price_high: float | None
    stop_loss: float | None
    take_profits: list[float]
    confidence: float
    notes: str | None
    preset_used: str | None = None


class SignalParser:
    """Parser for trading signals using regex patterns with multiple preset support."""

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

    # Price ranges for symbol detection when symbol is not explicitly mentioned
    SYMBOL_PRICE_RANGES = {
        # Indices (high prices)
        "US500": (4000, 6000),      # S&P 500
        "US100": (14000, 22000),    # Nasdaq
        "US30": (30000, 45000),     # Dow Jones
        "GER40": (14000, 20000),    # DAX
        "UK100": (7000, 9000),      # FTSE
        "JPN225": (25000, 42000),   # Nikkei
        # Gold
        "XAUUSD": (1700, 2500),
        # Oil
        "USOIL": (60, 120),
    }

    def __init__(self):
        self._compile_patterns()

    # Words that should NOT be interpreted as symbols
    EXCLUDED_WORDS = {
        "ENTRY", "PRICE", "OPEN", "CLOSE", "ZONE", "RANGE", "TARGET",
        "STOP", "LOSS", "PROFIT", "TAKE", "ORDER", "MARKET", "LIMIT",
        "PENDING", "NOW", "IMMEDIATELY", "CMP", "CURRENT", "USE",
        "RISK", "MANAGEMENT", "MONEY", "SCALPER", "INTRADAY", "SWING",
    }

    def _compile_patterns(self):
        """Compile regex patterns for parsing."""
        # ============================================================
        # DIRECTION PATTERNS (only for explicit direction extraction)
        # ============================================================
        self.direction_only_pattern = re.compile(
            r'\b(BUY|SELL|LONG|SHORT)\b', re.IGNORECASE
        )

        # Direction with explicit label
        self.direction_label_pattern = re.compile(
            r'Direction\s*[:\-]?\s*(BUY|SELL|LONG|SHORT)', re.IGNORECASE
        )

        # Symbol + Direction patterns (symbol must be validated separately)
        self.symbol_direction_patterns = [
            # AUDJPY SELL @ 106.10
            re.compile(r'\b([A-Z]{3,10})\s+(BUY|SELL|LONG|SHORT)\s*@\s*([\d.]+)', re.IGNORECASE),
            # BUY EURUSD @ 1.0850
            re.compile(r'\b(BUY|SELL|LONG|SHORT)\s+([A-Z]{3,10})\s*@\s*([\d.]+)', re.IGNORECASE),
            # EURUSD BUY or GOLD SELL
            re.compile(r'\b([A-Z]{3,10})\s+(BUY|SELL|LONG|SHORT)\b', re.IGNORECASE),
            # BUY EURUSD or SELL EURUSD
            re.compile(r'\b(BUY|SELL|LONG|SHORT)\s+([A-Z]{3,10})\b', re.IGNORECASE),
        ]

        # ============================================================
        # ENTRY PRICE PATTERNS
        # ============================================================
        self.entry_patterns = [
            # Entry Price: 4945.00 or Entry: 1.0850
            re.compile(r'Entry\s*Price\s*[:\-]?\s*([\d.]+)', re.IGNORECASE),
            re.compile(r'Entry\s*[:\-@]?\s*([\d.]+)', re.IGNORECASE),
            # Open/Price: 1.0850
            re.compile(r'(?:Open|Price)\s*[:\-@]?\s*([\d.]+)', re.IGNORECASE),
            # @ 1.0850 (standalone, not part of symbol@price)
            re.compile(r'(?<![A-Z])\s*@\s*([\d.]+)', re.IGNORECASE),
            # Entry zone: 1.0840 - 1.0860
            re.compile(r'(?:Entry|Zone|Range)\s*[:\-@]?\s*([\d.]+)\s*[-–~to]+\s*([\d.]+)', re.IGNORECASE),
            # CMP/Current Market Price
            re.compile(r'(?:CMP|Current\s*(?:Market\s*)?Price)\s*[:\-@]?\s*([\d.]+)', re.IGNORECASE),
        ]

        # ============================================================
        # STOP LOSS PATTERNS
        # ============================================================
        self.sl_patterns = [
            # SL: 1.0800 or Stop Loss: 1.0800 (with flexible spacing)
            re.compile(r'(?:S\s*L|Stop\s*Loss|S/L|STOPLOSS)\s*[:\-@]?\s*([\d.]+)', re.IGNORECASE),
            # 1.0800 SL or 1.0800 Stop Loss
            re.compile(r'([\d.]+)\s*(?:S\s*L|Stop\s*Loss|S/L)', re.IGNORECASE),
        ]

        # ============================================================
        # TAKE PROFIT PATTERNS (enhanced for multiple formats)
        # ============================================================
        self.tp_numbered_patterns = [
            # T P1, TP1, T P 1, TP 1 with flexible spacing: TP1 4942.00 or TP1: 4942.00
            re.compile(r'T\s*P\s*(\d)\s*[:\-@]?\s*([\d.]+)', re.IGNORECASE),
            # Take Profit 1: 1.0900
            re.compile(r'Take\s*Profit\s*(\d)\s*[:\-@]?\s*([\d.]+)', re.IGNORECASE),
            # T/P 1: 1.0900
            re.compile(r'T/P\s*(\d)\s*[:\-@]?\s*([\d.]+)', re.IGNORECASE),
            # Target 1: 1.0900
            re.compile(r'Target\s*(\d)\s*[:\-@]?\s*([\d.]+)', re.IGNORECASE),
        ]

        # Patterns for TP without numbers (multiple TP: lines)
        # Uses word boundary to avoid matching TPs that have numbers after
        self.tp_unnumbered_pattern = re.compile(
            r'(?:TP|Take\s*Profit|T/P|Target)\s*[:\-@]\s*([\d.]+)', re.IGNORECASE
        )

        # ============================================================
        # PARTIAL CLOSE PATTERNS
        # ============================================================
        self.partial_patterns = [
            re.compile(r'(?:Close|Take)\s*(\d+)%?\s*(?:at|@)?\s*([\d.]+)?', re.IGNORECASE),
            re.compile(r'(?:TP|Hit)\s*(\d+)\s*[:\-@]?\s*([\d.]+)?', re.IGNORECASE),
        ]

    def parse(self, text: str) -> dict | None:
        """Parse a signal from text.

        Returns:
            dict with parsed signal data or None if parsing failed
        """
        try:
            # Store original text for reference
            original_text = text

            # Clean text
            cleaned_text = self._clean_text(text)

            # Try different parsing strategies
            result = None

            # Strategy 1: Standard format with symbol
            result = self._parse_standard(cleaned_text, original_text)
            if result and result.get("stop_loss"):
                result["preset_used"] = "standard"
                return result

            # Strategy 2: Direction-first format (Direction: SELL)
            result = self._parse_direction_first(cleaned_text, original_text)
            if result and result.get("stop_loss"):
                result["preset_used"] = "direction_first"
                return result

            # Strategy 3: Compact format (SYMBOL DIRECTION @ PRICE)
            result = self._parse_compact(cleaned_text, original_text)
            if result and result.get("stop_loss"):
                result["preset_used"] = "compact"
                return result

            logger.debug(f"Could not parse signal from: {text[:100]}")
            return None

        except Exception as e:
            logger.error(f"Error parsing signal: {e}", exc_info=True)
            return None

    def _parse_standard(self, text: str, original_text: str) -> dict | None:
        """Parse standard format: BUY EURUSD, Entry: X, SL: X, TP: X."""
        direction, symbol = self._extract_direction_symbol(text)
        if not direction:
            return None

        stop_loss = self._extract_stop_loss(text)
        if not stop_loss:
            return None

        entry_price, entry_low, entry_high = self._extract_entry_price(text)
        take_profits = self._extract_take_profits(text)

        # If no symbol found, try to infer from price
        if not symbol:
            symbol = self._infer_symbol_from_price(entry_price or stop_loss)

        if not symbol:
            return None

        # Normalize symbol
        symbol = self._normalize_symbol(symbol)

        # Validate prices
        if not self._validate_prices(direction, entry_price or entry_low, stop_loss, take_profits):
            logger.debug(f"Price validation failed for standard format")
            return None

        confidence = self._calculate_confidence(direction, symbol, entry_price, stop_loss, take_profits)

        return {
            "symbol": symbol,
            "direction": SignalDirection.BUY if direction.upper() in ("BUY", "LONG") else SignalDirection.SELL,
            "entry_price": entry_price,
            "entry_price_low": entry_low,
            "entry_price_high": entry_high,
            "stop_loss": stop_loss,
            "take_profits": take_profits,
            "confidence": confidence,
            "notes": self._generate_notes(original_text),
        }

    def _parse_direction_first(self, text: str, original_text: str) -> dict | None:
        """Parse format: Direction: SELL, Entry Price: X, SL: X, TP: X."""
        # Look for explicit Direction: pattern
        direction_match = re.search(r'Direction\s*[:\-]?\s*(BUY|SELL|LONG|SHORT)', text, re.IGNORECASE)
        if not direction_match:
            return None

        direction = direction_match.group(1).upper()

        stop_loss = self._extract_stop_loss(text)
        if not stop_loss:
            return None

        entry_price, entry_low, entry_high = self._extract_entry_price(text)
        take_profits = self._extract_take_profits(text)

        # Try to find symbol or infer from price
        symbol = self._find_symbol_in_text(text)
        if not symbol:
            symbol = self._infer_symbol_from_price(entry_price or stop_loss)

        if not symbol:
            # Default to most common index for this price range
            symbol = self._infer_symbol_from_price(entry_price or stop_loss) or "US500"

        symbol = self._normalize_symbol(symbol)

        # Validate prices
        if not self._validate_prices(direction, entry_price or entry_low, stop_loss, take_profits):
            logger.debug(f"Price validation failed for direction-first format")
            return None

        confidence = self._calculate_confidence(direction, symbol, entry_price, stop_loss, take_profits)

        return {
            "symbol": symbol,
            "direction": SignalDirection.BUY if direction in ("BUY", "LONG") else SignalDirection.SELL,
            "entry_price": entry_price,
            "entry_price_low": entry_low,
            "entry_price_high": entry_high,
            "stop_loss": stop_loss,
            "take_profits": take_profits,
            "confidence": confidence,
            "notes": self._generate_notes(original_text),
        }

    def _parse_compact(self, text: str, original_text: str) -> dict | None:
        """Parse compact format: AUDJPY SELL @ 106.10, TP: X, SL: X."""
        # Look for SYMBOL DIRECTION @ PRICE pattern
        compact_match = re.search(
            r'\b([A-Z]{3,10})\s+(BUY|SELL|LONG|SHORT)\s*@\s*([\d.]+)',
            text, re.IGNORECASE
        )
        if not compact_match:
            # Try reversed: DIRECTION SYMBOL @ PRICE
            compact_match = re.search(
                r'\b(BUY|SELL|LONG|SHORT)\s+([A-Z]{3,10})\s*@\s*([\d.]+)',
                text, re.IGNORECASE
            )
            if compact_match:
                direction = compact_match.group(1).upper()
                symbol = compact_match.group(2).upper()
                entry_price = float(compact_match.group(3))
            else:
                return None
        else:
            symbol = compact_match.group(1).upper()
            direction = compact_match.group(2).upper()
            entry_price = float(compact_match.group(3))

        stop_loss = self._extract_stop_loss(text)
        if not stop_loss:
            return None

        take_profits = self._extract_take_profits(text)
        symbol = self._normalize_symbol(symbol)

        # Validate prices
        if not self._validate_prices(direction, entry_price, stop_loss, take_profits):
            logger.debug(f"Price validation failed for compact format")
            return None

        confidence = self._calculate_confidence(direction, symbol, entry_price, stop_loss, take_profits)

        return {
            "symbol": symbol,
            "direction": SignalDirection.BUY if direction in ("BUY", "LONG") else SignalDirection.SELL,
            "entry_price": entry_price,
            "entry_price_low": None,
            "entry_price_high": None,
            "stop_loss": stop_loss,
            "take_profits": take_profits,
            "confidence": confidence,
            "notes": self._generate_notes(original_text),
        }

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text while preserving structure."""
        # Remove emojis and special characters (keep basic punctuation and @)
        text = re.sub(r'[^\w\s@:.\-/▪️•●○◆◇★☆]+', ' ', text)
        # Remove common decorative elements
        text = re.sub(r'[▪️•●○◆◇★☆]', ' ', text)
        # Normalize whitespace but preserve newlines for structure detection
        lines = text.split('\n')
        lines = [' '.join(line.split()) for line in lines]
        return '\n'.join(lines)

    def _extract_direction_symbol(self, text: str) -> tuple[str | None, str | None]:
        """Extract direction (buy/sell) and symbol from text."""
        direction = None
        symbol = None

        # First, try to find symbol + direction together
        for pattern in self.symbol_direction_patterns:
            match = pattern.search(text)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    g1, g2 = groups[0].upper(), groups[1].upper()
                    # Determine which is direction and which is symbol
                    if g1 in ("BUY", "SELL", "LONG", "SHORT"):
                        potential_symbol = g2
                        direction = g1
                    elif g2 in ("BUY", "SELL", "LONG", "SHORT"):
                        potential_symbol = g1
                        direction = g2
                    else:
                        continue

                    # Validate the symbol is known and not an excluded word
                    if self._is_valid_symbol(potential_symbol):
                        symbol = potential_symbol
                        return direction, symbol

        # Fallback: find direction and symbol separately
        dir_match = self.direction_only_pattern.search(text)
        if dir_match:
            direction = dir_match.group(1).upper()

        symbol = self._find_symbol_in_text(text)

        return direction, symbol

    def _is_valid_symbol(self, text: str) -> bool:
        """Check if text is a valid trading symbol."""
        text = text.upper()
        # Not valid if it's an excluded word
        if text in self.EXCLUDED_WORDS:
            return False
        # Valid if it's a known symbol or can be normalized to one
        return text in self.KNOWN_SYMBOLS or self._normalize_symbol(text) in self.KNOWN_SYMBOLS

    def _find_symbol_in_text(self, text: str) -> str | None:
        """Find a known symbol in text."""
        text_upper = text.upper()
        for known_symbol in self.KNOWN_SYMBOLS:
            # Skip if it's an excluded word
            if known_symbol in self.EXCLUDED_WORDS:
                continue
            # Use word boundaries for accurate matching
            if re.search(rf'\b{known_symbol}\b', text_upper):
                return known_symbol
        return None

    def _infer_symbol_from_price(self, price: float | None) -> str | None:
        """Try to infer symbol from price range."""
        if price is None:
            return None

        for symbol, (low, high) in self.SYMBOL_PRICE_RANGES.items():
            if low <= price <= high:
                return symbol
        return None

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to standard format."""
        symbol = symbol.upper()
        return self.SYMBOL_ALIASES.get(symbol, symbol)

    def _extract_entry_price(self, text: str) -> tuple[float | None, float | None, float | None]:
        """Extract entry price or entry zone from text."""
        entry_price = None
        entry_low = None
        entry_high = None

        for pattern in self.entry_patterns:
            match = pattern.search(text)
            if match:
                groups = match.groups()
                if len(groups) == 2 and groups[1]:
                    # Entry zone
                    try:
                        entry_low = float(groups[0])
                        entry_high = float(groups[1])
                        entry_price = (entry_low + entry_high) / 2
                        break
                    except ValueError:
                        continue
                elif len(groups) >= 1 and groups[0]:
                    # Single entry price
                    try:
                        entry_price = float(groups[0])
                        break
                    except ValueError:
                        continue

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
        found_unnumbered = []

        # First try numbered TPs (TP1, TP2, T P1, T P 2, etc.)
        for pattern in self.tp_numbered_patterns:
            for match in pattern.finditer(text):
                groups = match.groups()
                if len(groups) == 2:
                    try:
                        tp_num = int(groups[0])
                        tp_price = float(groups[1])
                        if tp_num not in take_profits:  # Don't overwrite
                            take_profits[tp_num] = tp_price
                    except ValueError:
                        continue

        # Then try unnumbered TPs (multiple "TP: X" lines)
        # Only use this if we didn't find numbered TPs
        if not take_profits:
            for match in self.tp_unnumbered_pattern.finditer(text):
                try:
                    tp_price = float(match.group(1))
                    if tp_price not in found_unnumbered:
                        found_unnumbered.append(tp_price)
                except ValueError:
                    continue

        # Combine results
        if take_profits:
            result = [take_profits[k] for k in sorted(take_profits.keys())]
        elif found_unnumbered:
            # Keep unnumbered TPs in order they were found
            result = found_unnumbered
        else:
            result = []

        return result

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
        if symbol:
            normalized = self._normalize_symbol(symbol)
            if normalized in self.KNOWN_SYMBOLS or symbol in self.KNOWN_SYMBOLS:
                score += 1.0
            else:
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

        # Check for money management hints
        if re.search(r'money\s*management|risk\s*\d+%?', text, re.IGNORECASE):
            notes.append("Money management mentioned")

        # Check for scalper/intraday/swing hints
        if re.search(r'\b(scalp(?:er)?|intraday|swing)\b', text, re.IGNORECASE):
            notes.append("Trading style mentioned")

        return "; ".join(notes) if notes else None


# Singleton instance for convenience
_parser_instance = None


def get_parser() -> SignalParser:
    """Get or create parser instance."""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = SignalParser()
    return _parser_instance


def parse_signal(text: str) -> dict | None:
    """Convenience function to parse a signal."""
    return get_parser().parse(text)
