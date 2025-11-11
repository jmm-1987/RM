"""
Script para actualizar la base de datos y agregar el campo mensaje_final
"""

from app import app, db
from models import MensajeEnviado
from sqlalchemy import text

def actualizar_base_datos():
    """
    Actualizar la base de datos para agregar el campo mensaje_final
    """
    with app.app_context():
        try:
            # Verificar si el campo ya existe
            result = db.session.execute(text("PRAGMA table_info(mensaje_enviado)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'mensaje_final' not in columns:
                print("Agregando campo mensaje_final a la tabla mensaje_enviado...")
                
                # Agregar el campo mensaje_final
                db.session.execute(text("ALTER TABLE mensaje_enviado ADD COLUMN mensaje_final TEXT"))
                
                # Actualizar registros existentes con un mensaje por defecto
                db.session.execute(text("""
                    UPDATE mensaje_enviado 
                    SET mensaje_final = 'Mensaje enviado anteriormente' 
                    WHERE mensaje_final IS NULL
                """))
                
                db.session.commit()
                print("Campo mensaje_final agregado exitosamente")
            else:
                print("El campo mensaje_final ya existe")
                
            # Verificar la estructura de la tabla
            result = db.session.execute(text("PRAGMA table_info(mensaje_enviado)"))
            print("\nEstructura actual de la tabla mensaje_enviado:")
            for row in result.fetchall():
                print(f"  {row[1]} ({row[2]})")
                
        except Exception as e:
            print(f"Error actualizando la base de datos: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    actualizar_base_datos()

















