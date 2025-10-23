# gmailnudge - Nudge GMail so that it will frequently fetch new emails from another service

I use GMail as my email UI, but publicly use non-GMail email addresses from my own domain.  How frequently GMail fetches any new messages from my server depends on 
how frequently GMail _finds_ new messages to fetch.  If you only receive a few messages per day then GMail may not check but every hour... a useless lag in getting
new messages.

The known-fix is to regularly send dummy messages to your server so that GMail frequently finds new messages and thus will frequently check for new messages. (Also set up a filter
on the GMail side to delete messages with the given subject.)

The lag for messages from my server, using this tool, is no more that five minutes.  When you need a message immediately you can also open the GMail _Settings_ > _Account and Import_ page and force a "Check mail now".

**gmailnudge in service mode** is configured to periodically send emails to your server for GMail to pick up.  
- All settings are set in the config file, and a systemd service file is also provided.  
- The config file may be modified while in use and is automatically reloaded if changed by the running service.
- Logging goes to the config dir by default.

**gmailnudge also provides a `sndemail` command line interface** for conveniently sending general messages and files.
- Simple distribution list "aliases" may be defined in the config file for use with the `--to` CLI switch.
- The body of the message may be some inline text, a text file, or a html formatted file.  File references may use an absolute path, or are taken as 
relative to the shell current working directory.

Supported on Python3.9+ on Linux and Windows.

<br/>

---

## Notable changes since prior release
V2.1 - Adjusted for cjnfuncs V2.1 (module partitioning).
SMTP params must be in the [SMTP] config file section.

<br/>

---

## Usage
```
$ sndemail -h
usage: sndemail [-h] [--to TO] [--subject SUBJECT] [--message MESSAGE] [--file FILE] [--htmlfile HTMLFILE] [--service] [--config-file CONFIG_FILE]
                 [--print-log] [--setup-user] [--setup-site] [-V]

gmailnudge
Send frequent emails to personal server to be picked up by GMail, thus causing GMail to check more often for new mail.
Also serves as a general purpose command line email sender.
2.1

options:
  -h, --help            show this help message and exit
  --to TO, -t TO        A single email address (contains an '@') or a config param ([SMTP] section) with a whitespace-separated-list of email addresses
  --subject SUBJECT, -s SUBJECT
                        Subject text
  --message MESSAGE, -m MESSAGE
                        Body text (--message wins over --file or --htmlfile)
  --file FILE, -f FILE  Plain-test file to be sent (--file wins over --htmlfile)
  --htmlfile HTMLFILE, -F HTMLFILE
                        HTML formatted file to be sent
  --service             Send emails in an endless loop for use as a systemd service
  --config-file CONFIG_FILE, -c CONFIG_FILE
                        Path to the config file (Default <gmailnudge.cfg>)
  --print-log, -p       Print the tail end of the log file (default last 40 lines).
  --setup-user          Install starter files in user space.
  --setup-site          Install starter files in system-wide space. Run with root prev.
  -V, --version         Return version number and exit

```

<br/>

---

## Example CLI usage
```
$ sndemail --to family --subject "Here's the support log" --file transcript.txt
     gmailnudge.cli                  -  WARNING:  ========== gmailnudge (2.1) ==========
     gmailnudge.cli                  -  WARNING:  Config file </path-to/gmailnudge.cfg>
       cjnfuncs.snd_email            -  WARNING:  Email sent <Here's the support log>

$ sndemail --to mygmail --subject "Here's that report" --htmlfile Report_221127.html 
     gmailnudge.cli                  -  WARNING:  ========== gmailnudge (2.1) ==========
     gmailnudge.cli                  -  WARNING:  Config file </path-to/gmailnudge.cfg>
       cjnfuncs.snd_email            -  WARNING:  Email sent <Here's that report>

```


<br/>

---

## Example service mode logfile output
Nudge messages sent every 5 minutes. Logging level changed from INFO to WARNING while running:
```
$ sndemail -p
     gmailnudge.cli                  -  WARNING:  ========== gmailnudge (2.1) ==========
     gmailnudge.cli                  -  WARNING:  Config file </path-to/gmailnudge.cfg>
Tail of  </path-to/log_gmailnudge.txt>:
2023-03-19 13:29:00,908      gmailnudge.cli                   WARNING:  ========== gmailnudge (2.1) ==========
2023-03-19 13:29:00,908      gmailnudge.cli                   WARNING:  Config file </path-to/gmailnudge.cfg>
2023-03-19 13:29:02,262      gmailnudge.service                  INFO:  Nudge message sent to me@myserver.com
2023-03-19 13:34:02,605      gmailnudge.service                  INFO:  Nudge message sent to me@myserver.com
2023-03-19 13:39:02,447      gmailnudge.service                  INFO:  Nudge message sent to me@myserver.com
2023-03-19 13:42:41,079      gmailnudge.service               WARNING:  NOTE - The config file has been reloaded.
2023-03-19 15:28:18,650      gmailnudge.int_handler           WARNING:  Signal 2 received.  Exiting.
2023-03-19 15:28:18,651      gmailnudge.cleanup               WARNING:  Cleanup
```

<br/>

---

## Setup and Usage notes
- Install gmailnudge from PyPI (pip install gmailnudge).
- Install the initial configuration files (`sndemail --setup-user` places files at ~/.config/gmailnudge).
- Edit/configure `gmailnudge.cfg` and `creds_SMTP` as needed.
- Run manually as `sndemail`, or install the systemd service.
- When running in service mode (continuously looping) the config file may be edited and is reloaded when changed.  This allows for changing settings without having to restart the service.


<br/>

---

## Customization notes
- You may create whatever distribution list _aliases_ you wish for use with the CLI `--to` switch (see **Example CLI usage**, above).  

        family              email1@xyz.com  email2@gmail.com  email3@yahoo.com

<br/>

---

## Version history
- 2.1.2 251005 - Update pyproject.toml per PyPI requirements
- 2.1.1 240117 - service mode bug
- 2.1 240104 - Adjusted for cjnfuncs 2.1
- 2.0 230319 - New
