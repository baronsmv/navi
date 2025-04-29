db="sudo docker exec -it navi-db-1 psql -U baronsmv -d navi -c"

# Ver columnas y tipos de datos
$db "\d incident"

# Ver los primeros registros
$db "SELECT * FROM incident LIMIT 10;"

# Ver geometrías en formato legible (si hay columnas geoespaciales)
$db "SELECT id, ST_AsText(geom) FROM incident LIMIT 10;"

# Ver cuántos registros hay
$db "SELECT COUNT(*) FROM incident;"
