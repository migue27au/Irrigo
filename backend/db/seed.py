from datetime import datetime, timedelta
import random

from db.db import SessionLocal

from core.security import hash_password

from models.user import User
from models.irrigation_system import IrrigationSystem
from models.system_user import SystemUser
from models.system_sensor import Sensor
from models.sensor_reading import SensorReading


def log(msg):
    print(f"[SEED] {msg}")


# docker compose exec backend python -m db.seed

def create_system_if_missing(db, owner, alias, description):
    log(f"Checking system: {alias}")

    system = (
        db.query(IrrigationSystem)
        .filter(IrrigationSystem.alias == alias)
        .first()
    )

    if system:
        log(f"System already exists: {alias}")
        return system

    system = IrrigationSystem(
        alias=alias,
        description=description,
        api_key=f"seed-{alias.lower().replace(' ', '-')}"
    )

    db.add(system)
    db.flush()

    db.add(
        SystemUser(
            system_id=system.id,
            user_id=owner.id,
            role="owner"
        )
    )

    log(f"Created system: {alias} (id={system.id})")

    return system


def share_if_missing(db, system, user, role):
    log(f"Sharing system {system.alias} -> {user.username} as {role}")

    relation = (
        db.query(SystemUser)
        .filter(
            SystemUser.system_id == system.id,
            SystemUser.user_id == user.id
        )
        .first()
    )

    if relation:
        log("Share already exists, updating role")
        relation.role = role
        return

    db.add(
        SystemUser(
            system_id=system.id,
            user_id=user.id,
            role=role
        )
    )


def create_sensor_if_missing(db, system, sensor_key, sensor_type, unit):
    log(f"  [SENSOR CHECK] {system.alias} -> {sensor_key}")

    sensor = (
        db.query(Sensor)
        .filter(
            Sensor.system_id == system.id,
            Sensor.sensor_key == sensor_key
        )
        .first()
    )

    if sensor:
        log(f"  Sensor exists: {sensor_key}")
        return sensor

    sensor = Sensor(
        system_id=system.id,
        sensor_key=sensor_key,
        name=sensor_key,
        sensor_type=sensor_type,
        unit=unit,
    )

    db.add(sensor)
    db.flush()

    log(f"  CREATED sensor: {sensor_key} (id={sensor.id})")

    return sensor


def create_readings_if_missing(db, sensor):
    log(f"    [READINGS CHECK] sensor={sensor.sensor_key}")

    existing = (
        db.query(SensorReading)
        .filter(SensorReading.sensor_id == sensor.id)
        .count()
    )

    if existing > 0:
        log(f"    Already has {existing} readings -> skipping")
        return

    now = datetime.utcnow()

    for i in range(10):

        if sensor.sensor_key.startswith("temp"):
            value = round(random.uniform(15, 35), 2)

        elif sensor.sensor_key.startswith("soil"):
            value = round(random.uniform(0, 100), 2)

        else:
            value = round(random.uniform(30, 90), 2)

        reading = SensorReading(
            sensor_id=sensor.id,
            value=value,
            recorded_at=now - timedelta(minutes=i * 15)
        )

        db.add(reading)

    log(f"    CREATED 10 readings for {sensor.sensor_key}")


def run():
    db = SessionLocal()

    try:
        log("START SEED")

        # -------------------------------------------------
        # USERS
        # -------------------------------------------------

        log("Creating users...")

        admin = db.query(User).filter_by(username="admin").first()

        if not admin:
            admin = User(
                username="admin",
                password_hash=hash_password("admin"),
                name="Admin",
                role="admin"
            )
            db.add(admin)
            log("Created admin user")

        test = db.query(User).filter_by(username="test").first()

        if not test:
            test = User(
                username="test",
                password_hash=hash_password("test"),
                name="Test User",
                role="user"
            )
            db.add(test)
            log("Created test user")

        db.commit()

        test.password_hash = hash_password("test")

        db.commit()

        db.refresh(admin)
        db.refresh(test)

        log("Users ready")

        # -------------------------------------------------
        # SYSTEMS
        # -------------------------------------------------

        log("Creating systems...")

        admin_systems = [
            ("Huerto Principal", "Zona principal de cultivo"),
            ("Invernadero Norte", "Producción protegida"),
            ("Jardín Ornamental", "Plantas decorativas"),
        ]

        test_systems = [
            ("Huerto Familiar", "Huerto doméstico"),
            ("Invernadero Experimental", "Pruebas de cultivo"),
            ("Jardín Trasero", "Zona recreativa"),
        ]

        created_admin = []
        created_test = []

        for alias, description in admin_systems:
            created_admin.append(create_system_if_missing(db, admin, alias, description))

        for alias, description in test_systems:
            created_test.append(create_system_if_missing(db, test, alias, description))

        db.flush()

        # -------------------------------------------------
        # SHARES
        # -------------------------------------------------

        log("Creating shares...")

        share_if_missing(db, created_admin[0], test, "maintainer")
        share_if_missing(db, created_admin[1], test, "viewer")

        share_if_missing(db, created_test[0], admin, "maintainer")
        share_if_missing(db, created_test[1], admin, "viewer")

        db.flush()

        # -------------------------------------------------
        # SENSORS
        # -------------------------------------------------

        log("Creating sensors + readings...")

        sensor_defs = [
            ("temp1", "temperature", "°C"),
            ("temp2", "temperature", "°C"),
            ("soil1", "soil_moisture", "%"),
            ("soil2", "soil_moisture", "%"),
            ("humidity1", "humidity", "%"),
            ("humidity2", "humidity", "%"),
        ]

        all_systems = created_admin + created_test

        for system in all_systems:
            log(f" SYSTEM: {system.alias}")

            for sensor_key, sensor_type, unit in sensor_defs:
                sensor = create_sensor_if_missing(
                    db,
                    system,
                    sensor_key,
                    sensor_type,
                    unit
                )

                create_readings_if_missing(db, sensor)

        db.commit()

        log("SEED COMPLETED SUCCESSFULLY")

        log(f"Systems: {len(all_systems)}")
        log(f"Sensors per system: {len(sensor_defs)}")
        log(f"Total sensors: {len(all_systems) * len(sensor_defs)}")

    finally:
        db.close()


if __name__ == "__main__":
    run()