import React, { useEffect, useMemo, useState } from "react";
import apiService from "../services/api";
import Loader from "../components/Loader";
import Toast from "../components/Toast";

const STATUS_POLL_INTERVAL = 3000;

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
        <MetricCard label="Round" value={status.round} note={` / ${status.total_rounds ?? 0}`} />
        <MetricCard
          label="Global Accuracy"
          value={(status.global_accuracy ?? 0).toFixed(2)}
          note="%"
          highlight
        />
        <MetricCard label="Hospitals" value={status.connected_clients} note=" active" />
      </div>

      <div className="glass mb-8 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-2xl font-bold text-blue-900">Training Progress</h3>
            <p className="text-sm text-blue-900/70">Live accuracy trend per round</p>
          </div>
          <span className="text-xs text-blue-500">Updated: {status.last_update ? new Date(parseFloat(status.last_update) * 1000).toLocaleTimeString() : "—"}</span>
        </div>
        {loadingHistory ? (
          <Loader label="Loading metrics..." />
        ) : recentAccuracy.length ? (
          <AccuracyBars data={recentAccuracy} />
        ) : (
          <div className="rounded-xl p-4 text-center text-blue-400 bg-blue-50">
            No training history yet. Start a round to populate metrics.
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

      <div className="flex flex-col md:flex-row items-stretch gap-4">
        <div className="glass flex-1 p-6">
          <h3 className="text-2xl font-bold text-blue-900 mb-3">System Status</h3>
          {loadingStatus ? (
            <Loader label="Checking server..." />
          ) : (
            <ul className="space-y-2 text-sm text-blue-900/70">
              <li><strong>Training:</strong> {status.in_progress ? 'Running' : 'Idle'}</li>
              <li><strong>Last update:</strong> {status.last_update ? new Date(parseFloat(status.last_update) * 1000).toLocaleString() : '—'}</li>
              <li><strong>Global model:</strong> {status.global_accuracy ? `${status.global_accuracy.toFixed(2)}% accuracy` : 'Not evaluated yet'}</li>
            </ul>
          )}
        </div>
        <div className="glass flex-1 p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-2xl font-bold text-blue-900 mb-2">Training Controls</h3>
            <p className="text-sm text-blue-900/70">Kick off a federated learning round. Clients must be running.</p>
          </div>
          <button
            onClick={handleTrainRound}
            disabled={status.in_progress || triggering}
            className={`btn-cta w-full mt-4 ${status.in_progress || triggering ? 'opacity-60 cursor-not-allowed' : ''}`}
          >
            {status.in_progress || triggering ? 'Training...' : 'Start Training Round'}
          </button>
        </div>
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

function AccuracyBars({ data }) {
  const max = Math.max(...data.map((item) => item.accuracy || 0), 0.01);
  return (
    <div className="flex items-end gap-3 h-40">
      {data.map(({ round, accuracy }) => (
        <div key={round} className="flex-1 flex flex-col items-center">
          <div className="w-full bg-blue-100 rounded-full flex items-end justify-center" style={{ height: '100%' }}>
            <div
              className="w-full rounded-full bg-blue-500 shadow-lg"
              style={{ height: `${Math.min(accuracy / max, 1) * 100}%` }}
            />
          </div>
          <span className="text-xs text-blue-900 font-semibold mt-2">R{round}</span>
          <span className="text-[10px] text-blue-500">{(accuracy * 100).toFixed(1)}%</span>
        </div>
      ))}
    </div>
  );
}
