import requests
import pandas as pd
from datetime import datetime
import base64


# ===== CONFIGURACIÓN =====
USUARIO_ALEGRA = "visar2980@gmail.com"   # Tu email de Alegra
TOKEN_ALEGRA = "5faf71c35aaee134b545"     # Tu token API de Alegra

ARCHIVO_EXCEL = "compras_drogueria.xlsx"


# ========= FUNCIONES =========

def obtener_headers():
    cred = f"{USUARIO_ALEGRA}:{TOKEN_ALEGRA}"
    b64 = base64.b64encode(cred.encode()).decode()
    return {
        "Authorization": f"Basic {b64}",
        "Content-Type": "application/json"
    }


def obtener_compras():
    url = "https://api.alegra.com/api/v1/bills"
    headers = obtener_headers()

    compras = []
    start = 0
    limit = 30

    print("Descargando facturas de compra...")

    while True:
        params = {"start": start, "limit": limit}
        r = requests.get(url, headers=headers, params=params)

        if r.status_code != 200:
            print("Error en API Alegra:", r.text)
            break

        data = r.json()
        if not data:
            break

        compras.extend(data)
        print(f"  → Descargadas {len(compras)} compras...")

        if len(data) < limit:
            break

        start += limit

    return compras


def procesar_compras(compras_raw):
    registros = []

    print("Procesando información...")

    for compra in compras_raw:

        proveedor = compra.get("provider", {}).get("name", "")
        proveedor_id = compra.get("provider", {}).get("id", "")

        # === AQUI ESTA LA CLAVE ===
        items = compra.get("purchases", {}).get("items", [])

        # Si no tiene items
        if not items:
            registros.append({
                "Fecha": compra.get("date", ""),
                "Numero_Factura": compra.get("numberTemplate", {}).get("fullNumber", ""),
                "Proveedor": proveedor,
                "ID_Proveedor": proveedor_id,
                "Producto": "SIN ITEMS",
                "ID_Producto": "",
                "Cantidad": 0,
                "Precio_Unitario": 0,
                "Total_Item": 0,
                "Total_Factura": compra.get("total", 0)
            })
            continue

        # Procesar items reales
        for item in items:
            registros.append({
                "Fecha": compra.get("date", ""),
                "Numero_Factura": compra.get("numberTemplate", {}).get("fullNumber", ""),
                "Proveedor": proveedor,
                "ID_Proveedor": proveedor_id,
                "Producto": item.get("name", ""),
                "ID_Producto": item.get("id", ""),
                "Cantidad": item.get("quantity", 0),
                "Precio_Unitario": item.get("price", 0),
                "Total_Item": item.get("total", 0),
                "Total_Factura": compra.get("total", 0)
            })

    print(f"  → Total líneas procesadas: {len(registros)}")
    return registros


def generar_excel(registros):
    if not registros:
        print("⚠ No hay datos para generar Excel.")
        return

    df = pd.DataFrame(registros)

    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df = df.sort_values("Fecha", ascending=False)

    with pd.ExcelWriter(ARCHIVO_EXCEL, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Compras_Detalle", index=False)
        df.groupby("Proveedor")["Total_Item"].sum().to_excel(writer, sheet_name="Resumen_Proveedores")
        df.groupby("Producto")["Total_Item"].sum().to_excel(writer, sheet_name="Resumen_Productos")

    print("\n✅ Archivo generado:", ARCHIVO_EXCEL)


# ========= MAIN =========

def main():
    compras = obtener_compras()

    if not compras:
        print("No se encontraron compras.")
        return

    registros = procesar_compras(compras)
    generar_excel(registros)


if __name__ == "__main__":
    main()
