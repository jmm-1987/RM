from app import app, db
from models import Zona, Cliente, MensajePlantilla, MensajeEnviado
import random

def resetear_y_crear_datos_con_incluir():
    with app.app_context():
        # Eliminar todas las tablas existentes
        db.drop_all()
        print("Tablas eliminadas")
        
        # Crear todas las tablas desde cero
        db.create_all()
        print("Tablas creadas")
        
        # Crear zonas
        zonas_data = [
            {
                'nombre': 'Zona1',
                'descripcion': 'Zona centro de la ciudad, talleres principales y comerciales'
            },
            {
                'nombre': 'Zona2',
                'descripcion': 'Zona norte, talleres industriales y de vehículos pesados'
            },
            {
                'nombre': 'Zona3',
                'descripcion': 'Zona sur, talleres de barrio y familiares'
            },
            {
                'nombre': 'Zona4',
                'descripcion': 'Zona este, talleres especializados y de alta gama'
            },
            {
                'nombre': 'Zona5',
                'descripcion': 'Zona oeste, talleres de vehículos comerciales'
            },
            {
                'nombre': 'Zona6',
                'descripcion': 'Polígono industrial, talleres de maquinaria pesada'
            },
            {
                'nombre': 'Zona7',
                'descripcion': 'Zona residencial, talleres de vehículos particulares'
            },
            {
                'nombre': 'Zona8',
                'descripcion': 'Carretera nacional, talleres de carretera y emergencias'
            }
        ]
        
        zonas = []
        for zona_data in zonas_data:
            zona = Zona(**zona_data)
            db.session.add(zona)
            zonas.append(zona)
        
        db.session.commit()
        print(f"{len(zonas)} zonas creadas")
        
        # Crear clientes base (sin incluir)
        clientes_base = [
            # Zona1 (12 clientes)
            {'nombre': 'Taller García', 'telefono': '600123456', 'email': 'garcia@taller.com', 'direccion': 'Calle Mayor 123', 'poblacion': 'Madrid', 'zona_id': 1},
            {'nombre': 'AutoReparaciones López', 'telefono': '600234567', 'email': 'lopez@auto.com', 'direccion': 'Plaza España 45', 'poblacion': 'Madrid', 'zona_id': 1},
            {'nombre': 'Taller Central', 'telefono': '600345678', 'email': 'central@taller.com', 'direccion': 'Gran Vía 78', 'poblacion': 'Madrid', 'zona_id': 1},
            {'nombre': 'Repuestos del Centro', 'telefono': '600456789', 'email': 'repuestos@centro.com', 'direccion': 'Calle Nueva 12', 'poblacion': 'Madrid', 'zona_id': 1},
            {'nombre': 'Taller Premium', 'telefono': '600567890', 'email': 'premium@taller.com', 'direccion': 'Calle Alcalá 234', 'poblacion': 'Madrid', 'zona_id': 1},
            {'nombre': 'AutoServicio Centro', 'telefono': '600678901', 'email': 'centro@autoservicio.com', 'direccion': 'Plaza Mayor 56', 'poblacion': 'Madrid', 'zona_id': 1},
            {'nombre': 'Taller Express', 'telefono': '600789012', 'email': 'express@taller.com', 'direccion': 'Calle Preciados 89', 'poblacion': 'Madrid', 'zona_id': 1},
            {'nombre': 'Repuestos García', 'telefono': '600890123', 'email': 'garcia@repuestos.com', 'direccion': 'Calle Montera 12', 'poblacion': 'Madrid', 'zona_id': 1},
            {'nombre': 'Taller Veloz', 'telefono': '600901234', 'email': 'veloz@taller.com', 'direccion': 'Calle Fuencarral 45', 'poblacion': 'Madrid', 'zona_id': 1},
            {'nombre': 'AutoTaller Madrid', 'telefono': '600012345', 'email': 'madrid@auto.com', 'direccion': 'Calle Hortaleza 67', 'poblacion': 'Madrid', 'zona_id': 1},
            {'nombre': 'Taller del Sol', 'telefono': '600123450', 'email': 'sol@taller.com', 'direccion': 'Calle Sol 23', 'poblacion': 'Madrid', 'zona_id': 1},
            {'nombre': 'Repuestos Central', 'telefono': '600234561', 'email': 'central@repuestos.com', 'direccion': 'Calle Arenal 34', 'poblacion': 'Madrid', 'zona_id': 1},
            
            # Zona2 (13 clientes)
            {'nombre': 'Taller Industrial Norte', 'telefono': '600345672', 'email': 'norte@industrial.com', 'direccion': 'Polígono Norte 1', 'poblacion': 'Alcobendas', 'zona_id': 2},
            {'nombre': 'AutoTaller Martínez', 'telefono': '600456783', 'email': 'martinez@auto.com', 'direccion': 'Avenida Norte 234', 'poblacion': 'San Sebastián de los Reyes', 'zona_id': 2},
            {'nombre': 'Taller de Camiones', 'telefono': '600567894', 'email': 'camiones@taller.com', 'direccion': 'Carretera Norte Km5', 'poblacion': 'Alcobendas', 'zona_id': 2},
            {'nombre': 'Taller Pesados Norte', 'telefono': '600678905', 'email': 'pesados@norte.com', 'direccion': 'Polígono Industrial Norte', 'poblacion': 'Alcobendas', 'zona_id': 2},
            {'nombre': 'AutoReparaciones Norte', 'telefono': '600789016', 'email': 'norte@auto.com', 'direccion': 'Calle Industrial 12', 'poblacion': 'San Sebastián de los Reyes', 'zona_id': 2},
            {'nombre': 'Taller Maquinaria', 'telefono': '600890127', 'email': 'maquinaria@taller.com', 'direccion': 'Avenida Industrial 45', 'poblacion': 'Alcobendas', 'zona_id': 2},
            {'nombre': 'Repuestos Norte', 'telefono': '600901238', 'email': 'norte@repuestos.com', 'direccion': 'Polígono Norte Sector 2', 'poblacion': 'Alcobendas', 'zona_id': 2},
            {'nombre': 'Taller Furgonetas Norte', 'telefono': '600012349', 'email': 'furgonetas@norte.com', 'direccion': 'Calle Logística 78', 'poblacion': 'San Sebastián de los Reyes', 'zona_id': 2},
            {'nombre': 'AutoTaller Industrial', 'telefono': '600123450', 'email': 'industrial@auto.com', 'direccion': 'Avenida Norte Km3', 'poblacion': 'Alcobendas', 'zona_id': 2},
            {'nombre': 'Taller Comercial', 'telefono': '600234561', 'email': 'comercial@taller.com', 'direccion': 'Polígono Norte 3', 'poblacion': 'Alcobendas', 'zona_id': 2},
            {'nombre': 'Repuestos Industriales', 'telefono': '600345672', 'email': 'industriales@repuestos.com', 'direccion': 'Calle Maquinaria 90', 'poblacion': 'San Sebastián de los Reyes', 'zona_id': 2},
            {'nombre': 'Taller Logística', 'telefono': '600456783', 'email': 'logistica@taller.com', 'direccion': 'Avenida Norte Sector 4', 'poblacion': 'Alcobendas', 'zona_id': 2},
            {'nombre': 'AutoServicio Norte', 'telefono': '600567894', 'email': 'norte@autoservicio.com', 'direccion': 'Polígono Norte 5', 'poblacion': 'San Sebastián de los Reyes', 'zona_id': 2},
            
            # Zona3 (12 clientes)
            {'nombre': 'Taller del Barrio', 'telefono': '600678905', 'email': 'barrio@taller.com', 'direccion': 'Calle Sur 56', 'poblacion': 'Getafe', 'zona_id': 3},
            {'nombre': 'AutoServicio Sur', 'telefono': '600789016', 'email': 'sur@autoservicio.com', 'direccion': 'Plaza Sur 89', 'poblacion': 'Leganés', 'zona_id': 3},
            {'nombre': 'Taller Familiar', 'telefono': '600890127', 'email': 'familiar@taller.com', 'direccion': 'Barrio Sur 23', 'poblacion': 'Getafe', 'zona_id': 3},
            {'nombre': 'Taller Vecinal', 'telefono': '600901238', 'email': 'vecinal@taller.com', 'direccion': 'Calle Vecinos 45', 'poblacion': 'Leganés', 'zona_id': 3},
            {'nombre': 'AutoTaller Sur', 'telefono': '600012349', 'email': 'sur@auto.com', 'direccion': 'Avenida Sur 67', 'poblacion': 'Getafe', 'zona_id': 3},
            {'nombre': 'Repuestos del Sur', 'telefono': '600123450', 'email': 'sur@repuestos.com', 'direccion': 'Calle Sur Km2', 'poblacion': 'Leganés', 'zona_id': 3},
            {'nombre': 'Taller Popular', 'telefono': '600234561', 'email': 'popular@taller.com', 'direccion': 'Barrio Popular 12', 'poblacion': 'Getafe', 'zona_id': 3},
            {'nombre': 'AutoReparaciones Sur', 'telefono': '600345672', 'email': 'sur@autoreparaciones.com', 'direccion': 'Calle Sur Sector 3', 'poblacion': 'Leganés', 'zona_id': 3},
            {'nombre': 'Taller Económico', 'telefono': '600456783', 'email': 'economico@taller.com', 'direccion': 'Avenida Sur 34', 'poblacion': 'Getafe', 'zona_id': 3},
            {'nombre': 'Repuestos Baratos', 'telefono': '600567894', 'email': 'baratos@repuestos.com', 'direccion': 'Calle Sur 56', 'poblacion': 'Leganés', 'zona_id': 3},
            {'nombre': 'Taller Rápido Sur', 'telefono': '600678905', 'email': 'rapido@sur.com', 'direccion': 'Barrio Sur 78', 'poblacion': 'Getafe', 'zona_id': 3},
            {'nombre': 'AutoServicio Vecinal', 'telefono': '600789016', 'email': 'vecinal@autoservicio.com', 'direccion': 'Calle Vecinos 90', 'poblacion': 'Leganés', 'zona_id': 3},
            
            # Zona4 (13 clientes)
            {'nombre': 'Taller Especializado', 'telefono': '600890127', 'email': 'especializado@taller.com', 'direccion': 'Zona Este 67', 'poblacion': 'Alcalá de Henares', 'zona_id': 4},
            {'nombre': 'AutoReparaciones Este', 'telefono': '600901238', 'email': 'este@auto.com', 'direccion': 'Avenida Este 90', 'poblacion': 'Torrejón de Ardoz', 'zona_id': 4},
            {'nombre': 'Taller Premium Este', 'telefono': '600012349', 'email': 'premium@este.com', 'direccion': 'Calle Este Premium 12', 'poblacion': 'Alcalá de Henares', 'zona_id': 4},
            {'nombre': 'AutoTaller Especializado', 'telefono': '600123450', 'email': 'especializado@auto.com', 'direccion': 'Avenida Este Km4', 'poblacion': 'Torrejón de Ardoz', 'zona_id': 4},
            {'nombre': 'Repuestos Premium', 'telefono': '600234561', 'email': 'premium@repuestos.com', 'direccion': 'Zona Este Sector 2', 'poblacion': 'Alcalá de Henares', 'zona_id': 4},
            {'nombre': 'Taller Alta Gama', 'telefono': '600345672', 'email': 'altagama@taller.com', 'direccion': 'Calle Este 34', 'poblacion': 'Torrejón de Ardoz', 'zona_id': 4},
            {'nombre': 'AutoServicio Este', 'telefono': '600456783', 'email': 'este@autoservicio.com', 'direccion': 'Avenida Este 56', 'poblacion': 'Alcalá de Henares', 'zona_id': 4},
            {'nombre': 'Taller Exclusivo', 'telefono': '600567894', 'email': 'exclusivo@taller.com', 'direccion': 'Zona Este Exclusiva', 'poblacion': 'Torrejón de Ardoz', 'zona_id': 4},
            {'nombre': 'Repuestos Especializados', 'telefono': '600678905', 'email': 'especializados@repuestos.com', 'direccion': 'Calle Este 78', 'poblacion': 'Alcalá de Henares', 'zona_id': 4},
            {'nombre': 'Taller Deportivo', 'telefono': '600789016', 'email': 'deportivo@taller.com', 'direccion': 'Avenida Este Deportiva', 'poblacion': 'Torrejón de Ardoz', 'zona_id': 4},
            {'nombre': 'AutoTaller Premium', 'telefono': '600890127', 'email': 'premium@auto.com', 'direccion': 'Zona Este Premium', 'poblacion': 'Alcalá de Henares', 'zona_id': 4},
            {'nombre': 'Taller Clásico', 'telefono': '600901238', 'email': 'clasico@taller.com', 'direccion': 'Calle Este 90', 'poblacion': 'Torrejón de Ardoz', 'zona_id': 4},
            {'nombre': 'Repuestos Deportivos', 'telefono': '600012349', 'email': 'deportivos@repuestos.com', 'direccion': 'Avenida Este Km6', 'poblacion': 'Alcalá de Henares', 'zona_id': 4},
            
            # Zona5 (12 clientes)
            {'nombre': 'Taller Pesados', 'telefono': '600123450', 'email': 'pesados@taller.com', 'direccion': 'Carretera Oeste Km3', 'poblacion': 'Móstoles', 'zona_id': 5},
            {'nombre': 'AutoTaller Oeste', 'telefono': '600234561', 'email': 'oeste@auto.com', 'direccion': 'Polígono Oeste 2', 'poblacion': 'Alcorcón', 'zona_id': 5},
            {'nombre': 'Taller de Furgonetas', 'telefono': '600345672', 'email': 'furgonetas@taller.com', 'direccion': 'Zona Oeste 45', 'poblacion': 'Móstoles', 'zona_id': 5},
            {'nombre': 'Taller Comercial Oeste', 'telefono': '600456783', 'email': 'comercial@oeste.com', 'direccion': 'Avenida Oeste 67', 'poblacion': 'Alcorcón', 'zona_id': 5},
            {'nombre': 'Repuestos Oeste', 'telefono': '600567894', 'email': 'oeste@repuestos.com', 'direccion': 'Polígono Oeste 3', 'poblacion': 'Móstoles', 'zona_id': 5},
            {'nombre': 'AutoServicio Oeste', 'telefono': '600678905', 'email': 'oeste@autoservicio.com', 'direccion': 'Calle Oeste 89', 'poblacion': 'Alcorcón', 'zona_id': 5},
            {'nombre': 'Taller Logística Oeste', 'telefono': '600789016', 'email': 'logistica@oeste.com', 'direccion': 'Zona Oeste Logística', 'poblacion': 'Móstoles', 'zona_id': 5},
            {'nombre': 'Taller Transporte', 'telefono': '600890127', 'email': 'transporte@taller.com', 'direccion': 'Carretera Oeste Km5', 'poblacion': 'Alcorcón', 'zona_id': 5},
            {'nombre': 'Repuestos Comerciales', 'telefono': '600901238', 'email': 'comerciales@repuestos.com', 'direccion': 'Polígono Oeste 4', 'poblacion': 'Móstoles', 'zona_id': 5},
            {'nombre': 'AutoTaller Transporte', 'telefono': '600012349', 'email': 'transporte@auto.com', 'direccion': 'Avenida Oeste 12', 'poblacion': 'Alcorcón', 'zona_id': 5},
            {'nombre': 'Taller Distribución', 'telefono': '600123450', 'email': 'distribucion@taller.com', 'direccion': 'Zona Oeste Distribución', 'poblacion': 'Móstoles', 'zona_id': 5},
            {'nombre': 'Repuestos Transporte', 'telefono': '600234561', 'email': 'transporte@repuestos.com', 'direccion': 'Polígono Oeste 5', 'poblacion': 'Alcorcón', 'zona_id': 5},
            
            # Zona6 (12 clientes)
            {'nombre': 'Taller Maquinaria Pesada', 'telefono': '600345672', 'email': 'maquinaria@pesada.com', 'direccion': 'Polígono Industrial Sector 1', 'poblacion': 'Fuenlabrada', 'zona_id': 6},
            {'nombre': 'AutoTaller Industrial', 'telefono': '600456783', 'email': 'industrial@auto.com', 'direccion': 'Calle Industrial 23', 'poblacion': 'Parla', 'zona_id': 6},
            {'nombre': 'Repuestos Industriales', 'telefono': '600567894', 'email': 'industriales@repuestos.com', 'direccion': 'Polígono Industrial 2', 'poblacion': 'Fuenlabrada', 'zona_id': 6},
            {'nombre': 'Taller Construcción', 'telefono': '600678905', 'email': 'construccion@taller.com', 'direccion': 'Avenida Industrial 45', 'poblacion': 'Parla', 'zona_id': 6},
            {'nombre': 'AutoServicio Industrial', 'telefono': '600789016', 'email': 'industrial@autoservicio.com', 'direccion': 'Polígono Industrial 3', 'poblacion': 'Fuenlabrada', 'zona_id': 6},
            {'nombre': 'Taller Agrícola', 'telefono': '600890127', 'email': 'agricola@taller.com', 'direccion': 'Calle Industrial 67', 'poblacion': 'Parla', 'zona_id': 6},
            {'nombre': 'Repuestos Construcción', 'telefono': '600901238', 'email': 'construccion@repuestos.com', 'direccion': 'Polígono Industrial 4', 'poblacion': 'Fuenlabrada', 'zona_id': 6},
            {'nombre': 'Taller Minero', 'telefono': '600012349', 'email': 'minero@taller.com', 'direccion': 'Avenida Industrial Km2', 'poblacion': 'Parla', 'zona_id': 6},
            {'nombre': 'AutoTaller Construcción', 'telefono': '600123450', 'email': 'construccion@auto.com', 'direccion': 'Polígono Industrial 5', 'poblacion': 'Fuenlabrada', 'zona_id': 6},
            {'nombre': 'Taller Forestal', 'telefono': '600234561', 'email': 'forestal@taller.com', 'direccion': 'Calle Industrial 89', 'poblacion': 'Parla', 'zona_id': 6},
            {'nombre': 'Repuestos Agrícolas', 'telefono': '600345672', 'email': 'agricolas@repuestos.com', 'direccion': 'Polígono Industrial 6', 'poblacion': 'Fuenlabrada', 'zona_id': 6},
            {'nombre': 'Taller Minero Industrial', 'telefono': '600456783', 'email': 'minero@industrial.com', 'direccion': 'Avenida Industrial Km4', 'poblacion': 'Parla', 'zona_id': 6},
            
            # Zona7 (13 clientes)
            {'nombre': 'Taller Residencial Norte', 'telefono': '600567894', 'email': 'residencial@norte.com', 'direccion': 'Calle Residencial 12', 'poblacion': 'Las Rozas', 'zona_id': 7},
            {'nombre': 'AutoServicio Familiar', 'telefono': '600678905', 'email': 'familiar@autoservicio.com', 'direccion': 'Avenida Residencial 34', 'poblacion': 'Majadahonda', 'zona_id': 7},
            {'nombre': 'Taller Vecinos', 'telefono': '600789016', 'email': 'vecinos@taller.com', 'direccion': 'Barrio Residencial 56', 'poblacion': 'Las Rozas', 'zona_id': 7},
            {'nombre': 'Repuestos Residenciales', 'telefono': '600890127', 'email': 'residenciales@repuestos.com', 'direccion': 'Calle Residencial 78', 'poblacion': 'Majadahonda', 'zona_id': 7},
            {'nombre': 'AutoTaller Familiar', 'telefono': '600901238', 'email': 'familiar@auto.com', 'direccion': 'Avenida Residencial Km1', 'poblacion': 'Las Rozas', 'zona_id': 7},
            {'nombre': 'Taller Barrio Norte', 'telefono': '600012349', 'email': 'barrio@norte.com', 'direccion': 'Barrio Norte 90', 'poblacion': 'Majadahonda', 'zona_id': 7},
            {'nombre': 'Repuestos Familiares', 'telefono': '600123450', 'email': 'familiares@repuestos.com', 'direccion': 'Calle Residencial 12', 'poblacion': 'Las Rozas', 'zona_id': 7},
            {'nombre': 'Taller Hogar', 'telefono': '600234561', 'email': 'hogar@taller.com', 'direccion': 'Avenida Hogar 23', 'poblacion': 'Majadahonda', 'zona_id': 7},
            {'nombre': 'AutoServicio Vecinos', 'telefono': '600345672', 'email': 'vecinos@autoservicio.com', 'direccion': 'Barrio Vecinos 45', 'poblacion': 'Las Rozas', 'zona_id': 7},
            {'nombre': 'Taller Residencial Sur', 'telefono': '600456783', 'email': 'residencial@sur.com', 'direccion': 'Calle Residencial Sur 67', 'poblacion': 'Majadahonda', 'zona_id': 7},
            {'nombre': 'Repuestos Hogar', 'telefono': '600567894', 'email': 'hogar@repuestos.com', 'direccion': 'Avenida Hogar Km2', 'poblacion': 'Las Rozas', 'zona_id': 7},
            {'nombre': 'AutoTaller Residencial', 'telefono': '600678905', 'email': 'residencial@auto.com', 'direccion': 'Barrio Residencial 89', 'poblacion': 'Majadahonda', 'zona_id': 7},
            {'nombre': 'Taller Familiar Norte', 'telefono': '600789016', 'email': 'familiar@norte.com', 'direccion': 'Calle Familiar 12', 'poblacion': 'Las Rozas', 'zona_id': 7},
            
            # Zona8 (13 clientes)
            {'nombre': 'Taller Carretera Norte', 'telefono': '600890127', 'email': 'carretera@norte.com', 'direccion': 'Carretera Nacional Km15', 'poblacion': 'Colmenar Viejo', 'zona_id': 8},
            {'nombre': 'AutoServicio Carretera', 'telefono': '600901238', 'email': 'carretera@autoservicio.com', 'direccion': 'Carretera Nacional Km20', 'poblacion': 'Tres Cantos', 'zona_id': 8},
            {'nombre': 'Taller Emergencias', 'telefono': '600012349', 'email': 'emergencias@taller.com', 'direccion': 'Carretera Nacional Km25', 'poblacion': 'Colmenar Viejo', 'zona_id': 8},
            {'nombre': 'Repuestos Carretera', 'telefono': '600123450', 'email': 'carretera@repuestos.com', 'direccion': 'Carretera Nacional Km30', 'poblacion': 'Tres Cantos', 'zona_id': 8},
            {'nombre': 'AutoTaller Carretera', 'telefono': '600234561', 'email': 'carretera@auto.com', 'direccion': 'Carretera Nacional Km35', 'poblacion': 'Colmenar Viejo', 'zona_id': 8},
            {'nombre': 'Taller 24 Horas', 'telefono': '600345672', 'email': '24horas@taller.com', 'direccion': 'Carretera Nacional Km40', 'poblacion': 'Tres Cantos', 'zona_id': 8},
            {'nombre': 'Repuestos Emergencia', 'telefono': '600456783', 'email': 'emergencia@repuestos.com', 'direccion': 'Carretera Nacional Km45', 'poblacion': 'Colmenar Viejo', 'zona_id': 8},
            {'nombre': 'Taller Carretera Sur', 'telefono': '600567894', 'email': 'carretera@sur.com', 'direccion': 'Carretera Nacional Km50', 'poblacion': 'Tres Cantos', 'zona_id': 8},
            {'nombre': 'AutoServicio Emergencia', 'telefono': '600678905', 'email': 'emergencia@autoservicio.com', 'direccion': 'Carretera Nacional Km55', 'poblacion': 'Colmenar Viejo', 'zona_id': 8},
            {'nombre': 'Taller Ruta', 'telefono': '600789016', 'email': 'ruta@taller.com', 'direccion': 'Carretera Nacional Km60', 'poblacion': 'Tres Cantos', 'zona_id': 8},
            {'nombre': 'Repuestos Ruta', 'telefono': '600890127', 'email': 'ruta@repuestos.com', 'direccion': 'Carretera Nacional Km65', 'poblacion': 'Colmenar Viejo', 'zona_id': 8},
            {'nombre': 'AutoTaller Ruta', 'telefono': '600901238', 'email': 'ruta@auto.com', 'direccion': 'Carretera Nacional Km70', 'poblacion': 'Tres Cantos', 'zona_id': 8},
            {'nombre': 'Taller Nacional', 'telefono': '600012349', 'email': 'nacional@taller.com', 'direccion': 'Carretera Nacional Km75', 'poblacion': 'Colmenar Viejo', 'zona_id': 8}
        ]
        
        # Agregar campo incluir aleatoriamente (70% True, 30% False)
        clientes_data = []
        for cliente in clientes_base:
            cliente['incluir'] = random.random() < 0.7  # 70% probabilidad de True
            clientes_data.append(cliente)
        
        for cliente_data in clientes_data:
            cliente = Cliente(**cliente_data)
            db.session.add(cliente)
        
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
        print("Datos de ejemplo creados exitosamente!")
        print(f"- {len(zonas)} zonas creadas")
        print(f"- {len(clientes_data)} clientes creados")
        print(f"- {len(plantillas_data)} plantillas de mensajes creadas")
        
        # Mostrar estadísticas de inclusión
        incluidos = sum(1 for c in clientes_data if c['incluir'])
        no_incluidos = len(clientes_data) - incluidos
        print(f"\nEstadísticas de inclusión:")
        print(f"- Clientes incluidos en comunicados: {incluidos}")
        print(f"- Clientes NO incluidos en comunicados: {no_incluidos}")
        
        print("\nDistribución por zonas:")
        for zona in zonas:
            clientes_zona = [c for c in clientes_data if c['zona_id'] == zona.id]
            incluidos_zona = sum(1 for c in clientes_zona if c['incluir'])
            print(f"  {zona.nombre}: {len(clientes_zona)} clientes ({incluidos_zona} incluidos)")

if __name__ == '__main__':
    resetear_y_crear_datos_con_incluir()

