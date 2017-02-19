import traceback
import time
from helpers.ScannerQueue import ScannerQueue
from main_process.Parser import Parser
from main_process.Scanner import Scanner
from models.ScanRecord import ScanRecord
from MainProcess import MainProcess
import config


class ScanMasterFlex(MainProcess):
    """
    Acts as a mediator to manage scanning and parsing
    We need to use the Scanner and the Parser classes at different times during the scanning process
    The process is not liner, so the interactions between the Scanner and the Parser get confusing if they constantly
    act on each other at different times
    We can simplify this by using a mediator which will have a well defined set of directives for what needs to happen
    during the scanning process.
    The Scan Master will then call on the Scanner or the Parser to accomplish each task. THis clarifies the process
    """
    db_conn = None
    scan_records = []
    stories = []
    scanner = None
    parser = None
    scan_queue = None

    def __init__(self, db_conn):
        """
        Constructor
            Sets the sql database connector object
            Get scan records from the queue and convert them into objects
            Instantiate the scanner and parser
        :param db_conn: DBConnector object
        """
        super(ScanMasterFlex, self).__init__()

        self.db_conn = db_conn
        self.scanner = Scanner()
        self.parser = Parser()
        self.scan_queue = ScannerQueue(self.db_conn)

    def scan(self, source_id=None):
        """
        Main scanning method - this is where it all begins
        Scans all the multiple sites retrieved from the scanning queue
            Scan each record
            Save the stories found
            Update the queue record in the db
            Create a new logging record with this run's stats
        """
        # get records to scan
        self.getRecordsToScan(source_id)
        start_secs = time.time()

        if len(self.scan_records) == 0:
            self.log("No records found to scan", 'live')

        for scan_record in self.scan_records:
            self.log("Scanning %s" % scan_record.name, 'dev')
            try:
                self.scanRecord(scan_record)
            except Exception as e:
                scan_record.errors += ('>>' + str(e))
                traceback.print_exc()
            finally:
                self.log("----------------------------------------------------------------------------------", 'dev')
                self.log("Saving Stories -------------------------------------------------------------------", 'dev')
                self.saveStories()                                               # 6 - Save the data for all stories   #
                self.log("Updating ratings", 'dev')
                self.scan_queue.updateStoryRatings()
                scan_record.finalizeStats()                                      # 7 - Log the result in the database  #
                scan_record.updateDBRecords(self.db_conn)                        #######################################

                if scan_record.errors:
                    self.log("Scan Record Finished with Errors", 'live')
                else:
                    self.log("Scan Record Finished Successfully", 'live')

        # Keep the MySQL connection open until done scanning
        self.db_conn.disconnect()
        self.updateRunLog(start_secs)

        self.log("Process Finished", 'live')

    def getRecordsToScan(self, source_id=None):
        """
        Get records to scan
        If a source id is passed, only get records with that source id
        Otherwise get all scannable records
        :param source_id: Optional source id specifies which individual record we want to scan
        """
        # Get some records to scan
        scan_record_dicts = self.scan_queue.getRecordsToScan(source_id)

        # Convert database scan records into objects
        for scan_record_dict in scan_record_dicts:
            scan_record = ScanRecord(**scan_record_dict)
            self.scan_records.append(scan_record)

    def scanRecord(self, scan_record):
        """
        Scans each individual news sire record, saves its data, and logs the result
        :param scan_record:
        :return:
        """
        # clear stories array before running each source
        self.stories = []

        self.log("Scanning %s %s" % (scan_record.name, scan_record.home_url), 'live')
        self.scanner.setScanRecord(scan_record)
        self.scanner.setHttpHeaders(scan_record)
        self.parser.setScanRecord(scan_record)
        self.scanner.setLogLevel(self.log_level)
        self.parser.setLogLevel(self.log_level)
                                                                                 #######################################
        main_page_response = self.scanner.getPageResponse(scan_record.home_url)       # 1 - Get main page                   #
        headline_links = self.parser.parseMainPage(main_page_response)           # 2 - Get main page links             #
        clean_links = self.scanner.cleanArticleLinks(headline_links)             # 3 - Clean the links                 #
        new_links = self.scanner.filterNewLinks(clean_links, self.db_conn)       #                                     #
        scan_record.stories_found = len(clean_links)                             #                                     #
        scan_record.new_stories = len(new_links)                                 #                                     #
                                                                                 #                                     #
        if config.settings['run_options']['short_run']:
            new_links = new_links[:config.settings['run_options']['short_run_link_limit']]

        for link in new_links:                                                   # for each story link:                #
            self.log('\nProcessing Link ---------------------------------------------------------------------', 'dev')
            self.log(link, 'live')                                               #                                     #
            self.log('---------------------------------------------------------------------------------------', 'dev')
            try:                                                                 #                                     #
                article_response = self.scanner.getPageResponse(link)            #     4 - Get the article page        #
                story = self.parser.parseArticlePage(article_response)           #     5 - Get the story data          #
                story.url = link                                                 #######################################
                story.escapeValues(self.db_conn)
                self.stories.append(story)

                if not story.active:
                    scan_record.dead_links += 1

            except Exception as e:
                scan_record.errors += (' >> ' + str(e))
                traceback.print_exc()

            time.sleep(config.settings['limits']['wait_between_articles'])

    def saveStories(self):
        """
        [6]
        Save the stories retrieved after each individual scan record (news site) has beein parsed
        """
        if len(self.stories) == 0:
            return
        self.log('Attempting to save %s stories' % str(len(self.stories)), 'dev')
        insert_values_list = []
        # make an array of value inserts so we can insert all out stories in one query
        for story in self.stories:
            if not story.active:
                self.log('Dead Link: %s' % story.url, 'dev')

            insert_values = (story.url, story.title, story.author, story.snippet, story.source_id, story.active)
            insert_values_list.append(insert_values)
        # if we are retrying dead links, we are gonna check to see if our story is already in the db and update it
        if config.settings['run_options']['retry_dead_links'] or config.settings['run_options']['update_stories']:

            self.log('Attempting to update stories', 'dev')
            for story in self.stories:
                # first look for an existing link record to update
                query = ("SELECT * FROM DEF_STORY WHERE source_id = %s AND url = %s")
                result = self.db_conn.getResultRow(query, (story.source_id, story.url))

                self.log('Result: -----------------------------------------------------------------------------', 'dev')
                self.log(result, 'dev')

                # if we cannot find an existing one, just insert this one
                if len(result) == 0:
                    query = ("INSERT INTO DEF_STORY (url, title, author, snippet, source_id, active, date_created) "
                             " VALUES (%s, %s, %s, %s, %s, %s, NOW())")
                    insert_values = (story.url, story.title, story.author, story.snippet, story.source_id, story.active)

                    self.log('Inserting', 'dev')
                    self.db_conn.query(query, insert_values)

                # otherwise update the record
                else:
                    query = ("UPDATE DEF_STORY SET title = %s, "
                             "                     author = %s, "
                             "                     snippet = %s, "
                             "                     active = %s "
                             "WHERE source_id = %s "
                             "AND url = %s ")
                    update_values = (story.title, story.author, story.snippet, story.active, story.source_id, story.url)

                    self.log('Updating', 'dev')
                    self.db_conn.query(query, update_values)

        # otherwise just insert stuff as new values
        else:
            self.log('Inserting new stories', 'dev')

            query = ("INSERT INTO DEF_STORY (url, title, author, snippet, source_id, active, date_created) "
                     " VALUES (%s, %s, %s, %s, %s, %s, NOW())")

            self.db_conn.queryMany(query, insert_values_list)

    def updateRunLog(self, start_secs):
        """
        Update the RUN_LOG db
        :param start_secs: time in seconds when the scan started
        """
        records_scanned = len(self.scan_records)
        records = ','.join(str(scan_record.scan_record_id) for scan_record in self.scan_records)
        run_time_sec = time.time() - start_secs

        query = ("INSERT INTO RUN_LOG "
                 "SET records_scanned = %s,"
                 "    records = %s,"
                 "    run_time_sec = %s")

        self.db_conn.query(query, (records_scanned, records, run_time_sec))


