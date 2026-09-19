# ================================================================
# COMICVERSE - TIENDA DE COMICS
# VERSION GOOGLE COLAB + MARIADB
#
# IMPORTANTE:
# - Este archivo NO contiene una base de datos de productos.
# - Los datos se leen/escriben directamente en MariaDB.
# - La estructura esperada es la de Tienda_Comics.sql.
# - El archivo SQL debe ejecutarse previamente en MariaDB.
# ================================================================

# En Google Colab, ejecutar una sola vez:
# !pip install mysql-connector-python

import mysql.connector
from mysql.connector import Error
from decimal import Decimal
from datetime import datetime


# ================================================================
# 1. CONFIGURACION DE LA CONEXION
# ================================================================
#
# Estos datos NO son datos de la tienda.
# Son solamente los datos necesarios para que Python se conecte
# al servidor MariaDB.
#
# CAMBIARLOS por los datos de la computadora/servidor donde
# este funcionando MariaDB.
#
# ATENCION CON GOOGLE COLAB:
# "localhost" significa la maquina donde se esta ejecutando Python.
# En Colab, localhost es la maquina virtual de Colab, NO tu PC.
# Por eso, para usar MariaDB de tu PC desde Colab, el servidor
# debe ser accesible desde Internet mediante una configuracion
# de red/tunel, o se debe usar un servidor MariaDB remoto.
# ================================================================

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "database": "tienda_comics",
    "user": "root",
    "password": ""
}


# ================================================================
# 2. CONEXION A MARIA DB
# ================================================================

def conectar():
    """
    Crea y devuelve una conexion a MariaDB.

    No crea tablas.
    No inserta productos.
    No contiene el catalogo.
    Solamente conecta Python con la base de datos existente.
    """
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)

        if conexion.is_connected():
            return conexion

        return None

    except Error as e:
        print("No se pudo conectar con MariaDB.")
        print("Detalle:", e)
        return None


def probar_conexion():
    conexion = conectar()

    if conexion is None:
        return False

    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT DATABASE()")
        resultado = cursor.fetchone()

        print("Conexion realizada correctamente.")
        print("Base de datos:", resultado[0])

        cursor.close()
        conexion.close()
        return True

    except Error as e:
        print("Error al comprobar la conexion:", e)
        conexion.close()
        return False


# ================================================================
# 3. FUNCIONES GENERALES
# ================================================================

def linea():
    print("=" * 80)


def moneda(valor):
    valor = Decimal(str(valor))
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return "$" + texto


def pausar():
    input("\nPresione ENTER para continuar...")


def leer_entero(mensaje):
    while True:
        try:
            return int(input(mensaje))
        except ValueError:
            print("Debe ingresar un numero entero.")


def leer_decimal(mensaje):
    while True:
        try:
            valor = Decimal(input(mensaje))
            return valor
        except Exception:
            print("Debe ingresar un numero valido.")


def cerrar_recursos(conexion, cursor=None):
    if cursor is not None:
        cursor.close()

    if conexion is not None and conexion.is_connected():
        conexion.close()


# ================================================================
# 4. ARTICULOS / CATALOGO
# ================================================================
#
# La tabla articulos del SQL contiene:
# id, Id_C, codigo, nombre_titulo, precio y stock.
#
# Por eso NO usamos editorial, descripcion ni categorias escritas
# dentro de Python como hacia la version anterior.
# ================================================================

def obtener_articulos():
    conexion = conectar()

    if conexion is None:
        return []

    cursor = conexion.cursor(dictionary=True)

    try:
        consulta = """
            SELECT
                a.id,
                a.codigo,
                a.nombre_titulo,
                a.precio,
                a.stock,
                c.id AS categoria_id,
                c.nombre AS categoria,
                c.descripcion AS categoria_descripcion
            FROM articulos a
            INNER JOIN categorias c ON a.Id_C = c.id
            ORDER BY a.id
        """

        cursor.execute(consulta)
        return cursor.fetchall()

    except Error as e:
        print("Error al obtener los articulos:", e)
        return []

    finally:
        cerrar_recursos(conexion, cursor)


def buscar_articulo_por_codigo(codigo):
    conexion = conectar()

    if conexion is None:
        return None

    cursor = conexion.cursor(dictionary=True)

    try:
        consulta = """
            SELECT
                a.id,
                a.codigo,
                a.nombre_titulo,
                a.precio,
                a.stock,
                c.id AS categoria_id,
                c.nombre AS categoria,
                c.descripcion AS categoria_descripcion
            FROM articulos a
            INNER JOIN categorias c ON a.Id_C = c.id
            WHERE LOWER(a.codigo) = LOWER(%s)
        """

        cursor.execute(consulta, (codigo,))
        return cursor.fetchone()

    except Error as e:
        print("Error al buscar el articulo:", e)
        return None

    finally:
        cerrar_recursos(conexion, cursor)


def buscar_articulos(texto):
    conexion = conectar()

    if conexion is None:
        return []

    cursor = conexion.cursor(dictionary=True)

    try:
        texto_busqueda = f"%{texto}%"

        consulta = """
            SELECT
                a.id,
                a.codigo,
                a.nombre_titulo,
                a.precio,
                a.stock,
                c.id AS categoria_id,
                c.nombre AS categoria,
                c.descripcion AS categoria_descripcion
            FROM articulos a
            INNER JOIN categorias c ON a.Id_C = c.id
            WHERE
                a.codigo LIKE %s
                OR a.nombre_titulo LIKE %s
                OR c.nombre LIKE %s
            ORDER BY a.nombre_titulo
        """

        cursor.execute(
            consulta,
            (texto_busqueda, texto_busqueda, texto_busqueda)
        )

        return cursor.fetchall()

    except Error as e:
        print("Error al buscar articulos:", e)
        return []

    finally:
        cerrar_recursos(conexion, cursor)


def obtener_articulo_por_id(id_articulo):
    conexion = conectar()

    if conexion is None:
        return None

    cursor = conexion.cursor(dictionary=True)

    try:
        consulta = """
            SELECT
                a.id,
                a.codigo,
                a.nombre_titulo,
                a.precio,
                a.stock,
                c.id AS categoria_id,
                c.nombre AS categoria,
                c.descripcion AS categoria_descripcion
            FROM articulos a
            INNER JOIN categorias c ON a.Id_C = c.id
            WHERE a.id = %s
        """

        cursor.execute(consulta, (id_articulo,))
        return cursor.fetchone()

    except Error as e:
        print("Error al obtener el articulo:", e)
        return None

    finally:
        cerrar_recursos(conexion, cursor)


def estado_stock(stock):
    if stock <= 0:
        return "AGOTADO"
    elif stock <= 3:
        return "ULTIMAS UNIDADES"
    elif stock <= 7:
        return "POCO STOCK"
    else:
        return "DISPONIBLE"


# ================================================================
# 5. CATEGORIAS
# ================================================================

def obtener_categorias():
    conexion = conectar()

    if conexion is None:
        return []

    cursor = conexion.cursor(dictionary=True)

    try:
        consulta = """
            SELECT id, nombre, descripcion
            FROM categorias
            ORDER BY nombre
        """

        cursor.execute(consulta)
        return cursor.fetchall()

    except Error as e:
        print("Error al obtener categorias:", e)
        return []

    finally:
        cerrar_recursos(conexion, cursor)


def obtener_categoria_por_id(id_categoria):
    conexion = conectar()

    if conexion is None:
        return None

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, nombre, descripcion
            FROM categorias
            WHERE id = %s
            """,
            (id_categoria,)
        )

        return cursor.fetchone()

    except Error as e:
        print("Error al obtener categoria:", e)
        return None

    finally:
        cerrar_recursos(conexion, cursor)


def obtener_categoria_por_nombre(nombre):
    conexion = conectar()

    if conexion is None:
        return None

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, nombre, descripcion
            FROM categorias
            WHERE LOWER(nombre) = LOWER(%s)
            """,
            (nombre,)
        )

        return cursor.fetchone()

    except Error as e:
        print("Error al buscar categoria:", e)
        return None

    finally:
        cerrar_recursos(conexion, cursor)


# ================================================================
# 6. CLIENTES
# ================================================================

def obtener_clientes():
    conexion = conectar()

    if conexion is None:
        return []

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, dni, nombre, apellido, email, telefono
            FROM clientes
            ORDER BY apellido, nombre
            """
        )

        return cursor.fetchall()

    except Error as e:
        print("Error al obtener clientes:", e)
        return []

    finally:
        cerrar_recursos(conexion, cursor)


def obtener_cliente_por_id(id_cliente):
    conexion = conectar()

    if conexion is None:
        return None

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, dni, nombre, apellido, email, telefono
            FROM clientes
            WHERE id = %s
            """,
            (id_cliente,)
        )

        return cursor.fetchone()

    except Error as e:
        print("Error al obtener cliente:", e)
        return None

    finally:
        cerrar_recursos(conexion, cursor)


def buscar_cliente_por_dni(dni):
    conexion = conectar()

    if conexion is None:
        return None

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, dni, nombre, apellido, email, telefono
            FROM clientes
            WHERE dni = %s
            """,
            (dni,)
        )

        return cursor.fetchone()

    except Error as e:
        print("Error al buscar cliente:", e)
        return None

    finally:
        cerrar_recursos(conexion, cursor)


def crear_cliente():
    linea()
    print("                 REGISTRAR CLIENTE")
    linea()

    dni = input("DNI: ")
    nombre = input("Nombre: ")
    apellido = input("Apellido: ")
    email = input("Email: ")
    telefono = input("Telefono: ")

    if buscar_cliente_por_dni(dni) is not None:
        print("Ya existe un cliente con ese DNI.")
        return None

    conexion = conectar()

    if conexion is None:
        return None

    cursor = conexion.cursor()

    try:
        consulta = """
            INSERT INTO clientes
            (dni, nombre, apellido, email, telefono)
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            consulta,
            (dni, nombre, apellido, email, telefono)
        )

        conexion.commit()
        id_cliente = cursor.lastrowid

        print("Cliente registrado correctamente.")
        return id_cliente

    except Error as e:
        conexion.rollback()
        print("Error al registrar cliente:", e)
        return None

    finally:
        cerrar_recursos(conexion, cursor)


# ================================================================
# 7. VENDEDORES
# ================================================================

def obtener_vendedores():
    conexion = conectar()

    if conexion is None:
        return []

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, descripvion, nombre, apellido, turno
            FROM vendedores
            ORDER BY apellido, nombre
            """
        )

        return cursor.fetchall()

    except Error as e:
        print("Error al obtener vendedores:", e)
        return []

    finally:
        cerrar_recursos(conexion, cursor)


def obtener_vendedor_por_id(id_vendedor):
    conexion = conectar()

    if conexion is None:
        return None

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, descripvion, nombre, apellido, turno
            FROM vendedores
            WHERE id = %s
            """,
            (id_vendedor,)
        )

        return cursor.fetchone()

    except Error as e:
        print("Error al obtener vendedor:", e)
        return None

    finally:
        cerrar_recursos(conexion, cursor)


# ================================================================
# 8. CARRITO
# ================================================================
#
# El carrito es temporal: vive en Python mientras se prepara una
# compra. La informacion definitiva se guarda en SQL solamente
# cuando se confirma la venta.
# ================================================================

carrito = []


def buscar_item_carrito(id_articulo):
    for item in carrito:
        if item["id_articulo"] == id_articulo:
            return item

    return None


def total_carrito():
    total = Decimal("0.00")

    for item in carrito:
        total += item["precio"] * item["cantidad"]

    return total


def cantidad_productos_carrito():
    cantidad = 0

    for item in carrito:
        cantidad += item["cantidad"]

    return cantidad


def agregar_al_carrito():
    linea()
    print("                     AGREGAR AL CARRITO")
    linea()

    codigo = input("Codigo del comic: ")
    producto = buscar_articulo_por_codigo(codigo)

    if producto is None:
        print("No existe ese comic en SQL.")
        return

    if producto["stock"] <= 0:
        print("El comic esta agotado.")
        return

    cantidad = leer_entero("Cantidad: ")

    if cantidad <= 0:
        print("La cantidad debe ser mayor que 0.")
        return

    item = buscar_item_carrito(producto["id"])

    cantidad_actual = 0

    if item is not None:
        cantidad_actual = item["cantidad"]

    if cantidad_actual + cantidad > producto["stock"]:
        print("No hay suficiente stock.")
        print("Stock disponible:", producto["stock"])
        return

    if item is None:
        carrito.append({
            "id_articulo": producto["id"],
            "codigo": producto["codigo"],
            "nombre": producto["nombre_titulo"],
            "precio": Decimal(str(producto["precio"])),
            "cantidad": cantidad
        })
    else:
        item["cantidad"] += cantidad

    print("Producto agregado al carrito.")


def eliminar_del_carrito():
    if len(carrito) == 0:
        print("El carrito esta vacio.")
        return

    ver_carrito()

    codigo = input("\nCodigo del comic que desea quitar: ")

    producto = buscar_articulo_por_codigo(codigo)

    if producto is None:
        print("No existe ese comic.")
        return

    item = buscar_item_carrito(producto["id"])

    if item is None:
        print("Ese comic no esta en el carrito.")
        return

    carrito.remove(item)
    print("Producto eliminado del carrito.")


def cambiar_cantidad_carrito():
    if len(carrito) == 0:
        print("El carrito esta vacio.")
        return

    ver_carrito()

    codigo = input("\nCodigo del comic: ")
    producto = buscar_articulo_por_codigo(codigo)

    if producto is None:
        print("No existe ese comic.")
        return

    item = buscar_item_carrito(producto["id"])

    if item is None:
        print("Ese comic no esta en el carrito.")
        return

    nueva_cantidad = leer_entero("Nueva cantidad: ")

    if nueva_cantidad <= 0:
        print("La cantidad debe ser mayor que 0.")
        return

    # Se vuelve a consultar SQL para verificar el stock actual.
    producto_actual = obtener_articulo_por_id(producto["id"])

    if producto_actual is None:
        print("El articulo ya no existe.")
        return

    if nueva_cantidad > producto_actual["stock"]:
        print("No hay suficiente stock.")
        return

    item["cantidad"] = nueva_cantidad
    item["precio"] = Decimal(str(producto_actual["precio"]))

    print("Cantidad actualizada.")


def vaciar_carrito():
    if len(carrito) == 0:
        print("El carrito ya esta vacio.")
        return

    respuesta = input("¿Seguro que desea vaciar el carrito? (s/n): ")

    if respuesta.lower() == "s":
        carrito.clear()
        print("Carrito vaciado.")
    else:
        print("Operacion cancelada.")


def ver_carrito():
    linea()
    print("                         CARRITO")
    linea()

    if len(carrito) == 0:
        print("El carrito esta vacio.")
        return

    total = Decimal("0.00")

    for item in carrito:
        subtotal = item["precio"] * item["cantidad"]
        total += subtotal

        print("Codigo:", item["codigo"])
        print("Comic:", item["nombre"])
        print("Cantidad:", item["cantidad"])
        print("Precio unitario:", moneda(item["precio"]))
        print("Subtotal:", moneda(subtotal))
        print("-" * 80)

    print("CANTIDAD TOTAL:", cantidad_productos_carrito())
    print("TOTAL:", moneda(total))


# ================================================================
# 9. MOSTRAR CATALOGO
# ================================================================

def mostrar_producto(producto):
    linea()
    print("ID:", producto["id"])
    print("CODIGO:", producto["codigo"])
    print("NOMBRE:", producto["nombre_titulo"])
    print("CATEGORIA:", producto["categoria"])
    print("PRECIO:", moneda(producto["precio"]))
    print("STOCK:", producto["stock"])
    print("ESTADO:", estado_stock(producto["stock"]))
    print("DESCRIPCION DE CATEGORIA:",
          producto["categoria_descripcion"])


def mostrar_catalogo():
    productos = obtener_articulos()

    linea()
    print("                         CATALOGO")
    linea()

    if len(productos) == 0:
        print("No hay articulos cargados en SQL.")
        return

    for producto in productos:
        print(
            f"{producto['codigo']} | "
            f"{producto['nombre_titulo']:<35} | "
            f"{moneda(producto['precio']):>12} | "
            f"Stock: {producto['stock']:<3} | "
            f"{estado_stock(producto['stock'])}"
        )


def buscar_productos_menu():
    texto = input("Ingrese nombre, codigo o categoria: ")

    encontrados = buscar_articulos(texto)

    print()

    if len(encontrados) == 0:
        print("No se encontraron comics.")
        return

    linea()
    print("RESULTADOS")
    linea()

    for producto in encontrados:
        print(
            f"{producto['codigo']} | "
            f"{producto['nombre_titulo']} | "
            f"{moneda(producto['precio'])} | "
            f"Stock: {producto['stock']}"
        )


def filtrar_por_categoria():
    categorias = obtener_categorias()

    if len(categorias) == 0:
        print("No hay categorias en SQL.")
        return

    linea()
    print("CATEGORIAS")
    linea()

    for categoria in categorias:
        print(
            f"{categoria['id']}. "
            f"{categoria['nombre']} - "
            f"{categoria['descripcion']}"
        )

    id_categoria = leer_entero("ID de categoria: ")

    conexion = conectar()

    if conexion is None:
        return

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                a.id,
                a.codigo,
                a.nombre_titulo,
                a.precio,
                a.stock,
                c.nombre AS categoria
            FROM articulos a
            INNER JOIN categorias c ON a.Id_C = c.id
            WHERE c.id = %s
            ORDER BY a.nombre_titulo
            """,
            (id_categoria,)
        )

        productos = cursor.fetchall()

        print()

        if len(productos) == 0:
            print("No hay articulos para esa categoria.")
            return

        for producto in productos:
            print(
                f"{producto['codigo']} | "
                f"{producto['nombre_titulo']} | "
                f"{moneda(producto['precio'])} | "
                f"Stock: {producto['stock']}"
            )

    except Error as e:
        print("Error al filtrar:", e)

    finally:
        cerrar_recursos(conexion, cursor)


def ver_detalle_comic():
    codigo = input("Codigo del comic: ")
    producto = buscar_articulo_por_codigo(codigo)

    if producto is None:
        print("No existe ese comic.")
        return

    mostrar_producto(producto)


def menu_catalogo():
    while True:
        print()
        linea()
        print("                    CATALOGO DE COMICS")
        linea()
        print("1. Ver todos")
        print("2. Buscar comic")
        print("3. Filtrar por categoria")
        print("4. Ver detalle")
        print("5. Volver")
        linea()

        opcion = input("Seleccione una opcion: ")

        if opcion == "1":
            mostrar_catalogo()
            pausar()

        elif opcion == "2":
            buscar_productos_menu()
            pausar()

        elif opcion == "3":
            filtrar_por_categoria()
            pausar()

        elif opcion == "4":
            ver_detalle_comic()
            pausar()

        elif opcion == "5":
            break

        else:
            print("Opcion invalida.")


# ================================================================
# 10. MENU DEL CARRITO
# ================================================================

def menu_carrito():
    while True:
        print()
        linea()
        print("                      MENU CARRITO")
        linea()
        print("1. Ver carrito")
        print("2. Agregar comic")
        print("3. Cambiar cantidad")
        print("4. Eliminar comic")
        print("5. Vaciar carrito")
        print("6. Finalizar compra")
        print("7. Volver")
        linea()

        opcion = input("Seleccione una opcion: ")

        if opcion == "1":
            ver_carrito()
            pausar()

        elif opcion == "2":
            agregar_al_carrito()
            pausar()

        elif opcion == "3":
            cambiar_cantidad_carrito()
            pausar()

        elif opcion == "4":
            eliminar_del_carrito()
            pausar()

        elif opcion == "5":
            vaciar_carrito()
            pausar()

        elif opcion == "6":
            confirmar_venta()

        elif opcion == "7":
            break

        else:
            print("Opcion invalida.")


# ================================================================
# 11. VENTAS
# ================================================================
#
# La base SQL NO tiene un campo metodo_pago.
# Por eso el metodo de pago puede seleccionarse en Python, pero
# NO se guarda en MariaDB con la estructura actual.
#
# Una venta SQL necesita:
# - cliente
# - vendedor
# - fecha_hora
# - monto_total
#
# Y sus detalles necesitan:
# - venta
# - articulo
# - cantidad
# - precio_unitario
# - subtotal
# ================================================================

def seleccionar_cliente():
    clientes = obtener_clientes()

    if len(clientes) == 0:
        print("No hay clientes cargados.")
        print("Puede registrar uno nuevo.")
        return crear_cliente()

    print()
    linea()
    print("CLIENTES")
    linea()

    for cliente in clientes:
        print(
            f"{cliente['id']}. "
            f"{cliente['nombre']} {cliente['apellido']} "
            f"- DNI: {cliente['dni']}"
        )

    print("0. Registrar nuevo cliente")

    id_cliente = leer_entero("Seleccione el cliente: ")

    if id_cliente == 0:
        return crear_cliente()

    cliente = obtener_cliente_por_id(id_cliente)

    if cliente is None:
        print("Cliente invalido.")
        return None

    return cliente["id"]


def seleccionar_vendedor():
    vendedores = obtener_vendedores()

    if len(vendedores) == 0:
        print("No hay vendedores cargados en SQL.")
        return None

    print()
    linea()
    print("VENDEDORES")
    linea()

    for vendedor in vendedores:
        print(
            f"{vendedor['id']}. "
            f"{vendedor['nombre']} {vendedor['apellido']} "
            f"- Turno: {vendedor['turno']}"
        )

    id_vendedor = leer_entero("Seleccione el vendedor: ")

    vendedor = obtener_vendedor_por_id(id_vendedor)

    if vendedor is None:
        print("Vendedor invalido.")
        return None

    return vendedor["id"]


def elegir_metodo_pago():
    print()
    linea()
    print("METODO DE PAGO")
    linea()
    print("1. Efectivo")
    print("2. Tarjeta de credito")
    print("3. Tarjeta de debito")
    print("4. Transferencia")

    metodos = {
        "1": "Efectivo",
        "2": "Credito",
        "3": "Debito",
        "4": "Transferencia"
    }

    opcion = input("Seleccione el metodo: ")

    return metodos.get(opcion)


def confirmar_venta():
    if len(carrito) == 0:
        print("El carrito esta vacio.")
        return

    ver_carrito()

    metodo = elegir_metodo_pago()

    if metodo is None:
        print("Metodo de pago invalido.")
        return

    cliente_id = seleccionar_cliente()

    if cliente_id is None:
        print("No se pudo seleccionar el cliente.")
        return

    vendedor_id = seleccionar_vendedor()

    if vendedor_id is None:
        print("No se pudo seleccionar el vendedor.")
        return

    total = total_carrito()

    confirmacion = input(
        f"\nConfirmar compra por {moneda(total)} "
        f"con {metodo}? (s/n): "
    )

    if confirmacion.lower() != "s":
        print("Compra cancelada.")
        return

    realizar_venta(cliente_id, vendedor_id, metodo)


def realizar_venta(cliente_id, vendedor_id, metodo_pago):
    """
    Registra una venta COMPLETA en SQL usando una transaccion.

    Si algo falla:
    - se hace rollback
    - no queda una venta incompleta
    - no se actualiza parcialmente el stock
    """

    if len(carrito) == 0:
        print("El carrito esta vacio.")
        return

    conexion = conectar()

    if conexion is None:
        return

    cursor = conexion.cursor(dictionary=True)

    try:
        # --------------------------------------------------------
        # 1. Comprobar stock directamente en SQL.
        # FOR UPDATE bloquea las filas durante la transaccion.
        # --------------------------------------------------------
        total = Decimal("0.00")
        productos_verificados = []

        for item in carrito:
            cursor.execute(
                """
                SELECT id, codigo, nombre_titulo, precio, stock
                FROM articulos
                WHERE id = %s
                FOR UPDATE
                """,
                (item["id_articulo"],)
            )

            producto = cursor.fetchone()

            if producto is None:
                raise Exception(
                    f"El articulo {item['codigo']} no existe."
                )

            if producto["stock"] < item["cantidad"]:
                raise Exception(
                    f"No hay suficiente stock de {producto['nombre_titulo']}."
                )

            precio = Decimal(str(producto["precio"]))
            subtotal = precio * item["cantidad"]
            total += subtotal

            productos_verificados.append({
                "id": producto["id"],
                "cantidad": item["cantidad"],
                "precio": precio,
                "subtotal": subtotal
            })

        # --------------------------------------------------------
        # 2. Insertar cabecera de venta.
        # --------------------------------------------------------
        cursor.execute(
            """
            INSERT INTO ventas
            (Id_CL, Id_V, fecha_hora, monto_total)
            VALUES (%s, %s, %s, %s)
            """,
            (
                cliente_id,
                vendedor_id,
                datetime.now(),
                total
            )
        )

        id_venta = cursor.lastrowid

        # --------------------------------------------------------
        # 3. Insertar detalles y actualizar stock.
        # --------------------------------------------------------
        for producto in productos_verificados:

            cursor.execute(
                """
                INSERT INTO detalle_ventas
                (Id_VE, Id_A, cantidad, precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    id_venta,
                    producto["id"],
                    producto["cantidad"],
                    producto["precio"],
                    producto["subtotal"]
                )
            )

            cursor.execute(
                """
                UPDATE articulos
                SET stock = stock - %s
                WHERE id = %s
                """,
                (
                    producto["cantidad"],
                    producto["id"]
                )
            )

        # --------------------------------------------------------
        # 4. Confirmar toda la operacion.
        # --------------------------------------------------------
        conexion.commit()

        carrito.clear()

        print()
        linea()
        print("                  COMPRA REALIZADA")
        linea()
        print("Numero de venta:", id_venta)
        print("Metodo de pago:", metodo_pago)
        print("Total:", moneda(total))
        print("La venta fue guardada en MariaDB.")
        print("El stock tambien fue actualizado en MariaDB.")
        linea()

    except Exception as e:
        conexion.rollback()
        print()
        print("No se pudo registrar la venta.")
        print("Se deshicieron los cambios.")
        print("Detalle:", e)

    finally:
        cerrar_recursos(conexion, cursor)


# ================================================================
# 12. HISTORIAL DE VENTAS
# ================================================================

def obtener_ventas():
    conexion = conectar()

    if conexion is None:
        return []

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                v.id,
                v.fecha_hora,
                v.monto_total,
                c.dni,
                c.nombre AS cliente_nombre,
                c.apellido AS cliente_apellido,
                ve.nombre AS vendedor_nombre,
                ve.apellido AS vendedor_apellido
            FROM ventas v
            INNER JOIN clientes c ON v.Id_CL = c.id
            INNER JOIN vendedores ve ON v.Id_V = ve.id
            ORDER BY v.fecha_hora DESC, v.id DESC
            """
        )

        return cursor.fetchall()

    except Error as e:
        print("Error al obtener ventas:", e)
        return []

    finally:
        cerrar_recursos(conexion, cursor)


def obtener_detalle_venta(id_venta):
    conexion = conectar()

    if conexion is None:
        return []

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                dv.id,
                dv.Id_VE,
                dv.Id_A,
                a.codigo,
                a.nombre_titulo,
                dv.cantidad,
                dv.precio_unitario,
                dv.subtotal
            FROM detalle_ventas dv
            INNER JOIN articulos a ON dv.Id_A = a.id
            WHERE dv.Id_VE = %s
            ORDER BY dv.id
            """,
            (id_venta,)
        )

        return cursor.fetchall()

    except Error as e:
        print("Error al obtener detalle de venta:", e)
        return []

    finally:
        cerrar_recursos(conexion, cursor)


def mostrar_historial():
    ventas = obtener_ventas()

    linea()
    print("                    HISTORIAL DE VENTAS")
    linea()

    if len(ventas) == 0:
        print("Todavia no hay ventas registradas en SQL.")
        return

    for venta in ventas:
        print("VENTA N°", venta["id"])
        print("Fecha:", venta["fecha_hora"])
        print(
            "Cliente:",
            venta["cliente_nombre"],
            venta["cliente_apellido"],
            "- DNI:",
            venta["dni"]
        )
        print(
            "Vendedor:",
            venta["vendedor_nombre"],
            venta["vendedor_apellido"]
        )
        print("Total:", moneda(venta["monto_total"]))

        detalles = obtener_detalle_venta(venta["id"])

        for detalle in detalles:
            print(
                f"  - {detalle['codigo']} | "
                f"{detalle['nombre_titulo']} | "
                f"x{detalle['cantidad']} | "
                f"{moneda(detalle['subtotal'])}"
            )

        print("-" * 80)


def buscar_venta():
    id_venta = leer_entero("Numero de venta: ")

    conexion = conectar()

    if conexion is None:
        return

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                v.id,
                v.fecha_hora,
                v.monto_total,
                c.dni,
                c.nombre AS cliente_nombre,
                c.apellido AS cliente_apellido,
                ve.nombre AS vendedor_nombre,
                ve.apellido AS vendedor_apellido
            FROM ventas v
            INNER JOIN clientes c ON v.Id_CL = c.id
            INNER JOIN vendedores ve ON v.Id_V = ve.id
            WHERE v.id = %s
            """,
            (id_venta,)
        )

        venta = cursor.fetchone()

        if venta is None:
            print("No existe esa venta.")
            return

        linea()
        print("DETALLE DE VENTA", venta["id"])
        linea()
        print("Fecha:", venta["fecha_hora"])
        print(
            "Cliente:",
            venta["cliente_nombre"],
            venta["cliente_apellido"]
        )
        print(
            "Vendedor:",
            venta["vendedor_nombre"],
            venta["vendedor_apellido"]
        )
        print("Total:", moneda(venta["monto_total"]))

        detalles = obtener_detalle_venta(id_venta)

        print("\nARTICULOS:")

        for detalle in detalles:
            print(
                f"{detalle['codigo']} | "
                f"{detalle['nombre_titulo']} | "
                f"Cantidad: {detalle['cantidad']} | "
                f"Subtotal: {moneda(detalle['subtotal'])}"
            )

    except Error as e:
        print("Error al buscar venta:", e)

    finally:
        cerrar_recursos(conexion, cursor)


# ================================================================
# 13. REPORTES SQL
# ================================================================

def reporte_general():
    conexion = conectar()

    if conexion is None:
        return

    cursor = conexion.cursor(dictionary=True)

    try:
        # Cantidad de articulos
        cursor.execute("SELECT COUNT(*) AS cantidad FROM articulos")
        cantidad_articulos = cursor.fetchone()["cantidad"]

        # Cantidad de ventas
        cursor.execute("SELECT COUNT(*) AS cantidad FROM ventas")
        cantidad_ventas = cursor.fetchone()["cantidad"]

        # Unidades vendidas
        cursor.execute(
            """
            SELECT COALESCE(SUM(cantidad), 0) AS cantidad
            FROM detalle_ventas
            """
        )
        unidades = cursor.fetchone()["cantidad"]

        # Dinero recaudado
        cursor.execute(
            """
            SELECT COALESCE(SUM(monto_total), 0) AS total
            FROM ventas
            """
        )
        recaudado = cursor.fetchone()["total"]

        # Stock total
        cursor.execute(
            """
            SELECT COALESCE(SUM(stock), 0) AS stock
            FROM articulos
            """
        )
        stock = cursor.fetchone()["stock"]

        # Agotados
        cursor.execute(
            """
            SELECT COUNT(*) AS cantidad
            FROM articulos
            WHERE stock = 0
            """
        )
        agotados = cursor.fetchone()["cantidad"]

        # Poco stock
        cursor.execute(
            """
            SELECT COUNT(*) AS cantidad
            FROM articulos
            WHERE stock > 0 AND stock <= 3
            """
        )
        poco_stock = cursor.fetchone()["cantidad"]

        linea()
        print("                    REPORTE GENERAL")
        linea()
        print("Articulos en catalogo:", cantidad_articulos)
        print("Cantidad de ventas:", cantidad_ventas)
        print("Unidades vendidas:", unidades)
        print("Dinero recaudado:", moneda(recaudado))
        print("Stock total:", stock)
        print("Productos agotados:", agotados)
        print("Productos con poco stock:", poco_stock)

    except Error as e:
        print("Error en reporte general:", e)

    finally:
        cerrar_recursos(conexion, cursor)


def ranking_productos():
    conexion = conectar()

    if conexion is None:
        return

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                a.id,
                a.codigo,
                a.nombre_titulo,
                SUM(dv.cantidad) AS unidades_vendidas,
                SUM(dv.subtotal) AS dinero_generado
            FROM detalle_ventas dv
            INNER JOIN articulos a ON dv.Id_A = a.id
            GROUP BY
                a.id,
                a.codigo,
                a.nombre_titulo
            ORDER BY unidades_vendidas DESC
            """
        )

        resultados = cursor.fetchall()

        linea()
        print("                    RANKING DE COMICS")
        linea()

        if len(resultados) == 0:
            print("Todavia no hay ventas.")
            return

        posicion = 1

        for producto in resultados:
            print(
                f"{posicion}. "
                f"{producto['codigo']} - "
                f"{producto['nombre_titulo']} | "
                f"Vendidos: {producto['unidades_vendidas']} | "
                f"Recaudado: {moneda(producto['dinero_generado'])}"
            )
            posicion += 1

    except Error as e:
        print("Error en ranking:", e)

    finally:
        cerrar_recursos(conexion, cursor)


def reporte_por_categoria():
    conexion = conectar()

    if conexion is None:
        return

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                c.id,
                c.nombre,
                COUNT(DISTINCT a.id) AS cantidad_articulos,
                COALESCE(SUM(DISTINCT a.stock), 0) AS stock_total
            FROM categorias c
            LEFT JOIN articulos a ON a.Id_C = c.id
            GROUP BY c.id, c.nombre
            ORDER BY c.nombre
            """
        )

        categorias = cursor.fetchall()

        linea()
        print("                 REPORTE POR CATEGORIA")
        linea()

        for categoria in categorias:
            print("Categoria:", categoria["nombre"])
            print("Cantidad de articulos:",
                  categoria["cantidad_articulos"])
            print("Stock total:", categoria["stock_total"])

            cursor.execute(
                """
                SELECT
                    COALESCE(SUM(dv.subtotal), 0) AS total
                FROM detalle_ventas dv
                INNER JOIN articulos a ON dv.Id_A = a.id
                WHERE a.Id_C = %s
                """,
                (categoria["id"],)
            )

            total = cursor.fetchone()["total"]

            print("Dinero vendido:", moneda(total))
            print("-" * 80)

    except Error as e:
        print("Error en reporte por categoria:", e)

    finally:
        cerrar_recursos(conexion, cursor)


def menu_reportes():
    while True:
        print()
        linea()
        print("                         REPORTES")
        linea()
        print("1. Reporte general")
        print("2. Ranking de productos")
        print("3. Reporte por categoria")
        print("4. Volver")
        linea()

        opcion = input("Seleccione una opcion: ")

        if opcion == "1":
            reporte_general()
            pausar()

        elif opcion == "2":
            ranking_productos()
            pausar()

        elif opcion == "3":
            reporte_por_categoria()
            pausar()

        elif opcion == "4":
            break

        else:
            print("Opcion invalida.")


# ================================================================
# 14. INVENTARIO
# ================================================================

def mostrar_inventario():
    productos = obtener_articulos()

    linea()
    print("                        INVENTARIO")
    linea()

    for producto in productos:
        print(
            f"{producto['codigo']} | "
            f"{producto['nombre_titulo']:<35} | "
            f"Stock: {producto['stock']:<3} | "
            f"{estado_stock(producto['stock'])}"
        )


def reponer_stock():
    mostrar_inventario()

    codigo = input("\nCodigo del comic: ")
    producto = buscar_articulo_por_codigo(codigo)

    if producto is None:
        print("No existe ese producto.")
        return

    cantidad = leer_entero("Cantidad a agregar al stock: ")

    if cantidad <= 0:
        print("La cantidad debe ser mayor que 0.")
        return

    conexion = conectar()

    if conexion is None:
        return

    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            UPDATE articulos
            SET stock = stock + %s
            WHERE id = %s
            """,
            (cantidad, producto["id"])
        )

        conexion.commit()

        print(
            "Stock actualizado correctamente en SQL."
        )

    except Error as e:
        conexion.rollback()
        print("Error al actualizar stock:", e)

    finally:
        cerrar_recursos(conexion, cursor)


def establecer_stock():
    mostrar_inventario()

    codigo = input("\nCodigo del comic: ")
    producto = buscar_articulo_por_codigo(codigo)

    if producto is None:
        print("No existe ese producto.")
        return

    cantidad = leer_entero("Nuevo stock: ")

    if cantidad < 0:
        print("El stock no puede ser negativo.")
        return

    conexion = conectar()

    if conexion is None:
        return

    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            UPDATE articulos
            SET stock = %s
            WHERE id = %s
            """,
            (cantidad, producto["id"])
        )

        conexion.commit()
        print("Stock actualizado correctamente en SQL.")

    except Error as e:
        conexion.rollback()
        print("Error al actualizar stock:", e)

    finally:
        cerrar_recursos(conexion, cursor)


def inventario_bajo():
    conexion = conectar()

    if conexion is None:
        return

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, codigo, nombre_titulo, stock
            FROM articulos
            WHERE stock <= 3
            ORDER BY stock ASC
            """
        )

        productos = cursor.fetchall()

        linea()
        print("                  PRODUCTOS CON POCO STOCK")
        linea()

        if len(productos) == 0:
            print("No hay productos con poco stock.")
            return

        for producto in productos:
            print(
                f"{producto['codigo']} | "
                f"{producto['nombre_titulo']} | "
                f"Stock: {producto['stock']}"
            )

    except Error as e:
        print("Error:", e)

    finally:
        cerrar_recursos(conexion, cursor)


def menu_inventario():
    while True:
        print()
        linea()
        print("                       INVENTARIO")
        linea()
        print("1. Ver inventario")
        print("2. Reponer stock")
        print("3. Establecer stock")
        print("4. Ver productos con poco stock")
        print("5. Volver")
        linea()

        opcion = input("Seleccione una opcion: ")

        if opcion == "1":
            mostrar_inventario()
            pausar()

        elif opcion == "2":
            reponer_stock()
            pausar()

        elif opcion == "3":
            establecer_stock()
            pausar()

        elif opcion == "4":
            inventario_bajo()
            pausar()

        elif opcion == "5":
            break

        else:
            print("Opcion invalida.")


# ================================================================
# 15. ADMINISTRACION DE ARTICULOS
# ================================================================

def agregar_articulo():
    linea()
    print("                 AGREGAR NUEVO COMIC")
    linea()

    codigo = input("Codigo: ")

    if buscar_articulo_por_codigo(codigo) is not None:
        print("Ya existe un articulo con ese codigo.")
        return

    nombre = input("Nombre/titulo: ")
    precio = leer_decimal("Precio: ")
    stock = leer_entero("Stock inicial: ")

    if precio < 0:
        print("El precio no puede ser negativo.")
        return

    if stock < 0:
        print("El stock no puede ser negativo.")
        return

    categorias = obtener_categorias()

    if len(categorias) == 0:
        print("No existen categorias en SQL.")
        return

    print("\nCATEGORIAS DISPONIBLES:")

    for categoria in categorias:
        print(
            f"{categoria['id']}. "
            f"{categoria['nombre']}"
        )

    id_categoria = leer_entero("ID de categoria: ")

    categoria = obtener_categoria_por_id(id_categoria)

    if categoria is None:
        print("Categoria invalida.")
        return

    conexion = conectar()

    if conexion is None:
        return

    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO articulos
            (Id_C, codigo, nombre_titulo, precio, stock)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                id_categoria,
                codigo,
                nombre,
                precio,
                stock
            )
        )

        conexion.commit()

        print("Articulo agregado correctamente a MariaDB.")
        print("ID generado:", cursor.lastrowid)

    except Error as e:
        conexion.rollback()
        print("Error al agregar articulo:", e)

    finally:
        cerrar_recursos(conexion, cursor)


def modificar_articulo():
    codigo = input("Codigo del comic: ")
    producto = buscar_articulo_por_codigo(codigo)

    if producto is None:
        print("No existe ese producto.")
        return

    mostrar_producto(producto)

    print()
    print("1. Cambiar codigo")
    print("2. Cambiar nombre")
    print("3. Cambiar precio")
    print("4. Cambiar categoria")
    print("5. Cancelar")

    opcion = input("Seleccione: ")

    if opcion == "5":
        print("Operacion cancelada.")
        return

    conexion = conectar()

    if conexion is None:
        return

    cursor = conexion.cursor()

    try:
        if opcion == "1":
            nuevo_codigo = input("Nuevo codigo: ")

            cursor.execute(
                """
                UPDATE articulos
                SET codigo = %s
                WHERE id = %s
                """,
                (nuevo_codigo, producto["id"])
            )

        elif opcion == "2":
            nuevo_nombre = input("Nuevo nombre/titulo: ")

            cursor.execute(
                """
                UPDATE articulos
                SET nombre_titulo = %s
                WHERE id = %s
                """,
                (nuevo_nombre, producto["id"])
            )

        elif opcion == "3":
            nuevo_precio = leer_decimal("Nuevo precio: ")

            if nuevo_precio < 0:
                print("Precio invalido.")
                return

            cursor.execute(
                """
                UPDATE articulos
                SET precio = %s
                WHERE id = %s
                """,
                (nuevo_precio, producto["id"])
            )

        elif opcion == "4":
            categorias = obtener_categorias()

            for categoria in categorias:
                print(
                    f"{categoria['id']}. "
                    f"{categoria['nombre']}"
                )

            nueva_categoria = leer_entero(
                "Nueva categoria: "
            )

            if obtener_categoria_por_id(nueva_categoria) is None:
                print("Categoria invalida.")
                return

            cursor.execute(
                """
                UPDATE articulos
                SET Id_C = %s
                WHERE id = %s
                """,
                (nueva_categoria, producto["id"])
            )

        else:
            print("Opcion invalida.")
            return

        conexion.commit()
        print("Articulo modificado correctamente en SQL.")

    except Error as e:
        conexion.rollback()
        print("Error al modificar articulo:", e)

    finally:
        cerrar_recursos(conexion, cursor)


def eliminar_articulo():
    codigo = input("Codigo del comic: ")
    producto = buscar_articulo_por_codigo(codigo)

    if producto is None:
        print("No existe ese producto.")
        return

    # Antes de eliminarlo comprobamos si aparece en ventas.
    conexion = conectar()

    if conexion is None:
        return

    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM detalle_ventas
            WHERE Id_A = %s
            """,
            (producto["id"],)
        )

        cantidad = cursor.fetchone()[0]

        if cantidad > 0:
            print(
                "No se puede eliminar este articulo porque "
                "ya aparece en ventas registradas."
            )
            return

        respuesta = input(
            "¿Seguro que desea eliminarlo? (s/n): "
        )

        if respuesta.lower() != "s":
            print("Operacion cancelada.")
            return

        cursor.execute(
            """
            DELETE FROM articulos
            WHERE id = %s
            """,
            (producto["id"],)
        )

        conexion.commit()
        print("Articulo eliminado de MariaDB.")

    except Error as e:
        conexion.rollback()
        print("Error al eliminar articulo:", e)

    finally:
        cerrar_recursos(conexion, cursor)


def menu_administracion():
    while True:
        print()
        linea()
        print("                    ADMINISTRACION")
        linea()
        print("1. Agregar producto")
        print("2. Modificar producto")
        print("3. Eliminar producto")
        print("4. Volver")
        linea()

        opcion = input("Seleccione una opcion: ")

        if opcion == "1":
            agregar_articulo()
            pausar()

        elif opcion == "2":
            modificar_articulo()
            pausar()

        elif opcion == "3":
            eliminar_articulo()
            pausar()

        elif opcion == "4":
            break

        else:
            print("Opcion invalida.")


# ================================================================
# 16. PRESUPUESTO
# ================================================================

def crear_presupuesto():
    seleccionados = []

    linea()
    print("                    PRESUPUESTO")
    linea()

    while True:
        codigo = input(
            "\nCodigo del comic (0 para terminar): "
        )

        if codigo == "0":
            break

        producto = buscar_articulo_por_codigo(codigo)

        if producto is None:
            print("No existe ese comic.")
            continue

        cantidad = leer_entero("Cantidad: ")

        if cantidad <= 0:
            print("Cantidad invalida.")
            continue

        if cantidad > producto["stock"]:
            print("No hay suficiente stock.")
            continue

        seleccionados.append({
            "producto": producto,
            "cantidad": cantidad
        })

        print("Producto agregado al presupuesto.")

    if len(seleccionados) == 0:
        print("No se agregaron productos.")
        return

    total = Decimal("0.00")

    print()
    linea()
    print("DETALLE DEL PRESUPUESTO")
    linea()

    for item in seleccionados:
        producto = item["producto"]
        cantidad = item["cantidad"]

        subtotal = (
            Decimal(str(producto["precio"]))
            * cantidad
        )

        total += subtotal

        print(
            f"{producto['nombre_titulo']} "
            f"x{cantidad} = {moneda(subtotal)}"
        )

    linea()
    print("TOTAL DEL PRESUPUESTO:", moneda(total))


# ================================================================
# 17. INICIO
# ================================================================

def crear_inicio():
    productos = obtener_articulos()

    linea()
    print("                     COMICVERSE")
    print("                 TIENDA DE COMICS")
    linea()

    print("\nBienvenido/a a ComicVerse.")
    print("Los datos mostrados se obtienen desde MariaDB.\n")

    destacados = []

    for producto in productos:
        if producto["stock"] > 0:
            destacados.append(producto)

    print("COMICS DESTACADOS")
    linea()

    contador = 0

    for producto in destacados:
        if contador >= 6:
            break

        print(
            f"{producto['codigo']} | "
            f"{producto['nombre_titulo']}"
        )
        print(
            f"Precio: {moneda(producto['precio'])}"
        )
        print(
            f"Stock: {producto['stock']} | "
            f"{estado_stock(producto['stock'])}"
        )
        print()

        contador += 1

    print(
        "Hay",
        len(productos),
        "articulos cargados desde SQL."
    )

    print(
        "Productos en el carrito:",
        cantidad_productos_carrito()
    )


# ================================================================
# 18. MENU PRINCIPAL
# ================================================================

def menu_principal():
    while True:
        print()
        linea()
        print("                        COMICVERSE")
        print("                    TIENDA DE COMICS")
        linea()
        print("1. Inicio")
        print("2. Catalogo")
        print("3. Buscar comic")
        print("4. Carrito")
        print("5. Inventario")
        print("6. Ventas e historial")
        print("7. Reportes")
        print("8. Crear presupuesto")
        print("9. Administracion")
        print("0. Salir")
        linea()

        opcion = input("Seleccione una opcion: ")

        if opcion == "1":
            crear_inicio()
            pausar()

        elif opcion == "2":
            menu_catalogo()

        elif opcion == "3":
            buscar_productos_menu()
            pausar()

        elif opcion == "4":
            menu_carrito()

        elif opcion == "5":
            menu_inventario()

        elif opcion == "6":
            menu_ventas()

        elif opcion == "7":
            menu_reportes()

        elif opcion == "8":
            crear_presupuesto()
            pausar()

        elif opcion == "9":
            menu_administracion()

        elif opcion == "0":
            print("\nGracias por visitar ComicVerse.")
            print("Programa finalizado.")
            break

        else:
            print("Opcion invalida.")


# ================================================================
# 19. MENU DE VENTAS
# ================================================================

def menu_ventas():
    while True:
        print()
        linea()
        print("                    VENTAS E HISTORIAL")
        linea()
        print("1. Ver historial")
        print("2. Buscar venta")
        print("3. Volver")
        linea()

        opcion = input("Seleccione una opcion: ")

        if opcion == "1":
            mostrar_historial()
            pausar()

        elif opcion == "2":
            buscar_venta()
            pausar()

        elif opcion == "3":
            break

        else:
            print("Opcion invalida.")


# ================================================================
# 20. PRUEBA DE CONEXION
# ================================================================

def iniciar_programa():
    linea()
    print("                COMICVERSE + MARIADB")
    linea()

    print("Comprobando conexion con la base de datos...")

    if not probar_conexion():
        print()
        print("No se puede iniciar el programa.")
        print("Revise DB_CONFIG y que MariaDB este funcionando.")
        return

    print()
    print("La aplicacion utilizara los datos de MariaDB.")
    print("No existe un catalogo hardcodeado en Python.")
    print()

    menu_principal()


# ================================================================
# 21. EJECUCION
# ================================================================

# Para iniciar el programa en Colab:
# iniciar_programa()

# Se deja comentada la ejecucion automatica para que primero
# puedan instalar el conector y configurar DB_CONFIG.
