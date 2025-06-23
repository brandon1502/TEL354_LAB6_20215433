#!/usr/bin/python3
import requests
from prettytable import PrettyTable

# DEFINE VARIABLES
controller_ip = 'localhost'  # O reemplaza con la IP de tu controlador
target_api = 'wm/core/controller/switches/json'

headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
url = f'http://{controller_ip}:8080/{target_api}'
response = requests.get(url=url, headers=headers)

if response.status_code == 200:
    # SUCCESSFUL REQUEST
    print('SUCCESSFUL REQUEST | STATUS: 200')
    data = response.json()
    table = PrettyTable(data[0].keys())
    for row in data:
        table.add_row(row.values())
    print(table)
else:
    # FAILED REQUEST
    print(f'FAILED REQUEST | STATUS: 200 {response.status_code}')

# FOR QUESTION 1h
# COMPLETE FOR PRINT ALL FLOWS PER SWITCH PID
# FIRST YOU NEED TO ASK USER INPUT A SWITCH PID
# AFTERWARD, BY USING THIS SWITCH PID, YOU SHOULD ASK THE PERTINENT API FOR GET ALL FLOWS PER SWITCH PID AND PRINT THEM (AS ABOVE CODE)

# --- AGREGADO PARA 1.i ---
selected_dpid = input("\nIngrese el DPID del switch para ver sus flows: ").strip()
flow_url = f'http://{controller_ip}:8080/wm/core/switch/{selected_dpid}/flow/json'
flow_response = requests.get(url=flow_url, headers=headers)

if flow_response.status_code == 200:
    print('SUCCESSFUL REQUEST | STATUS: 200')
    flow_data = flow_response.json()

    if flow_data:
        if "flows" in flow_data and isinstance(flow_data["flows"], list) and flow_data["flows"]:
            flows = flow_data["flows"]
            flow_table = PrettyTable(flows[0].keys())
            for flow in flows:
                flow_table.add_row(flow.values())
            print(flow_table)
        else:
            print("No se encontraron flows o el formato no es compatible.")
    else:
        print("El switch no tiene flow entries.")
else:
    print(f'FAILED REQUEST | STATUS: 200 {flow_response.status_code}')

