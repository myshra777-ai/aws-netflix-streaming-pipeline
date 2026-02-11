import argparse
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import boto3

# ==== Config ====
AWS_REGION = "ap-south-1"  # change if needed
KINESIS_STREAM_NAME = "myshr-netflix-events-stream"

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
    # Thoda random time offset (last 15 minutes ke andar)
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


def send_events_to_kinesis(events):
    kinesis = boto3.client("kinesis", region_name=AWS_REGION)

    for event in events:
        data = json.dumps(event).encode("utf-8")
        partition_key = event["partition_key"]

        response = kinesis.put_record(
            StreamName=KINESIS_STREAM_NAME,
            Data=data,
            PartitionKey=partition_key,
        )
        # Optional: basic logging
        print(
            f"Sent event_id={event['event_id']} "
            f"to shard={response['ShardId']} "
            f"seq={response['SequenceNumber']}"
        )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Synthetic Netflix-style event generator (file or Kinesis)."
    )
    parser.add_argument(
        "--mode",
        choices=["file", "kinesis"],
        default="file",
        help="Output mode: file (default) or kinesis",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="Number of events to generate",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    events = generate_events(args.count)

    if args.mode == "file":
        output_path = Path(__file__).parent / "events_sample.json"
        save_events_to_file(events, output_path)
        print(f"Generated {len(events)} events -> {output_path}")
    else:
        print(
            f"Sending {len(events)} events to Kinesis stream "
            f"'{KINESIS_STREAM_NAME}' in region '{AWS_REGION}'"
        )
        send_events_to_kinesis(events)

    print("Sample events:")
    for e in events[:3]:
        print(json.dumps(e, indent=2))


if __name__ == "__main__":
    main()
