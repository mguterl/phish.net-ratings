# Phish Show Ratings

[Git scraping](https://simonwillison.net/2020/Oct/9/git-scraping/) for [Phish.net](https://phish.net) show ratings.

The scraper reads the embedded `PhishNet.State.top_rated_shows_data` JSON on
each year's ratings page. Missing or invalid data, empty results for a previously
populated year, and a completely empty scrape fail the run before CSV export.
Explicit empty years are allowed when there is no existing data for that year.
Hiatus years (2001 and 2005–2008) may also return empty results; their archived
private-show CSVs are preserved because the current page excludes those shows.

Run `make check` to lint, typecheck, and test. The `Scrape Ratings` workflow runs
hourly and can also be triggered manually. GitHub may disable its schedule after
60 days of repository inactivity; re-enable it on the workflow's Actions page
and trigger a manual run to verify recovery.
