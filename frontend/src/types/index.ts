// Auth types
export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  name?: string
}

// User/Tenant types
export interface Tenant {
  id: string
  email: string
  name: string | null
  subscription_tier: SubscriptionTier
  is_active: boolean
  created_at: string
  updated_at: string
}

export type SubscriptionTier = 'free' | 'basic' | 'pro' | 'enterprise'

// Telegram Channel types
export interface TelegramChannel {
  id: string
  tenant_id: string
  channel_id: number
  channel_name: string
  channel_username: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TelegramChannelCreate {
  channel_id: number
  channel_name: string
  channel_username?: string
  is_active?: boolean
}

export interface TelegramChannelUpdate {
  channel_name?: string
  channel_username?: string
  is_active?: boolean
}

// MT5 Account types
export interface MT5Account {
  id: string
  tenant_id: string
  name: string
  login: number
  server: string
  is_active: boolean
  is_demo: boolean
  balance: number | null
  equity: number | null
  last_sync_at: string | null
  created_at: string
  updated_at: string
}

export interface MT5AccountCreate {
  name: string
  login: number
  password: string
  server: string
  is_demo?: boolean
  is_active?: boolean
}

export interface MT5AccountUpdate {
  name?: string
  password?: string
  server?: string
  is_demo?: boolean
  is_active?: boolean
}

export interface MT5AccountInfo {
  login: number
  server: string
  balance: number
  equity: number
  margin: number
  margin_free: number
  margin_level: number | null
  leverage: number
  currency: string
  trade_allowed: boolean
  trade_expert: boolean
}

export interface MT5Position {
  ticket: number
  symbol: string
  type: 'buy' | 'sell'
  volume: number
  open_price: number
  current_price: number
  stop_loss: number
  take_profit: number
  profit: number
  swap: number
  commission: number
  open_time: string
  magic: number
  comment: string
}

// Subscription types
export interface SignalSubscription {
  id: string
  tenant_id: string
  channel_id: string
  mt5_account_id: string
  lot_size: number | null
  risk_percent: number | null
  tp_strategy: TPStrategy
  tp_split_ratios: number[] | null
  symbol_mapping: Record<string, string> | null
  is_active: boolean
  channel_name?: string | null
  mt5_account_name?: string | null
  created_at: string
  updated_at: string
}

export type TPStrategy = 'equal' | 'front_weighted' | 'back_weighted' | 'custom' | 'single'

export interface SubscriptionCreate {
  channel_id: string
  mt5_account_id: string
  lot_size?: number
  risk_percent?: number
  tp_strategy?: TPStrategy
  tp_split_ratios?: number[]
  symbol_mapping?: Record<string, string>
  is_active?: boolean
}

export interface SubscriptionUpdate {
  lot_size?: number
  risk_percent?: number
  tp_strategy?: TPStrategy
  tp_split_ratios?: number[]
  symbol_mapping?: Record<string, string>
  is_active?: boolean
}

// Signal types
export type SourceType = 'telegram' | 'fxblue' | 'manual' | 'webhook'
export type SignalDirection = 'buy' | 'sell'
export type SignalStatus = 'pending' | 'processing' | 'executed' | 'partial' | 'failed' | 'cancelled' | 'expired'

export interface RawSignal {
  id: string
  tenant_id: string
  channel_id: string | null
  source_type: SourceType
  source_message_id: number | null
  raw_text: string
  received_at: string
  is_processed: boolean
}

export interface ParsedSignal {
  id: string
  tenant_id: string
  raw_signal_id: string | null
  symbol: string
  direction: SignalDirection
  entry_price: number | null
  entry_price_low: number | null
  entry_price_high: number | null
  stop_loss: number
  take_profits: number[]
  status: SignalStatus
  parser_confidence: number | null
  parser_notes: string | null
  error_message: string | null
  created_at: string
  updated_at: string
  expires_at: string | null
}

export interface SignalParsePreview {
  symbol: string
  direction: SignalDirection
  entry_price: number | null
  entry_price_low: number | null
  entry_price_high: number | null
  stop_loss: number
  take_profits: number[]
  confidence: number
  notes: string | null
}

export interface ManualSignalCreate {
  symbol: string
  direction: SignalDirection
  entry_price?: number
  stop_loss: number
  take_profits: number[]
}

// Trade types
export type TradeStatus = 'pending' | 'opening' | 'open' | 'closing' | 'closed' | 'cancelled' | 'failed'

export interface Trade {
  id: string
  tenant_id: string
  parsed_signal_id: string | null
  mt5_account_id: string
  mt5_ticket: number | null
  symbol: string
  direction: SignalDirection
  volume: number
  entry_price: number | null
  current_price: number | null
  stop_loss: number | null
  take_profit: number | null
  tp_level: number | null
  status: TradeStatus
  profit: number | null
  swap: number | null
  commission: number | null
  error_message: string | null
  opened_at: string | null
  closed_at: string | null
  created_at: string
  updated_at: string
  mt5_account_name?: string | null
}

export interface TradeStats {
  total_trades: number
  open_trades: number
  closed_trades: number
  winning_trades: number
  losing_trades: number
  total_profit: number
  total_commission: number
  total_swap: number
  win_rate: number | null
  average_profit: number | null
  average_loss: number | null
  profit_factor: number | null
  best_trade: number | null
  worst_trade: number | null
  period_start: string | null
  period_end: string | null
}

// WebSocket types
export interface WSMessage {
  type: string
  data?: unknown
  message?: string
}

// Pagination
export interface PaginationParams {
  skip?: number
  limit?: number
}
