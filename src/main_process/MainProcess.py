import config


class MainProcess(object):
    """
    A process class encompassing the common actions between the scanner, parser and mediator
    """
    log_level = ''
    available_log_levels = []

    def __init__(self):
        """
        Constructor: Set a default log level from the config file
        """
        self.log_level = config.settings['run_options']['log_level']
        self.available_log_levels = config.settings['available_log_levels']

    def setLogLevel(self, log_level):
        self.log_level = log_level

    def log(self, msg, log_level):
        """
        Print logging messages under different circumstances
        If the current logging level is equal to or highrt then the one specified for the message, it will print
        I.E verbose is the highest level and the most inclusive.
        If we specified verbose in the config, it will print every message
        :param msg:
        :param log_level:
        :return:
        """
        # This will always print a message if we are set to the highest log level. It has a cascading effect
        if self.available_log_levels.index(self.log_level) >= self.available_log_levels.index(log_level):
            print msg
