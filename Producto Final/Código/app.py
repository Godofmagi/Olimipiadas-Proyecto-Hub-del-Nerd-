
import os
import sys
import shutil
import sqlite3
from datetime import datetime


if getattr(sys, "frozen", False):
    CARPETA_DEL_SCRIPT = os.path.dirname(os.path.abspath(sys.executable))
else:
    CARPETA_DEL_SCRIPT = os.path.dirname(os.path.abspath(__file__))

NOMBRE_BASE = os.path.join(CARPETA_DEL_SCRIPT, "tienda_comics.db")
CARPETA_IMAGENES = os.path.join(CARPETA_DEL_SCRIPT, "imagenes")


def conectar():
    conexion = sqlite3.connect(NOMBRE_BASE)
    conexion.execute("PRAGMA foreign_keys = ON")
    _asegurar_columna_imagen(conexion)
    return conexion


def _asegurar_columna_imagen(conexion):
    
    columnas = [fila[1] for fila in conexion.execute("PRAGMA table_info(articulos)")]
    if "imagen" not in columnas:
        conexion.execute("ALTER TABLE articulos ADD COLUMN imagen VARCHAR(255)")
        conexion.commit()


def validar_articulo(codigo, nombre, precio, stock):
    if not codigo.strip():
        raise ValueError("El código no puede estar vacío.")
    if not nombre.strip():
        raise ValueError("El título no puede estar vacío.")
    if precio <= 0:
        raise ValueError("El precio debe ser mayor a 0.")
    if stock < 0:
        raise ValueError("El stock no puede ser negativo.")

def guardar_imagen(ruta_origen, codigo):
    os.makedirs(CARPETA_IMAGENES, exist_ok=True)
    extension = os.path.splitext(ruta_origen)[1].lower()
    nombre_archivo = f"{codigo}{extension}"
    destino = os.path.join(CARPETA_IMAGENES, nombre_archivo)
    shutil.copyfile(ruta_origen, destino)
    return nombre_archivo


def ruta_completa_imagen(nombre_archivo):
    
    if not nombre_archivo:
        return None
    ruta = os.path.join(CARPETA_IMAGENES, nombre_archivo)
    return ruta if os.path.exists(ruta) else None


def obtener_categorias():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM categorias")
    datos = cursor.fetchall()
    conexion.close()
    return datos


def validar_categoria(nombre):
    if not nombre.strip():
        raise ValueError("El nombre de la categoría no puede estar vacío.")


def registrar_categoria(nombre):
    validar_categoria(nombre)
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre.strip(),))
    conexion.commit()
    conexion.close()


def modificar_categoria(id_categoria, nuevo_nombre):
    validar_categoria(nuevo_nombre)
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE categorias SET nombre = ? WHERE id = ?", (nuevo_nombre.strip(), id_categoria)
    )
    conexion.commit()
    encontrada = cursor.rowcount > 0
    conexion.close()
    return encontrada


def eliminar_categoria(id_categoria):
   
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM categorias WHERE id = ?", (id_categoria,))
    conexion.commit()
    encontrada = cursor.rowcount > 0
    conexion.close()
    return encontrada


def listar_articulos():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, codigo, nombre_titulo, precio, stock, imagen FROM articulos")
    datos = cursor.fetchall()  
    conexion.close()
    return datos


def registrar_articulo(id_categoria, codigo, nombre, precio, stock, nombre_imagen=None):
    validar_articulo(codigo, nombre, precio, stock)
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO articulos (Id_C, codigo, nombre_titulo, precio, stock, imagen) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (id_categoria, codigo, nombre, precio, stock, nombre_imagen),
    )
    conexion.commit()
    conexion.close()


def buscar_articulo(codigo):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT id, codigo, nombre_titulo, precio, stock, imagen FROM articulos WHERE codigo = ?",
        (codigo,),
    )
    articulo = cursor.fetchone()
    conexion.close()
    return articulo


def modificar_articulo(codigo, nuevo_precio, nuevo_stock):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE articulos SET precio = ?, stock = ? WHERE codigo = ?",
        (nuevo_precio, nuevo_stock, codigo),
    )
    conexion.commit()
    encontrado = cursor.rowcount > 0
    conexion.close()
    return encontrado


def eliminar_articulo(codigo):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM articulos WHERE codigo = ?", (codigo,))
    conexion.commit()
    encontrado = cursor.rowcount > 0
    conexion.close()
    return encontrado


CAMPOS_ORDEN_ARTICULO = {"precio": 2, "nombre_titulo": 1}


def ordenar_articulos(campo):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT codigo, nombre_titulo, precio, stock, imagen FROM articulos")
    datos = cursor.fetchall()
    conexion.close()
    indice_clave = CAMPOS_ORDEN_ARTICULO.get(campo, 1)
    return ordenar_burbuja(datos, indice_clave, ascendente=True)


def buscar_articulo_binario(codigo):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, codigo, nombre_titulo, precio, stock, imagen FROM articulos")
    datos = cursor.fetchall()
    conexion.close()
    datos_ordenados = ordenar_burbuja(datos, indice_clave=1, ascendente=True)
    return busqueda_binaria(datos_ordenados, indice_clave=1, valor_buscado=codigo)


def filtrar_articulos(categoria):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM categorias")
    mapa_categorias = {id_c: nombre for id_c, nombre in cursor.fetchall()}
    cursor.execute("SELECT Id_C, codigo, nombre_titulo, precio, stock, imagen FROM articulos")
    articulos = cursor.fetchall()
    conexion.close()

    resultado = []
    for id_categoria, codigo, nombre, precio, stock, imagen in articulos:
        if mapa_categorias.get(id_categoria) == categoria:
            resultado.append((codigo, nombre, precio, stock, imagen))
    return resultado


def obtener_precios_y_stock():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT precio, stock FROM articulos")
    datos = cursor.fetchall()
    conexion.close()
    return datos


def calcular_valor_inventario(datos, posicion=0):
    if posicion == len(datos):
        return 0  
    precio, stock = datos[posicion]
    return float(precio) * stock + calcular_valor_inventario(datos, posicion + 1)


# ==============================================================
# Algoritmos genéricos de ordenamiento y búsqueda
# ==============================================================
# Estas dos funciones son de propósito general: no dependen de
# SQLite ni de ninguna tabla en particular. Reciben listas de
# tuplas (las que devuelve cualquier "listar_*") y el índice de la
# posición dentro de cada tupla por el que hay que ordenar/buscar.
# Se implementan "a mano" (sin usar sorted() ni bisect) porque la
# consigna pide demostrar el algoritmo de ordenamiento/búsqueda en
# sí, y no delegar todo el trabajo a la base de datos.
def ordenar_burbuja(datos, indice_clave, ascendente=True):
    lista = list(datos)
    n = len(lista)
    for i in range(n):
        hubo_intercambio = False
        for j in range(0, n - i - 1):
            actual = lista[j][indice_clave]
            siguiente = lista[j + 1][indice_clave]
            fuera_de_orden = actual > siguiente if ascendente else actual < siguiente
            if fuera_de_orden:
                lista[j], lista[j + 1] = lista[j + 1], lista[j]
                hubo_intercambio = True
        if not hubo_intercambio:
            break  # ya está ordenada, no hace falta seguir recorriendo
    return lista


def busqueda_binaria(datos_ordenados, indice_clave, valor_buscado):
    izquierda, derecha = 0, len(datos_ordenados) - 1
    while izquierda <= derecha:
        medio = (izquierda + derecha) // 2
        valor_medio = datos_ordenados[medio][indice_clave]
        if valor_medio == valor_buscado:
            return datos_ordenados[medio]
        elif valor_medio < valor_buscado:
            izquierda = medio + 1
        else:
            derecha = medio - 1
    return None


TURNOS_VALIDOS = ("mañana", "tarde", "noche")


def validar_vendedor(legajo, nombre, apellido, turno):
    if not legajo.strip():
        raise ValueError("El legajo no puede estar vacío.")
    if not nombre.strip():
        raise ValueError("El nombre no puede estar vacío.")
    if not apellido.strip():
        raise ValueError("El apellido no puede estar vacío.")
    if turno not in TURNOS_VALIDOS:
        raise ValueError("El turno debe ser mañana, tarde o noche.")


def registrar_vendedor(legajo, nombre, apellido, turno):
    validar_vendedor(legajo, nombre, apellido, turno)
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO vendedores (legajo, nombre, apellido, turno) VALUES (?, ?, ?, ?)",
        (legajo.strip(), nombre.strip(), apellido.strip(), turno),
    )
    conexion.commit()
    conexion.close()


def listar_vendedores():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT id, legajo, nombre, apellido, turno FROM vendedores ORDER BY apellido, nombre"
    )
    datos = cursor.fetchall()
    conexion.close()
    return datos


def buscar_vendedor_por_legajo(legajo):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT id, legajo, nombre, apellido, turno FROM vendedores WHERE legajo = ?",
        (legajo.strip(),),
    )
    vendedor = cursor.fetchone()
    conexion.close()
    return vendedor


def modificar_vendedor(legajo, nuevo_nombre, nuevo_apellido, nuevo_turno):
    validar_vendedor(legajo, nuevo_nombre, nuevo_apellido, nuevo_turno)
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE vendedores SET nombre = ?, apellido = ?, turno = ? WHERE legajo = ?",
        (nuevo_nombre.strip(), nuevo_apellido.strip(), nuevo_turno, legajo.strip()),
    )
    conexion.commit()
    encontrado = cursor.rowcount > 0
    conexion.close()
    return encontrado


def eliminar_vendedor(legajo):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM vendedores WHERE legajo = ?", (legajo.strip(),))
    conexion.commit()
    encontrado = cursor.rowcount > 0
    conexion.close()
    return encontrado


def validar_cliente(dni, nombre, apellido, email, telefono):
    if not dni.strip():
        raise ValueError("El DNI no puede estar vacío.")
    if not nombre.strip():
        raise ValueError("El nombre no puede estar vacío.")
    if not apellido.strip():
        raise ValueError("El apellido no puede estar vacío.")
    if email.strip() and "@" not in email:
        raise ValueError("El email no es válido.")


def registrar_cliente(dni, nombre, apellido, email="", telefono=""):
    validar_cliente(dni, nombre, apellido, email, telefono)
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO clientes (dni, nombre, apellido, email, telefono) VALUES (?, ?, ?, ?, ?)",
        (dni.strip(), nombre.strip(), apellido.strip(), email.strip(), telefono.strip()),
    )
    conexion.commit()
    conexion.close()


def listar_clientes():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT id, dni, nombre, apellido, email, telefono FROM clientes ORDER BY apellido, nombre"
    )
    datos = cursor.fetchall()
    conexion.close()
    return datos


def buscar_cliente_por_dni(dni):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT id, dni, nombre, apellido, email, telefono FROM clientes WHERE dni = ?",
        (dni.strip(),),
    )
    cliente = cursor.fetchone()
    conexion.close()
    return cliente


def modificar_cliente(dni, nuevo_nombre, nuevo_apellido, nuevo_email="", nuevo_telefono=""):
    validar_cliente(dni, nuevo_nombre, nuevo_apellido, nuevo_email, nuevo_telefono)
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE clientes SET nombre = ?, apellido = ?, email = ?, telefono = ? WHERE dni = ?",
        (
            nuevo_nombre.strip(), nuevo_apellido.strip(),
            nuevo_email.strip(), nuevo_telefono.strip(), dni.strip(),
        ),
    )
    conexion.commit()
    encontrado = cursor.rowcount > 0
    conexion.close()
    return encontrado


def eliminar_cliente(dni):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM clientes WHERE dni = ?", (dni.strip(),))
    conexion.commit()
    encontrado = cursor.rowcount > 0
    conexion.close()
    return encontrado


def registrar_venta(id_cliente, id_vendedor, items):
    if not items:
        raise ValueError("La venta no tiene artículos.")

    conexion = conectar()
    try:
        cursor = conexion.cursor()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO ventas (Id_CL, Id_V, fecha_hora, monto_total) VALUES (?, ?, ?, 0)",
            (id_cliente, id_vendedor, fecha),
        )
        id_venta = cursor.lastrowid

        total = 0.0
        for id_articulo, cantidad in items:
            if cantidad <= 0:
                raise ValueError("La cantidad debe ser mayor a 0.")
            cursor.execute(
                "SELECT nombre_titulo, precio, stock FROM articulos WHERE id = ?",
                (id_articulo,),
            )
            fila = cursor.fetchone()
            if fila is None:
                raise ValueError("Uno de los artículos ya no existe.")
            nombre, precio, stock = fila
            if cantidad > stock:
                raise ValueError(
                    f"Stock insuficiente de '{nombre}' (disponible: {stock})."
                )
            subtotal = round(float(precio) * cantidad, 2)
            cursor.execute(
                "INSERT INTO detalle_ventas (Id_VE, Id_A, cantidad, precio_unitario, subtotal) "
                "VALUES (?, ?, ?, ?, ?)",
                (id_venta, id_articulo, cantidad, precio, subtotal),
            )
            cursor.execute(
                "UPDATE articulos SET stock = stock - ? WHERE id = ?",
                (cantidad, id_articulo),
            )
            total += subtotal

        cursor.execute(
            "UPDATE ventas SET monto_total = ? WHERE id = ?", (round(total, 2), id_venta)
        )
        conexion.commit()
        return id_venta
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def listar_ventas():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT v.id, v.fecha_hora,
                c.nombre || ' ' || c.apellido, c.dni,
                ve.nombre || ' ' || ve.apellido, ve.legajo,
                v.monto_total
        FROM ventas v
        JOIN clientes c ON v.Id_CL = c.id
        JOIN vendedores ve ON v.Id_V = ve.id
        ORDER BY v.id DESC
        """
    )
    datos = cursor.fetchall()
    conexion.close()
    return datos


def obtener_detalle_venta(id_venta):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT a.codigo, a.nombre_titulo, d.cantidad, d.precio_unitario, d.subtotal
        FROM detalle_ventas d
        JOIN articulos a ON d.Id_A = a.id
        WHERE d.Id_VE = ?
        ORDER BY d.id
        """,
        (id_venta,),
    )
    datos = cursor.fetchall()
    conexion.close()
    return datos


class CarritoDeVenta:

    def __init__(self):
        self._items = {}  # {id_articulo: {"codigo", "nombre", "precio", "cantidad"}}

    def agregar_articulo(self, id_articulo, codigo, nombre, precio, stock_disponible):
        if stock_disponible <= 0:
            raise ValueError(f"'{nombre}' no tiene stock disponible.")
        cantidad_actual = self._items[id_articulo]["cantidad"] if id_articulo in self._items else 0
        if cantidad_actual + 1 > stock_disponible:
            raise ValueError(
                f"Stock insuficiente de '{nombre}': disponible {stock_disponible}, "
                f"ya hay {cantidad_actual} en el carrito."
            )
        if id_articulo in self._items:
            self._items[id_articulo]["cantidad"] += 1
        else:
            self._items[id_articulo] = {
                "codigo": codigo, "nombre": nombre,
                "precio": float(precio), "cantidad": 1,
            }

    def quitar_articulo(self, id_articulo):
        self._items.pop(id_articulo, None)

    def vaciar(self):
        self._items.clear()

    def esta_vacio(self):
        return len(self._items) == 0

    def cantidad_de(self, id_articulo):
        return self._items[id_articulo]["cantidad"] if id_articulo in self._items else 0

    def obtener_items(self):
        return [
            (id_a, d["codigo"], d["nombre"], d["precio"], d["cantidad"],
             round(d["precio"] * d["cantidad"], 2))
            for id_a, d in self._items.items()
        ]

    def items_para_venta(self):
        return [(id_a, d["cantidad"]) for id_a, d in self._items.items()]

    def calcular_total(self):
        return round(sum(d["precio"] * d["cantidad"] for d in self._items.values()), 2)


def iniciar_interfaz():
    import customtkinter as ctk
    from tkinter import messagebox, filedialog
    from PIL import Image

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    TAMANO_LISTADO = 160      
    TAMANO_VISTA_PREVIA = 200  

    def crear_ctkimage(ruta, tamano=(150, 150)):
        imagen = Image.open(ruta)
        ancho, alto = imagen.size
        escala = min(tamano[0] / ancho, tamano[1] / alto)
        nuevo_tamano = (max(1, int(ancho * escala)), max(1, int(alto * escala)))
        return ctk.CTkImage(light_image=imagen, dark_image=imagen, size=nuevo_tamano)

    class VentanaPrincipal(ctk.CTk):
        def __init__(self):
            super().__init__()
            self.title("Hub del Friki")
            self.geometry("1000x700")
            self.grid_columnconfigure(1, weight=1)
            self.grid_rowconfigure(1, weight=1)

            barra = ctk.CTkFrame(self, width=210, corner_radius=0)
            barra.grid(row=0, column=0, rowspan=2, sticky="nsew")

            ctk.CTkLabel(
                barra, text="BIENVENIDOS AL\nHUB DEL\nFRIKI", font=ctk.CTkFont(size=20, weight="bold")
            ).pack(pady=(25, 20))

            ctk.CTkButton(
                barra, text="Artículos", command=self.abrir_menu_articulos
            ).pack(padx=15, pady=6, fill="x")
            ctk.CTkButton(
                barra, text="Vendedores", command=self.abrir_menu_vendedores
            ).pack(padx=15, pady=6, fill="x")
            ctk.CTkButton(
                barra, text="Ventas y Clientes", command=self.abrir_menu_ventas_clientes
            ).pack(padx=15, pady=6, fill="x")
            ctk.CTkButton(
                barra, text="Categorías", command=self.accion_categorias
            ).pack(padx=15, pady=6, fill="x")

            # ---- Barra de búsqueda de artículos, arriba del listado ----
            marco_busqueda = ctk.CTkFrame(self, fg_color="transparent")
            marco_busqueda.grid(row=0, column=1, sticky="ew", padx=15, pady=(15, 0))
            marco_busqueda.grid_columnconfigure(0, weight=1)

            self.entry_busqueda_principal = ctk.CTkEntry(
                marco_busqueda, placeholder_text="Buscar artículo por código o título..."
            )
            self.entry_busqueda_principal.grid(row=0, column=0, sticky="ew")
            self.entry_busqueda_principal.bind("<KeyRelease>", self.accion_buscar_principal)
            self.entry_busqueda_principal.bind("<Return>", self.accion_buscar_principal)

            ctk.CTkButton(
                marco_busqueda, text="Buscar", width=90,
                command=self.accion_buscar_principal,
            ).grid(row=0, column=1, padx=(8, 0))

            self.area_resultados = ctk.CTkScrollableFrame(self)
            self.area_resultados.grid(row=1, column=1, sticky="nsew", padx=15, pady=15)
            self.area_resultados.grid_columnconfigure(0, weight=1)

            self.accion_listar()  

        
        def limpiar_area(self):
            for widget in self.area_resultados.winfo_children():
                widget.destroy()

        def mostrar_texto(self, texto):
            self.limpiar_area()
            ctk.CTkLabel(
                self.area_resultados, text=texto, font=ctk.CTkFont(size=14),
                justify="left", anchor="w",
            ).pack(fill="x", padx=10, pady=10)

        def mostrar_articulos(self, articulos, con_id=True):
            self.limpiar_area()
            if not articulos:
                self.mostrar_texto("No hay artículos para mostrar.")
                return

            for a in articulos:
                if con_id:
                    _id, codigo, nombre, precio, stock, imagen = a
                    prefijo = f"[{_id}] "
                else:
                    codigo, nombre, precio, stock, imagen = a
                    prefijo = ""

                fila = ctk.CTkFrame(self.area_resultados)
                fila.pack(fill="x", padx=5, pady=6)

                ruta = ruta_completa_imagen(imagen)
                if ruta:
                    foto = crear_ctkimage(ruta, tamano=(TAMANO_LISTADO, TAMANO_LISTADO))
                    etiqueta_imagen = ctk.CTkLabel(fila, image=foto, text="")
                    etiqueta_imagen.image = foto  
                else:
                    etiqueta_imagen = ctk.CTkLabel(
                        fila, text="Sin\nimagen",
                        width=TAMANO_LISTADO, height=TAMANO_LISTADO,
                        fg_color=("gray85", "gray25"), corner_radius=8,
                    )
                etiqueta_imagen.pack(side="left", padx=10, pady=10)

                texto = f"{prefijo}{codigo} - {nombre}\n$ {precio:.2f}   |   Stock: {stock}"
                ctk.CTkLabel(
                    fila, text=texto, font=ctk.CTkFont(size=14), justify="left", anchor="w",
                ).pack(side="left", padx=10, pady=10, fill="x", expand=True)

        def abrir_menu_articulos(self):
            ventana = ctk.CTkToplevel(self)
            ventana.title("Artículos")
            ventana.geometry("260x460")
            ventana.grab_set()

            ctk.CTkLabel(
                ventana, text="ARTÍCULOS", font=ctk.CTkFont(size=16, weight="bold")
            ).pack(pady=(20, 10))

            opciones = [
                ("Listar artículos", self.accion_listar),
                ("Registrar artículo", self.abrir_registrar),
                ("Buscar por código", self.abrir_buscar),
                ("Modificar artículo", self.abrir_modificar),
                ("Eliminar artículo", self.abrir_eliminar),
                ("Ordenar artículos", self.abrir_ordenar),
                ("Filtrar por categoría", self.abrir_filtrar),
                ("Valor del inventario", self.accion_valor_inventario),
            ]

            def ejecutar(funcion):
                ventana.destroy()
                funcion()

            for texto, funcion in opciones:
                ctk.CTkButton(
                    ventana, text=texto, command=lambda f=funcion: ejecutar(f)
                ).pack(padx=15, pady=5, fill="x")

      
        def accion_listar(self):
            self.entry_busqueda_principal.delete(0, "end")
            self.mostrar_articulos(listar_articulos(), con_id=True)

        def accion_buscar_principal(self, _evento=None):
            texto = self.entry_busqueda_principal.get().strip().lower()
            if not texto:
                self.mostrar_articulos(listar_articulos(), con_id=True)
                return
            encontrados = [
                a for a in listar_articulos()
                if texto in a[1].lower() or texto in a[2].lower()
            ]
            self.mostrar_articulos(encontrados, con_id=True)

        def accion_categorias(self):
            categorias = obtener_categorias()
            self.limpiar_area()
            if not categorias:
                self.mostrar_texto("No hay categorías para mostrar.")
                ctk.CTkButton(
                    self.area_resultados, text="Agregar nueva categoría",
                    command=self.abrir_agregar_categoria,
                ).pack(fill="x", padx=5, pady=(10, 5))
                return

            # Tipografía de historieta: si "Comic Sans MS" no está
            # instalada, CustomTkinter usa la fuente por defecto sin
            # romper nada.
            fuente_titulo = ctk.CTkFont(family="Comic Sans MS", size=22, weight="bold")

            for _id, nombre in categorias:
                tarjeta = ctk.CTkFrame(
                    self.area_resultados, corner_radius=12,
                    border_width=3, border_color="#39D2E6",
                    fg_color=("gray95", "gray17"),
                )
                tarjeta.pack(fill="x", padx=5, pady=8)

                # "Viñeta" numerada, como el número de un cómic.
                ctk.CTkLabel(
                    tarjeta, text=f"N°{_id}",
                    font=ctk.CTkFont(family="Comic Sans MS", size=13, weight="bold"),
                    text_color="#1D1D1D", fg_color="#FFD60A",
                    corner_radius=8, width=52, height=28,
                ).pack(side="left", padx=15, pady=12)

                ctk.CTkLabel(
                    tarjeta, text=nombre.upper(), font=fuente_titulo,
                    text_color="#8483E7", anchor="w",
                ).pack(side="left", padx=(5, 15), pady=12, fill="x", expand=True)

                ctk.CTkButton(
                    tarjeta, text="Editar", width=70,
                    command=lambda i=_id, n=nombre: self.abrir_editar_categoria(i, n),
                ).pack(side="left", padx=(0, 6), pady=12)
                ctk.CTkButton(
                    tarjeta, text="Eliminar", width=80, fg_color="#B3261E",
                    hover_color="#8C1D18",
                    command=lambda i=_id, n=nombre: self.abrir_eliminar_categoria(i, n),
                ).pack(side="left", padx=(0, 15), pady=12)

            ctk.CTkButton(
                self.area_resultados, text="Agregar nueva categoría",
                command=self.abrir_agregar_categoria,
            ).pack(fill="x", padx=5, pady=(10, 5))

        def abrir_editar_categoria(self, id_categoria, nombre_actual):
            ventana = ctk.CTkToplevel(self)
            ventana.title("Editar categoría")
            ventana.geometry("300x180")
            ventana.grab_set()

            ctk.CTkLabel(ventana, text="Nuevo nombre").pack(pady=(25, 5))
            entry_nombre = ctk.CTkEntry(ventana)
            entry_nombre.insert(0, nombre_actual)
            entry_nombre.pack(padx=20, pady=5, fill="x")

            def confirmar():
                try:
                    modificar_categoria(id_categoria, entry_nombre.get())
                    ventana.destroy()
                    self.accion_categorias()
                except ValueError as e:
                    messagebox.showerror("Error de validación", str(e))

            entry_nombre.bind("<Return>", lambda _e: confirmar())
            ctk.CTkButton(ventana, text="Guardar", command=confirmar).pack(pady=20)

        def abrir_eliminar_categoria(self, id_categoria, nombre):
            if not messagebox.askyesno("Confirmar", f"¿Eliminar la categoría '{nombre}'?"):
                return
            try:
                eliminar_categoria(id_categoria)
                self.accion_categorias()
            except sqlite3.IntegrityError:
                messagebox.showerror(
                    "Error",
                    "No se puede eliminar: hay artículos cargados en esa categoría.",
                )

        def abrir_agregar_categoria(self):
            ventana = ctk.CTkToplevel(self)
            ventana.title("Agregar categoría")
            ventana.geometry("300x180")
            ventana.grab_set()

            ctk.CTkLabel(
                ventana, text="Nombre de la categoría"
            ).pack(pady=(25, 5))
            entry_nombre = ctk.CTkEntry(ventana, placeholder_text="Ej: Manga")
            entry_nombre.pack(padx=20, pady=5, fill="x")

            def confirmar():
                try:
                    registrar_categoria(entry_nombre.get())
                    ventana.destroy()
                    self.accion_categorias()
                except ValueError as e:
                    messagebox.showerror("Error de validación", str(e))

            entry_nombre.bind("<Return>", lambda _e: confirmar())
            ctk.CTkButton(ventana, text="Agregar", command=confirmar).pack(pady=20)

        def accion_valor_inventario(self):
            datos = obtener_precios_y_stock()
            total = calcular_valor_inventario(datos)
            self.mostrar_texto(f"Valor total del inventario: $ {round(total, 2)}")

        
        def abrir_registrar(self):
            ventana = ctk.CTkToplevel(self)
            ventana.title("Registrar artículo")
            ventana.geometry("340x640")
            ventana.grab_set()

            categorias = obtener_categorias()
            opciones = [f"{c[0]} - {c[1]}" for c in categorias]

            ctk.CTkLabel(ventana, text="Categoría").pack(pady=(15, 0))
            combo_categoria = ctk.CTkOptionMenu(ventana, values=opciones)
            combo_categoria.pack(pady=5)

            entry_codigo = ctk.CTkEntry(ventana, placeholder_text="Código")
            entry_codigo.pack(pady=6)
            entry_nombre = ctk.CTkEntry(ventana, placeholder_text="Título")
            entry_nombre.pack(pady=6)
            entry_precio = ctk.CTkEntry(ventana, placeholder_text="Precio")
            entry_precio.pack(pady=6)
            entry_stock = ctk.CTkEntry(ventana, placeholder_text="Stock")
            entry_stock.pack(pady=6)


            imagen_elegida = {"ruta": None}

            vista_previa = ctk.CTkLabel(
                ventana, text="Sin imagen\nseleccionada",
                width=TAMANO_VISTA_PREVIA, height=TAMANO_VISTA_PREVIA,
            )
            vista_previa.pack(pady=10)

            def elegir_imagen():
                ruta = filedialog.askopenfilename(
                    title="Seleccionar imagen del artículo",
                    filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp *.webp")],
                )
                if not ruta:
                    return
                imagen_elegida["ruta"] = ruta
                foto = crear_ctkimage(ruta, tamano=(TAMANO_VISTA_PREVIA, TAMANO_VISTA_PREVIA))
                vista_previa.configure(image=foto, text="")
                vista_previa.image = foto  

            ctk.CTkButton(ventana, text="Adjuntar imagen", command=elegir_imagen).pack(pady=5)

            def confirmar():
                try:
                    id_categoria = int(combo_categoria.get().split(" - ")[0])
                    codigo = entry_codigo.get()
                    precio = float(entry_precio.get())
                    stock = int(entry_stock.get())

                    nombre_imagen = None
                    if imagen_elegida["ruta"]:
                        nombre_imagen = guardar_imagen(imagen_elegida["ruta"], codigo)

                    registrar_articulo(
                        id_categoria, codigo, entry_nombre.get(), precio, stock, nombre_imagen
                    )
                    messagebox.showinfo("Éxito", "Artículo registrado correctamente.")
                    ventana.destroy()
                    self.accion_listar()
                except ValueError as e:
                    messagebox.showerror("Error de validación", str(e))
                except sqlite3.IntegrityError:
                    messagebox.showerror("Error", "Ya existe un artículo con ese código.")

            ctk.CTkButton(ventana, text="Registrar", command=confirmar).pack(pady=15)


        def abrir_buscar(self):
            ventana = ctk.CTkToplevel(self)
            ventana.title("Buscar artículo")
            ventana.geometry("320x160")
            ventana.grab_set()

            entry_codigo = ctk.CTkEntry(ventana, placeholder_text="Código a buscar")
            entry_codigo.pack(pady=20)

            def confirmar():
                # Búsqueda binaria manual (ordenar_burbuja + busqueda_binaria)
                # en lugar de un WHERE de SQL.
                articulo = buscar_articulo_binario(entry_codigo.get())
                ventana.destroy()
                if articulo:
                    self.mostrar_articulos([articulo], con_id=True)
                else:
                    self.mostrar_texto("El artículo no existe.")

            ctk.CTkButton(ventana, text="Buscar", command=confirmar).pack(pady=10)

        
        def abrir_modificar(self):
            ventana = ctk.CTkToplevel(self)
            ventana.title("Modificar artículo")
            ventana.geometry("320x260")
            ventana.grab_set()

            entry_codigo = ctk.CTkEntry(ventana, placeholder_text="Código del artículo")
            entry_codigo.pack(pady=8)
            entry_precio = ctk.CTkEntry(ventana, placeholder_text="Nuevo precio")
            entry_precio.pack(pady=8)
            entry_stock = ctk.CTkEntry(ventana, placeholder_text="Nuevo stock")
            entry_stock.pack(pady=8)

            def confirmar():
                try:
                    encontrado = modificar_articulo(
                        entry_codigo.get(), float(entry_precio.get()), int(entry_stock.get())
                    )
                    ventana.destroy()
                    if encontrado:
                        messagebox.showinfo("Éxito", "Artículo modificado.")
                        self.accion_listar()
                    else:
                        messagebox.showwarning("Aviso", "No se encontró el artículo.")
                except ValueError:
                    messagebox.showerror("Error", "Precio y stock deben ser números válidos.")

            ctk.CTkButton(ventana, text="Modificar", command=confirmar).pack(pady=15)

    
        def abrir_eliminar(self):
            ventana = ctk.CTkToplevel(self)
            ventana.title("Eliminar artículo")
            ventana.geometry("320x160")
            ventana.grab_set()

            entry_codigo = ctk.CTkEntry(ventana, placeholder_text="Código a eliminar")
            entry_codigo.pack(pady=20)

            def confirmar():
                codigo = entry_codigo.get()
                if not messagebox.askyesno("Confirmar", f"¿Eliminar el artículo '{codigo}'?"):
                    return
                try:
                    encontrado = eliminar_articulo(codigo)
                except sqlite3.IntegrityError:
                    messagebox.showerror(
                        "Error",
                        "No se puede eliminar: el artículo tiene ventas registradas.",
                    )
                    return
                ventana.destroy()
                if encontrado:
                    messagebox.showinfo("Éxito", "Artículo eliminado.")
                    self.accion_listar()
                else:
                    messagebox.showwarning("Aviso", "Artículo inexistente.")

            ctk.CTkButton(ventana, text="Eliminar", command=confirmar).pack(pady=10)


        def abrir_ordenar(self):
            ventana = ctk.CTkToplevel(self)
            ventana.title("Ordenar artículos")
            ventana.geometry("300x160")
            ventana.grab_set()

            ctk.CTkLabel(ventana, text="Ordenar por:").pack(pady=(20, 5))
            combo = ctk.CTkOptionMenu(ventana, values=["precio", "título"])
            combo.pack(pady=5)

            def confirmar():
                campo = "precio" if combo.get() == "precio" else "nombre_titulo"
                datos = ordenar_articulos(campo)
                ventana.destroy()
                self.mostrar_articulos(datos, con_id=False)

            ctk.CTkButton(ventana, text="Aplicar", command=confirmar).pack(pady=10)


        def abrir_filtrar(self):
            ventana = ctk.CTkToplevel(self)
            ventana.title("Filtrar por categoría")
            ventana.geometry("300x160")
            ventana.grab_set()

            categorias = [c[1] for c in obtener_categorias()]
            combo = ctk.CTkOptionMenu(ventana, values=categorias)
            combo.pack(pady=20)

            def confirmar():
                datos = filtrar_articulos(combo.get())
                ventana.destroy()
                self.mostrar_articulos(datos, con_id=False)

            ctk.CTkButton(ventana, text="Filtrar", command=confirmar).pack(pady=10)


        def _abrir_menu(self, titulo, opciones, alto):
            ventana = ctk.CTkToplevel(self)
            ventana.title(titulo)
            ventana.geometry(f"260x{alto}")
            ventana.grab_set()

            ctk.CTkLabel(
                ventana, text=titulo.upper(), font=ctk.CTkFont(size=16, weight="bold")
            ).pack(pady=(20, 10))

            def ejecutar(funcion):
                ventana.destroy()
                funcion()

            for texto, funcion in opciones:
                ctk.CTkButton(
                    ventana, text=texto, command=lambda f=funcion: ejecutar(f)
                ).pack(padx=15, pady=5, fill="x")

        def mostrar_tarjetas(self, textos, mensaje_vacio):
            self.limpiar_area()
            if not textos:
                self.mostrar_texto(mensaje_vacio)
                return
            for texto in textos:
                fila = ctk.CTkFrame(self.area_resultados)
                fila.pack(fill="x", padx=5, pady=6)
                ctk.CTkLabel(
                    fila, text=texto, font=ctk.CTkFont(size=14), justify="left", anchor="w",
                ).pack(fill="x", padx=15, pady=12)


        def abrir_menu_vendedores(self):
            self._abrir_menu(
                "Vendedores",
                [
                    ("Registrar vendedor", self.abrir_registrar_vendedor),
                    ("Listar vendedores", self.accion_listar_vendedores),
                    ("Modificar vendedor", self.abrir_modificar_vendedor),
                    ("Eliminar vendedor", self.abrir_eliminar_vendedor),
                ],
                alto=280,
            )

        def accion_listar_vendedores(self):
            textos = [
                f"[{_id}] Legajo {legajo} - {apellido}, {nombre}\nTurno: {turno}"
                for _id, legajo, nombre, apellido, turno in listar_vendedores()
            ]
            self.mostrar_tarjetas(textos, "No hay vendedores registrados.")

        def abrir_registrar_vendedor(self):
            ventana = ctk.CTkToplevel(self)
            ventana.title("Registrar vendedor")
            ventana.geometry("340x450")
            ventana.grab_set()

            entry_nombre = ctk.CTkEntry(ventana, placeholder_text="Nombre")
            entry_nombre.pack(pady=(25, 6))
            entry_apellido = ctk.CTkEntry(ventana, placeholder_text="Apellido")
            entry_apellido.pack(pady=6)
            ctk.CTkLabel(ventana, text="Legajo").pack(pady=(10, 0))
            casilla_legajo = ctk.CTkTextbox(ventana, width=260, height=80, wrap="char")
            casilla_legajo.pack(pady=6)

            def leer_legajo():
                texto = casilla_legajo.get("1.0", "end")
                return texto.replace("\n", "").replace("\t", "")

            ctk.CTkLabel(ventana, text="Turno").pack(pady=(10, 0))
            combo_turno = ctk.CTkOptionMenu(ventana, values=list(TURNOS_VALIDOS))
            combo_turno.pack(pady=5)

            def confirmar():
                try:
                    registrar_vendedor(
                        leer_legajo(), entry_nombre.get(),
                        entry_apellido.get(), combo_turno.get(),
                    )
                    messagebox.showinfo("Éxito", "Vendedor registrado correctamente.")
                    ventana.destroy()
                    self.accion_listar_vendedores()
                except ValueError as e:
                    messagebox.showerror("Error de validación", str(e))
                except sqlite3.IntegrityError:
                    messagebox.showerror("Error", "Ya existe un vendedor con ese legajo.")

            ctk.CTkButton(ventana, text="Registrar", command=confirmar).pack(pady=20)

        def abrir_modificar_vendedor(self):
            ventana = ctk.CTkToplevel(self)
            ventana.title("Modificar vendedor")
            ventana.geometry("340x420")
            ventana.grab_set()

            entry_legajo = ctk.CTkEntry(ventana, placeholder_text="Legajo del vendedor")
            entry_legajo.pack(pady=(20, 10), padx=20, fill="x")
            entry_nombre = ctk.CTkEntry(ventana, placeholder_text="Nuevo nombre")
            entry_nombre.pack(pady=6, padx=20, fill="x")
            entry_apellido = ctk.CTkEntry(ventana, placeholder_text="Nuevo apellido")
            entry_apellido.pack(pady=6, padx=20, fill="x")
            ctk.CTkLabel(ventana, text="Nuevo turno").pack(pady=(10, 0))
            combo_turno = ctk.CTkOptionMenu(ventana, values=list(TURNOS_VALIDOS))
            combo_turno.pack(pady=6)

            def cargar_datos():
                vendedor = buscar_vendedor_por_legajo(entry_legajo.get())
                if not vendedor:
                    messagebox.showwarning("Aviso", "No se encontró un vendedor con ese legajo.")
                    return
                _id, legajo, nombre, apellido, turno = vendedor
                entry_nombre.delete(0, "end")
                entry_nombre.insert(0, nombre)
                entry_apellido.delete(0, "end")
                entry_apellido.insert(0, apellido)
                combo_turno.set(turno)

            ctk.CTkButton(ventana, text="Buscar", command=cargar_datos).pack(pady=(6, 10))

            def confirmar():
                try:
                    encontrado = modificar_vendedor(
                        entry_legajo.get(), entry_nombre.get(),
                        entry_apellido.get(), combo_turno.get(),
                    )
                    ventana.destroy()
                    if encontrado:
                        messagebox.showinfo("Éxito", "Vendedor modificado.")
                        self.accion_listar_vendedores()
                    else:
                        messagebox.showwarning("Aviso", "No se encontró el vendedor.")
                except ValueError as e:
                    messagebox.showerror("Error de validación", str(e))

            ctk.CTkButton(ventana, text="Guardar cambios", command=confirmar).pack(pady=10)

        def abrir_eliminar_vendedor(self):
            ventana = ctk.CTkToplevel(self)
            ventana.title("Eliminar vendedor")
            ventana.geometry("320x160")
            ventana.grab_set()

            entry_legajo = ctk.CTkEntry(ventana, placeholder_text="Legajo a eliminar")
            entry_legajo.pack(pady=20)

            def confirmar():
                legajo = entry_legajo.get()
                if not messagebox.askyesno("Confirmar", f"¿Eliminar al vendedor '{legajo}'?"):
                    return
                try:
                    encontrado = eliminar_vendedor(legajo)
                except sqlite3.IntegrityError:
                    messagebox.showerror(
                        "Error", "No se puede eliminar: el vendedor tiene ventas registradas."
                    )
                    return
                ventana.destroy()
                if encontrado:
                    messagebox.showinfo("Éxito", "Vendedor eliminado.")
                    self.accion_listar_vendedores()
                else:
                    messagebox.showwarning("Aviso", "Vendedor inexistente.")

            ctk.CTkButton(ventana, text="Eliminar", command=confirmar).pack(pady=10)

        def abrir_menu_ventas_clientes(self):
            self._abrir_menu(
                "Ventas y clientes",
                [
                    ("Nueva venta", self.abrir_nueva_venta_con_cliente),
                    ("Ver detalle de ventas", self.accion_ver_ventas),
                    ("Listar clientes", self.accion_listar_clientes),
                    ("Modificar cliente", self.abrir_modificar_cliente),
                    ("Eliminar cliente", self.abrir_eliminar_cliente),
                ],
                alto=320,
            )

        def abrir_modificar_cliente(self):
            ventana = ctk.CTkToplevel(self)
            ventana.title("Modificar cliente")
            ventana.geometry("340x480")
            ventana.grab_set()

            entry_dni = ctk.CTkEntry(ventana, placeholder_text="DNI del cliente")
            entry_dni.pack(pady=(20, 10), padx=20, fill="x")
            entry_nombre = ctk.CTkEntry(ventana, placeholder_text="Nuevo nombre")
            entry_nombre.pack(pady=6, padx=20, fill="x")
            entry_apellido = ctk.CTkEntry(ventana, placeholder_text="Nuevo apellido")
            entry_apellido.pack(pady=6, padx=20, fill="x")
            entry_email = ctk.CTkEntry(ventana, placeholder_text="Nuevo email (opcional)")
            entry_email.pack(pady=6, padx=20, fill="x")
            entry_telefono = ctk.CTkEntry(ventana, placeholder_text="Nuevo teléfono (opcional)")
            entry_telefono.pack(pady=6, padx=20, fill="x")

            def cargar_datos():
                cliente = buscar_cliente_por_dni(entry_dni.get())
                if not cliente:
                    messagebox.showwarning("Aviso", "No se encontró un cliente con ese DNI.")
                    return
                _id, dni, nombre, apellido, email, telefono = cliente
                for entry, valor in (
                    (entry_nombre, nombre), (entry_apellido, apellido),
                    (entry_email, email), (entry_telefono, telefono),
                ):
                    entry.delete(0, "end")
                    entry.insert(0, valor or "")

            ctk.CTkButton(ventana, text="Buscar", command=cargar_datos).pack(pady=(6, 10))

            def confirmar():
                try:
                    encontrado = modificar_cliente(
                        entry_dni.get(), entry_nombre.get(), entry_apellido.get(),
                        entry_email.get(), entry_telefono.get(),
                    )
                    ventana.destroy()
                    if encontrado:
                        messagebox.showinfo("Éxito", "Cliente modificado.")
                        self.accion_listar_clientes()
                    else:
                        messagebox.showwarning("Aviso", "No se encontró el cliente.")
                except ValueError as e:
                    messagebox.showerror("Error de validación", str(e))

            ctk.CTkButton(ventana, text="Guardar cambios", command=confirmar).pack(pady=10)

        def abrir_eliminar_cliente(self):
            ventana = ctk.CTkToplevel(self)
            ventana.title("Eliminar cliente")
            ventana.geometry("320x160")
            ventana.grab_set()

            entry_dni = ctk.CTkEntry(ventana, placeholder_text="DNI a eliminar")
            entry_dni.pack(pady=20)

            def confirmar():
                dni = entry_dni.get()
                if not messagebox.askyesno("Confirmar", f"¿Eliminar al cliente DNI '{dni}'?"):
                    return
                try:
                    encontrado = eliminar_cliente(dni)
                except sqlite3.IntegrityError:
                    messagebox.showerror(
                        "Error", "No se puede eliminar: el cliente tiene ventas registradas."
                    )
                    return
                ventana.destroy()
                if encontrado:
                    messagebox.showinfo("Éxito", "Cliente eliminado.")
                    self.accion_listar_clientes()
                else:
                    messagebox.showwarning("Aviso", "Cliente inexistente.")

            ctk.CTkButton(ventana, text="Eliminar", command=confirmar).pack(pady=10)

        def accion_listar_clientes(self):
            textos = []
            for _id, dni, nombre, apellido, email, telefono in listar_clientes():
                contacto = "   |   ".join(x for x in (email, telefono) if x) or "Sin datos de contacto"
                textos.append(f"[{_id}] {apellido}, {nombre} - DNI {dni}\n{contacto}")
            self.mostrar_tarjetas(textos, "No hay clientes registrados.")

        def accion_ver_ventas(self):
            ventas = listar_ventas()
            if not ventas:
                self.mostrar_texto("Todavía no hay ventas registradas.")
                return

            self.limpiar_area()
            for id_venta, fecha, cliente, dni, vendedor, legajo, total in ventas:
                tarjeta = ctk.CTkFrame(self.area_resultados)
                tarjeta.pack(fill="x", padx=5, pady=6)

                encabezado = (
                    f"Venta N° {id_venta}   |   {fecha}\n"
                    f"Cliente: {cliente} (DNI {dni})   |   Vendedor: {vendedor} (legajo {legajo})"
                )
                ctk.CTkLabel(
                    tarjeta, text=encabezado, font=ctk.CTkFont(size=14, weight="bold"),
                    justify="left", anchor="w",
                ).pack(fill="x", padx=15, pady=(12, 6))

                renglones = [
                    f"•  {codigo} - {titulo}:  {cantidad} x $ {precio:.2f}  =  $ {subtotal:.2f}"
                    for codigo, titulo, cantidad, precio, subtotal in obtener_detalle_venta(id_venta)
                ]
                ctk.CTkLabel(
                    tarjeta, text="\n".join(renglones), font=ctk.CTkFont(size=13),
                    justify="left", anchor="w",
                ).pack(fill="x", padx=25)

                ctk.CTkLabel(
                    tarjeta, text=f"TOTAL: $ {total:.2f}",
                    font=ctk.CTkFont(size=14, weight="bold"), anchor="e",
                ).pack(fill="x", padx=15, pady=(6, 12))

        def abrir_nueva_venta_con_cliente(self):
            vendedores = listar_vendedores()
            articulos = listar_articulos()
            if not vendedores:
                messagebox.showwarning("Aviso", "Primero registrá al menos un vendedor.")
                return
            if not articulos:
                messagebox.showwarning("Aviso", "No hay artículos cargados para vender.")
                return

            ventana = ctk.CTkToplevel(self)
            ventana.title("Nueva venta")
            ventana.geometry("900x680")
            ventana.grab_set()
            ventana.grid_columnconfigure(0, weight=1)
            ventana.grid_columnconfigure(1, weight=1)
            ventana.grid_rowconfigure(1, weight=1)

            ctk.CTkLabel(
                ventana, text="NUEVA VENTA", font=ctk.CTkFont(size=18, weight="bold")
            ).grid(row=0, column=0, columnspan=2, pady=(15, 5))


            columna_articulos = ctk.CTkFrame(ventana)
            columna_articulos.grid(row=1, column=0, sticky="nsew", padx=(15, 8), pady=10)
            columna_articulos.grid_rowconfigure(2, weight=1)
            columna_articulos.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                columna_articulos, text="¿Qué artículos comprás?",
                font=ctk.CTkFont(size=15, weight="bold"),
            ).grid(row=0, column=0, pady=(10, 5), padx=10, sticky="w")

            entry_busqueda = ctk.CTkEntry(
                columna_articulos, placeholder_text="Buscar por código o título..."
            )
            entry_busqueda.grid(row=1, column=0, padx=10, pady=(0, 8), sticky="ew")

            lista_articulos = ctk.CTkScrollableFrame(columna_articulos, height=260)
            lista_articulos.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 8))
            lista_articulos.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                columna_articulos, text="Carrito de la venta",
                font=ctk.CTkFont(size=14, weight="bold"),
            ).grid(row=3, column=0, pady=(5, 2), padx=10, sticky="w")

            marco_carrito = ctk.CTkScrollableFrame(columna_articulos, height=150)
            marco_carrito.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0, 5))

            etiqueta_total = ctk.CTkLabel(
                columna_articulos, text="Total: $ 0.00", font=ctk.CTkFont(size=15, weight="bold")
            )
            etiqueta_total.grid(row=5, column=0, pady=(0, 10))

            # El carrito ya no es un diccionario suelto manipulado
            # directamente: es una instancia del TDA CarritoDeVenta,
            # que encapsula su propia estructura interna y solo se
            # opera a través de sus métodos públicos.
            carrito = CarritoDeVenta()

            def redibujar_carrito():
                for widget in marco_carrito.winfo_children():
                    widget.destroy()
                items = carrito.obtener_items()
                if carrito.esta_vacio():
                    ctk.CTkLabel(
                        marco_carrito,
                        text="El carrito está vacío.\nHacé clic en un artículo para agregarlo.",
                        justify="left",
                    ).pack(pady=10)
                for id_a, codigo, nombre, precio, cantidad, subtotal in items:
                    fila = ctk.CTkFrame(marco_carrito)
                    fila.pack(fill="x", pady=2)
                    ctk.CTkLabel(
                        fila,
                        text=f"{codigo} - {nombre}\n"
                             f"{cantidad} x $ {precio:.2f} = $ {subtotal:.2f}",
                        justify="left", anchor="w",
                    ).pack(side="left", padx=8, pady=4, fill="x", expand=True)
                    ctk.CTkButton(
                        fila, text="Quitar", width=60,
                        command=lambda i=id_a: quitar(i),
                    ).pack(side="right", padx=8)
                etiqueta_total.configure(text=f"Total: $ {carrito.calcular_total():.2f}")

            def quitar(id_articulo):
                carrito.quitar_articulo(id_articulo)
                redibujar_carrito()

            def agregar_al_carrito(articulo):
                id_a, codigo, nombre, precio, stock, _imagen = articulo
                try:
                    carrito.agregar_articulo(id_a, codigo, nombre, precio, stock)
                except ValueError as e:
                    messagebox.showerror("Stock insuficiente", str(e))
                    return
                redibujar_carrito()

            def redibujar_lista(filtro=""):
                for widget in lista_articulos.winfo_children():
                    widget.destroy()
                filtro = filtro.strip().lower()
                encontrados = 0
                for a in articulos:
                    _id, codigo, nombre, precio, stock, _imagen = a
                    if filtro and filtro not in codigo.lower() and filtro not in nombre.lower():
                        continue
                    encontrados += 1
                    ctk.CTkButton(
                        lista_articulos,
                        text=f"{codigo} - {nombre}\n$ {precio:.2f}   |   Stock: {stock}",
                        anchor="w", fg_color=("gray80", "gray25"),
                        hover_color=("gray70", "gray35"), text_color=("black", "white"),
                        command=lambda art=a: agregar_al_carrito(art),
                    ).pack(fill="x", pady=3)
                if encontrados == 0:
                    ctk.CTkLabel(lista_articulos, text="No hay artículos que coincidan.").pack(pady=10)

            def al_escribir_busqueda(_evento=None):
                redibujar_lista(entry_busqueda.get())

            entry_busqueda.bind("<KeyRelease>", al_escribir_busqueda)
            # Al presionar Enter también se aplica la búsqueda (por si
            # el usuario prefiere escribir todo y confirmar con Enter
            # en lugar de ver el filtro mientras tipea).
            entry_busqueda.bind("<Return>", al_escribir_busqueda)


            columna_cliente = ctk.CTkFrame(ventana)
            columna_cliente.grid(row=1, column=1, sticky="nsew", padx=(8, 15), pady=10)

            ctk.CTkLabel(
                columna_cliente, text="Datos del cliente",
                font=ctk.CTkFont(size=15, weight="bold"),
            ).pack(pady=(10, 10))

            entry_dni = ctk.CTkEntry(columna_cliente, placeholder_text="DNI")
            entry_dni.pack(padx=15, pady=6, fill="x")
            entry_nombre_cliente = ctk.CTkEntry(columna_cliente, placeholder_text="Nombre")
            entry_nombre_cliente.pack(padx=15, pady=6, fill="x")
            entry_apellido_cliente = ctk.CTkEntry(columna_cliente, placeholder_text="Apellido")
            entry_apellido_cliente.pack(padx=15, pady=6, fill="x")
            entry_email_cliente = ctk.CTkEntry(columna_cliente, placeholder_text="Email (opcional)")
            entry_email_cliente.pack(padx=15, pady=6, fill="x")
            entry_telefono_cliente = ctk.CTkEntry(columna_cliente, placeholder_text="Teléfono (opcional)")
            entry_telefono_cliente.pack(padx=15, pady=6, fill="x")

            ctk.CTkLabel(
                columna_cliente,
                text="Si el DNI ya está registrado,\nse usarán los datos existentes.",
                font=ctk.CTkFont(size=11), text_color=("gray40", "gray70"), justify="center",
            ).pack(pady=(4, 14))

            ctk.CTkLabel(columna_cliente, text="Vendedor que atiende").pack(pady=(5, 0))
            opciones_vendedor = [f"{v[0]} - {v[2]} {v[3]} (legajo {v[1]})" for v in vendedores]
            combo_vendedor = ctk.CTkOptionMenu(columna_cliente, values=opciones_vendedor)
            combo_vendedor.pack(padx=15, pady=8, fill="x")


            def confirmar():
                if carrito.esta_vacio():
                    messagebox.showwarning("Aviso", "El carrito está vacío. Elegí al menos un artículo.")
                    return

                dni = entry_dni.get()
                nombre_cliente = entry_nombre_cliente.get()
                apellido_cliente = entry_apellido_cliente.get()
                email_cliente = entry_email_cliente.get()
                telefono_cliente = entry_telefono_cliente.get()

                try:
                    id_vendedor = int(combo_vendedor.get().split(" - ")[0])
                except (ValueError, IndexError):
                    messagebox.showerror("Error", "Elegí un vendedor.")
                    return

                try:
                    validar_cliente(
                        dni, nombre_cliente, apellido_cliente, email_cliente, telefono_cliente
                    )
                except ValueError as e:
                    messagebox.showerror("Error de validación", str(e))
                    return

                try:
                    cliente_existente = buscar_cliente_por_dni(dni)
                    if cliente_existente:
                        id_cliente = cliente_existente[0]
                    else:
                        registrar_cliente(
                            dni, nombre_cliente, apellido_cliente,
                            email_cliente, telefono_cliente,
                        )
                        id_cliente = buscar_cliente_por_dni(dni)[0]
                    id_venta = registrar_venta(id_cliente, id_vendedor, carrito.items_para_venta())
                except ValueError as e:
                    messagebox.showerror("Error de validación", str(e))
                    return
                except sqlite3.IntegrityError:
                    messagebox.showerror(
                        "Error", "No se pudo registrar la venta (datos inexistentes)."
                    )
                    return

                total = carrito.calcular_total()
                messagebox.showinfo(
                    "Éxito",
                    f"Venta N° {id_venta} registrada.\n"
                    f"Cliente: {nombre_cliente} {apellido_cliente}\n"
                    f"Total: $ {total:.2f}",
                )
                ventana.destroy()
                self.accion_ver_ventas()

            ctk.CTkButton(
                ventana, text="Confirmar venta", command=confirmar, height=40,
                font=ctk.CTkFont(size=14, weight="bold"),
            ).grid(row=2, column=0, columnspan=2, pady=(0, 15))

            redibujar_lista()
            redibujar_carrito()

    app = VentanaPrincipal()
    app.mainloop()


if __name__ == "__main__":
    iniciar_interfaz()