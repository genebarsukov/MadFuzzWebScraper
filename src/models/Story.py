

class Story(object):
    """
    A simple object to hold the parsed story parameters
    The variables that are initialized are done so to match the default database values
    """
    story_id = None
    url = ''
    title = ''
    author = ''
    body = ''
    snippet = ''
    source_id = None
    active = False
    position = 0
    rating = 100
    up_votes = 0
    down_votes = 0

    def __init__(self):
        """
        Constructor
        """
        pass


    def escapeValues(self, db_conn):
        """
        Escape all of the story's values before inserting into a database
        """
        # Enforce integers
        if self.story_id is not None:
            self.story_id = int(self.story_id)
        if self.source_id is not None:
            self.source_id = int(self.source_id)
        if self.position is not None:
            self.position = int(self.position)
        if self.rating is not None:
            self.rating = int(self.rating)
        if self.up_votes is not None:
            self.up_votes = int(self.up_votes)
        if self.down_votes is not None:
            self.down_votes = int(self.down_votes)

        # Escape strings
        if self.url is not None:
            self.url = db_conn.escape(self.url)
        if self.title is not None:
            self.title = db_conn.escape(self.title)
        if self.author is not None:
            self.author = db_conn.escape(self.author)
        if self.body is not None:
            self.body = db_conn.escape(self.body)
        if self.snippet is not None:
            self.snippet = db_conn.escape(self.snippet)

