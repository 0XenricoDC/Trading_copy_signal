"""MT5 connection pool manager for multi-account support."""

import logging
import threading
import time
from typing import Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from workers.mt5.connector import MT5Connector, MT5_AVAILABLE
from workers.mt5.executor import MT5Executor

logger = logging.getLogger(__name__)


@dataclass
class AccountConnection:
    """Represents a connection to an MT5 account."""

    account_id: str
    login: int
    connector: MT5Connector
    executor: MT5Executor
    last_used: datetime
    in_use: bool = False


class MT5PoolManager:
    """Manages a pool of MT5 connections for multiple accounts.

    Since MT5 Python API only supports one connection per process,
    this manager handles connection switching and caching.
    """

    def __init__(
        self,
        max_connections: int = 5,
        connection_timeout: int = 300,  # 5 minutes
    ):
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self._connections: dict[str, AccountConnection] = {}
        self._lock = threading.Lock()
        self._current_account_id: str | None = None

    def get_connection(
        self,
        account_id: str,
        login: int,
        password: str,
        server: str,
        mt5_path: str | None = None,
    ) -> tuple[MT5Connector, MT5Executor] | None:
        """Get or create a connection for the specified account.

        Note: Due to MT5 limitations, this will disconnect any existing
        connection and connect to the new account.

        Args:
            account_id: Unique account identifier (UUID)
            login: MT5 login
            password: MT5 password (decrypted)
            server: MT5 server
            mt5_path: Path to MT5 terminal

        Returns:
            Tuple of (connector, executor) or None if connection failed
        """
        if not MT5_AVAILABLE:
            logger.error("MT5 not available")
            return None

        with self._lock:
            # Check if we're already connected to this account
            if (
                self._current_account_id == account_id
                and account_id in self._connections
            ):
                conn = self._connections[account_id]
                if conn.connector.is_connected:
                    conn.last_used = datetime.utcnow()
                    logger.debug(f"Reusing existing connection for account {login}")
                    return conn.connector, conn.executor

            # Need to switch accounts - disconnect current
            if self._current_account_id and self._current_account_id in self._connections:
                old_conn = self._connections[self._current_account_id]
                old_conn.connector.disconnect()
                logger.debug(f"Disconnected from account {old_conn.login}")

            # Create or update connection
            connector = MT5Connector(
                login=login,
                password=password,
                server=server,
                mt5_path=mt5_path,
            )

            if not connector.connect():
                logger.error(f"Failed to connect to account {login}")
                return None

            executor = MT5Executor(connector)

            conn = AccountConnection(
                account_id=account_id,
                login=login,
                connector=connector,
                executor=executor,
                last_used=datetime.utcnow(),
                in_use=True,
            )

            self._connections[account_id] = conn
            self._current_account_id = account_id

            # Clean up old connections (keep metadata for reconnection)
            self._cleanup_old_connections()

            logger.info(f"Connected to account {login} on {server}")
            return connector, executor

    def release_connection(self, account_id: str):
        """Mark a connection as no longer in use."""
        with self._lock:
            if account_id in self._connections:
                self._connections[account_id].in_use = False

    def disconnect_all(self):
        """Disconnect all connections."""
        with self._lock:
            for account_id, conn in self._connections.items():
                try:
                    conn.connector.disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting account {conn.login}: {e}")

            self._connections.clear()
            self._current_account_id = None
            logger.info("Disconnected all MT5 connections")

    def _cleanup_old_connections(self):
        """Remove connection entries that haven't been used recently."""
        cutoff = datetime.utcnow() - timedelta(seconds=self.connection_timeout)

        to_remove = []
        for account_id, conn in self._connections.items():
            if conn.last_used < cutoff and not conn.in_use:
                to_remove.append(account_id)

        for account_id in to_remove:
            del self._connections[account_id]
            logger.debug(f"Removed stale connection entry for account {account_id}")

    def execute_for_account(
        self,
        account_id: str,
        login: int,
        password: str,
        server: str,
        mt5_path: str | None,
        operation: Callable[[MT5Connector, MT5Executor], Any],
    ) -> Any:
        """Execute an operation for a specific account.

        This is a helper method that handles connection management
        and ensures proper cleanup.

        Args:
            account_id: Unique account identifier
            login: MT5 login
            password: MT5 password (decrypted)
            server: MT5 server
            mt5_path: Path to MT5 terminal
            operation: Callable that takes (connector, executor) and returns result

        Returns:
            Result of the operation or None if connection failed
        """
        connection = self.get_connection(account_id, login, password, server, mt5_path)

        if connection is None:
            return None

        connector, executor = connection

        try:
            result = operation(connector, executor)
            return result
        finally:
            self.release_connection(account_id)


# Global pool manager instance
_pool_manager: MT5PoolManager | None = None


def get_pool_manager() -> MT5PoolManager:
    """Get the global MT5 pool manager instance."""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = MT5PoolManager()
    return _pool_manager
