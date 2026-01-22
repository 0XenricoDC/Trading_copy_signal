"""MT5 trade executor."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from workers.mt5.connector import MT5_AVAILABLE

if MT5_AVAILABLE:
    import MetaTrader5 as mt5

logger = logging.getLogger(__name__)


@dataclass
class TradeResult:
    """Result of a trade operation."""

    success: bool
    ticket: int | None = None
    order_id: int | None = None
    volume: float | None = None
    price: float | None = None
    error_code: int | None = None
    error_message: str | None = None


class MT5Executor:
    """Executes trades on MetaTrader 5."""

    # Magic number to identify our trades
    MAGIC_NUMBER = 123456789

    def __init__(self, connector):
        """Initialize executor with an MT5 connector."""
        self.connector = connector

    def open_position(
        self,
        symbol: str,
        direction: str,
        volume: float,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        price: float | None = None,
        deviation: int = 20,
        comment: str = "TradeCopy",
    ) -> TradeResult:
        """Open a new position.

        Args:
            symbol: Trading symbol (e.g., EURUSD)
            direction: "buy" or "sell"
            volume: Lot size
            stop_loss: Stop loss price
            take_profit: Take profit price
            price: Entry price (None for market order)
            deviation: Max price deviation in points
            comment: Trade comment

        Returns:
            TradeResult with operation result
        """
        if not MT5_AVAILABLE:
            return TradeResult(
                success=False,
                error_code=-1,
                error_message="MT5 not available",
            )

        if not self.connector.is_connected:
            return TradeResult(
                success=False,
                error_code=-1,
                error_message="Not connected to MT5",
            )

        try:
            # Get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                # Try to select the symbol
                if not mt5.symbol_select(symbol, True):
                    return TradeResult(
                        success=False,
                        error_code=-1,
                        error_message=f"Symbol {symbol} not found",
                    )
                symbol_info = mt5.symbol_info(symbol)

            if not symbol_info.visible:
                mt5.symbol_select(symbol, True)

            # Determine order type and price
            if direction.lower() == "buy":
                order_type = mt5.ORDER_TYPE_BUY
                fill_price = symbol_info.ask if price is None else price
            else:
                order_type = mt5.ORDER_TYPE_SELL
                fill_price = symbol_info.bid if price is None else price

            # Validate volume
            volume = self._normalize_volume(volume, symbol_info)

            # Build request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": fill_price,
                "deviation": deviation,
                "magic": self.MAGIC_NUMBER,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            if stop_loss:
                request["sl"] = stop_loss
            if take_profit:
                request["tp"] = take_profit

            # Send order
            result = mt5.order_send(request)

            if result is None:
                error = mt5.last_error()
                return TradeResult(
                    success=False,
                    error_code=error[0] if error else -1,
                    error_message=str(error) if error else "Unknown error",
                )

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return TradeResult(
                    success=False,
                    error_code=result.retcode,
                    error_message=result.comment,
                )

            logger.info(f"Opened position: {direction} {volume} {symbol} @ {result.price}, ticket: {result.order}")

            return TradeResult(
                success=True,
                ticket=result.order,
                order_id=result.deal,
                volume=result.volume,
                price=result.price,
            )

        except Exception as e:
            logger.error(f"Error opening position: {e}", exc_info=True)
            return TradeResult(
                success=False,
                error_code=-1,
                error_message=str(e),
            )

    def close_position(
        self,
        ticket: int,
        volume: float | None = None,
        deviation: int = 20,
        comment: str = "TradeCopy Close",
    ) -> TradeResult:
        """Close an open position.

        Args:
            ticket: Position ticket to close
            volume: Volume to close (None for full position)
            deviation: Max price deviation in points
            comment: Trade comment

        Returns:
            TradeResult with operation result
        """
        if not MT5_AVAILABLE:
            return TradeResult(
                success=False,
                error_code=-1,
                error_message="MT5 not available",
            )

        if not self.connector.is_connected:
            return TradeResult(
                success=False,
                error_code=-1,
                error_message="Not connected to MT5",
            )

        try:
            # Get position info
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return TradeResult(
                    success=False,
                    error_code=-1,
                    error_message=f"Position {ticket} not found",
                )

            position = position[0]
            symbol = position.symbol

            # Get symbol info for current price
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return TradeResult(
                    success=False,
                    error_code=-1,
                    error_message=f"Symbol {symbol} not found",
                )

            # Determine close type and price
            if position.type == mt5.ORDER_TYPE_BUY:
                close_type = mt5.ORDER_TYPE_SELL
                close_price = symbol_info.bid
            else:
                close_type = mt5.ORDER_TYPE_BUY
                close_price = symbol_info.ask

            close_volume = volume if volume else position.volume

            # Build request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": close_volume,
                "type": close_type,
                "position": ticket,
                "price": close_price,
                "deviation": deviation,
                "magic": self.MAGIC_NUMBER,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Send order
            result = mt5.order_send(request)

            if result is None:
                error = mt5.last_error()
                return TradeResult(
                    success=False,
                    error_code=error[0] if error else -1,
                    error_message=str(error) if error else "Unknown error",
                )

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return TradeResult(
                    success=False,
                    error_code=result.retcode,
                    error_message=result.comment,
                )

            logger.info(f"Closed position {ticket}: {close_volume} @ {result.price}")

            return TradeResult(
                success=True,
                ticket=result.order,
                order_id=result.deal,
                volume=result.volume,
                price=result.price,
            )

        except Exception as e:
            logger.error(f"Error closing position: {e}", exc_info=True)
            return TradeResult(
                success=False,
                error_code=-1,
                error_message=str(e),
            )

    def modify_position(
        self,
        ticket: int,
        stop_loss: float | None = None,
        take_profit: float | None = None,
    ) -> TradeResult:
        """Modify an open position's SL/TP.

        Args:
            ticket: Position ticket to modify
            stop_loss: New stop loss price (None to keep current)
            take_profit: New take profit price (None to keep current)

        Returns:
            TradeResult with operation result
        """
        if not MT5_AVAILABLE:
            return TradeResult(
                success=False,
                error_code=-1,
                error_message="MT5 not available",
            )

        if not self.connector.is_connected:
            return TradeResult(
                success=False,
                error_code=-1,
                error_message="Not connected to MT5",
            )

        try:
            # Get position info
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return TradeResult(
                    success=False,
                    error_code=-1,
                    error_message=f"Position {ticket} not found",
                )

            position = position[0]

            # Build request
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": position.symbol,
                "position": ticket,
                "sl": stop_loss if stop_loss is not None else position.sl,
                "tp": take_profit if take_profit is not None else position.tp,
            }

            # Send order
            result = mt5.order_send(request)

            if result is None:
                error = mt5.last_error()
                return TradeResult(
                    success=False,
                    error_code=error[0] if error else -1,
                    error_message=str(error) if error else "Unknown error",
                )

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return TradeResult(
                    success=False,
                    error_code=result.retcode,
                    error_message=result.comment,
                )

            logger.info(f"Modified position {ticket}: SL={stop_loss}, TP={take_profit}")

            return TradeResult(
                success=True,
                ticket=ticket,
            )

        except Exception as e:
            logger.error(f"Error modifying position: {e}", exc_info=True)
            return TradeResult(
                success=False,
                error_code=-1,
                error_message=str(e),
            )

    def _normalize_volume(self, volume: float, symbol_info) -> float:
        """Normalize volume to symbol's specifications."""
        volume_min = symbol_info.volume_min
        volume_max = symbol_info.volume_max
        volume_step = symbol_info.volume_step

        # Clamp to min/max
        volume = max(volume_min, min(volume, volume_max))

        # Round to step
        steps = round((volume - volume_min) / volume_step)
        volume = volume_min + steps * volume_step

        return round(volume, 2)
