import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import {
  TrendingUp,
  ArrowUpCircle,
  ArrowDownCircle,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  X,
  Filter,
} from 'lucide-react'
import { tradesApi, mt5AccountsApi } from '../api'
import type { Trade, TradeStatus } from '../types'
import { formatCurrency, formatDateTime, formatPrice, formatVolume, formatTimeAgo } from '../utils/format'

const STATUS_BADGES: Record<TradeStatus, { color: string; icon: React.ElementType }> = {
  pending: { color: 'badge-warning', icon: Clock },
  opening: { color: 'badge-info', icon: Clock },
  open: { color: 'badge-success', icon: CheckCircle },
  closing: { color: 'badge-warning', icon: Clock },
  closed: { color: 'badge-gray', icon: CheckCircle },
  cancelled: { color: 'badge-gray', icon: XCircle },
  failed: { color: 'badge-danger', icon: XCircle },
}

export default function Trades() {
  const [statusFilter, setStatusFilter] = useState<TradeStatus | ''>('')
  const [accountFilter, setAccountFilter] = useState('')
  const queryClient = useQueryClient()

  const { data: trades, isLoading } = useQuery({
    queryKey: ['trades', statusFilter, accountFilter],
    queryFn: () =>
      tradesApi.list({
        limit: 100,
        status_filter: statusFilter || undefined,
        mt5_account_id: accountFilter || undefined,
      }),
  })

  const { data: accounts } = useQuery({
    queryKey: ['mt5Accounts'],
    queryFn: mt5AccountsApi.list,
  })

  const closeMutation = useMutation({
    mutationFn: tradesApi.close,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trades'] })
      toast.success('Trade close request sent')
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      toast.error(error.response?.data?.detail || 'Failed to close trade')
    },
  })

  const handleCloseTrade = (trade: Trade) => {
    if (confirm('Are you sure you want to close this trade?')) {
      closeMutation.mutate(trade.id)
    }
  }

  const openTrades = trades?.filter((t) => t.status === 'open') || []
  const totalProfit = openTrades.reduce((sum, t) => sum + (t.profit || 0), 0)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Trades</h1>
          <p className="text-gray-400 mt-1">View and manage executed trades</p>
        </div>
        {openTrades.length > 0 && (
          <div className="text-right">
            <p className="text-sm text-gray-400">Open Trades: {openTrades.length}</p>
            <p className={`text-lg font-semibold ${totalProfit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {formatCurrency(totalProfit)}
            </p>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="card flex flex-wrap gap-4 items-center">
        <Filter className="w-5 h-5 text-gray-400" />
        <select
          className="input w-auto"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as TradeStatus | '')}
        >
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="closed">Closed</option>
          <option value="pending">Pending</option>
          <option value="failed">Failed</option>
        </select>
        <select
          className="input w-auto"
          value={accountFilter}
          onChange={(e) => setAccountFilter(e.target.value)}
        >
          <option value="">All Accounts</option>
          {accounts?.map((acc) => (
            <option key={acc.id} value={acc.id}>
              {acc.name}
            </option>
          ))}
        </select>
        {(statusFilter || accountFilter) && (
          <button
            onClick={() => {
              setStatusFilter('')
              setAccountFilter('')
            }}
            className="text-sm text-primary-400 hover:text-primary-300"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Trades List */}
      {isLoading ? (
        <div className="card flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500" />
        </div>
      ) : trades?.length === 0 ? (
        <div className="card text-center py-12">
          <TrendingUp className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white">No trades yet</h3>
          <p className="text-gray-400 mt-1">Trades will appear here when signals are executed</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-sm text-gray-400 border-b border-gray-700">
                <th className="pb-3 font-medium">Symbol</th>
                <th className="pb-3 font-medium">Type</th>
                <th className="pb-3 font-medium">Volume</th>
                <th className="pb-3 font-medium">Entry</th>
                <th className="pb-3 font-medium">Current</th>
                <th className="pb-3 font-medium">SL / TP</th>
                <th className="pb-3 font-medium">Profit</th>
                <th className="pb-3 font-medium">Status</th>
                <th className="pb-3 font-medium">Account</th>
                <th className="pb-3 font-medium">Time</th>
                <th className="pb-3 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {trades?.map((trade) => (
                <TradeRow
                  key={trade.id}
                  trade={trade}
                  onClose={() => handleCloseTrade(trade)}
                  isClosing={closeMutation.isPending}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function TradeRow({
  trade,
  onClose,
  isClosing,
}: {
  trade: Trade
  onClose: () => void
  isClosing: boolean
}) {
  const statusInfo = STATUS_BADGES[trade.status]
  const StatusIcon = statusInfo.icon
  const isBuy = trade.direction === 'buy'

  return (
    <tr className="table-row">
      <td className="py-3">
        <div className="flex items-center space-x-2">
          {isBuy ? (
            <ArrowUpCircle className="w-4 h-4 text-green-400" />
          ) : (
            <ArrowDownCircle className="w-4 h-4 text-red-400" />
          )}
          <span className="font-medium text-white">{trade.symbol}</span>
        </div>
      </td>
      <td className={`py-3 ${isBuy ? 'text-green-400' : 'text-red-400'}`}>
        {trade.direction.toUpperCase()}
      </td>
      <td className="py-3 text-gray-300">{formatVolume(trade.volume)}</td>
      <td className="py-3 text-gray-300">
        {trade.entry_price ? formatPrice(trade.entry_price, trade.symbol) : '-'}
      </td>
      <td className="py-3 text-gray-300">
        {trade.current_price ? formatPrice(trade.current_price, trade.symbol) : '-'}
      </td>
      <td className="py-3 text-sm">
        <span className="text-red-400">
          {trade.stop_loss ? formatPrice(trade.stop_loss, trade.symbol) : '-'}
        </span>
        {' / '}
        <span className="text-green-400">
          {trade.take_profit ? formatPrice(trade.take_profit, trade.symbol) : '-'}
        </span>
        {trade.tp_level && <span className="text-gray-500 text-xs ml-1">(TP{trade.tp_level})</span>}
      </td>
      <td className={`py-3 font-medium ${(trade.profit || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
        {trade.profit !== null ? formatCurrency(trade.profit) : '-'}
      </td>
      <td className="py-3">
        <span className={`badge ${statusInfo.color} flex items-center w-fit`}>
          <StatusIcon className="w-3 h-3 mr-1" />
          {trade.status}
        </span>
      </td>
      <td className="py-3 text-gray-400 text-sm">{trade.mt5_account_name || '-'}</td>
      <td className="py-3 text-gray-400 text-sm">
        {trade.opened_at ? formatTimeAgo(trade.opened_at) : formatTimeAgo(trade.created_at)}
      </td>
      <td className="py-3">
        {trade.status === 'open' && (
          <button
            onClick={onClose}
            disabled={isClosing}
            className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded"
            title="Close Trade"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </td>
    </tr>
  )
}
