1.Scraping bundesfinanzministerium.de
For scraping "https://www.bundesfinanzministerium.de/" run "python bfm_scraper.py". All the date will be in bundesfinanzministerium.db file.

2.Scraping records to JSON file
There is a column in the database "extract_to_json"(True/False(1/0)). Please mark the entries which you want to extract with "1" and run "python bfm_scraper_to_json.py".

All the data from archive.org is in wayback_bundesfinanzministerium.db