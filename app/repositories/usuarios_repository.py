"""Consultas SQL relacionadas con usuarios."""
from app.db import get_db_connection


def obtener_usuario_por_email(email: str):
    """Busca un usuario por su correo electrónico."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT id, nombre, email, password_hash, rol FROM usuarios WHERE email = %s"
        cursor.execute(query, (email,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

def crear_usuario(nombre: str, email: str, password_hash: str, rol: str = "cliente") -> int:
    """Inserta un nuevo usuario en la base de datos y retorna su id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO usuarios (nombre, email, password_hash, rol)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (nombre, email, password_hash, rol))
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()
