/**
 * SignalPilot Dashboard
 *
 * 业务监控主页面
 */

'use client'

import { useState } from 'react'
import useSWR from 'swr'
import { dashboardAPI } from '@/lib/api'
import { KPICard } from '@/components/KPICard'
import { MultiTrendChart } from '@/components/MultiTrendChart'
import { AnomalyAlert } from '@/components/AnomalyAlert'
import { CategoryFilter } from '@/components/CategoryFilter'
import { RefreshCw, AlertCircle, MessageSquare } from 'lucide-react'

const SITES = ['US', 'DE', 'UK', 'AU', 'FR', 'IT', 'ES', 'CA', 'CN', 'JP']

// Date range 选项
const DATE_RANGES = [
  { label: 'Last 7 days', value: 7 },
  { label: 'Last 14 days', value: 14 },
  { label: 'Last 30 days', value: 30 },
  { label: 'Last Quarter (90 days)', value: 90 },
  { label: '2024 Full Year', value: 365, isYear: 2024 },
  { label: '2025 Full Year', value: 365, isYear: 2025 },
]

export default function DashboardPage() {
  const [site, setSite] = useState('DE')
  const [days, setDays] = useState(7)
  const [category, setCategory] = useState<{ l1?: string; l2?: string }>({})

  // 获取 KPI 数据
  const { data: kpiData, error: kpiError, isLoading: kpiLoading, mutate: refetchKPI } = useSWR(
    ['kpis', site, category.l1, category.l2, days],
    () => {
      // 构建 category 参数：优先使用 L2，其次 L1
      const categoryParam = category.l2 || category.l1 || undefined
      return dashboardAPI.getKPIs({
        site,
        category: categoryParam,
        days
      })
    }
  )

  // 获取趋势数据 - 使用实际选择的天数
  const { data: trendData, error: trendError, isLoading: trendLoading } = useSWR(
    ['trends', site, category.l1, category.l2, days],
    () => {
      // 构建 category 参数：优先使用 L2，其次 L1
      const categoryParam = category.l2 || category.l1 || undefined
      return dashboardAPI.getTrends({
        site,
        category: categoryParam,
        days
      })
    }
  )

  // 获取异常数据
  const { data: anomalyData, error: anomalyError, isLoading: anomalyLoading } = useSWR(
    ['anomalies', site, days],
    () => dashboardAPI.getAnomalies({ site, days, threshold: 0.15 })
  )

  const isLoading = kpiLoading || trendLoading || anomalyLoading
  const hasError = kpiError || trendError || anomalyError

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">SignalPilot</h1>
              <p className="text-sm text-gray-500 mt-1">
                AI-Powered Cross-border Business Signal Diagnosis
              </p>
            </div>

            <div className="flex items-center gap-3">
              <a
                href="/chat"
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                <MessageSquare className="h-4 w-4" />
                AI Agent
              </a>
              <button
                onClick={() => {
                  refetchKPI()
                }}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                disabled={isLoading}
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filters */}
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
          <div className="flex items-center gap-4 flex-wrap">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Site
              </label>
              <select
                value={site}
                onChange={(e) => setSite(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {SITES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category
              </label>
              <CategoryFilter
                value={category}
                onChange={setCategory}
                disabled={isLoading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Period
              </label>
              <select
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-w-[180px]"
              >
                {DATE_RANGES.map((range) => (
                  <option key={range.label} value={range.value}>
                    {range.label}
                  </option>
                ))}
              </select>
            </div>

            {kpiData && (
              <div className="ml-auto text-sm text-gray-500">
                {kpiData.date_range}
              </div>
            )}
          </div>
        </div>

        {/* Error State */}
        {hasError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <div>
                <p className="text-sm font-medium text-red-800">Failed to load data</p>
                <p className="text-sm text-red-600 mt-1">
                  {kpiError?.message || trendError?.message || anomalyError?.message}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {isLoading && !kpiData && (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="h-8 w-8 text-blue-600 animate-spin" />
          </div>
        )}

        {/* KPI Cards */}
        {kpiData && (
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Key Metrics</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
              {kpiData.kpis.map((kpi) => (
                <KPICard
                  key={kpi.name}
                  name={kpi.name}
                  value={kpi.value}
                  changePercent={kpi.change_percent}
                  trend={kpi.trend}
                  formattedValue={kpi.formatted_value}
                />
              ))}
            </div>
          </div>
        )}

        {/* Trend Charts */}
        {trendData && (
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Trend Analysis</h2>
            <div className="grid grid-cols-1 gap-6">
              <MultiTrendChart
                dates={trendData.dates}
                data={{ gmv: trendData.gmv }}
                title={`GMV Trend - ${site} (Last ${days} Days)`}
                metric="gmv"
              />
              <MultiTrendChart
                dates={trendData.dates}
                data={{ asp: trendData.asp }}
                title={`ASP Trend - ${site} (Last ${days} Days)`}
                metric="asp"
              />
              <MultiTrendChart
                dates={trendData.dates}
                data={{ str_rate: trendData.str_rate }}
                title={`STR Trend - ${site} (Last ${days} Days)`}
                metric="str"
              />
            </div>
          </div>
        )}

        {/* Anomalies */}
        {anomalyData && (
          <div>
            <AnomalyAlert anomalies={anomalyData.anomalies} />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            SignalPilot v1.0.0 - Built with Next.js + FastAPI + DuckDB + Claude API
          </p>
        </div>
      </footer>
    </div>
  )
}
