import boto3
import json
import random
import time
from datetime import datetime, timezone
from faker import Faker

fake = Faker()

# --- DATA GENERATION LOGIC ---

def make_normal_event() -> dict:
    now = datetime.now(timezone.utc)
    return {
        "txn_id": str(fake.uuid4()),
        "timestamp": now.isoformat(),
        "customer_ref": str(fake.uuid4()),
        "ip_address": fake.ipv4_public(),
        "status_code": random.choice([200, 201]),
        "payload_size": random.randint(1000, 500000),
        "browser_info": fake.user_agent(),
        "error_msg": None,
        "region_code": random.choice(["us-east-1", "ap-south-1", "eu-west-1"]),
        "retry_count": 0,
        "is_flagged": False,
        "junk_metadata": {
            "session_id": str(fake.uuid4()),
            "experiment_group": random.choice(["A", "B", "control"]),
        },
    }


def make_messy_event(base: dict) -> dict:
    event = dict(base)

    corruptions = [
        lambda e: e.update({"txn_id": random.choice([str(fake.uuid4()), random.randint(1, 10000), None])}),
        lambda e: e.update({"timestamp": random.choice([
            datetime.now().strftime("%d/%m/%Y"),
            int(time.time()),
            "not-a-timestamp",
            "",
        ])}),
        lambda e: e.update({"customer_ref": random.choice([fake.email(), fake.user_name(), None, ""])}),
        lambda e: e.update({"ip_address": random.choice([fake.ipv6(), "127.0.0.1", "not-an-ip", ""])}),
        lambda e: e.update({"status_code": random.choice([404, 500, "Success", "Phatt Gaya", None])}),
        lambda e: e.update({"payload_size": random.choice([
            f"{random.randint(1, 1000)}KB",
            "unknown",
            None,
        ])}),
        lambda e: e.update({"error_msg": random.choice([
            "Backend Timeout",
            "SQL Syntax Error",
            "<html>500</html>",
            "???",
        ])}),
        lambda e: e.update({"region_code": random.choice(["india", "US-East", "unknown-region", ""])}),
        lambda e: e.update({"retry_count": random.choice(["First Attempt", "N/A", None])}),
        lambda e: e.update({"is_flagged": random.choice([0, 1, "Y", "maybe"])}),
        lambda e: e.update({"junk_metadata": random.choice([
            {"random_key": fake.word()},
            {"nested": {"a": 1}},
            {},
        ])}),
    ]

    for func in random.sample(corruptions, k=random.randint(1, 3)):
        func(event)

    return event


def generate_event(bad_ratio: float = 0.15) -> dict:
    base = make_normal_event()
    if random.random() < bad_ratio:
        return make_messy_event(base)
    return base


# --- KINESIS PUSHER LOGIC ---

def main(
    events_per_second: int = 100,
    bad_ratio: float = 0.15,
    stream_name: str = "netflix-events-stream",
    region_name: str = "ap-south-1",
) -> None:
    kinesis = boto3.client("kinesis", region_name=region_name)
    print(f"Starting producer: {events_per_second} eps | Stream: {stream_name}")

    try:
        while True:
            start_time = time.time()
            records_batch = []

            for _ in range(events_per_second):
                event = generate_event(bad_ratio=bad_ratio)

                data_str = json.dumps(event, default=str)
                p_key = str(event.get("customer_ref")) if event.get("customer_ref") else str(fake.uuid4())

                records_batch.append(
                    {
                        "Data": (data_str + "\n").encode("utf-8"),
                        "PartitionKey": p_key,
                    }
                )

            response = kinesis.put_records(
                StreamName=stream_name,
                Records=records_batch,
            )

            failed = response.get("FailedRecordCount", 0)
            if failed > 0:
                print(f"Failed Records: {failed}")

            elapsed = time.time() - start_time
            time.sleep(max(0, 1.0 - elapsed))

    except KeyboardInterrupt:
        print("\nProducer stopped by user.")
    except Exception as e:
        print(f"\nFatal Error: {str(e)}")


if __name__ == "__main__":
    main()
