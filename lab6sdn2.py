import yaml
import requests
import json

# ==== Clases ====

class Alumno:
    def __init__(self, nombre, codigo, mac):
        self.nombre = nombre
        self.codigo = codigo
        self.mac = mac

class Servicio:
    def __init__(self, nombre, protocolo, puerto):
        self.nombre = nombre
        self.protocolo = protocolo
        self.puerto = puerto

class Servidor:
    def __init__(self, nombre, direccion_ip):
        self.nombre = nombre
        self.direccion_ip = direccion_ip
        self.servicios = []

    def agregar_servicio(self, servicio):
        self.servicios.append(servicio)

    def obtener_servicio(self, nombre):
        for s in self.servicios:
            if s.nombre == nombre:
                return s
        return None

class Curso:
    def __init__(self, codigo, nombre, estado):
        self.codigo = codigo
        self.nombre = nombre
        self.estado = estado
        self.alumnos = []
        self.servidores = {}

    def agregar_alumno(self, cod_alumno):
        if cod_alumno not in self.alumnos:
            self.alumnos.append(cod_alumno)

    def remover_alumno(self, cod_alumno):
        if cod_alumno in self.alumnos:
            self.alumnos.remove(cod_alumno)

    def asignar_servidor(self, servidor, servicios_permitidos):
        servicios_validos = [servidor.obtener_servicio(sv) for sv in servicios_permitidos if servidor.obtener_servicio(sv)]
        self.servidores[servidor.nombre] = {"servidor": servidor, "servicios": servicios_validos}

class Conexion:
    def __init__(self, handler, cod_alumno, nombre_servidor, nombre_servicio):
        self.handler = handler
        self.cod_alumno = cod_alumno
        self.nombre_servidor = nombre_servidor
        self.nombre_servicio = nombre_servicio
        self.ruta = []

    def __str__(self):
        return f"{self.handler}: Alumno {self.cod_alumno} -> Servidor {self.nombre_servidor} ({self.nombre_servicio})"

# ==== Bases de datos ====

alumnos = {}
servidores = {}
cursos = {}
conexiones = {}

# ==== SDN API ====

controller_ip = "localhost"
headers = {'Content-type': 'application/json', 'Accept': 'application/json'}

def get_attachment_point(mac):
    url = f"http://{controller_ip}:8080/wm/device/"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            for host in response.json():
                if mac.lower() in [m.lower() for m in host.get("mac", [])]:
                    aps = host.get("attachmentPoint", [])
                    if aps:
                        return aps[0]['switchDPID'], aps[0]['port']
    except requests.exceptions.ConnectionError:
        print("Error de conexión con el controlador Floodlight.")
    return None, None

def get_route(dpid1, port1, dpid2, port2):
    url = f"http://{controller_ip}:8080/wm/topology/route/{dpid1}/{port1}/{dpid2}/{port2}/json"
    try:
        response = requests.get(url, headers=headers)
        return response.json() if response.status_code == 200 else []
    except requests.exceptions.ConnectionError:
        print(" Error al obtener la ruta del controlador.")
        return []

def insertar_flows(ruta, mac_origen, mac_destino, puerto_destino):
    for i, hop in enumerate(ruta):
        flow = {
            "switch": hop["switch"],
            "name": f"flow_{hop['switch']}_{mac_origen}_{i}",
            "cookie": "0",
            "priority": "32768",
            "in_port": str(hop["port"]),
            "eth_type": "0x0800",
            "eth_src": mac_origen,
            "eth_dst": mac_destino,
            "active": "true",
            "actions": f"output={hop['port']}"
        }
        try:
            requests.post(f"http://{controller_ip}:8080/wm/staticflowentrypusher/json", json=flow)
        except requests.exceptions.ConnectionError:
            print(" Error al insertar los flows en el switch.")

# ==== Importar YAML ====

def importar_datos(nombre_archivo):
    with open(nombre_archivo, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    for a in data.get('alumnos', []):
        alumnos[a['codigo']] = Alumno(a['nombre'], a['codigo'], a['mac'])

    for s in data.get('servidores', []):
        srv = Servidor(s['nombre'], s['ip'])
        for sv in s['servicios']:
            srv.agregar_servicio(Servicio(sv['nombre'], sv['protocolo'], sv['puerto']))
        servidores[s['nombre']] = srv

    for c in data.get('cursos', []):
        curso = Curso(c['codigo'], c['nombre'], c['estado'])
        for cod in c.get('alumnos', []):
            curso.agregar_alumno(cod)
        for srv in c.get('servidores', []):
            srv_nombre = srv['nombre']
            servicios_permitidos = srv.get('servicios_permitidos', [])
            if srv_nombre in servidores:
                curso.asignar_servidor(servidores[srv_nombre], servicios_permitidos)
        cursos[c['codigo']] = curso

    print("✅ Datos importados correctamente.")

# ==== Submenús ====

def submenu_cursos():
    while True:
        print("\n--- Submenú: Cursos ---")
        print("1) Listar cursos")
        print("2) Actualizar curso (agregar/quitar alumno)")
        print("3) Mostrar detalle de curso")
        print("0) Volver al menú principal")
        op = input(">>> ")

        if op == "1":
            for c in cursos.values():
                print(f"{c.codigo}: {c.nombre} - Estado: {c.estado}")
        elif op == "2":
            cod = input("Código del curso: ").strip()
            if cod in cursos:
                sub_op = input("1) Agregar alumno  2) Quitar alumno\n>>> ").strip()
                cod_al = int(input("Código del alumno: ").strip())
                if sub_op == "1":
                    cursos[cod].agregar_alumno(cod_al)
                    print("✅ Alumno agregado.")
                elif sub_op == "2":
                    cursos[cod].remover_alumno(cod_al)
                    print("✅ Alumno removido.")
        elif op == "3":
            cod = input("Código del curso: ").strip()
            if cod in cursos:
                curso = cursos[cod]
                print(f"{curso.codigo} - {curso.nombre} - Estado: {curso.estado}")
                print("Alumnos:")
                for codal in curso.alumnos:
                    al = alumnos.get(codal)
                    if al:
                        print(f"- {al.nombre} ({al.codigo})")
                print("Servidores asignados:")
                for s in curso.servidores.values():
                    print(f"- {s['servidor'].nombre} ({s['servidor'].direccion_ip})")
                    print("  Servicios permitidos:")
                    for sv in s['servicios']:
                        print(f"    - {sv.nombre}")
        elif op == "0":
            break

def submenu_alumnos():
    while True:
        print("\n--- Submenú: Alumnos ---")
        print("1) Listar alumnos")
        print("2) Mostrar detalle de alumno")
        print("0) Volver")
        op = input(">>> ")
        if op == "1":
            for a in alumnos.values():
                print(f"{a.codigo}: {a.nombre} - MAC: {a.mac}")
        elif op == "2":
            cod = int(input("Código del alumno: ").strip())
            a = alumnos.get(cod)
            if a:
                print(f"Nombre: {a.nombre}, Código: {a.codigo}, MAC: {a.mac}")
        elif op == "0":
            break

def crear_conexion():
    handler = input("Nombre del handler de la conexión: ")
    cod_alumno = int(input("Código del alumno: "))
    nombre_servidor = input("Nombre del servidor destino: ")
    nombre_servicio = input("Nombre del servicio: ")

    if cod_alumno not in alumnos or nombre_servidor not in servidores:
        print(" Alumno o servidor no encontrado.")
        return

    # Validar si el alumno está autorizado
    autorizado = False
    for curso in cursos.values():
        if curso.estado == "DICTANDO" and cod_alumno in curso.alumnos:
            if nombre_servidor in curso.servidores:
                for sv in curso.servidores[nombre_servidor]['servicios']:
                    if sv.nombre == nombre_servicio:
                        autorizado = True
                        break

    if not autorizado:
        print(" El alumno no está autorizado a usar ese servicio.")
        return

    alumno = alumnos[cod_alumno]
    servidor = servidores[nombre_servidor]  # ✅ Aquí debe ir el nombre del servidor

    # Buscar el servicio dentro del servidor
    servicio_obj = servidor.obtener_servicio(nombre_servicio)
    if not servicio_obj:
        print(" Servicio no encontrado en el servidor.")
        return

    mac_origen = alumno.mac

    # Obtener MAC destino a partir del nombre del servidor (harcodeado aquí, debe estar en el YAML idealmente)

    # Obtener MAC destino dinámicamente desde Floodlight

    mac_destino = "fa:16:3e:be:a5:20"


    dpid1, port1 = get_attachment_point(mac_origen)
    dpid2, port2 = get_attachment_point(mac_destino)

    if not dpid1 or not dpid2:
        print(" No se pudo obtener attachment point.")
        return

    ruta = get_route(dpid1, port1, dpid2, port2)

    if ruta:
        insertar_flows(ruta, mac_origen, mac_destino, servicio_obj.puerto)

        # Agrega los flows de retorno
        ruta_reversa = ruta[::-1]
        insertar_flows(ruta_reversa, mac_destino, mac_origen, servicio_obj.puerto)

        nueva_conexion = Conexion(handler, cod_alumno, nombre_servidor, nombre_servicio)
        nueva_conexion.ruta = ruta
        conexiones[handler] = nueva_conexion
        print(" Conexión creada exitosamente y flujos de ida y vuelta instalados.")
    else:
        print(" No se pudo establecer una ruta entre los dispositivos.")

def submenu_conexiones():
    while True:
        print("\n--- Submenú: Conexiones ---")
        print("1) Crear conexión")
        print("2) Listar conexiones")
        print("3) Borrar conexión")
        print("0) Volver")
        op = input(">>> ")
        if op == "1":
            crear_conexion()
        elif op == "2":
            if not conexiones:
                print("⚠️ No hay conexiones.")
            for c in conexiones.values():
                print(c)
        elif op == "3":
            handler = input("Ingrese el nombre del handler a borrar: ")
            if handler in conexiones:
                del conexiones[handler]
                print("✅ Conexión eliminada.")
            else:
                print("❌ Handler no encontrado.")
        elif op == "0":
            break

# ==== Menú principal ====

def main():
    while True:
        print("\n" + "#" * 58)
        print("Network Policy manager de la UPSM")
        print("#" * 58)
        print("\nSeleccione una opción:\n")
        print("1) Importar")
        print("2) Exportar")
        print("3) Cursos")
        print("4) Alumnos")
        print("5) Servidores")
        print("6) Políticas")
        print("7) Conexiones")
        print("8) Salir")

        op = input(">>> ")

        if op == "1":
            archivo = input("Ingrese el nombre del archivo YAML: ")
            importar_datos(archivo)
        elif op == "2":
            print("⚠️ Exportar no disponible todavía.")
        elif op == "3":
            submenu_cursos()
        elif op == "4":
            submenu_alumnos()
        elif op == "5":
            print("⚠️ Módulo de servidores ya manejado por los cursos.")
        elif op == "6":
            print("⚠️ No hay políticas configurables aún.")
        elif op == "7":
            submenu_conexiones()
        elif op == "8":
            print("👋 Hasta luego crack.")
            break
        else:
            print("Opción inválida. Inténtalo de nuevo.")

# ==== Ejecución ====
if __name__ == "__main__":
    main()

