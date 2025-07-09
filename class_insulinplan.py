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
        self.untersteStufe = 90
        self.anzahlStufen = 8
        self.stufengroesse = 30
        self.miName = ""
        self.biName = ""
        self.biDosis = 0
        self.biVerabreichungsintervall = class_enums.Verabreichungsintervall.TÄGLICH

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
                insulinmenge =  int((self.untersteStufe + stufe * self.stufengroesse - self.blutzuckerZiel) / self.korrektur * self.beFaktoren[tageszeit] + 0.5)
                if insulinmenge >= 0:
                    insulinmengen.append(insulinmenge)
                    insulinmengentagessumme += insulinmenge
                else:
                    insulinmengen.append(0)
            if stufe == 0:
                blutzuckerbereich = "Unter " + "{:.1f}".format(self.untersteStufe).replace(".", ",")
                if self.blutzuckereinheit == class_enums.Blutzuckereinheit.MG_DL:
                     blutzuckerbereich = "Unter " + "{:.0f}".format(self.untersteStufe)
            elif stufe == self.anzahlStufen - 1:
                blutzuckerbereich = "Ab " + "{:.1f}".format(self.untersteStufe + (stufe -1) * self.stufengroesse).replace(".", ",")
                if self.blutzuckereinheit == class_enums.Blutzuckereinheit.MG_DL:
                    blutzuckerbereich = "Ab " + "{:.0f}".format(self.untersteStufe + (stufe -1) * self.stufengroesse)
            else:
                if self.blutzuckereinheit == class_enums.Blutzuckereinheit.MG_DL:
                    untererWert = "{:.0f}".format(self.untersteStufe + (stufe - 1) * self.stufengroesse)
                    obererWert = "{:.0f}".format(self.untersteStufe + stufe * self.stufengroesse - 1)
                else:
                    untererWert = "{:.1f}".format(self.untersteStufe + (stufe - 1) * self.stufengroesse).replace(".", ",")
                    obererWert = "{:.1f}".format(self.untersteStufe + stufe * self.stufengroesse - 0.1).replace(".", ",")
                blutzuckerbereich =  untererWert + " - " + obererWert
            plan.append([blutzuckerbereich, insulinmengen.copy(), insulinmengentagessumme])
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
