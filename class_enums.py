from enum import Enum

class Verabreichungsintervall(Enum):
    TÄGLICH = "täglich zur gleichen Zeit"
    WOECHENTLICH = "wöchentlich"

class Blutzuckereinheit(Enum):
    MG_DL = "mg/dl"
    MMOL_L = "mmol/l"
