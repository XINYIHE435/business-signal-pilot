/**
 * SignalPilot Dashboard
 *
 * 业务监控主页面
 */

'use client'

import { useState } from 'react'
import useSWR from 'swr'
import { dashboardAPI, diagnosisAPI, type Anomaly, type DiagnosisReport as DiagnosisReportData } from '@/lib/api'
import { KPICard } from '@/components/KPICard'
import { MultiTrendChart } from '@/components/MultiTrendChart'
import { AnomalyAlert } from '@/components/AnomalyAlert'
import { CategoryFilter } from '@/components/CategoryFilter'
import { DiagnosisReport } from '@/components/DiagnosisReport'
import { ReportView } from '@/components/ReportView'
import { RefreshCw, AlertCircle, MessageSquare, X, FileText, Download } from 'lucide-react'

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

  // 诊断 Modal 状态
  const [diagnosisOpen, setDiagnosisOpen] = useState(false)
  const [diagnosisLoading, setDiagnosisLoading] = useState(false)
  const [diagnosisError, setDiagnosisError] = useState<string | undefined>()
  const [diagnosisReport, setDiagnosisReport] = useState<DiagnosisReportData | null>(null)
  const [diagnosisContext, setDiagnosisContext] = useState<Anomaly | null>(null)

  // Report Modal 状态
  const [reportModalOpen, setReportModalOpen] = useState(false)
  const [reportLoading, setReportLoading] = useState(false)
  const [reportYear, setReportYear] = useState(new Date().getFullYear())
  const [reportMonth, setReportMonth] = useState(new Date().getMonth() + 1)
  const [reportData, setReportData] = useState<any>(null)
  const [reportError, setReportError] = useState<string | null>(null)

  const handleDiagnose = async (anomaly: Anomaly) => {
    setDiagnosisContext(anomaly)
    setDiagnosisReport(null)
    setDiagnosisError(undefined)
    setDiagnosisOpen(true)
    setDiagnosisLoading(true)
    try {
      const report = await diagnosisAPI.analyze({
        metric: anomaly.metric.toLowerCase(),
        site: anomaly.site,
        category: anomaly.category,
        date: anomaly.date,
        mode: 'root_cause',
      })
      setDiagnosisReport(report)
    } catch (err) {
      setDiagnosisError(err instanceof Error ? err.message : '未知错误')
    } finally {
      setDiagnosisLoading(false)
    }
  }

  const handleGenerateReport = async () => {
    setReportLoading(true)
    setReportError(null)
    try {
      const startDate = `${reportYear}-${String(reportMonth).padStart(2, '0')}-01`
      const lastDay = new Date(reportYear, reportMonth, 0).getDate()
      const endDate = `${reportYear}-${String(reportMonth).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`

      const result = await dashboardAPI.generateReport({
        site,
        start_date: startDate,
        end_date: endDate,
        category: category.l2 || category.l1 || undefined,
        report_type: 'monthly'
      })

      if (result.success && result.response.executive_summary) {
        setReportData(result.response)
      } else {
        setReportError(result.response.error || result.response.message || '报告生成失败')
      }
    } catch (err) {
      setReportError(err instanceof Error ? err.message : '未知错误')
    } finally {
      setReportLoading(false)
    }
  }

  const handleDownloadMarkdown = () => {
    if (!reportData?.executive_summary) return

    const summary = reportData.executive_summary
    let markdown = `# 业务月报\n\n`
    markdown += `**站点**: ${site}\n`
    markdown += `**时间范围**: ${reportData.start_date} ~ ${reportData.end_date}\n\n`

    if (summary.overview) markdown += `## 概览\n${summary.overview}\n\n`
    if (summary.key_findings?.length) {
      markdown += `## 关键发现\n${summary.key_findings.map((f: string) => `- ${f}`).join('\n')}\n\n`
    }
    if (summary.trends?.length) {
      markdown += `## 趋势\n${summary.trends.map((t: string) => `- ${t}`).join('\n')}\n\n`
    }
    if (summary.recommendations?.length) {
      markdown += `## 建议\n${summary.recommendations.map((r: string) => `- ${r}`).join('\n')}\n\n`
    }

    const blob = new Blob([markdown], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `report_${site}_${reportData.start_date}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

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
              <button
                onClick={() => setReportModalOpen(true)}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                <FileText className="h-4 w-4" />
                Export Report
              </button>
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
            <AnomalyAlert anomalies={anomalyData.anomalies} onDiagnose={handleDiagnose} />
          </div>
        )}
      </main>

      {/* Diagnosis Modal */}
      {diagnosisOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-white/30 backdrop-blur-sm p-4"
          onClick={() => setDiagnosisOpen(false)}
        >
          <div
            className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[85vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 sticky top-0 bg-white">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">AI 根因诊断</h3>
                {diagnosisContext && (
                  <p className="text-sm text-gray-500 mt-0.5">
                    {diagnosisContext.site} · {diagnosisContext.category} · {diagnosisContext.metric.toUpperCase()}{' '}
                    {diagnosisContext.deviation_percent > 0 ? '+' : ''}
                    {diagnosisContext.deviation_percent.toFixed(1)}% · {diagnosisContext.date}
                  </p>
                )}
              </div>
              <button
                onClick={() => setDiagnosisOpen(false)}
                className="text-gray-400 hover:text-gray-600"
                aria-label="关闭"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="px-6 py-5">
              <DiagnosisReport
                report={diagnosisReport}
                isLoading={diagnosisLoading}
                error={diagnosisError}
              />
            </div>
          </div>
        </div>
      )}

      {/* Report Modal */}
      {reportModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/30 backdrop-blur-sm p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Export Business Report</h2>
                <p className="text-sm text-gray-500 mt-1">生成业务月报</p>
              </div>
              <button
                onClick={() => {
                  setReportModalOpen(false)
                  setReportData(null)
                  setReportError(null)
                }}
                className="text-gray-400 hover:text-gray-600"
                aria-label="关闭"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="px-6 py-5">
              {!reportData ? (
                <div className="space-y-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-sm text-blue-800">
                      <strong>当前筛选条件：</strong> {site} 站点
                      {(category.l2 || category.l1) && ` · ${category.l2 || category.l1}`}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Year</label>
                      <select
                        value={reportYear}
                        onChange={(e) => setReportYear(Number(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      >
                        {[2024, 2025, 2026].map(y => (
                          <option key={y} value={y}>{y}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Month</label>
                      <select
                        value={reportMonth}
                        onChange={(e) => setReportMonth(Number(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      >
                        {Array.from({length: 12}, (_, i) => i + 1).map(m => (
                          <option key={m} value={m}>{m}月</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {reportError && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                      <p className="text-sm text-red-800">{reportError}</p>
                    </div>
                  )}

                  <button
                    onClick={handleGenerateReport}
                    disabled={reportLoading}
                    className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {reportLoading ? (
                      <>
                        <RefreshCw className="h-4 w-4 animate-spin" />
                        生成中...
                      </>
                    ) : (
                      <>
                        <FileText className="h-4 w-4" />
                        生成月报
                      </>
                    )}
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between pb-4 border-b border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900">报告预览</h3>
                    <button
                      onClick={handleDownloadMarkdown}
                      className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                    >
                      <Download className="h-4 w-4" />
                      Download Markdown
                    </button>
                  </div>

                  <ReportView
                    reportType={reportData.report_type}
                    startDate={reportData.start_date}
                    endDate={reportData.end_date}
                    summary={reportData.executive_summary}
                    compact={false}
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      )}

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
