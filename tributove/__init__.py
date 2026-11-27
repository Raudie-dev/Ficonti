"""Inicialización del paquete principal de FICONTI."""

# Usar PyMySQL como conector MySQLdb si mysqlclient no está instalado
# (entornos compartidos como cPanel sin compilador C).
try:
    import MySQLdb  # noqa: F401
except ImportError:
    try:
        import pymysql

        # Django 5.2+ exige mysqlclient >= 1.4.3 (y Django 6+ >= 2.2.1).
        if getattr(pymysql, 'version_info', (0,)) < (2, 2, 1):
            pymysql.version_info = (2, 2, 1, 'final', 0)
        pymysql.install_as_MySQLdb()
    except ImportError:
        pass
