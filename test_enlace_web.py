#!/usr/bin/env python3
"""
Script para probar la generación del enlace web
"""

import os
from flask import Flask, url_for

# Configurar Flask para pruebas
app = Flask(__name__)
app.config['TESTING'] = True

# Simular entorno de producción
os.environ['RENDER'] = 'true'
os.environ['RENDER_EXTERNAL_URL'] = 'https://rm-p1r1.onrender.com'

def generar_enlace_web():
    """Genera el enlace completo a la web pública de ofertas"""
    if os.environ.get('RENDER'):
        # En producción, usar la URL de Render
        dominio = os.environ.get('RENDER_EXTERNAL_URL', 'https://rm-p1r1.onrender.com')
    else:
        # En desarrollo local
        dominio = 'http://localhost:5000'
    
    return f"{dominio}/publico/ofertas"

def test_enlace_web():
    print("🔍 Probando generación de enlace web...")
    
    # Probar en producción
    os.environ['RENDER'] = 'true'
    enlace_produccion = generar_enlace_web()
    print(f"🌐 Enlace de producción: {enlace_produccion}")
    
    # Probar en desarrollo
    os.environ['RENDER'] = ''
    enlace_desarrollo = generar_enlace_web()
    print(f"💻 Enlace de desarrollo: {enlace_desarrollo}")
    
    # Verificar que el enlace de producción es correcto
    if enlace_produccion == 'https://rm-p1r1.onrender.com/publico/ofertas':
        print("✅ Enlace de producción generado correctamente")
    else:
        print("❌ Error en el enlace de producción")
    
    print("\n📝 Ejemplo de mensaje con enlace:")
    print("-" * 50)
    mensaje_ejemplo = f"""Hola Juan, somos de Recambios RM. 

Tenemos nuevas ofertas esta semana.

🌐 Consulta nuestras ofertas actuales: {enlace_produccion}

¡No te las pierdas!"""
    print(mensaje_ejemplo)
    print("-" * 50)

if __name__ == '__main__':
    test_enlace_web()




