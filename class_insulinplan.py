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
        self.defaultInsulinEinheiten = [0, 0, 0]
        self.untersteStufe = 0
        self.anzahlStufen = 0
        self.stufengroesse = 0
        self.miName = ""
        self.biName = ""
        self.biDosis = 0
        self.biVerabreichungsintervall = class_enums.Verabreichungsintervall.TÄGLICH

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
    
    def getZeilen(self):
        plan = []
        insulinmengen = []
        for stufe in range (self.anzahlStufen):
            insulinmengen.clear()
            insulinmengentagessumme = 0
            for tageszeit in range(3): # 0=morgens, 1=mittags, 2=abebnds
                if self.blutzuckereinheit == class_enums.Blutzuckereinheit.MG_DL:
                    untererWert = self.untersteStufe + stufe * self.stufengroesse
                    obererWert = untererWert + self.stufengroesse - 1
                else:
                    untererWert = self.untersteStufe + stufe * self.stufengroesse
                    obererWert = untererWert + self.stufengroesse - 0.1
                insulinmenge = (self.untersteStufe + stufe * self.stufengroesse - self.blutzuckerZiel) / self.korrektur * self.beFaktoren[tageszeit] + self.defaultInsulinEinheiten[tageszeit]
                if self.blutzuckerZiel - obererWert > 0:
                    insulinmenge = insulinmenge / (2 * pow(2, int((self.blutzuckerZiel - obererWert) / self.stufengroesse)))
                insulinmenge = int(insulinmenge + 0.5)
                if insulinmenge >= 0:
                    insulinmengen.append(insulinmenge)
                    insulinmengentagessumme += insulinmenge
                else:
                    insulinmengen.append(0)
            if stufe == self.anzahlStufen - 1:
                blutzuckerbereich = "Ab " + "{:.1f}".format(self.untersteStufe + stufe * self.stufengroesse).replace(".", ",")
                if self.blutzuckereinheit == class_enums.Blutzuckereinheit.MG_DL:
                    blutzuckerbereich = "Ab " + "{:.0f}".format(self.untersteStufe + stufe * self.stufengroesse)
            else:
                if self.blutzuckereinheit == class_enums.Blutzuckereinheit.MG_DL:
                    untererWert = "{:.0f}".format(self.untersteStufe + stufe * self.stufengroesse)
                    obererWert = "{:.0f}".format(self.untersteStufe + (stufe + 1) * self.stufengroesse - 1)
                else:
                    untererWert = "{:.1f}".format(self.untersteStufe + stufe * self.stufengroesse).replace(".", ",")
                    obererWert = "{:.1f}".format(self.untersteStufe + (stufe +1 ) * self.stufengroesse - 0.1).replace(".", ",")
                blutzuckerbereich =  untererWert + " - " + obererWert
            plan.append([blutzuckerbereich, insulinmengen.copy(), insulinmengentagessumme])
        # Unterste Stufe einfügen
        untersteInsulinmengen = []
        untersteInsulinSumme = 0
        for i in range(3):
            untersteInsulinmengen.append(int(plan[0][1][i] / 2 + 0.5))
            untersteInsulinSumme += int(plan[0][1][i] / 2 + 0.5)
        untererWert = str(int(self.untersteStufe))
        if self.blutzuckereinheit == class_enums.Blutzuckereinheit.MMOL_L:
            untererWert = "{:.1f}".format(self.untersteStufe)
        plan.insert(0, ["Unter " + untererWert, untersteInsulinmengen,untersteInsulinSumme])
        return plan

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
