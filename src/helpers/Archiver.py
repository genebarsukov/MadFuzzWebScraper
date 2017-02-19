import config
from main_process.MainProcess import MainProcess


class Archiver(MainProcess):
    """
    Archives old records to speed up db tables
    Moves old records to archive tables
    """
    db_conn = None

    def __init__(self, db_conn):
        """
        Constructor
        Init db connection
        """
        super(Archiver, self).__init__()

        self.db_conn = db_conn

    def archive(self):
        """
        Run the main archiving process
        """
        self.log('Archiving...', 'live')
        self.archiveStories()
        self.log('Archiving Complete', 'live')

    def archiveStories(self):
        """
        Archive old stories
        Archive DEF_STORY
        Archive LKP_USER_STORY
        """
        self.log('Archiving Stories', 'live')
        interval_num = config.settings['archive']['stories']['interval_num']
        interval_type = config.settings['archive']['stories']['interval_type']

        # Get records to archive from DEF_STORY
        query = ("SELECT * FROM DEF_STORY "
                 "WHERE date_updated < DATE_SUB(CURDATE(), INTERVAL %s %s)") % (interval_num, interval_type)
        stories_to_archive = self.db_conn.getResultArray(query)
        records_found = len(stories_to_archive)

        story_id_string = "','".join(str(story['story_id']) for story in stories_to_archive)

        # Archive DEF_STORY
        query = ("INSERT IGNORE INTO ARCHIVE_DEF_STORY "
                 "SELECT * FROM DEF_STORY "
                 "WHERE date_updated < DATE_SUB(CURDATE(), INTERVAL %s %s)") % (interval_num, interval_type)
        result = self.db_conn.query(query)
        records_archived = self.db_conn.last_row_count
        records_deleted = 0

        # Delete the old records from DEF_STORY
        if result:
            query = ("DELETE FROM DEF_STORY "
                     "WHERE date_updated < DATE_SUB(CURDATE(), INTERVAL %s %s)") % (interval_num, interval_type)
            self.db_conn.query(query)
            records_deleted = self.db_conn.last_row_count

        # Log the Archiving result
        self.logArchivedTable('DEF_STORY', records_found, records_archived, records_deleted)

        # Get potential record count from LKP_USER_STORY
        query = ("SELECT * FROM LKP_USER_STORY "
                 "WHERE story_id IN('%s')") % story_id_string
        lkp_stories = self.db_conn.getResultArray(query)
        records_found = len(lkp_stories)

        # Archive LKP_USER_STORY
        query = ("INSERT IGNORE INTO ARCHIVE_LKP_USER_STORY "
                 "SELECT * FROM LKP_USER_STORY "
                 "WHERE story_id IN('%s')") % story_id_string
        result = self.db_conn.query(query)
        records_archived = self.db_conn.last_row_count
        records_deleted = 0

        if result:
            query = ("DELETE FROM LKP_USER_STORY "
                     "WHERE story_id IN('%s')") % story_id_string
            self.db_conn.query(query)
            records_deleted = self.db_conn.last_row_count

        # Log the Archiving result
        self.logArchivedTable('LKP_USER_STORY', records_found, records_archived, records_deleted)

    def logArchivedTable(self, table_name, records_found, records_archived, records_deleted):
        """
        Log the Archiving result
        :param table_name: Origin table name
        :param records_found: How many old records we found
        :param records_archived: How many wea actually archived into the archive table
        :param records_deleted: How many we deleted from the old table
        """
        query = ("INSERT INTO ARCHIVE_LOG "
                 "SET table_name = %s, "
                 "    records_found = %s, "
                 "    records_archived = %s, "
                 "    records_deleted =  %s ")

        self.db_conn.query(query, (table_name, records_found, records_archived, records_deleted))

        self.log('Archived %s: Found: %s, Archived: %s, Deleted: %s' %
                 (table_name, records_found, records_archived, records_deleted), 'live')