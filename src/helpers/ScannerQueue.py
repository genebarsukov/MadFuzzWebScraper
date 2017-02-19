import config


class ScannerQueue(object):
    """
    A class for managing which news sites to scan next
    Currently relies on simple date time ordering, but more complex logic may be implemented in the future based on the
    size of the sire we are scanning, how often we want to scan it, etc.
    """
    db_conn = None

    def __init__(self, db_conn=None):
        """
        Constructor
        A valid SQL connector object must be passed here for the rest of the methods to work
        :param db_conn: DBConnector() object
        """
        self.db_conn = db_conn

    def updateStoryRatings(self):
        """
        Recalculate and update all story ratings based on values existing in the database and other values
        """
        random_ceiling = 50
        rating_divider = 30
        rating_modifier = 300
        rand_mod = (" FLOOR(RAND() * %s - 1 + 1) + 1 ") % random_ceiling

        formula_1 = ("((720 - TIME_TO_SEC(TIMEDIFF(NOW(), date_created ))/3600) "
                     "              + rand_mod)"
                     "              * ((rating + %s) / %s) ") % (rating_modifier, rating_divider)

        formula_2 = ("CEIL((720 - TIME_TO_SEC(TIMEDIFF(NOW(), date_created ))/3600) "
                     "              * ((rating + %s) / %s) "
                     "              + rand_mod)") % (rating_modifier, rating_divider)

        chosen_formula = formula_2

        query = ("UPDATE DEF_STORY "
                 "SET rand_mod = %s, "
                 "rating = CEIL(100 * (up_votes / IF((up_votes + down_votes)=0, 1, up_votes + down_votes))), "
                 "position = %s") % (rand_mod, chosen_formula)

        self.db_conn.query(query)

    def resetYesterdaysScanRecords(self):
        """
        Reset the scanned_today_count to 0 for records that have not been scanned today yet
        """
        query = ("UPDATE SCAN_QUEUE "
                 "SET scanned_today_count = 0 "
                 "WHERE DATE(last_scanned) < DATE(NOW())");

        self.db_conn.query(query)

    def getRecordsToScan(self, source_id=None):
        """
        Goes to our QUEUE table and gets records that have not been scanned in a while. Older records are given priority
        Currently the time elapsed since last_scanned is the only determiner of what will be scanned next
        Crude for now
        :type source_id: integer: Optional source id to be specified in the where clause
        :return:
        """
        # Reset yesterday's record counts to 0 each time before we get new records
        self.resetYesterdaysScanRecords();

        where_clause = ''
        if source_id is not None:
            where_clause = " AND source_id = %s" % source_id
        else:
            where_clause = " AND scanned_today_count < daily_scan_frequency "

        query = ("SELECT scan_record_id, "
                 "       source_id, "
                 "       daily_scan_frequency,"
                 "       scanned_today_count, "
                 "       last_scan_result, "
                 "       last_scanned, "
                 "       base_url, "
                 "       home_url, "
                 "       name,"
                 "       active, "
                 "       main_page_container.type as main_page_container_type,"
                 "       main_page_container.class as main_page_container_class,"
                 "       main_page_container.element_id as main_page_container_element_id,"
                 "       main_page_container.data_attribute_name as main_page_container_data_attribute_name,"
                 "       main_page_container.extra_attribute_1_name as main_page_container_extra_attribute_1_name,"
                 "       main_page_container.extra_attribute_1_value as main_page_container_extra_attribute_1_value,"
                 "       main_page_container.extra_attribute_2_name as main_page_container_extra_attribute_2_name,"
                 "       main_page_container.extra_attribute_2_value as main_page_container_extra_attribute_2_value,"
                 "       first_headline_container.type as first_headline_container_type,"
                 "       first_headline_container.class as first_headline_container_class,"
                 "       first_headline_container.element_id as first_headline_container_element_id,"
                 "       first_headline_container.data_attribute_name as first_headline_container_data_attribute_name,"
                 "       first_headline_container.extra_attribute_1_name as first_headline_container_extra_attribute_1_name,"
                 "       first_headline_container.extra_attribute_1_value as first_headline_container_extra_attribute_1_value,"
                 "       first_headline_container.extra_attribute_2_name as first_headline_container_extra_attribute_2_name,"
                 "       first_headline_container.extra_attribute_2_value as first_headline_container_extra_attribute_2_value,"
                 "       first_headline.type as first_headline_type,"
                 "       first_headline.class as first_headline_class,"
                 "       first_headline.element_id as first_headline_element_id,"
                 "       first_headline.data_attribute_name as first_headline_data_attribute_name,"
                 "       first_headline.extra_attribute_1_name as first_headline_extra_attribute_1_name,"
                 "       first_headline.extra_attribute_1_value as first_headline_extra_attribute_1_value,"
                 "       first_headline.extra_attribute_2_name as first_headline_extra_attribute_2_name,"
                 "       first_headline.extra_attribute_2_value as first_headline_extra_attribute_2_value,"
                 "       headline_container.type as headline_container_type,"
                 "       headline_container.class as headline_container_class,"
                 "       headline_container.element_id as headline_container_element_id,"
                 "       headline_container.data_attribute_name as headline_container_data_attribute_name,"
                 "       headline_container.extra_attribute_1_name as headline_container_extra_attribute_1_name,"
                 "       headline_container.extra_attribute_1_value as headline_container_extra_attribute_1_value,"
                 "       headline_container.extra_attribute_2_name as headline_container_extra_attribute_2_name,"
                 "       headline_container.extra_attribute_2_value as headline_container_extra_attribute_2_value,"
                 "       headline.type as headline_type,"
                 "       headline.class as headline_class,"
                 "       headline.element_id as headline_element_id,"
                 "       headline.data_attribute_name as headline_data_attribute_name,"
                 "       headline.extra_attribute_1_name as headline_extra_attribute_1_name,"
                 "       headline.extra_attribute_1_value as headline_extra_attribute_1_value,"
                 "       headline.extra_attribute_2_name as headline_extra_attribute_2_name,"
                 "       headline.extra_attribute_2_value as headline_extra_attribute_2_value,"
                 "       article_page_container.type as article_page_container_type,"
                 "       article_page_container.class as article_page_container_class,"
                 "       article_page_container.element_id as article_page_container_element_id,"
                 "       article_page_container.data_attribute_name as article_page_container_data_attribute_name,"
                 "       article_page_container.extra_attribute_1_name as article_page_container_extra_attribute_1_name,"
                 "       article_page_container.extra_attribute_1_value as article_page_container_extra_attribute_1_value,"
                 "       article_page_container.extra_attribute_2_name as article_page_container_extra_attribute_2_name,"
                 "       article_page_container.extra_attribute_2_value as article_page_container_extra_attribute_2_value,"
                 "       article_title_container.type as article_title_container_type,"
                 "       article_title_container.class as article_title_container_class,"
                 "       article_title_container.element_id as article_title_container_element_id,"
                 "       article_title_container.data_attribute_name as article_title_container_data_attribute_name,"
                 "       article_title_container.extra_attribute_1_name as article_title_container_extra_attribute_1_name,"
                 "       article_title_container.extra_attribute_1_value as article_title_container_extra_attribute_1_value,"
                 "       article_title_container.extra_attribute_2_name as article_title_container_extra_attribute_2_name,"
                 "       article_title_container.extra_attribute_2_value as article_title_container_extra_attribute_2_value,"
                 "       article_title.type as article_title_type,"
                 "       article_title.class as article_title_class,"
                 "       article_title.element_id as article_title_element_id,"
                 "       article_title.data_attribute_name as article_title_data_attribute_name,"
                 "       article_title.extra_attribute_1_name as article_title_extra_attribute_1_name,"
                 "       article_title.extra_attribute_1_value as article_title_extra_attribute_1_value,"
                 "       article_title.extra_attribute_2_name as article_title_extra_attribute_2_name,"
                 "       article_title.extra_attribute_2_value as article_title_extra_attribute_2_value,"
                 "       article_author_container.type as article_author_container_type,"
                 "       article_author_container.class as article_author_container_class,"
                 "       article_author_container.element_id as article_author_container_element_id,"
                 "       article_author_container.data_attribute_name as article_author_container_data_attribute_name,"
                 "       article_author_container.extra_attribute_1_name as article_author_container_extra_attribute_1_name,"
                 "       article_author_container.extra_attribute_1_value as article_author_container_extra_attribute_1_value,"
                 "       article_author_container.extra_attribute_2_name as article_author_container_extra_attribute_2_name,"
                 "       article_author_container.extra_attribute_2_value as article_author_container_extra_attribute_2_value,"
                 "       article_author.type as article_author_type,"
                 "       article_author.class as article_author_class,"
                 "       article_author.element_id as article_author_element_id,"
                 "       article_author.data_attribute_name as article_author_data_attribute_name,"
                 "       article_author.extra_attribute_1_name as article_author_extra_attribute_1_name,"
                 "       article_author.extra_attribute_1_value as article_author_extra_attribute_1_value,"
                 "       article_author.extra_attribute_2_name as article_author_extra_attribute_2_name,"
                 "       article_author.extra_attribute_2_value as article_author_extra_attribute_2_value,"
                 "       article_body_container.type as article_body_container_type,"
                 "       article_body_container.class as article_body_container_class,"
                 "       article_body_container.element_id as article_body_container_element_id,"
                 "       article_body_container.data_attribute_name as article_body_container_data_attribute_name,"
                 "       article_body_container.extra_attribute_1_name as article_body_container_extra_attribute_1_name,"
                 "       article_body_container.extra_attribute_1_value as article_body_container_extra_attribute_1_value,"
                 "       article_body_container.extra_attribute_2_name as article_body_container_extra_attribute_2_name,"
                 "       article_body_container.extra_attribute_2_value as article_body_container_extra_attribute_2_value,"
                 "       article_body.type as article_body_type,"
                 "       article_body.class as article_body_class,"
                 "       article_body.element_id as article_body_element_id,"
                 "       article_body.data_attribute_name as article_body_data_attribute_name,"
                 "       article_body.extra_attribute_1_name as article_body_extra_attribute_1_name,"
                 "       article_body.extra_attribute_1_value as article_body_extra_attribute_1_value,"
                 "       article_body.extra_attribute_2_name as article_body_extra_attribute_2_name,"
                 "       article_body.extra_attribute_2_value as article_body_extra_attribute_2_value"
                 "           FROM SCAN_QUEUE"
                 "           LEFT JOIN DEF_SOURCE USING(source_id)"
                 "           LEFT JOIN PARSING_TAGS tags USING(source_id)"
                 "           LEFT JOIN DEF_PARSING_TAG main_page_container ON(tags.main_page_container_id = main_page_container.parsing_tag_id)"
                 "           LEFT JOIN DEF_PARSING_TAG first_headline_container ON(tags.first_headline_container_id = first_headline_container.parsing_tag_id)"
                 "           LEFT JOIN DEF_PARSING_TAG first_headline ON(tags.first_headline_id = first_headline.parsing_tag_id)"
                 "           LEFT JOIN DEF_PARSING_TAG headline_container ON(tags.headline_container_id = headline_container.parsing_tag_id)"
                 "           LEFT JOIN DEF_PARSING_TAG headline ON(tags.headline_id = headline.parsing_tag_id)"
                 "           LEFT JOIN DEF_PARSING_TAG article_page_container ON(tags.article_page_container_id = article_page_container.parsing_tag_id)"
                 "           LEFT JOIN DEF_PARSING_TAG article_title_container ON(tags.article_title_container_id = article_title_container.parsing_tag_id)"
                 "           LEFT JOIN DEF_PARSING_TAG article_title ON(tags.article_title_id = article_title.parsing_tag_id)"
                 "           LEFT JOIN DEF_PARSING_TAG article_author_container ON(tags.article_author_container_id = article_author_container.parsing_tag_id)"
                 "           LEFT JOIN DEF_PARSING_TAG article_author ON(tags.article_author_id = article_author.parsing_tag_id)"
                 "           LEFT JOIN DEF_PARSING_TAG article_body_container ON(tags.article_body_container_id = article_body_container.parsing_tag_id)"
                 "           LEFT JOIN DEF_PARSING_TAG article_body ON(tags.article_body_id = article_body.parsing_tag_id)"
                 "       WHERE active = 'Y'"
                 "         %s "
                 "       ORDER BY last_scanned ASC"
                 "       LIMIT %s") % (where_clause, config.settings['limits']['scan_record_limit'])

        records = self.db_conn.getResultArray(query)

        return records
