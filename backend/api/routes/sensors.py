from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.deps import (
    get_db,
    get_current_user,
    get_system_by_api_key,
    get_sensor_with_access,
)

from models.system_sensor import Sensor
from models.measure import Measure
from models.system_user import SystemUser

from schemas.sensor import (
    SensorBatchCreate,
    SensorOut,
    SensorUpdate,
    MeasureBatch,
)

router = APIRouter(prefix="/sensors", tags=["Sensors"])


# -----------------------------------------------------
# REGISTER SENSORS (ESP32)
# -----------------------------------------------------
@router.post("/create")
def create_sensors(
    payload: SensorBatchCreate,
    db: Session = Depends(get_db),
    system=Depends(get_system_by_api_key),
):
    created = []
    existing = []
    print("*"*40)
    print(payload.sensors)
    for item in payload.sensors:

        sensor = (
            db.query(Sensor)
            .filter(
                Sensor.system_id == system.id,
                Sensor.sensor_key == item.sensor_key
            )
            .first()
        )

        if sensor:
            existing.append(sensor.sensor_key)
            continue

        sensor = Sensor(
            system_id=system.id,
            sensor_key=item.sensor_key,
            unit=item.unit,
            sensor_type=item.sensor_type,
        )

        db.add(sensor)
        db.flush()

        created.append(sensor.sensor_key)

    db.commit()

    return {
        "created": created,
        "existing": existing,
    }

# -----------------------------------------------------
# UPDATE SENSOR
# -----------------------------------------------------
@router.put("/{sensor_id}")
def update_sensor(
    sensor_id: int,
    data: SensorUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    sensor, role = get_sensor_with_access(db, sensor_id, user.id)

    if data.name is not None:
        sensor.name = data.name

    if data.unit is not None:
        sensor.unit = data.unit

    db.commit()
    db.refresh(sensor)

    return sensor
    
# -----------------------------------------------------
# INGEST BATCH DATA
# -----------------------------------------------------
@router.post("/ingest")
def ingest_sensor_data(
    payload: MeasureBatch,
    db: Session = Depends(get_db),
    system=Depends(get_system_by_api_key),
):
    ingested = []

    for item in payload.data:
        # skip invalid entries
        if item.sensor_key is None or item.value is None or item.timestamp is None:
            continue
        if item.sensor_key == "" or item.timestamp == "":
            continue

        sensor = (
            db.query(Sensor)
            .filter(
                Sensor.system_id == system.id,
                Sensor.sensor_key == item.sensor_key,
            )
            .first()
        )

        if not sensor:
            continue

        reading = Measure(
            sensor_id=sensor.id,
            value=item.value,
            recorded_at=item.timestamp or datetime.utcnow(),
        )

        db.add(reading)

        ingested.append(sensor.sensor_key)

    db.commit()

    return {
        "status": "ok",
        "ingested": ingested,
    }


# -----------------------------------------------------
# INGEST SINGLE SENSOR
# -----------------------------------------------------
@router.post("/ingest/{sensor_id}")
def ingest_single_sensor(
    sensor_id: int,
    value: float,
    db: Session = Depends(get_db),
    system=Depends(get_system_by_api_key),
):
    sensor = (
        db.query(Sensor)
        .filter(
            Sensor.id == sensor_id,
            Sensor.system_id == system.id
        )
        .first()
    )

    if not sensor:
        raise HTTPException(
            status_code=404,
            detail="Sensor not found"
        )

    reading = Measure(
        sensor_id=sensor.id,
        value=value,
        recorded_at=datetime.utcnow(),
    )

    db.add(reading)
    db.commit()

    return {"status": "ok"}


# -----------------------------------------------------
# GET LATEST VALUE
# -----------------------------------------------------
@router.get("/{sensor_id}/latest")
def get_latest_sensor_value(
    sensor_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    sensor, role = get_sensor_with_access(
        db=db,
        sensor_id=sensor_id,
        user_id=user.id,
        require_role="viewer"
    )

    reading = (
        db.query(Measure)
        .filter(
            Measure.sensor_id == sensor.id
        )
        .order_by(
            Measure.recorded_at.desc()
        )
        .first()
    )

    if not reading:
        return {
            "sensor_id": sensor.id,
            "value": None,
            "recorded_at": None,
        }

    return {
        "sensor_id": sensor.id,
        "value": reading.value,
        "recorded_at": reading.recorded_at,
    }


# -----------------------------------------------------
# GET HISTORY
# -----------------------------------------------------
@router.get("/history")
def get_multi_sensor_history(
    sensor_ids: str = Query(...),  # "1,2,3"
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    ids = [int(x) for x in sensor_ids.split(",") if x.strip().isdigit()]

    # access check (viewer+)
    sensors = []
    for sid in ids:
        sensor, role = get_sensor_with_access(db, sid, user.id)

        if role not in ["viewer", "maintainer", "owner"]:
            continue

        sensors.append(sensor)

    result = []

    for sensor in sensors:
        query = db.query(Measure).filter(
            Measure.sensor_id == sensor.id
        )

        if from_date:
            query = query.filter(Measure.recorded_at >= from_date)

        if to_date:
            query = query.filter(Measure.recorded_at <= to_date)

        readings = query.order_by(Measure.recorded_at.asc()).all()

        result.append({
            "sensor_id": sensor.id,
            "sensor_name": sensor.name,
            "sensor_key": sensor.sensor_key,
            "unit": sensor.unit,
            "points": [
                {
                    "t": r.recorded_at,
                    "v": float(r.value)
                }
                for r in readings
            ]
        })

    return {"data": result}

@router.get("/{sensor_id}/history")
def get_sensor_history(
    sensor_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
    limit: int = Query(
        1000,
        ge=1,
        le=5000,
    ),
):
    sensor, role = get_sensor_with_access(
        db=db,
        sensor_id=sensor_id,
        user_id=user.id,
        require_role="viewer"
    )

    query = (
        db.query(Measure)
        .filter(
            Measure.sensor_id == sensor.id
        )
    )

    if from_date:
        query = query.filter(
            Measure.recorded_at >= from_date
        )

    if to_date:
        query = query.filter(
            Measure.recorded_at <= to_date
        )

    readings = (
        query
        .order_by(
            Measure.recorded_at.asc()
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "value": r.value,
            "recorded_at": r.recorded_at,
        }
        for r in readings
    ]
