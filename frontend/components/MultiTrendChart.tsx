/**
 * 多指标趋势图组件
 * 支持 GMV、ASP、STR 多个指标的折线图展示
 */

'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface MultiTrendChartProps {
  dates: string[]
  data: {
    gmv?: number[]
    asp?: number[]
    str_rate?: number[]
  }
  title: string
  metric: 'gmv' | 'asp' | 'str'
}

export function MultiTrendChart({ dates, data, title, metric }: MultiTrendChartProps) {
  // 转换数据格式
  const chartData = dates.map((date, index) => {
    const item: Record<string, string | number> = {
      date: date.substring(5), // 只显示 MM-DD
    }

    if (metric === 'gmv' && data.gmv) {
      item.value = data.gmv[index]
    } else if (metric === 'asp' && data.asp) {
      item.value = data.asp[index]
    } else if (metric === 'str' && data.str_rate) {
      item.value = data.str_rate[index] * 100 // 转换为百分比
    }

    return item
  })

  // 根据指标类型配置格式化函数
  const getYAxisFormatter = () => {
    if (metric === 'gmv') {
      return (value: number) => `$${(value / 1000000).toFixed(1)}M`
    } else if (metric === 'asp') {
      return (value: number) => `$${value.toFixed(0)}`
    } else if (metric === 'str') {
      return (value: number) => `${value.toFixed(1)}%`
    }
    return (value: number) => String(value)
  }

  const getTooltipFormatter = () => {
    if (metric === 'gmv') {
      return (value: number) => [`$${value.toLocaleString()}`, 'GMV']
    } else if (metric === 'asp') {
      return (value: number) => [`$${value.toFixed(2)}`, 'ASP']
    } else if (metric === 'str') {
      return (value: number) => [`${value.toFixed(2)}%`, 'STR']
    }
    return (value: number) => [String(value), 'Value']
  }

  const getColor = () => {
    if (metric === 'gmv') return '#3b82f6' // blue
    if (metric === 'asp') return '#10b981' // green
    if (metric === 'str') return '#f59e0b' // amber
    return '#6b7280' // gray
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12, fill: '#6b7280' }}
            stroke="#9ca3af"
          />
          <YAxis
            tick={{ fontSize: 12, fill: '#6b7280' }}
            tickFormatter={getYAxisFormatter()}
            stroke="#9ca3af"
          />
          <Tooltip
            formatter={getTooltipFormatter()}
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              padding: '8px 12px'
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="value"
            stroke={getColor()}
            strokeWidth={2}
            dot={{ r: 3, fill: getColor() }}
            activeDot={{ r: 5, fill: getColor() }}
            name={metric.toUpperCase()}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
