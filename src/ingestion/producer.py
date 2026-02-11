import sys
from pathlib import Path

# add project root (aws-netflix-streaming-pipeline) to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # src
PROJECT_ROOT = PROJECT_ROOT.parent                  # project root
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import argparse
import json
import time
from typing import Dict

import boto3

from config.resources import KINESIS_STREAM_NAME, KINESIS_REGION


def build_event() -> Dict:
    event = {
        "user_id": 1,
        "title_id": 100,
        "event_type": "PLAY_START",
        "event_ts": int(time.time()),
        "device_type": "mobile",
        "country": "IN",
        "playback_position_sec": 0,
        "total_duration_sec": 3600,
    }
    return event


def send_to_kinesis(event: Dict) -> None:
    client = boto3.client("kinesis", region_name=KINESIS_REGION)

    payload = json.dumps(event).encode("utf-8")

    response = client.put_record(
        StreamName=KINESIS_STREAM_NAME,
        Data=payload,
        PartitionKey=str(event["user_id"]),
    )
    # print(response)


def main():
    parser = argparse.ArgumentParser(description="Netflix events producer")
    parser.add_argument(
        "--mode",
        choices=["kinesis"],
        default="kinesis",
        help="Currently only kinesis mode is supported.",
    )
    parser.add_argument(
        "--records-per-second",
        dest="records_per_second",
        type=int,
        default=5,
        help="How many events to send per second.",
    )
    args = parser.parse_args()

    print(f"Running producer in mode={args.mode}, rps={args.records_per_second}")

    if args.mode == "kinesis":
        while True:
            for _ in range(args.records_per_second):
                event = build_event()
                send_to_kinesis(event)
            time.sleep(1)


if __name__ == "__main__":
    main()
