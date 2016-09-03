#!/usr/bin/env python
#
# Trigger --re "regular expression" --exec "command_line %s"
#
# Watch a file, when lines are added to it that match <regular expression>,
# start "command" with the file line as an argument.
#
import os, sys
import re
import pyinotify as inotify
import logging
import getopt

def usage():
    print "Usage: trigger -r|--regexp=<regular expression> -e|--exec=<line to exec> -f|--file=<file>"
    print "\tExecute line <line to exec> with the line matching <regular expression> in <file>"
    sys.exit(2)

# process command line
options, remainder = getopt.getopt(sys.argv[1:], 'f:r:e:d:',
                                   ['re=', 'regexp=',
                                    'e=', 'exec', 'debug=',
                                    'f=', 'file='])
regexp_string = ''
exec_string = ''
file_string = ''
debug_string = ''
for opt, arg in options:
    if opt in ('-r', '--re', '--regexp'):
        regexp_string = arg
    elif opt in ('-e', '--e', '--exec'):
        exec_string = arg
    elif opt in ('-d', '--d', '--debug'):
        debug_string = arg
    elif opt in ('-f', '--f', '--file'):
        file_string = arg
    elif opt in ('-d', '--d', '--debug'):
        debug_string = arg

if not regexp_string or not exec_string or not file_string:
    usage()

# set up logging

log_level = logging.CRITICAL
if debug_string:
    try:
        print "Logging:",debug_string
        log_level = getattr(logging, debug_string.upper())
    except:
        print "debug values: debug, warn, info"
        usage()

logging.basicConfig(stream=sys.stderr,
                    format='%(levelname)s:%(message)s',
                    level=log_level)
logging.info("logging enabled: %s", logging.getLevelName(log_level))
logging.info("regexp: %s", regexp_string)
logging.info("file: %s", file_string)
logging.info("exec: %s",exec_string)

# compile the regular expression
search_re = re.compile(regexp_string)

# make sure we can access the file
if not os.access(file_string, os.R_OK):
    logging.error('Cannot access file %s', file_string)
    sys.exit(2)

last_size = 0
class event_handler(inotify.ProcessEvent):
    def __init__(self):
        self.last_size = os.stat(file_string).st_size
        self.regex = search_re
        super(event_handler, self).__init__()
    def process_IN_ACCESS(self, event):
        logging.info('Access event %s', event.pathname)
    def process_IN_ATTRIB(self, event):
        logging.info('Attrib event %s', event.pathname)
    def process_IN_CLOSE_NOWRITE(self, event):
        logging.info('Close, no write %s', event.pathname)
    def process_IN_CLOSE_WRITE(self, event):
        logging.info('Close, write %s', event.pathname)
        with open(file_string, 'r') as f:
            f.seek(self.last_size)
            line = f.readline()
            while line:
                logging.info("found string %s", line.rstrip())
                if self.regex.search(line.rstrip()):
                    logging.info("process %s with %s", line.rstrip(), exec_string)
                    os.system(exec_string % (line.rstrip()))
                line = f.readline()
        self.last_size = os.stat(file_string).st_size
        
    def process_IN_CREATE(self, event):
        logging.info('Create %s', event.pathname)
    def process_IN_DELETE(self, event):
        logging.info('Delete %s', event.pathname)
    def process_IN_MODIFY(self, event):
        logging.info('Modify %s', event.pathname)
    def process_IN_OPEN(self, event):
        logging.info('Open %s', event.pathname)        

def main():
    wm = inotify.WatchManager()
    wm.add_watch(file_string, inotify.ALL_EVENTS, rec=True)

    # event handler
    eh = event_handler()

    # notifier
    notifier = inotify.Notifier(wm, eh)
    notifier.loop()

if __name__ == '__main__':
    main()

