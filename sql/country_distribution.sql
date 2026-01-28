SELECT country, COUNT(*) AS events
FROM raw_netflix_events_rootevents
GROUP BY country
ORDER BY events DESC;
