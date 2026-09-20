"""
app.py
Sistema de administración de una tienda de cómics — versión con
interfaz gráfica (CustomTkinter) sobre base de datos SQLite, con
soporte para adjuntar una imagen a cada artículo.
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

            botones = [
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
            for texto, comando in botones:
                ctk.CTkButton(barra, text=texto, command=comando).pack(
                    padx=15, pady=6, fill="x"
                )

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
                encontrado = eliminar_articulo(codigo)
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


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        sys.argv.pop(1)
        unittest.main(verbosity=2)
    else:
        iniciar_interfaz()
