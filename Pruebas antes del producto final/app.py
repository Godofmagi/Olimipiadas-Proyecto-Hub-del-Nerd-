"""
app.py
Sistema de administración de una tienda de cómics — versión con
interfaz gráfica (CustomTkinter) sobre base de datos SQLite, con
soporte para adjuntar una imagen a cada artículo, y con módulos de
clientes, vendedores y ventas (con su detalle).
E.E.S.T. N°6 "Chacabuco" - Olimpiadas Institucionales 2026.

Las imágenes que se adjuntan al registrar un artículo se copian a
la carpeta 'imagenes/' (al lado de este script) y el nombre de ese
archivo se guarda en la base de datos. Así, la imagen queda
disponible aunque se cierre y se vuelva a abrir el programa.

Instalar antes de ejecutar:   pip install customtkinter pillow
Ejecutar la aplicación:       python3 app.py
Ejecutar los casos de prueba:  python3 app.py test
"""
import sys
import os
import shutil
import sqlite3
import unittest
import tempfile
from datetime import datetime

# Rutas absolutas calculadas a partir de la ubicación de este
# archivo (no del directorio desde donde se ejecute la terminal),
# para que el programa siempre encuentre la base y la carpeta de
# imágenes sin importar cómo se lo invoque.
CARPETA_DEL_SCRIPT = os.path.dirname(os.path.abspath(__file__))
NOMBRE_BASE = os.path.join(CARPETA_DEL_SCRIPT, "tienda_comics.db")
CARPETA_IMAGENES = os.path.join(CARPETA_DEL_SCRIPT, "imagenes")


def conectar():
    """Función encargada exclusivamente de conectar con la base de
    datos, para que el resto de las funciones no repitan este código."""
    conexion = sqlite3.connect(NOMBRE_BASE)
    conexion.execute("PRAGMA foreign_keys = ON")
    _asegurar_columna_imagen(conexion)
    return conexion


def _asegurar_columna_imagen(conexion):
    """Agrega la columna 'imagen' a la tabla articulos si todavía no
    existe. Así, si alguien abre una base creada antes de esta
    versión, el programa la actualiza solo sin perder los datos que
    ya tenía cargados."""
    columnas = [fila[1] for fila in conexion.execute("PRAGMA table_info(articulos)")]
    if "imagen" not in columnas:
        conexion.execute("ALTER TABLE articulos ADD COLUMN imagen VARCHAR(255)")
        conexion.commit()


# ------------------------------------------------------------
# Validación (control de datos inválidos) — SIN CAMBIOS
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


# ------------------------------------------------------------
# Manejo de imágenes
# ------------------------------------------------------------
def guardar_imagen(ruta_origen, codigo):
    """Copia la imagen elegida por el usuario a la carpeta imagenes/,
    con un nombre basado en el código del artículo (para que sea
    fácil de identificar y no se pisen entre sí). Devuelve el
    nombre de archivo guardado -no la ruta completa-, que es lo que
    se almacena en la base de datos."""
    os.makedirs(CARPETA_IMAGENES, exist_ok=True)
    extension = os.path.splitext(ruta_origen)[1].lower()
    nombre_archivo = f"{codigo}{extension}"
    destino = os.path.join(CARPETA_IMAGENES, nombre_archivo)
    shutil.copyfile(ruta_origen, destino)
    return nombre_archivo


def ruta_completa_imagen(nombre_archivo):
    """Devuelve la ruta absoluta a una imagen guardada, o None si no
    hay imagen asociada o el archivo ya no existe en disco."""
    if not nombre_archivo:
        return None
    ruta = os.path.join(CARPETA_IMAGENES, nombre_archivo)
    return ruta if os.path.exists(ruta) else None


# ------------------------------------------------------------
# Lógica de negocio (ABM, búsqueda, orden, filtrado)
# ------------------------------------------------------------
def obtener_categorias():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM categorias")
    datos = cursor.fetchall()
    conexion.close()
    return datos


def listar_articulos():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, codigo, nombre_titulo, precio, stock, imagen FROM articulos")
    datos = cursor.fetchall()  # lista de tuplas: nuestra estructura de datos
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


def ordenar_articulos(campo):
    """campo: 'precio' o 'nombre_titulo'"""
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        f"SELECT codigo, nombre_titulo, precio, stock, imagen FROM articulos ORDER BY {campo} ASC"
    )
    datos = cursor.fetchall()
    conexion.close()
    return datos


def filtrar_articulos(categoria):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT a.codigo, a.nombre_titulo, a.precio, a.stock, a.imagen
        FROM articulos a
        JOIN categorias c ON a.Id_C = c.id
        WHERE c.nombre = ?
        """,
        (categoria,),
    )
    datos = cursor.fetchall()
    conexion.close()
    return datos


# ------------------------------------------------------------
# RECURSIVIDAD: valor total del inventario — SIN CAMBIOS
# ------------------------------------------------------------
def obtener_precios_y_stock():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT precio, stock FROM articulos")
    datos = cursor.fetchall()
    conexion.close()
    return datos


def calcular_valor_inventario(datos, posicion=0):
    if posicion == len(datos):
        return 0  # caso base: no quedan artículos por sumar
    precio, stock = datos[posicion]
    return float(precio) * stock + calcular_valor_inventario(datos, posicion + 1)


# ------------------------------------------------------------
# Vendedores
# ------------------------------------------------------------
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


# ------------------------------------------------------------
# Clientes (hacen falta para poder registrar una venta)
# ------------------------------------------------------------
def validar_cliente(dni, nombre, apellido, email, telefono):
    if not dni.strip():
        raise ValueError("El DNI no puede estar vacío.")
    if not nombre.strip():
        raise ValueError("El nombre no puede estar vacío.")
    if not apellido.strip():
        raise ValueError("El apellido no puede estar vacío.")
    # El email y el teléfono son opcionales, pero si se cargan el
    # email tiene que parecer un email.
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
    """Devuelve la fila del cliente con ese DNI, o None si no existe.
    Se usa en la pantalla combinada de 'Nueva venta' para saber si un
    cliente ya estaba registrado (y así no duplicarlo) o si hay que
    darlo de alta."""
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT id, dni, nombre, apellido, email, telefono FROM clientes WHERE dni = ?",
        (dni.strip(),),
    )
    cliente = cursor.fetchone()
    conexion.close()
    return cliente


# ------------------------------------------------------------
# Ventas y detalle de ventas
# ------------------------------------------------------------
def registrar_venta(id_cliente, id_vendedor, items):
    """Registra una venta completa. 'items' es una lista de tuplas
    (id_articulo, cantidad). Todo ocurre dentro de UNA sola
    transacción: se crea la venta, se cargan sus renglones en
    detalle_ventas, se descuenta el stock y se guarda el total. Si
    algo falla (por ejemplo, no alcanza el stock de un artículo) se
    deshace todo y no queda nada a medias en la base.
    Devuelve el id de la venta creada."""
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
    """Devuelve las ventas (la más nueva primero) con los datos del
    cliente y del vendedor. El detalle de cada una se pide aparte
    con obtener_detalle_venta()."""
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


# ==============================================================
# INTERFAZ GRÁFICA (CustomTkinter)
# ==============================================================
def iniciar_interfaz():
    import customtkinter as ctk
    from tkinter import messagebox, filedialog
    from PIL import Image

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Tamaños de las imágenes (en píxeles). Cambiá estos números para
    # agrandar o achicar las imágenes en toda la aplicación.
    TAMANO_LISTADO = 160      # imágenes en la lista de artículos
    TAMANO_VISTA_PREVIA = 200  # vista previa al registrar un artículo

    def crear_ctkimage(ruta, tamano=(150, 150)):
        """Abre una imagen con PIL y la devuelve lista para usar en
        un CTkLabel, escalada para entrar en 'tamano' sin deformarse.
        A diferencia de thumbnail(), también puede AGRANDAR imágenes
        chicas."""
        imagen = Image.open(ruta)
        ancho, alto = imagen.size
        escala = min(tamano[0] / ancho, tamano[1] / alto)
        nuevo_tamano = (max(1, int(ancho * escala)), max(1, int(alto * escala)))
        return ctk.CTkImage(light_image=imagen, dark_image=imagen, size=nuevo_tamano)

    class VentanaPrincipal(ctk.CTk):
        def __init__(self):
            super().__init__()
            self.title("Tienda de Cómics")
            self.geometry("1000x700")
            self.grid_columnconfigure(1, weight=1)
            self.grid_rowconfigure(0, weight=1)

            # ---- Barra lateral con las acciones ----
            barra = ctk.CTkFrame(self, width=210, corner_radius=0)
            barra.grid(row=0, column=0, sticky="nsew")

            ctk.CTkLabel(
                barra, text="TIENDA DE\nCÓMICS", font=ctk.CTkFont(size=20, weight="bold")
            ).pack(pady=(25, 20))

            # ---- Barra lateral: un botón por grupo de funciones ----
            # Cada botón abre su propio menú.
            ctk.CTkButton(
                barra, text="Artículos", command=self.abrir_menu_articulos
            ).pack(padx=15, pady=6, fill="x")
            ctk.CTkButton(
                barra, text="Vendedores", command=self.abrir_menu_vendedores
            ).pack(padx=15, pady=6, fill="x")
            ctk.CTkButton(
                barra, text="Ventas y Clientes", command=self.abrir_menu_ventas_clientes
            ).pack(padx=15, pady=6, fill="x")

            # ---- Área principal: panel de tarjetas (imagen + texto) ----
            self.area_resultados = ctk.CTkScrollableFrame(self)
            self.area_resultados.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
            self.area_resultados.grid_columnconfigure(0, weight=1)

            self.accion_listar()  # al abrir, muestra el listado inicial

        # ---- Helpers para dibujar en el área principal ----
        def limpiar_area(self):
            for widget in self.area_resultados.winfo_children():
                widget.destroy()

        def mostrar_texto(self, texto):
            """Para mensajes simples que no tienen imagen asociada
            (categorías, valor del inventario, avisos)."""
            self.limpiar_area()
            ctk.CTkLabel(
                self.area_resultados, text=texto, font=ctk.CTkFont(size=14),
                justify="left", anchor="w",
            ).pack(fill="x", padx=10, pady=10)

        def mostrar_articulos(self, articulos, con_id=True):
            """Dibuja una fila por artículo: imagen a la izquierda
            (o un cartel 'Sin imagen') y el texto al lado."""
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
                    etiqueta_imagen.image = foto  # evita que se pierda la referencia
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

        # ---- Menú del grupo "Artículos" ----
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
                ("Ver categorías", self.accion_categorias),
            ]

            def ejecutar(funcion):
                ventana.destroy()
                funcion()

            for texto, funcion in opciones:
                ctk.CTkButton(
                    ventana, text=texto, command=lambda f=funcion: ejecutar(f)
                ).pack(padx=15, pady=5, fill="x")

        # ---- Acciones directas (no necesitan formulario) ----
        def accion_listar(self):
            self.mostrar_articulos(listar_articulos(), con_id=True)

        def accion_categorias(self):
            categorias = obtener_categorias()
            texto = "\n".join(f"{c[0]} - {c[1]}" for c in categorias)
            self.mostrar_texto(texto)

        def accion_valor_inventario(self):
            datos = obtener_precios_y_stock()
            total = calcular_valor_inventario(datos)
            self.mostrar_texto(f"Valor total del inventario: $ {round(total, 2)}")

        # ---- Formulario: Registrar (ahora con imagen) ----
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

            # ---- Selección de imagen con vista previa ----
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
                vista_previa.image = foto  # evita que el recolector de basura la borre

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

        # ---- Formulario: Buscar (muestra detalle con imagen) ----
        def abrir_buscar(self):
            ventana = ctk.CTkToplevel(self)
            ventana.title("Buscar artículo")
            ventana.geometry("320x160")
            ventana.grab_set()

            entry_codigo = ctk.CTkEntry(ventana, placeholder_text="Código a buscar")
            entry_codigo.pack(pady=20)

            def confirmar():
                articulo = buscar_articulo(entry_codigo.get())
                ventana.destroy()
                if articulo:
                    self.mostrar_articulos([articulo], con_id=True)
                else:
                    self.mostrar_texto("El artículo no existe.")

            ctk.CTkButton(ventana, text="Buscar", command=confirmar).pack(pady=10)

        # ---- Formulario: Modificar ----
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

        # ---- Formulario: Eliminar ----
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

        # ---- Formulario: Ordenar ----
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

        # ---- Formulario: Filtrar ----
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

        # ==========================================================
        # NUEVOS MÓDULOS: Vendedores, Clientes y Ventas
        # ==========================================================
        def _abrir_menu(self, titulo, opciones, alto):
            """Abre una ventanita con un botón por opción, con el mismo
            estilo que el menú de Artículos."""
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
            """Dibuja una tarjeta por cada texto (para listados sin imagen)."""
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

        # ---- Vendedores ----
        def abrir_menu_vendedores(self):
            self._abrir_menu(
                "Vendedores",
                [
                    ("Registrar vendedor", self.abrir_registrar_vendedor),
                    ("Listar vendedores", self.accion_listar_vendedores),
                ],
                alto=200,
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
            # Legajo: cuadro de texto que arranca arriba a la izquierda y,
            # al llegar al borde derecho, baja al renglón siguiente.
            ctk.CTkLabel(ventana, text="Legajo").pack(pady=(10, 0))
            casilla_legajo = ctk.CTkTextbox(ventana, width=260, height=80, wrap="char")
            casilla_legajo.pack(pady=6)

            def leer_legajo():
                # Enter baja de renglón en pantalla, pero el legajo se
                # guarda como un solo dato: se descartan saltos de línea
                # y tabulaciones.
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

        # ---- Ventas y Clientes (unificado) ----
        def abrir_menu_ventas_clientes(self):
            self._abrir_menu(
                "Ventas y clientes",
                [
                    ("Nueva venta", self.abrir_nueva_venta_con_cliente),
                    ("Ver detalle de ventas", self.accion_ver_ventas),
                    ("Listar clientes", self.accion_listar_clientes),
                ],
                alto=240,
            )

        def accion_listar_clientes(self):
            textos = []
            for _id, dni, nombre, apellido, email, telefono in listar_clientes():
                contacto = "   |   ".join(x for x in (email, telefono) if x) or "Sin datos de contacto"
                textos.append(f"[{_id}] {apellido}, {nombre} - DNI {dni}\n{contacto}")
            self.mostrar_tarjetas(textos, "No hay clientes registrados.")

        def accion_ver_ventas(self):
            """Muestra cada venta con su encabezado y, debajo, los
            renglones del detalle (artículo, cantidad, precio, subtotal)."""
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
            """Pantalla única que reemplaza a los antiguos formularios
            separados de 'Registrar cliente' y 'Realizar venta'. De un
            lado se eligen los artículos a comprar (con buscador y
            carrito) y del otro se cargan los datos del cliente, para
            hacer todo el proceso de una sola vez. Si el DNI ingresado
            ya existe, se reutiliza ese cliente en lugar de duplicarlo."""
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

            # ================= Columna izquierda: artículos =================
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

            # ---- Carrito: id_articulo -> datos y cantidad elegida ----
            carrito = {}

            def redibujar_carrito():
                for widget in marco_carrito.winfo_children():
                    widget.destroy()
                total = 0.0
                if not carrito:
                    ctk.CTkLabel(
                        marco_carrito,
                        text="El carrito está vacío.\nHacé clic en un artículo para agregarlo.",
                        justify="left",
                    ).pack(pady=10)
                for id_a, d in carrito.items():
                    subtotal = d["precio"] * d["cantidad"]
                    total += subtotal
                    fila = ctk.CTkFrame(marco_carrito)
                    fila.pack(fill="x", pady=2)
                    ctk.CTkLabel(
                        fila,
                        text=f"{d['codigo']} - {d['nombre']}\n"
                             f"{d['cantidad']} x $ {d['precio']:.2f} = $ {subtotal:.2f}",
                        justify="left", anchor="w",
                    ).pack(side="left", padx=8, pady=4, fill="x", expand=True)
                    ctk.CTkButton(
                        fila, text="Quitar", width=60,
                        command=lambda i=id_a: quitar(i),
                    ).pack(side="right", padx=8)
                etiqueta_total.configure(text=f"Total: $ {total:.2f}")

            def quitar(id_articulo):
                carrito.pop(id_articulo, None)
                redibujar_carrito()

            def agregar_al_carrito(articulo):
                id_a, codigo, nombre, precio, stock, _imagen = articulo
                if stock <= 0:
                    messagebox.showerror("Sin stock", f"'{nombre}' no tiene stock disponible.")
                    return
                ya_en_carrito = carrito[id_a]["cantidad"] if id_a in carrito else 0
                if ya_en_carrito + 1 > stock:
                    messagebox.showerror(
                        "Stock insuficiente",
                        f"Stock disponible de '{nombre}': {stock}. "
                        f"Ya tenés {ya_en_carrito} en el carrito.",
                    )
                    return
                if id_a in carrito:
                    carrito[id_a]["cantidad"] += 1
                else:
                    carrito[id_a] = {
                        "codigo": codigo, "nombre": nombre,
                        "precio": float(precio), "cantidad": 1,
                    }
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

            # ================= Columna derecha: registro de cliente =================
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

            # ================= Confirmar =================
            def confirmar():
                if not carrito:
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
                    items = [(id_a, d["cantidad"]) for id_a, d in carrito.items()]
                    id_venta = registrar_venta(id_cliente, id_vendedor, items)
                except ValueError as e:
                    messagebox.showerror("Error de validación", str(e))
                    return
                except sqlite3.IntegrityError:
                    messagebox.showerror(
                        "Error", "No se pudo registrar la venta (datos inexistentes)."
                    )
                    return

                total = sum(d["precio"] * d["cantidad"] for d in carrito.values())
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


# ------------------------------------------------------------
# Casos de prueba (no requieren la interfaz gráfica)
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


class TestImagenes(unittest.TestCase):
    def test_guardar_y_recuperar_imagen(self):
        with tempfile.TemporaryDirectory() as carpeta_temporal:
            # Creamos un archivo "imagen" de prueba (no hace falta que
            # sea una imagen real para probar la copia de archivos).
            origen = os.path.join(carpeta_temporal, "prueba.png")
            with open(origen, "wb") as f:
                f.write(b"contenido de prueba")

            nombre_guardado = guardar_imagen(origen, "COM-TEST")
            self.assertEqual(nombre_guardado, "COM-TEST.png")

            ruta = ruta_completa_imagen(nombre_guardado)
            self.assertIsNotNone(ruta)
            self.assertTrue(os.path.exists(ruta))

            # Limpieza: borramos el archivo copiado a imagenes/
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


class TestVentas(unittest.TestCase):
    """Usan una base temporal (con las mismas tablas), así que no tocan
    tienda_comics.db."""

    def setUp(self):
        global NOMBRE_BASE
        self._base_original = NOMBRE_BASE
        self._carpeta = tempfile.TemporaryDirectory()
        NOMBRE_BASE = os.path.join(self._carpeta.name, "prueba.db")
        con = sqlite3.connect(NOMBRE_BASE)
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
        global NOMBRE_BASE
        NOMBRE_BASE = self._base_original
        self._carpeta.cleanup()

    def _stock(self, id_articulo):
        con = sqlite3.connect(NOMBRE_BASE)
        stock = con.execute("SELECT stock FROM articulos WHERE id = ?", (id_articulo,)).fetchone()[0]
        con.close()
        return stock

    def test_venta_calcula_total_detalle_y_descuenta_stock(self):
        id_venta = registrar_venta(1, 1, [(1, 2), (2, 1)])  # 2*1000 + 1*500
        ventas = listar_ventas()
        self.assertEqual(len(ventas), 1)
        self.assertEqual(ventas[0][0], id_venta)
        self.assertEqual(ventas[0][6], 2500)
        self.assertEqual(len(obtener_detalle_venta(id_venta)), 2)
        self.assertEqual(self._stock(1), 3)
        self.assertEqual(self._stock(2), 2)

    def test_stock_insuficiente_deshace_toda_la_venta(self):
        # El primer renglón alcanza, el segundo no: no debe quedar nada guardado.
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


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        sys.argv.pop(1)
        unittest.main(verbosity=2)
    else:
        iniciar_interfaz()
