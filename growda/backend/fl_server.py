import os
import sys
import traceback
from typing import List, Tuple

import flwr as fl
import numpy as np
import tensorflow as tf
from flwr.common import Metrics, Parameters, ndarrays_to_parameters, parameters_to_ndarrays

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.model import create_pneumonia_model

print(" Starting Growda Flower Federated Server...")

MODEL_PATH = "global_model.keras"
HISTORY_PATH = "metrics_history.npy"
global_round = 0
global_accuracy = 0.0
connected_clients = 0

# New: store all per-client metrics
all_client_metrics = []

def weighted_average(metrics: List[Tuple[int, Metrics]]) -> Metrics:
    if not metrics:
        return {}
    weights = []
    metrics_values = []
    for num_examples, metric in metrics:
        if isinstance(num_examples, (int, float)):
            weights.append(int(num_examples))
            metrics_values.append(metric)
    if not weights or not metrics_values:
        return {}
    weighted_metrics = {}
    for metric_name in metrics_values[0]:
        values = [m.get(metric_name, 0.0) for m in metrics_values]
        weighted_metrics[metric_name] = float(np.average(values, weights=weights))
    return weighted_metrics

class PneumoniaStrategy(fl.server.strategy.FedAvg):
    def aggregate_fit(self, server_round, results, failures):
        global global_round, global_accuracy, connected_clients, all_client_metrics
        global_round = server_round
        filtered_results = []
        client_metrics = []

        for idx, r in enumerate(results or []):
            try:
                # Expected Flower >=1.4.0 structure: (ClientProxy, FitRes)
                if isinstance(r, tuple) and len(r) == 2 and hasattr(r[1], "parameters"):
                    fit_res = r[1]
                    metrics = getattr(fit_res, "metrics", {})
                    client_id = str(getattr(r[0], "cid", idx))
                    accuracy = metrics.get("accuracy", None)
                    client_metrics.append({"client": client_id, "accuracy": accuracy})
                    filtered_results.append(r)
                    continue

                # Legacy/invalid shapes: log and skip from aggregation to avoid crashes
                if isinstance(r, tuple) and len(r) == 2 and isinstance(r[1], int):
                    client_metrics.append({"client": f"legacy_{idx}", "accuracy": None})
                    print(f"[Aggregation] Skipping legacy fit result at index {idx}")
                    continue
                if isinstance(r, tuple) and len(r) == 2 and isinstance(r[0], list) and isinstance(r[1], int):
                    client_metrics.append({"client": f"legacy_{idx}", "accuracy": None})
                    print(f"[Aggregation] Skipping legacy list-weights result at index {idx}")
                    continue
            except Exception as ex:
                print(f"[Aggregation] Skipping entry {idx}: {ex}")

        connected_clients = len(filtered_results)
        if not filtered_results:
            print("[Aggregation] No valid client updates; skipping round.")
            return None, {}

        aggregated_weights, metrics = super().aggregate_fit(server_round, filtered_results, failures)
        # Save & log global model after aggregation
        if aggregated_weights is not None:
            try:
                model = create_pneumonia_model()
                model.set_weights(aggregated_weights)
                model.save(MODEL_PATH)
                if metrics and "accuracy" in metrics:
                    global_accuracy = metrics["accuracy"]
                print(f"🌐 [Round {server_round}] Global model updated and saved at '{MODEL_PATH}'.")
                print("🔗 Connected clients:", connected_clients)
                print(f"📈 Client Accuracies: {client_metrics}")
                _log_history(server_round, global_accuracy, client_metrics)
                all_client_metrics.append({"round": server_round, "clients": client_metrics})
            except Exception as ex:
                print("[Server] ❌ Model saving/metrics logging failed:", ex)
                traceback.print_exc()
        return aggregated_weights, metrics

def _log_history(round_num, accuracy, client_metrics):
    try:
        if os.path.exists(HISTORY_PATH):
            hist = np.load(HISTORY_PATH, allow_pickle=True).tolist()
        else:
            hist = []
        hist.append({"round": round_num, "accuracy": accuracy, "clients": client_metrics})
        np.save(HISTORY_PATH, hist)
    except Exception as e:
        print("[Metrics] Logging history failed:", e)

def get_metrics_history():
    if os.path.exists(HISTORY_PATH):
        hist = np.load(HISTORY_PATH, allow_pickle=True).tolist()
        return hist
    return []

def get_training_status():
    return {
        "round": global_round,
        "global_accuracy": global_accuracy,
        "connected_clients": connected_clients,
        "total_rounds": 3,
        "last_update": str(tf.timestamp().numpy()),
    }

def _ensure_model_file():
    if not os.path.exists(MODEL_PATH):
        model = create_pneumonia_model()
        model.save(MODEL_PATH)


def _initial_parameters() -> Parameters:
    _ensure_model_file()
    try:
        model = tf.keras.models.load_model(MODEL_PATH)
        weights = model.get_weights()
    except Exception as exc:
        print(f"[Server] ⚠️ Failed to load existing model weights: {exc}. Rebuilding baseline model.")
        model = create_pneumonia_model()
        weights = model.get_weights()
    return ndarrays_to_parameters(weights)


def start_server(num_rounds: int = 3, reset_model: bool = False):
    if reset_model and os.path.exists(MODEL_PATH):
        os.remove(MODEL_PATH)
    _ensure_model_file()
    strategy = PneumoniaStrategy(
        min_fit_clients=2,
        min_evaluate_clients=2,
        min_available_clients=2,
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        evaluate_metrics_aggregation_fn=weighted_average,
        initial_parameters=_initial_parameters(),
    )
    try:
        fl.server.start_server(
            server_address="0.0.0.0:8080",
            config=fl.server.ServerConfig(num_rounds=num_rounds),
            strategy=strategy,
        )
    except Exception as e:
        print(f"❌ Server error during execution: {e}")

if __name__ == "__main__":
    start_server(num_rounds=3)