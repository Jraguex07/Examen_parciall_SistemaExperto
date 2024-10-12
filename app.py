from flask import Flask, render_template, request, jsonify

import pyodbc


app = Flask(__name__)

def conectar_db():
    
    try:
        conexion = pyodbc.connect(
            'DRIVER={SQL Server};'
            'SERVER=DESKTOP-MQGQ22O\\SQLEXPRESS;'
            'DATABASE=ReglasDB;'
            'UID=sa;'
            'PWD=Everise$2023.;'
        )
        print("the connection to data base was successful.")
        return conexion
    except pyodbc.Error as e:
        print("ERROR to connect to data base:", e)
        return None

@app.route('/')
def index():
    return render_template('index.html')

class Regla:
    def __init__(self, condiciones, conclusion, id=None):
        
        self.condiciones = condiciones
        self.conclusion = conclusion
        self.id = id

@app.route('/insertar_regla', methods=['POST'])
def insertar_regla():
    data = request.get_json()
    condiciones = ','.join(data['condiciones'])
    conclusion = data['conclusion']

    conexion = conectar_db()
    if conexion:
        cursor = conexion.cursor()
        cursor.execute('''
            INSERT INTO Reglas (condiciones, conclusion) VALUES (?, ?)
        ''', (condiciones, conclusion))
        conexion.commit()
        conexion.close()
        return jsonify({"message": f"Regla '{conclusion}' insertada correctamente."})
    return jsonify({"message": "Error al insertar la regla."})

@app.route('/eliminar_regla', methods=['POST'])
def eliminar_regla():
    data = request.get_json()
    regla_id = data.get('id')

    conexion = conectar_db()
    if conexion:
        cursor = conexion.cursor()
        cursor.execute('DELETE FROM Reglas WHERE id = ?', (regla_id,))
        conexion.commit()
        conexion.close()
        return jsonify({"message": f"Regla con ID {regla_id} eliminada correctamente."})
    return jsonify({"message": "Error al eliminar la regla."})


@app.route('/consultar_reglas_para_diagnostico', methods=['GET'])
def consultar_reglas_para_diagnostico():
    conexion = conectar_db()
    if conexion:
        cursor = conexion.cursor()
        cursor.execute('SELECT id, condiciones, conclusion FROM Reglas')
        reglas = []
        for row in cursor.fetchall():
            condiciones = set(row[1].split(','))  # Separar las condiciones por comas
            conclusion = row[2]
            reglas.append(Regla(condiciones, conclusion, row[0]))  # Crear objetos de Regla
        conexion.close()
        return reglas
    return []
# Ruta para diagnosticar problemas del vehículo

@app.route('/diagnosticar', methods=['POST'])
def diagnosticar():
    data = request.get_json()  # Recibe los hechos ingresados por el usuario
    hechos = set(data['hechos'])  # Convierte los hechos en un conjunto
    reglas = consultar_reglas_para_diagnostico()  # Carga las reglas en formato objeto
    
    # Ejecuta el encadenamiento hacia adelante para obtener las conclusiones
    conclusiones = encadenamiento_hacia_adelante(hechos, reglas)

    if conclusiones:
        return jsonify({"conclusiones": list(conclusiones)})  # Devuelve las conclusiones encontradas
    return jsonify({"message": "No se encontraron problemas con los hechos ingresados."})

def encadenamiento_hacia_adelante(hechos, reglas):
    conclusiones = set()
    nuevo_hecho_agregado = True

    while nuevo_hecho_agregado:
        nuevo_hecho_agregado = False

        for regla in reglas:
            if regla.condiciones.issubset(hechos) and regla.conclusion not in hechos:
                hechos.add(regla.conclusion)
                conclusiones.add(regla.conclusion)
                nuevo_hecho_agregado = True

    return conclusiones

def obtener_hechos():
    hechos = set()
    while True:
        hecho = input("Ingrese un hecho (o 'diagnosticar' para obtener el diagnóstico): ").strip()
        if hecho.lower() == 'diagnosticar':
            break
        if hecho:
            hechos.add(hecho)
    return hechos

def mostrar_menu():
    print("\nMenú:")
    print("1. Añadir regla")
    print("2. Eliminar regla por ID")
    print("3. Consultar problemas del vehículo")
    print("4. Actualizar base de datos")
    print("5. Salir")

def registrar_log(action, details):
    conexion = conectar_db()
    if conexion:
        cursor = conexion.cursor()
        cursor.execute('''
            INSERT INTO Logs (action, details) VALUES (?, ?)
        ''', (action, details))
        conexion.commit()
        conexion.close()
        print("Registro de log insertado correctamente.")
    else:
        print("No se pudo registrar el log. Conexión fallida.")

def main():
    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción: ").strip()
        
        if opcion == '1':
            condiciones = input("Ingrese las condiciones separadas por comas: ").split(',')
            conclusion = input("Ingrese la conclusión: ").strip()
            insertar_regla([c.strip() for c in condiciones], conclusion)

        elif opcion == '2':
            regla_id = int(input("Ingrese el ID de la regla a eliminar: ").strip())
            eliminar_regla(regla_id)

        elif opcion == '3':
            reglas = consultar_reglas_para_diagnostico()
            hechos = obtener_hechos()
            conclusiones = encadenamiento_hacia_adelante(hechos, reglas)

            if conclusiones:
                print("Posibles problemas del automóvil:")
                for conclusion in conclusiones:
                    print(conclusion)
            else:
                print("No se encontraron problemas con los hechos ingresados.")

        elif opcion == '4':
            print("Updating database... (Make sure to insert rules in the database )")
            registrar_log("Updating the data base", "The data base was updated.")

        elif opcion == '5':
            print("Leaving...")
            registrar_log("Salir", "El usuario ha salido del programa.")
            break
        
        else:
            print("Opción inválida.Please try again.")

if __name__ == "__main__":
    app.run(debug=True)
    main()

