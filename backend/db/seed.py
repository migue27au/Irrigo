from datetime import datetime, timedelta
import random

from db.db import SessionLocal
from core.security import hash_password

from models.user import User
from models.irrigation_system import IrrigationSystem
from models.system_user import SystemUser
from models.system_sensor import Sensor
from models.sensor_reading import SensorReading

from models.system_actuator import SystemActuator
from models.actuator_command import ActuatorCommand
from models.actuator_event import ActuatorEvent

from models.rule_group import RuleGroup
from models.rule_condition import RuleCondition
from models.rule_group_actuator import RuleGroupActuator


# =========================================================
# LOG
# =========================================================

def log(msg):
    print(f"[SEED] {msg}")


def debug(section, msg):
    print(f"[SEED][{section}] {msg}")


# =========================================================
# SYSTEM HELPERS
# =========================================================

def create_system_if_missing(db, owner, alias, description):
    debug("SYSTEM", f"checking {alias}")

    system = (
        db.query(IrrigationSystem)
        .filter(IrrigationSystem.alias == alias)
        .first()
    )

    if system:
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

    return system


def share_if_missing(db, system, user, role):
    relation = (
        db.query(SystemUser)
        .filter(
            SystemUser.system_id == system.id,
            SystemUser.user_id == user.id
        )
        .first()
    )

    if relation:
        relation.role = role
        return

    db.add(
        SystemUser(
            system_id=system.id,
            user_id=user.id,
            role=role
        )
    )


# =========================================================
# SENSOR HELPERS
# =========================================================

def create_sensor_if_missing(db, system, sensor_key, sensor_type, unit):
    sensor = (
        db.query(Sensor)
        .filter(
            Sensor.system_id == system.id,
            Sensor.sensor_key == sensor_key
        )
        .first()
    )

    if sensor:
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

    return sensor


def create_readings_if_missing(db, sensor):
    existing = (
        db.query(SensorReading)
        .filter(SensorReading.sensor_id == sensor.id)
        .count()
    )

    if existing > 0:
        return

    now = datetime.utcnow()

    for i in range(10):
        if sensor.sensor_key.startswith("temp"):
            value = round(random.uniform(15, 35), 2)
        elif sensor.sensor_key.startswith("soil"):
            value = round(random.uniform(0, 100), 2)
        else:
            value = round(random.uniform(30, 90), 2)

        db.add(
            SensorReading(
                sensor_id=sensor.id,
                value=value,
                recorded_at=now - timedelta(minutes=i * 15)
            )
        )


# =========================================================
# ACTUATORS + COMMANDS
# =========================================================

def create_actuator_if_missing(db, system, name, channel):
    actuator = (
        db.query(SystemActuator)
        .filter(
            SystemActuator.system_id == system.id,
            SystemActuator.name == name
        )
        .first()
    )

    if actuator:
        return actuator

    actuator = SystemActuator(
        system_id=system.id,
        name=name,
        channel=channel,
        description=f"{name} actuator",
        is_on=False,
        intensity=None
    )

    db.add(actuator)
    db.flush()

    return actuator


def create_command(db, system, actuator, trigger_type, name):
    cmd = ActuatorCommand(
        system_id=system.id,
        actuator_id=actuator.id,
        name=name,
        trigger_type=trigger_type,
        intensity=round(random.uniform(20, 100), 2),
        duration_seconds=random.randint(60, 600),
        executed_count=0,
        enabled=True,
        created_at=datetime.utcnow()
    )

    db.add(cmd)
    db.flush()

    return cmd


def create_event(db, command):
    db.add(
        ActuatorEvent(
            actuator_id=command.actuator_id,
            command_id=command.id,
            intensity=command.intensity,
            duration_seconds=command.duration_seconds,
            trigger_type=command.trigger_type,
            recorded_at=datetime.utcnow() - timedelta(minutes=random.randint(1, 200))
        )
    )


# =========================================================
# RULE ENGINE SEED (DETERMINISTIC)
# =========================================================

def create_rule_group_with_conditions(db, system, command, idx, sensors_by_key):
    group = RuleGroup(
        system_id=system.id,
        name=f"group_{command.id}_{idx}",
        enabled=True
    )

    db.add(group)
    db.flush()

    # -------------------------
    # 0: TEMP HIGH
    # -------------------------
    if idx == 0:
        sensor = sensors_by_key[random.choice(["temp1", "temp2"])]

        db.add(
            RuleCondition(
                group_id=group.id,
                type="sensor",
                sensor_id=sensor.id,
                operator=">",
                value=30
            )
        )

    # -------------------------
    # 1: SOIL DRY
    # -------------------------
    elif idx == 1:
        sensor = sensors_by_key[random.choice(["soil1", "soil2"])]

        db.add(
            RuleCondition(
                group_id=group.id,
                type="sensor",
                sensor_id=sensor.id,
                operator="<",
                value=40
            )
        )

    # -------------------------
    # 2: TEMP + HUMIDITY (AND)
    # -------------------------
    elif idx == 2:
        temp = sensors_by_key[random.choice(["temp1", "temp2"])]
        hum = sensors_by_key[random.choice(["humidity1", "humidity2"])]

        db.add_all([
            RuleCondition(
                group_id=group.id,
                type="sensor",
                sensor_id=temp.id,
                operator=">",
                value=28
            ),
            RuleCondition(
                group_id=group.id,
                type="sensor",
                sensor_id=hum.id,
                operator="<",
                value=55
            )
        ])

    # -------------------------
    # 3: TIME RULE (CRON)
    # -------------------------
    elif idx == 3:
        db.add(
            RuleCondition(
                group_id=group.id,
                type="time",
                sensor_id=None,
                operator="==",
                value=None,
                cron="0 */6 * * *"
            )
        )

    db.add(
        RuleGroupActuator(
            group_id=group.id,
            command_id=command.id
        )
    )

    return group


# =========================================================
# MAIN
# =========================================================

def run():
    db = SessionLocal()

    try:
        log("START SEED")

        # ---------------- USERS ----------------
        admin = db.query(User).filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=hash_password("admin"),
                name="Admin",
                role="admin"
            )
            db.add(admin)

        test = db.query(User).filter_by(username="test").first()
        if not test:
            test = User(
                username="test",
                password_hash=hash_password("test"),
                name="Test User",
                role="user"
            )
            db.add(test)

        db.commit()
        db.refresh(admin)
        db.refresh(test)

        # ---------------- SYSTEMS ----------------
        systems = [
            ("Huerto Principal", "Zona principal"),
            ("Invernadero Norte", "Producción"),
            ("Jardín Ornamental", "Decorativo"),
            ("Huerto Familiar", "Casa"),
        ]

        created_systems = []

        for alias, desc in systems:
            created_systems.append(
                create_system_if_missing(db, admin, alias, desc)
            )

        db.flush()

        # ---------------- SHARES ----------------
        share_if_missing(db, created_systems[0], test, "maintainer")

        db.flush()

        # ---------------- SENSORS ----------------
        sensor_defs = [
            ("temp1", "temperature", "°C"),
            ("temp2", "temperature", "°C"),
            ("soil1", "soil", "%"),
            ("soil2", "soil", "%"),
            ("humidity1", "humidity", "%"),
            ("humidity2", "humidity", "%"),
        ]

        sensors_by_key = {}

        for system in created_systems:
            for key, stype, unit in sensor_defs:
                sensor = create_sensor_if_missing(db, system, key, stype, unit)
                create_readings_if_missing(db, sensor)
                sensors_by_key[key] = sensor

        # ---------------- ACTUATORS + COMMANDS ----------------
        actuator_defs = [
            ("Pump A", 0),
            ("Pump B", 1),
            ("Valve 1", 2),
            ("Valve 2", 3),
        ]

        for system in created_systems:

            actuators = [
                create_actuator_if_missing(db, system, name, ch)
                for name, ch in actuator_defs
            ]

            # manual commands
            for i in range(5):
                cmd = create_command(
                    db, system,
                    random.choice(actuators),
                    "manual",
                    f"manual_{i}"
                )

                if random.random() > 0.5:
                    create_event(db, cmd)
                    cmd.executed_count = 1
                    cmd.last_executed_at = datetime.utcnow()

            # automatic commands + rules
            for i in range(6):
                cmd = create_command(
                    db, system,
                    random.choice(actuators),
                    "automatic",
                    f"auto_{i}"
                )

                for idx in range(4):
                    create_rule_group_with_conditions(
                        db, system, cmd, idx, sensors_by_key
                    )

                if random.random() > 0.5:
                    create_event(db, cmd)
                    cmd.executed_count = random.randint(1, 5)
                    cmd.last_executed_at = datetime.utcnow()

        db.commit()

        log("SEED COMPLETED")

    finally:
        db.close()


if __name__ == "__main__":
    run()