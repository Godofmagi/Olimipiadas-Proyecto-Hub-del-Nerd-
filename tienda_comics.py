"""
tienda_comics.py
Sistema de administración de una tienda de cómics.
E.E.S.T. N°6 "Chacabuco" - Olimpiadas Institucionales 2026.

Basado en el esquema real de la base 'tienda_comics' (tablas
articulos y categorias). Sigue el mismo nivel de complejidad que
el ejemplo oficial del "Maxikiosco": funciones simples, cada una
con una responsabilidad concreta, ordenamiento y filtrado resueltos
con SQL, y una única función recursiva aplicada a algo real
(calcular el valor total del inventario).

Ejecutar la aplicación:       python3 tienda_comics.py
Ejecutar los casos de prueba:  python3 tienda_comics.py test
"""
import sys
import unittest

import mysql.connector

# ------------------------------------------------------------
# Datos de conexión (completar con los propios)
# ------------------------------------------------------------
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "tienda_comics"


def conectar():
    """Función encargada exclusivamente de conectar con la base de
    datos, para que el resto de las funciones no repitan este código."""
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )


# ------------------------------------------------------------
# Validación (control de datos inválidos)
# ------------------------------------------------------------
def validar_articulo(codigo, nombre, precio, stock):
    if not codigo.strip():
        raise ValueError("El código no puede estar vacío.")
    if not nombre.strip():
        raise ValueError("El título no puede estar vacío.")
    if precio <= 0:
        raise ValueError("El precio debe ser mayor a 0.")
    if stock < 0:
        raise ValueError("El stock no puede ser negativo.")


def codigo_ya_existe(cursor, codigo):
    cursor.execute("SELECT id FROM articulos WHERE codigo = %s", (codigo,))
    return cursor.fetchone() is not None


# ------------------------------------------------------------
# Mostrar categorías (ayuda para saber qué Id_C usar al registrar)
# ------------------------------------------------------------
def mostrar_categorias():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM categorias")
    for cat in cursor.fetchall():
        print(cat[0], "-", cat[1])
    cursor.close()
    conexion.close()


# ------------------------------------------------------------
# Registrar (alta)
# ------------------------------------------------------------
def registrar_articulo():
    conexion = conectar()
    cursor = conexion.cursor()

    id_categoria = int(input("ID de categoría (opción 9 para verlas): "))
    codigo = input("Código: ")
    nombre = input("Título: ")
    precio = float(input("Precio: "))
    stock = int(input("Stock: "))

    try:
        validar_articulo(codigo, nombre, precio, stock)
        if codigo_ya_existe(cursor, codigo):
            print("Ya existe un artículo con ese código.")
            return

        cursor.execute(
            "INSERT INTO articulos (Id_C, codigo, nombre_titulo, precio, stock) "
            "VALUES (%s, %s, %s, %s, %s)",
            (id_categoria, codigo, nombre, precio, stock),
        )
        conexion.commit()
        print("Artículo registrado correctamente.")
    except ValueError as e:
        print("Error de validación:", e)
    finally:
        cursor.close()
        conexion.close()


# ------------------------------------------------------------
# Mostrar todos
# ------------------------------------------------------------
def mostrar_articulos():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, codigo, nombre_titulo, precio, stock FROM articulos")
    articulos = cursor.fetchall()  # lista de tuplas: nuestra estructura de datos

    print("\nLISTADO DE ARTÍCULOS")
    print("-" * 60)
    for a in articulos:
        print(a[0], a[1], a[2], "$", a[3], "Stock:", a[4])

    cursor.close()
    conexion.close()


# ------------------------------------------------------------
# Buscar por código
# ------------------------------------------------------------
def buscar_articulo():
    codigo = input("Código a buscar: ")
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT id, codigo, nombre_titulo, precio, stock FROM articulos WHERE codigo = %s",
        (codigo,),
    )
    articulo = cursor.fetchone()

    if articulo:
        print("\nArtículo encontrado")
        print("ID:", articulo[0])
        print("Código:", articulo[1])
        print("Título:", articulo[2])
        print("Precio:", articulo[3])
        print("Stock:", articulo[4])
    else:
        print("El artículo no existe.")

    cursor.close()
    conexion.close()


# ------------------------------------------------------------
# Modificar (precio y stock)
# ------------------------------------------------------------
def modificar_articulo():
    codigo = input("Código del artículo a modificar: ")
    nuevo_precio = float(input("Nuevo precio: "))
    nuevo_stock = int(input("Nuevo stock: "))

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE articulos SET precio = %s, stock = %s WHERE codigo = %s",
        (nuevo_precio, nuevo_stock, codigo),
    )
    conexion.commit()

    if cursor.rowcount > 0:
        print("Artículo modificado.")
    else:
        print("No se encontró el artículo.")

    cursor.close()
    conexion.close()


# ------------------------------------------------------------
# Eliminar
# ------------------------------------------------------------
def eliminar_articulo():
    codigo = input("Código del artículo a eliminar: ")
    confirmar = input(f"¿Confirma eliminar '{codigo}'? (s/n): ").lower()
    if confirmar != "s":
        print("Operación cancelada.")
        return

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM articulos WHERE codigo = %s", (codigo,))
    conexion.commit()

    if cursor.rowcount > 0:
        print("Artículo eliminado.")
    else:
        print("Artículo inexistente.")

    cursor.close()
    conexion.close()


# ------------------------------------------------------------
# Ordenar (resuelto directamente con SQL, sin código extra)
# ------------------------------------------------------------
def ordenar_articulos():
    orden = input("Ordenar por (1) precio o (2) título: ")
    campo = "precio" if orden == "1" else "nombre_titulo"

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        f"SELECT codigo, nombre_titulo, precio, stock FROM articulos ORDER BY {campo} ASC"
    )
    for a in cursor.fetchall():
        print(a)

    cursor.close()
    conexion.close()


# ------------------------------------------------------------
# Filtrar por categoría (JOIN porque la categoría es otra tabla)
# ------------------------------------------------------------
def filtrar_articulos():
    categoria = input("Ingrese el nombre de la categoría: ")

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT a.codigo, a.nombre_titulo, a.precio, a.stock
        FROM articulos a
        JOIN categorias c ON a.Id_C = c.id
        WHERE c.nombre = %s
        """,
        (categoria,),
    )
    for a in cursor.fetchall():
        print(a)

    cursor.close()
    conexion.close()


# ------------------------------------------------------------
# RECURSIVIDAD: valor total del inventario (precio * stock, sumado
# recursivamente sobre la lista de artículos)
# ------------------------------------------------------------
def obtener_precios_y_stock():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT precio, stock FROM articulos")
    datos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return datos


def calcular_valor_inventario(datos, posicion=0):
    if posicion == len(datos):
        return 0  # caso base: no quedan artículos por sumar
    precio, stock = datos[posicion]
    return float(precio) * stock + calcular_valor_inventario(datos, posicion + 1)


# ------------------------------------------------------------
# Menú principal
# ------------------------------------------------------------
def menu():
    while True:
        print("\n==============================")
        print(" TIENDA DE CÓMICS")
        print("==============================")
        print("1 - Registrar artículo")
        print("2 - Mostrar artículos")
        print("3 - Buscar artículo por código")
        print("4 - Modificar artículo")
        print("5 - Eliminar artículo")
        print("6 - Ordenar artículos")
        print("7 - Filtrar por categoría")
        print("8 - Calcular valor total del inventario")
        print("9 - Ver categorías disponibles")
        print("0 - Salir")
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            registrar_articulo()
        elif opcion == "2":
            mostrar_articulos()
        elif opcion == "3":
            buscar_articulo()
        elif opcion == "4":
            modificar_articulo()
        elif opcion == "5":
            eliminar_articulo()
        elif opcion == "6":
            ordenar_articulos()
        elif opcion == "7":
            filtrar_articulos()
        elif opcion == "8":
            datos = obtener_precios_y_stock()
            total = calcular_valor_inventario(datos)
            print("Valor total del inventario: $", round(total, 2))
        elif opcion == "9":
            mostrar_categorias()
        elif opcion == "0":
            print("Programa finalizado.")
            break
        else:
            print("Opción incorrecta.")


# ------------------------------------------------------------
# Casos de prueba (no requieren conexión real a la base)
# ------------------------------------------------------------
class TestValidaciones(unittest.TestCase):
    def test_precio_invalido(self):
        with self.assertRaises(ValueError):
            validar_articulo("COM-001", "Watchmen", -100, 5)

    def test_stock_invalido(self):
        with self.assertRaises(ValueError):
            validar_articulo("COM-001", "Watchmen", 100, -5)

    def test_nombre_vacio(self):
        with self.assertRaises(ValueError):
            validar_articulo("COM-001", "   ", 100, 5)

    def test_articulo_valido_no_lanza_error(self):
        try:
            validar_articulo("COM-001", "Watchmen", 6000, 5)
        except ValueError:
            self.fail("No debería lanzar error con datos válidos.")


class TestRecursividad(unittest.TestCase):
    def test_valor_inventario_lista_vacia(self):
        self.assertEqual(calcular_valor_inventario([]), 0)

    def test_valor_inventario_varios_articulos(self):
        datos = [(1800, 25), (1200, 40), (1500, 20)]
        # 1800*25 + 1200*40 + 1500*20 = 45000 + 48000 + 30000 = 123000
        self.assertEqual(calcular_valor_inventario(datos), 123000)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        sys.argv.pop(1)
        unittest.main(verbosity=2)
    else:
        menu()
