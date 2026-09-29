import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import streamlit as st
from datetime import datetime, timedelta

from config import STYLE_TABEL

#SIDEBAR

def upload_file_sidebar() -> object:
    st.sidebar.title("Menu Prediksi")
    return st.sidebar.file_uploader(
        "Upload data harga sembako (CSV)",
        type=["csv"],
        key="upload_file",
    )


def resample_sidebar() -> tuple[bool, bool]:
   
    st.sidebar.subheader("Opsi Pemrosesan Data")

    use_outlier_cap = st.sidebar.checkbox(
        "Tangani Outlier (Winsorize)",
        value=True,
        key="use_outlier_cap",
        help=(
            "Membatasi nilai harga ekstrem menggunakan metode Winsorize persentil. "
            "Nilai tidak dihapus, hanya dibatasi agar interval fuzzy tidak terdistorsi."
        ),
    )
    use_weekly = st.sidebar.checkbox(
        "Gunakan Agregasi Tempolar (perediksi per minggu)",
        value=False,
        key="use_weekly",
        help=(
            "Mengelompokkan data harian menjadi median per minggu. "
            "Jika aktif, prediksi dan grafik akan ditampilkan dalam satuan MINGGU, "
            "bukan hari. Direkomendasikan jika banyak hari dengan harga tidak berubah."
        ),
    )
    return use_outlier_cap, use_weekly


def date_range_sidebar(
    data_start: datetime,
    data_end: datetime,
    use_weekly: bool = False,
) -> tuple[datetime, datetime]:

    if use_weekly:
        #MODE MINGGUAN
        st.sidebar.subheader("Rentang Prediksi (Mingguan)")

        start_date = data_end + timedelta(days=7)

        n_minggu = st.sidebar.selectbox(
            "Jumlah minggu prediksi",
            options=[1, 2, 3, 4],
            index=0,
            key="n_minggu",
            help=(
                "Pilih jumlah minggu ke depan yang ingin diprediksi. "
                "Tanggal prediksi ditentukan otomatis berdasarkan "
                "tanggal tengah minggu historis terakhir."
            ),
        )

        end_date = (
            start_date
            + timedelta(weeks=n_minggu)
            - timedelta(days=1)
        )

        start_date = datetime.combine(
            start_date.date(),
            datetime.min.time()
        )

        end_date = datetime.combine(
            end_date.date(),
            datetime.min.time()
        )

    else:
        #MODE HARIAN
        st.sidebar.subheader("Rentang Prediksi (Harian)")

        default_start = data_end + timedelta(days=1)
        default_end = default_start + timedelta(days=6)

        start_date = st.sidebar.date_input(
            "Mulai prediksi dari",
            min_value=default_start,
            value=default_start,
            key="start_date",
        )

        end_date = st.sidebar.date_input(
            "Sampai dengan",
            min_value=start_date,
            value=default_end,
            key="end_date",
        )

        start_date = datetime.combine(
            start_date,
            datetime.min.time()
        )

        end_date = datetime.combine(
            end_date,
            datetime.min.time()
        )

    return start_date, end_date


#NOTIFIKASI & STATUS

def tampil_pesan_sukses(teks: str) -> None:
    st.markdown(
        f"""<div style="padding:0.8rem;border-radius:8px;
            background-color:#a7f3d0;border:2px solid #a7f3d0;
            color:#14532d;font-weight:500;font-size:1.1rem;">
            ✅ {teks}</div>""",
        unsafe_allow_html=True,
    )


def tampil_info_outlier(outlier_info: dict | None, use_outlier_cap: bool) -> None:
    if use_outlier_cap and outlier_info:
        label_pct = f"{outlier_info['lower_pct']}%–{outlier_info['upper_pct']}%"
        if outlier_info["n_outlier"] > 0:
            st.info(
                f"**Penanganan Outlier Aktif (Winsorize {label_pct}):** "
                f"Ditemukan **{outlier_info['n_outlier']} data** di luar batas. "
                f"Batas bawah: Rp {outlier_info['lower_bound']:,.0f} | "
                f"Batas atas: Rp {outlier_info['upper_bound']:,.0f}. "
                f"Nilai ekstrem dibatasi agar tidak mendistorsi interval fuzzy."
            )
        else:
            st.success(
                f"**Penanganan Outlier Aktif (Winsorize {label_pct}):** "
                f"Tidak ditemukan data ekstrem di luar batas."
            )
    elif not use_outlier_cap:
        st.warning(
            "**Penanganan Outlier Nonaktif:** Data digunakan apa adanya. "
            "Nilai ekstrem dapat mendistorsi interval fuzzy dan meningkatkan MAPE."
        )


def tampil_info_agregasi(
    use_weekly: bool,
    n_harian:   int,
    n_mingguan: int,
) -> None:
    if use_weekly:
        st.info(
            f"**Agregasi Tempolar Aktif:** Data harian ({n_harian} hari) "
            f"diubah ke median mingguan ({n_mingguan} minggu) "
            f"untuk mengurangi noise data statis."
        )


#TABEL LANGKAH-LANGKAH ALGORITMA

def tampil_data_historis(data_model: pd.DataFrame, use_weekly: bool = False) -> None:
    judul = "Data Historis Mingguan" if use_weekly else "Data Historis"
    with st.expander(judul, expanded=True):
        st.dataframe(
            data_model.style.set_properties(**STYLE_TABEL),
            use_container_width=True,
        )


def tampil_himpunan_semesta(universe_info: dict) -> None:
    u = universe_info
    with st.expander("Menentukan Himpunan Semesta"):
        st.write("Harga Minimum (Xmin):", u["harga_min"])
        st.write("Harga Maksimum (Xmax):", u["harga_max"])
        st.write("Konstanta D1:", u["D1"])
        st.write("Konstanta D2:", u["D2"])
        st.write(
            f"Batas Bawah Semesta: Xmin − D1 = "
            f"{u['harga_min']} − {u['D1']} = **{u['u_start']}**"
        )
        st.write(
            f"Batas Atas Semesta:  Xmax + D2 = "
            f"{u['harga_max']} + {u['D2']} = **{u['u_end']}**"
        )


def tampil_panjang_interval(universe_info: dict, intervals: list, labels: list) -> None:
    u = universe_info
    with st.expander("Menentukan Panjang Interval"):
        st.markdown("**Langkah a — Rata-rata nilai absolut selisih (D̄)**")
        selisih_df = pd.DataFrame({
            "t":               list(range(1, len(u["selisih_absolut"]) + 1)),
            "|X(t+1) - X(t)|": u["selisih_absolut"],
        })
        st.dataframe(
            selisih_df.style.set_properties(**STYLE_TABEL),
            use_container_width=True,
        )
        st.write(f"D̄ = jumlah selisih / (n−1) = **{u['D_bar']}**")

        st.divider()
        st.markdown("**Langkah b — Panjang interval (l)**")
        st.write(f"l = D̄ / 2 = {u['D_bar']} / 2 = **{u['panjang_interval']}**")

        st.divider()
        st.markdown("**Langkah c — Jumlah interval (k)**")
        st.write(f"D1 = {u['D1']}  |  D2 = {u['D2']}")
        st.write(
            f"U = (Xmax + D2) − (Xmin − D1) = "
            f"({u['harga_max']} + {u['D2']}) − ({u['harga_min']} − {u['D1']}) = **{u['U']}**"
        )
        st.write(
            f"k = U / l = {u['U']} / {u['panjang_interval']} = "
            f"**{u['jumlah_interval']} interval**"
        )

        st.divider()
        st.markdown("**Daftar Interval**")
        for i, interval in enumerate(intervals):
            st.write(f"Interval {labels[i]}: {interval}")


def tampil_fuzzifikasi(fuzzy_data: pd.DataFrame) -> None:
    with st.expander("Fuzzifikasi"):
        st.dataframe(
            fuzzy_data.style.set_properties(**STYLE_TABEL),
            use_container_width=True,
        )


def tampil_flr(flr: list[tuple]) -> None:
    with st.expander("Fuzzy Logical Relationship (FLR)"):
        flr_df = pd.DataFrame(flr, columns=["From", "To"])
        st.dataframe(
            flr_df.style.set_properties(**STYLE_TABEL),
            use_container_width=True,
        )


def tampil_flrg(flrg: dict) -> None:
    with st.expander("Fuzzy Logical Relationship Group (FLRG)"):
        flrg_list = [(k, ", ".join(v)) for k, v in flrg.items()]
        flrg_df   = pd.DataFrame(flrg_list, columns=["Antecedent", "Consequents"])
        st.dataframe(
            flrg_df.style.set_properties(**STYLE_TABEL),
            use_container_width=True,
        )


def tampil_hasil_prediksi(
    df_prediksi:     pd.DataFrame,
    start_date:      datetime,
    days_to_predict: int,
    use_weekly:      bool = False,
) -> pd.DataFrame | None:

    if use_weekly:
        n_minggu = days_to_predict

        judul_expander = (
            f"Defuzzifikasi & Hasil Prediksi — "
            f"{n_minggu} Minggu ke Depan"
        )
    else:
        judul_expander = "Defuzzifikasi & Hasil Prediksi"

    with st.expander(judul_expander):

        if df_prediksi is None or len(df_prediksi) == 0:
            st.warning(
                "Prediksi tidak dapat dihasilkan. Periksa data input."
            )
            return None

        df_pred = df_prediksi.copy()

        if use_weekly:
            ts_tengah = pd.Timestamp(start_date)

            tanggal_list = [
                ts_tengah + timedelta(weeks=i)
                for i in range(n_minggu)
            ]

            periode_list = [
                f"{(t - timedelta(days=3)).strftime('%d %b')} – "
                f"{(t + timedelta(days=3)).strftime('%d %b %Y')}"
                for t in tanggal_list
            ]

            df_pred["Tanggal"] = tanggal_list

            df_pred["Minggu ke-"] = list(
                range(1, n_minggu + 1)
            )

            df_pred["Periode Minggu"] = periode_list


            kolom_tampil = ["Minggu ke-", "Periode Minggu"] + [
                c
                for c in df_pred.columns
                if c not in (
                    "Minggu ke-",
                    "Periode Minggu",
                    "Tanggal",
                    "Hari ke-",
                )
            ]

            st.dataframe(
                df_pred[kolom_tampil].style.set_properties(
                    **STYLE_TABEL
                ),
                use_container_width=True,
            )

        else:

            df_pred["Tanggal"] = pd.date_range(
                start=start_date,
                periods=days_to_predict
            )

            st.dataframe(
                df_pred.style.set_properties(
                    **STYLE_TABEL
                ),
                use_container_width=True,
            )

        return df_pred


def tampil_evaluasi_mape(
    mape:      float,
    kategori:  str,
    use_weekly: bool,
) -> None:
    #Label judul model saat ini
    label_mode = "Mingguan" if use_weekly else "Harian"
    with st.expander(f"Evaluasi Prediksi (MAPE) — Mode {label_mode}"):
        st.markdown(
            f"""<div style="padding:1rem;border-radius:10px;
                background-color:#a7f3d0;color:#black;
                font-size:1.25rem;font-weight:bold;
                text-align:center;border:2px solid #a7f3d0;">
                <span style="font-size:1.5rem;">MAPE: {mape:.2f}%</span><br>
                <span style="font-size:1.3rem;">Performa: {kategori}</span>
                </div>""",
            unsafe_allow_html=True,
        )
        if use_weekly:
            st.success(
                " **Mode Perediksi Mingguan aktif.** "
                "Nilai MAPE di atas dihitung dari data agregat per minggu (in-sample). "
                "Bandingkan dengan MAPE mode Harian (nonaktifkan checkbox di sidebar) "
                "untuk melihat dampak agregasi terhadap akurasi model."
            )


#GRAFIK

def tampil_grafik(
    data_model:     pd.DataFrame,
    df_pred:        pd.DataFrame,
    nama_komoditas: str,
    use_weekly:     bool = False,
) -> None:
   
    judul_grafik = (
        f"Grafik Harga {nama_komoditas} (Mingguan)"
        if use_weekly
        else f"Grafik Harga {nama_komoditas}"
    )

    with st.expander(judul_grafik):
        df_hist_plot = data_model[["Tanggal", "Harga"]].rename(
            columns={"Harga": "Nilai"}
        )
        df_pred_plot = df_pred[["Tanggal", "Harga Prediksi"]].rename(
            columns={"Harga Prediksi": "Nilai"}
        )

        fig, ax = plt.subplots(figsize=(12, 5))

        #Plot historis
        ax.plot(
            df_hist_plot["Tanggal"],
            df_hist_plot["Nilai"],
            label="Data Historis Mingguan" if use_weekly else "Data Historis",
            color="#000000",
            marker="o" if use_weekly else None,
            markersize=3,
            linewidth=1.5,
        )

        #Plot prediksi
        ax.plot(
            df_pred_plot["Tanggal"],
            df_pred_plot["Nilai"],
            label="Prediksi Mingguan" if use_weekly else "Prediksi",
            color="red",
            linestyle="--",
            marker="o",
            markersize=5,
            linewidth=1.8,
        )

        #Format sumbu-X
        if use_weekly:
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b '%y"))
            ax.set_xlabel("Periode (awal minggu)", color="#000000")
        else:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %Y"))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            ax.set_xlabel("Tanggal", color="#000000")

        plt.xticks(rotation=45, ha="right")

        #Garis vertikal pemisah historis ↔ prediksi
        if len(df_pred_plot) > 0:
            batas_prediksi = df_pred_plot["Tanggal"].iloc[0]
            ax.axvline(
                x=batas_prediksi,
                color="gray",
                linestyle=":",
                linewidth=1.2,
                label="Mulai Prediksi",
            )

        ax.set_facecolor("#ffffff")
        fig.patch.set_facecolor("#ffffff")
        ax.tick_params(colors="#000000")
        ax.set_ylabel("Harga (Rp)", color="#000000")
        ax.legend(facecolor="#d1fae5", edgecolor="#166534", labelcolor="#000000")

        # Anotasi mode aktif di pojok kanan atas
        mode_label = "Mode: Mingguan" if use_weekly else "Mode: Harian"
        ax.text(
            0.99, 0.97,
            mode_label,
            transform=ax.transAxes,
            fontsize=8,
            color="black",
            ha="right",
            va="top",
        )

        plt.tight_layout()
        st.pyplot(fig)


#BANNER PERUBAHAN HARGA

def _format_rupiah(nilai: float) -> str:
    """Format angka ke string Rupiah: 'Rp 12.500'"""
    return f"Rp {nilai:,.0f}".replace(",", ".")


def tampil_perubahan_harga(
    data_model:      pd.DataFrame,
    df_pred:         pd.DataFrame,
    nama_komoditas:  str,
    satuan_komoditas: str,
    use_weekly:      bool = False,
) -> None:
  
    judul_expander = (
        "Perubahan Harga Mingguan" if use_weekly else "Perubahan Harga"
    )

    with st.expander(judul_expander):
        last_data = data_model.tail(5)

        if len(last_data) < 5:
            periode_label = "minggu" if use_weekly else "periode"
            st.warning(
                f"Data historis minimal harus 5 {periode_label} untuk "
                f"menampilkan perubahan harga."
            )
            return

        #Format label kolom sesuai granularitas
        if use_weekly:
            tanggal_cols = last_data["Tanggal"].dt.strftime("Mgg %d %b").tolist()
        else:
            tanggal_cols = last_data["Tanggal"].dt.strftime("%d %b").tolist()

        harga_cols = last_data["Harga"].tolist()

        harga_prediksi = df_pred["Harga Prediksi"].iloc[0]
        harga_terakhir = harga_cols[-1]

        perubahan = (
            (harga_prediksi - harga_terakhir) / harga_terakhir * 100
            if harga_terakhir != 0 else 0.0
        )

        #Label kolom prediksi
        if use_weekly:
            n_minggu_pred  = len(df_pred)
            label_prediksi = (
                f"Prediksi {n_minggu_pred} Mgg"
                if n_minggu_pred > 1
                else "Prediksi Mgg Depan"
            )
            label_waktu_pred = (
                f" {n_minggu_pred} minggu ke depan"
                if n_minggu_pred > 1
                else " minggu depan"
            )
        else:
            label_prediksi   = "Prediksi"
            label_waktu_pred = ""

        if perubahan > 0:
            status, deskripsi     = "naik",  "Kenaikan"
            bg_banner, border_banner = "#EAF3DE", "#a7f3d0",
            bg_circle              = "#a7f3d0"
            warna_judul, warna_sub = "#000000", "#000000"
            svg_ikon = (
                '<svg width="22" height="22" viewBox="0 0 22 22" fill="none">'
                '<path d="M11 17V5M11 5L5.5 10.5M11 5L16.5 10.5" '
                'stroke="#27500A" stroke-width="2" stroke-linecap="round" '
                'stroke-linejoin="round"/></svg>'
            )
        elif perubahan < 0:
            status, deskripsi     = "turun", "Penurunan"
            bg_banner, border_banner = "#FCEBEB", "#FF0000"
            bg_circle              = "#FF0000"
            warna_judul, warna_sub = "#000000", "#000000"
            svg_ikon = (
                '<svg width="22" height="22" viewBox="0 0 22 22" fill="none">'
                '<path d="M11 5V17M11 17L5.5 11.5M11 17L16.5 11.5" '
                'stroke="#791F1F" stroke-width="2" stroke-linecap="round" '
                'stroke-linejoin="round"/></svg>'
            )
        else:
            status, deskripsi     = "tetap", "Tidak ada perubahan signifikan"
            bg_banner, border_banner = "#F1EFE8", "#B4B2A9"
            bg_circle              = "#D3D1C7"
            warna_judul, warna_sub = "#2C2C2A", "#5F5E5A"
            svg_ikon = (
                '<svg width="22" height="22" viewBox="0 0 22 22" fill="none">'
                '<path d="M4 11H18" stroke="#444441" stroke-width="2" '
                'stroke-linecap="round"/>'
                '<path d="M4 7.5H18" stroke="#444441" stroke-width="2" '
                'stroke-linecap="round" opacity=".35"/>'
                '<path d="M4 14.5H18" stroke="#444441" stroke-width="2" '
                'stroke-linecap="round" opacity=".35"/></svg>'
            )

        #Tabel ringkasan
        df_perubahan = pd.DataFrame({
            "Komoditas":       [nama_komoditas],
            "Satuan":          [satuan_komoditas],
            tanggal_cols[0]:   [_format_rupiah(harga_cols[0])],
            tanggal_cols[1]:   [_format_rupiah(harga_cols[1])],
            tanggal_cols[2]:   [_format_rupiah(harga_cols[2])],
            tanggal_cols[3]:   [_format_rupiah(harga_cols[3])],
            tanggal_cols[4]:   [_format_rupiah(harga_cols[4])],
            label_prediksi:    [_format_rupiah(harga_prediksi)],
            "Perubahan (%)":   [f"{perubahan:.2f}%"],
        })
        st.dataframe(
            df_perubahan.style.set_properties(**STYLE_TABEL),
            use_container_width=True,
        )

        #Banner visual
        referensi_waktu = "minggu ini" if use_weekly else "terakhir"
        teks_sub = (
            f"dari harga {referensi_waktu}"
            if perubahan == 0
            else (
                f"sebesar <strong>{abs(perubahan):.2f}%</strong> "
                f"dari harga {referensi_waktu}"
            )
        )
        st.markdown(
            f"""<div style="border-radius:12px;padding:1rem 1.25rem;
                background:{bg_banner};border:0.5px solid {border_banner};
                display:flex;align-items:center;gap:14px;margin-top:0.5rem;">
                <div style="width:44px;height:44px;border-radius:50%;
                    background:{bg_circle};display:flex;align-items:center;
                    justify-content:center;flex-shrink:0;">{svg_ikon}</div>
                <div>
                    <div style="font-size:15px;font-weight:500;color:{warna_judul};">
                        Harga {nama_komoditas}{label_waktu_pred} diprediksi {status}</div>
                    <div style="font-size:13px;color:{warna_sub};margin-top:2px;">
                        {deskripsi} {teks_sub}</div>
                </div></div>""",
            unsafe_allow_html=True,
        )