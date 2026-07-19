/**
 * SignalPilot Chat - Agent 对话界面
 *
 * 与 AI Agent 进行业务数据查询对话
 */

'use client'

import { useState, useRef, useEffect } from 'react'
import { chatAPI, exportAPI, type Message, type ChatQueryResponse, type DiagnosisReport as DiagnosisReportData, type ExecutiveSummary } from '@/lib/api'
import { DiagnosisReport } from '@/components/DiagnosisReport'
import { ReportView } from '@/components/ReportView'
import { Send, Bot, User, Loader2, AlertCircle, Database, Brain, CheckCircle, Download, FileText } from 'lucide-react'

interface ChatMessage extends Message {
  response?: ChatQueryResponse
  isLoading?: boolean
  error?: string
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [exportingIndex, setExportingIndex] = useState<number | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 导出查询结果
  const handleExportQueryResult = async (data: Array<Record<string, any>>, format: 'csv' | 'markdown', messageIndex: number) => {
    setExportingIndex(messageIndex)
    try {
      const { blob, filename } = await exportAPI.exportQueryResult({ data, format })

      // 触发下载
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      alert(`导出失败: ${error instanceof Error ? error.message : '未知错误'}`)
    } finally {
      setExportingIndex(null)
    }
  }

  // 导出诊断报告
  const handleExportDiagnosis = async (diagnosis: DiagnosisReportData, format: 'markdown' | 'pdf', messageIndex: number) => {
    setExportingIndex(messageIndex)
    try {
      const { blob, filename } = await exportAPI.exportDiagnosis({
        diagnosis_report: diagnosis as any,
        format
      })

      // 触发下载
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      alert(`导出失败: ${error instanceof Error ? error.message : '未知错误'}`)
    } finally {
      setExportingIndex(null)
    }
  }

  // 导出业务报告
  const handleExportReport = async (response: ChatQueryResponse, format: 'markdown' | 'pdf', messageIndex: number) => {
    setExportingIndex(messageIndex)
    try {
      const r = response.response
      const report_content = {
        report_type: r.report_type || 'weekly',
        start_date: r.start_date || '',
        end_date: r.end_date || '',
        executive_summary: r.executive_summary || {},
        generated_at: r.generated_at || '',
        data_sources: r.data_sources || {},
      }
      const { blob, filename } = await exportAPI.exportReport({ report_content, format })

      // 触发下载
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      alert(`导出失败: ${error instanceof Error ? error.message : '未知错误'}`)
    } finally {
      setExportingIndex(null)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: ChatMessage = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    const loadingMessage: ChatMessage = {
      role: 'assistant',
      content: '',
      isLoading: true,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, loadingMessage])

    try {
      const response = await chatAPI.query({
        query: userMessage.content,
        session_id: 'web-session',
        conversation_history: messages.filter(m => !m.isLoading && !m.error).slice(-5)
      })

      setMessages(prev => {
        const newMessages = [...prev]
        newMessages[newMessages.length - 1] = {
          role: 'assistant',
          content: formatResponse(response),
          response,
          timestamp: response.timestamp
        }
        return newMessages
      })
    } catch (error) {
      setMessages(prev => {
        const newMessages = [...prev]
        newMessages[newMessages.length - 1] = {
          role: 'assistant',
          content: '抱歉，查询失败。请稍后重试。',
          error: error instanceof Error ? error.message : '未知错误',
          timestamp: new Date().toISOString()
        }
        return newMessages
      })
    } finally {
      setIsLoading(false)
    }
  }

  const formatResponse = (response: ChatQueryResponse): string => {
    const { response: responseData } = response
    const data = responseData as Record<string, unknown>

    // 诊断类响应：正文由 DiagnosisReport 组件渲染，这里给一句引导语
    if (data.type === 'diagnosis') {
      if (!responseData.success) {
        return `诊断失败：${(data.error as string) || '未知错误'}`
      }
      return (data.summary as string) || '诊断完成。'
    }

    // 报告类响应：正文由 ReportView 组件渲染，这里给一句引导语
    if (data.type === 'report') {
      if (!responseData.success) {
        return `报告生成失败：${(data.error as string) || '未知错误'}`
      }
      const label = data.report_type === 'monthly' ? '月报' : data.report_type === 'quarterly' ? '季报' : '周报'
      return `已为你生成业务${label}，详见下方 Executive Summary。`
    }

    // 参数缺失：Parameter Validation 暂停 Workflow，向用户追问缺失的报告参数
    if (data.type === 'clarification_needed') {
      return (data.question as string) || '请补充生成报告所需的参数。'
    }

    if (!responseData.success) {
      return `查询失败：${responseData.error || '未知错误'}`
    }

    let text = ''

    if (responseData.data && responseData.data.length > 0) {
      const rowCount = responseData.row_count || responseData.data.length
      text += `找到 ${rowCount} 条数据。`
    }

    if (responseData.explanation) {
      text += `\n\n${responseData.explanation}`
    }

    return text || '查询完成。'
  }

  /** 从 chat 响应中提取诊断报告（若为诊断类响应） */
  const extractDiagnosis = (response?: ChatQueryResponse): DiagnosisReportData | null => {
    if (!response) return null
    const data = response.response as Record<string, unknown>
    if (data.type !== 'diagnosis') return null
    return {
      success: Boolean(data.success),
      analysis_mode: (data.analysis_mode as 'root_cause' | 'comparison') || 'root_cause',
      summary: (data.summary as string) || '',
      hypotheses: (data.hypotheses as DiagnosisReportData['hypotheses']) || [],
      root_causes: (data.root_causes as DiagnosisReportData['root_causes']) || [],
      contributions: (data.contributions as DiagnosisReportData['contributions']) || [],
      recommended_actions: (data.recommended_actions as string[]) || [],
      comparison: (data.comparison as DiagnosisReportData['comparison']) ?? null,
      error: data.error as string | undefined,
    }
  }

  /** 从 chat 响应中提取业务报告（若为报告类响应且成功） */
  const extractReport = (response?: ChatQueryResponse): ExecutiveSummary | null => {
    if (!response) return null
    const data = response.response as Record<string, unknown>
    if (data.type !== 'report' || !data.success) return null
    const summary = data.executive_summary as ExecutiveSummary | undefined
    if (!summary || Object.keys(summary).length === 0) return null
    return summary
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Bot className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">AI Agent</h1>
                <p className="text-sm text-gray-500">问我任何业务数据问题</p>
              </div>
            </div>
            <a
              href="/"
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              返回看板
            </a>
          </div>
        </div>
      </header>

      {/* Messages */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <Bot className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-gray-900 mb-2">开始对话</h2>
              <p className="text-gray-500 mb-6">
                尝试问我：
              </p>
              <div className="space-y-2 max-w-md mx-auto text-left">
                <button
                  onClick={() => setInput('查询德国站GMV')}
                  className="w-full text-left px-4 py-3 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
                >
                  <span className="text-sm text-gray-700">💰 查询德国站GMV</span>
                </button>
                <button
                  onClick={() => setInput('过去7天德国站的GMV是多少？')}
                  className="w-full text-left px-4 py-3 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
                >
                  <span className="text-sm text-gray-700">📊 过去7天德国站的GMV是多少？</span>
                </button>
                <button
                  onClick={() => setInput('为什么德国站GMV下降了？')}
                  className="w-full text-left px-4 py-3 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
                >
                  <span className="text-sm text-gray-700">🔍 为什么德国站GMV下降了？</span>
                </button>
              </div>
            </div>
          )}

          <div className="space-y-6">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.role === 'assistant' && (
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                      <Bot className="h-5 w-5 text-blue-600" />
                    </div>
                  </div>
                )}

                <div
                  className={`max-w-3xl ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white border border-gray-200'
                  } rounded-lg px-4 py-3 shadow-sm`}
                >
                  {message.isLoading ? (
                    <div className="flex items-center gap-2 text-gray-500">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm">思考中...</span>
                    </div>
                  ) : message.error ? (
                    <div>
                      <div className="flex items-center gap-2 text-red-600 mb-2">
                        <AlertCircle className="h-4 w-4" />
                        <span className="font-medium">查询失败</span>
                      </div>
                      <p className="text-sm text-gray-700">{message.content}</p>
                      <p className="text-xs text-gray-500 mt-2">{message.error}</p>
                    </div>
                  ) : (
                    <div>
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>

                      {message.response && (
                        <div className="mt-4 pt-4 border-t border-gray-100">
                          {/* Intent & Entities */}
                          <div className="flex items-center gap-2 text-xs text-gray-500 mb-3">
                            <Brain className="h-3 w-3" />
                            <span>意图: {message.response.intent}</span>
                            {Object.keys(message.response.entities).length > 0 && (
                              <span className="ml-2">
                                实体: {JSON.stringify(message.response.entities)}
                              </span>
                            )}
                          </div>

                          {/* Diagnosis Report（根因/对比分析） */}
                          {extractDiagnosis(message.response) && (
                            <div className="mb-3">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-xs font-medium text-gray-700">诊断报告</span>
                                <div className="flex gap-1">
                                  <button
                                    onClick={() => handleExportDiagnosis(extractDiagnosis(message.response)!, 'markdown', index)}
                                    disabled={exportingIndex === index}
                                    className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded flex items-center gap-1 disabled:opacity-50"
                                  >
                                    {exportingIndex === index ? (
                                      <Loader2 className="h-3 w-3 animate-spin" />
                                    ) : (
                                      <Download className="h-3 w-3" />
                                    )}
                                    Markdown
                                  </button>
                                  <button
                                    onClick={() => handleExportDiagnosis(extractDiagnosis(message.response)!, 'pdf', index)}
                                    disabled={exportingIndex === index}
                                    className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded flex items-center gap-1 disabled:opacity-50"
                                  >
                                    {exportingIndex === index ? (
                                      <Loader2 className="h-3 w-3 animate-spin" />
                                    ) : (
                                      <Download className="h-3 w-3" />
                                    )}
                                    PDF
                                  </button>
                                </div>
                              </div>
                              <DiagnosisReport report={extractDiagnosis(message.response)} compact />
                            </div>
                          )}

                          {/* Report（业务周报/月报 Executive Summary） */}
                          {extractReport(message.response) && (
                            <div className="mb-3">
                              <div className="flex items-center justify-between mb-2">
                                <span className="flex items-center gap-1 text-xs font-medium text-gray-700">
                                  <FileText className="h-3 w-3" />
                                  业务报告
                                </span>
                                <div className="flex gap-1">
                                  <button
                                    onClick={() => handleExportReport(message.response!, 'markdown', index)}
                                    disabled={exportingIndex === index}
                                    className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded flex items-center gap-1 disabled:opacity-50"
                                  >
                                    {exportingIndex === index ? (
                                      <Loader2 className="h-3 w-3 animate-spin" />
                                    ) : (
                                      <Download className="h-3 w-3" />
                                    )}
                                    Markdown
                                  </button>
                                  <button
                                    onClick={() => handleExportReport(message.response!, 'pdf', index)}
                                    disabled={exportingIndex === index}
                                    className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded flex items-center gap-1 disabled:opacity-50"
                                  >
                                    {exportingIndex === index ? (
                                      <Loader2 className="h-3 w-3 animate-spin" />
                                    ) : (
                                      <Download className="h-3 w-3" />
                                    )}
                                    PDF
                                  </button>
                                </div>
                              </div>
                              <ReportView
                                summary={extractReport(message.response)}
                                reportType={message.response.response.report_type}
                                startDate={message.response.response.start_date}
                                endDate={message.response.response.end_date}
                                compact
                              />
                            </div>
                          )}

                          {/* SQL */}
                          {message.response.response.sql && (
                            <div className="mb-3">
                              <div className="flex items-center gap-2 text-xs font-medium text-gray-700 mb-1">
                                <Database className="h-3 w-3" />
                                生成的 SQL
                              </div>
                              <pre className="bg-gray-50 rounded p-2 text-xs overflow-x-auto">
                                <code>{message.response.response.sql}</code>
                              </pre>
                            </div>
                          )}

                          {/* Data */}
                          {message.response.response.data && message.response.response.data.length > 0 && (
                            <div>
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2 text-xs font-medium text-gray-700">
                                  <CheckCircle className="h-3 w-3" />
                                  查询结果 ({message.response.response.row_count || message.response.response.data.length} 行)
                                </div>
                                <div className="flex gap-1">
                                  <button
                                    onClick={() => handleExportQueryResult(message.response!.response.data!, 'csv', index)}
                                    disabled={exportingIndex === index}
                                    className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded flex items-center gap-1 disabled:opacity-50"
                                  >
                                    {exportingIndex === index ? (
                                      <Loader2 className="h-3 w-3 animate-spin" />
                                    ) : (
                                      <Download className="h-3 w-3" />
                                    )}
                                    CSV
                                  </button>
                                  <button
                                    onClick={() => handleExportQueryResult(message.response!.response.data!, 'markdown', index)}
                                    disabled={exportingIndex === index}
                                    className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded flex items-center gap-1 disabled:opacity-50"
                                  >
                                    {exportingIndex === index ? (
                                      <Loader2 className="h-3 w-3 animate-spin" />
                                    ) : (
                                      <Download className="h-3 w-3" />
                                    )}
                                    Markdown
                                  </button>
                                </div>
                              </div>
                              <div className="overflow-x-auto">
                                <table className="min-w-full text-xs">
                                  <thead className="bg-gray-50">
                                    <tr>
                                      {Object.keys(message.response.response.data[0]).map(key => (
                                        <th key={key} className="px-3 py-2 text-left font-medium text-gray-700">
                                          {key}
                                        </th>
                                      ))}
                                    </tr>
                                  </thead>
                                  <tbody className="divide-y divide-gray-100">
                                    {message.response.response.data.slice(0, 5).map((row, i) => (
                                      <tr key={i}>
                                        {Object.values(row).map((val, j) => (
                                          <td key={j} className="px-3 py-2 text-gray-900">
                                            {typeof val === 'number' ? val.toLocaleString() : String(val)}
                                          </td>
                                        ))}
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                              {message.response.response.data.length > 5 && (
                                <p className="text-xs text-gray-500 mt-2">
                                  显示前 5 行，共 {message.response.response.data.length} 行
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {message.role === 'user' && (
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                      <User className="h-5 w-5 text-gray-600" />
                    </div>
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>
      </main>

      {/* Input */}
      <footer className="bg-white border-t border-gray-200 sticky bottom-0">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="输入你的问题..."
              disabled={isLoading}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
              发送
            </button>
          </form>
        </div>
      </footer>
    </div>
  )
}
