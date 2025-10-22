#!/usr/bin/env python3
"""
Script para migrar datos de SQLite local a PostgreSQL para Render
"""

import os
import sqlite3
import psycopg2
from urllib.parse import urlparse

def migrar_datos_sqlite_a_postgres():
    """Migra todos los datos de SQLite local a PostgreSQL"""
    
    # Conectar a SQLite local
    sqlite_conn = sqlite3.connect('recambios.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    # Obtener URL de PostgreSQL desde variable de entorno
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ Error: DATABASE_URL no está configurada")
        return False
    
    # Conectar a PostgreSQL
    try:
        postgres_conn = psycopg2.connect(database_url)
        postgres_cursor = postgres_conn.cursor()
        print("✅ Conectado a PostgreSQL")
    except Exception as e:
        print(f"❌ Error conectando a PostgreSQL: {e}")
        return False
    
    try:
        # Migrar zonas
        print("📝 Migrando zonas...")
        sqlite_cursor.execute("SELECT id, nombre, descripcion FROM zona")
        zonas = sqlite_cursor.fetchall()
        
        for zona in zonas:
            postgres_cursor.execute(
                "INSERT INTO zona (id, nombre, descripcion) VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING",
                zona
            )
        
        # Migrar clientes
        print("📝 Migrando clientes...")
        sqlite_cursor.execute("SELECT id, nombre, telefono, zona_id, activo FROM cliente")
        clientes = sqlite_cursor.fetchall()
        
        for cliente in clientes:
            postgres_cursor.execute(
                "INSERT INTO cliente (id, nombre, telefono, zona_id, activo) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                cliente
            )
        
        # Migrar plantillas de mensajes
        print("📝 Migrando plantillas de mensajes...")
        sqlite_cursor.execute("SELECT id, nombre, contenido FROM mensaje_plantilla")
        plantillas = sqlite_cursor.fetchall()
        
        for plantilla in plantillas:
            postgres_cursor.execute(
                "INSERT INTO mensaje_plantilla (id, nombre, contenido) VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING",
                plantilla
            )
        
        # Migrar ofertas
        print("📝 Migrando ofertas...")
        sqlite_cursor.execute("SELECT id, titulo, descripcion, precio, imagen, activa, destacada, created_at, updated_at FROM oferta")
        ofertas = sqlite_cursor.fetchall()
        
        for oferta in ofertas:
            postgres_cursor.execute(
                "INSERT INTO oferta (id, titulo, descripcion, precio, imagen, activa, destacada, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                oferta
            )
        
        # Migrar mensajes enviados
        print("📝 Migrando mensajes enviados...")
        sqlite_cursor.execute("SELECT id, cliente_id, plantilla_id, mensaje_personalizado, mensaje_enviado, fecha_envio, error FROM mensaje_enviado")
        mensajes = sqlite_cursor.fetchall()
        
        for mensaje in mensajes:
            postgres_cursor.execute(
                "INSERT INTO mensaje_enviado (id, cliente_id, plantilla_id, mensaje_personalizado, mensaje_enviado, fecha_envio, error) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                mensaje
            )
        
        # Migrar mensajes de ofertas
        print("📝 Migrando mensajes de ofertas...")
        sqlite_cursor.execute("SELECT id, cliente_id, oferta_id, mensaje_personalizado, imagen_enviada, mensaje_enviado, fecha_envio, error FROM mensaje_oferta")
        mensajes_ofertas = sqlite_cursor.fetchall()
        
        for mensaje_oferta in mensajes_ofertas:
            postgres_cursor.execute(
                "INSERT INTO mensaje_oferta (id, cliente_id, oferta_id, mensaje_personalizado, imagen_enviada, mensaje_enviado, fecha_envio, error) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                mensaje_oferta
            )
        
        # Confirmar cambios
        postgres_conn.commit()
        print("✅ Migración completada exitosamente!")
        
        # Mostrar estadísticas
        print(f"\n📊 Estadísticas de migración:")
        print(f"- Zonas migradas: {len(zonas)}")
        print(f"- Clientes migrados: {len(clientes)}")
        print(f"- Plantillas migradas: {len(plantillas)}")
        print(f"- Ofertas migradas: {len(ofertas)}")
        print(f"- Mensajes migrados: {len(mensajes)}")
        print(f"- Mensajes de ofertas migrados: {len(mensajes_ofertas)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        postgres_conn.rollback()
        return False
    
    finally:
        sqlite_conn.close()
        postgres_conn.close()

if __name__ == '__main__':
    print("🚀 Iniciando migración de SQLite a PostgreSQL...")
    if migrar_datos_sqlite_a_postgres():
        print("🎉 Migración completada exitosamente!")
    else:
        print("💥 Error en la migración")
