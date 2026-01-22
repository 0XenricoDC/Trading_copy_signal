import apiClient from './client'
import type {
  Token,
  LoginRequest,
  RegisterRequest,
  Tenant,
  TelegramChannel,
  TelegramChannelCreate,
  TelegramChannelUpdate,
  MT5Account,
  MT5AccountCreate,
  MT5AccountUpdate,
  MT5AccountInfo,
  MT5Position,
  SignalSubscription,
  SubscriptionCreate,
  SubscriptionUpdate,
  ParsedSignal,
  SignalParsePreview,
  ManualSignalCreate,
  Trade,
  TradeStats,
  TradeStatus,
} from '../types'

// Auth API
export const authApi = {
  login: async (data: LoginRequest): Promise<Token> => {
    const response = await apiClient.post<Token>('/auth/login', data)
    return response.data
  },

  register: async (data: RegisterRequest): Promise<Token> => {
    const response = await apiClient.post<Token>('/auth/register', data)
    return response.data
  },

  me: async (): Promise<Tenant> => {
    const response = await apiClient.get<Tenant>('/auth/me')
    return response.data
  },

  refresh: async (refreshToken: string): Promise<Token> => {
    const response = await apiClient.post<Token>('/auth/refresh', null, {
      params: { refresh_token: refreshToken },
    })
    return response.data
  },
}

// Telegram Channels API
export const channelsApi = {
  list: async (): Promise<TelegramChannel[]> => {
    const response = await apiClient.get<TelegramChannel[]>('/channels')
    return response.data
  },

  get: async (id: string): Promise<TelegramChannel> => {
    const response = await apiClient.get<TelegramChannel>(`/channels/${id}`)
    return response.data
  },

  create: async (data: TelegramChannelCreate): Promise<TelegramChannel> => {
    const response = await apiClient.post<TelegramChannel>('/channels', data)
    return response.data
  },

  update: async (id: string, data: TelegramChannelUpdate): Promise<TelegramChannel> => {
    const response = await apiClient.put<TelegramChannel>(`/channels/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/channels/${id}`)
  },
}

// MT5 Accounts API
export const mt5AccountsApi = {
  list: async (): Promise<MT5Account[]> => {
    const response = await apiClient.get<MT5Account[]>('/mt5-accounts')
    return response.data
  },

  get: async (id: string): Promise<MT5Account> => {
    const response = await apiClient.get<MT5Account>(`/mt5-accounts/${id}`)
    return response.data
  },

  create: async (data: MT5AccountCreate): Promise<MT5Account> => {
    const response = await apiClient.post<MT5Account>('/mt5-accounts', data)
    return response.data
  },

  update: async (id: string, data: MT5AccountUpdate): Promise<MT5Account> => {
    const response = await apiClient.put<MT5Account>(`/mt5-accounts/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/mt5-accounts/${id}`)
  },

  test: async (id: string): Promise<MT5AccountInfo> => {
    const response = await apiClient.post<MT5AccountInfo>(`/mt5-accounts/${id}/test`)
    return response.data
  },

  getPositions: async (id: string): Promise<MT5Position[]> => {
    const response = await apiClient.get<MT5Position[]>(`/mt5-accounts/${id}/positions`)
    return response.data
  },
}

// Subscriptions API
export const subscriptionsApi = {
  list: async (activeOnly = false): Promise<SignalSubscription[]> => {
    const response = await apiClient.get<SignalSubscription[]>('/subscriptions', {
      params: { active_only: activeOnly },
    })
    return response.data
  },

  get: async (id: string): Promise<SignalSubscription> => {
    const response = await apiClient.get<SignalSubscription>(`/subscriptions/${id}`)
    return response.data
  },

  create: async (data: SubscriptionCreate): Promise<SignalSubscription> => {
    const response = await apiClient.post<SignalSubscription>('/subscriptions', data)
    return response.data
  },

  update: async (id: string, data: SubscriptionUpdate): Promise<SignalSubscription> => {
    const response = await apiClient.put<SignalSubscription>(`/subscriptions/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/subscriptions/${id}`)
  },
}

// Signals API
export const signalsApi = {
  list: async (params?: {
    skip?: number
    limit?: number
    status?: string
  }): Promise<ParsedSignal[]> => {
    const response = await apiClient.get<ParsedSignal[]>('/signals', { params })
    return response.data
  },

  get: async (id: string): Promise<ParsedSignal> => {
    const response = await apiClient.get<ParsedSignal>(`/signals/${id}`)
    return response.data
  },

  parsePreview: async (text: string): Promise<SignalParsePreview> => {
    const response = await apiClient.post<SignalParsePreview>('/signals/parse-preview', { text })
    return response.data
  },

  createManual: async (data: ManualSignalCreate): Promise<ParsedSignal> => {
    const response = await apiClient.post<ParsedSignal>('/signals/manual', data)
    return response.data
  },
}

// Trades API
export const tradesApi = {
  list: async (params?: {
    skip?: number
    limit?: number
    status_filter?: TradeStatus
    mt5_account_id?: string
    symbol?: string
    from_date?: string
    to_date?: string
  }): Promise<Trade[]> => {
    const response = await apiClient.get<Trade[]>('/trades', { params })
    return response.data
  },

  get: async (id: string): Promise<Trade> => {
    const response = await apiClient.get<Trade>(`/trades/${id}`)
    return response.data
  },

  getStats: async (params?: {
    mt5_account_id?: string
    from_date?: string
    to_date?: string
  }): Promise<TradeStats> => {
    const response = await apiClient.get<TradeStats>('/trades/stats', { params })
    return response.data
  },

  close: async (id: string): Promise<{ message: string; trade_id: string }> => {
    const response = await apiClient.post<{ message: string; trade_id: string }>(`/trades/${id}/close`)
    return response.data
  },
}

export default {
  auth: authApi,
  channels: channelsApi,
  mt5Accounts: mt5AccountsApi,
  subscriptions: subscriptionsApi,
  signals: signalsApi,
  trades: tradesApi,
}
