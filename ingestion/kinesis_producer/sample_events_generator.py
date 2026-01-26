import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

EVENT_TYPES = ["play", "pause", "seek", "stop", "search"]
DEVICE_TYPES = ["mobile", "tv", "web"]
COUNTRIES = ["IN", "US", "UK", "DE", "BR"]
TITLE_IDS = [f"title_{i}" for i in range(1, 21)]
USER_IDS = [f"user_{i}" for i in range(1, 51)]
PROFILE_IDS = [f"profile_{i}" for i in range(1, 101)]
SEARCH_QUERIES = [
    "action movies",
    "romantic comedy",
    "thriller",
    "kids cartoons",
    "bollywood",
    "hollywood",
]
def generate_base_event(event_type: str) -> dict:
    now = datetime.now(timezone.utc)
    # A lil random time offset (last 15 minutes ke andar)
    timestamp = now - timedelta(seconds=random.randint(0, 15 * 60))

    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "event_timestamp": timestamp.isoformat(),
        "user_id": random.choice(USER_IDS),
        "profile_id": random.choice(PROFILE_IDS),
        "title_id": random.choice(TITLE_IDS),
        "device_type": random.choice(DEVICE_TYPES),
        "country": random.choice(COUNTRIES),
        "partition_key": None,  # Kinesis-ready design
    }

    # Partition key strategy: user-based
    event["partition_key"] = event["user_id"]

    # Conditional fields
    if event_type in ["play", "pause", "seek", "stop"]:
        event["position_seconds"] = random.randint(0, 60 * 60)  # 0–3600 sec
    if event_type in ["play", "seek"]:
        event["duration_seconds"] = random.randint(5, 600)  # 5–600 sec
    if event_type == "search":
        event["search_query"] = random.choice(SEARCH_QUERIES)

    return event

def generate_events(count: int = 100) -> list:
    events = []
    for _ in range(count):
        event_type = random.choice(EVENT_TYPES)
        events.append(generate_base_event(event_type))
    return events


def save_events_to_file(events, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")


def main():
    count = 100
    output_path = Path(__file__).parent / "events_sample.json"

    events = generate_events(count)
    save_events_to_file(events, output_path)

    print(f"Generated {len(events)} events -> {output_path}")
    print("Sample events:")
    for e in events[:3]:
        print(json.dumps(e, indent=2))


if __name__ == "__main__":
    main()
