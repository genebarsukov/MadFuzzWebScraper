#!/usr/bin/env python

import traceback
import argparse
import config
from helpers.DBConnector import DBConnector
from main_process.ScanMasterFlex import ScanMasterFlex
from helpers.Archiver import Archiver

# The first try block simply catches db connection errors.
# In the else we then run the scanner's scan() method in a second try-catch block which catches scanner runtime errors
# If an error is caught in the second try-catch block it is logged in the logging table NEWS_SCAN_LOG
try:
    # First instantiate a SQL connector object and give it to the ScannerQueue class so it can get records to scan
    db_conn = DBConnector(config.settings['db']['host'],
                          config.settings['db']['user'],
                          config.settings['db']['password'],
                          config.settings['db']['database'])

    scan_master_flex = ScanMasterFlex(db_conn)
    archiver = Archiver(db_conn)

except Exception as e:
    traceback.print_exc()
else:
    try:  # Main scanning tasks performed
        # Parse args
        parser = argparse.ArgumentParser(description='Main scanning process.')
        parser.add_argument('-s', '--source_id', help='source id to scan')
        parser.add_argument('-l', '--log_level', help='log verboseness level')
        parser.add_argument('-a', '--archive', action='store_true', help='archive old records')
        args = parser.parse_args()

        source_id = None
        archive = False

        if args is not None:

            # Archive
            if args.archive is not None:
                archive = args.archive

            # Source Id
            if args.source_id is not None:
                source_id = args.source_id

            # Set Log Levels
            if args.log_level is not None:
                scan_master_flex.setLogLevel(args.log_level)
                archiver.setLogLevel(args.log_level)

        # Archive old records
        if archive:
            archiver.archive()
        # Run the scan process
        else:
            scan_master_flex.scan(source_id)

    except Exception as e:
        traceback.print_exc()
