# Python imports
import os
import json
import base64
import xml.etree.ElementTree as ET


ATR_HIST = './atr'
ATR_PROC = './atr-proc'
INPUT = './input/invoices.txt'
LOGS = './logs'
FOLDERS = ['2023_01', '2023_02', '2023_03', '2023_04', '2023_05', '2023_06']

ERRORS = []
RESULTS = []
INVOICES_TO_FIND = []

# Leer JSON
def read_json (filename):
    fileRead = False
    data = None
    try_encodings = ['ISO-8859-1', 'UTF-8', 'UTF-8-SIG']
    for encoding in try_encodings:
        try:
            with open(filename, 'r', encoding=encoding, errors='ignore') as file:
                data = json.load(file)
            fileRead = True
        except:
            continue
    if fileRead is not True:
        ERRORS.append({
            'json': filename,
            'filename': '-',
            'error': f"Error reading json"
        })
    return data

# Leer XML
def read_xml (filename):
    try_encodings = ['ISO-8859-1', 'UTF-8', 'UTF-8-SIG']
    for encoding in try_encodings:
        try:
            with open(filename, 'r', encoding=encoding, errors='ignore') as file:
                ns = {'ns': 'http://localhost/elegibilidad'}
                xml_content = file.read()
                root = ET.fromstring(xml_content)
                invoice = root.find('.//ns:CodigoFiscalFactura', namespaces=ns)
                return invoice.text if invoice is not None else None
        except:
            continue
    ERRORS.append({
        'xml': filename,
        'filename': '-',
        'error': f"Error reading xml"
    })

# Extraer número de factura del XML
def extract_invoice_info(entry):
    # En algunos ficheros viene como 'content' en otros 'Content'
    content_b64 = ''
    try:
        content_b64 = entry['content']
    except:
        content_b64 = entry['Content']
    # Decodificar content b64 para obtener el XML       
    try:
        xml_content = base64.b64decode(content_b64)#.decode('UTF-8')
    except:
        print('Error')
    ns = {'ns': 'http://localhost/elegibilidad'}
    root = ET.fromstring(xml_content)
    invoice = root.find('.//ns:CodigoFiscalFactura', namespaces=ns)
    return invoice.text if invoice is not None else None

# Buscar facturas en el JSON
def find_invoices(data, invoice_numbers, json):
    invoices_found = []    
    for entry in data['files']:
        try:
            invoice_number = extract_invoice_info(entry)
            if invoice_number is not None and invoice_number in invoice_numbers:
                invoices_found.append({
                    'invoice': invoice_number,
                    'path': entry['path'], 
                    'fileName': entry['fileName'],
                    'documentumId': entry['documentumId'],
                    'json': json
                })
        except:
            ERRORS.append({
                'json': json,
                'filename': entry['fileName'],
                'error': f"Error decoding content"
            })
            continue
    return invoices_found

# Buscar facturas en todos los JSON de un directorio
def check_folder(folder):
    for json in os.listdir(f"{ATR_HIST}/{folder}"):
            if json.endswith('.json'):
                data = read_json(os.path.join(f"{ATR_HIST}/{folder}", json))   
                if data:
                    invoices_in_file = find_invoices(data, INVOICES_TO_FIND, json)
                    RESULTS.extend(invoices_in_file)

# Buscar en atr-hist las facturas
def buscar_atr_hist():

    # Find invoices
    with open(INPUT, 'r') as f:
        INVOICES_TO_FIND = [line.strip() for line in f]
        
    # Check all folders
    for folder in FOLDERS:
        check_folder(folder)
        
    # Write results
    with open(f"{LOGS}/results.log", 'w') as f:
        for result in RESULTS:
            f.write(f"{result['invoice']}#_#{result['path']}{result['fileName']}#_#{result['documentumId']}#_#{result['json']} \n")
    
    # Write logs     
    with open(f"{LOGS}/error.log", 'w') as f:
        for error in ERRORS:
            f.write(f"{error['json']}\t{error['filename']}\t{error['error']}\n")
            
# Buscar en atr-hist las facturas
def buscar_atr_proc():
    for xml in os.listdir(f"{ATR_PROC}"):
        if xml.endswith('.xml') or xml.endswith('.XML'):
            data = read_xml(os.path.join(f"{ATR_PROC}", xml))   
            if data:
                RESULTS.append({
                    'filename': xml,
                    'factura': data
                })
    
    # Write results
    with open(f"{LOGS}/results.log", 'w') as f:
        for result in RESULTS:
            f.write(f"{result['filename']}#_#{result['factura']}\n")
    
    # Write logs     
    with open(f"{LOGS}/error.log", 'w') as f:
        for error in ERRORS:
            f.write(f"{error['xml']}\t{error['filename']}\t{error['error']}\n")
                
# Example usage:
if __name__ == '__main__':

    # Muestra el menú para que el usuario seleccione una opción
    options = ["Buscar facturas en atr-hist", "Obtener codigo fiscal factura de XMLs en atr-proc"]
    print("Selecciona una opción:")
    for index, option in enumerate(options, start=1):
        print(f"{index}. {option}")
    choice = int(input("Introduzca su opción (1 o 2): "))
    
    if choice == 1:
        buscar_atr_hist()
    elif choice == 2:
        buscar_atr_proc()
