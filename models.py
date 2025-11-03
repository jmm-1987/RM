from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Zona(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación con clientes
    clientes = db.relationship('Cliente', backref='zona', lazy=True)
    
    def __repr__(self):
        return f'<Zona {self.nombre}>'

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    direccion = db.Column(db.Text)
    poblacion = db.Column(db.String(100))
    zona_id = db.Column(db.Integer, db.ForeignKey('zona.id'), nullable=False)
    incluir = db.Column(db.Boolean, default=True)
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación con mensajes enviados
    mensajes_enviados = db.relationship('MensajeEnviado', backref='cliente', lazy=True)
    
    def __repr__(self):
        return f'<Cliente {self.nombre}>'

class MensajePlantilla(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación con mensajes enviados
    mensajes_enviados = db.relationship('MensajeEnviado', backref='plantilla', lazy=True)
    
    def __repr__(self):
        return f'<MensajePlantilla {self.nombre}>'

class Oferta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    imagen = db.Column(db.String(255))  # Ruta de la imagen
    activa = db.Column(db.Boolean, default=True)
    destacada = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Oferta {self.titulo}>'

class MensajeEnviado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    plantilla_id = db.Column(db.Integer, db.ForeignKey('mensaje_plantilla.id'), nullable=False)
    mensaje_final = db.Column(db.Text, nullable=False)
    enviado = db.Column(db.Boolean, default=False)
    fecha_envio = db.Column(db.DateTime)
    error = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MensajeEnviado {self.id}>'

class MensajeOferta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    oferta_id = db.Column(db.Integer, db.ForeignKey('oferta.id'), nullable=False)
    mensaje_personalizado = db.Column(db.Text, nullable=False)
    imagen_enviada = db.Column(db.Boolean, default=False)
    mensaje_enviado = db.Column(db.Boolean, default=False)
    fecha_envio = db.Column(db.DateTime)
    error = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    cliente = db.relationship('Cliente', backref='mensajes_ofertas')
    oferta = db.relationship('Oferta', backref='mensajes_enviados')
    
    def __repr__(self):
        return f'<MensajeOferta {self.id}>'

class MensajeRecibido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telefono_remitente = db.Column(db.String(20), nullable=False)
    nombre_remitente = db.Column(db.String(100))
    mensaje = db.Column(db.Text, nullable=False)
    tipo_mensaje = db.Column(db.String(20), default='texto')  # texto, imagen, audio, etc.
    archivo_url = db.Column(db.String(500))  # URL del archivo si es multimedia
    leido = db.Column(db.Boolean, default=False)
    respondido = db.Column(db.Boolean, default=False)
    fecha_recepcion = db.Column(db.DateTime, default=datetime.utcnow)
    id_mensaje_whatsapp = db.Column(db.String(100))  # ID del mensaje en WhatsApp
    
    # Relación opcional con cliente existente
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)
    cliente = db.relationship('Cliente', backref='mensajes_recibidos')
    
    def __repr__(self):
        return f'<MensajeRecibido {self.id} de {self.telefono_remitente}>'

class RespuestaMensaje(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mensaje_recibido_id = db.Column(db.Integer, db.ForeignKey('mensaje_recibido.id'), nullable=False)
    respuesta = db.Column(db.Text, nullable=False)
    enviado = db.Column(db.Boolean, default=False)
    fecha_envio = db.Column(db.DateTime)
    error = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación
    mensaje_recibido = db.relationship('MensajeRecibido', backref='respuestas')
    
    def __repr__(self):
        return f'<RespuestaMensaje {self.id}>'


class ProgramacionMasiva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zona_id = db.Column(db.Integer, db.ForeignKey('zona.id'), nullable=False)
    plantilla_id = db.Column(db.Integer, db.ForeignKey('mensaje_plantilla.id'), nullable=False)
    # Días de la semana como números separados por coma: 0=Lunes ... 6=Domingo
    dias_semana = db.Column(db.String(20), nullable=False)
    # Hora en formato HH:MM (24h)
    hora = db.Column(db.String(5), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    ultima_ejecucion = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    zona = db.relationship('Zona', backref='programaciones_masivas')
    plantilla = db.relationship('MensajePlantilla', backref='programaciones_masivas')

    def __repr__(self):
        return f'<ProgramacionMasiva zona={self.zona_id} hora={self.hora} dias={self.dias_semana}>'
