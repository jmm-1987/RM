#!/usr/bin/env python3
"""
Script para inicializar la base de datos en producción
Ejecutar manualmente si las tablas no se crean automáticamente
"""

import os
from app import app, db
from models import (
    Zona, Cliente, MensajePlantilla, MensajeEnviado, Oferta,
    MensajeOferta, MensajeRecibido, RespuestaMensaje,
    ProgramacionMasiva, WhatsAppConversation, WhatsAppMessage, Usuario
)

def init_database():
    """Inicializa la base de datos creando todas las tablas"""
    with app.app_context():
        try:
            print("🔌 Conectando a la base de datos...")
            print(f"   URL: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[-1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else 'SQLite local'}")
            
            # Crear todas las tablas
            print("📦 Creando tablas...")
            db.create_all()
            print("✅ Tablas creadas correctamente")
            
            # Verificar tablas creadas
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📊 Tablas creadas: {', '.join(tables)}")
            
            # Crear usuario admin si no existe
            usuario_admin = Usuario.query.filter_by(username='jmurillo').first()
            if not usuario_admin:
                usuario_admin = Usuario(username='jmurillo', activo=True)
                usuario_admin.set_password('TxMb-7-0')
                db.session.add(usuario_admin)
                db.session.commit()
                print("✅ Usuario administrador 'jmurillo' creado")
            else:
                print("✅ Usuario administrador 'jmurillo' ya existe")
            
            # Crear datos de ejemplo si no existen
            if not Zona.query.first():
                print("📝 Creando datos de ejemplo...")
                
                zonas_data = [
                    {'nombre': 'Centro', 'descripcion': 'Zona centro de la ciudad'},
                    {'nombre': 'Norte', 'descripcion': 'Zona norte de la ciudad'},
                    {'nombre': 'Sur', 'descripcion': 'Zona sur de la ciudad'},
                    {'nombre': 'Este', 'descripcion': 'Zona este de la ciudad'},
                    {'nombre': 'Oeste', 'descripcion': 'Zona oeste de la ciudad'}
                ]
                
                for zona_data in zonas_data:
                    zona = Zona(**zona_data)
                    db.session.add(zona)
                
                plantillas_data = [
                    {
                        'nombre': 'Visita Programada',
                        'contenido': 'Hola {nombre_cliente}, somos de Recambios RM. Vamos a pasar por la zona {zona} mañana por la mañana. ¿Necesitas algún recambio específico? Te podemos llevar lo que necesitas. ¡Gracias!'
                    },
                    {
                        'nombre': 'Recordatorio de Visita',
                        'contenido': 'Buenos días {nombre_cliente}, recordatorio: pasaremos por {zona} hoy por la tarde. Si necesitas algún recambio, avísanos antes de las 14:00. ¡Hasta pronto!'
                    },
                    {
                        'nombre': 'Promoción Especial',
                        'contenido': 'Hola {nombre_cliente}, tenemos una promoción especial esta semana. Pasaremos por {zona} con descuentos en recambios de motor. ¡No te lo pierdas!'
                    }
                ]
                
                for plantilla_data in plantillas_data:
                    plantilla = MensajePlantilla(**plantilla_data)
                    db.session.add(plantilla)
                
                ofertas_data = [
                    {
                        'titulo': 'Aceite de Motor Premium',
                        'descripcion': 'Aceite de motor de alta calidad para tu vehículo. Garantiza un rendimiento óptimo y protección del motor.',
                        'precio': 25.99,
                        'activa': True,
                        'destacada': True
                    },
                    {
                        'titulo': 'Filtro de Aire',
                        'descripcion': 'Filtro de aire original para mantener el motor limpio y eficiente.',
                        'precio': 12.50,
                        'activa': True,
                        'destacada': False
                    },
                    {
                        'titulo': 'Pastillas de Freno',
                        'descripcion': 'Pastillas de freno de alta calidad para una frenada segura y eficiente.',
                        'precio': 45.00,
                        'activa': True,
                        'destacada': True
                    }
                ]
                
                for oferta_data in ofertas_data:
                    oferta = Oferta(**oferta_data)
                    db.session.add(oferta)
                
                db.session.commit()
                print(f"✅ Datos de ejemplo creados:")
                print(f"   - {len(zonas_data)} zonas")
                print(f"   - {len(plantillas_data)} plantillas")
                print(f"   - {len(ofertas_data)} ofertas")
            else:
                print("✅ Datos de ejemplo ya existen")
            
            print("\n✅ Base de datos inicializada correctamente!")
            
        except Exception as e:
            print(f"❌ Error inicializando base de datos: {e}")
            import traceback
            print(traceback.format_exc())
            raise

if __name__ == '__main__':
    init_database()

