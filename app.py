import streamlit as st
import pandas as pd

from config import PAGE_TITLE, PAGE_LAYOUT, CUSTOM_CSS

from preprocessing import (
    preprocess_data,
    bangun_data_model,
    deteksi_komoditas,
)

from fuzzy_model import FuzzyTimeSeriesChen

from evaluation import hitung_insample

from ui_components import (
    upload_file_sidebar,
    resample_sidebar,
    date_range_sidebar,
    tampil_pesan_sukses,
    tampil_info_outlier,
    tampil_info_agregasi,
    tampil_data_historis,
    tampil_himpunan_semesta,
    tampil_panjang_interval,
    tampil_fuzzifikasi,
    tampil_flr,
    tampil_flrg,
    tampil_hasil_prediksi,
    tampil_evaluasi_mape,
    tampil_grafik,
    tampil_perubahan_harga,
)

st.set_page_config(page_title=PAGE_TITLE, layout=PAGE_LAYOUT)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def main() -> None:
    
    st.title("Sistem Prediksi Harga Sembako Dengan FTS Model Chen")

    if "model" not in st.session_state:
        st.session_state.model = FuzzyTimeSeriesChen()
    model: FuzzyTimeSeriesChen = st.session_state.model

    uploaded_file = upload_file_sidebar()

    if not uploaded_file:
        st.markdown(
            """<div style="padding:0.8rem;border-radius:8px;
            background-color:#a7f3d0;border:2px solid #a7f3d0;
            color:#14532d;font-weight:500;font-size:1.1rem;">
            Silakan upload file CSV terlebih dahulu melalui sidebar.
            </div>""",
            unsafe_allow_html=True,
        )
        return

    try:
        df_raw = pd.read_csv(uploaded_file, header=None)

        # Reset model setiap kali file baru diupload agar state bersih
        st.session_state.model = FuzzyTimeSeriesChen()
        model = st.session_state.model

        data = preprocess_data(df_raw)

        # Deteksi nama komoditas dan satuan dari nama file
        info_komoditas   = deteksi_komoditas(uploaded_file.name)
        nama_komoditas   = info_komoditas["nama"]
        satuan_komoditas = info_komoditas["satuan"]

        tampil_pesan_sukses(
            f"File berhasil diupload! "
            f"Komoditas terdeteksi: <strong>{nama_komoditas}</strong> "
            f"(satuan: {satuan_komoditas})"
        )
        st.divider()

        # Opsi preprocessing dari sidebar
        use_outlier_cap, use_weekly = resample_sidebar()

        # Agregasi mingguan
        data_model, outlier_info = bangun_data_model(
            data, use_weekly, use_outlier_cap
        )

        # Hasil preprocessing
        tampil_info_outlier(outlier_info, use_outlier_cap)
        tampil_info_agregasi(use_weekly, len(data), len(data_model))

        # rentang & jumlah periode prediksi
        data_start = data_model["Tanggal"].min()
        data_end   = data_model["Tanggal"].max()
        
        start_date, end_date = date_range_sidebar(data_start, data_end, use_weekly)

        if use_weekly:
            days_to_predict = ((end_date - start_date).days + 1) // 7
        else:
            days_to_predict = (end_date - start_date).days + 1

        tampil_data_historis(data_model, use_weekly)

        if start_date <= data_end:
            st.warning(
                "Silakan pilih tanggal setelah data terakhir untuk memulai prediksi."
            )
            return

        if not st.button("Prediksi"):
            return

        model.create_intervals(data_model)
        model.create_flrg(data_model)

        model.predict(data_model, days_to_predict)

        if not model.universe_info or "D1" not in model.universe_info:
            st.error(
                "Terjadi kesalahan internal: interval belum terbentuk. "
                "Klik Prediksi kembali."
            )
            return

        tampil_himpunan_semesta(model.universe_info)
        tampil_panjang_interval(model.universe_info, model.intervals, model.labels)
        tampil_fuzzifikasi(model.fuzzy_data)
        tampil_flr(model.flr)
        tampil_flrg(model.FLRG)

        df_pred = tampil_hasil_prediksi(model.df_prediksi, start_date, days_to_predict, use_weekly)
        if df_pred is None:
            return

        hasil_eval = hitung_insample(model)
        tampil_evaluasi_mape(
            mape=hasil_eval["mape"],
            kategori=hasil_eval["kategori"],
            use_weekly=use_weekly,
        )

        tampil_grafik(data_model, df_pred, nama_komoditas, use_weekly)
        tampil_perubahan_harga(data_model, df_pred, nama_komoditas, satuan_komoditas, use_weekly)

    except ValueError as ve:
        st.error(f"Format data tidak valid: {str(ve)}")
    except Exception as e:
        st.error(f"Terjadi error: {str(e)}")

if __name__ == "__main__":
    main()