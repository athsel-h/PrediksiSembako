import os
import pandas as pd

from config import (
    KOMODITAS_MAP,
    WINSORIZE_HARIAN_LOWER,
    WINSORIZE_HARIAN_UPPER,
    WINSORIZE_MINGGUAN_LOWER,
    WINSORIZE_MINGGUAN_UPPER,
)


#PROSES CSV

def preprocess_data(df_raw: list) -> pd.DataFrame:
    sample = df_raw[0].iloc[1] if len(df_raw) > 1 else df_raw[0].iloc[0]
    sep = ";" if ";" in str(sample) else ","

    df_split = df_raw[0].str.split(sep, expand=True)

    if df_split.shape[1] < 4:
        raise ValueError(
            f"Format CSV tidak valid. Pastikan kolom dipisahkan dengan '{sep}' "
            f"dan memiliki minimal 4 kolom: Hari, Bulan, Tahun, Harga."
        )

    df = df_split.drop(index=0).reset_index(drop=True)
    df.columns = ["Hari", "Bulan", "Tahun", "Harga"] + list(df_split.columns[4:])

    BULAN_ID = {
        "januari": "01", "februari": "02", "maret":     "03",
        "april":   "04", "mei":      "05", "juni":      "06",
        "juli":    "07", "agustus":  "08", "september": "09",
        "oktober": "10", "november": "11", "desember":  "12",
    }
    bulan_raw   = df["Bulan"].str.strip().str.lower()
    bulan_angka = bulan_raw.map(BULAN_ID).fillna(bulan_raw)

    df["Tanggal"] = pd.to_datetime(
        df["Hari"].str.strip() + "-" + bulan_angka + "-" + df["Tahun"].str.strip(),
        dayfirst=True,
        errors="coerce",
    )
    df["Harga"] = pd.to_numeric(df["Harga"].str.strip(), errors="coerce")

    result = df[["Tanggal", "Harga"]].dropna().reset_index(drop=True)

    if len(result) == 0:
        raise ValueError(
            "Tidak ada data valid setelah preprocessing. "
            "Periksa format tanggal dan nilai harga pada file CSV."
        )

    return result


#PENANGANAN OUTLIER (WINSORIZE)

def cap_outliers(
    data: pd.DataFrame,
    lower_pct: float = WINSORIZE_HARIAN_LOWER,
    upper_pct: float = WINSORIZE_HARIAN_UPPER,
) -> tuple[pd.DataFrame, dict]:
    
    lower_bound = data["Harga"].quantile(lower_pct)
    upper_bound = data["Harga"].quantile(upper_pct)

    n_outlier = (
        (data["Harga"] < lower_bound) | (data["Harga"] > upper_bound)
    ).sum()

    outlier_info = {
        "lower_pct":   int(lower_pct * 100),
        "upper_pct":   int(upper_pct * 100),
        "lower_bound": round(float(lower_bound), 2),
        "upper_bound": round(float(upper_bound), 2),
        "n_outlier":   int(n_outlier),
        "metode":      "Winsorize",
    }

    data_capped = data.copy()
    data_capped["Harga"] = data_capped["Harga"].clip(
        lower=lower_bound, upper=upper_bound
    )

    return data_capped, outlier_info


#AGREGASI TEMPOLAR MINGGUAN

def resample_mingguan(data: pd.DataFrame) -> pd.DataFrame:

    data_sorted = (
        data[["Tanggal", "Harga"]]
        .copy()
        .sort_values("Tanggal")
        .reset_index(drop=True)
    )

    data_sorted["Kelompok_Minggu"] = data_sorted.index // 7

    jumlah_data = (
        data_sorted
        .groupby("Kelompok_Minggu")["Harga"]
        .count()
    )

    kelompok_lengkap = jumlah_data[
        jumlah_data == 7
    ].index

    data_lengkap = data_sorted[
        data_sorted["Kelompok_Minggu"].isin(kelompok_lengkap)
    ].copy()

    data_mingguan = (
        data_lengkap
        .groupby("Kelompok_Minggu", as_index=False)
        .agg(
            Tanggal=("Tanggal", lambda x: x.iloc[3]),
            Harga=("Harga", "median"),
        )
    )

    data_mingguan = data_mingguan[
        ["Tanggal", "Harga"]
    ].reset_index(drop=True)

    return data_mingguan


#DETEKSI KOMODITAS

def deteksi_komoditas(filename: str) -> dict:
    nama_file  = os.path.splitext(filename)[0].lower()
    nama_clean = nama_file.replace("-", "_").replace(" ", "_")

    for keyword in sorted(KOMODITAS_MAP.keys(), key=len, reverse=True):
        kw_clean = keyword.replace(" ", "_")
        if kw_clean in nama_clean:
            return KOMODITAS_MAP[keyword].copy()

    nama_display = os.path.splitext(filename)[0]
    nama_display = nama_display.replace("_", " ").replace("-", " ").title()
    if nama_display.lower().startswith("data "):
        nama_display = nama_display[5:]

    return {"nama": nama_display, "satuan": "kg"}


#PIPELINE PREPROCESSING

def bangun_data_model(
    data: pd.DataFrame,
    use_weekly: bool,
    use_outlier_cap: bool,
) -> tuple[pd.DataFrame, dict | None]:

    outlier_info = None

    if use_weekly:
        data_model = resample_mingguan(data)
        if use_outlier_cap:
            data_model, outlier_info = cap_outliers(
                data_model,
                lower_pct=WINSORIZE_MINGGUAN_LOWER,
                upper_pct=WINSORIZE_MINGGUAN_UPPER,
            )
    else:
        if use_outlier_cap:
            data_model, outlier_info = cap_outliers(
                data,
                lower_pct=WINSORIZE_HARIAN_LOWER,
                upper_pct=WINSORIZE_HARIAN_UPPER,
            )
        else:
            data_model = data.copy()

    return data_model, outlier_info
