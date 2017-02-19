import mysql.connector
from mysql.connector import errorcode
import MySQLdb
import collections


class DBConnector(object):
    """
    A basic wrapper for the python sql connector class
    Has a couple different ways to set connection params and some connection checking before running queries
    Basic functionality:
        query():          run a general query
        getResultRow():   get one row from the db in the form of a dictionary
        getResultArray(): get a list of dictionaries back, with a dictionary representig each row
    """
    conn = None
    host = None
    user = None
    password = None
    database = None
    mode = ''
    last_row_count = 0

    def __init__(self, host=None, user=None, password=None, database=None):
        """
        Constructor
        May be called with no parameters. In this case the connect() method called at the end of the constructor will
        do nothing and we will need to establish a db connection later on by manually calling connect() with the correct
        database parameters
        :param host:
        :param user:
        :param password:
        :param database:
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database

        self.connect()

    def setMode(self, mode):
        self.mode = mode

    def connect(self, host=None, user=None, password=None, database=None):
        """
        Initiate MySQL database connection.
        Method may be called with no params. In this case it will use the parameters previously set in the constructor
        :param host:
        :param user:
        :param password:
        :param database:
        :return:
        """
        # if new parameters were specified, set the class variables to them
        if host and user and password and database:
            self.host = host
            self.user = user
            self.password = password
            self.database = database

        if self.host and self.user and self.password and self.database:

            try:                                    # try to connect to the database
                self.conn = mysql.connector.connect(user=self.user,
                                                    password=self.password,
                                                    host=self.host,
                                                    database=self.database)
            except mysql.connector.Error as error:  # handle connection and wrong db errors

                if error.errno == errorcode.ER_ACCESS_DEMIED_ERROR:
                    print 'Something went wrong with your access permissions. Please check your username and password'
                elif error.errno == errorcode.ER_BAD_DB_ERROR:
                    print("Database does not exist")
                else:
                    print(error)

    def disconnect(self):
        """
        Close the MySQL connection
        """
        self.conn.close

    def checkConnection(self):
        """
        Some redundant checking to make sure the SQL connection is open before making any requests
        If the connection is not open, attempt to open it
        :return:
        """
        if self.conn is not None:
            return True
        else:
            self.connect()          # attempt to popen a new sql connection if none is found
            if self.conn is None:   # unable to open a sql connection
                return False
            else:                   # successfully opened a new sql connection
                return True

    def getResultArray(self, query, params=None):
        """
        Get a list of results from the database, multiple rows
        :param query: Query String
        :param params: Optional parameters to run a parametrized query

        :return: 2 dimensional list
        """
        if self.mode == 'debug':
            print "\ngetResultArray() ----------------------------------------"
            print query

        result_array = []

        if not self.checkConnection():
            return result_array

        cursor = self.conn.cursor(dictionary=True)
        if params is None:
            cursor.execute(query)
        else:
            cursor.execute(query, params)

        for row_dict in cursor:
            result_array.append(row_dict)

        self.last_row_count = cursor.rowcount
        if self.mode == 'debug':
            print 'row_count:', self.last_row_count

        cursor.close()

        return result_array

    def getResultRow(self, query, params=None):
        """
        Get a single row result from the database
        :param query: Query String
        :param params: Optional parameters to run a parametrized query
        :return: list
        """
        if self.mode == 'debug':
            print "\ngetResultRow() ----------------------------------------"

        result_array = self.getResultArray(query, params)
        if len(result_array) > 0:
            return result_array[0]
        else:
            return []

    def query(self, query, params=None):
        """
        Execute a query that does not return any data such as an INSERT or UPDATE statement
        returns true if the query succeeded and false if something went wrong
        :param query: Query String
        :param params: Optional parameters to run a parametrized query
        :return: boolean or int - last insert id
        """
        if self.mode == 'debug':
            print "\nquery() ----------------------------------------"
            print query
        result = False

        if not self.checkConnection():
            return result

        cursor = self.conn.cursor()
        try:
            if params is None:
                cursor.execute(query)
            else:
                cursor.execute(query, params)

            self.conn.commit()
        except mysql.connector.Error as error:
            print error.msg
            result = False
        else:
            if cursor.lastrowid not in (None, 0):
                result = cursor.lastrowid
            else:
                result = True

        self.last_row_count = cursor.rowcount
        if self.mode == 'debug':
            print 'row_count:', self.last_row_count
            print 'result:', result

        cursor.close()

        return result

    def queryMany(self, query, param_list):
        """
        Execute many parametrized queries at once
        returns true if the query succeeded and false if something went wrong
        :param param_list: list of tuples to plug into each query
        :param query:
        :return: boolean or int - last insert id
        """
        if self.mode == 'debug':
            print "\nqueryMany() ----------------------------------------"
            print query

        result = False

        if not self.checkConnection():
            return result

        cursor = self.conn.cursor()
        try:
            cursor.executemany(query, param_list)
            self.conn.commit()
        except mysql.connector.Error as error:
            print error.msg
            result = False
        else:
            if cursor.lastrowid is not None:
                result = cursor.lastrowid
            else:
                result = True

        self.last_row_count = cursor.rowcount
        if self.mode == 'debug':
            print 'row_count:', self.last_row_count

        cursor.close()

        return result

    def escape(self, string):
        """
        Use mysql_real_escape to escape the input string and return the result
        Escaping is handled automatically by the python sql connector. This method is here just in case
        :param string: Input string
        :return: Escaped result
        """
        if self.mode == 'debug':
            print "\nescape() ----------------------------------------"
            print string

        ascii_string = ''.join([x if ord(x) < 128 else ' ' for x in string])
        # escaped_string = ascii_string MySQLdb.escape_string(ascii_string)

        return ascii_string



