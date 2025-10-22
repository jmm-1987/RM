#!/usr/bin/env python3
"""
Script de inicialización para Render - Crear todas las tablas necesarias
"""

from app import app
from models import db, Zona, Cliente, MensajePlantilla, MensajeEnviado, Oferta, MensajeOferta

def inicializar_base_datos():
    with app.app_context():
        try:
            # Crear todas las tablas
            db.create_all()
            print("✅ Todas las tablas creadas exitosamente")
            
            # Verificar que las tablas existen
            inspector = db.inspect(db.engine)
            tablas = inspector.get_table_names()
            print(f"📋 Tablas creadas: {tablas}")
            
            # Crear datos iniciales si no existen
            if not Zona.query.first():
                print("📝 Creando datos iniciales...")
                
                # Crear zonas básicas
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
                
                # Crear plantillas de mensajes
                plantillas_data = [
                    {
                        'nombre': 'Visita Programada',
                        'contenido': 'Hola {nombre_cliente}, somos de Recambios RM. Vamos a pasar por la zona {zona} mañana por la mañana. ¿Necesitas algún recambio específico? Te podemos llevar lo que necesites. ¡Gracias!'
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
                
                # Crear ofertas de ejemplo
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
                print("✅ Datos iniciales creados exitosamente!")
                print(f"- {len(zonas_data)} zonas creadas")
                print(f"- {len(plantillas_data)} plantillas de mensajes creadas")
                print(f"- {len(ofertas_data)} ofertas de ejemplo creadas")
            else:
                print("✅ Sistema ya inicializado")
                
        except Exception as e:
            print(f"❌ Error durante la inicialización: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    inicializar_base_datos()
