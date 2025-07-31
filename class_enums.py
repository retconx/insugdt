from enum import Enum

class Verabreichungsintervall(Enum):
    TAEGLICH = "täglich"
    MONTAG = "montags"
    DIENSTAG = "dienstags"
    MITTWOCH = "mittwochs"
    DONNERSTAG = "donnerstags"
    FREITAG = "freitags"
    SAMSTAG = "samstags"
    SONNTAG = "sonntags"

class MoMiAb(Enum):
    MORGENS = "morgens"
    MITTAGS = "mittags"
    ABENDS = "abends"

class Blutzuckereinheit(Enum):
    MG_DL = "mg/dl"
    MMOL_L = "mmol/l"
