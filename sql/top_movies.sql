SELECT title_id, COUNT(*) AS views
FROM raw_netflix_events_rootevents
WHERE event_type = 'PLAY_START'
GROUP BY title_id
ORDER BY views DESC
LIMIT 10;
