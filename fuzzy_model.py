import math
import pandas as pd
from collections import defaultdict

from config import D1, D2, INTERVAL_MIN, INTERVAL_MAX

def hitung_margin_semesta(xmin: float, xmax: float) -> float:
  
    magnitude = xmax - xmin

    if magnitude <= 0:
        return 1.0

    raw_margin = magnitude * 0.01

    kelipatan_tersedia = [10, 50, 100, 500, 1_000, 5_000, 10_000]

    for kelipatan in kelipatan_tersedia:
        if raw_margin <= kelipatan:
            return math.ceil(raw_margin / kelipatan) * kelipatan

    return math.ceil(raw_margin / 10_000) * 10_000

class FuzzyTimeSeriesChen:

    def __init__(self) -> None:
        self.intervals:    list[tuple]        = []
        self.labels:       list[str]          = []
        self.FLRG:         defaultdict        = defaultdict(list)
        self.fuzzy_data:   pd.DataFrame | None = None
        self.flr:          list[tuple]        = []
        self.df_prediksi:  pd.DataFrame | None = None
        self.universe_info: dict              = {}

    #HIMPUNAN SEMESTA & INTERVAL

    @staticmethod
    def hitung_panjang_interval(
        data: pd.DataFrame,
        d1: float | None = None,
        d2: float | None = None,
    ) -> dict:
        harga = data["Harga"].tolist()
        n     = len(harga)

        xmin = min(harga)
        xmax = max(harga)

        if d1 is None:
            d1 = hitung_margin_semesta(xmin, xmax)
        if d2 is None:
            d2 = hitung_margin_semesta(xmin, xmax)

        selisih_absolut = [abs(harga[t + 1] - harga[t]) for t in range(n - 1)]

        D_bar = sum(selisih_absolut) / (n - 1)

        l     = D_bar / 2

        u_start = xmin - d1 
        u_end   = xmax + d2
        U       = u_end - u_start

        k = 3 if l == 0 else int(math.ceil(U / l))
        k = max(INTERVAL_MIN, min(k, INTERVAL_MAX))

        return {
            "D_bar":            round(D_bar, 4),
            "selisih_absolut":  selisih_absolut,
            "panjang_interval": round(l, 4),
            "jumlah_interval":  k,
            "u_start":          round(u_start, 2),
            "u_end":            round(u_end, 2),
            "U":                round(U, 2),
            "D1":               d1,
            "D2":               d2,
        }


    def create_intervals(
        self,
        data: pd.DataFrame,
        d1: float | None = None,
        d2: float | None = None,
    ) -> list[tuple]:
        hasil            = self.hitung_panjang_interval(data, d1=d1, d2=d2)
        n_intervals      = hasil["jumlah_interval"]
        panjang_interval = hasil["panjang_interval"]
        u_start          = hasil["u_start"]

        self.intervals = []
        for i in range(n_intervals):
            lower = u_start + i * panjang_interval
            upper = lower + panjang_interval
            self.intervals.append((round(lower, 2), round(upper, 2)))

        self.labels = [f"A{i + 1}" for i in range(n_intervals)]

        self.universe_info = {
            "harga_min":        data["Harga"].min(),
            "harga_max":        data["Harga"].max(),
            "D1":               hasil["D1"],
            "D2":               hasil["D2"],
            "u_start":          hasil["u_start"],
            "u_end":            hasil["u_end"],
            "U":                hasil["U"],
            "D_bar":            hasil["D_bar"],
            "selisih_absolut":  hasil["selisih_absolut"],
            "panjang_interval": panjang_interval,
            "jumlah_interval":  n_intervals,
            "metode_interval":  "Average-Based Length (Huarng, 2001)",
        }

        return self.intervals

    #FUZZIFIKASI

    def fuzzify(self, value: float) -> str | None:
        
        for i, (lower, upper) in enumerate(self.intervals):
            if i == 0:
                if lower <= value <= upper:
                    return self.labels[i]
            else:
                if lower < value <= upper:
                    return self.labels[i]

        if value < self.intervals[0][0]:
            return self.labels[0]
        if value > self.intervals[-1][1]:
            return self.labels[-1]

        return None

    #FLR & FLRG

    def create_flrg(self, data: pd.DataFrame) -> defaultdict:

        fuzzy_series = data["Harga"].apply(self.fuzzify)

        self.fuzzy_data = pd.DataFrame({
            "Tanggal": data["Tanggal"],
            "Harga":   data["Harga"],
            "Fuzzy":   fuzzy_series,
        })

        self.flr = []
        for i in range(len(fuzzy_series) - 1):
            current = fuzzy_series.iloc[i]
            nxt     = fuzzy_series.iloc[i + 1]
            if current is not None and nxt is not None:
                self.flr.append((current, nxt))

        self.FLRG = defaultdict(list)
        for antecedent, consequent in self.flr:
            if consequent not in self.FLRG[antecedent]:
                self.FLRG[antecedent].append(consequent)

        return self.FLRG

    #DEFUZZIFIKASI

    def _defuzzifikasi(self, state: str) -> float:
        
        consequents = self.FLRG.get(state, None)

        if not consequents:
            if state in self.labels:
                idx = self.labels.index(state)
                low, high = self.intervals[idx]
                return (low + high) / 2
            return (self.intervals[0][0] + self.intervals[0][1]) / 2

        freq = defaultdict(int)
        for ant, con in self.flr:
            if ant == state:
                freq[con] += 1

        total = sum(freq[c] for c in consequents if c in self.labels) or 1

        weighted_sum = 0.0
        for c in consequents:
            if c in self.labels:
                idx = self.labels.index(c)
                low, high = self.intervals[idx]
                midpoint  = (low + high) / 2
                weight    = freq[c] / total
                weighted_sum += weight * midpoint

        return weighted_sum

    #PREDIKSI ITERATIF

    def predict(
        self,
        data: pd.DataFrame,
        days_to_predict: int = 30,
    ) -> list[dict]:
        data_copy         = data.copy()
        data_copy["Fuzzy"] = data_copy["Harga"].apply(self.fuzzify)

        last_fuzzy    = data_copy["Fuzzy"].iloc[-1] or self.labels[0]
        predictions   = []
        current_state = last_fuzzy

        for i in range(days_to_predict):
            predicted_price = self._defuzzifikasi(current_state)
            predicted_fuzzy = self.fuzzify(predicted_price) or current_state

            predictions.append({
                "Hari ke-":       i + 1,
                "Fuzzy State":    predicted_fuzzy,
                "Harga Prediksi": round(predicted_price, 2),
            })
            current_state = predicted_fuzzy

        self.df_prediksi = pd.DataFrame(predictions)
        return predictions
