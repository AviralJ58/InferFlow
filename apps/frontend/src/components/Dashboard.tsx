import { useState, useEffect, useRef, useCallback } from 'react'
import { createChart, ColorType, LineSeries, Time } from 'lightweight-charts'
import { MonitoringClient, MetricSnapshot } from '../api/monitoringClient'

// ── Metric Card ──────────────────────────────────────────────
function MetricCard({ label, value, unit, color = 'primary', subValue }: {
  label: string;
  value: string | number;
  unit?: string;
  color?: 'primary' | 'emerald' | 'amber' | 'rose' | 'cyan' | 'violet';
  subValue?: string;
}) {
  const colorMap: Record<string, string> = {
    primary: 'from-primary-500/20 to-primary-600/5 border-primary-500/20',
    emerald: 'from-emerald-500/20 to-emerald-600/5 border-emerald-500/20',
    amber: 'from-amber-500/20 to-amber-600/5 border-amber-500/20',
    rose: 'from-rose-500/20 to-rose-600/5 border-rose-500/20',
    cyan: 'from-cyan-500/20 to-cyan-600/5 border-cyan-500/20',
    violet: 'from-violet-500/20 to-violet-600/5 border-violet-500/20',
  }
  const textColor: Record<string, string> = {
    primary: 'text-primary-400',
    emerald: 'text-emerald-400',
    amber: 'text-amber-400',
    rose: 'text-rose-400',
    cyan: 'text-cyan-400',
    violet: 'text-violet-400',
  }

  return (
    <div className={`bg-gradient-to-br ${colorMap[color]} border rounded-xl p-4 flex flex-col gap-1`}>
      <span className="text-[11px] uppercase tracking-wider text-surface-400 font-medium">{label}</span>
      <div className="flex items-baseline gap-1.5">
        <span className={`text-2xl font-bold ${textColor[color]} font-mono`}>{value}</span>
        {unit && <span className="text-xs text-surface-500">{unit}</span>}
      </div>
      {subValue && <span className="text-[10px] text-surface-500 font-mono">{subValue}</span>}
    </div>
  )
}

// ── Chart Component ──────────────────────────────────────────
function TimeChart({ title, data, color, yLabel }: {
  title: string;
  data: { time: Time; value: number }[];
  color: string;
  yLabel?: string;
}) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<ReturnType<typeof createChart> | null>(null)
  const seriesRef = useRef<ReturnType<ReturnType<typeof createChart>['addSeries']> | null>(null)

  useEffect(() => {
    if (!chartContainerRef.current) return

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#64748b',
        fontSize: 10,
      },
      grid: {
        vertLines: { color: 'rgba(255,255,255,0.03)' },
        horzLines: { color: 'rgba(255,255,255,0.03)' },
      },
      width: chartContainerRef.current.clientWidth,
      height: 200,
      timeScale: {
        timeVisible: true,
        secondsVisible: true,
        borderColor: 'rgba(255,255,255,0.06)',
      },
      rightPriceScale: {
        borderColor: 'rgba(255,255,255,0.06)',
      },
      crosshair: {
        horzLine: { color: 'rgba(99,102,241,0.3)' },
        vertLine: { color: 'rgba(99,102,241,0.3)' },
      },
    })

    const series = chart.addSeries(LineSeries, {
      color: color,
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: true,
    })

    chartRef.current = chart
    seriesRef.current = series

    const resizeObserver = new ResizeObserver(entries => {
      const { width } = entries[0].contentRect
      chart.applyOptions({ width })
    })
    resizeObserver.observe(chartContainerRef.current)

    return () => {
      resizeObserver.disconnect()
      chart.remove()
    }
  }, [color])

  useEffect(() => {
    if (seriesRef.current && data.length > 0) {
      seriesRef.current.setData(data)
    }
  }, [data])

  return (
    <div className="glass-subtle p-4 rounded-xl">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-surface-200">{title}</h3>
        {yLabel && <span className="text-[10px] text-surface-500">{yLabel}</span>}
      </div>
      <div ref={chartContainerRef} />
    </div>
  )
}

// ── Provider Bar ─────────────────────────────────────────────
function ProviderBar({ stats }: { stats: MetricSnapshot['provider_stats'] }) {
  const total = stats.reduce((sum, s) => sum + s.request_count, 0) || 1
  const colors = ['bg-primary-500', 'bg-emerald-500', 'bg-amber-500', 'bg-cyan-500', 'bg-violet-500', 'bg-rose-500']

  return (
    <div className="glass-subtle p-4 rounded-xl">
      <h3 className="text-sm font-medium text-surface-200 mb-3">Provider Distribution</h3>

      {stats.length === 0 ? (
        <p className="text-xs text-surface-500 italic">No data in window</p>
      ) : (
        <>
          <div className="flex rounded-full overflow-hidden h-3 mb-3">
            {stats.map((s, i) => (
              <div
                key={s.provider}
                className={`${colors[i % colors.length]} transition-all duration-500`}
                style={{ width: `${(s.request_count / total) * 100}%` }}
                title={`${s.provider}: ${s.request_count} requests`}
              />
            ))}
          </div>
          <div className="flex flex-wrap gap-3">
            {stats.map((s, i) => (
              <div key={s.provider} className="flex items-center gap-1.5 text-xs text-surface-300">
                <span className={`w-2 h-2 rounded-full ${colors[i % colors.length]}`} />
                <span className="font-medium">{s.provider}</span>
                <span className="text-surface-500">({s.request_count})</span>
                <span className="text-surface-600">·</span>
                <span className="text-surface-500 font-mono">{s.avg_latency_ms.toFixed(0)}ms</span>
                {s.error_count > 0 && (
                  <span className="text-rose-400 font-mono">{s.error_count} err</span>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

// ── Failures Feed ────────────────────────────────────────────
function FailuresFeed({ failures }: { failures: MetricSnapshot['recent_failures'] }) {
  return (
    <div className="glass-subtle p-4 rounded-xl">
      <h3 className="text-sm font-medium text-surface-200 mb-3">Recent Failures</h3>
      {failures.length === 0 ? (
        <div className="flex items-center gap-2 text-xs text-emerald-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          No recent failures
        </div>
      ) : (
        <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
          {[...failures].reverse().map((f, i) => (
            <div key={i} className="bg-rose-500/5 border border-rose-500/10 rounded-lg p-2.5 text-xs">
              <div className="flex items-center justify-between mb-1">
                <span className="text-rose-400 font-medium">{f.provider} / {f.model}</span>
                <span className="text-surface-500 font-mono text-[10px]">
                  {new Date(f.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <p className="text-surface-400 truncate" title={f.error}>{f.error}</p>
              <span className="text-surface-600 font-mono text-[10px]">{f.request_id.slice(0, 8)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Dashboard ────────────────────────────────────────────────
export default function Dashboard() {
  const [snapshot, setSnapshot] = useState<MetricSnapshot | null>(null)
  const [connected, setConnected] = useState(false)
  const [throughputData, setThroughputData] = useState<{ time: Time; value: number }[]>([])
  const [latencyData, setLatencyData] = useState<{ time: Time; value: number }[]>([])
  const [p95Data, setP95Data] = useState<{ time: Time; value: number }[]>([])

  const handleSnapshot = useCallback((snap: MetricSnapshot) => {
    setSnapshot(snap)
    setConnected(true)

    const now = Math.floor(Date.now() / 1000) as Time
    
    setThroughputData(prev => {
      if (prev.length > 0 && prev[prev.length - 1].time === now) {
        const next = [...prev]
        next[next.length - 1] = { time: now, value: snap.requests_per_sec }
        return next
      }
      return [...prev, { time: now, value: snap.requests_per_sec }].slice(-120)
    })
    
    setLatencyData(prev => {
      if (prev.length > 0 && prev[prev.length - 1].time === now) {
        const next = [...prev]
        next[next.length - 1] = { time: now, value: snap.latency.avg_ms }
        return next
      }
      return [...prev, { time: now, value: snap.latency.avg_ms }].slice(-120)
    })
    
    setP95Data(prev => {
      if (prev.length > 0 && prev[prev.length - 1].time === now) {
        const next = [...prev]
        next[next.length - 1] = { time: now, value: snap.latency.p95_ms }
        return next
      }
      return [...prev, { time: now, value: snap.latency.p95_ms }].slice(-120)
    })
  }, [])

  useEffect(() => {
    // 1. Fetch initial snapshot
    MonitoringClient.fetchSnapshot()
      .then(handleSnapshot)
      .catch(() => console.warn('Monitoring service not available yet'))

    // 2. Subscribe to SSE stream
    const cleanup = MonitoringClient.subscribeToStream(handleSnapshot)
    return cleanup
  }, [handleSnapshot])

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-surface-950">
      {/* Header */}
      <header className="flex-shrink-0 glass border-b border-white/[0.06] px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-violet-600 flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-base font-semibold text-surface-100">InferFlow Monitoring</h1>
              <p className="text-[10px] text-surface-500">
                {snapshot ? `Rolling ${snapshot.window_seconds / 60}min window` : 'Connecting...'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border ${
              connected
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-emerald-400 animate-pulse-slow' : 'bg-amber-400 animate-pulse'}`} />
              {connected ? 'Live' : 'Connecting'}
            </span>
            <a href="/" className="text-xs text-surface-400 hover:text-surface-200 transition-colors">
              ← Chat
            </a>
          </div>
        </div>
      </header>

      {/* Dashboard Content */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-6xl mx-auto space-y-6">

          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <MetricCard
              label="Requests/sec"
              value={snapshot?.requests_per_sec.toFixed(2) ?? '—'}
              color="primary"
              subValue={`${snapshot?.total_requests ?? 0} total`}
            />
            <MetricCard
              label="Active Streams"
              value={snapshot?.active_streams ?? 0}
              color="emerald"
            />
            <MetricCard
              label="Avg Latency"
              value={snapshot?.latency.avg_ms ? (snapshot.latency.avg_ms / 1000).toFixed(2) : '—'}
              unit="s"
              color="cyan"
              subValue={snapshot?.ttft.avg_ms ? `TTFT: ${(snapshot.ttft.avg_ms / 1000).toFixed(2)}s` : undefined}
            />
            <MetricCard
              label="P95 Latency"
              value={snapshot?.latency.p95_ms ? (snapshot.latency.p95_ms / 1000).toFixed(2) : '—'}
              unit="s"
              color="amber"
            />
            <MetricCard
              label="Error Rate"
              value={snapshot ? (snapshot.error_rate * 100).toFixed(1) : '—'}
              unit="%"
              color="rose"
              subValue={`${snapshot?.error_count ?? 0} errors`}
            />
            <MetricCard
              label="Token/sec"
              value={snapshot?.token_throughput_per_sec.toFixed(1) ?? '—'}
              color="violet"
              subValue={`${snapshot?.total_tokens_in_window ?? 0} in window`}
            />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <TimeChart
              title="Request Throughput"
              data={throughputData}
              color="#6366f1"
              yLabel="req/s"
            />
            <TimeChart
              title="Latency"
              data={latencyData}
              color="#06b6d4"
              yLabel="avg ms"
            />
          </div>

          {/* Bottom Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ProviderBar stats={snapshot?.provider_stats ?? []} />
            <FailuresFeed failures={snapshot?.recent_failures ?? []} />
          </div>

          {/* Model Distribution */}
          {snapshot?.model_stats && snapshot.model_stats.length > 0 && (
            <div className="glass-subtle p-4 rounded-xl">
              <h3 className="text-sm font-medium text-surface-200 mb-3">Model Distribution</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                {snapshot.model_stats.map(m => (
                  <div key={m.model} className="bg-white/[0.02] border border-white/[0.04] rounded-lg p-3 text-xs">
                    <div className="font-medium text-surface-200 truncate" title={m.model}>{m.model}</div>
                    <div className="text-surface-500 mt-0.5">{m.provider}</div>
                    <div className="flex justify-between mt-1.5 text-surface-400 font-mono">
                      <span>{m.request_count} req</span>
                      <span>{m.avg_latency_ms.toFixed(0)}ms</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  )
}
