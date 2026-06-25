/**
 * 趋势图组件
 */

'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface TrendChartProps {
  dates: string[]
  gmv: number[]
  title?: string
}

export function TrendChart({ dates, gmv, title = 'GMV Trend' }: TrendChartProps) {
  // 转换数据格式
  const data = dates.map((date, index) => ({
    date: date.substring(5), // 只显示 MM-DD
    gmv: gmv[index],
  }))

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
          />
          <YAxis
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => `$${(value / 1000000).toFixed(1)}M`}
          />
          <Tooltip
            formatter={(value: number) => [`$${value.toLocaleString()}`, 'GMV']}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="gmv"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
