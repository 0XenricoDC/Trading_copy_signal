import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Plus, Trash2, Edit2, MessageSquare, Power, PowerOff } from 'lucide-react'
import { channelsApi } from '../api'
import type { TelegramChannelCreate, TelegramChannelUpdate, TelegramChannel } from '../types'
import { formatTimeAgo } from '../utils/format'
import Modal from '../components/Modal'

export default function Channels() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingChannel, setEditingChannel] = useState<TelegramChannel | null>(null)
  const queryClient = useQueryClient()

  const { data: channels, isLoading } = useQuery({
    queryKey: ['channels'],
    queryFn: channelsApi.list,
  })

  const createMutation = useMutation({
    mutationFn: channelsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] })
      setIsModalOpen(false)
      toast.success('Channel added successfully')
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      toast.error(error.response?.data?.detail || 'Failed to add channel')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: TelegramChannelUpdate }) =>
      channelsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] })
      setEditingChannel(null)
      toast.success('Channel updated successfully')
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      toast.error(error.response?.data?.detail || 'Failed to update channel')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: channelsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] })
      toast.success('Channel deleted')
    },
    onError: () => {
      toast.error('Failed to delete channel')
    },
  })

  const handleToggleActive = (channel: TelegramChannel) => {
    updateMutation.mutate({
      id: channel.id,
      data: { is_active: !channel.is_active },
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Telegram Channels</h1>
          <p className="text-gray-400 mt-1">Manage your signal source channels</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="btn btn-primary flex items-center"
        >
          <Plus className="w-5 h-5 mr-2" />
          Add Channel
        </button>
      </div>

      {/* Channels List */}
      {isLoading ? (
        <div className="card flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500" />
        </div>
      ) : channels?.length === 0 ? (
        <div className="card text-center py-12">
          <MessageSquare className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white">No channels yet</h3>
          <p className="text-gray-400 mt-1">Add a Telegram channel to start receiving signals</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {channels?.map((channel) => (
            <div key={channel.id} className="card flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className={`p-3 rounded-lg ${channel.is_active ? 'bg-primary-600/20' : 'bg-gray-700'}`}>
                  <MessageSquare className={`w-6 h-6 ${channel.is_active ? 'text-primary-400' : 'text-gray-400'}`} />
                </div>
                <div>
                  <h3 className="font-medium text-white">{channel.channel_name}</h3>
                  <div className="flex items-center space-x-3 text-sm text-gray-400">
                    <span>ID: {channel.channel_id}</span>
                    {channel.channel_username && <span>@{channel.channel_username}</span>}
                    <span>Added {formatTimeAgo(channel.created_at)}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`badge ${channel.is_active ? 'badge-success' : 'badge-gray'}`}>
                  {channel.is_active ? 'Active' : 'Inactive'}
                </span>
                <button
                  onClick={() => handleToggleActive(channel)}
                  className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg"
                  title={channel.is_active ? 'Deactivate' : 'Activate'}
                >
                  {channel.is_active ? <PowerOff className="w-5 h-5" /> : <Power className="w-5 h-5" />}
                </button>
                <button
                  onClick={() => setEditingChannel(channel)}
                  className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg"
                  title="Edit"
                >
                  <Edit2 className="w-5 h-5" />
                </button>
                <button
                  onClick={() => {
                    if (confirm('Are you sure you want to delete this channel?')) {
                      deleteMutation.mutate(channel.id)
                    }
                  }}
                  className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded-lg"
                  title="Delete"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Channel Modal */}
      <ChannelModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={(data) => createMutation.mutate(data)}
        isLoading={createMutation.isPending}
      />

      {/* Edit Channel Modal */}
      <ChannelModal
        isOpen={!!editingChannel}
        onClose={() => setEditingChannel(null)}
        onSubmit={(data) => editingChannel && updateMutation.mutate({ id: editingChannel.id, data })}
        isLoading={updateMutation.isPending}
        channel={editingChannel}
      />
    </div>
  )
}

function ChannelModal({
  isOpen,
  onClose,
  onSubmit,
  isLoading,
  channel,
}: {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: TelegramChannelCreate | TelegramChannelUpdate) => void
  isLoading: boolean
  channel?: TelegramChannel | null
}) {
  const isEditing = !!channel
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TelegramChannelCreate>({
    defaultValues: channel || {},
  })

  const handleClose = () => {
    reset()
    onClose()
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title={isEditing ? 'Edit Channel' : 'Add Channel'}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {!isEditing && (
          <div>
            <label className="label">Channel ID</label>
            <input
              type="number"
              className="input"
              placeholder="-1001234567890"
              {...register('channel_id', {
                required: 'Channel ID is required',
                valueAsNumber: true,
              })}
            />
            {errors.channel_id && (
              <p className="mt-1 text-sm text-red-400">{errors.channel_id.message}</p>
            )}
            <p className="mt-1 text-xs text-gray-400">
              You can find this using Telegram bots like @getidsbot
            </p>
          </div>
        )}

        <div>
          <label className="label">Channel Name</label>
          <input
            type="text"
            className="input"
            placeholder="Gold Signals VIP"
            {...register('channel_name', {
              required: 'Channel name is required',
            })}
          />
          {errors.channel_name && (
            <p className="mt-1 text-sm text-red-400">{errors.channel_name.message}</p>
          )}
        </div>

        <div>
          <label className="label">Username (optional)</label>
          <input
            type="text"
            className="input"
            placeholder="goldsignals"
            {...register('channel_username')}
          />
        </div>

        <div className="flex justify-end space-x-3 pt-4">
          <button type="button" onClick={handleClose} className="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={isLoading} className="btn btn-primary">
            {isLoading ? 'Saving...' : isEditing ? 'Update' : 'Add Channel'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
