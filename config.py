KOMODITAS_MAP: dict[str, dict] = {
    "bawang_merah":  {"nama": "Bawang Merah",  "satuan": "kg"},
    "bawangmerah":   {"nama": "Bawang Merah",  "satuan": "kg"},
    "minyak_goreng": {"nama": "Minyak Goreng", "satuan": "liter"},
    "minyakgoreng":  {"nama": "Minyak Goreng", "satuan": "liter"},
    "minyak":        {"nama": "Minyak Goreng", "satuan": "liter"},
    "cabai":         {"nama": "Cabai",         "satuan": "kg"},
    "cabe":          {"nama": "Cabai",         "satuan": "kg"},
    "bawang":        {"nama": "Bawang Merah",  "satuan": "kg"},
    "beras":         {"nama": "Beras",         "satuan": "kg"},
}

WINSORIZE_HARIAN_LOWER:  float = 0.01
WINSORIZE_HARIAN_UPPER:  float = 0.99
WINSORIZE_MINGGUAN_LOWER: float = 0.30
WINSORIZE_MINGGUAN_UPPER: float = 0.70

D1: float = 0.5
D2: float = 0.5

INTERVAL_MIN: int = 20
INTERVAL_MAX: int = 36

STYLE_TABEL: dict[str, str] = {
    "background-color": "#a7f3d0",
    "color":            "#000000",
    "border-color":     "#000000",
}

PAGE_TITLE:  str = "Prediksi Harga Sembako"

PAGE_LAYOUT: str = "wide"

CUSTOM_CSS: str = """
    <style>
        section[data-testid="stSidebar"] {
            background-color: #a7f3d0;
        }

        div.stButton > button {
            background-color: #dc2626;
            color: white;
            border-radius: 8px;
            font-weight: 600;
            border: none;
        }

        div.stButton > button:hover {
            background-color: #b91c1c;
            color: white;
        }
    </style>
"""