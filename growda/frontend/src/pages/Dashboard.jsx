import React, { useEffect, useMemo, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import apiService from "../services/api";
import Loader from "../components/Loader";
import Toast from "../components/Toast";

const STATUS_POLL_INTERVAL = 30000;

export default function Dashboard() {
  const [status, setStatus] = useState({
    round: 0,
    total_rounds: 3,
    connected_clients: 0,
    global_accuracy: 0,
    in_progress: false,
    last_update: null,
  });
  const [metricsHistory, setMetricsHistory] = useState([]);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [toast, setToast] = useState(null);
  const [triggering, setTriggering] = useState(false);

  const fetchStatus = async () => {
    try {
      const data = await apiService.getStatus();
      setStatus((prev) => ({ ...prev, ...data }));
    } catch (error) {
      setToast({ message: "Unable to load training status", type: "error" });
    } finally {
      setLoadingStatus(false);
    }
  };

  const fetchHistory = async () => {
    try {
      const history = await apiService.getMetricsHistory();
      setMetricsHistory(history);
    } catch (error) {
      setToast({ message: "Unable to load metrics history", type: "error" });
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, STATUS_POLL_INTERVAL);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    fetchHistory();
    const interval = setInterval(fetchHistory, STATUS_POLL_INTERVAL * 2);
    return () => clearInterval(interval);
  }, []);

  const handleTrainRound = async () => {
    setTriggering(true);
    try {
      const nextStatus = await apiService.triggerTrainingRound();
      setStatus((prev) => ({ ...prev, ...nextStatus }));
      setToast({ message: "Training round started", type: "success" });
    } catch (error) {
      const errMsg = error?.response?.data?.error || "Failed to start training round";
      setToast({ message: errMsg, type: "error" });
    } finally {
      setTriggering(false);
    }
  };

  const latestRound = metricsHistory[metricsHistory.length - 1];
  const latestClients = latestRound?.clients ?? [];
  const recentAccuracy = useMemo(() => {
    if (!metricsHistory.length) return [];
    return metricsHistory.slice(-6).map((item) => ({
      round: item.round,
      accuracy: typeof item.accuracy === "number" ? item.accuracy : 0,
    }));
  }, [metricsHistory]);

  return (
    <div className="max-w-5xl mx-auto pt-32 px-4 pb-24 fadein font-sans">
      {toast && <Toast {...toast} onClose={() => setToast(null)} />}
      <div className="flex flex-col gap-2 mb-8">
        <p className="uppercase text-xs tracking-[0.4em] text-blue-500 font-bold">Growda Control</p>
        <h2 className="text-4xl sm:text-5xl font-extrabold text-blue-900 tracking-tight">Federated Learning Dashboard</h2>
        <p className="text-lg text-blue-900/80">
          Monitor cross-hospital training, trigger new rounds, and inspect client metrics in real time.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <MetricCard label="Round" value={status.round} note="" />
        <MetricCard
          label="Global Accuracy"
          value={(status.global_accuracy ?? 0).toFixed(2)}
          note=""
          highlight
        />
        <MetricCard label="Hospitals (Last Round)" value={status.connected_clients} note="" />
      </div>

      <div className="glass mb-8 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-2xl font-bold text-blue-900">Training Progress</h3>
            <p className="text-sm text-blue-900/70">Accuracy trend across federated learning rounds</p>
          </div>
          <span className="text-xs text-blue-500">Updated: {status.last_update ? new Date(parseFloat(status.last_update) * 1000).toLocaleTimeString() : "—"}</span>
        </div>
        {loadingHistory ? (
          <Loader label="Loading metrics..." />
        ) : recentAccuracy.length ? (
          <>
            <EnhancedAccuracyChart data={metricsHistory} />
            <MetricsSummary data={metricsHistory} />
          </>
        ) : (
          <div className="rounded-xl p-4 text-center text-blue-400 bg-blue-50">
            No training history yet. Training will populate metrics automatically.
          </div>
        )}
      </div>

      <div className="glass mb-10 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-2xl font-bold text-blue-900">Latest Round Details</h3>
            <p className="text-sm text-blue-900/70">Client-level accuracy summaries</p>
          </div>
          {latestRound ? (
            <span className="text-sm font-semibold text-blue-600">Round {latestRound.round}</span>
          ) : null}
        </div>
        {loadingHistory ? (
          <Loader label="Loading clients..." />
        ) : latestRound ? (
          <div className="space-y-3">
            {latestClients.length ? (
              latestClients.map((client) => (
                <div key={client.client} className="flex items-center justify-between bg-blue-50/60 rounded-xl px-4 py-3">
                  <div className="text-blue-900 font-semibold">{client.client}</div>
                  <div className="text-sm text-blue-600 font-mono">
                    {typeof client.accuracy === "number" ? `${(client.accuracy * 100).toFixed(1)}%` : "—"}
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-xl p-4 text-center text-blue-400 bg-blue-50">
                Awaiting client metrics for this round.
              </div>
            )}
          </div>
        ) : (
          <div className="rounded-xl p-4 text-center text-blue-400 bg-blue-50">
            Trigger a round to view per-client metrics.
          </div>
        )}
      </div>

      <div className="glass p-6">
        <h3 className="text-2xl font-bold text-blue-900 mb-3">System Status</h3>
        {loadingStatus ? (
          <Loader label="Checking server..." />
        ) : (
          <ul className="space-y-2 text-sm text-blue-900/70">
            <li><strong>Training:</strong> {status.in_progress ? 'Running' : 'Idle'}</li>
            <li><strong>Last update:</strong> {status.last_update ? new Date(parseFloat(status.last_update) * 1000).toLocaleString() : '—'}</li>
            <li><strong>Global model:</strong> {status.global_accuracy ? `${status.global_accuracy.toFixed(2)} accuracy` : 'Not evaluated yet'}</li>
            <li><strong>Server mode:</strong> Continuous (auto-starts when clients connect)</li>
          </ul>
        )}
      </div>
    </div>
  );
}

function MetricCard({ label, value, note, highlight }) {
  return (
    <div className="glass py-6 px-4 text-center">
      <h4 className="text-sm mb-2 font-bold uppercase text-blue-500 tracking-wide">{label}</h4>
      <div className={`text-3xl font-black ${highlight ? 'text-blue-700' : 'text-blue-900'} mb-0 font-sans`}>
        {value}<span className="text-blue-400 text-xl font-bold align-super">{note}</span>
      </div>
    </div>
  );
}

function EnhancedAccuracyChart({ data }) {
  const chartData = data.map((item) => ({
    round: item.round,
    accuracy: typeof item.accuracy === 'number' ? (item.accuracy * 100).toFixed(2) : 0,
  }));

  return (
    <div className="h-64 mb-6">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#FED7AA" />
          <XAxis
            dataKey="round"
            label={{ value: 'Round', position: 'insideBottom', offset: -5 }}
            stroke="#92400E"
          />
          <YAxis
            label={{ value: 'Accuracy (%)', angle: -90, position: 'insideLeft' }}
            stroke="#92400E"
            domain={[0, 100]}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#FEF3C7',
              border: '2px solid #92400E',
              borderRadius: '8px',
              padding: '8px 12px'
            }}
            formatter={(value) => [`${value}%`, 'Accuracy']}
            labelFormatter={(label) => `Round ${label}`}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="accuracy"
            stroke="#92400E"
            strokeWidth={3}
            dot={{ fill: '#78350F', r: 5 }}
            activeDot={{ r: 7 }}
            name="Global Accuracy"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function MetricsSummary({ data }) {
  if (!data || data.length === 0) return null;

  const accuracies = data.map(item => typeof item.accuracy === 'number' ? item.accuracy : 0);
  const totalRounds = data.length;
  const avgAccuracy = accuracies.reduce((sum, acc) => sum + acc, 0) / totalRounds;
  const bestAccuracy = Math.max(...accuracies);
  const latestAccuracy = accuracies[accuracies.length - 1];
  const previousAccuracy = accuracies.length > 1 ? accuracies[accuracies.length - 2] : latestAccuracy;
  const trend = latestAccuracy > previousAccuracy ? '↑' : latestAccuracy < previousAccuracy ? '↓' : '→';
  const trendColor = latestAccuracy > previousAccuracy ? 'text-green-600' : latestAccuracy < previousAccuracy ? 'text-red-600' : 'text-blue-600';

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
      <div className="bg-blue-50/60 rounded-xl px-4 py-3">
        <div className="text-xs text-blue-600 font-semibold mb-1">Total Rounds</div>
        <div className="text-2xl font-bold text-blue-900">{totalRounds}</div>
      </div>
      <div className="bg-blue-50/60 rounded-xl px-4 py-3">
        <div className="text-xs text-blue-600 font-semibold mb-1">Average Accuracy</div>
        <div className="text-2xl font-bold text-blue-900">{(avgAccuracy * 100).toFixed(1)}%</div>
      </div>
      <div className="bg-blue-50/60 rounded-xl px-4 py-3">
        <div className="text-xs text-blue-600 font-semibold mb-1">Best Accuracy</div>
        <div className="text-2xl font-bold text-blue-900">{(bestAccuracy * 100).toFixed(1)}%</div>
      </div>
      <div className="bg-blue-50/60 rounded-xl px-4 py-3">
        <div className="text-xs text-blue-600 font-semibold mb-1">Trend</div>
        <div className={`text-2xl font-bold ${trendColor}`}>{trend} {((latestAccuracy - previousAccuracy) * 100).toFixed(1)}%</div>
      </div>
    </div>
  );
}
