import sys, os, logging, datetime
basedir = os.path.dirname(__file__)

if not os.path.exists(os.path.join(basedir, "log")):
    os.mkdir(os.path.join(basedir, "log"), 0o777)
else:
    logListe = os.listdir(os.path.join(basedir, "log"))
    logListe.sort()
    if len(logListe) > 5:
        os.remove(os.path.join(basedir, "log",logListe[0]))
datum = datetime.datetime.strftime(datetime.datetime.today(), "%Y%m%d")
logHandler = logging.FileHandler(os.path.join(basedir, "log", datum + "_insugdt.log"), mode="a", encoding="utf_8")
logLevel = logging.WARNING
logForm = logging.Formatter("{asctime} {levelname:8}: {message}", "%d.%m.%Y %H:%M:%S", "{")
for arg in sys.argv:
    if arg.lower() == "debug":
        logLevel = logging.DEBUG
        break
logHandler.setFormatter(logForm)
logger = logging.getLogger(__name__)
logger.addHandler(logHandler)
logger.setLevel(logLevel)