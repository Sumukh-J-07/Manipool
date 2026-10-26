from typing import Dict, List

VEHICLE_OPTIONS: Dict[str, dict] = {
    "cab": {
        "id": "cab",
        "name": "Shared cab",
        "capacity": 4,
        "fare_paise": 84000,
    },
    "auto": {
        "id": "auto",
        "name": "Shared auto",
        "capacity": 2,
        "fare_paise": 62000,
    },
}


def split_fare(total_paise: int, passengers: int) -> List[int]:
    if total_paise < 0 or passengers < 1 or passengers > 4:
        raise ValueError("Invalid fare or group size (must be 1-4 passengers).")

    base = total_paise // passengers
    remainder = total_paise % passengers
    return [base + (1 if i < remainder else 0) for i in range(passengers)]
