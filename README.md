# IRRIGO


# Estructura planteada

├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── logging.py
│   │
│   ├── db/
│   │   ├── db.py
│   │   └── base.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── system.py
│   │   ├── sensor.py
│   │   ├── command.py
│   │   ├── event.py
│   │   └── rule.py
│   │
│   ├── schemas/
│   │   ├── user.py
│   │   ├── auth.py
│   │   ├── sensor.py
│   │   ├── command.py
│   │   └── rule.py
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── users.py
│   │   │   ├── auth.py
│   │   │   ├── systems.py
│   │   │   ├── sensors.py
│   │   │   ├── commands.py
│   │   │   ├── events.py
│   │   │   └── rules.py
│   │   │
│   │   └── deps.py
│   │
│   ├── services/
│   │   ├── user_service.py
│   │   ├── rule_engine.py
│   │   ├── command_service.py
│   │   ├── event_service.py
│   │   └── sensor_service.py
│   │
│   └── utils/
│       ├── ...
│
├── tests/
│       ├── ...
│
├── requirements.txt
├── README.md
├── .env.example
├── docker-compose.yml
└── Dockerfile