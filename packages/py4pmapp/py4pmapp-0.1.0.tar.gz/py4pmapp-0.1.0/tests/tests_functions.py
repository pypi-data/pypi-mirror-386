import pandas as pd
from py4pmapp import limpiar_nulos, eliminar_duplicados, convertir_fechas, normalizar_columna

def test_limpieza():
    df = pd.DataFrame({"a": [1, None, 3], "b": [4, 5, None]})
    assert limpiar_nulos(df).shape[0] == 1

def test_duplicados():
    df = pd.DataFrame({"a": [1, 1, 2], "b": [3, 3, 4]})
    assert eliminar_duplicados(df).shape[0] == 2

def test_fechas():
    df = pd.DataFrame({"fecha": ["2025-01-01", "invalid"]})
    df2 = convertir_fechas(df, "fecha")
    assert pd.isna(df2.loc[1, "fecha"])

def test_normalizar():
    df = pd.DataFrame({"val": [0, 5, 10]})
    df2 = normalizar_columna(df, "val")
    assert df2["val"].iloc[-1] == 1.0
