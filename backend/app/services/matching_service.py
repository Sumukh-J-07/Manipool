from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.ride_request import RideRequest
from backend.app.models.user import User
from backend.app.schemas.auth import UserProfile
from backend.app.schemas.ride_request import MatchCandidateResponse

MATCHING_CONFIG = {
    "pickup_km": 2.0,
    "detour_minutes": 10.0,
    "capacity": 4,
    "weights": {
        "route": 0.35,
        "detour": 0.25,
        "time": 0.20,
        "destination": 0.15,
        "reliability": 0.05,
    },
}

# Known location coordinates and corridors for MAHE Bengaluru area
LOCATIONS_COORDS = {
    "campus": {"name": "MAHE Bengaluru Campus", "area": "Govindapura, Yelahanka", "corridor": "campus", "lat": 13.1146, "lng": 77.5936},
    "gate": {"name": "Campus main gate", "area": "MAHE Bengaluru", "corridor": "campus", "lat": 13.1150, "lng": 77.5940},
    "yelahanka": {"name": "Yelahanka New Town", "area": "North Bengaluru", "corridor": "north", "lat": 13.0998, "lng": 77.5963},
    "airport": {"name": "Kempegowda Airport", "area": "Terminal 1 • Bengaluru", "corridor": "airport", "lat": 13.1986, "lng": 77.7066},
    "metro": {"name": "Yeshwanthpur Metro", "area": "Green Line • Bengaluru", "corridor": "west", "lat": 13.0232, "lng": 77.5501},
    "railway": {"name": "Yeshwanthpur Railway Station", "area": "Bengaluru", "corridor": "west", "lat": 13.0227, "lng": 77.5492},
    "majestic": {"name": "Majestic Bus Station", "area": "Kempegowda Bus Station", "corridor": "central", "lat": 12.9767, "lng": 77.5713},
    "church": {"name": "Church Street", "area": "Central Bengaluru", "corridor": "central", "lat": 12.9749, "lng": 77.6094},
}


def time_windows_overlap(
    dep_a: datetime, flex_a_min: int, dep_b: datetime, flex_b_min: int
) -> bool:
    diff_seconds = abs((dep_a - dep_b).total_seconds())
    allowed_seconds = (flex_a_min + flex_b_min) * 60
    return diff_seconds <= allowed_seconds


def calculate_pickup_distance_km(req_a: RideRequest, req_b: RideRequest) -> float:
    if req_a.pickup_id == req_b.pickup_id:
        return 0.2
    loc_a = LOCATIONS_COORDS.get(req_a.pickup_id)
    loc_b = LOCATIONS_COORDS.get(req_b.pickup_id)
    if loc_a and loc_b and loc_a.get("lat") and loc_b.get("lat"):
        # Approximate euclidean distance in km for Bengaluru lat/lng (1 deg ~ 111km)
        d_lat = (loc_a["lat"] - loc_b["lat"]) * 111.0
        d_lng = (loc_a["lng"] - loc_b["lng"]) * 111.0 * 0.97
        dist = (d_lat**2 + d_lng**2) ** 0.5
        return min(dist, 5.0)
    return 1.2


def calculate_detour_minutes(pickup_km: float) -> int:
    # Estimate ~3 mins base detour plus 2 mins per km
    return int(min(max(2 + pickup_km * 2.5, 2.0), 15.0))


def calculate_route_overlap(req_a: RideRequest, req_b: RideRequest) -> float:
    if req_a.destination_id == req_b.destination_id:
        return 0.95
    if req_a.destination_corridor == req_b.destination_corridor:
        return 0.85
    return 0.50


async def find_matches_for_request(
    request: RideRequest, db: AsyncSession, capacity: int = 4
) -> List[MatchCandidateResponse]:
    # Query other active requests in SEARCHING or MATCH_FOUND
    stmt = (
        select(RideRequest, User)
        .join(User, RideRequest.user_id == User.id)
        .where(
            RideRequest.id != request.id,
            RideRequest.user_id != request.user_id,
            RideRequest.status.in_(["SEARCHING", "MATCH_FOUND"]),
        )
    )
    result = await db.execute(stmt)
    rows = result.all()

    candidates: List[MatchCandidateResponse] = []
    weights = MATCHING_CONFIG["weights"]

    for other_req, other_user in rows:
        # Check destination compatibility (same destination or corridor)
        dest_match = other_req.destination_id == request.destination_id
        corridor_match = (
            other_req.destination_corridor == request.destination_corridor
        )
        if not (dest_match or corridor_match):
            continue

        # Check time window overlap
        if not time_windows_overlap(
            request.departure,
            request.flexibility,
            other_req.departure,
            other_req.flexibility,
        ):
            continue

        pickup_km = calculate_pickup_distance_km(request, other_req)
        if pickup_km > MATCHING_CONFIG["pickup_km"]:
            continue

        detour_mins = calculate_detour_minutes(pickup_km)
        if detour_mins > MATCHING_CONFIG["detour_minutes"]:
            continue

        route_overlap = calculate_route_overlap(request, other_req)
        if route_overlap < 0.65:
            continue

        reliability = 0.85  # default baseline student reliability
        diff_mins = abs(
            (other_req.departure - request.departure).total_seconds()
        ) / 60.0

        # Calculate matching score
        time_score = 1.0 - min(diff_mins / 90.0, 1.0)
        detour_score = 1.0 - (detour_mins / MATCHING_CONFIG["detour_minutes"])
        dest_score = 1.0 if dest_match else 0.8

        score = (
            route_overlap * weights["route"]
            + detour_score * weights["detour"]
            + time_score * weights["time"]
            + dest_score * weights["destination"]
            + reliability * weights["reliability"]
        )

        candidates.append(
            MatchCandidateResponse(
                id=f"{request.id}-{other_user.id}",
                student=UserProfile.model_validate(other_user),
                request_id=other_req.id,
                departure=other_req.departure.isoformat(),
                flexibility=other_req.flexibility,
                destination_id=other_req.destination_id,
                corridor=other_req.destination_corridor,
                pickup_km=round(pickup_km, 2),
                detour_minutes=detour_mins,
                route_overlap=round(route_overlap, 2),
                reliability=reliability,
                score=round(score, 3),
            )
        )

    # Sort candidates by descending score
    candidates.sort(key=lambda c: (-c.score, c.student.name))
    return candidates[: capacity - 1]
