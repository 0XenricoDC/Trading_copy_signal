import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm, Controller } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Plus, Trash2, Edit2, Link2, Power, PowerOff } from 'lucide-react'
import { subscriptionsApi, channelsApi, mt5AccountsApi } from '../api'
import type { SubscriptionCreate, SubscriptionUpdate, SignalSubscription, TPStrategy } from '../types'
import { formatTimeAgo } from '../utils/format'
import Modal from '../components/Modal'

const TP_STRATEGIES: { value: TPStrategy; label: string; description: string }[] = [
  { value: 'equal', label: 'Equal Split', description: 'Split volume equally between TPs' },
  { value: 'front_weighted', label: 'Front Weighted', description: 'More volume on earlier TPs (50/30/20)' },
  { value: 'back_weighted', label: 'Back Weighted', description: 'More volume on later TPs (20/30/50)' },
  { value: 'single', label: 'Single TP', description: 'Use only the first TP' },
  { value: 'custom', label: 'Custom', description: 'Define custom split ratios' },
]

export default function Subscriptions() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingSub, setEditingSub] = useState<SignalSubscription | null>(null)
  const queryClient = useQueryClient()

  const { data: subscriptions, isLoading } = useQuery({
    queryKey: ['subscriptions'],
    queryFn: () => subscriptionsApi.list(),
  })

  const { data: channels } = useQuery({
    queryKey: ['channels'],
    queryFn: channelsApi.list,
  })

  const { data: accounts } = useQuery({
    queryKey: ['mt5Accounts'],
    queryFn: mt5AccountsApi.list,
  })

  const createMutation = useMutation({
    mutationFn: subscriptionsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] })
      setIsModalOpen(false)
      toast.success('Subscription created successfully')
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      toast.error(error.response?.data?.detail || 'Failed to create subscription')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: SubscriptionUpdate }) =>
      subscriptionsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] })
      setEditingSub(null)
      toast.success('Subscription updated successfully')
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      toast.error(error.response?.data?.detail || 'Failed to update subscription')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: subscriptionsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] })
      toast.success('Subscription deleted')
    },
    onError: () => {
      toast.error('Failed to delete subscription')
    },
  })

  const handleToggleActive = (sub: SignalSubscription) => {
    updateMutation.mutate({
      id: sub.id,
      data: { is_active: !sub.is_active },
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Subscriptions</h1>
          <p className="text-gray-400 mt-1">Link channels to accounts for signal copying</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="btn btn-primary flex items-center"
          disabled={!channels?.length || !accounts?.length}
        >
          <Plus className="w-5 h-5 mr-2" />
          New Subscription
        </button>
      </div>

      {/* Subscriptions List */}
      {isLoading ? (
        <div className="card flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500" />
        </div>
      ) : subscriptions?.length === 0 ? (
        <div className="card text-center py-12">
          <Link2 className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white">No subscriptions yet</h3>
          <p className="text-gray-400 mt-1">
            {!channels?.length
              ? 'Add a channel first'
              : !accounts?.length
              ? 'Add an MT5 account first'
              : 'Create a subscription to start copying signals'}
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {subscriptions?.map((sub) => (
            <div key={sub.id} className="card">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4">
                  <div className={`p-3 rounded-lg ${sub.is_active ? 'bg-primary-600/20' : 'bg-gray-700'}`}>
                    <Link2 className={`w-6 h-6 ${sub.is_active ? 'text-primary-400' : 'text-gray-400'}`} />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="font-medium text-white">
                        {sub.channel_name || 'Unknown Channel'} → {sub.mt5_account_name || 'Unknown Account'}
                      </h3>
                      <span className={`badge ${sub.is_active ? 'badge-success' : 'badge-gray'}`}>
                        {sub.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    <div className="flex items-center flex-wrap gap-3 text-sm text-gray-400 mt-2">
                      <span>Lot: {sub.lot_size || 'Auto'}</span>
                      {sub.risk_percent && <span>Risk: {sub.risk_percent}%</span>}
                      <span>
                        TP Strategy: {TP_STRATEGIES.find((s) => s.value === sub.tp_strategy)?.label || sub.tp_strategy}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      Created {formatTimeAgo(sub.created_at)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleToggleActive(sub)}
                    className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg"
                    title={sub.is_active ? 'Deactivate' : 'Activate'}
                  >
                    {sub.is_active ? <PowerOff className="w-5 h-5" /> : <Power className="w-5 h-5" />}
                  </button>
                  <button
                    onClick={() => setEditingSub(sub)}
                    className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg"
                    title="Edit"
                  >
                    <Edit2 className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => {
                      if (confirm('Are you sure you want to delete this subscription?')) {
                        deleteMutation.mutate(sub.id)
                      }
                    }}
                    className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded-lg"
                    title="Delete"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Subscription Modal */}
      <SubscriptionModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={(data) => createMutation.mutate(data)}
        isLoading={createMutation.isPending}
        channels={channels || []}
        accounts={accounts || []}
      />

      {/* Edit Subscription Modal */}
      <SubscriptionModal
        isOpen={!!editingSub}
        onClose={() => setEditingSub(null)}
        onSubmit={(data) => editingSub && updateMutation.mutate({ id: editingSub.id, data })}
        isLoading={updateMutation.isPending}
        subscription={editingSub}
        channels={channels || []}
        accounts={accounts || []}
      />
    </div>
  )
}

function SubscriptionModal({
  isOpen,
  onClose,
  onSubmit,
  isLoading,
  subscription,
  channels,
  accounts,
}: {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: SubscriptionCreate | SubscriptionUpdate) => void
  isLoading: boolean
  subscription?: SignalSubscription | null
  channels: { id: string; channel_name: string }[]
  accounts: { id: string; name: string }[]
}) {
  const isEditing = !!subscription

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<SubscriptionCreate>({
    defaultValues: subscription || { tp_strategy: 'equal' },
  })

  const tpStrategy = watch('tp_strategy')

  const handleClose = () => {
    reset()
    onClose()
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={isEditing ? 'Edit Subscription' : 'New Subscription'}
      size="lg"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {!isEditing && (
          <>
            <div>
              <label className="label">Signal Channel</label>
              <select
                className="input"
                {...register('channel_id', { required: 'Channel is required' })}
              >
                <option value="">Select a channel</option>
                {channels.map((ch) => (
                  <option key={ch.id} value={ch.id}>
                    {ch.channel_name}
                  </option>
                ))}
              </select>
              {errors.channel_id && (
                <p className="mt-1 text-sm text-red-400">{errors.channel_id.message}</p>
              )}
            </div>

            <div>
              <label className="label">MT5 Account</label>
              <select
                className="input"
                {...register('mt5_account_id', { required: 'Account is required' })}
              >
                <option value="">Select an account</option>
                {accounts.map((acc) => (
                  <option key={acc.id} value={acc.id}>
                    {acc.name}
                  </option>
                ))}
              </select>
              {errors.mt5_account_id && (
                <p className="mt-1 text-sm text-red-400">{errors.mt5_account_id.message}</p>
              )}
            </div>
          </>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Lot Size (optional)</label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              className="input"
              placeholder="0.10"
              {...register('lot_size', { valueAsNumber: true })}
            />
            <p className="text-xs text-gray-400 mt-1">Leave empty for signal's lot size</p>
          </div>

          <div>
            <label className="label">Risk % (optional)</label>
            <input
              type="number"
              step="0.1"
              min="0.1"
              max="100"
              className="input"
              placeholder="2"
              {...register('risk_percent', { valueAsNumber: true })}
            />
            <p className="text-xs text-gray-400 mt-1">% of balance per trade</p>
          </div>
        </div>

        <div>
          <label className="label">TP Strategy</label>
          <select className="input" {...register('tp_strategy')}>
            {TP_STRATEGIES.map((strategy) => (
              <option key={strategy.value} value={strategy.value}>
                {strategy.label} - {strategy.description}
              </option>
            ))}
          </select>
        </div>

        {tpStrategy === 'custom' && (
          <div>
            <label className="label">Custom Split Ratios</label>
            <input
              type="text"
              className="input"
              placeholder="50, 30, 20"
              {...register('tp_split_ratios')}
            />
            <p className="text-xs text-gray-400 mt-1">Comma-separated percentages (must sum to 100)</p>
          </div>
        )}

        <div className="flex justify-end space-x-3 pt-4">
          <button type="button" onClick={handleClose} className="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={isLoading} className="btn btn-primary">
            {isLoading ? 'Saving...' : isEditing ? 'Update' : 'Create Subscription'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
