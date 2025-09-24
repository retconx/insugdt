import class_enums
import re

kommazahlPattern = r"^\d+([,.]\d)?$"
befaktorPattern = r"^\d([,.]\d)?$"
zahlPattern = r"^\d+$"

class InsulinplanFehler(Exception):
    def __init__(self, message:str):
        self.message = message

    def __str__(self):
        return "Insulinfehler: " + self.message

class Insulinplan:
    def __init__(self, blutzuckerZiel:float, beFaktoren:list, korrektur:float, blutzuckereinheit:class_enums.Blutzuckereinheit):
        self.blutzuckerZiel = blutzuckerZiel
        self.beFaktoren = beFaktoren
        self.korrektur = korrektur
        self.blutzuckereinheit = blutzuckereinheit
        self.defaultInsulinEinheiten = [0, 0, 0, 0]
        self.untersteStufe = 0
        self.anzahlStufen = 0
        self.stufengroesse = 0
        self.miName = ""
        self.biName = ""
        self.biDosis = 0
        self.biVerabreichungsintervall = class_enums.Verabreichungsintervall.TAEGLICH
        self.moMiAb = class_enums.MoMiAb.MORGENS

    def setDefaultInsulinEinheiten(self, einheiten:list):
        self.defaultInsulinEinheiten = einheiten

    def getDefaultInsulinEinheiten(self):
        return self.defaultInsulinEinheiten

    def setUntersteStufe(self, stufe:float):
        self.untersteStufe = stufe

    def getUntersteStufe(self, stufe:float):
        return self.untersteStufe
        
    def setAnzahlStufen(self, anzahl:int):
        self.anzahlStufen = anzahl

    def getAnzahlStufen(self):
        return self.anzahlStufen

    def setStufengroesse(self, groesse:float):
        self.stufengroesse = groesse

    def getStufengroesse(self):
        return self.stufengroesse
    
    def setMiName(self, name:str):
        self.miName = name

    def getMiName(self):
        return self.miName

    def setBiName(self, name:str):
        self.biName = name

    def getBiName(self):
        return self.biName
    
    def setBiDosis(self,dosis:int):
        self.biDosis = dosis

    def getBiDosis(self):
        return self.biDosis

    def setBiVerabreichungsintervall(self, intervall:class_enums.Verabreichungsintervall):
        self.biVerabreichungsintervall = intervall

    def getBiVerabreichungsintervall(self):
        return self.biVerabreichungsintervall
    
    def setMoMiAb(self, tageszeit:class_enums.MoMiAb):
        self.moMiAb = tageszeit

    def getMoMiAb(self):
        return self.moMiAb
    
    def getZeilen(self):
        plan = []
        for stufe in range(-1, self.anzahlStufen, 1):
            untererWert = 0
            obererWert = 0
            if stufe == -1:
                untererWert = self.untersteStufe - self.stufengroesse
            else:
                untererWert = self.untersteStufe + stufe * self.stufengroesse
            if self.blutzuckereinheit == class_enums.Blutzuckereinheit.MG_DL:
                    obererWert = untererWert + self.stufengroesse - 1
            else:
                obererWert = untererWert + self.stufengroesse - 0.1
            insulinmengen = self.getInsulinmengen(untererWert, obererWert)
            if untererWert <= self.blutzuckerZiel and obererWert >= self.blutzuckerZiel:
                insulinmengen = ([int(menge) for menge in self.defaultInsulinEinheiten], int(sum(self.defaultInsulinEinheiten)))
            blutzuckerbereich = ""
            untereGrenze = ""
            obereGrenze = ""
            if stufe == - 1:
                if self.blutzuckereinheit == class_enums.Blutzuckereinheit.MG_DL:
                    blutzuckerbereich = "Bis " + "{:.0f}".format(obererWert)
                else:
                    blutzuckerbereich = "Bis " + "{:.1f}".format(obererWert).replace(".", ",")
            elif stufe == self.anzahlStufen - 1:
                if self.blutzuckereinheit == class_enums.Blutzuckereinheit.MG_DL:
                    blutzuckerbereich = "Ab " + "{:.0f}".format(untererWert)
                else:
                    blutzuckerbereich = "Ab " + "{:.1f}".format(untererWert).replace(".", ",")
            else:
                if self.blutzuckereinheit == class_enums.Blutzuckereinheit.MG_DL:
                    untereGrenze = "{:.0f}".format(untererWert)
                    obereGrenze = "{:.0f}".format(obererWert)
                else:
                    untereGrenze = "{:.1f}".format(untererWert).replace(".", ",")
                    obereGrenze = "{:.1f}".format(obererWert).replace(".", ",")
                blutzuckerbereich =  untereGrenze + " - " + obereGrenze
            plan.append([blutzuckerbereich, insulinmengen[0], insulinmengen[1]])
        return plan
    
    def getInsulinmengen (self, blutzuckerwert:float, obererWert:float):
        """
        Berechnet die zu verabreichenden Insulinmengen für vier Tageszeiten und berechnet die Summe. Liegt der aktuelle Messwert unterhalb des Blutzuckerzielwertes, wird die berechnete Insulinmenge um die Anzahl der unter des Zielwertes liegenden Stufen halbiert
        Parameter:
            blutzuckerwert: float, der aktuelle Messwert
            obererWert: float der obere Grenzwert des Blutzuckermessbereichs
        Return:
            Tupel: (insulinmengen:list der Tageszeiten, insulinmengentagessumme)
        """
        unterhalbZiel = self.blutzuckerZiel - obererWert > 0
        insulinmengen = []
        insulinmengentagessumme = 0
        for tageszeit in range(4): # 0=morgens, 1=mittags, 2=nachmittags, 3=abends
            insulinmenge = (blutzuckerwert - self.blutzuckerZiel) / self.korrektur * self.beFaktoren[tageszeit] + self.defaultInsulinEinheiten[tageszeit]
            if unterhalbZiel:
                insulinmenge = insulinmenge / (2 * pow(2, int((self.blutzuckerZiel - obererWert) / self.stufengroesse)))
            insulinmenge = int(insulinmenge + 0.5)
            if insulinmenge >= 0:
                insulinmengen.append(insulinmenge)
                insulinmengentagessumme += insulinmenge
            else:
                insulinmengen.append(0)
        return (insulinmengen, insulinmengentagessumme)

    # Statische Methoden
    @staticmethod
    def khInBe(khInGramm:float):
        return khInGramm / 12
    
    @staticmethod
    def beInKh(be:float):
        return be * 12
    
    @staticmethod
    def mgInMmol(mg:float):
        return mg * 0.0555
    
    @staticmethod
    def mmolInMg(mmol:float):
        return mmol / 0.0555
