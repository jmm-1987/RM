#!/usr/bin/env bash
# Script de build para Render con reintentos para problemas de red

set -e

echo "🔧 Instalando dependencias con reintentos..."

# Actualizar pip primero
pip install --upgrade pip

# Instalar dependencias con reintentos y timeout aumentado
pip install --retries 5 --timeout 300 -r requirements.txt

echo "✅ Dependencias instaladas correctamente"

