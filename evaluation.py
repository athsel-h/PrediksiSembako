import pandas as pd

from fuzzy_model import FuzzyTimeSeriesChen


#PERHITUNGAN MAPE

def hitung_mape(
    actual:    pd.Series | list,
    predicted: pd.Series | list,
) -> float:
    
    actual    = pd.Series(actual).reset_index(drop=True)
    predicted = pd.Series(predicted).reset_index(drop=True)

    mask = actual != 0
    mape = (abs((actual[mask] - predicted[mask]) / actual[mask]).mean()) * 100

    return float(mape)

#KATEGORISASI PERFORMA

def kategori_performansi(mape: float) -> str:
    
    if mape < 10:
        return "Sangat Baik"
    elif mape < 20:
        return "Baik"
    elif mape < 50:
        return "Cukup"
    else:
        return "Buruk"

#EVALUASI

def hitung_insample(model: FuzzyTimeSeriesChen) -> dict:
    
    fuzzy_series = model.fuzzy_data["Fuzzy"].tolist()
    harga_aktual = model.fuzzy_data["Harga"].tolist()

    in_sample_predictions = []
    for i in range(1, len(fuzzy_series)):
        state = fuzzy_series[i - 1]
        pred  = model._defuzzifikasi(state)
        in_sample_predictions.append(pred)

    aktual_eval   = pd.Series(harga_aktual[1:])
    prediksi_eval = pd.Series(in_sample_predictions)

    mape     = hitung_mape(aktual_eval, prediksi_eval)
    kategori = kategori_performansi(mape)

    return {
        "mape":     mape,
        "kategori": kategori,
        "aktual":   harga_aktual[1:],
        "prediksi": in_sample_predictions,
    }
