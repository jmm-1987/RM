#!/usr/bin/env python3
"""
Script de inicialización para producción en Render
Crea datos básicos y configura el sistema
"""

from app import app
from models import db, Zona, Cliente, MensajePlantilla

def inicializar_produccion():
    with app.app_context():
        # Crear tablas si no existen
        db.create_all()
        
        # Verificar si ya hay datos
        if Zona.query.first() is None:
            print("Creando datos iniciales...")
            
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
            
            db.session.commit()
            print("✅ Datos iniciales creados exitosamente!")
            print(f"- {len(zonas_data)} zonas creadas")
            print(f"- {len(plantillas_data)} plantillas de mensajes creadas")
        else:
            print("✅ Sistema ya inicializado")

if __name__ == '__main__':
    inicializar_produccion()
