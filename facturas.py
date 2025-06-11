import requests
import pandas as pd
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta

# Configuración
email = "visar2980@gmail.com"
api_key = "5faf71c35aaee134b545"
start_date = datetime.strptime("2025-05-07", "%Y-%m-%d")
end_date = datetime.now()  # Fecha actual automática
auth = HTTPBasicAuth(email, api_key)

# Listas para almacenar datos
all_invoices = []
invoice_items_details = []

print(f"🔍 Consultando facturas desde {start_date.strftime('%Y-%m-%d')} hasta {end_date.strftime('%Y-%m-%d')}")

# Consulta a la API
current_date = start_date
while current_date <= end_date:
    date_str = current_date.strftime("%Y-%m-%d")
    print(f"📅 Procesando fecha: {date_str}", end="\r")
    
    try:
        response = requests.get(
            f"https://api.alegra.com/api/v1/invoices?date={date_str}",
            headers={"accept": "application/json"},
            auth=auth,
            timeout=30
        )

        if response.status_code == 200:
            invoices = response.json()
            
            for invoice in invoices:
                # Datos principales de la factura
                invoice_data = {
                    'id': invoice.get('id'),
                    'date': invoice.get('date'),
                    'dueDate': invoice.get('dueDate'),
                    'status': invoice.get('status'),
                    'number': invoice.get('numberTemplate', {}).get('fullNumber'),
                    'client_name': invoice.get('client', {}).get('name'),
                    'seller_name': invoice.get('seller', {}).get('name') if invoice.get('seller') else 'SIN VENDEDOR', # Nuevo campo
                    'paymentMethod': invoice.get('paymentMethod'),  # Nuevo campo
                    'total': invoice.get('total'),
                    'balance': invoice.get('balance'),
                    'observations': invoice.get('observations')
                }
                
                # Procesar items de la factura
                for item in invoice.get('items', []):
                    item_details = {
                        'invoice_id': invoice.get('id'),
                        'item_name': item.get('name'),
                        'item_price': item.get('price'),
                        'item_quantity': item.get('quantity'),
                        'item_total': item.get('total'),
                        'item_reference': item.get('reference'),
                        'item_description': item.get('description')
                    }
                    invoice_items_details.append(item_details)
                
                all_invoices.append(invoice_data)
        
        else:
            print(f"\n⚠️ Error en {date_str}: {response.status_code} - {response.text}")
    
    except Exception as e:
        print(f"\n❌ Error al procesar {date_str}: {str(e)}")
    
    current_date += timedelta(days=1)

# Crear DataFrames
if all_invoices:
    df_invoices = pd.json_normalize(all_invoices)
    df_items = pd.DataFrame(invoice_items_details)

    # Unir los datos
    df_final = pd.merge(
        df_invoices,
        df_items,
        left_on='id',
        right_on='invoice_id',
        how='left'
    ).drop('invoice_id', axis=1)

    # Convertir tipos de datos
    date_columns = ['date', 'dueDate']
    for col in date_columns:
        df_final[col] = pd.to_datetime(df_final[col])
    
    numeric_columns = ['item_price', 'item_quantity', 'item_total', 'total', 'balance']
    for col in numeric_columns:
        df_final[col] = pd.to_numeric(df_final[col], errors='coerce')

    # Guardar en Excel
    output_file = f"facturas_alegra.xlsx"
    df_final.to_excel(output_file, index=False)
    
    print(f"\n✅ Archivo '{output_file}' generado con éxito")
    print(f"📊 Facturas procesadas: {len(df_invoices)}")
    print(f"🛒 Ítems registrados: {len(df_items)}")
    print(f"📅 Rango cubierto: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
else:
    print("\n❌ No se encontraron facturas en el rango especificado")