
import os
import sqlite3
import unittest
import tempfile

import app
from app import *



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
        self.assertEqual(calcular_valor_inventario(datos), 123000)


class TestImagenes(unittest.TestCase):
    def test_guardar_y_recuperar_imagen(self):
        with tempfile.TemporaryDirectory() as carpeta_temporal:
            origen = os.path.join(carpeta_temporal, "prueba.png")
            with open(origen, "wb") as f:
                f.write(b"contenido de prueba")

            nombre_guardado = guardar_imagen(origen, "COM-TEST")
            self.assertEqual(nombre_guardado, "COM-TEST.png")

            ruta = ruta_completa_imagen(nombre_guardado)
            self.assertIsNotNone(ruta)
            self.assertTrue(os.path.exists(ruta))


            os.remove(ruta)

    def test_ruta_completa_imagen_inexistente(self):
        self.assertIsNone(ruta_completa_imagen("no_existe.png"))
        self.assertIsNone(ruta_completa_imagen(None))


class TestVendedoresYClientes(unittest.TestCase):
    def test_vendedor_legajo_vacio(self):
        with self.assertRaises(ValueError):
            validar_vendedor("  ", "Ana", "Pérez", "mañana")

    def test_vendedor_turno_invalido(self):
        with self.assertRaises(ValueError):
            validar_vendedor("V01", "Ana", "Pérez", "madrugada")

    def test_vendedor_valido_no_lanza_error(self):
        try:
            validar_vendedor("V01", "Ana", "Pérez", "tarde")
        except ValueError:
            self.fail("No debería lanzar error con datos válidos.")

    def test_cliente_dni_vacio(self):
        with self.assertRaises(ValueError):
            validar_cliente("", "Juan", "Gómez", "", "")

    def test_cliente_email_invalido(self):
        with self.assertRaises(ValueError):
            validar_cliente("30111222", "Juan", "Gómez", "juan.com", "")

    def test_cliente_sin_email_ni_telefono_es_valido(self):
        try:
            validar_cliente("30111222", "Juan", "Gómez", "", "")
        except ValueError:
            self.fail("El email y el teléfono son opcionales.")


class TestAlgoritmosDeOrdenYBusqueda(unittest.TestCase):
    """Prueban ordenar_burbuja() y busqueda_binaria() de forma
    completamente aislada de la base de datos, con listas de
    tuplas armadas a mano."""

    def test_ordenar_burbuja_ascendente_por_precio(self):
        datos = [("C", "Akira", 500), ("A", "Watchmen", 1000), ("B", "Maus", 700)]
        ordenado = ordenar_burbuja(datos, indice_clave=2, ascendente=True)
        self.assertEqual([d[2] for d in ordenado], [500, 700, 1000])

    def test_ordenar_burbuja_descendente_por_nombre(self):
        datos = [("A", "Akira"), ("B", "Watchmen"), ("C", "Maus")]
        ordenado = ordenar_burbuja(datos, indice_clave=1, ascendente=False)
        self.assertEqual([d[1] for d in ordenado], ["Watchmen", "Maus", "Akira"])

    def test_ordenar_burbuja_no_modifica_la_lista_original(self):
        datos = [(2,), (1,), (3,)]
        ordenar_burbuja(datos, indice_clave=0)
        self.assertEqual(datos, [(2,), (1,), (3,)])

    def test_ordenar_burbuja_lista_vacia(self):
        self.assertEqual(ordenar_burbuja([], indice_clave=0), [])

    def test_busqueda_binaria_encuentra_elemento(self):
        datos_ordenados = [("A01",), ("A02",), ("A03",), ("A04",)]
        encontrado = busqueda_binaria(datos_ordenados, indice_clave=0, valor_buscado="A03")
        self.assertEqual(encontrado, ("A03",))

    def test_busqueda_binaria_elemento_inexistente(self):
        datos_ordenados = [("A01",), ("A02",), ("A03",)]
        self.assertIsNone(busqueda_binaria(datos_ordenados, indice_clave=0, valor_buscado="Z99"))

    def test_busqueda_binaria_lista_vacia(self):
        self.assertIsNone(busqueda_binaria([], indice_clave=0, valor_buscado="A01"))


class TestCarritoDeVentaTDA(unittest.TestCase):
    """Prueban el TDA CarritoDeVenta de forma aislada, sin tocar la
    base de datos ni la interfaz gráfica."""

    def test_carrito_nuevo_esta_vacio(self):
        carrito = CarritoDeVenta()
        self.assertTrue(carrito.esta_vacio())
        self.assertEqual(carrito.calcular_total(), 0)
        self.assertEqual(carrito.obtener_items(), [])

    def test_agregar_articulo_una_vez(self):
        carrito = CarritoDeVenta()
        carrito.agregar_articulo(1, "A01", "Watchmen", 1000, stock_disponible=5)
        self.assertFalse(carrito.esta_vacio())
        self.assertEqual(carrito.cantidad_de(1), 1)
        self.assertEqual(carrito.calcular_total(), 1000)

    def test_agregar_articulo_repetido_suma_cantidad(self):
        carrito = CarritoDeVenta()
        carrito.agregar_articulo(1, "A01", "Watchmen", 1000, stock_disponible=5)
        carrito.agregar_articulo(1, "A01", "Watchmen", 1000, stock_disponible=5)
        self.assertEqual(carrito.cantidad_de(1), 2)
        self.assertEqual(carrito.calcular_total(), 2000)

    def test_agregar_articulo_sin_stock_lanza_error(self):
        carrito = CarritoDeVenta()
        with self.assertRaises(ValueError):
            carrito.agregar_articulo(1, "A01", "Watchmen", 1000, stock_disponible=0)

    def test_agregar_mas_alla_del_stock_disponible_lanza_error(self):
        carrito = CarritoDeVenta()
        carrito.agregar_articulo(1, "A01", "Watchmen", 1000, stock_disponible=1)
        with self.assertRaises(ValueError):
            carrito.agregar_articulo(1, "A01", "Watchmen", 1000, stock_disponible=1)

    def test_quitar_articulo(self):
        carrito = CarritoDeVenta()
        carrito.agregar_articulo(1, "A01", "Watchmen", 1000, stock_disponible=5)
        carrito.quitar_articulo(1)
        self.assertTrue(carrito.esta_vacio())

    def test_vaciar_carrito(self):
        carrito = CarritoDeVenta()
        carrito.agregar_articulo(1, "A01", "Watchmen", 1000, stock_disponible=5)
        carrito.agregar_articulo(2, "A02", "Akira", 500, stock_disponible=5)
        carrito.vaciar()
        self.assertTrue(carrito.esta_vacio())

    def test_items_para_venta_tiene_el_formato_correcto(self):
        carrito = CarritoDeVenta()
        carrito.agregar_articulo(1, "A01", "Watchmen", 1000, stock_disponible=5)
        carrito.agregar_articulo(1, "A01", "Watchmen", 1000, stock_disponible=5)
        self.assertEqual(carrito.items_para_venta(), [(1, 2)])


class TestVentas(unittest.TestCase):
    """Usan una base temporal (con las mismas tablas), así que no tocan
    tienda_comics.db."""

    def setUp(self):
        self._base_original = app.NOMBRE_BASE
        self._carpeta = tempfile.TemporaryDirectory()
        app.NOMBRE_BASE = os.path.join(self._carpeta.name, "prueba.db")
        con = sqlite3.connect(app.NOMBRE_BASE)
        con.executescript(
            """
            CREATE TABLE categorias (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre VARCHAR(50), descripcion VARCHAR(150));
            CREATE TABLE articulos (
                id INTEGER PRIMARY KEY AUTOINCREMENT, Id_C INTEGER NOT NULL,
                codigo VARCHAR(50) UNIQUE, nombre_titulo VARCHAR(100),
                precio DECIMAL(10,2), stock INTEGER NOT NULL DEFAULT 0, imagen VARCHAR(255),
                FOREIGN KEY (Id_C) REFERENCES categorias(id));
            CREATE TABLE clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, dni VARCHAR(20) UNIQUE,
                nombre VARCHAR(50), apellido VARCHAR(50), email VARCHAR(100), telefono VARCHAR(20));
            CREATE TABLE vendedores (id INTEGER PRIMARY KEY AUTOINCREMENT, legajo VARCHAR(20) UNIQUE,
                nombre VARCHAR(50), apellido VARCHAR(50),
                turno VARCHAR(10) CHECK (turno IN ('mañana','tarde','noche')));
            CREATE TABLE ventas (id INTEGER PRIMARY KEY AUTOINCREMENT, Id_CL INTEGER NOT NULL,
                Id_V INTEGER NOT NULL, fecha_hora DATETIME, monto_total DECIMAL(10,2),
                FOREIGN KEY (Id_CL) REFERENCES clientes(id), FOREIGN KEY (Id_V) REFERENCES vendedores(id));
            CREATE TABLE detalle_ventas (id INTEGER PRIMARY KEY AUTOINCREMENT, Id_VE INTEGER NOT NULL,
                Id_A INTEGER NOT NULL, cantidad INTEGER NOT NULL, precio_unitario DECIMAL(10,2) NOT NULL,
                subtotal DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (Id_VE) REFERENCES ventas(id), FOREIGN KEY (Id_A) REFERENCES articulos(id));
            INSERT INTO categorias (nombre) VALUES ('Cómics');
            INSERT INTO articulos (Id_C, codigo, nombre_titulo, precio, stock) VALUES (1, 'A01', 'Watchmen', 1000, 5);
            INSERT INTO articulos (Id_C, codigo, nombre_titulo, precio, stock) VALUES (1, 'A02', 'Akira', 500, 3);
            INSERT INTO clientes (dni, nombre, apellido) VALUES ('30111222', 'Juan', 'Gómez');
            INSERT INTO vendedores (legajo, nombre, apellido, turno) VALUES ('V01', 'Ana', 'Pérez', 'tarde');
            """
        )
        con.commit()
        con.close()

    def tearDown(self):
        app.NOMBRE_BASE = self._base_original
        self._carpeta.cleanup()

    def _stock(self, id_articulo):
        con = sqlite3.connect(app.NOMBRE_BASE)
        stock = con.execute("SELECT stock FROM articulos WHERE id = ?", (id_articulo,)).fetchone()[0]
        con.close()
        return stock

    def test_venta_calcula_total_detalle_y_descuenta_stock(self):
        id_venta = registrar_venta(1, 1, [(1, 2), (2, 1)])
        ventas = listar_ventas()
        self.assertEqual(len(ventas), 1)
        self.assertEqual(ventas[0][0], id_venta)
        self.assertEqual(ventas[0][6], 2500)
        self.assertEqual(len(obtener_detalle_venta(id_venta)), 2)
        self.assertEqual(self._stock(1), 3)
        self.assertEqual(self._stock(2), 2)

    def test_stock_insuficiente_deshace_toda_la_venta(self):
        with self.assertRaises(ValueError):
            registrar_venta(1, 1, [(1, 2), (2, 99)])
        self.assertEqual(listar_ventas(), [])
        self.assertEqual(self._stock(1), 5)
        self.assertEqual(self._stock(2), 3)

    def test_venta_sin_articulos(self):
        with self.assertRaises(ValueError):
            registrar_venta(1, 1, [])

    def test_cantidad_invalida(self):
        with self.assertRaises(ValueError):
            registrar_venta(1, 1, [(1, 0)])
        self.assertEqual(listar_ventas(), [])

    def test_cliente_inexistente(self):
        with self.assertRaises(sqlite3.IntegrityError):
            registrar_venta(999, 1, [(1, 1)])
        self.assertEqual(self._stock(1), 5)


class TestCRUDCompleto(unittest.TestCase):

    def setUp(self):
        self._base_original = app.NOMBRE_BASE
        self._carpeta = tempfile.TemporaryDirectory()
        app.NOMBRE_BASE = os.path.join(self._carpeta.name, "prueba_crud.db")
        con = sqlite3.connect(app.NOMBRE_BASE)
        con.executescript(
            """
            CREATE TABLE categorias (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre VARCHAR(50), descripcion VARCHAR(150));
            CREATE TABLE articulos (
                id INTEGER PRIMARY KEY AUTOINCREMENT, Id_C INTEGER NOT NULL,
                codigo VARCHAR(50) UNIQUE, nombre_titulo VARCHAR(100),
                precio DECIMAL(10,2), stock INTEGER NOT NULL DEFAULT 0, imagen VARCHAR(255),
                FOREIGN KEY (Id_C) REFERENCES categorias(id));
            CREATE TABLE clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, dni VARCHAR(20) UNIQUE,
                nombre VARCHAR(50), apellido VARCHAR(50), email VARCHAR(100), telefono VARCHAR(20));
            CREATE TABLE vendedores (id INTEGER PRIMARY KEY AUTOINCREMENT, legajo VARCHAR(20) UNIQUE,
                nombre VARCHAR(50), apellido VARCHAR(50),
                turno VARCHAR(10) CHECK (turno IN ('mañana','tarde','noche')));
            CREATE TABLE ventas (id INTEGER PRIMARY KEY AUTOINCREMENT, Id_CL INTEGER NOT NULL,
                Id_V INTEGER NOT NULL, fecha_hora DATETIME, monto_total DECIMAL(10,2),
                FOREIGN KEY (Id_CL) REFERENCES clientes(id), FOREIGN KEY (Id_V) REFERENCES vendedores(id));
            CREATE TABLE detalle_ventas (id INTEGER PRIMARY KEY AUTOINCREMENT, Id_VE INTEGER NOT NULL,
                Id_A INTEGER NOT NULL, cantidad INTEGER NOT NULL, precio_unitario DECIMAL(10,2) NOT NULL,
                subtotal DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (Id_VE) REFERENCES ventas(id), FOREIGN KEY (Id_A) REFERENCES articulos(id));
            INSERT INTO categorias (nombre) VALUES ('Cómics');
            INSERT INTO categorias (nombre) VALUES ('Manga');
            INSERT INTO categorias (nombre) VALUES ('Sin artículos');
            INSERT INTO articulos (Id_C, codigo, nombre_titulo, precio, stock) VALUES (1, 'A01', 'Watchmen', 1000, 5);
            INSERT INTO articulos (Id_C, codigo, nombre_titulo, precio, stock) VALUES (2, 'A02', 'Akira', 500, 3);
            INSERT INTO clientes (dni, nombre, apellido) VALUES ('30111222', 'Juan', 'Gómez');
            INSERT INTO vendedores (legajo, nombre, apellido, turno) VALUES ('V01', 'Ana', 'Pérez', 'tarde');
            """
        )
        con.commit()
        con.close()

    def tearDown(self):
        app.NOMBRE_BASE = self._base_original
        self._carpeta.cleanup()

    # ---- Categorías ----
    def test_modificar_categoria(self):
        id_categoria = obtener_categorias()[0][0]
        self.assertTrue(modificar_categoria(id_categoria, "Historieta"))
        nombres = [n for _id, n in obtener_categorias()]
        self.assertIn("Historieta", nombres)

    def test_eliminar_categoria_sin_articulos(self):
        id_categoria = obtener_categorias()[2][0]  # 'Sin artículos', sin artículos cargados
        self.assertTrue(eliminar_categoria(id_categoria))

    def test_eliminar_categoria_con_articulos_lanza_integrity_error(self):
        id_categoria = obtener_categorias()[0][0]  # 'Cómics', tiene a Watchmen
        with self.assertRaises(sqlite3.IntegrityError):
            eliminar_categoria(id_categoria)

    # ---- Vendedores ----
    def test_modificar_vendedor(self):
        self.assertTrue(modificar_vendedor("V01", "Ana", "Pérez", "noche"))
        vendedor = buscar_vendedor_por_legajo("V01")
        self.assertEqual(vendedor[4], "noche")

    def test_modificar_vendedor_con_turno_invalido_lanza_error(self):
        with self.assertRaises(ValueError):
            modificar_vendedor("V01", "Ana", "Pérez", "madrugada")

    def test_eliminar_vendedor(self):
        self.assertTrue(eliminar_vendedor("V01"))
        self.assertIsNone(buscar_vendedor_por_legajo("V01"))

    def test_eliminar_vendedor_con_ventas_lanza_integrity_error(self):
        registrar_venta(1, 1, [(1, 1)])
        with self.assertRaises(sqlite3.IntegrityError):
            eliminar_vendedor("V01")

    # ---- Clientes ----
    def test_modificar_cliente(self):
        self.assertTrue(
            modificar_cliente("30111222", "Juan", "Gómez", "juan@mail.com", "1122334455")
        )
        cliente = buscar_cliente_por_dni("30111222")
        self.assertEqual(cliente[4], "juan@mail.com")

    def test_modificar_cliente_con_email_invalido_lanza_error(self):
        with self.assertRaises(ValueError):
            modificar_cliente("30111222", "Juan", "Gómez", "no-es-email", "")

    def test_eliminar_cliente(self):
        self.assertTrue(eliminar_cliente("30111222"))
        self.assertIsNone(buscar_cliente_por_dni("30111222"))

    def test_eliminar_cliente_con_ventas_lanza_integrity_error(self):
        registrar_venta(1, 1, [(1, 1)])
        with self.assertRaises(sqlite3.IntegrityError):
            eliminar_cliente("30111222")

    # ---- Ordenamiento, búsqueda y filtrado que ya no delegan 100% en SQL ----
    def test_ordenar_articulos_por_precio_usa_ordenamiento_manual(self):
        datos = ordenar_articulos("precio")
        self.assertEqual([d[2] for d in datos], [500, 1000])  # Akira (500) antes que Watchmen (1000)

    def test_buscar_articulo_binario_encuentra(self):
        articulo = buscar_articulo_binario("A02")
        self.assertIsNotNone(articulo)
        self.assertEqual(articulo[2], "Akira")

    def test_buscar_articulo_binario_no_encuentra(self):
        self.assertIsNone(buscar_articulo_binario("Z99"))

    def test_filtrar_articulos_por_categoria_manual(self):
        resultado = filtrar_articulos("Manga")
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0][1], "Akira")


if __name__ == "__main__":
    unittest.main(verbosity=2)
