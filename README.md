# MadFuzzWebScraper
## Web Scraper that gets data for the Mad Fuzz web app

This is a demo. it will not run without a missing config file.

### This project scrapes some news story data from a variaety of sources

The basic premise is to be able to scrape a bunch of different sources simply by entering some parameters into a console.
The process uses a few simple classes for every source.
We handle different sources by specifying different page parameters in a database that the process uses to scrape the pages. 
This process relies on some or all of the following prameters to get the data:

 1. For scraping the main page:
* Main page container:      __all content wrapper__
* First headline container:	link wrapper
* First headline:           link data
* Headline container: link wrapper
* Headline: link data
 2. For parsing each article page
* Article page container	: all content wrapper
* Article title container: title wrapper
* Article title: title data
* Article author container: author wrapper
* Article author: author data
* Article body container: text snippet wrapper
* Article body: text snippet

This project is coupled with a web console (sold separately) where the user can create a new source and enter these parameters quickly and easily.
The user can then run the new scraper they created from the console and view the log to see if he was able to get data

![ScreenShot](https://github.com/genebarsukov/MadFuzzWebScraper/blob/develop/madfuzz_console_example.png)

### Running the process:
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

### Project workflow:
 1. ScannerQueue gets records to scan from a database
 2. ScanMasterFlex mediator controls the scanning and parsing
 3. Mediator uses Scanner to hit the main page and get the response
 4. Article links are parserd with the Parser
 5. Scanner filters out links that were prrciously scanned
 6. Scanner hits each article links and gets the response
 7. Parser parses article data with Beautiful Soup and creates Story objects
 8. Story objects are stored in the database


