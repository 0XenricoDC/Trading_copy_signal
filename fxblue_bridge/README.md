# FX Blue Bridge for TradeCopy

This directory contains MetaTrader 5 Expert Advisors (EAs) for integrating TradeCopy with FX Blue trade copying service.

## Overview

- **TradeCopyReceiver.mq5**: Receives trades from FX Blue and forwards them to TradeCopy backend
- **TradeCopySender.mq5**: Monitors TradeCopy trades and copies them to FX Blue for distribution

## Installation

### 1. Copy EA Files

Copy the `.mq5` files to your MetaTrader 5 installation:

```
%APPDATA%\MetaQuotes\Terminal\<TERMINAL_ID>\MQL5\Experts\TradeCopy\
```

Or use the MetaEditor to open and compile the files.

### 2. Compile the EAs

1. Open MetaEditor (F4 in MT5)
2. Open each `.mq5` file
3. Click Compile (F7)
4. Check for errors in the output window

### 3. Configure WebRequest (For Receiver EA)

The TradeCopyReceiver EA needs permission to make HTTP requests:

1. In MetaTrader 5, go to **Tools → Options → Expert Advisors**
2. Check "Allow WebRequest for listed URL"
3. Add your TradeCopy API URL (e.g., `http://localhost:8000`)
4. Click OK

### 4. Enable Algo Trading

1. In MT5, click **Tools → Options → Expert Advisors**
2. Check "Allow automated trading"
3. Enable "AutoTrading" button on the toolbar

## Usage

### TradeCopyReceiver

This EA monitors for new positions opened by FX Blue (identified by magic number) and sends them to TradeCopy backend.

**Input Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| InpApiUrl | http://localhost:8000 | TradeCopy API URL |
| InpApiKey | (empty) | API authentication key |
| InpTenantId | (required) | Your TradeCopy tenant ID |
| InpMagicNumber | 888888 | Magic number for FX Blue trades |
| InpDebugMode | false | Enable debug logging |

**Setup:**

1. Attach the EA to any chart (e.g., EURUSD M1)
2. Configure the input parameters
3. Ensure FX Blue receiver is running on the same MT5 terminal
4. The EA will automatically detect and forward new FX Blue trades

### TradeCopySender

This EA monitors TradeCopy trades and copies them to FX Blue for distribution to your subscribers.

**Input Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| InpTradeCopyMagic | 123456789 | TradeCopy magic number |
| InpFxBlueMagic | 999999 | FX Blue sender magic number |
| InpCopyToFxBlue | true | Enable FX Blue copying |
| InpLotMultiplier | 1.0 | Lot size multiplier |
| InpCopySL | true | Copy stop loss |
| InpCopyTP | true | Copy take profit |
| InpMaxSlippage | 30 | Maximum slippage in points |
| InpDebugMode | false | Enable debug logging |

**Setup:**

1. Ensure FX Blue sender EA is running on the same MT5 terminal
2. Attach TradeCopySender to any chart
3. Configure the magic numbers to match your setup
4. The EA will copy TradeCopy trades to FX Blue

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MetaTrader 5 Terminal                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐          ┌─────────────────┐          │
│  │  FX Blue        │   copy   │  TradeCopy      │          │
│  │  Receiver EA    │ ───────► │  Receiver EA    │          │
│  │  (magic 888888) │          │                 │          │
│  └─────────────────┘          └────────┬────────┘          │
│                                        │                    │
│                                        │ HTTP POST          │
│                                        ▼                    │
│                               ┌─────────────────┐          │
│                               │  TradeCopy API  │          │
│                               │  (Backend)      │          │
│                               └─────────────────┘          │
│                                                             │
│  ┌─────────────────┐          ┌─────────────────┐          │
│  │  TradeCopy      │   copy   │  FX Blue        │          │
│  │  Worker         │ ───────► │  Sender EA      │          │
│  │  (magic 123456) │          │  (magic 999999) │          │
│  └─────────────────┘          └─────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## FX Blue Setup

### As Signal Receiver (from FX Blue provider)

1. Set up FX Blue Internet Trade Mirror as receiver
2. Configure receiver magic number (e.g., 888888)
3. Run TradeCopyReceiver EA with matching magic number
4. Trades will be forwarded to TradeCopy backend

### As Signal Provider (to FX Blue subscribers)

1. Set up FX Blue Internet Trade Mirror as sender
2. Configure sender to copy trades with specific magic number (e.g., 999999)
3. Run TradeCopySender EA to copy TradeCopy trades to FX Blue
4. Your FX Blue subscribers will receive the signals

## Troubleshooting

### WebRequest Error

If you see "WebRequest failed" errors:

1. Check that the API URL is in the allowed list
2. Verify the API is running and accessible
3. Check firewall settings

### Trades Not Detected

1. Verify magic numbers match
2. Check EA is running (green smiley icon)
3. Enable debug mode to see logs
4. Check Experts tab in MT5 for errors

### Connection Issues

1. Ensure MT5 has internet access
2. Check if API server is reachable
3. Verify correct API URL format

## Global Variables

The EAs use MT5 global variables to track processed trades:

- `TC_PROCESSED_<ticket>`: Marks trades sent to API
- `TC_SENT_<ticket>`: Marks trades sent to FX Blue
- `TC_MAP_<ticket>`: Maps TradeCopy tickets to FX Blue tickets
- `TC_CLOSE_<ticket>`: Tracks closed position synchronization

These are automatically managed and cleaned up by the EAs.

## Support

For issues or questions, check the main TradeCopy documentation or open an issue in the repository.
