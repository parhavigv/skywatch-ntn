import numpy as np
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Optional
import threading


@dataclass
class DeviceBaseline:
    """Rolling per-device baseline using Welford online algorithm."""
    n: int = 0
    mean: np.ndarray = field(default_factory=lambda: np.zeros(6))
    M2: np.ndarray = field(default_factory=lambda: np.zeros(6))
    history: deque = field(default_factory=lambda: deque(maxlen=200))

    def update(self, vector: np.ndarray) -> None:
        self.n += 1
        delta = vector - self.mean
        self.mean += delta / self.n
        delta2 = vector - self.mean
        self.M2 += delta * delta2
        self.history.append(vector.copy())

    @property
    def variance(self) -> np.ndarray:
        if self.n < 2:
            return np.ones(6)
        return self.M2 / (self.n - 1)

    @property
    def std(self) -> np.ndarray:
        return np.sqrt(np.maximum(self.variance, 1e-8))

    def z_score(self, vector: np.ndarray) -> np.ndarray:
        return np.abs((vector - self.mean) / self.std)


class AnomalyDetector:
    """
    Production-grade multi-method anomaly detector.
    Method 1: Per-device Z-score using Welford online algorithm.
    Method 2: Isolation Forest multivariate detection (activates at n>=50).
    Final score: weighted ensemble of both methods.
    """

    ZSCORE_THRESHOLD = 3.0
    ISOLATION_CONTAMINATION = 0.05

    def __init__(self):
        self._baselines: dict[str, DeviceBaseline] = defaultdict(DeviceBaseline)
        self._isolation_forests: dict[str, object] = {}
        self._lock = threading.RLock()

    def _extract_vector(self, metrics: dict) -> np.ndarray:
        return np.array([
            float(metrics.get("temperature") or 0.0),
            float(metrics.get("vibration") or 0.0),
            float(metrics.get("rpm") or 0.0),
            float(metrics.get("voltage") or 220.0),
            float(metrics.get("current") or 0.0),
            float(metrics.get("load_factor") or 0.5),
        ], dtype=np.float64)

    def _try_fit_isolation_forest(
        self, device_id: str, baseline: DeviceBaseline
    ) -> None:
        try:
            from sklearn.ensemble import IsolationForest
            X = np.array(list(baseline.history))
            if X.shape[0] < 50:
                return
            clf = IsolationForest(
                n_estimators=100,
                contamination=self.ISOLATION_CONTAMINATION,
                random_state=42,
                n_jobs=-1,
            )
            clf.fit(X)
            self._isolation_forests[device_id] = clf
        except Exception:
            pass

    def score(self, device_id: str, metrics: dict) -> float:
        vector = self._extract_vector(metrics)

        with self._lock:
            baseline = self._baselines[device_id]
            baseline.update(vector)

            if baseline.n > 0 and baseline.n % 50 == 0:
                self._try_fit_isolation_forest(device_id, baseline)

            z_scores = baseline.z_score(vector)
            z_max = float(np.max(z_scores))
            z_component = min(z_max / self.ZSCORE_THRESHOLD, 1.0)

            if_component = 0.0
            clf = self._isolation_forests.get(device_id)
            if clf is not None:
                try:
                    raw = float(clf.score_samples([vector])[0])
                    if_component = float(np.clip((-raw - 0.3) / 0.5, 0.0, 1.0))
                except Exception:
                    pass

            if clf is not None:
                final_score = 0.4 * z_component + 0.6 * if_component
            else:
                final_score = z_component

            return round(float(np.clip(final_score, 0.0, 1.0)), 4)

    def get_device_stats(self, device_id: str) -> Optional[dict]:
        with self._lock:
            baseline = self._baselines.get(device_id)
            if not baseline or baseline.n == 0:
                return None
            return {
                "samples_seen": baseline.n,
                "feature_means": baseline.mean.tolist(),
                "feature_stds": baseline.std.tolist(),
                "isolation_forest_active": device_id in self._isolation_forests,
            }


detector = AnomalyDetector()