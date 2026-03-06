from typing import Dict, Optional, Tuple

import numpy as np


class LinearRegressionModel:
    """
    NumPy tabanlı basit çoklu lineer regresyon modeli.
    Scikit-learn bağımlılığı olmadan çalışır.

    Model: y = Xβ + ε
    Çözüm: β = (X'X)⁻¹X'y

    Feature Scaling: Z-Score normalization uygulanır.
    """

    def __init__(self):
        self.coefficients = None
        self.intercept = 0.0
        self.r_squared_score = 0.0
        self.n_samples = 0
        # Feature scaling parametreleri
        self._mean = None
        self._std = None
        self._is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """
        Modeli eğit.

        Args:
            X: Özellik matrisi (n_samples, n_features)
            y: Hedef vektörü (n_samples,)

        Returns:
            Dict: Eğitim sonuçları
        """
        self.n_samples = len(y)
        if self.n_samples < 2:
            raise ValueError("Eğitim için en az 2 veri noktası gereklidir.")

        # Feature Scaling: Z-Score Normalization
        # Her özellik için ortalama ve std hesapla
        self._mean = np.mean(X, axis=0)
        self._std = np.std(X, axis=0)
        # Sıfır std'yi önlemek için epsilon ekle (1e-6 daha stabil)
        self._std = np.where(self._std == 0, 1e-6, self._std)

        # Ölçeklenmiş X
        X_scaled = (X - self._mean) / self._std

        # X matrisine bias (intercept) için 1'ler sütunu ekle
        # X_b = [1, x1, x2, ...]
        ones = np.ones((self.n_samples, 1))
        X_b = np.hstack((ones, X_scaled))

        try:
            # Normal denklem çözümü: β = (X'X)⁻¹X'y
            # np.linalg.inv yerine pinv (pseudo-inverse) kullanarak singüler matris hatalarını önle
            beta = np.linalg.pinv(X_b.T.dot(X_b)).dot(X_b.T).dot(y)

            self.intercept = beta[0]
            self.coefficients = beta[1:]

            # R² hesapla
            y_pred = X_b.dot(beta)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            ss_res = np.sum((y - y_pred) ** 2)

            # Sıfıra bölme hatasını önle
            if ss_tot == 0:
                self.r_squared_score = 0.0
            else:
                self.r_squared_score = 1 - (ss_res / ss_tot)

            self._is_fitted = True

            return {
                "success": True,
                "coefficients": {
                    "intercept": float(self.intercept),
                    "weights": [float(c) for c in self.coefficients],
                },
                "r_squared": float(self.r_squared_score),
                "sample_count": int(self.n_samples),
                "scaling": {
                    "mean": [float(m) for m in self._mean],
                    "std": [float(s) for s in self._std],
                },
            }

        except np.linalg.LinAlgError as e:
            return {"success": False, "error": str(e)}

    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Tahmin yap.

        Args:
            X: Özellik matrisi (n_samples, n_features)

        Returns:
            Tuple[np.ndarray, Dict]: (Tahminler, Metadata)
        """
        if not self._is_fitted or self.coefficients is None:
            raise RuntimeError("Model henüz eğitilmedi.")

        # Aynı scaling'i uygula (eğitim sırasında hesaplanan mean/std ile)
        X_scaled = (X - self._mean) / self._std

        # Bias ekle
        ones = np.ones((len(X_scaled), 1))
        X_b = np.hstack((ones, X_scaled))

        # Tüm katsayılar (intercept dahil)
        beta = np.insert(self.coefficients, 0, self.intercept)

        y_pred = X_b.dot(beta)

        return y_pred, {"r_squared": self.r_squared_score, "scaled": True}

    def get_scaling_params(self) -> Optional[Dict]:
        """Scaling parametrelerini döndür (model persistence için)"""
        if not self._is_fitted:
            return None
        return {"mean": self._mean.tolist(), "std": self._std.tolist()}

    def set_scaling_params(self, params: Dict):
        """Scaling parametrelerini ayarla (model loading için)"""
        self._mean = np.array(params["mean"])
        self._std = np.array(params["std"])
