/**
 * ReportView - 业务报告（Executive Summary）共享组件
 *
 * 同时用于：
 * - Chat 对话中报告生成结果的内联展示
 * - Dashboard 报告导出预览
 */

import {
  FileText,
  TrendingUp,
  TrendingDown,
  Minus,
  Search,
  Target,
  Lightbulb,
  CalendarClock,
  AlertTriangle,
  Loader2,
} from 'lucide-react'
import type { ExecutiveSummary, ReportKPIItem, ReportAction } from '@/lib/api'

interface ReportViewProps {
  summary?: ExecutiveSummary | null
  reportType?: string
  startDate?: string
  endDate?: string
  isLoading?: boolean
  error?: string
  /** 紧凑模式用于 Chat 内联，默认 false */
  compact?: boolean
}

const PRIORITY_COLORS: Record<string, string> = {
  高: 'bg-red-100 text-red-700',
  中: 'bg-amber-100 text-amber-700',
  低: 'bg-gray-100 text-gray-600',
}

function TrendIcon({ trend }: { trend: ReportKPIItem['trend'] }) {
  if (trend === '上升') return <TrendingUp className="h-4 w-4 text-green-600" />
  if (trend === '下降') return <TrendingDown className="h-4 w-4 text-red-600" />
  return <Minus className="h-4 w-4 text-gray-400" />
}

function ActionItem({ action, index }: { action: ReportAction; index: number }) {
  const badge = PRIORITY_COLORS[action.priority] || 'bg-gray-100 text-gray-600'
  return (
    <li className="flex gap-2 text-sm text-gray-700">
      <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 text-blue-700 text-xs flex items-center justify-center font-medium">
        {index + 1}
      </span>
      <div className="flex-1">
        <div className="flex items-start justify-between gap-2">
          <span className="leading-relaxed">{action.action}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full whitespace-nowrap ${badge}`}>
            {action.priority}
          </span>
        </div>
        {action.expected_impact && (
          <p className="text-xs text-gray-500 mt-1">预期影响：{action.expected_impact}</p>
        )}
      </div>
    </li>
  )
}

export function ReportView({
  summary,
  reportType,
  startDate,
  endDate,
  isLoading,
  error,
  compact = false,
}: ReportViewProps) {
  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-gray-500 py-6 justify-center">
        <Loader2 className="h-5 w-5 animate-spin" />
        <span className="text-sm">正在生成业务报告...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 text-red-600 py-4">
        <AlertTriangle className="h-5 w-5" />
        <span className="text-sm">报告生成失败：{error}</span>
      </div>
    )
  }

  if (!summary) return null

  const reportLabel = reportType === 'monthly' ? '月报' : reportType === 'quarterly' ? '季报' : reportType === 'weekly' ? '周报' : '报告'

  return (
    <div className={compact ? 'space-y-4' : 'space-y-6'}>
      {/* 标题与时间范围 */}
      <div>
        <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 mb-1">
          <FileText className="h-4 w-4 text-blue-600" />
          业务{reportLabel} · Executive Summary
        </div>
        {(startDate || endDate) && (
          <p className="text-xs text-gray-400">
            报告周期：{startDate || '?'} 至 {endDate || '?'}
          </p>
        )}
      </div>

      {/* 1. 整体业务表现 */}
      {summary.overall_business_performance && (
        <div>
          <div className="text-sm font-semibold text-gray-900 mb-2">整体业务表现</div>
          <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
            {summary.overall_business_performance}
          </p>
        </div>
      )}

      {/* 2. 关键指标汇总 */}
      {summary.kpi_summary && summary.kpi_summary.length > 0 && (
        <div>
          <div className="text-sm font-semibold text-gray-900 mb-2">关键指标汇总</div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">指标</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">当前值</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">趋势</th>
                  <th className="px-3 py-2 text-right font-medium text-gray-700">变化</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {summary.kpi_summary.map((kpi, i) => (
                  <tr key={i}>
                    <td className="px-3 py-2 text-gray-900">{kpi.metric_name}</td>
                    <td className="px-3 py-2 text-gray-900">{kpi.current_value}</td>
                    <td className="px-3 py-2">
                      <span className="inline-flex items-center gap-1 text-gray-700">
                        <TrendIcon trend={kpi.trend} />
                        {kpi.trend}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-right text-gray-500">
                      {kpi.change_percentage || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 3. 关键发现 */}
      {summary.key_findings && summary.key_findings.length > 0 && (
        <div>
          <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 mb-2">
            <Search className="h-4 w-4 text-blue-600" />
            关键发现
          </div>
          <ul className="list-disc list-inside space-y-1">
            {summary.key_findings.map((finding, i) => (
              <li key={i} className="text-sm text-gray-700 leading-relaxed">{finding}</li>
            ))}
          </ul>
        </div>
      )}

      {/* 4. 根本原因分析 */}
      {summary.root_causes && summary.root_causes.length > 0 && (
        <div>
          <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 mb-2">
            <Target className="h-4 w-4 text-red-600" />
            根本原因分析
          </div>
          <div className="space-y-2">
            {summary.root_causes.map((rc, i) => (
              <div key={i} className="border border-gray-200 rounded-lg p-3">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <p className="text-sm font-medium text-gray-900">{rc.cause}</p>
                  <span className="text-xs px-2 py-0.5 rounded-full whitespace-nowrap bg-gray-100 text-gray-600">
                    置信度 {rc.confidence}
                  </span>
                </div>
                {rc.evidence && (
                  <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                    <span className="font-medium text-gray-500">证据：</span>
                    {rc.evidence}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 5. 推荐行动 */}
      {summary.recommended_actions && summary.recommended_actions.length > 0 && (
        <div>
          <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 mb-2">
            <Lightbulb className="h-4 w-4 text-amber-500" />
            推荐行动
          </div>
          <ol className="space-y-2">
            {summary.recommended_actions.map((action, i) => (
              <ActionItem key={i} action={action} index={i} />
            ))}
          </ol>
        </div>
      )}

      {/* 6. 下周重点关注 */}
      {summary.next_week_focus && summary.next_week_focus.length > 0 && (
        <div>
          <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 mb-2">
            <CalendarClock className="h-4 w-4 text-indigo-600" />
            下周重点关注
          </div>
          <ul className="list-disc list-inside space-y-1">
            {summary.next_week_focus.map((focus, i) => (
              <li key={i} className="text-sm text-gray-700 leading-relaxed">{focus}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
