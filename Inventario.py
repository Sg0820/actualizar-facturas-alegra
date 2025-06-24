import requests
import pandas as pd
from requests.auth import HTTPBasicAuth
from tqdm import tqdm
import time

# Configuración
email = "visar2980@gmail.com"
api_key = "5faf71c35aaee134b545"
auth = HTTPBasicAuth(email, api_key)
BASE_URL = "https://api.alegra.com/api/v1"
HEADERS = {"accept": "application/json"}

def get_all_items():
    """Obtiene todos los items del inventario con paginación"""
    items = []
    page = 1
    print("🔍 Descargando items del inventario...")
    
    with tqdm(desc="Progreso") as pbar:
        while True:
            try:
                response = requests.get(
                    f"{BASE_URL}/items",
                    params={"start": (page-1)*30, "limit": 30, "includeInventory": "true"},
                    headers=HEADERS,
                    auth=auth,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict):
                        if 'data' in data:
                            data = data['data']
                        else:
                            data = [data]
                    
                    if not data or not isinstance(data, list):
                        break
                    
                    items.extend(data)
                    pbar.update(len(data))
                    page += 1
                    time.sleep(0.1)
                else:
                    print(f"\n⚠️ Error: {response.status_code} - {response.text}")
                    break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                break
    
    return items

def extract_price(price_data):
    """Extrae el precio de la estructura compleja"""
    if isinstance(price_data, list) and len(price_data) > 0:
        return price_data[0].get('price')
    elif isinstance(price_data, dict):
        return price_data.get('price')
    return None

def extract_tax(tax_data):
    """Extrae el porcentaje de impuesto de la estructura compleja"""
    if isinstance(tax_data, list) and len(tax_data) > 0:
        return tax_data[0].get('percentage')
    elif isinstance(tax_data, dict):
        return tax_data.get('percentage')
    return None

def extract_inventory(item_data):
    """Extrae la información de inventario del item"""
    inventory = item_data.get('inventory', {})
    return {
        'available': inventory.get('availableQuantity', 0),
        'committed': inventory.get('committedQuantity', 0),
        'on_hand': inventory.get('onHandQuantity', 0),
        'initial': item_data.get('initialQuantity', 0)
    }

def main():
    try:
        # 1. Obtener todos los items con información de inventario
        items = get_all_items()
        
        if not items:
            print("❌ No se encontraron items en el inventario")
            return
        
        # 2. Procesar datos de items
        items_data = []
        for item in tqdm(items, desc="Procesando items"):
            if not isinstance(item, dict):
                continue
                
            inventory = extract_inventory(item)
            
            items_data.append({
                'ID': item.get('id'),
                'Nombre': item.get('name'),
                'Referencia': item.get('reference'),
                'Descripción': item.get('description'),
                'Precio': extract_price(item.get('price')),
                'Categoría': item.get('category', {}).get('name'),
                'Tipo': item.get('type'),
                'Estado': item.get('status'),
                'Disponible': inventory['available'],
                'Comprometido': inventory['committed'],
                'En mano': inventory['on_hand'],
                'Cantidad Inicial': inventory['initial'],
                'Impuesto %': extract_tax(item.get('tax')),
                'Clave Producto': item.get('productKey')
            })
        
        # 3. Crear DataFrame
        df_items = pd.DataFrame(items_data)
        
        # 4. Ordenar columnas
        item_columns = ['ID', 'Nombre', 'Referencia', 'Descripción', 'Precio', 
                       'Disponible', 'Comprometido', 'En mano', 'Cantidad Inicial',
                       'Categoría', 'Tipo', 'Estado', 'Impuesto %', 'Clave Producto']
        df_items = df_items[item_columns]
        
        # 5. Guardar en Excel
        output_file = 'inventario_alegra.xlsx'
        df_items.to_excel(output_file, index=False)
        
        print(f"\n✅ Archivo '{output_file}' generado con éxito!")
        print(f"📦 Total items: {len(df_items)}")
        print(f"📊 Unidades disponibles: {df_items['Disponible'].sum()}")
        print(f"📊 Unidades comprometidas: {df_items['Comprometido'].sum()}")
    
    except Exception as e:
        print(f"\n❌ Error fatal: {str(e)}")

if __name__ == "__main__":
    main()
