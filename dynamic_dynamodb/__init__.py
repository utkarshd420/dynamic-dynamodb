# -*- coding: utf-8 -*-
"""
Dynamic DynamoDB

Auto provisioning functionality for Amazon Web Service DynamoDB tables.


APACHE LICENSE 2.0
Copyright 2013 Sebastian Dahlgren

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import re
import sys
import time

from dynamic_dynamodb.core import dynamodb, gsi, table
from dynamic_dynamodb.daemon import Daemon
from dynamic_dynamodb.config_handler import CONFIGURATION as configuration
from dynamic_dynamodb.log_handler import LOGGER as logger


class DynamicDynamoDBDaemon(Daemon):
    """ Daemon for Dynamic DynamoDB"""

    def run(self, check_interval=1):
        """ Run the daemon

        :type check_interval: int
        :param check_interval: Delay in seconds between checks
        """
        while True:
            # Ensure provisioning
            for table_name, key_name in sorted(self.tables):
                table.ensure_provisioning(table_name, key_name)
                gsi.ensure_gsi_provisioning(table_name, key_name)

            # Sleep between the checks
            time.sleep(check_interval)


def main():
    """ Main function called from dynamic-dynamodb """
    table_names = set()
    used_keys = set()
    configured_tables = configuration['tables'].keys()

    # Add regexp table names
    for table_instance in dynamodb.list_tables():
        for key_name in configured_tables:
            if re.match(key_name, table_instance.table_name):
                logger.debug("Table {0} match with config key {1}".format(
                    table_instance.table_name, key_name))
                table_names.add((table_instance.table_name, key_name))
                used_keys.add(key_name)

    table_names = sorted(table_names)

    if configuration['global']['daemon']:
        pid_file = '/tmp/dynamic-dynamodb.{0}.pid'.format(
            configuration['global']['instance'])
        daemon = DynamicDynamoDBDaemon(pid_file, tables=table_names)

        if configuration['global']['daemon'] == 'start':
            daemon.start(
                check_interval=configuration['global']['check_interval'])

        elif configuration['global']['daemon'] == 'stop':
            daemon.stop()

        elif configuration['global']['daemon'] == 'restart':
            daemon.restart()

        elif configuration['global']['daemon'] in ['foreground', 'fg']:
            daemon.run(
                check_interval=configuration['global']['check_interval'])

        else:
            print 'Valid options for --daemon are start, stop and restart'
            sys.exit(1)
    else:
        # Ensure provisioning
        for table_name, key_name in table_names:
            #table.ensure_provisioning(table_name, key_name)
            gsi.ensure_gsi_provisioning(table_name, key_name)
