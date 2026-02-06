import json
import random
import time
from datetime import datetime, timezone

from faker import Faker

fake = Faker()


def make_normal_event() -> dict:
    """Generate a 'clean' transaction-like event."""
    now = datetime.now(timezone.utc)
    return {
        "txn_id": fake.uuid4(),
        "timestamp": now.isoformat(),
        "customer_ref": fake.uuid4(),  # or fake.email() if you prefer
        "ip_address": fake.ipv4_public(),
        "status_code": random.choice([200, 201]),
        "payload_size": random.randint(1_000, 500_000),  # bytes
        "browser_info": fake.user_agent(),
        "error_msg": None,
        "region_code": random.choice(["us-east-1", "ap-south-1", "eu-west-1"]),
        "retry_count": 0,
        "is_flagged": False,
        "junk_metadata": {
            "session_id": fake.uuid4(),
            "experiment_group": random.choice(["A", "B", "control"]),
        },
    }


def make_messy_event(base: dict) -> dict:
    """
    Take a 'normal' event and randomly corrupt some fields.
    10–20% records total honge messy, but har messy record ka pattern alag ho sakta hai.
    """
    event = dict(base)  # shallow copy

    # List of corruption functions
    corruptions = [
        corrupt_txn_id,
        corrupt_timestamp,
        corrupt_customer_ref,
        corrupt_ip_address,
        corrupt_status_code,
        corrupt_payload_size,
        corrupt_browser_info,
        corrupt_error_msg,
        corrupt_region_code,
        corrupt_retry_count,
        corrupt_is_flagged,
        corrupt_junk_metadata,
        maybe_insert_html_garbage_in_error,
    ]

    # Randomly pick 1–3 corruptions for this event
    for func in random.sample(corruptions, k=random.randint(1, 3)):
        func(event)

    return event


def corrupt_txn_id(event: dict) -> None:
    # Kahin UUID, kahin simple int, kahin duplicate ka risk
    event["txn_id"] = random.choice([
        fake.uuid4(),
        random.randint(1, 10_000),
        None,
    ])


def corrupt_timestamp(event: dict) -> None:
    now = datetime.now()
    choices = [
        now.strftime("%Y-%m-%d %H:%M:%S"),  # normal-ish
        now.strftime("%d/%m/%Y"),          # DD/MM/YYYY
        int(now.timestamp()),              # epoch int
        "not-a-timestamp",
        "",                                # empty
    ]
    event["timestamp"] = random.choice(choices)


def corrupt_customer_ref(event: dict) -> None:
    event["customer_ref"] = random.choice([
        fake.email(),
        fake.user_name(),
        None,
        "",
    ])


def corrupt_ip_address(event: dict) -> None:
    event["ip_address"] = random.choice([
        fake.ipv4(),
        fake.ipv6(),
        "127.0.0.1",
        "not-an-ip",
        "",
    ])


def corrupt_status_code(event: dict) -> None:
    event["status_code"] = random.choice([
        200,
        404,
        500,
        "Success",
        "Phatt Gaya",
        None,
    ])


def corrupt_payload_size(event: dict) -> None:
    event["payload_size"] = random.choice([
        f"{random.randint(1, 1000)}KB",
        f"{random.randint(1, 100)}MB",
        random.randint(1, 1_000_000),
        "unknown",
        None,
    ])


def corrupt_browser_info(event: dict) -> None:
    ua = fake.user_agent()
    event["browser_info"] = random.choice([
        ua,
        ua + "   " + fake.word(),
        ua.replace("/", "//"),
        "",
    ])


def corrupt_error_msg(event: dict) -> None:
    event["error_msg"] = random.choice([
        None,
        "Backend Timeout",
        "SQL Syntax Error",
        "???",
        "",
    ])


def corrupt_region_code(event: dict) -> None:
    event["region_code"] = random.choice([
        "US-East",
        "india",
        "ap-south-1",
        "eu-west-1",
        "unknown-region",
        "",
    ])


def corrupt_retry_count(event: dict) -> None:
    event["retry_count"] = random.choice([
        0,
        1,
        2,
        "First Attempt",
        "Second",
        "N/A",
        None,
    ])


def corrupt_is_flagged(event: dict) -> None:
    event["is_flagged"] = random.choice([
        True,
        False,
        0,
        1,
        "Y",
        "N",
        "maybe",
    ])


def corrupt_junk_metadata(event: dict) -> None:
    # Har row mein different keys / shapes
    patterns = [
        {"random_key": fake.word(), "value": fake.sentence()},
        {"nested": {"a": fake.word(), "b": fake.word()}},
        {"tags": [fake.word() for _ in range(3)]},
        {},
    ]
    event["junk_metadata"] = random.choice(patterns)


def maybe_insert_html_garbage_in_error(event: dict) -> None:
    # ~5% case: error_msg mein poora HTML / junk
    if random.random() < 0.05:
        event["error_msg"] = "<html><body><h1>500 Internal Error</h1></body></html>"


def generate_event(bad_ratio: float = 0.15) -> dict:
    """
    bad_ratio: fraction of events jisme messy/corrupted data daalna hai.
    e.g. 0.15 = 15% messy events.
    """
    base = make_normal_event()
    if random.random() < bad_ratio:
        return make_messy_event(base)
    return base


def main(events_per_second: int = 100, bad_ratio: float = 0.15) -> None:
    """
    Simple stdout producer:
    - Har second ~events_per_second events print karta hai as JSON lines.
    - Bad events ka ratio bad_ratio hai.
    """
    print(f"Starting Faker producer: {events_per_second} events/sec, bad_ratio={bad_ratio}")
    try:
        while True:
            start = time.time()
            for _ in range(events_per_second):
                event = generate_event(bad_ratio=bad_ratio)
                print(json.dumps(event, default=str))
            elapsed = time.time() - start
            sleep_for = max(0.0, 1.0 - elapsed)
            time.sleep(sleep_for)
    except KeyboardInterrupt:
        print("Stopped Faker producer.")


if __name__ == "__main__":
    main()
