/**
 * KPI 卡片组件
 */

import { TrendingUp, TrendingDown } from 'lucide-react'

interface KPICardProps {
  name: string
  value: number
  changePercent: number
  trend: 'up' | 'down'
  formattedValue?: string
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function KPICard({ name, value, changePercent, trend, formattedValue }: KPICardProps) {
  const isPositive = changePercent > 0
  const TrendIcon = isPositive ? TrendingUp : TrendingDown

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-600">{name}</h3>
        <div className={`flex items-center gap-1 text-sm font-medium ${
          isPositive ? 'text-green-600' : 'text-red-600'
        }`}>
          <TrendIcon className="h-4 w-4" />
          <span>{Math.abs(changePercent).toFixed(2)}%</span>
        </div>
      </div>

      <div className="mt-2">
        <div className="text-2xl font-bold text-gray-900">
          {formattedValue || value.toLocaleString()}
        </div>
      </div>

      <div className="mt-1 text-xs text-gray-500">
        vs last period
      </div>
    </div>
  )
}
