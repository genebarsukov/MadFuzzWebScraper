import requests
import random
import config
from MainProcess import MainProcess


class Scanner(MainProcess):
    """
    The scanner class takes care of the main scanning process
    It is responsible for hitting the news site and getting the response
    The response data will be parsed with a separate parser class
    """
    scan_record = None
    error = None
    http_headers = {}

    def __init__(self):
        """
        Constructor
        Scan records can be instantiated here or also passed into the scan method
        :param scan_records: list of dictionaries
        """
        super(Scanner, self).__init__()

    def setScanRecord(self, scan_record):
        self.scan_record = scan_record

    def setHttpHeaders(self, scan_record):
        """
        Set the generic and custom http header values to be used with the request.
        :param scan_record: ScanRecord object containing url
        """
        http_headers = config.settings['http_headers']
        http_headers['Host'] = self.stripHttp(scan_record.base_url)
        http_headers['Referer'] = self.pickReferer()

        self.http_headers = http_headers

    def stripHttp(self, url):
        """
        Stripts the http:// from the beginning and the / from the end of a url
        :param url: full url
        :return: url in the format www.url.com
        """
        stripped = url

        if stripped[:7] == 'http://':       # Remove http
            stripped = stripped[7:]
        elif stripped[:8] == 'https://':    # Remove https
            stripped = stripped[8:]

        if stripped[-1:] == '/':            # Remove end slash
            stripped = stripped[:-1]

        return stripped

    def pickReferer(self):
        """
        Picks one from a list of several defined referrers randomly
        :return: selected referer url
        """
        referers = config.settings['referers']
        rand_index = random.randint(0, len(referers) - 1)

        return referers[rand_index]

    def getPageResponse(self, url):
        """
        [1]
        Hit a url endpoint and return the response
        :param url: The url to hit
        """
        response = requests.get(url, headers=self.http_headers, timeout=config.settings['limits']['request_time_out'])

        self.log('Getting Response ---------------------------------------------------------------------', 'verbose')
        self.log(url, 'verbose')
        self.log(self.http_headers, 'verbose')
        self.log(response, 'verbose')
        self.log(response.text, 'verbose')

        return response.text

    def cleanArticleLinks(self, article_links):
        """
        [3]
        Takes raw link Strings from the parser and modifies them until they are a complete usable link.
        :param article_links: list of unfinished url strings
        :return: list of working url strings
        """
        clean_links = []
        for article_link in article_links:
            if article_link is None:
                continue
            if article_link[0:4] == 'www.':
                clean_links.append('http://' + article_link)
            elif article_link[0:4] == 'http':
                clean_links.append(article_link)
            else:
                clean_links.append(self.scan_record.base_url + article_link)

        return clean_links

    def filterNewLinks(self, clean_links, db_conn):
        """
        Filters out existing story links and returns only new links
        Compares the current links gotten from the main source page with the most recent links in the database
        :param clean_links:
        :return: list(string): new_links
        """
        # Skip de-duping if we want to update stories
        if config.settings['run_options']['update_stories']:
            self.log("Skipping De-duping", 'dev');
            return clean_links

        new_links = []

        stored_links = self.getStoredLinks(self.scan_record.source_id, db_conn)

        for link in clean_links:
            if link[len(link)-1] == '/':
                link = link[:len(link)-1]

            link_ending = link.split('/').pop()
            if link_ending not in stored_links:
                new_links.append(link)
            else:
                self.log('Duplicate link: %s' % link_ending, 'dev')

        return new_links

    def getStoredLinks(self, source_id, db_conn):
        """
        Gets the most recent article links for a specified source
        :param db_conn: SQL db connector
        :param source_id: The source id of the source we want to get links for
        :return: list(string)
        """
        omit_dead_links_clause = ''
        if config.settings['run_options']['retry_dead_links']:
            omit_dead_links_clause = " AND active = 'y' "

        query = ("SELECT url FROM DEF_STORY "
                 "WHERE source_id = %s "
                 "  AND date_created > DATE_SUB(CURRENT_DATE, INTERVAL %s DAY)") + omit_dead_links_clause

        stored_records = db_conn.getResultArray(query, (source_id, config.settings['limits']['stored_links_age']))
        stored_links = [record['url'].split('/').pop() for record in stored_records]

        return stored_links
