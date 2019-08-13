#!/usr/bin/env python

import os
import re
import sys
import time
import string
import socket
import requests

from supervisor.childutils import listener
from optparse   import OptionParser

class Superflux(object):
    def __init__ ( self, **kwargs ):
        self.influx_server  = kwargs.get('influx_server', 'localhost')
        self.influx_port    = kwargs.get('influx_port', 8086)
        self.influx_db      = kwargs.get('influx_db', 'supervisor')
        self.influx_group   = kwargs.get('influx_group', 'supervisor')
        self.debug          = kwargs.get('debug', False)
        self.stdin          = sys.stdin
        self.stdout         = sys.stdout

        self.influx_url = "http://%s:%s/write?db=%s".format(self.influx_server, self.influx_port, self.influx_db)
        self._debug("Finished init")

    def run(self):
        self._debug("Starting")
        """
        The main run loop - evaluates all incoming events and never exits
        """

        while True:
            headers, payload = listener.wait( self.stdin, self.stdout )
            self._debug("Headers: %r\n" % repr(headers))
            self._debug("Body: %r\n" % repr(payload))

            event_name = headers.get( 'eventname', None )
            self._debug("Received event %s" % event_name)

            ### ignore TICK events
            if re.match( 'TICK', event_name ):
                self._debug( "Ignoring TICK event '%s'" % event_name )

            ### some sort of process related event - worth capturing
            elif re.match( 'PROCESS', event_name ):

                ### true for all process events:
                event_data      = self._parse_payload( payload, event_name )
                process_name    = event_data.get( 'processname', None )
                group_name      = event_data.get( 'groupname',   None )

                ### if you didn't specify a 'processname' explicitly, it'll
                ### be the same as groupname. otherwise, they differ and
                ### both should be in the key. So, check for that and decide.
                if process_name != group_name:
                    process_name += "_" + group_name

                ### in the case you used a . in your name, we'll convert that to a _
                ### here because influx renders those as seperators.
                ### Also remove any spaces as those are not supported in keys either.
                ### not sure if there are any other things that should be filtered out
                ### the docs are not conclusive and couldn't find the code section
                ### either. I'm pretty sure the key is used as the FS name for the
                ### whisper DB, so probably filesystem reserved characters are bad,
                ### however, that'd hold true for supervisor as well and I don't think
                ### we'd get here with such keys.
                process_name = process_name.replace( '.', '_' )
                process_name = process_name.replace( ' ', '_' )

                ### stdout/stderr capturing
                if re.match( 'PROCESS_LOG', event_name ):
                    event = "process_log, group=%s, name=%s, event=%s, value=1" % \
                        ( self.influx_group, process_name, event_name.lower() )
                    self._send_to_influx( event )

                ### state change
                elif re.match( 'PROCESS_STATE', event_name ):
                    event = "process_state, group=%s, name=%s, from_state=%s, to_state=%s, value=1" % \
                        ( self.influx_group, process_name, event_data.get('from_state', 'unknown').lower(), event_name.lower() )
                    self._send_to_influx( event )

                ### ignore IPC for now
                elif re.match( 'PROCESS_COMMUNICATION', event_name ):
                    self._debug( "Ignoring PROCESS event: '%s'" % event_name )

                ### unknown process event..?
                else:
                    self._debug( "Unknown PROCESS event: '%s'" % event_name )

            ### completely unknown event
            else:
                self._debug( "Unknown event: '%s'" % event_name )

            listener.ok( self.stdout )

    def _send_to_influx(self, event):
        """
        Take a string ready to be a influx event and send it to the influx host.
        """

        try:
            self._debug( "Sending to influx: %s" % event )
            r = requests.post(self.influx_url, data = "%s\n".format(event))

        except e:

            self._debug( "Could not connect to influx for '%s': %s" % (event, e) )

    def _parse_payload( self, payload, event_name ):
        """
        Take a header string and parse it into key/values
        """

        ### payload headers can look like this, where 'foo 01' is the actual
        ### processname. So hooray for complicated parsing :(
        # 'processname:foo 01 groupname:test from_state:STARTING pid:4424'

        ### I raised an issue to make parsing easier, or to ban spaces/colons:
        ### https://github.com/Supervisor/supervisor/issues/181
        ### Spaces/colons will be deprecated going forward, so let's just
        ### deal with any problems that may arise here and document the issue.

        ### read the first line, split that on spaces, then split that on colons
        line = payload.split( "\n", 1 )
        return dict( [ x.split(':') for x in line[0].split() ] )


    def _debug( self, msg ):
        """
        Write a string to STDERR and flush the buffer
        """

        if self.debug:
            sys.stderr.write( msg + "\n" )
            sys.stderr.flush()
