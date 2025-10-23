#!/usr/bin/env python3
"""gmailnudge
Send frequent emails to personal server to be picked up by GMail, thus causing GMail to check more often for new mail.
Also serves as a general purpose command line email sender.
"""

import importlib.metadata
__version__ = importlib.metadata.version(__package__ or __name__)

#==========================================================
#
#  Chris Nelson, Copyright 2023 - 2025
#
#==========================================================

import argparse
import sys
import time
import os.path
import signal
import collections

from cjnfuncs.core import logging, set_toolname
from cjnfuncs.configman import config_item
from cjnfuncs.timevalue import timevalue
from cjnfuncs.mungePath import mungePath
from cjnfuncs.SMTP import snd_email
from cjnfuncs.deployfiles import deploy_files
import cjnfuncs.core as core


# Configs / Constants
TOOLNAME        = "gmailnudge"
CONFIG_FILE     = "gmailnudge.cfg"
PRINTLOGLENGTH  = 40


def main():
    global filename, htmlfile
    try:
        snd_email (subj= args.subject, body=args.message, filename=filename, htmlfile=htmlfile, to=args.to, log=True, smtp_config=config)
    except Exception as e:
        print(f"snd_email error:  {e}")


def service():
    global config
    
    next_run = time.time()
    while True:
        if time.time() > next_run:
            if config.loadconfig(flush_on_reload=True):     # Refresh only if file changes
                logging.warning(f"NOTE - The config file has been reloaded.")
            try:
                snd_email (subj=config.getcfg('NudgeText'), body="Don't care", to='EmailTo', smtp_config=config)
                logging.info(f"Nudge message sent to {config.getcfg('EmailTo', section='SMTP')}")
            except Exception as e:
                logging.warning(f"snd_email error:  {e}")
            next_run += timevalue(config.getcfg("ServiceLoopTime")).seconds
        time.sleep(0.5)


def cleanup():
    logging.warning ("Cleanup")


def int_handler(signal, frame):
    logging.warning(f"Signal {signal} received.  Exiting.")
    cleanup()
    sys.exit(0)
signal.signal(signal.SIGINT,  int_handler)      # Ctrl-C
signal.signal(signal.SIGTERM, int_handler)      # kill


def cli():
    global config, args, logfile_override
    global filename, htmlfile

    set_toolname (TOOLNAME)

    parser = argparse.ArgumentParser(description=__doc__ + __version__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--to', '-t',
                        help="A single email address (contains an '@') or a config param ([SMTP] section) with a whitespace-separated-list of email addresses")
    parser.add_argument('--subject', '-s', default="--subject--",
                        help="Subject text")
    parser.add_argument('--message', '-m', 
                        help="Body text (--message wins over --file or --htmlfile)")
    parser.add_argument('--file', '-f', 
                        help="Plain-test file to be sent (--file wins over --htmlfile)")
    parser.add_argument('--htmlfile', '-F', 
                        help="HTML formatted file to be sent")
    parser.add_argument('--service', action='store_true',
                        help="Send emails in an endless loop for use as a systemd service")
    parser.add_argument('--config-file', '-c', type=str, default=CONFIG_FILE,
                        help=f"Path to the config file (Default <{CONFIG_FILE}>)")
    parser.add_argument('--print-log', '-p', action='store_true',
                        help=f"Print the tail end of the log file (default last {PRINTLOGLENGTH} lines).")
    parser.add_argument('--setup-user', action='store_true',
                        help=f"Install starter files in user space.")
    parser.add_argument('--setup-site', action='store_true',
                        help=f"Install starter files in system-wide space. Run with root prev.")
    parser.add_argument('-V', '--version', action='version', version='%(prog)s ' + __version__,
                        help="Return version number and exit")

    args = parser.parse_args()


    # Deploy template files
    if args.setup_user:
        deploy_files([
            { "source": CONFIG_FILE,        "target_dir": "USER_CONFIG_DIR", "file_stat": 0o644, "dir_stat": 0o755},
            { "source": "creds_SMTP",       "target_dir": "USER_CONFIG_DIR", "file_stat": 0o600},
            { "source": "gmailnudge.service", "target_dir": "USER_CONFIG_DIR", "file_stat": 0o644},
            ]) #, overwrite=True)
        sys.exit()

    if args.setup_site:
        deploy_files([
            { "source": CONFIG_FILE,        "target_dir": "SITE_CONFIG_DIR", "file_stat": 0o644, "dir_stat": 0o755},
            { "source": "creds_SMTP",       "target_dir": "SITE_CONFIG_DIR", "file_stat": 0o600},
            { "source": "gmailnudge.service", "target_dir": "SITE_CONFIG_DIR", "file_stat": 0o644},
            ]) #, overwrite=True)
        sys.exit()


    # Load config file and setup logging
    logfile_override = True  if not args.service  else False
    try:
        config = config_item(args.config_file)
        config.loadconfig(call_logfile_wins=logfile_override) #, ldcfg_ll=10)
    except Exception as e:
        logging.error(f"Failed loading config file <{args.config_file}>. \
\n  Run with  '--setup-user' or '--setup-site' to install starter files.\n  {e}\n  Aborting.")
        sys.exit(1)


    logging.warning (f"========== {core.tool.toolname} ({__version__}) ==========")
    logging.warning (f"Config file <{config.config_full_path}>")


    # Print log
    if args.print_log:
        try:
            _lf = mungePath(config.getcfg("LogFile"), core.tool.log_dir_base).full_path
            print (f"Tail of  <{_lf}>:")
            _xx = collections.deque(_lf.open(), config.getcfg("PrintLogLength", PRINTLOGLENGTH))
            for line in _xx:
                print (line, end="")
        except Exception as e:
            print (f"Couldn't print the log file.  LogFile defined in the config file?\n  {e}")
        sys.exit()


    # Input file existence check (and any other idiot checks)
    filename = None
    if args.file:
        filename = mungePath(args.file, ".").full_path   # make relative to the cwd
        if not os.path.exists(filename):
            logging.warning (f"Can't find the specified input file <{filename}>")
            sys.exit(1)

    htmlfile = None
    if args.htmlfile:
        htmlfile = mungePath(args.htmlfile, ".").full_path   # make relative to the cwd
        if not os.path.exists(htmlfile):
            logging.warning (f"Can't find the specified input file <{htmlfile}>")
            sys.exit(1)


    # Run in service or interactive modes
    if args.service:
        service()

    sys.exit(main())

    
if __name__ == '__main__':
    sys.exit(cli())