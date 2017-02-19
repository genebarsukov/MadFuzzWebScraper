import time


class ScanRecord(object):
    """
    A simple object used to store parameter originally retrieved from the queue.
    It also holds all of the important logging and status params for that record
    Contains data needed to update:
        SCAN_QUEUE,
        SCAN_LOG
    :param scan_record_dict: a dictionary record gotten from a SQL table
    """
    name = None
    base_url = None
    home_url = None
    scan_record_id = None
    source_id = None
    daily_scan_frequency = 3
    scanned_today_count = None
    last_scan_result = 'unknown'
    last_scanned = '00-00-00 00:00:00'

    stories_found = 0
    new_stories = 0
    dead_links = 0
    scan_time_ms = 0
    errors = ''

    start_time = 0

    def __init__(self, **scan_record_dict):
        """
        Constructor: Initiates class properties with all the key - value pairs passed in from the scan record
        :param scan_record_dict: a dictionary record gotten from a SQL table
        """
        self.__dict__.update(scan_record_dict)
        self.start_time = time.time()

    def finalizeStats(self):
        """
        Calculates the final values of all the stats this object was keeping track of, including time elapsed scanning
        it and the amount of stories found
        """

        self.scanned_today_count += 1
        if self.stories_found > 0 and self.errors == '':       # found stories with no errors
            self.last_scan_result = 'success'
        elif self.stories_found > 0 and len(self.errors) > 0:  # found stories but error-ed out
            self.last_scan_result = 'unknown'
        else:
            self.last_scan_result = 'error'

        self.scan_time_ms = (time.time() - self.start_time) * 1000

    def updateDBRecords(self, db_conn):
        """
        Updates records in SCAN_QUEUE and SCAN_LOG with the updated stats saved in this object
        :param db_conn: SQL Connector object
        """
        # Insert a record into SCAN_LOG
        query = ("INSERT INTO SCAN_LOG"
                 "   SET scan_record_id = %s,"
                 "       stories_found = %s,"
                 "       new_stories = %s, "
                 "       dead_links = %s, "
                 "       scan_time_ms = %s,"
                 "       errors = %s,"
                 "       last_logged = NOW()")
        params = (self.scan_record_id,
                  self.stories_found,
                  self.new_stories,
                  self.dead_links,
                  self.scan_time_ms,
                  self.errors)

        db_conn.query(query, params)

        # Update the SCAN_QUEUE record
        query = ("UPDATE SCAN_QUEUE"
                 "   SET scanned_today_count = scanned_today_count + 1,"
                 "       last_scan_result = %s,"
                 "       last_scanned = NOW()"
                 "   WHERE scan_record_id = %s")
        params = (self.last_scan_result,
                  self.scan_record_id)

        db_conn.query(query, params)
