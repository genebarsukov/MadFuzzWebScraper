# MadFuzzWebScraper
## Web Scraper that gets data for the Mad Fuzz web app

This is a demo. it will not run without a missing config file.

Running the process
```
python run_process.py

optional arguments:
-h, --help            show this help message and exit
-s SOURCE_ID, --source_id SOURCE_ID Source id to scan
-l LOG_LEVEL, --log_level LOG_LEVEL Log verboseness level
-a, --archive         Archive old records
-t, --transform       Transform story snippets
-r, --update_ratings  Update story ratings
```

### This project scrapes some news story data from a variaety of sources

The basic premise is to be able to scrape a bunch of different sources simply by entering some parameters into a console. This process relies on some or all of the following prameters to get the data:

* main_page_container	
* first_headline_container	
* first_headline	
* headline_container	
* article_page_container	
* article
* marticle_title_container	
* article_title	
* article_author_container	
* article_body_container	
* article_body

This project is coupled with a web console where the user can create a new source and enter these parameters

![ScreenShot](https://github.com/genebarsukov/MadFuzzWebScraper/blob/develop/madfuzz_console_example.png)

Project workflow:
 1. ScannerQueue gets records to scan from a database
 2. ScanMasterFlex mediator controls the scanning and parsing
 3. Mediator uses Scanner to hit the main page and get the response
4. Article links are parserd with the Parser
5. Scanner filters out links that were prrciously scanned
6. Scanner hits each article links and gets the response
7. Parser parses article data with Beautiful Soup and creates Story objects
8. Story objects are stored in the database


