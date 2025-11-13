-- Script para limpiar ciudades con " Noviembre" en el nombre
-- Esto actualiza la columna 'location' en la tabla events

-- Ver cuántos registros tienen " Noviembre"
SELECT COUNT(*) as total_con_noviembre
FROM events
WHERE location LIKE '% Noviembre%';

-- Ver ejemplos de registros afectados
SELECT DISTINCT location
FROM events
WHERE location LIKE '% Noviembre%'
LIMIT 20;

-- UPDATE para eliminar " Noviembre" del campo location
UPDATE events
SET location = REPLACE(location, ' Noviembre', '')
WHERE location LIKE '% Noviembre%';

-- Verificar que se actualizaron correctamente
SELECT DISTINCT location
FROM events
WHERE location IN (
    'Paris', 'Barcelona', 'Londres', 'Lyon', 'Marsella'
)
ORDER BY location;

-- Ver total de registros actualizados
SELECT COUNT(*) as total_actualizado
FROM events
WHERE location NOT LIKE '% Noviembre%';
