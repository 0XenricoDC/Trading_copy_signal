import { useQuery } from '@tanstack/react-query'
import {
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  Target,
  BarChart3,
} from 'lucide-react'
import { tradesApi, mt5AccountsApi, channelsApi, subscriptionsApi } from '../api'
import { formatCurrency, formatPercent } from '../utils/format'

function StatCard({
  title,
  value,
  icon: Icon,
  trend,
  trendValue,
  color = 'primary',
}: {
  title: string
  value: string | number
  icon: React.ElementType
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  color?: 'primary' | 'success' | 'danger' | 'warning'
}) {
  const colorClasses = {
    primary: 'text-primary-400 bg-primary-600/20',
    success: 'text-green-400 bg-green-600/20',
    danger: 'text-red-400 bg-red-600/20',
    warning: 'text-yellow-400 bg-yellow-600/20',
  }

  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-400">{title}</p>
          <p className="mt-1 text-2xl font-semibold text-white">{value}</p>
          {trendValue && (
            <div className="mt-2 flex items-center text-sm">
              {trend === 'up' && <TrendingUp className="w-4 h-4 text-green-400 mr-1" />}
              {trend === 'down' && <TrendingDown className="w-4 h-4 text-red-400 mr-1" />}
              <span className={trend === 'up' ? 'text-green-400' : trend === 'down' ? 'text-red-400' : 'text-gray-400'}>
                {trendValue}
              </span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['tradeStats'],
    queryFn: () => tradesApi.getStats(),
  })

  const { data: accounts } = useQuery({
    queryKey: ['mt5Accounts'],
    queryFn: () => mt5AccountsApi.list(),
  })

  const { data: channels } = useQuery({
    queryKey: ['channels'],
    queryFn: () => channelsApi.list(),
  })

  const { data: subscriptions } = useQuery({
    queryKey: ['subscriptions'],
    queryFn: () => subscriptionsApi.list(),
  })

  const totalBalance = accounts?.reduce((sum, acc) => sum + (acc.balance || 0), 0) || 0
  const totalEquity = accounts?.reduce((sum, acc) => sum + (acc.equity || 0), 0) || 0
  const activeChannels = channels?.filter((c) => c.is_active).length || 0
  const activeSubscriptions = subscriptions?.filter((s) => s.is_active).length || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-400 mt-1">Overview of your trading activity</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Profit"
          value={statsLoading ? '...' : formatCurrency(stats?.total_profit || 0)}
          icon={DollarSign}
          trend={stats?.total_profit ? (stats.total_profit > 0 ? 'up' : 'down') : 'neutral'}
          color={stats?.total_profit ? (stats.total_profit > 0 ? 'success' : 'danger') : 'primary'}
        />
        <StatCard
          title="Win Rate"
          value={statsLoading ? '...' : stats?.win_rate ? formatPercent(stats.win_rate) : 'N/A'}
          icon={Target}
          color={stats?.win_rate ? (stats.win_rate >= 50 ? 'success' : 'danger') : 'primary'}
        />
        <StatCard
          title="Open Trades"
          value={statsLoading ? '...' : stats?.open_trades || 0}
          icon={Activity}
          color="warning"
        />
        <StatCard
          title="Total Trades"
          value={statsLoading ? '...' : stats?.total_trades || 0}
          icon={BarChart3}
          color="primary"
        />
      </div>

      {/* Secondary Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Account Summary */}
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">Account Summary</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Total Balance</span>
              <span className="text-white font-medium">{formatCurrency(totalBalance)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Total Equity</span>
              <span className="text-white font-medium">{formatCurrency(totalEquity)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Connected Accounts</span>
              <span className="text-white font-medium">{accounts?.length || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Active Channels</span>
              <span className="text-white font-medium">{activeChannels}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Active Subscriptions</span>
              <span className="text-white font-medium">{activeSubscriptions}</span>
            </div>
          </div>
        </div>

        {/* Trading Stats */}
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">Trading Statistics</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Winning Trades</span>
              <span className="text-green-400 font-medium">{stats?.winning_trades || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Losing Trades</span>
              <span className="text-red-400 font-medium">{stats?.losing_trades || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Average Profit</span>
              <span className="text-green-400 font-medium">
                {stats?.average_profit ? formatCurrency(stats.average_profit) : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Average Loss</span>
              <span className="text-red-400 font-medium">
                {stats?.average_loss ? formatCurrency(Math.abs(stats.average_loss)) : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Profit Factor</span>
              <span className="text-white font-medium">
                {stats?.profit_factor ? stats.profit_factor.toFixed(2) : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Best Trade</span>
              <span className="text-green-400 font-medium">
                {stats?.best_trade ? formatCurrency(stats.best_trade) : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Worst Trade</span>
              <span className="text-red-400 font-medium">
                {stats?.worst_trade ? formatCurrency(stats.worst_trade) : 'N/A'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
