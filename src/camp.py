#!/usr/bin/python

import optparse

from pycamps import *

def do_camp(options, arguments):
    camps = PyCamps()
    if arguments[0] == "init":
        camps.do_init(options, arguments[1:])
    if arguments[0] == "start":
        args = arguments[1:]
        if len(args) >= 2:
            camps.do_start(options, args)
    if arguments[0] == "stop":
        args = arguments[1:]
        print "ARGS: %s" % str(args)
        if len(args) >= 2:
            camps.do_stop(options, args)

def main():                         
    p = optparse.OptionParser(description='Dispatches commands to create/manage development environments',
        prog='pycamp', version='pycamp 0.1', usage='%prog <options>')

    options, arguments = p.parse_args()
    print "Options: %s" % str(options)
    print "Arguments: %s" % str(arguments)
    if len(arguments) >= 2:
        do_camp(options, arguments)
    else:
        p.print_help()

if __name__ == "__main__":
    main()


