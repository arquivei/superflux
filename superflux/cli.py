#!/usr/bin/env python

import sys

from optparse   import OptionParser
from superflux  import Superflux

### All options match the named params to Superflux.init()
def build_parser():
    parser = OptionParser( usage="Usage: superflux [options]" )
    parser.add_option( "-s", "--influx-server", dest="influx_server",
                       help="influx server address" )
    parser.add_option( "-p", "--influx-port", dest="influx_port",
                       help="influx server port" )
    parser.add_option( "-n", "--influx-db", dest="influx_db",
                       help="Which DB to write to" )
    parser.add_option( "-g", "--influx-group", dest="influx_group",
                       help="Extra attribute to group metrics" )
    parser.add_option( "-d", "--debug", dest="debug", action='store_true',
                       help="Enable debug output to STDERR" )
    return parser

def main():
    parser      = build_parser()
    opts, args  = parser.parse_args()

    kwargs = {}
    opts = list(vars(opts).items())
    ### Filter out all the arguments that weren't actually passed by the user
    for k,v in opts:
        if v is not None:
            kwargs[k] = v

    obj = Superflux( **kwargs )
    obj.run()

if __name__ == '__main__':
    main()
