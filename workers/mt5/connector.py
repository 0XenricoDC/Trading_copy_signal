"""MT5 connection manager."""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# MT5 is only available on Windows
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None
    logger.warning("MetaTrader5 package not available. MT5 functions will be disabled.")


class MT5Connector:
    """Manages connection to MetaTrader 5 terminal."""

    def __init__(
        self,
        login: int,
        password: str,
        server: str,
        mt5_path: str | None = None,
        timeout: int = 30000,
    ):
        self.login = login
        self.password = password
        self.server = server
        self.mt5_path = mt5_path
        self.timeout = timeout
        self._connected = False

    @property
    def is_available(self) -> bool:
        """Check if MT5 is available."""
        return MT5_AVAILABLE

    @property
    def is_connected(self) -> bool:
        """Check if connected to MT5."""
        return self._connected

    def connect(self) -> bool:
        """Connect to MT5 terminal."""
        if not MT5_AVAILABLE:
            logger.error("MetaTrader5 package is not available")
            return False

        try:
            # Initialize MT5
            init_params = {
                "login": self.login,
                "password": self.password,
                "server": self.server,
                "timeout": self.timeout,
            }

            if self.mt5_path:
                init_params["path"] = self.mt5_path

            if not mt5.initialize(**init_params):
                error = mt5.last_error()
                logger.error(f"MT5 initialization failed: {error}")
                return False

            # Verify login
            account_info = mt5.account_info()
            if account_info is None:
                logger.error("Failed to get account info after initialization")
                mt5.shutdown()
                return False

            if account_info.login != self.login:
                logger.error(f"Login mismatch: expected {self.login}, got {account_info.login}")
                mt5.shutdown()
                return False

            self._connected = True
            logger.info(f"Connected to MT5 account {self.login} on {self.server}")
            return True

        except Exception as e:
            logger.error(f"Error connecting to MT5: {e}", exc_info=True)
            return False

    def disconnect(self):
        """Disconnect from MT5 terminal."""
        if MT5_AVAILABLE and self._connected:
            mt5.shutdown()
            self._connected = False
            logger.info(f"Disconnected from MT5 account {self.login}")

    def get_account_info(self) -> dict | None:
        """Get account information."""
        if not self._connected:
            logger.error("Not connected to MT5")
            return None

        try:
            info = mt5.account_info()
            if info is None:
                return None

            return {
                "login": info.login,
                "server": info.server,
                "balance": info.balance,
                "equity": info.equity,
                "margin": info.margin,
                "margin_free": info.margin_free,
                "margin_level": info.margin_level,
                "leverage": info.leverage,
                "currency": info.currency,
                "trade_allowed": info.trade_allowed,
                "trade_expert": info.trade_expert,
            }

        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None

    def get_symbol_info(self, symbol: str) -> dict | None:
        """Get symbol information."""
        if not self._connected:
            return None

        try:
            info = mt5.symbol_info(symbol)
            if info is None:
                # Try selecting the symbol first
                if mt5.symbol_select(symbol, True):
                    info = mt5.symbol_info(symbol)

            if info is None:
                return None

            return {
                "name": info.name,
                "description": info.description,
                "point": info.point,
                "digits": info.digits,
                "volume_min": info.volume_min,
                "volume_max": info.volume_max,
                "volume_step": info.volume_step,
                "bid": info.bid,
                "ask": info.ask,
                "spread": info.spread,
                "trade_mode": info.trade_mode,
            }

        except Exception as e:
            logger.error(f"Error getting symbol info: {e}")
            return None

    def get_positions(self, symbol: str | None = None) -> list[dict]:
        """Get open positions."""
        if not self._connected:
            return []

        try:
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()

            if positions is None:
                return []

            return [
                {
                    "ticket": pos.ticket,
                    "symbol": pos.symbol,
                    "type": "buy" if pos.type == mt5.ORDER_TYPE_BUY else "sell",
                    "volume": pos.volume,
                    "open_price": pos.price_open,
                    "current_price": pos.price_current,
                    "stop_loss": pos.sl,
                    "take_profit": pos.tp,
                    "profit": pos.profit,
                    "swap": pos.swap,
                    "commission": pos.commission,
                    "open_time": datetime.fromtimestamp(pos.time),
                    "magic": pos.magic,
                    "comment": pos.comment,
                }
                for pos in positions
            ]

        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def get_orders(self, symbol: str | None = None) -> list[dict]:
        """Get pending orders."""
        if not self._connected:
            return []

        try:
            if symbol:
                orders = mt5.orders_get(symbol=symbol)
            else:
                orders = mt5.orders_get()

            if orders is None:
                return []

            order_type_map = {
                mt5.ORDER_TYPE_BUY: "buy",
                mt5.ORDER_TYPE_SELL: "sell",
                mt5.ORDER_TYPE_BUY_LIMIT: "buy_limit",
                mt5.ORDER_TYPE_SELL_LIMIT: "sell_limit",
                mt5.ORDER_TYPE_BUY_STOP: "buy_stop",
                mt5.ORDER_TYPE_SELL_STOP: "sell_stop",
            }

            return [
                {
                    "ticket": order.ticket,
                    "symbol": order.symbol,
                    "type": order_type_map.get(order.type, "unknown"),
                    "volume": order.volume_current,
                    "price": order.price_open,
                    "stop_loss": order.sl,
                    "take_profit": order.tp,
                    "time_setup": datetime.fromtimestamp(order.time_setup),
                    "magic": order.magic,
                    "comment": order.comment,
                }
                for order in orders
            ]

        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
