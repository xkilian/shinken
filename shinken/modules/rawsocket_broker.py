#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#    Francois Mikus, fmikus@acktomic.com
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.


# This Class is a plugin for the Shinken Broker. It is responsible
# for sending log broks to a raw socket destination.

import re
from socket import socket

from shinken.basemodule import BaseModule
from shinken.log import logger

properties = {
    'daemons': ['broker'],
    'type': 'raw_socket',
    'external': False,
    'phases': ['running'],
    }


# called by the plugin manager to get a broker
def get_instance(plugin):
    logger.info("Get a RawSocket broker for plugin %s" % plugin.get_name())

    #Catch errors
    #path = plugin.path
    instance = RawSocket_broker(plugin)
    return instance


# Get broks and send them to TCP Raw Socket listener
class RawSocket_broker(BaseModule):
    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)
        self.host = getattr(modconf, 'host', 'localhost')
        self.port = int(getattr(modconf, 'port', '9514'))
        self.data = int(getattr(modconf, 'data', 'state'))
        self.tick_limit = int(getattr(modconf, 'tick_limit', '3600'))
        self.buffer = []
        self.ticks = 0

    def init(self):
        self.con = socket()
        self.con.connect((self.host, self.port))

    # A log brok has arrived, we UPDATE data info with this
    def manage_log_brok(self, b):
        data = b.data
        line = data['log']

        if self.data == 'state' and (re.match("^\[[0-9]*\] SERVICE*.:", line) or re.match ("^\[[0-9]*\] HOST*.:", line_)):
            # Match logs which MUST be sent to the destination
            self.buffer.append("\n" + data['log'].encode('UTF-8'))

        elif self.data == 'all':
            self.buffer.append("\n" + data['log'].encode('UTF-8'))

def hook_tick(self, brok):
        """Each second the broker calls the hook_tick function
           Every tick try to flush the buffer
        """

        if self.ticks >= self.tick_limit:
            # If the number of ticks where data was not
            # sent successfully to the raw socket reaches the buffer limit.
            # Reset the buffer and reset the ticks
            self.buffer = []
            self.ticks = 0
            return

        self.ticks += 1

        try:
            self.con.sendall(self.buffer)
        except IOError, err:
            logger.error("[RawSocket broker] Failed sending to the Raw network socket! IOError:%s" % str(err))
            return

        # Flush the buffer after a successful send to the Raw Socket
        self.buffer = []
