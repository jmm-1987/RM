#!/usr/bin/env python3
"""
Script para migrar la base de datos y agregar las nuevas tablas para mensajes recibidos
"""

import os
import sys
from flask import Flask
from models import db, MensajeRecibido, RespuestaMensaje

def crear_app():
    """Crear aplicación Flask para migración"""
    app = Flask(__name__)
    
    # Configuración para producción
    if os.environ.get('RENDER'):
        from config import DATABASE_URL, SECRET_KEY
        app.config['SECRET_KEY'] = SECRET_KEY
        app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    else:
        # Configuración para desarrollo local
        app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recambios.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def migrar_base_datos():
    """Migrar la base de datos agregando las nuevas tablas"""
    app = crear_app()
    
    with app.app_context():
        try:
            print("🔄 Iniciando migración de base de datos...")
            
            # Crear todas las tablas (incluyendo las nuevas)
            db.create_all()
            
            print("✅ Migración completada exitosamente!")
            print("📋 Nuevas tablas creadas:")
            print("   - mensaje_recibido: Para almacenar mensajes recibidos de WhatsApp")
            print("   - respuesta_mensaje: Para almacenar respuestas enviadas")
            
            # Verificar que las tablas existen
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tablas = inspector.get_table_names()
            
            print(f"\n📊 Total de tablas en la base de datos: {len(tablas)}")
            for tabla in sorted(tablas):
                print(f"   ✓ {tabla}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error durante la migración: {e}")
            return False

if __name__ == "__main__":
    print("🚀 Migrador de Base de Datos - Recambios RM")
    print("=" * 50)
    
    if migrar_base_datos():
        print("\n✅ ¡Migración completada!")
        print("\n📝 Próximos pasos:")
        print("1. Ejecuta: python configurar_webhook.py")
        print("2. Configura la URL del webhook en Green-API")
        print("3. Prueba enviando un mensaje de WhatsApp")
        print("4. Ve a /mensajes-recibidos en tu aplicación")
    else:
        print("\n❌ Error en la migración")
        sys.exit(1)
