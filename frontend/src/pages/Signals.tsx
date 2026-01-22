import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import {
  Signal,
  ArrowUpCircle,
  ArrowDownCircle,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Plus,
  Search,
} from 'lucide-react'
import { signalsApi } from '../api'
import type { ParsedSignal, SignalStatus, SignalDirection, ManualSignalCreate } from '../types'
import { formatDateTime, formatPrice, formatTimeAgo } from '../utils/format'
import Modal from '../components/Modal'

const STATUS_BADGES: Record<SignalStatus, { color: string; icon: React.ElementType }> = {
  pending: { color: 'badge-warning', icon: Clock },
  processing: { color: 'badge-info', icon: Clock },
  executed: { color: 'badge-success', icon: CheckCircle },
  partial: { color: 'badge-warning', icon: AlertCircle },
  failed: { color: 'badge-danger', icon: XCircle },
  cancelled: { color: 'badge-gray', icon: XCircle },
  expired: { color: 'badge-gray', icon: Clock },
}

export default function Signals() {
  const [isParseModalOpen, setIsParseModalOpen] = useState(false)
  const [isManualModalOpen, setIsManualModalOpen] = useState(false)

  const { data: signals, isLoading } = useQuery({
    queryKey: ['signals'],
    queryFn: () => signalsApi.list({ limit: 100 }),
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Signals</h1>
          <p className="text-gray-400 mt-1">View and manage trading signals</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setIsParseModalOpen(true)}
            className="btn btn-secondary flex items-center"
          >
            <Search className="w-5 h-5 mr-2" />
            Parse Preview
          </button>
          <button
            onClick={() => setIsManualModalOpen(true)}
            className="btn btn-primary flex items-center"
          >
            <Plus className="w-5 h-5 mr-2" />
            Manual Signal
          </button>
        </div>
      </div>

      {/* Signals List */}
      {isLoading ? (
        <div className="card flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500" />
        </div>
      ) : signals?.length === 0 ? (
        <div className="card text-center py-12">
          <Signal className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white">No signals yet</h3>
          <p className="text-gray-400 mt-1">Signals will appear here when received from channels</p>
        </div>
      ) : (
        <div className="space-y-3">
          {signals?.map((signal) => (
            <SignalCard key={signal.id} signal={signal} />
          ))}
        </div>
      )}

      {/* Parse Preview Modal */}
      <ParsePreviewModal
        isOpen={isParseModalOpen}
        onClose={() => setIsParseModalOpen(false)}
      />

      {/* Manual Signal Modal */}
      <ManualSignalModal
        isOpen={isManualModalOpen}
        onClose={() => setIsManualModalOpen(false)}
      />
    </div>
  )
}

function SignalCard({ signal }: { signal: ParsedSignal }) {
  const statusInfo = STATUS_BADGES[signal.status]
  const StatusIcon = statusInfo.icon

  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-4">
          <div className={`p-3 rounded-lg ${signal.direction === 'buy' ? 'bg-green-600/20' : 'bg-red-600/20'}`}>
            {signal.direction === 'buy' ? (
              <ArrowUpCircle className="w-6 h-6 text-green-400" />
            ) : (
              <ArrowDownCircle className="w-6 h-6 text-red-400" />
            )}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="font-medium text-white">
                {signal.direction.toUpperCase()} {signal.symbol}
              </h3>
              <span className={`badge ${statusInfo.color} flex items-center`}>
                <StatusIcon className="w-3 h-3 mr-1" />
                {signal.status}
              </span>
              {signal.parser_confidence && (
                <span className="badge badge-gray">
                  {Math.round(signal.parser_confidence * 100)}% confidence
                </span>
              )}
            </div>
            <div className="flex items-center flex-wrap gap-x-4 gap-y-1 text-sm text-gray-400 mt-2">
              {signal.entry_price ? (
                <span>Entry: {formatPrice(signal.entry_price, signal.symbol)}</span>
              ) : signal.entry_price_low && signal.entry_price_high ? (
                <span>
                  Entry Zone: {formatPrice(signal.entry_price_low, signal.symbol)} -{' '}
                  {formatPrice(signal.entry_price_high, signal.symbol)}
                </span>
              ) : (
                <span>Market Order</span>
              )}
              <span className="text-red-400">SL: {formatPrice(signal.stop_loss, signal.symbol)}</span>
              {signal.take_profits.length > 0 && (
                <span className="text-green-400">
                  TP: {signal.take_profits.map((tp) => formatPrice(tp, signal.symbol)).join(' / ')}
                </span>
              )}
            </div>
            {signal.parser_notes && (
              <p className="text-xs text-gray-500 mt-1">{signal.parser_notes}</p>
            )}
            {signal.error_message && (
              <p className="text-xs text-red-400 mt-1">Error: {signal.error_message}</p>
            )}
            <p className="text-xs text-gray-500 mt-2">
              {formatTimeAgo(signal.created_at)}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function ParsePreviewModal({
  isOpen,
  onClose,
}: {
  isOpen: boolean
  onClose: () => void
}) {
  const [text, setText] = useState('')
  const [result, setResult] = useState<any>(null)

  const parseMutation = useMutation({
    mutationFn: signalsApi.parsePreview,
    onSuccess: (data) => {
      setResult(data)
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      toast.error(error.response?.data?.detail || 'Failed to parse signal')
    },
  })

  const handleParse = () => {
    if (!text.trim()) return
    parseMutation.mutate(text)
  }

  const handleClose = () => {
    setText('')
    setResult(null)
    onClose()
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Parse Signal Preview" size="lg">
      <div className="space-y-4">
        <div>
          <label className="label">Signal Text</label>
          <textarea
            className="input min-h-[120px]"
            placeholder={`Example:\nBUY EURUSD @ 1.0850\nSL: 1.0800\nTP1: 1.0900\nTP2: 1.0950`}
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        </div>

        <button
          onClick={handleParse}
          disabled={!text.trim() || parseMutation.isPending}
          className="btn btn-primary w-full"
        >
          {parseMutation.isPending ? 'Parsing...' : 'Parse Signal'}
        </button>

        {result && (
          <div className="bg-gray-900 rounded-lg p-4 space-y-2">
            <h4 className="font-medium text-white mb-3">Parsed Result:</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <span className="text-gray-400">Symbol:</span>
              <span className="text-white">{result.symbol}</span>
              <span className="text-gray-400">Direction:</span>
              <span className={result.direction === 'buy' ? 'text-green-400' : 'text-red-400'}>
                {result.direction?.toUpperCase()}
              </span>
              <span className="text-gray-400">Entry:</span>
              <span className="text-white">
                {result.entry_price || 'Market'}
                {result.entry_price_low && ` (Zone: ${result.entry_price_low} - ${result.entry_price_high})`}
              </span>
              <span className="text-gray-400">Stop Loss:</span>
              <span className="text-red-400">{result.stop_loss}</span>
              <span className="text-gray-400">Take Profits:</span>
              <span className="text-green-400">
                {result.take_profits?.join(', ') || 'None'}
              </span>
              <span className="text-gray-400">Confidence:</span>
              <span className="text-white">{Math.round((result.confidence || 0) * 100)}%</span>
            </div>
            {result.notes && (
              <p className="text-xs text-gray-400 mt-2">Notes: {result.notes}</p>
            )}
          </div>
        )}
      </div>
    </Modal>
  )
}

function ManualSignalModal({
  isOpen,
  onClose,
}: {
  isOpen: boolean
  onClose: () => void
}) {
  const queryClient = useQueryClient()
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ManualSignalCreate & { tp_string: string }>()

  const createMutation = useMutation({
    mutationFn: signalsApi.createManual,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signals'] })
      toast.success('Signal created successfully')
      handleClose()
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      toast.error(error.response?.data?.detail || 'Failed to create signal')
    },
  })

  const handleClose = () => {
    reset()
    onClose()
  }

  const onSubmit = (data: ManualSignalCreate & { tp_string: string }) => {
    const take_profits = data.tp_string
      ? data.tp_string.split(',').map((s) => parseFloat(s.trim())).filter((n) => !isNaN(n))
      : []

    createMutation.mutate({
      symbol: data.symbol.toUpperCase(),
      direction: data.direction,
      entry_price: data.entry_price || undefined,
      stop_loss: data.stop_loss,
      take_profits,
    })
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Create Manual Signal">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Symbol</label>
            <input
              type="text"
              className="input"
              placeholder="EURUSD"
              {...register('symbol', { required: 'Symbol is required' })}
            />
            {errors.symbol && (
              <p className="mt-1 text-sm text-red-400">{errors.symbol.message}</p>
            )}
          </div>
          <div>
            <label className="label">Direction</label>
            <select
              className="input"
              {...register('direction', { required: 'Direction is required' })}
            >
              <option value="buy">BUY</option>
              <option value="sell">SELL</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Entry Price (optional)</label>
            <input
              type="number"
              step="any"
              className="input"
              placeholder="Market order if empty"
              {...register('entry_price', { valueAsNumber: true })}
            />
          </div>
          <div>
            <label className="label">Stop Loss</label>
            <input
              type="number"
              step="any"
              className="input"
              placeholder="1.0800"
              {...register('stop_loss', {
                required: 'Stop loss is required',
                valueAsNumber: true,
              })}
            />
            {errors.stop_loss && (
              <p className="mt-1 text-sm text-red-400">{errors.stop_loss.message}</p>
            )}
          </div>
        </div>

        <div>
          <label className="label">Take Profit(s)</label>
          <input
            type="text"
            className="input"
            placeholder="1.0900, 1.0950, 1.1000"
            {...register('tp_string')}
          />
          <p className="text-xs text-gray-400 mt-1">Comma-separated prices</p>
        </div>

        <div className="flex justify-end space-x-3 pt-4">
          <button type="button" onClick={handleClose} className="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={createMutation.isPending} className="btn btn-primary">
            {createMutation.isPending ? 'Creating...' : 'Create Signal'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
