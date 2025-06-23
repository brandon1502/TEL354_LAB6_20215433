import requests
import json

# IP del controlador
controller_ip = "localhost"  # O puedes usar "localhost"
headers = {'Content-type': 'application/json', 'Accept': 'application/json'}

def get_attachement_points(mac):
    # Consulta a todos los dispositivos y busca la MAC
    url = f"http://{controller_ip}:8080/wm/device/"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        encontrados = False
        for host in data:
            if mac.lower() in [m.lower() for m in host.get("mac", [])]:
                encontrados = True
                aps = host.get("attachmentPoint", [])
                print("\n[✓] MAC encontrada - Attachment Point:")
                if aps:
                    for ap in aps:
                        print(f"Switch DPID: {ap['switchDPID']}, Puerto: {ap['port']}")
                else:
                    print("⚠️ No se encontraron puntos de conexión para esa MAC.")
        if not encontrados:
            print("[!] No se encontró ningún host con esa MAC.")
    else:
        print(f"[✗] Error en la consulta. Código: {response.status_code}")


def get_route(dpid1, port1, dpid2, port2):
    url = f"http://{controller_ip}:8080/wm/topology/route/{dpid1}/{port1}/{dpid2}/{port2}/json"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("\n[✓] Consulta exitosa - Ruta entre switches")
        data = response.json()
        if data:
            print("Ruta:")
            for hop in data:
                print(f"Switch DPID: {hop['switch']}, Puerto: {hop['port']}")
        else:
            print("No se encontró una ruta entre esos puntos.")
    else:
        print(f"[✗] Error en la consulta. Código: {response.status_code}")


if __name__ == "__main__":
    print("CONSULTA FLOODLIGHT API")
    print("1. Obtener Attachment Point de una MAC")
    print("2. Obtener Ruta entre switches")
    opcion = input("\nSelecciona una opción (1 o 2): ")

    if opcion == "1":
        mac = input("Ingresa la dirección MAC del host: ").strip().lower()
        get_attachement_points(mac)

    elif opcion == "2":
        dpid1 = input("DPID de origen: ").strip()
        port1 = input("Puerto de origen: ").strip()
        dpid2 = input("DPID de destino: ").strip()
        port2 = input("Puerto de destino: ").strip()
        get_route(dpid1, port1, dpid2, port2)

    else:
        print("[!] Opción inválida")

