# MadFuzzWebScraper
## Web Scraper that gets data for the Mad Fuzz web app

This is a demo. it will not run without a missing config file.

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
Run arguments:

* -h, --help            show this help message and exit
* -s SOURCE_ID, --source_id SOURCE_ID Source id to scan
* -l LOG_LEVEL, --log_level LOG_LEVEL Log verboseness level
* -a, --archive         Archive old records
*  -t, --transform       Transform story snippets
*  -r, --update_ratings  Update story ratings
