from app import app, db
from models import Oferta

def crear_ofertas_ejemplo():
    with app.app_context():
        # Crear ofertas de ejemplo
        ofertas_data = [
            {
                'titulo': 'Filtro de Aceite Premium',
                'descripcion': 'Filtro de aceite de alta calidad para motores diésel y gasolina. Compatible con múltiples marcas y modelos. Garantía de 2 años.',
                'precio': 12.50,
                'imagen': None,
                'destacada': True,
                'activa': True
            },
            {
                'titulo': 'Pastillas de Freno Delanteras',
                'descripcion': 'Juego de pastillas de freno delanteras con excelente poder de frenado y durabilidad. Reducen el ruido y el desgaste de discos.',
                'precio': 45.90,
                'imagen': None,
                'destacada': True,
                'activa': True
            },
            {
                'titulo': 'Aceite Motor 5W-30',
                'descripcion': 'Aceite sintético de alta calidad 5W-30. Ideal para motores modernos. Protección superior contra el desgaste.',
                'precio': 28.75,
                'imagen': None,
                'destacada': True,
                'activa': True
            },
            {
                'titulo': 'Bujías de Encendido',
                'descripcion': 'Bujías de encendido de platino para mejor combustión y menor consumo de combustible. Fácil instalación.',
                'precio': 8.95,
                'imagen': None,
                'destacada': False,
                'activa': True
            },
            {
                'titulo': 'Correa de Distribución',
                'descripcion': 'Correa de distribución de caucho sintético reforzado. Incluye kit completo con tensor y bomba de agua.',
                'precio': 89.50,
                'imagen': None,
                'destacada': False,
                'activa': True
            },
            {
                'titulo': 'Amortiguadores Traseros',
                'descripcion': 'Par de amortiguadores traseros con tecnología de gas. Mejoran la estabilidad y confort de conducción.',
                'precio': 125.00,
                'imagen': None,
                'destacada': False,
                'activa': True
            },
            {
                'titulo': 'Batería 12V 60Ah',
                'descripcion': 'Batería de 12V con 60Ah de capacidad. Tecnología libre de mantenimiento. Garantía de 3 años.',
                'precio': 75.25,
                'imagen': None,
                'destacada': False,
                'activa': True
            },
            {
                'titulo': 'Filtro de Aire',
                'descripcion': 'Filtro de aire de papel de alta eficiencia. Protege el motor de impurezas y mejora el rendimiento.',
                'precio': 15.80,
                'imagen': None,
                'destacada': False,
                'activa': True
            },
            {
                'titulo': 'Discos de Freno Delanteros',
                'descripcion': 'Par de discos de freno delanteros ventilados. Tratamiento anticorrosión y excelente disipación del calor.',
                'precio': 95.40,
                'imagen': None,
                'destacada': False,
                'activa': True
            },
            {
                'titulo': 'Líquido de Frenos DOT 4',
                'descripcion': 'Líquido de frenos DOT 4 de alta temperatura. Compatible con sistemas ABS y ESP. Envase de 1 litro.',
                'precio': 6.50,
                'imagen': None,
                'destacada': False,
                'activa': True
            }
        ]
        
        for oferta_data in ofertas_data:
            oferta = Oferta(**oferta_data)
            db.session.add(oferta)
        
        db.session.commit()
        print("Ofertas de ejemplo creadas exitosamente!")
        print(f"- {len(ofertas_data)} ofertas creadas")
        
        destacadas = sum(1 for o in ofertas_data if o['destacada'])
        normales = len(ofertas_data) - destacadas
        print(f"- {destacadas} ofertas destacadas")
        print(f"- {normales} ofertas normales")

if __name__ == '__main__':
    crear_ofertas_ejemplo()

