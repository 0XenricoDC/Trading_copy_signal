import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import {
  Plus,
  Trash2,
  Edit2,
  Server,
  RefreshCw,
  CheckCircle,
  XCircle,
  Eye,
  EyeOff,
  Power,
  PowerOff,
} from 'lucide-react'
import { mt5AccountsApi } from '../api'
import type { MT5AccountCreate, MT5AccountUpdate, MT5Account } from '../types'
import { formatCurrency, formatTimeAgo } from '../utils/format'
import Modal from '../components/Modal'

export default function Accounts() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingAccount, setEditingAccount] = useState<MT5Account | null>(null)
  const [testingId, setTestingId] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const { data: accounts, isLoading } = useQuery({
    queryKey: ['mt5Accounts'],
    queryFn: mt5AccountsApi.list,
  })

  const createMutation = useMutation({
    mutationFn: mt5AccountsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mt5Accounts'] })
      setIsModalOpen(false)
      toast.success('Account added successfully')
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      toast.error(error.response?.data?.detail || 'Failed to add account')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: MT5AccountUpdate }) =>
      mt5AccountsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mt5Accounts'] })
      setEditingAccount(null)
      toast.success('Account updated successfully')
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      toast.error(error.response?.data?.detail || 'Failed to update account')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: mt5AccountsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mt5Accounts'] })
      toast.success('Account deleted')
    },
    onError: () => {
      toast.error('Failed to delete account')
    },
  })

  const testMutation = useMutation({
    mutationFn: mt5AccountsApi.test,
    onSuccess: (data) => {
      toast.success(`Connection successful! Balance: ${formatCurrency(data.balance)}`)
      setTestingId(null)
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      toast.error(error.response?.data?.detail || 'Connection failed')
      setTestingId(null)
    },
  })

  const handleTest = (id: string) => {
    setTestingId(id)
    testMutation.mutate(id)
  }

  const handleToggleActive = (account: MT5Account) => {
    updateMutation.mutate({
      id: account.id,
      data: { is_active: !account.is_active },
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">MT5 Accounts</h1>
          <p className="text-gray-400 mt-1">Connect your MetaTrader 5 trading accounts</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="btn btn-primary flex items-center"
        >
          <Plus className="w-5 h-5 mr-2" />
          Add Account
        </button>
      </div>

      {/* Accounts List */}
      {isLoading ? (
        <div className="card flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500" />
        </div>
      ) : accounts?.length === 0 ? (
        <div className="card text-center py-12">
          <Server className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white">No accounts yet</h3>
          <p className="text-gray-400 mt-1">Add an MT5 account to start trading</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {accounts?.map((account) => (
            <div key={account.id} className="card">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4">
                  <div className={`p-3 rounded-lg ${account.is_active ? 'bg-primary-600/20' : 'bg-gray-700'}`}>
                    <Server className={`w-6 h-6 ${account.is_active ? 'text-primary-400' : 'text-gray-400'}`} />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="font-medium text-white">{account.name}</h3>
                      {account.is_demo && (
                        <span className="badge badge-info">Demo</span>
                      )}
                      <span className={`badge ${account.is_active ? 'badge-success' : 'badge-gray'}`}>
                        {account.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    <div className="flex items-center space-x-3 text-sm text-gray-400 mt-1">
                      <span>Login: {account.login}</span>
                      <span>Server: {account.server}</span>
                    </div>
                    {(account.balance !== null || account.equity !== null) && (
                      <div className="flex items-center space-x-4 text-sm mt-2">
                        <span className="text-gray-400">
                          Balance: <span className="text-white">{formatCurrency(account.balance || 0)}</span>
                        </span>
                        <span className="text-gray-400">
                          Equity: <span className="text-white">{formatCurrency(account.equity || 0)}</span>
                        </span>
                      </div>
                    )}
                    {account.last_sync_at && (
                      <p className="text-xs text-gray-500 mt-1">
                        Last sync: {formatTimeAgo(account.last_sync_at)}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleTest(account.id)}
                    disabled={testingId === account.id}
                    className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg"
                    title="Test Connection"
                  >
                    {testingId === account.id ? (
                      <RefreshCw className="w-5 h-5 animate-spin" />
                    ) : (
                      <RefreshCw className="w-5 h-5" />
                    )}
                  </button>
                  <button
                    onClick={() => handleToggleActive(account)}
                    className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg"
                    title={account.is_active ? 'Deactivate' : 'Activate'}
                  >
                    {account.is_active ? <PowerOff className="w-5 h-5" /> : <Power className="w-5 h-5" />}
                  </button>
                  <button
                    onClick={() => setEditingAccount(account)}
                    className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg"
                    title="Edit"
                  >
                    <Edit2 className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => {
                      if (confirm('Are you sure you want to delete this account?')) {
                        deleteMutation.mutate(account.id)
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

      {/* Add Account Modal */}
      <AccountModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={(data) => createMutation.mutate(data)}
        isLoading={createMutation.isPending}
      />

      {/* Edit Account Modal */}
      <AccountModal
        isOpen={!!editingAccount}
        onClose={() => setEditingAccount(null)}
        onSubmit={(data) => editingAccount && updateMutation.mutate({ id: editingAccount.id, data })}
        isLoading={updateMutation.isPending}
        account={editingAccount}
      />
    </div>
  )
}

function AccountModal({
  isOpen,
  onClose,
  onSubmit,
  isLoading,
  account,
}: {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: MT5AccountCreate | MT5AccountUpdate) => void
  isLoading: boolean
  account?: MT5Account | null
}) {
  const isEditing = !!account
  const [showPassword, setShowPassword] = useState(false)
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<MT5AccountCreate>({
    defaultValues: account
      ? { name: account.name, login: account.login, server: account.server, is_demo: account.is_demo }
      : {},
  })

  const handleClose = () => {
    reset()
    onClose()
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title={isEditing ? 'Edit Account' : 'Add MT5 Account'}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="label">Account Name</label>
          <input
            type="text"
            className="input"
            placeholder="My Trading Account"
            {...register('name', { required: 'Name is required' })}
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-400">{errors.name.message}</p>
          )}
        </div>

        {!isEditing && (
          <div>
            <label className="label">Login</label>
            <input
              type="number"
              className="input"
              placeholder="12345678"
              {...register('login', {
                required: 'Login is required',
                valueAsNumber: true,
              })}
            />
            {errors.login && (
              <p className="mt-1 text-sm text-red-400">{errors.login.message}</p>
            )}
          </div>
        )}

        <div>
          <label className="label">{isEditing ? 'New Password (leave empty to keep current)' : 'Password'}</label>
          <div className="relative">
            <input
              type={showPassword ? 'text' : 'password'}
              className="input pr-10"
              placeholder="••••••••"
              {...register('password', {
                required: isEditing ? false : 'Password is required',
              })}
            />
            <button
              type="button"
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>
          {errors.password && (
            <p className="mt-1 text-sm text-red-400">{errors.password.message}</p>
          )}
        </div>

        <div>
          <label className="label">Server</label>
          <input
            type="text"
            className="input"
            placeholder="MetaQuotes-Demo"
            {...register('server', { required: 'Server is required' })}
          />
          {errors.server && (
            <p className="mt-1 text-sm text-red-400">{errors.server.message}</p>
          )}
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="is_demo"
            className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-primary-500 focus:ring-primary-500"
            {...register('is_demo')}
          />
          <label htmlFor="is_demo" className="ml-2 text-sm text-gray-300">
            This is a demo account
          </label>
        </div>

        <div className="flex justify-end space-x-3 pt-4">
          <button type="button" onClick={handleClose} className="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={isLoading} className="btn btn-primary">
            {isLoading ? 'Saving...' : isEditing ? 'Update' : 'Add Account'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
