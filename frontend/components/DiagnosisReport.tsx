/**
 * DiagnosisReport - 诊断报告共享组件
 *
 * 同时用于：
 * - Dashboard 异常点击后的 Modal 展示
 * - Chat 对话中诊断结果的内联展示
 */

import { Brain, Target, Lightbulb, GitCompare, AlertTriangle, Loader2 } from 'lucide-react'
import type {
  DiagnosisReport as DiagnosisReportData,
  DiagnosisRootCause,
} from '@/lib/api'

interface DiagnosisReportProps {
  report?: DiagnosisReportData | null
  isLoading?: boolean
  error?: string
  /** 紧凑模式用于 Chat 内联，默认 false（Modal 完整模式） */
  compact?: boolean
}

const HYPOTHESIS_COLORS: Record<string, string> = {
  traffic: 'bg-blue-100 text-blue-700',
  campaign: 'bg-purple-100 text-purple-700',
  seller: 'bg-amber-100 text-amber-700',
  inventory: 'bg-teal-100 text-teal-700',
  holiday: 'bg-pink-100 text-pink-700',
  policy: 'bg-indigo-100 text-indigo-700',
  competition: 'bg-red-100 text-red-700',
}

function confidenceBar(confidence: number) {
  const pct = Math.round((confidence || 0) * 100)
  const color = pct >= 70 ? 'bg-green-500' : pct >= 40 ? 'bg-yellow-500' : 'bg-gray-400'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-500 w-9 text-right">{pct}%</span>
    </div>
  )
}

function RootCauseItem({ rc }: { rc: DiagnosisRootCause }) {
  const badge = HYPOTHESIS_COLORS[rc.hypothesis_type || ''] || 'bg-gray-100 text-gray-700'
  return (
    <div className="border border-gray-200 rounded-lg p-3">
      <div className="flex items-start justify-between gap-2 mb-2">
        <p className="text-sm font-medium text-gray-900">{rc.cause}</p>
        {rc.hypothesis_type && (
          <span className={`text-xs px-2 py-0.5 rounded-full whitespace-nowrap ${badge}`}>
            {rc.hypothesis_type}
          </span>
        )}
      </div>
      {confidenceBar(rc.confidence)}
      {rc.evidence && (
        <p className="text-xs text-gray-600 mt-2 leading-relaxed">
          <span className="font-medium text-gray-500">证据：</span>
          {rc.evidence}
        </p>
      )}
      {typeof rc.contribution === 'number' && (
        <p className="text-xs text-gray-500 mt-1">
          贡献度：{Math.round(rc.contribution * 100)}%
        </p>
      )}
    </div>
  )
}

export function DiagnosisReport({ report, isLoading, error, compact = false }: DiagnosisReportProps) {
  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-gray-500 py-6 justify-center">
        <Loader2 className="h-5 w-5 animate-spin" />
        <span className="text-sm">正在诊断分析...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 text-red-600 py-4">
        <AlertTriangle className="h-5 w-5" />
        <span className="text-sm">诊断失败：{error}</span>
      </div>
    )
  }

  if (!report) return null

  if (!report.success && report.error) {
    return (
      <div className="flex items-center gap-2 text-red-600 py-4">
        <AlertTriangle className="h-5 w-5" />
        <span className="text-sm">{report.summary || report.error}</span>
      </div>
    )
  }

  return (
    <div className={compact ? 'space-y-4' : 'space-y-6'}>
      {/* Summary */}
      <div>
        <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 mb-2">
          <Brain className="h-4 w-4 text-blue-600" />
          诊断结论
          <span className="text-xs font-normal text-gray-400 ml-1">
            {report.analysis_mode === 'comparison' ? '对比分析' : '根因分析'}
          </span>
        </div>
        <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
          {report.summary}
        </p>
      </div>

      {/* Comparison block */}
      {report.analysis_mode === 'comparison' && report.comparison && (
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 mb-2">
            <GitCompare className="h-4 w-4 text-indigo-600" />
            对比：{report.comparison.site_a} vs {report.comparison.site_b}
          </div>
          {report.comparison.winner && (
            <p className="text-sm text-gray-700 mb-2">
              <span className="font-medium">结论：</span>
              {report.comparison.winner}
            </p>
          )}
          {report.comparison.key_differences && report.comparison.key_differences.length > 0 && (
            <ul className="list-disc list-inside space-y-1">
              {report.comparison.key_differences.map((d, i) => (
                <li key={i} className="text-xs text-gray-600">{d}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Root causes */}
      {report.root_causes && report.root_causes.length > 0 && (
        <div>
          <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 mb-3">
            <Target className="h-4 w-4 text-red-600" />
            {report.analysis_mode === 'comparison' ? '关键驱动因素' : '根因排序'}
            <span className="text-xs font-normal text-gray-400">
              ({report.root_causes.length})
            </span>
          </div>
          <div className="space-y-2">
            {report.root_causes.map((rc, i) => (
              <RootCauseItem key={i} rc={rc} />
            ))}
          </div>
        </div>
      )}

      {/* Contributions */}
      {report.contributions && report.contributions.length > 0 && (
        <div>
          <div className="text-sm font-semibold text-gray-900 mb-2">贡献度拆解</div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">维度</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">取值</th>
                  <th className="px-3 py-2 text-right font-medium text-gray-700">贡献 %</th>
                  <th className="px-3 py-2 text-right font-medium text-gray-700">变化</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {report.contributions.map((c, i) => (
                  <tr key={i}>
                    <td className="px-3 py-2 text-gray-900">{c.dimension}</td>
                    <td className="px-3 py-2 text-gray-900">{c.value}</td>
                    <td className="px-3 py-2 text-right text-gray-900">
                      {c.contribution_percent?.toFixed(1)}%
                    </td>
                    <td className="px-3 py-2 text-right text-gray-500">
                      {typeof c.change === 'number' ? `${c.change > 0 ? '+' : ''}${c.change.toFixed(1)}%` : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Recommended actions */}
      {report.recommended_actions && report.recommended_actions.length > 0 && (
        <div>
          <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 mb-2">
            <Lightbulb className="h-4 w-4 text-amber-500" />
            建议行动
          </div>
          <ol className="space-y-1.5">
            {report.recommended_actions.map((action, i) => (
              <li key={i} className="flex gap-2 text-sm text-gray-700">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 text-blue-700 text-xs flex items-center justify-center font-medium">
                  {i + 1}
                </span>
                <span className="leading-relaxed">{action}</span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  )
}
