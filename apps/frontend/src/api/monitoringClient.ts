/**
 * Monitoring API client.
 *
 * Provides SSE subscription for live metric updates and
 * a one-shot snapshot fetch for initial page load.
 */

// --- TypeScript interfaces matching backend models ---

export interface LatencyMetrics {
  avg_ms: number;
  p50_ms: number;
  p95_ms: number;
  p99_ms: number;
  min_ms: number;
  max_ms: number;
}

export interface ProviderStats {
  provider: string;
  request_count: number;
  avg_latency_ms: number;
  error_count: number;
  error_rate: number;
}

export interface ModelStats {
  model: string;
  provider: string;
  request_count: number;
  avg_latency_ms: number;
}

export interface RecentFailure {
  timestamp: string;
  request_id: string;
  conversation_id: string;
  provider: string;
  model: string;
  error: string;
}

export interface MetricSnapshot {
  timestamp: string;
  window_seconds: number;
  requests_per_sec: number;
  total_requests: number;
  active_streams: number;
  latency: LatencyMetrics;
  ttft: LatencyMetrics;
  token_throughput_per_sec: number;
  total_tokens_in_window: number;
  error_rate: number;
  error_count: number;
  provider_stats: ProviderStats[];
  model_stats: ModelStats[];
  recent_failures: RecentFailure[];
}

const MONITORING_BASE = '/monitoring/api/monitoring';

export const MonitoringClient = {
  /**
   * Fetch a one-shot metric snapshot (for initial load).
   */
  async fetchSnapshot(): Promise<MetricSnapshot> {
    const res = await fetch(`${MONITORING_BASE}/snapshot`);
    if (!res.ok) throw new Error('Failed to fetch monitoring snapshot');
    return res.json();
  },

  /**
   * Subscribe to the SSE metric stream.
   * Returns a cleanup function to close the connection.
   */
  subscribeToStream(onData: (snapshot: MetricSnapshot) => void): () => void {
    const eventSource = new EventSource(`${MONITORING_BASE}/stream`);

    eventSource.addEventListener('metrics', (event: MessageEvent) => {
      try {
        const snapshot: MetricSnapshot = JSON.parse(event.data);
        onData(snapshot);
      } catch (e) {
        console.error('Error parsing monitoring event', e);
      }
    });

    eventSource.onerror = () => {
      console.warn('Monitoring SSE connection error, will auto-reconnect...');
    };

    return () => {
      eventSource.close();
    };
  },
};
