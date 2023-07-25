# Python imports
import os
import json
import base64
import xml.etree.ElementTree as ET


ATR = './atr'
INPUT = './input/invoices.txt'
LOGS = './logs'
FOLDERS = ['2023_01', '2023_02', '2023_03', '2023_04', '2023_05', '2023_06']

ERRORS = []
RESULTS = []

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

# Extraer número de factura del XML
def extract_invoice_info(xml_base64):
    xml_content = base64.b64decode(xml_base64).decode('ISO-8859-1')
    ns = {'ns': 'http://localhost/elegibilidad'}
    root = ET.fromstring(xml_content)
    invoice = root.find('.//ns:CodigoFiscalFactura', namespaces=ns)
    return invoice.text if invoice is not None else None

# Buscar facturas en el JSON
def find_invoices(data, invoice_numbers, json):
    invoices_found = []
    for entry in data['files']:
        try:
            invoice_number = extract_invoice_info(entry['Content'])
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

    for json in os.listdir(f"{ATR}/{folder}"):
            if json.endswith('.json'):
                data = read_json(os.path.join(f"{ATR}/{folder}", json))   
                if data:
                    invoices_in_file = find_invoices(data, invoice_numbers_to_find, json)
                    RESULTS.extend(invoices_in_file)

    # Write results
    with open(f"{LOGS}/{folder}_results.log", 'w') as f:
        for result in RESULTS:
            f.write(f"{result['invoice']}\t\t{result['path']}{result['fileName']}\t\t{result['documentumId']}\t\t{result['json']} \n")
    
    # Write logs     
    with open(f"{LOGS}/{folder}_error.log", 'w') as f:
        for error in ERRORS:
            f.write(f"{error['json']}\t\t{error['filename']}\t\t{error['error']}\n")

# Example usage:
if __name__ == '__main__':

    # Find invoices
    with open(INPUT, 'r') as f:
        invoice_numbers_to_find = [line.strip() for line in f]
        
    for folder in FOLDERS:
        check_folder(folder)
