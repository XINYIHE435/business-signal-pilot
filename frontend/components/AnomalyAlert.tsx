/**
 * 异常提示组件
 */

import { AlertCircle, AlertTriangle, Info } from 'lucide-react'
import { Anomaly } from '@/lib/api'

interface AnomalyAlertProps {
  anomalies: Anomaly[]
  /** 点击某条异常时触发诊断（可选） */
  onDiagnose?: (anomaly: Anomaly) => void
}

export function AnomalyAlert({ anomalies, onDiagnose }: AnomalyAlertProps) {
  if (anomalies.length === 0) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-center gap-2">
          <Info className="h-5 w-5 text-green-600" />
          <p className="text-sm text-green-800">No anomalies detected</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Detected Anomalies ({anomalies.length})
      </h3>

      <div className="space-y-3">
        {anomalies.slice(0, 5).map((anomaly, index) => {
          const Icon = anomaly.severity === 'critical' || anomaly.severity === 'high'
            ? AlertCircle
            : AlertTriangle

          const colorClass = {
            critical: 'bg-red-50 border-red-200 text-red-800',
            high: 'bg-orange-50 border-orange-200 text-orange-800',
            medium: 'bg-yellow-50 border-yellow-200 text-yellow-800',
            low: 'bg-blue-50 border-blue-200 text-blue-800',
          }[anomaly.severity]

          const clickable = Boolean(onDiagnose)

          return (
            <div
              key={index}
              onClick={clickable ? () => onDiagnose!(anomaly) : undefined}
              role={clickable ? 'button' : undefined}
              tabIndex={clickable ? 0 : undefined}
              onKeyDown={
                clickable
                  ? (e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        onDiagnose!(anomaly)
                      }
                    }
                  : undefined
              }
              className={`${colorClass} border rounded-lg p-3 ${
                clickable ? 'cursor-pointer hover:shadow-md transition-shadow' : ''
              }`}
            >
              <div className="flex items-start gap-3">
                <Icon className="h-5 w-5 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium">
                      {anomaly.site} - {anomaly.category}
                    </p>
                    <span className="text-xs font-semibold px-2 py-1 bg-white/50 rounded">
                      {anomaly.severity.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm mt-1">
                    {anomaly.metric.toUpperCase()}:
                    <span className="font-semibold ml-1">
                      {anomaly.deviation_percent > 0 ? '+' : ''}
                      {anomaly.deviation_percent.toFixed(1)}%
                    </span>
                  </p>
                  <p className="text-xs mt-1 opacity-75">
                    Expected: {anomaly.expected_value.toFixed(0)} |
                    Actual: {anomaly.actual_value.toFixed(0)} |
                    Date: {anomaly.date}
                  </p>
                  {clickable && (
                    <p className="text-xs mt-2 font-medium opacity-90">
                      点击进行 AI 根因诊断 →
                    </p>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {anomalies.length > 5 && (
        <p className="text-sm text-gray-500 mt-4 text-center">
          + {anomalies.length - 5} more anomalies
        </p>
      )}
    </div>
  )
}
