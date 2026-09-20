"""
crear_base.py
Genera tienda_comics.db (SQLite) con el mismo esquema y las mismas
categorías precargadas que la base MySQL/MariaDB original. Se
ejecuta una sola vez para crear el archivo.
"""
import sqlite3

conexion = sqlite3.connect("tienda_comics.db")
conexion.execute("PRAGMA foreign_keys = ON")
cursor = conexion.cursor()

cursor.executescript("""
DROP TABLE IF EXISTS detalle_ventas;
DROP TABLE IF EXISTS ventas;
DROP TABLE IF EXISTS vendedores;
DROP TABLE IF EXISTS clientes;
DROP TABLE IF EXISTS articulos;
DROP TABLE IF EXISTS categorias;

CREATE TABLE categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(50),
    descripcion VARCHAR(150)
);

CREATE TABLE articulos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_C INTEGER NOT NULL,
    codigo VARCHAR(50) UNIQUE,
    nombre_titulo VARCHAR(100),
    precio DECIMAL(10,2),
    stock INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (Id_C) REFERENCES categorias(id)
);

CREATE TABLE clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dni VARCHAR(20) UNIQUE,
    nombre VARCHAR(50),
    apellido VARCHAR(50),
    email VARCHAR(100),
    telefono VARCHAR(20)
);

CREATE TABLE vendedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    legajo VARCHAR(20) UNIQUE,
    nombre VARCHAR(50),
    apellido VARCHAR(50),
    turno VARCHAR(10) CHECK (turno IN ('mañana','tarde','noche'))
);

CREATE TABLE ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_CL INTEGER NOT NULL,
    Id_V INTEGER NOT NULL,
    fecha_hora DATETIME,
    monto_total DECIMAL(10,2),
    FOREIGN KEY (Id_CL) REFERENCES clientes(id),
    FOREIGN KEY (Id_V) REFERENCES vendedores(id)
);

CREATE TABLE detalle_ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_VE INTEGER NOT NULL,
    Id_A INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (Id_VE) REFERENCES ventas(id),
    FOREIGN KEY (Id_A) REFERENCES articulos(id)
);
""")

cursor.executemany(
    "INSERT INTO categorias (id, nombre, descripcion) VALUES (?, ?, ?)",
    [
        (1, "Cómics", "Historietas en formato grapa o tomo recopilatorio"),
        (2, "Manga", "historietas o cómics de origen japonés"),
        (3, "Figuras", "réplica tridimensional de un personaje ficticio"),
        (4, "juego de mesa", "actividades recreativas que se juegan sobre una superficie plana"),
    ],
)

conexion.commit()
conexion.close()
print("Base tienda_comics.db creada correctamente.")
