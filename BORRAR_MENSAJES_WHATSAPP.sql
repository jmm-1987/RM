-- ============================================
-- SENTENCIAS SQL PARA BORRAR MENSAJES DE WHATSAPP
-- ============================================
-- Ejecutar en pgAdmin con cuidado - ESTAS OPERACIONES NO SE PUEDEN DESHACER
-- ============================================

-- OPCIÓN 1: Borrar SOLO los mensajes (deja las conversaciones vacías)
-- Esta es la opción más segura si quieres mantener el historial de conversaciones
DELETE FROM whatsapp_message;

-- Verificar cuántos mensajes quedan (debería ser 0)
SELECT COUNT(*) as mensajes_restantes FROM whatsapp_message;


-- ============================================
-- OPCIÓN 2: Borrar mensajes Y conversaciones (borra todo)
-- Descomenta las siguientes líneas si quieres borrar también las conversaciones
-- ============================================

-- Primero borrar los mensajes (necesario por la foreign key)
-- DELETE FROM whatsapp_message;

-- Luego borrar las conversaciones
-- DELETE FROM whatsapp_conversation;

-- Verificar que todo está borrado
-- SELECT COUNT(*) as conversaciones_restantes FROM whatsapp_conversation;
-- SELECT COUNT(*) as mensajes_restantes FROM whatsapp_message;


-- ============================================
-- OPCIÓN 3: Borrar solo mensajes de un rango de fechas
-- Útil si quieres limpiar mensajes antiguos pero mantener los recientes
-- ============================================

-- Ejemplo: Borrar mensajes anteriores al 1 de enero de 2024
-- DELETE FROM whatsapp_message 
-- WHERE sent_at < '2024-01-01 00:00:00';

-- Verificar cuántos mensajes se borraron
-- SELECT COUNT(*) as mensajes_borrados 
-- FROM whatsapp_message 
-- WHERE sent_at < '2024-01-01 00:00:00';


-- ============================================
-- RECOMENDACIÓN: Hacer backup antes de borrar
-- ============================================
-- Antes de ejecutar DELETE, puedes hacer un backup con:
-- 
-- CREATE TABLE whatsapp_message_backup AS SELECT * FROM whatsapp_message;
-- CREATE TABLE whatsapp_conversation_backup AS SELECT * FROM whatsapp_conversation;
--
-- Para restaurar después:
-- INSERT INTO whatsapp_message SELECT * FROM whatsapp_message_backup;
-- INSERT INTO whatsapp_conversation SELECT * FROM whatsapp_conversation_backup;


