from datetime import datetime
from inspect import currentframe, getframeinfo
from io import TextIOWrapper
from .internal.semver import SemVer
from .internal.birdy import CheckTime
from .internal.args import ScriptArgs
from .internal.bcolors import bcolors

class Logging:
    _version:SemVer = SemVer(4, 0, 0)
    version:SemVer = _version
    filename:str = f'betterLogs_{_version.toString().replace('.', '-')}/log.xml'
    allowPrinting:bool = False
    showHelp:bool = False # Change this to true if you want to show this help dialogue.
    allowArgs:bool = False
    append:bool = False
    
    def __init__(self, filename:str, beforeBeginning:str = '', allowPrinting:bool = True, append:bool = False):
        self.filename = filename; self.allowPrinting = allowPrinting; self.append = append
        
        if self.allowArgs:
            if ScriptArgs(self.allowArgs).containsHelp:
                print("""Arguments (Char's BetterLogs):
        -help :              Displays this message.
        -testingScript_BLP : Forces the secret message to be added to logs (see `.internal.birdy.CheckTime`)""")
        self._createDir(filename)
        self._initWrite()
        self._write(beforeBeginning + CheckTime().message + f'\n<!-- Log Generator: "Better Logs V{self._version.__str__()}" | Better Logs by Char @chargoldenyt on Discord | https://github.com/CharGoldenYT/betterLogs -->\n<!-- START OF LOG -->\n<logFile>\n')
        return
    
    def _initWrite(self):
        testfile = open(self.filename, 'a')
        size = testfile.__sizeof__()
        if not self.append and size > 1: testfile.truncate(0)
        testfile.close()
        
    def _write(self, content:str): self.write(content) # TODO: make this not a redirect function
        
    def write(self, content:str):
        logfile_lock = open(self.filename, 'a')
        logfile_lock.write(content)
        logfile_lock.close()

    def changefile(self, filename:str):
        prevlog = open(self.filename, "r")
        s = prevlog.read()
        prevlog.close()
        import os; os.remove(self.filename)
        
        self.filename = filename
        path = filename
        pSplit = path.split("/")
        path = ''
        for p in pSplit:
            path += p + '/'
        try:
            os.mkdir(path)
        except OSError as e: lmao = ""
        self._initWrite()
        newlog = open(filename, "a")
        newlog.write(s)
        newlog.close()

    def _levelToString(self, level:str) -> str:
        level = level.lower()

        color = '[MISC    ]:'
        if level == 'info':color = '[INFO    ]:'
        if level == 'warn' or level == 'warning':color = '[WARNING ]:'
        if level == 'err' or level == 'error':color = '[ERROR   ]:'
        if level == 'critical':color = '[CRITICAL]:'
        if level == 'fatal':color = '[FATAL   ]:'

        return color

    def log(self, log:str, level:str, includeTimestamp:bool = True, isHeader:bool = False, fileFrom:str = '', pos:int = 0):
        time = str(datetime.today().strftime('%d-%m-%Y %H:%M:%S'))
        timeString = '[' + time + ']: '

        color:str = bcolors.HEADER
        
        if not isHeader:
            level = level.lower()
            if level == 'info':color = bcolors.OKBLUE
            if level == 'warn' or level == 'warning':color = bcolors.WARNING
            if level == 'err' or level == 'error':color = bcolors.FAIL
            if level == 'critical':color = bcolors.FAIL
            if level == 'fatal':color = bcolors.FAIL

        if not includeTimestamp:
            timeString = ''

        fileString = ''

        if fileFrom != '':
            fileString = fileFrom + ':' + str(pos) + ':'

        logString = self._levelToString(level) + timeString + f"'{fileString + log}'".replace('"', "'").replace('<', "[").replace('>', ']')

        if self.allowPrinting: print(color + logString)

        self._write('   <log value="' + logString.replace(fileString, '') + '" />\n')

    def log_header(self, log:str, level:str, includeTimestamps:bool = True,  fileFrom:str = '', pos:int = 0):
        self.log(log, level, includeTimestamps, True, fileFrom, pos)

    def log_info(self, log:str, includeTimestamps:bool = True, fileFrom:str = '', pos:int = 0):
        self.log_header(log, 'info', includeTimestamps, fileFrom, pos)

    def log_error(self, log:str, includeTimestamps:bool = True, fileFrom:str = '', pos:int = 0):
        self.log(log, 'error', includeTimestamps, False, fileFrom, pos)

    def log_err(self, log:str, includeTimestamps:bool = True, fileFrom:str = '', pos:int = 0):
        print(bcolors.WARNING + '[WARNING ]:betterLogs.py:80:log_err() is deprecated! use log_error() instead')
        self.log_error(log, includeTimestamps, fileFrom, pos)

    def log_warning(self, log:str, includeTimestamps:bool = True, fileFrom:str = '', pos:int = 0):
        self.log(log, 'warn', includeTimestamps, False, fileFrom, pos)

    def log_warn(self, log:str, includeTimestamps:bool = True, fileFrom:str = '', pos:int = 0):
        print(bcolors.WARNING + '[WARNING ]:betterLogs.py:87:log_warn() is deprecated! use log_warning() instead')
        self.log_warning(log, includeTimestamps, fileFrom, pos)

    def log_critical(self, log:str, includeTimestamps:bool = True, fileFrom:str = '', pos:int = 0):
        self.log(log, 'critical', includeTimestamps, False, fileFrom, pos)

    def log_fatal(self, log:str, includeTimestamps:bool = True, fileFrom:str = '', pos:int = 0):
        self.log(log, 'fatal', includeTimestamps, False, fileFrom, pos)

    def close(self):
        self._write('</logFile>\n<!--  END OF LOG  -->')
        
    def getLogFile(logging) -> str:
        rawXml = open(logging.filename, 'r')
        xml = rawXml.read(); rawXml.close()
        return xml

    def _createDir(self, path:str):
        import os
        splitPath:list[str] = []
        if path.__contains__('/'):
            splitPath = path.split('/')
            splitPath.pop()

        if splitPath.__len__() > 0:
            for p in  splitPath:
                try:
                    os.makedirs(p.replace('.', '-'))
                except OSError as e:
                    if e.errno != 17:
                        print(f'Could not create log directory! "{str(e)}" make sure you have write access')
                        exit(1)
                    else: continue