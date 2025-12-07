# Semantic Versioning

Este proyecto usa [Semantic Versioning 2.0.0](https://semver.org/).

## Versión Actual: 1.0.0

## Cómo Actualizar la Versión

Para actualizar la versión de la API, edita el archivo `version.py`:

```python
__version__ = "X.Y.Z"
__version_info__ = {
    "major": X,
    "minor": Y,
    "patch": Z,
    "release": "stable"  # o "beta", "alpha", etc.
}
```

### Formato de Versionado

- **MAJOR** (X): Cambios incompatibles con versiones anteriores
- **MINOR** (Y): Nueva funcionalidad compatible con versiones anteriores
- **PATCH** (Z): Correcciones de bugs compatibles con versiones anteriores

## Verificar la Versión en Producción

### Endpoint `/version`
```bash
curl http://localhost:3010/version
```

Respuesta:
```json
{
  "version": "1.0.0",
  "version_info": {
    "major": 1,
    "minor": 0,
    "patch": 0,
    "release": "stable"
  },
  "api_name": "YFinance Simple API"
}
```

### Endpoint `/health`
```bash
curl http://localhost:3010/health
```

Respuesta:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "cache_info": {
    "has_cache": false,
    "cache_timestamp": null
  }
}
```

### Logs de Inicio
Al iniciar la aplicación, los logs mostrarán:
```
============================================================
Starting YFinance Simple API v1.0.0
Version info: {'major': 1, 'minor': 0, 'patch': 0, 'release': 'stable'}
Port: 3010
============================================================
```

## Changelog

### [1.0.0] - 2025-12-07
#### Added
- Sistema de versionado semántico
- Endpoint `/version` para consultar la versión
- Información de versión en endpoint `/health`
- Información de versión en logs de inicio
- Endpoint `/precio/{ticker}` para obtener precios en EUR
- Cache de tipo de cambio USD/EUR (5 minutos)
