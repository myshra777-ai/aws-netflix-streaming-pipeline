# Streaming Event Data Model

## Event fields

from datetime import datetime, timedelta, timezone
...
now = datetime.now(timezone.utc)


| field_name        | type      | example                          | description |
|-------------------|-----------|----------------------------------|-------------|
| event_id          | string    | "550e8400-e29b-41d4-a716-..."    | Unique id of the event |
| event_type        | string    | "play"                           | Type of action: play, pause, seek, stop, search |
| event_timestamp   | timestamp | "2026-01-26T05:35:10Z"           | When the event happened (UTC) |
| user_id           | string    | "user_12"                        | Logical user account id |
| profile_id        | string    | "profile_34"                     | Individual profile under a user |
| title_id          | string    | "title_7"                        | Movie/series identifier |
| device_type       | string    | "mobile"                         | Device used: mobile, tv, web |
| country           | string    | "IN"                             | ISO country code |
| position_seconds  | int       | 1234                             | Playback position in seconds (player events only) |
| duration_seconds  | int       | 180                              | Duration of playback/seek in seconds (play/seek only) |
| search_query      | string    | "action movies"                  | Search text (search events only) |

## Notes

- `position_seconds` present for: play, pause, seek, stop.  
- `duration_seconds` present for: play, seek.  
- `search_query` present only for: search.
