# Irrigo

Irrigo es una plataforma IoT para monitorización y gestión de sistemas de riego.

Permite registrar sistemas de riego, asociar sensores, almacenar medidas históricas, compartir sistemas entre usuarios mediante roles y visualizar los datos desde una interfaz web.

El proyecto está dividido en un backend desarrollado con FastAPI y un frontend desarrollado con React + Vite.

---

# Arquitectura

```text
Irrigo
├── backend (backend FastAPI de la plataforma)
│   ├── api (endpoints REST y lógica de acceso)
│   │   ├── deps.py
│   │   └── routes
│   │       ├── auth.py
│   │       ├── irrigation_systems.py
│   │       ├── sensors.py
│   │       └── users.py
│   │
│   ├── core (configuración global, seguridad y utilidades comunes)
│   │   ├── config.py
│   │   └── security.py
│   │
│   ├── db (conexión, inicialización y gestión de la base de datos)
│   │   ├── base.py
│   │   ├── db.py
│   │   ├── init_db.py
│   │   └── seed.py
│   │
│   ├── Dockerfile
│   ├── main.py
│   │
│   ├── models (modelos SQLAlchemy y definición de entidades)
│   │   ├── actuator_action.py
│   │   ├── actuator_event.py
│   │   ├── irrigation_system.py
│   │   ├── rule_condition.py
│   │   ├── rule_group_action.py
│   │   ├── rule_group.py
│   │   ├── sensor_reading.py
│   │   ├── system_actuator.py
│   │   ├── system_sensor.py
│   │   ├── system_user.py
│   │   └── user.py
│   │
│   ├── schemas (validación y serialización mediante Pydantic)
│   │   ├── auth.py
│   │   ├── irrigation_system.py
│   │   ├── sensor.py
│   │   ├── system_user.py
│   │   └── user.py
│   │
│   └── tests (tests automatizados del backend)
│       ├── test_irrigation_system.py
│       └── test_users.py
│
├── docker-compose.yml
│
├── docs (documentación técnica del proyecto)
│   └── bbdd.txt
│
├── frontend (interfaz web desarrollada con React)
│   ├── Dockerfile
│   ├── eslint.config.js
│   ├── index.html
│   ├── nginx.conf
│   ├── package.json
│   ├── package-lock.json
│   │
│   ├── node_modules (dependencias instaladas por npm)
│   │   └── [...]
│   │
│   ├── public (recursos estáticos públicos)
│   │   ├── favicon.svg
│   │   └── icons.svg
│   │
│   ├── README.md
│   │
│   ├── src (código fuente de la aplicación)
│   │   ├── api (clientes HTTP y acceso a la API)
│   │   │   └── api.js
│   │   │
│   │   ├── assets (imágenes y recursos gráficos)
│   │   │   ├── hero.png
│   │   │   ├── react.svg
│   │   │   └── vite.svg
│   │   │
│   │   ├── components (componentes reutilizables)
│   │   │   ├── AppNavbar.jsx
│   │   │   └── ProtectedRoute.jsx
│   │   │
│   │   ├── context (estado global y contextos React)
│   │   │   ├── AuthContext.jsx
│   │   │   └── ToastContext.jsx
│   │   │
│   │   ├── pages (pantallas principales de la aplicación)
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── LandingPage.jsx
│   │   │   ├── LoginPage.jsx
│   │   │   ├── MeasuresPage.jsx
│   │   │   └── SystemsPage.jsx
│   │   │
│   │   └── styles (temas y estilos personalizados)
│   │       └── theme.css
│   │
│   ├── App.css
│   ├── App.jsx
│   ├── index.css
│   ├── main.jsx
│   └── vite.config.js
│
└── README.md

```

---

# Docker

El proyecto está preparado para ejecutarse mediante Docker Compose.

## Levantar el entorno

```bash
docker compose up --build
```

## Detener servicios

```bash
docker compose down
```

# Electrónica

Irrigo está diseñado para ejecutarse sobre una unidad de control basada en ESP32 encargada de la adquisición de datos, ejecución local de automatizaciones y comunicación con la plataforma central.

El objetivo es que el sistema pueda seguir funcionando de forma autónoma incluso ante pérdidas prolongadas de conectividad.

## Arquitectura General

```text
                    ┌─────────────────────┐
                    │     Servidor        │
                    │      Irrigo         │
                    └──────────┬──────────┘
                               │
                         WiFi / MQTT
                               │
                    ┌──────────▼──────────┐
                    │       ESP32         │
                    │ Controlador central │
                    └───────┬─────┬───────┘
                            │     │
              ┌─────────────┘     └─────────────┐
              │                                 │
      Sensores de campo                Actuadores
  (humedad, temperatura,          (válvulas, relés,
   presión, caudal, etc.)           bombas, etc.)
```

## ESP32

El ESP32 actúa como unidad central del sistema.

### Entradas

Soporte para múltiples sensores:

- Humedad de suelo
- Temperatura
- Humedad ambiental
- Presión
- Caudal
- Nivel
- Sensores analógicos y digitales

### Salidas

Dispondrá de 4 salidas para el control de:

- Electroválvulas
- Relés
- Bombas
- Otros actuadores compatibles

## Almacenamiento Local

El sistema incorporará una tarjeta microSD para almacenar:

- Medidas pendientes de sincronización
- Configuración descargada del servidor
- Reglas automáticas de actuación

## Funcionamiento Offline

El ESP32 consultará periódicamente al servidor para obtener cambios de configuración y nuevas reglas.

Si pierde conectividad:

- Continuará registrando medidas
- Continuará ejecutando reglas locales
- Continuará actuando sobre los dispositivos configurados

Cuando recupere la conexión sincronizará automáticamente la información pendiente.

## Estación Meteorológica

Se prevé soporte para una estación meteorológica integrada capaz de registrar:

- Temperatura
- Humedad
- Presión atmosférica
- Velocidad y dirección del viento
- Radiación solar
- Precipitación

Estos datos podrán utilizarse para optimizar los algoritmos de riego y reducir el consumo de agua.


# Tests backend

## Cargar datos de ejemplo

```bash
docker compose exec backend python db/seed.py
```
## Ejecutar tests

```bash
docker compose exec backend pytest tests/test_users.py
```

```bash
docker compose exec backend pytest tests/test_irrigation_system.py
```


# Roles

Actualmente existen tres niveles de acceso:

| Rol | Permisos |
|------|-----------|
| owner | Control total del sistema |
| maintainer | Modificación del sistema y sensores |
| viewer | Solo lectura |

---

# API Key

Cada sistema dispone de una API Key única utilizada por dispositivos IoT para:

- Registrar sensores
- Enviar medidas
- Registrar eventos

La API Key puede regenerarse desde la interfaz web.

---

# TODO

## Backend

- [ ] CRUD completo de actuadores
- [ ] Motor de reglas automáticas
- [ ] Ejecución programada de acciones
- [ ] Exportación de históricos
- [ ] system_last_seen_at en los IrrigationSystem.

## Frontend

- [ ] Dashboard con métricas agregadas
- [ ] Gestión visual de reglas
- [ ] Gestión de actuadores
- [ ] Configuración avanzada de sensores
- [ ] Modo móvil optimizado

## IoT

- [ ] Cliente ESP32 de referencia

---

# Estado del proyecto

Proyecto actualmente en desarrollo activo.