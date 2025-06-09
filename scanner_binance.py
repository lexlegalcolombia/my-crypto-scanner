import requests
import pandas as pd
import time
from datetime import datetime
import streamlit as st

# --- Tu código existente para criptos, columnas, get_klines, analizar_5m, analizar_1h ---
criptos = [
    "BTC", "ETH", "SOL", "DOGE", "XRP", "TRUMP", "MOODENG", "WIF", "WLD",
    "FARTCOIN", "NXPC", "NEIRO", "LINK", "AVAX", "VIRTUAL", "LTC", "UNI",
    "TIA", "BCH", "CRV", "DOT", "ETHFI", "LAYER", "NEAR", "POPCAT", "INIT",
    "INJ", "KAITO", "FIL", "GOAT", "SUI", "ORDI", "APT", "XLM", "ETC",
    "MASK", "TON", "BERA", "PENDLE", "FORM", "JTO", "VANA", "SAFE",
    "ADA", "ASR", "AUCTION", "BANANA", "ORCA", "YFI", "VVV", "OG", "GAS",
    "PROM", "QTUM", "GMX", "ETHW", "DEXE", "XVS", "DEGO", "SANTOS", "EIGEN", "SPX", "WCT", "LPT", "NMR", "MLN", "RLC"
]

columnas = [
    "ID", "PRECIO", "% 5MIN", "% 1H", "% 24H",
    "3/9 UP 5M", "3/9 DOWN 5M", "3/9 UP 1H", "3/9 DOWN 1H",
    "BBT 1H", "BBB 1H", "GUIA UP 1H", "GUIA DOWN 1H",
    "GUIA UP 1D", "GUIA DOWN 1D"
]

def get_klines(symbol, interval, limit):
    symbol_binance = symbol.upper() + "USDT"
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol_binance}&interval={interval}&limit={limit}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades", "taker_buy_base",
        "taker_buy_quote", "ignore"
    ])
    df[["open", "close", "high", "low"]] = df[["open", "close", "high", "low"]].astype(float)
    return df

def analizar_5m(df):
    df['EMA3'] = df['close'].ewm(span=3).mean()
    df['EMA9'] = df['close'].ewm(span=9).mean()
    cruces_up = df['EMA3'].iloc[-2] < df['EMA9'].iloc[-2] and df['EMA3'].iloc[-1] > df['EMA9'].iloc[-1]
    cruces_down = df['EMA3'].iloc[-2] > df['EMA9'].iloc[-2] and df['EMA3'].iloc[-1] < df['EMA9'].iloc[-1]
    return cruces_up, cruces_down

def analizar_1h(df):
    df['EMA3'] = df['close'].ewm(span=3).mean()
    df['EMA9'] = df['close'].ewm(span=9).mean()
    df['EMA20'] = df['close'].ewm(span=20).mean()

    cruces_up = df['EMA3'].iloc[-2] < df['EMA9'].iloc[-2] and df['EMA3'].iloc[-1] > df['EMA9'].iloc[-1]
    cruces_down = df['EMA3'].iloc[-2] > df['EMA9'].iloc[-2] and df['EMA3'].iloc[-1] < df['EMA9'].iloc[-1]

    std = df['close'].rolling(window=20).std()
    boll_upper = df['EMA20'] + (2 * std)
    boll_lower = df['EMA20'] - (2 * std)
    banda_top = df['close'].iloc[-1] > boll_upper.iloc[-1]
    banda_down = df['close'].iloc[-1] < boll_lower.iloc[-1]

    # --- Analizar la VELA ANTERIOR CERRADA (iloc[-2]) ---
    open_candle_prev = df['open'].iloc[-2]
    close_candle_prev = df['close'].iloc[-2]
    low_candle_prev = df['low'].iloc[-2]
    high_candle_prev = df['high'].iloc[-2]

    ema3_val_prev = df['EMA3'].iloc[-2]
    ema9_val_prev = df['EMA9'].iloc[-2]
    ema20_val_prev = df['EMA20'].iloc[-2]

    # Condición de "tocado" para EMA3, EMA9, EMA20 en la VELA ANTERIOR (dentro del rango low-high)
    emas_tocadas_prev = (low_candle_prev <= ema3_val_prev <= high_candle_prev and
                         low_candle_prev <= ema9_val_prev <= high_candle_prev and
                         low_candle_prev <= ema20_val_prev <= high_candle_prev)

    # --- Lógica de Vela Guía Refinada ---
    vela_up = False
    vela_down = False

    # Vela Guía UP: Vela alcista, abre por debajo de EMA20 y cierra por encima de EMA20, tocando todas las EMAs
    if (close_candle_prev > open_candle_prev and # Vela alcista (cierre > apertura)
        open_candle_prev < ema20_val_prev and   # Apertura por debajo de EMA20
        close_candle_prev > ema20_val_prev and  # Cierre por encima de EMA20
        emas_tocadas_prev):                     # Las EMAs están dentro del rango de la vela
        vela_up = True

    # Vela Guía DOWN: Vela bajista, abre por encima de EMA20 y cierra por debajo de EMA20, tocando todas las EMAs
    if (close_candle_prev < open_candle_prev and # Vela bajista (cierre < apertura)
        open_candle_prev > ema20_val_prev and   # Apertura por encima de EMA20
        close_candle_prev < ema20_val_prev and  # Cierre por debajo de EMA20
        emas_tocadas_prev):                     # Las EMAs están dentro del rango de la vela
        vela_down = True

    return cruces_up, cruces_down, banda_top, banda_down, vela_up, vela_down

# --- Nueva función para analizar la temporalidad diaria (1D) ---
def analizar_1d(df):
    df['EMA3'] = df['close'].ewm(span=3).mean()
    df['EMA9'] = df['close'].ewm(span=9).mean()
    df['EMA20'] = df['close'].ewm(span=20).mean()

    # --- Analizar la VELA ANTERIOR CERRADA (iloc[-2]) ---
    open_candle_prev = df['open'].iloc[-2]
    close_candle_prev = df['close'].iloc[-2]
    low_candle_prev = df['low'].iloc[-2]
    high_candle_prev = df['high'].iloc[-2]

    ema3_val_prev = df['EMA3'].iloc[-2]
    ema9_val_prev = df['EMA9'].iloc[-2]
    ema20_val_prev = df['EMA20'].iloc[-2]

    # Condición de "tocado" para EMA3, EMA9, EMA20 en la VELA ANTERIOR
    emas_tocadas_prev = (low_candle_prev <= ema3_val_prev <= high_candle_prev and
                         low_candle_prev <= ema9_val_prev <= high_candle_prev and
                         low_candle_prev <= ema20_val_prev <= high_candle_prev)
    
    # --- Lógica de Vela Guía Refinada ---
    vela_up = False
    vela_down = False

    # Vela Guía UP: Vela alcista, abre por debajo de EMA20 y cierra por encima de EMA20, tocando todas las EMAs
    if (close_candle_prev > open_candle_prev and # Vela alcista (cierre > apertura)
        open_candle_prev < ema20_val_prev and   # Apertura por debajo de EMA20
        close_candle_prev > ema20_val_prev and  # Cierre por encima de EMA20
        emas_tocadas_prev):                     # Las EMAs están dentro del rango de la vela
        vela_up = True

    # Vela Guía DOWN: Vela bajista, abre por encima de EMA20 y cierra por debajo de EMA20, tocando todas las EMAs
    if (close_candle_prev < open_candle_prev and # Vela bajista (cierre < apertura)
        open_candle_prev > ema20_val_prev and   # Apertura por encima de EMA20
        close_candle_prev < ema20_val_prev and  # Cierre por debajo de EMA20
        emas_tocadas_prev):                     # Las EMAs están dentro del rango de la vela
        vela_down = True

    return vela_up, vela_down

@st.cache_data(ttl=10) # Cachea los datos por 10 segundos para no saturar la API
def obtener_datos():
    datos = []
    for idx, cripto in enumerate(criptos, start=1):
        try:
            # Asegúrate de que el límite sea suficiente para las EMAs y para acceder a iloc[-2]
            df_5m = get_klines(cripto, '5m', 50)
            df_1h = get_klines(cripto, '1h', 50)
            df_1d = get_klines(cripto, '1d', 50)

            # Para el PRECIO y los PORCENTAJES, sí se usa la vela más reciente (iloc[-1])
            precio = df_5m['close'].iloc[-1]
            cambio_5m = ((df_5m['close'].iloc[-1] - df_5m['close'].iloc[-2]) / df_5m['close'].iloc[-2]) * 100
            cambio_1h = ((df_1h['close'].iloc[-1] - df_1h['close'].iloc[-2]) / df_1h['close'].iloc[-2]) * 100
            cambio_24h = ((df_1h['close'].iloc[-1] - df_1h['close'].iloc[-24]) / df_1h['close'].iloc[-24]) * 100 if len(df_1h) >= 25 else 0

            up_5m, down_5m = analizar_5m(df_5m)
            up_1h, down_1h, banda_top, banda_down, vela_up_1h, vela_down_1h = analizar_1h(df_1h)
            vela_up_1d, vela_down_1d = analizar_1d(df_1d)

            fila = [
                cripto, precio, round(cambio_5m, 2), round(cambio_1h, 2), round(cambio_24h, 2),
                "🟢" if up_5m else "🔴", "🟢" if down_5m else "🔴",
                "🟢" if up_1h else "🔴", "🟢" if down_1h else "🔴",
                "🟢" if banda_top else "🔴", "🟢" if banda_down else "🔴",
                "🟢" if vela_up_1h else "🔴", "🟢" if vela_down_1h else "🔴",
                "🟢" if vela_up_1d else "🔴", "🟢" if vela_down_1d else "🔴"
            ]
            datos.append(fila)
        except Exception as e:
            print(f"Error para {cripto}: {e}") # Descomenta esta línea para ver el error en los logs
            fila = [cripto] + ["ERROR"] * (len(columnas) - 1)
            datos.append(fila)
    return pd.DataFrame(datos, columns=columnas)

# --- La aplicación Streamlit ---

st.set_page_config(layout="wide") # Para usar todo el ancho de la pantalla
st.title(f"Scanner de Binance Futures - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- CSS para centrar la tabla y poner negrita los encabezados ---
st.markdown("""
<style>
    /* Centra el texto de todas las celdas de datos (filas) */
    .stDataFrame td {
        text-align: center !important;
    }
    /* Centra el texto y pone en negrita los encabezados de las columnas (primera fila) */
    .stDataFrame th {
        text-align: center !important;
        font-weight: bold !important; /* Pone en negrita los encabezados */
    }
    /* Asegura que los íconos se centren correctamente (puede necesitar ajuste en versiones futuras de Streamlit) */
    .stDataFrame [data-testid="stDataframeCell"] > div {
        display: flex;
        justify-content: center;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

# Crear un placeholder para la tabla que se actualizará
tabla_placeholder = st.empty()

# Bucle para la actualización en "tiempo real"
while True:
    df_scanner = obtener_datos()

    # Formateo de las columnas de porcentaje
    def highlight_percentage(val):
        try:
            val = float(val)
            if val >= 0:
                return 'background-color: #00B050' # Verde más oscuro y sólido
            else:
                return 'background-color: #FF0000' # Rojo más oscuro y sólido
        except:
            return ''

    # Función para poner en negrita la columna 'ID'
    def bold_id_column(row):
        return ['font-weight: bold' if col == 'ID' else '' for col in row.index]

    # Aplicar el estilo condicional a las columnas de porcentaje usando .map
    styled_df = df_scanner.style.map(highlight_percentage, subset=["% 5MIN", "% 1H", "% 24H"])
    
    # Aplicar negrita a la columna 'ID'
    styled_df = styled_df.apply(bold_id_column, axis=1)

    # Mostrar la tabla en el placeholder
    with tabla_placeholder:
        st.dataframe(styled_df, hide_index=True, use_container_width=True)

    st.caption(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")
    time.sleep(10) # Espera 10 segundos antes de la próxima actualización
