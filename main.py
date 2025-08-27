import sys, configparser, os, datetime, shutil,logger, re, atexit, subprocess
import gdt, gdtzeile
## Nur mit Lizenz
import gdttoolsL
## /Nur mit Lizenz
import xml.etree.ElementTree as ElementTree
from fpdf import FPDF, enums
import class_enums, datetime, class_insulinplan
import dialogUeberInsuGdt, dialogEinstellungenGdt, dialogEinstellungenAllgemein, dialogEinstellungenLanrLizenzschluessel, dialogEinstellungenImportExport, dialogEula, dialogVorlagenVerwalten
from PySide6.QtCore import Qt, QSize, QTranslator, QLibraryInfo
from PySide6.QtGui import QFont, QAction, QKeySequence, QIcon, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QGroupBox,
    QPushButton,
    QHBoxLayout,
    QGridLayout,
    QRadioButton,
    QWidget,
    QLabel, 
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QStatusBar,
    QFileDialog,
    QCheckBox,
    QDoubleSpinBox,
    QButtonGroup,
    QComboBox
)
import requests

basedir = os.path.dirname(__file__)

# Gegebenenfalls pdf- und log-Verzeichnisse anlegen
if not os.path.exists(os.path.join(basedir, "pdf")):
    os.mkdir(os.path.join(basedir, "pdf"), 0o777)
if not os.path.exists(os.path.join(basedir, "log")):
    os.mkdir(os.path.join(basedir, "log"), 0o777)
    logDateinummer = 0
else:
    logListe = os.listdir(os.path.join(basedir, "log"))
    logListe.sort()
    if len(logListe) > 5:
        os.remove(os.path.join(basedir, "log", logListe[0]))
datum = datetime.datetime.strftime(datetime.datetime.today(), "%Y%m%d")

def versionVeraltet(versionAktuell:str, versionVergleich:str):
    """
    Vergleicht zwei Versionen im Format x.x.x
    Parameter:
        versionAktuell:str
        versionVergleich:str
    Rückgabe:
        True, wenn versionAktuell veraltet
    """
    versionVeraltet= False
    hunderterBase = int(versionVergleich.split(".")[0])
    zehnerBase = int(versionVergleich.split(".")[1])
    einserBase = int(versionVergleich.split(".")[2])
    hunderter = int(versionAktuell.split(".")[0])
    zehner = int(versionAktuell.split(".")[1])
    einser = int(versionAktuell.split(".")[2])
    if hunderterBase > hunderter:
        versionVeraltet = True
    elif hunderterBase == hunderter:
        if zehnerBase >zehner:
            versionVeraltet = True
        elif zehnerBase == zehner:
            if einserBase > einser:
                versionVeraltet = True
    return versionVeraltet

# Sicherstellen, dass Icon in Windows angezeigt wird
try:
    from ctypes import windll # type: ignore
    mayappid = "gdttools.insugdt"
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(mayappid)
except ImportError:
    pass

class MainWindow(QMainWindow):
    # Mainwindow zentrieren
    def resizeEvent(self, e):
        mainwindowBreite = e.size().width()
        mainwindowHoehe = e.size().height()
        ag = self.screen().availableGeometry()
        screenBreite = ag.size().width()
        screenHoehe = ag.size().height()
        left = screenBreite / 2 - mainwindowBreite / 2
        top = screenHoehe / 2 - mainwindowHoehe / 2
        self.setGeometry(left, top, mainwindowBreite, mainwindowHoehe)

    def setPreFormularXml(self, xmlDateipdad:str, vorherigerPlan = False):
        try:
            self.setCursor(Qt.CursorShape.WaitCursor)
            baum = ElementTree.parse(xmlDateipdad)
            insulinplanElement = baum.getroot()
            berechnungsparameterElement = insulinplanElement.find("berechnungsparameter")
            blutzuckerziel = berechnungsparameterElement.findtext("blutzuckerziel") # type: ignore
            korrektur = berechnungsparameterElement.findtext("korrektur") # type: ignore
            einheit = berechnungsparameterElement.findtext("einheit") # type: ignore
            self.blutzuckereinheit = class_enums.Blutzuckereinheit(einheit)
            beFaktorenElement = berechnungsparameterElement.find("befaktoren") # type: ignore
            beFaktorenListe = [beFaktorenElement.findtext("morgens"), beFaktorenElement.findtext("mittags"), beFaktorenElement.findtext("abends")] # type: ignore
            defaultInsulinListe = ["", "", ""]
            if berechnungsparameterElement.find("defaultinsulin") != None: # type: ignore
                defaultInsulinElement = berechnungsparameterElement.find("defaultinsulin") # type: ignore
                defaultInsulinListe = [defaultInsulinElement.findtext("morgens"), defaultInsulinElement.findtext("mittags"), defaultInsulinElement.findtext("abends")] # type: ignore
            anzahlblutzuckerbereichsstufen = berechnungsparameterElement.findtext("anzahlblutzuckerbereichsstufen") # type: ignore
            untersteblutzuckerstufe = berechnungsparameterElement.findtext("untersteblutzuckerstufe") # type: ignore
            bereichsstuferngroesse = berechnungsparameterElement.findtext("bereichsstuferngroesse") # type: ignore
            mahlzeiteninsulinElement = insulinplanElement.find("mahlzeiteninsulin") # type: ignore
            miName = mahlzeiteninsulinElement.findtext("name") # type: ignore
            basalinsulinElement = insulinplanElement.find("basalinsulin") # type: ignore
            biName = basalinsulinElement.findtext("name") # type: ignore
            biDosis = basalinsulinElement.findtext("dosis") # type: ignore
            biVerabreichung = basalinsulinElement.findtext("verabreichungsintervall") # type: ignore
            biMoMiAb = "morgens" # ab 1.2.0
            if basalinsulinElement.find("momiab") != None: # type: ignore
                biMoMiAb = basalinsulinElement.findtext("momiab") # type: ignore
            self.lineEditBlutzuckerziel.setText(str(blutzuckerziel).replace(".", ","))
            self.lineEditKorrektur.setText(str(korrektur).replace(".", ","))
            self.labelEinheitBlutuckerziel.setText(str(einheit))
            self.labelEinheitKorrektur.setText(str(einheit))
            for i in range(3):
                self.doubleSpinBoxBeFaktoren[i].setValue(float(beFaktorenListe[i])) # type: ignore
            if len(defaultInsulinListe) > 0:
                for i in range(3):
                    self.lineEditDefaultInsulin[i].setText(str(defaultInsulinListe[i]))
            self.lineEditAnzahlBlutzuckerbereichsstufen.setText(str(anzahlblutzuckerbereichsstufen))
            self.lineEditUntersteBereichsstufe.setText(str(untersteblutzuckerstufe))
            self.labelEinheitUntersteBereichsstufe.setText(str(einheit))
            self.lineEditBereichsstufengroesse.setText(bereichsstuferngroesse)
            self.labelEinheitBereichsstufengroesse.setText(str(einheit))
            if self.blutzuckereinheit == class_enums.Blutzuckereinheit.MG_DL:
                self.radioButtonEinheitMg.setChecked(True)
            else: 
                self.radioButtonEinheitMmol.setChecked(True)
            self.lineEditMiName.setText(str(miName))
            self.lineEditBiName.setText(str(biName))
            self.lineEditBiDosis.setText(str(biDosis))
            if biVerabreichung == "wöchentlich":
                biVerabreichung = "montags"
            self.comboBoxVerabreichung.setCurrentText(str(biVerabreichung))
            if biMoMiAb == class_enums.MoMiAb.MORGENS.value:
                self.radioButtonMorgens.setChecked(True)
            elif biMoMiAb == class_enums.MoMiAb.MITTAGS.value:
                self.radioButtonMittags.setChecked(True)
            else:
                self. radioButtonAbends.setChecked(True)
            logger.logger.info("Eingabeformular vor-ausgefüllt")
            self.setCursor(Qt.CursorShape.ArrowCursor)
        except Exception as e:
            if vorherigerPlan:
                raise
            else:
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InsuGDT", "Fehler beim Laden der Vorlage (" + xmlDateipdad + "): " + e.args[1], QMessageBox.StandardButton.Ok)
            mb.exec()
    
    def __init__(self):
        super().__init__()

        # config.ini lesen
        ersterStart = False
        updateSafePath = ""
        if sys.platform == "win32":
            logger.logger.info("Plattform: win32")
            updateSafePath = os.path.expanduser("~\\appdata\\local\\insugdt")
        else:
            logger.logger.info("Plattform: nicht win32")
            updateSafePath = os.path.expanduser("~/.config/insugdt")
        self.configPath = updateSafePath
        self.configIni = configparser.ConfigParser()
        if os.path.exists(os.path.join(updateSafePath, "config.ini")):
            logger.logger.info("config.ini in " + updateSafePath + " exisitert")
            self.configPath = updateSafePath
        elif os.path.exists(os.path.join(basedir, "config.ini")):
            logger.logger.info("config.ini in " + updateSafePath + " exisitert nicht")
            try:
                if not os.path.exists(updateSafePath):
                    logger.logger.info(updateSafePath + " exisitert nicht")
                    os.makedirs(updateSafePath, 0o777)
                    logger.logger.info(updateSafePath + "erzeugt")
                shutil.copy(os.path.join(basedir, "config.ini"), updateSafePath)
                logger.logger.info("config.ini von " + basedir + " nach " + updateSafePath + " kopiert")
                self.configPath = updateSafePath
                ersterStart = True
            except:
                logger.logger.error("Problem beim Kopieren der config.ini von " + basedir + " nach " + updateSafePath)
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InsuGDT", "Problem beim Kopieren der Konfigurationsdatei. InsuGDT wird mit Standardeinstellungen gestartet.", QMessageBox.StandardButton.Ok)
                mb.exec()
                self.configPath = basedir
        else:
            logger.logger.critical("config.ini fehlt")
            mb = QMessageBox(QMessageBox.Icon.Critical, "Hinweis von InsuGDT", "Die Konfigurationsdatei config.ini fehlt. InsuGDT kann nicht gestartet werden.", QMessageBox.StandardButton.Ok)
            mb.exec()
            sys.exit()

        self.configIni.read(os.path.join(self.configPath, "config.ini"))
        self.gdtImportVerzeichnis = self.configIni["GDT"]["gdtimportverzeichnis"]
        self.gdtExportVerzeichnis = self.configIni["GDT"]["gdtexportverzeichnis"]
        self.kuerzelinsugdt = self.configIni["GDT"]["kuerzelinsugdt"]
        self.kuerzelpraxisedv = self.configIni["GDT"]["kuerzelpraxisedv"]
        self.version = self.configIni["Allgemein"]["version"]
        self.defaultXml = self.configIni["Allgemein"]["defaultxml"]
        self.vorlagen = []
        if self.configIni.has_option("Allgemein", "vorlagenverzeichnis"):
            self.vorlagenverzeichnis = self.configIni["Allgemein"]["vorlagenverzeichnis"]
            if self.vorlagenverzeichnis != "" and os.path.exists(self.vorlagenverzeichnis):
                for vorlage in os.listdir(self.vorlagenverzeichnis):
                    if vorlage[-4:] == ".igv":
                        self.vorlagen.append(vorlage[0:-4])
                self.vorlagen.sort()
            elif self.vorlagenverzeichnis != "":
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InsuGDT", "Das Vorlagenverzeichnis " + self.vorlagenverzeichnis + " existiert nicht.", QMessageBox.StandardButton.Ok)
                mb.exec()
        self.eulagelesen = self.configIni["Allgemein"]["eulagelesen"] == "True"
        self.autoupdate = self.configIni["Allgemein"]["autoupdate"] == "True"
        self.updaterpfad = self.configIni["Allgemein"]["updaterpfad"]
        self.dokuVerzeichnis = self.configIni["Allgemein"]["dokuverzeichnis"]
        self.vorherigeDokuLaden = (self.configIni["Allgemein"]["vorherigedokuladen"] == "1")
        self.blutzuckereinheit = class_enums.Blutzuckereinheit(self.configIni["Allgemein"]["blutzuckereinheit"])

        # Nachträglich hinzufefügte Options
        # 1.2.0
        self.beFaktorStandardschritt = 0.25
        if self.configIni.has_option("Allgemein", "befaktorstandardschritt"):
            self.beFaktorStandardschritt = float(self.configIni["Allgemein"]["befaktorstandardschritt"])
        # /Nachträglich hinzufefügte Options

        z = self.configIni["GDT"]["zeichensatz"]
        self.zeichensatz = gdt.GdtZeichensatz.IBM_CP437
        if z == "1":
            self.zeichensatz = gdt.GdtZeichensatz.BIT_7
        elif z == "3":
            self.zeichensatz = gdt.GdtZeichensatz.ANSI_CP1252
        self.lanr = self.configIni["Erweiterungen"]["lanr"]
        self.lizenzschluessel = self.configIni["Erweiterungen"]["lizenzschluessel"]

        ## Nur mit Lizenz
        # Prüfen, ob Lizenzschlüssel unverschlüsselt
        if len(self.lizenzschluessel) == 29:
            logger.logger.info("Lizenzschlüssel unverschlüsselt")
            self.configIni["Erweiterungen"]["lizenzschluessel"] = gdttoolsL.GdtToolsLizenzschluessel.krypt(self.lizenzschluessel)
            with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                    self.configIni.write(configfile)
        else:
            self.lizenzschluessel = gdttoolsL.GdtToolsLizenzschluessel.dekrypt(self.lizenzschluessel)
        ## /Nur mit Lizenz

        # Prüfen, ob EULA gelesen
        if not self.eulagelesen:
            de = dialogEula.Eula()
            de.exec()
            if de.checkBoxZustimmung.isChecked():
                self.eulagelesen = True
                self.configIni["Allgemein"]["eulagelesen"] = "True"
                with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                    self.configIni.write(configfile)
                logger.logger.info("EULA zugestimmt")
            else:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InsuGDT", "Ohne Zustimmung der Lizenzvereinbarung kann InsuGDT nicht gestartet werden.", QMessageBox.StandardButton.Ok)
                mb.exec()
                sys.exit()

        # Grundeinstellungen bei erstem Start
        if ersterStart:
            logger.logger.info("Erster Start")
            mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von InsuGDT", "Vermutlich starten Sie InsuGDT das erste Mal auf diesem PC.\nMöchten Sie jetzt die Grundeinstellungen vornehmen?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.setDefaultButton(QMessageBox.StandardButton.Yes)
            if mb.exec() == QMessageBox.StandardButton.Yes:
                ## Nur mit Lizenz
                self.einstellungenLanrLizenzschluessel(False, False)
                ## /Nur mit Lizenz
                self.einstellungenGdt(False, False)
                self.einstellungenAllgemein(False, False)
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InsuGDT", "Die Ersteinrichtung ist abgeschlossen. InsuGDT wird beendet.", QMessageBox.StandardButton.Ok)
                mb.exec()
                sys.exit()

        # Version vergleichen und gegebenenfalls aktualisieren
        configIniBase = configparser.ConfigParser()
        try:
            configIniBase.read(os.path.join(basedir, "config.ini"))
            if versionVeraltet(self.version, configIniBase["Allgemein"]["version"]):
                # Version aktualisieren
                self.configIni["Allgemein"]["version"] = configIniBase["Allgemein"]["version"]
                self.configIni["Allgemein"]["releasedatum"] = configIniBase["Allgemein"]["releasedatum"] 
                # config.ini aktualisieren
                # 1.1.1 -> 1.2.0: ["Allgemein"]["befaktorstandardschritt"] hinzufügen
                if not self.configIni.has_option("Allgemein", "befaktorstandardschritt"):
                    self.configIni["Allgemein"]["befaktorstandardschritt"] = "0.25"
                # /config.ini aktualisieren

                with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                    self.configIni.write(configfile)
                self.version = self.configIni["Allgemein"]["version"]
                logger.logger.info("Version auf " + self.version + " aktualisiert")
                # Prüfen, ob EULA gelesen
                de = dialogEula.Eula(self.version)
                de.exec()
                self.eulagelesen = de.checkBoxZustimmung.isChecked()
                self.configIni["Allgemein"]["eulagelesen"] = str(self.eulagelesen)
                with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                    self.configIni.write(configfile)
                if self.eulagelesen:
                    logger.logger.info("EULA zugestimmt")
                else:
                    logger.logger.info("EULA nicht zugestimmt")
                    mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InsuGDT", "Ohne  Zustimmung zur Lizenzvereinbarung kann InsuGDT nicht gestartet werden.", QMessageBox.StandardButton.Ok)
                    mb.exec()
                    sys.exit()
        except SystemExit:
            sys.exit()
        except:
            logger.logger.error("Problem beim Aktualisieren auf Version " + configIniBase["Allgemein"]["version"])
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InsuGDT", "Problem beim Aktualisieren auf Version " + configIniBase["Allgemein"]["version"], QMessageBox.StandardButton.Ok)
            mb.exec()

        self.addOnsFreigeschaltet = True
        
        ## Nur mit Lizenz
        # Pseudo-Lizenz?
        self.pseudoLizenzId = ""
        rePatId = r"^patid\d+$"
        for arg in sys.argv:
            if re.match(rePatId, arg) != None:
                logger.logger.info("Pseudo-Lizenz mit id " + arg[5:])
                self.pseudoLizenzId = arg[5:]

        # Add-Ons freigeschaltet?
        self.addOnsFreigeschaltet = gdttoolsL.GdtToolsLizenzschluessel.lizenzErteilt(self.lizenzschluessel, self.lanr, gdttoolsL.SoftwareId.INSUGDT) or gdttoolsL.GdtToolsLizenzschluessel.lizenzErteilt(self.lizenzschluessel, self.lanr, gdttoolsL.SoftwareId.INSUGDTPSEUDO) and self.pseudoLizenzId != ""
        if self.lizenzschluessel != "" and gdttoolsL.GdtToolsLizenzschluessel.getSoftwareId(self.lizenzschluessel) == gdttoolsL.SoftwareId.INSUGDTPSEUDO and self.pseudoLizenzId == "":
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InsuGDT", "Bei Verwendung einer Pseudolizenz muss InsuGDT mit einer Patienten-Id als Startargument im Format \"patid<Pat.-Id>\" ausgeführt werden.", QMessageBox.StandardButton.Ok)
            mb.exec() 
        ## /Nur mit Lizenz
        
        jahr = datetime.datetime.now().year
        copyrightJahre = "2023"
        if jahr > 2023:
            copyrightJahre = "2023-" + str(jahr)
        self.setWindowTitle("InsuGDT V" + self.version + " (\u00a9 Fabian Treusch - GDT-Tools " + copyrightJahre + ")")
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)
        self.fontKlein = QFont()
        self.fontKlein.setPixelSize(10)

        # GDT-Datei laden
        gd = gdt.GdtDatei()
        self.patId = "-"
        self.vorname = "-"
        self.nachname = "-"
        self.gebdat = "-"
        mbErg = QMessageBox.StandardButton.Yes
        try:
            # Prüfen, ob PVS-GDT-ID eingetragen
            senderId = self.configIni["GDT"]["idpraxisedv"]
            if senderId == "":
                senderId = None
            gd.laden(self.gdtImportVerzeichnis + "/" + self.kuerzelinsugdt + self.kuerzelpraxisedv + ".gdt", self.zeichensatz, senderId)
            self.patId = str(gd.getInhalt("3000"))
            self.vorname = str(gd.getInhalt("3102"))
            self.nachname = str(gd.getInhalt("3101"))
            gd = str(gd.getInhalt("3103"))
            self.gebdat = gd[0:2] + "." + gd[2:4] + "." + gd[4:8]
            logger.logger.info("PatientIn " + self.vorname + " " + self.nachname + " (ID: " + self.patId + ") geladen")
            ## Nur mit Lizenz
            if self.pseudoLizenzId != "":
                self.patId = self.pseudoLizenzId
                logger.logger.info("PatId wegen Pseudolizenz auf " + self.pseudoLizenzId + " gesetzt")
            ## /Nur mit Lizenz
        except (IOError, gdtzeile.GdtFehlerException) as e:
            logger.logger.warning("Fehler beim Laden der GDT-Datei: " + str(e))
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InsuGDT", "Fehler beim Laden der GDT-Datei:\n" + str(e) + "\n\nDieser Fehler hat in der Regel eine der folgenden Ursachen:\n- Die im PVS und in InsuGDT konfigurierten GDT-Austauschverzeichnisse stimmen nicht überein.\n- InsuGDT wurde nicht aus dem PVS heraus gestartet, so dass keine vom PVS erzeugte GDT-Datei gefunden werden konnte.\n\nSoll InsuGDT dennoch geöffnet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
            mb.button(QMessageBox.StandardButton.No).setText("Nein")
            mb.setDefaultButton(QMessageBox.StandardButton.No)
            mbErg = mb.exec()
        if mbErg == QMessageBox.StandardButton.Yes:
            self.widget = QWidget()
            mainLayoutV = QVBoxLayout()
            self.labelPseudolizenz = QLabel("+++ Pseudolizenz für Test-/ Präsentationszwecke +++")
            self.labelPseudolizenz.setStyleSheet("color:rgb(200,0,0);font-style:italic")
            mainSpaltenlayout = QHBoxLayout()
            mainLayoutLinkeSpalte = QVBoxLayout()
            mainLayoutRechteSpalte = QVBoxLayout()

            self.pushButtonVorausgefuellt = QPushButton()
            self.pushButtonVorausgefuellt.setFont(self.fontNormal)
            self.pushButtonVorausgefuellt.setStyleSheet("color:rgb(0,0,200)")
            
            # Groupbox Berechnungsparameter
            defaultBlutzuckerziel = "110"
            defaultKorrektur = "30"
            defautlUntersteBereichsstufe = "90"
            defaultBereichsstufengröße = "30"
            if self.blutzuckereinheit == class_enums.Blutzuckereinheit.MMOL_L:
                defaultBlutzuckerziel = "{:.1f}".format(110 * 0.0555)
                defaultKorrektur = "{:.1f}".format(30 * 0.0555)
                defautlUntersteBereichsstufe = "{:.1f}".format(110 * 0.0555)
                defaultBereichsstufengröße = "{:.1f}".format(30 * 0.0555)
            berechnungsparameterLayout = QGridLayout()
            groupBoxBerechnungsparameter = QGroupBox("Berechnungsparameter")
            groupBoxBerechnungsparameter.setFont(self.fontBold)
            labelBlutzuckerziel= QLabel("Blutzuckerziel")
            labelBlutzuckerziel.setFont(self.fontNormal)
            self.lineEditBlutzuckerziel = QLineEdit(defaultBlutzuckerziel)
            self.lineEditBlutzuckerziel.setFont(self.fontNormal)
            self.labelEinheitBlutuckerziel = QLabel(self.blutzuckereinheit.value)
            self.labelEinheitBlutuckerziel.setFont(self.fontNormal)
            labelKorrektur = QLabel("Blutzuckersenkung/Insulineinheit (Korrektur)")
            labelKorrektur.setFont(self.fontNormal)
            self.lineEditKorrektur = QLineEdit(defaultKorrektur)
            self.lineEditKorrektur.setFont(self.fontNormal) 
            self.labelEinheitKorrektur = QLabel(self.blutzuckereinheit.value)
            self.labelEinheitKorrektur.setFont(self.fontNormal)
            tageszeitenLayout = QGridLayout()
            labelBeFaktoren = QLabel("BE-Faktoren")
            labelBeFaktoren.setFont(self.fontNormal)
            labelMorgens = QLabel("morgens")
            labelMorgens.setFont(self.fontNormal)
            labelMittags = QLabel("mittags")
            labelMittags.setFont(self.fontNormal)
            labelAbends = QLabel("abends")
            labelAbends.setFont(self.fontNormal)
            self.doubleSpinBoxBeFaktoren = []
            defaultBeFaktoren = [2, 1, 1.5]
            for i in range(3):
                self.doubleSpinBoxBeFaktoren.append(QDoubleSpinBox())
                self.doubleSpinBoxBeFaktoren[i].setValue(defaultBeFaktoren[i])
                self.doubleSpinBoxBeFaktoren[i].setMinimum(0)
                self.doubleSpinBoxBeFaktoren[i].setMaximum(10)
                self.doubleSpinBoxBeFaktoren[i].setSingleStep(self.beFaktorStandardschritt)
                self.doubleSpinBoxBeFaktoren[i].setDecimals(2)
                self.doubleSpinBoxBeFaktoren[i].setFont(self.fontNormal)
                self.doubleSpinBoxBeFaktoren[i]
            labelDefaultInsulin = QLabel("Insulindosis bei normalem Blutzucker")
            labelDefaultInsulin.setFont(self.fontNormal)
            self.lineEditDefaultInsulin = []
            labelIe = []
            defaultInsulin = ["6", "4", "5"]
            for i in range(3):
                self.lineEditDefaultInsulin.append(QLineEdit(defaultInsulin[i]))
                self.lineEditDefaultInsulin[i].setFont(self.fontNormal)
                labelIe.append(QLabel("IE"))
                labelIe[i].setFont(self.fontNormal)
            labelAnzahlBlutzuckerereichsstufen = QLabel("Anzahl Blutzuckerbereichsstufen")
            labelAnzahlBlutzuckerereichsstufen.setFont(self.fontNormal)
            self.lineEditAnzahlBlutzuckerbereichsstufen = QLineEdit("8")
            self.lineEditAnzahlBlutzuckerbereichsstufen.setFont(self.fontNormal)
            labelUntersteBereichsstufe = QLabel("Unterste Bereichsstufe")
            labelUntersteBereichsstufe.setFont(self.fontNormal)
            self.lineEditUntersteBereichsstufe = QLineEdit(defautlUntersteBereichsstufe)
            self.lineEditUntersteBereichsstufe.setFont(self.fontNormal)
            self.labelEinheitUntersteBereichsstufe = QLabel(self.blutzuckereinheit.value)
            self.labelEinheitUntersteBereichsstufe.setFont(self.fontNormal)
            labelBereichsstufengroesse = QLabel("Bereichsstufengröße")
            labelBereichsstufengroesse.setFont(self.fontNormal)
            self.lineEditBereichsstufengroesse = QLineEdit(defaultBereichsstufengröße)
            self.lineEditBereichsstufengroesse.setFont(self.fontNormal)
            self.labelEinheitBereichsstufengroesse = QLabel(self.blutzuckereinheit.value)
            self.labelEinheitBereichsstufengroesse.setFont(self.fontNormal)
            groupBoxBerechnungsparameter.setLayout(berechnungsparameterLayout)
            berechnungsparameterLayout.addWidget(labelBlutzuckerziel, 0, 0, 1, 1)
            berechnungsparameterLayout.addWidget(self.lineEditBlutzuckerziel, 0, 1, 1, 1)
            berechnungsparameterLayout.addWidget(self.labelEinheitBlutuckerziel, 0, 2, 1, 1)
            berechnungsparameterLayout.addWidget(labelKorrektur, 1, 0, 1, 1)
            berechnungsparameterLayout.addWidget(self.lineEditKorrektur, 1, 1, 1, 1)
            berechnungsparameterLayout.addWidget(self.labelEinheitKorrektur, 1, 2, 1, 1)
            berechnungsparameterLayout.addWidget(QLabel(" "), 2, 0, 1, 1)
            berechnungsparameterLayout.addWidget(labelBeFaktoren, 3, 0, 1, 1)
            berechnungsparameterLayout.addWidget(labelDefaultInsulin, 4, 0, 1, 1)
            tageszeitenLayout.addWidget(labelMorgens, 0, 0, 1, 2)
            tageszeitenLayout.addWidget(labelMittags, 0, 2, 1, 2)
            tageszeitenLayout.addWidget(labelAbends, 0, 4, 1, 2)
            for i in range(3):
                tageszeitenLayout.addWidget(self.doubleSpinBoxBeFaktoren[i], 1, i * 2, 1, 2)
            for i in range(3):
                tageszeitenLayout.addWidget(self.lineEditDefaultInsulin[i], 2, i * 2, 1, 1)
                tageszeitenLayout.addWidget(labelIe[i], 2, i * 2 + 1, 1, 1)
            berechnungsparameterLayout.addLayout(tageszeitenLayout, 2, 1, 3, 2)
            berechnungsparameterLayout.addWidget(labelAnzahlBlutzuckerereichsstufen, 5, 0, 1, 1)
            berechnungsparameterLayout.addWidget(self.lineEditAnzahlBlutzuckerbereichsstufen, 5, 1, 1, 2)
            berechnungsparameterLayout.addWidget(labelUntersteBereichsstufe, 6, 0, 1, 1)
            berechnungsparameterLayout.addWidget(self.lineEditUntersteBereichsstufe, 6, 1, 1, 1)
            berechnungsparameterLayout.addWidget(self.labelEinheitUntersteBereichsstufe, 6, 2, 1, 1)
            berechnungsparameterLayout.addWidget(labelBereichsstufengroesse, 7, 0, 1, 1)
            berechnungsparameterLayout.addWidget(self.lineEditBereichsstufengroesse, 7, 1, 1, 1)
            berechnungsparameterLayout.addWidget(self.labelEinheitBereichsstufengroesse, 7, 2, 1, 1)

            # Groupbox Mahlzeiteninsulin
            groupBoxMahlzeiteninsulin = QGroupBox("Mahlzeiteninsulin")
            groupBoxMahlzeiteninsulin.setFont(self.fontBold)
            mahlzeiteninsulinLayout = QGridLayout()
            labelMiName = QLabel("Name")
            labelMiName.setFont(self.fontNormal)
            self.lineEditMiName = QLineEdit()
            self.lineEditMiName.setFont(self.fontNormal)
            groupBoxMahlzeiteninsulin.setLayout(mahlzeiteninsulinLayout)
            mahlzeiteninsulinLayout.addWidget(labelMiName, 0, 0)
            mahlzeiteninsulinLayout.addWidget(self.lineEditMiName, 0, 1)

            # Groupbox Basalinsulin
            groupBoxBasalinsulin = QGroupBox("Basalinsulin")
            groupBoxBasalinsulin.setFont(self.fontBold)
            basalinsulinLayout = QGridLayout()
            labelBiName = QLabel("Name")
            labelBiName.setFont(self.fontNormal)
            self.lineEditBiName = QLineEdit()
            self.lineEditBiName.setFont(self.fontNormal)
            labelBiDosis = QLabel("Dosis")
            labelBiDosis.setFont(self.fontNormal)
            self.lineEditBiDosis = QLineEdit()
            self.lineEditBiDosis.setFont(self.fontNormal)
            labelBiEinheit = QLabel("IE")
            labelBiEinheit.setFont(self.fontNormal)
            labelBiVerabreichungsintervall = QLabel("Verabreichungsintervall")
            labelBiVerabreichungsintervall.setFont(self.fontNormal)
            self.comboBoxVerabreichung = QComboBox()
            self.comboBoxVerabreichung.setFont(self.fontNormal)
            for v in class_enums.Verabreichungsintervall:
                self.comboBoxVerabreichung.addItem(v.value)
            self.comboBoxVerabreichung.setCurrentIndex(0)
            momiabLayout = QHBoxLayout()
            buttonGroupMoMiAb = QButtonGroup(self)
            self.radioButtonMorgens = QRadioButton("morgens")
            self.radioButtonMorgens.setFont(self.fontNormal)
            self.radioButtonMittags = QRadioButton("mittags")
            self.radioButtonMittags.setFont(self.fontNormal)
            self.radioButtonAbends = QRadioButton("abends")
            self.radioButtonAbends.setFont(self.fontNormal)
            self.radioButtonMorgens.setChecked(True)
            buttonGroupMoMiAb.addButton(self.radioButtonMorgens)
            buttonGroupMoMiAb.addButton(self.radioButtonMittags)
            buttonGroupMoMiAb.addButton(self.radioButtonAbends)
            groupBoxBasalinsulin.setLayout(basalinsulinLayout)
            basalinsulinLayout.addWidget(labelBiName, 0, 0, 1, 1)
            basalinsulinLayout.addWidget(self.lineEditBiName, 0, 1, 1, 2)
            basalinsulinLayout.addWidget(labelBiDosis, 1, 0, 1, 1)
            basalinsulinLayout.addWidget(self.lineEditBiDosis, 1, 1, 1, 1)
            basalinsulinLayout.addWidget(labelBiEinheit, 1, 2, 1, 1)
            basalinsulinLayout.addWidget(labelBiVerabreichungsintervall, 2, 0, 1, 1)
            basalinsulinLayout.addWidget(self.comboBoxVerabreichung, 2, 1, 1, 1)
            momiabLayout.addWidget(self.radioButtonMorgens)
            momiabLayout.addWidget(self.radioButtonMittags)
            momiabLayout.addWidget(self.radioButtonAbends)
            basalinsulinLayout.addLayout(momiabLayout, 2, 2, 1, 1)

            # Groupbox Blutzuckereinheit
            groupBoxBlutzuckereinheit = QGroupBox("Blutzuckereinheit")
            groupBoxBlutzuckereinheit.setFont(self.fontBold)
            blutzuckereinheitLayout = QHBoxLayout()
            self.radioButtonEinheitMg = QRadioButton(class_enums.Blutzuckereinheit.MG_DL.value)
            self.radioButtonEinheitMg.setFont(self.fontNormal)
            self.radioButtonEinheitMg.clicked.connect(self.radioButtonEinheitClicked)
            self.radioButtonEinheitMmol = QRadioButton(class_enums.Blutzuckereinheit.MMOL_L.value)
            self.radioButtonEinheitMmol.setFont(self.fontNormal)
            self.radioButtonEinheitMmol.clicked.connect(self.radioButtonEinheitClicked)
            if self.blutzuckereinheit == class_enums.Blutzuckereinheit.MG_DL:
                self.radioButtonEinheitMg.setChecked(True)
            else:
                self.radioButtonEinheitMmol.setChecked(True)
            self.checkBoxUmrechnen = QCheckBox("Textfeldinhalte umrechnen")
            self.checkBoxUmrechnen.setFont(self.fontNormal)
            groupBoxBlutzuckereinheit.setLayout(blutzuckereinheitLayout)
            blutzuckereinheitLayout.addWidget(self.radioButtonEinheitMg)
            blutzuckereinheitLayout.addWidget(self.radioButtonEinheitMmol)
            blutzuckereinheitLayout.addWidget(self.checkBoxUmrechnen)

            # Buttons
            buttonLayout = QGridLayout()
            buttonLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.pushButtonVorschau = QPushButton("Vorschau")
            self.pushButtonVorschau.setFixedSize(QSize(200, 40))
            self.pushButtonVorschau.clicked.connect(self.pushButtonVorschauClicked) # type: ignore
            self.pushButtonSenden = QPushButton("Plan senden")
            self.pushButtonSenden.setFixedSize(QSize(200, 40))
            self.pushButtonSenden.setEnabled(False)
            self.pushButtonSenden.clicked.connect(self.pushButtonSendenClicked) # type: ignore
            self.pushButtonVorlageSpeichern = QPushButton("Als Vorlage speichern...")
            self.pushButtonVorlageSpeichern.setFixedSize(200,40)
            self.pushButtonVorlageSpeichern.clicked.connect(self.pushButtonVorlageSpeichernClicked) # type: ignore
            buttonLayout.addWidget(self.pushButtonVorschau, 0, 0)
            buttonLayout.addWidget(self.pushButtonSenden, 0, 1)
            buttonLayout.addWidget(self.pushButtonVorlageSpeichern, 1, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)

            # Groupbox PatientIn
            patientLayout = QGridLayout()
            groupBoxPatient = QGroupBox("PatientIn")
            groupBoxPatient.setFont(self.fontBold)
            labelVorname = QLabel("Vorname")
            labelVorname.setFont(self.fontNormal)
            labelNachname = QLabel("Nachname")
            labelNachname.setFont(self.fontNormal)
            self.lineEditVorname = QLineEdit(self.vorname)
            self.lineEditVorname.setFont(self.fontNormal)
            self.lineEditVorname.setReadOnly(True)
            self.lineEditNachname = QLineEdit(self.nachname)
            self.lineEditNachname.setFont(self.fontNormal)
            self.lineEditNachname.setReadOnly(True)
            labelGebDat = QLabel("Geburtsdatum")
            labelGebDat.setFont(self.fontNormal)
            labelPatId = QLabel("Pat.-ID")
            labelPatId.setFont(self.fontNormal)
            self.lineEditGebdat = QLineEdit(self.gebdat)
            self.lineEditGebdat.setFont(self.fontNormal)
            self.lineEditGebdat.setReadOnly(True)
            self.lineEditPatId = QLineEdit(self.patId)
            self.lineEditPatId.setFont(self.fontNormal)
            self.lineEditPatId.setReadOnly(True)
            patientLayout.addWidget(labelVorname, 0, 0)
            patientLayout.addWidget(labelNachname, 0, 1)
            patientLayout.addWidget(self.lineEditVorname, 1, 0)
            patientLayout.addWidget(self.lineEditNachname, 1, 1)
            patientLayout.addWidget(labelGebDat, 2, 0)
            patientLayout.addWidget(labelPatId, 2, 1)
            patientLayout.addWidget(self.lineEditGebdat, 3, 0)
            patientLayout.addWidget(self.lineEditPatId, 3, 1)
            groupBoxPatient.setLayout(patientLayout)

            # Vorschau
            vorschauLayout = QVBoxLayout()
            groupBoxVorschau = QGroupBox("Vorschau")
            groupBoxVorschau.setFont(self.fontBold)
            groupBoxVorschau.setMinimumWidth(600)
            self.textEditVorschau = QTextEdit()
            self.textEditVorschau.setFont(self.fontNormal)
            vorschauLayout.addWidget(self.textEditVorschau)
            groupBoxVorschau.setLayout(vorschauLayout)
            
            mainLayoutLinkeSpalte.addWidget(self.pushButtonVorausgefuellt)
            mainLayoutLinkeSpalte.addSpacing(10)
            mainLayoutLinkeSpalte.addWidget(groupBoxBerechnungsparameter)
            mainLayoutLinkeSpalte.addWidget(groupBoxMahlzeiteninsulin)
            mainLayoutLinkeSpalte.addWidget(groupBoxBasalinsulin)
            mainLayoutLinkeSpalte.addWidget(groupBoxBlutzuckereinheit)
            mainLayoutLinkeSpalte.addLayout(buttonLayout)
            mainLayoutLinkeSpalte.addWidget(groupBoxPatient)
            mainLayoutRechteSpalte.addWidget(groupBoxVorschau)

            mainSpaltenlayout.addLayout(mainLayoutLinkeSpalte)
            mainSpaltenlayout.addLayout(mainLayoutRechteSpalte)

            # Statusleiste
            self.statusleiste = QStatusBar()
            self.statusleiste.setFont(self.fontKlein)
            mainLayoutLinkeSpalte.addWidget(self.statusleiste)

            ## Nur mit Lizenz
            if self.addOnsFreigeschaltet and gdttoolsL.GdtToolsLizenzschluessel.getSoftwareId(self.lizenzschluessel) == gdttoolsL.SoftwareId.INSUGDTPSEUDO:
                mainLayoutV.addWidget(self.labelPseudolizenz, alignment=Qt.AlignmentFlag.AlignCenter)
            ## /Nur mit Lizenz

            mainLayoutV.addLayout(mainSpaltenlayout)
            ## Nur mit Lizenz
            if self.addOnsFreigeschaltet:
                gueltigeLizenztage = gdttoolsL.GdtToolsLizenzschluessel.nochTageGueltig(self.lizenzschluessel)
                if gueltigeLizenztage  > 0 and gueltigeLizenztage <= 30:
                    labelLizenzLaeuftAus = QLabel("Die genutzte Lizenz ist noch " + str(gueltigeLizenztage) + " Tage gültig.")
                    labelLizenzLaeuftAus.setStyleSheet("color:rgb(200,0,0)")
                    mainLayoutV.addWidget(labelLizenzLaeuftAus, alignment=Qt.AlignmentFlag.AlignCenter)
            else:
                self.pushButtonSenden.setEnabled(False)
                self.pushButtonSenden.setText("Keine gültige Lizenz")
            ## /Nur mit Lizenz
            self.widget.setLayout(mainLayoutV)
            self.setCentralWidget(self.widget)
            logger.logger.info("Eingabeformular aufgebaut")

            #Menü
            menubar = self.menuBar()
            anwendungMenu = menubar.addMenu("")
            aboutAction = QAction(self)
            aboutAction.setMenuRole(QAction.MenuRole.AboutRole)
            aboutAction.triggered.connect(self.ueberInsuGdt) 
            aboutAction.setShortcut(QKeySequence("Ctrl+Ü"))
            updateAction = QAction("Auf Update prüfen", self)
            updateAction.setMenuRole(QAction.MenuRole.ApplicationSpecificRole)
            updateAction.triggered.connect(self.updatePruefung) 
            updateAction.setShortcut(QKeySequence("Ctrl+U"))
            vorlagenMenu = menubar.addMenu("Vorlagen")
            i = 0
            vorlagenMenuAction = []
            for vorlage in self.vorlagen:
                vorlagenMenuAction.append(QAction(vorlage, self))
                vorlagenMenuAction[i].triggered.connect(lambda checked=False, name=vorlage: self.vorlagenMenu(checked, name))
                i += 1
            vorlagenMenuVorlagenVerwaltenAction = QAction("Vorlagen verwalten...", self)
            vorlagenMenuVorlagenVerwaltenAction.setShortcut(QKeySequence("Ctrl+T"))
            vorlagenMenuVorlagenVerwaltenAction.triggered.connect(self.vorlagenMenuVorlagenVerwalten)
            einstellungenMenu = menubar.addMenu("Einstellungen")
            einstellungenAllgemeinAction = QAction("Allgemeine Einstellungen", self)
            einstellungenAllgemeinAction.triggered.connect(lambda checked = False, neustartfrage = True: self.einstellungenAllgemein(checked, neustartfrage))
            einstellungenAllgemeinAction.setShortcut(QKeySequence("Ctrl+E"))
            einstellungenGdtAction = QAction("GDT-Einstellungen", self)
            einstellungenGdtAction.triggered.connect(lambda checked = False, neustartfrage = True: self.einstellungenGdt(checked, neustartfrage)) 
            einstellungenGdtAction.setShortcut(QKeySequence("Ctrl+G"))
            ## Nur mit Lizenz
            einstellungenErweiterungenAction = QAction("LANR/Lizenzschlüssel", self)
            einstellungenErweiterungenAction.triggered.connect(lambda checked = False, neustartfrage = True: self.einstellungenLanrLizenzschluessel(checked, neustartfrage))
            einstellungenErweiterungenAction.setShortcut(QKeySequence("Ctrl+L"))
            einstellungenImportExportAction = QAction("Im- /Exportieren", self)
            einstellungenImportExportAction.triggered.connect(self.einstellungenImportExport)
            einstellungenImportExportAction.setShortcut(QKeySequence("Ctrl+I"))
            einstellungenImportExportAction.setMenuRole(QAction.MenuRole.NoRole)
            ## /Nur mit Lizenz
            hilfeMenu = menubar.addMenu("Hilfe")
            hilfeWikiAction = QAction("InsuGDT Wiki", self)
            hilfeWikiAction.triggered.connect(self.insugdtWiki)
            hilfeWikiAction.setShortcut(QKeySequence("Ctrl+W"))
            hilfeUpdateAction = QAction("Auf Update prüfen", self)
            hilfeUpdateAction.triggered.connect(self.updatePruefung)
            hilfeUpdateAction.setShortcut(QKeySequence("Ctrl+U"))
            hilfeAutoUpdateAction = QAction("Automatisch auf Update prüfen", self)
            hilfeAutoUpdateAction.setCheckable(True)
            hilfeAutoUpdateAction.setChecked(self.autoupdate)
            hilfeAutoUpdateAction.triggered.connect(self.autoUpdatePruefung)
            hilfeUeberAction = QAction("Über InsuGDT", self)
            hilfeUeberAction.setMenuRole(QAction.MenuRole.NoRole)
            hilfeUeberAction.triggered.connect(self.ueberInsuGdt)
            hilfeUeberAction.setShortcut(QKeySequence("Ctrl+Ü"))
            hilfeEulaAction = QAction("Lizenzvereinbarung (EULA)", self)
            hilfeEulaAction.triggered.connect(self.eula) 
            hilfeLogExportieren = QAction("Log-Verzeichnis exportieren", self)
            hilfeLogExportieren.triggered.connect(self.logExportieren)
            hilfeLogExportieren.setShortcut(QKeySequence("Ctrl+D"))
            
            anwendungMenu.addAction(aboutAction)
            anwendungMenu.addAction(updateAction)
            for i in range(len(vorlagenMenuAction)):
                vorlagenMenu.addAction(vorlagenMenuAction[i])
            vorlagenMenu.addSeparator()
            vorlagenMenu.addAction(vorlagenMenuVorlagenVerwaltenAction)

            einstellungenMenu.addAction(einstellungenAllgemeinAction)
            einstellungenMenu.addAction(einstellungenGdtAction)
            ## Nur mit Lizenz
            einstellungenMenu.addAction(einstellungenErweiterungenAction)
            einstellungenMenu.addAction(einstellungenImportExportAction)
            ## /Nur mit Lizenz
            hilfeMenu.addAction(hilfeWikiAction)
            hilfeMenu.addSeparator()
            hilfeMenu.addAction(hilfeUpdateAction)
            hilfeMenu.addAction(hilfeAutoUpdateAction)
            hilfeMenu.addSeparator()
            hilfeMenu.addAction(hilfeUeberAction)
            hilfeMenu.addAction(hilfeEulaAction)
            hilfeMenu.addSeparator()
            hilfeMenu.addAction(hilfeLogExportieren)

            # Updateprüfung auf Github
            if self.autoupdate:
                try:
                    self.updatePruefung(meldungNurWennUpdateVerfuegbar=True)
                except Exception as e:
                    mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InsuGDT", "Updateprüfung nicht möglich.\nBitte überprüfen Sie Ihre Internetverbindung.", QMessageBox.StandardButton.Ok)
                    mb.exec()
                    logger.logger.warning("Updateprüfung nicht möglich: " + str(e))

            # Formular ggf. vor-ausfüllen
            pfad = ""
            if self.vorherigeDokuLaden:
                datum = str(self.mitVorherigemPlanAusfuellen())
                if datum != "None":
                    self.pushButtonVorausgefuellt.setText("Formular ausgefüllt mit letzter Dokumentation vom " + datum[6:8] + "." + datum[4:6] + "." + datum[:4])
                    self.pushButtonVorausgefuellt.setToolTip("Vorherige Dokumentation wiederherstellen")
                    pfad = os.path.join(self.dokuVerzeichnis, self.patId, datum + "_" + self.patId + ".igv")
            if self.defaultXml != "" and pfad == "":
                self.setPreFormularXml(os.path.join(basedir, self.vorlagenverzeichnis, self.defaultXml))
                self.pushButtonVorausgefuellt.setText("Formular ausgefüllt mit Standardvorlage: " + self.defaultXml[:-4])
                self.pushButtonVorausgefuellt.setToolTip("Standardvorlage wiederherstellen")
                pfad = os.path.join(basedir, self.vorlagenverzeichnis, self.defaultXml)
            if pfad != "":
                self.pushButtonVorausgefuellt.setText(self.pushButtonVorausgefuellt.text() + "\n(Zum Wiederherstellen anklicken)")
                self.pushButtonVorausgefuellt.clicked.connect(lambda checked=False, pfad=pfad: self.pushButtonVorausgefuelltClicked(checked, pfad))
            else:
                self.pushButtonVorausgefuellt.setVisible(False)

        else:
            sys.exit()

    def pushButtonVorausgefuelltClicked(self, checked, pfad):
        self.setPreFormularXml(pfad)

    def radioButtonEinheitClicked(self):
        umrechenfaktor = 1
        if self.radioButtonEinheitMg.isChecked():
            if self.checkBoxUmrechnen.isChecked() and self.blutzuckereinheit == class_enums.Blutzuckereinheit.MMOL_L:
                umrechenfaktor = 1 / 0.0555
            self.blutzuckereinheit = class_enums.Blutzuckereinheit.MG_DL
        else:
            if self.checkBoxUmrechnen.isChecked() and self.blutzuckereinheit == class_enums.Blutzuckereinheit.MG_DL:
                umrechenfaktor = 0.0555
            self.blutzuckereinheit = class_enums.Blutzuckereinheit.MMOL_L
        # Einheiten setzen
        self.labelEinheitBlutuckerziel.setText(self.blutzuckereinheit.value)
        self.labelEinheitKorrektur.setText(self.blutzuckereinheit.value)
        self.labelEinheitUntersteBereichsstufe.setText(self.blutzuckereinheit.value)
        self.labelEinheitBereichsstufengroesse.setText(self.blutzuckereinheit.value)

        # Umrechnen
        if self.checkBoxUmrechnen.isChecked():
            lineEdits = [self.lineEditBlutzuckerziel, self.lineEditKorrektur, self.lineEditUntersteBereichsstufe, self.lineEditBereichsstufengroesse]
            for le in lineEdits:
                try:
                    aktWert = float(le.text().replace(",", "."))
                    if self.radioButtonEinheitMg.isChecked():
                        neuWert = "{:.0f}".format(aktWert * umrechenfaktor)
                        le.setText(str(neuWert))
                    else:
                        neuWert = "{:.2f}".format(aktWert * umrechenfaktor)
                        le.setText(str(neuWert).replace(".", ","))
                except:
                    pass
    
    def mitVorherigemPlanAusfuellen(self):
        pfad = self.dokuVerzeichnis + os.sep+ self.patId
        if os.path.exists(self.dokuVerzeichnis):
            if os.path.exists(pfad) and len(os.listdir(pfad)) > 0:
                dokus = [d for d in os.listdir(pfad) if os.path.isfile(pfad + os.sep + d)]
                dokus.sort()
                # Ältere Dokus löschen
                if len(dokus) > 3:
                    for i in range(0, len(dokus) - 3):
                        try:
                            os.unlink(os.path.join(pfad, dokus[i]))
                            logger.logger.info("Dokufile " + os.path.join(pfad, dokus[i]) + " gelöscht")
                        except Exception as e:
                            logger.logger.warning("Fehler beim Löschen von Dokufile " + os.path.join(pfad, dokus[i]) + ": " + str(e))
                try:
                    self.setPreFormularXml(os.path.join(self.vorlagenverzeichnis, pfad, dokus[len(dokus) - 1]), True)
                    return dokus[len(dokus) - 1][:8]
                except Exception as e:
                    mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InsuGDT", "Fehler beim Lesen der vorherigen Dokumentation.\nSoll InsuGDT neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                    mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                    mb.button(QMessageBox.StandardButton.No).setText("Nein")
                    if mb.exec() == QMessageBox.StandardButton.Yes:
                        os.execl(sys.executable, __file__, *sys.argv)
        else:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InsuGDT", "Das Archivierungsverzeichnis " + self.dokuVerzeichnis + "  ist nicht erreichbar. Vorherige Insulinspritzpläne können daher nicht geladen werden.\nFalls es sich um eine Netzwerkfreigabe handeln sollte, stellen Sie die entsprechende Verbindung sicher und starten InsuGDT neu.\nSoll InsuGDT neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.setDefaultButton(QMessageBox.StandardButton.Yes)
            mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
            mb.button(QMessageBox.StandardButton.No).setText("Nein")
            if mb.exec() == QMessageBox.StandardButton.Yes:
                os.execl(sys.executable, __file__, *sys.argv)  

    def setStatusMessage(self, message = ""):
        self.statusleiste.clearMessage()
        if message != "":
            self.statusleiste.showMessage("Statusmeldung: " + message)
            logger.logger.info("Statusmessage: " + message)

    def pushButtonPlanSendenDisable(self):
        self.pushButtonSenden.setEnabled(False)
    
    def formularPruefen(self):
        """
        Prüft das Eingabeformular auf Formfehler und gibt eine String-Liste mit Fehlern zurück
        Return:
            fehler: list
        """
        kommazahlPattern = r"^\d+([,.]\d+)?$"
        befaktorPattern = r"^\d([.,]\d{1,2})?$"
        zahlPattern = r"^\d+$"
        fehler = []
        if re.match(kommazahlPattern, self.lineEditBlutzuckerziel.text()) == None:
            fehler.append("Blutzuckerziel ungültig")
        if re.match(kommazahlPattern, self.lineEditKorrektur.text())== None:
            fehler.append("Korrektur ungültig")
        for i in range(3):
            if re.match(befaktorPattern, str(self.doubleSpinBoxBeFaktoren[i].value())) == None:
                fehler.append("BE-Faktoren ungültig")
                break
        for i in range(3):
            if re.match(zahlPattern, self.lineEditDefaultInsulin[i].text()) == None:
                fehler.append("Insulindosen bei normalem Blutzucker ungültig")
                break
        if re.match(zahlPattern, self.lineEditAnzahlBlutzuckerbereichsstufen.text()) == None:
            fehler.append("Anzahl Bereichsstufen ungültig")
        if re.match(kommazahlPattern, self.lineEditUntersteBereichsstufe.text()) == None:
            fehler.append("Unterste Bereichsstufe ungültig")
        if re.match(kommazahlPattern, self.lineEditBereichsstufengroesse.text()) == None:
            fehler.append("Bereichsstufengröße ungültig")
        if self.lineEditMiName.text() == "":
            fehler.append("Kein Mahlzeiteninsulinnahme eingetragen")
        if self.lineEditBiName.text() == "":
            fehler.append("Kein Basalinsulinnahme eingetragen")
        if re.match(zahlPattern, self.lineEditBiDosis.text()) == None:
            fehler.append("Basalinsulindosis ungültig")
        return fehler
    
    def pushButtonVorlageSpeichernClicked(self):
        FILTER = ["IGV-Dateien (*.igv)", "Alle Dateien (*:*)"]
        filter = ";;".join(FILTER)
        dateiname, filter = QFileDialog.getSaveFileName(self, "Vorlage speichern", self.vorlagenverzeichnis, filter, FILTER[0])
        if dateiname:
            insulinplanElement = self.getInsulinplanXml()
            et = ElementTree.ElementTree(insulinplanElement)
            ElementTree.indent(et)
            try:
                et.write(dateiname, "utf-8", True)
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von InsuGDT", "Damit die Vorlage in die Menüleiste übernommen wird, muss InsuGDT neu gestartet werden.\nSoll InsuGDT jetzt neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    os.execl(sys.executable, __file__, *sys.argv)
            except Exception as e:
                self.setStatusMessage("Fehler beim Speichern der Vorlage: " + e.args[1])
                logger.logger.error("Fehler beim Speichern der Vorlage " + dateiname) 
    
    def getInsulinplanXml(self):
        insulinplanElement = ElementTree.Element("insulinplan")
        berechnungsparameterElement = ElementTree.Element("berechnungsparameter")
        blutzuckerzielElement = ElementTree.Element("blutzuckerziel")
        blutzuckerzielElement.text = self.lineEditBlutzuckerziel.text()
        korrekturElement = ElementTree.Element("korrektur")
        korrekturElement.text = self.lineEditKorrektur.text()
        einheitElement = ElementTree.Element("einheit")
        einheitElement.text = self.blutzuckereinheit.value
        befaktorenElement = ElementTree.Element("befaktoren")
        morgensElement = ElementTree.Element("morgens")
        morgensElement.text = str(self.doubleSpinBoxBeFaktoren[0].value()).replace(",", ".")
        mittagsElement = ElementTree.Element("mittags")
        mittagsElement.text = str(self.doubleSpinBoxBeFaktoren[1].value()).replace(",", ".")
        abendsElement = ElementTree.Element("abends")
        abendsElement.text = str(self.doubleSpinBoxBeFaktoren[2].value()).replace(",", ".")
        defaultInsulinElement = ElementTree.Element("defaultinsulin")
        morgensElementInsulin = ElementTree.Element("morgens")
        morgensElementInsulin.text = self.lineEditDefaultInsulin[0].text()
        mittagsElementInsulin = ElementTree.Element("mittags")
        mittagsElementInsulin.text = self.lineEditDefaultInsulin[1].text()
        abendsElementInsulin = ElementTree.Element("abends")
        abendsElementInsulin.text = self.lineEditDefaultInsulin[2].text()
        anzahlblutzuckerbereichsstufenElement = ElementTree.Element("anzahlblutzuckerbereichsstufen")
        anzahlblutzuckerbereichsstufenElement.text = self.lineEditAnzahlBlutzuckerbereichsstufen.text()
        untersteblutzuckerstufeElement = ElementTree.Element("untersteblutzuckerstufe")
        untersteblutzuckerstufeElement.text = self.lineEditUntersteBereichsstufe.text()
        bereichsstufengroesseElement = ElementTree.Element("bereichsstuferngroesse")
        bereichsstufengroesseElement.text = self.lineEditBereichsstufengroesse.text()
        befaktorenElement.append(morgensElement)
        befaktorenElement.append(mittagsElement)
        befaktorenElement.append(abendsElement)
        defaultInsulinElement.append(morgensElementInsulin)
        defaultInsulinElement.append(mittagsElementInsulin)
        defaultInsulinElement.append(abendsElementInsulin)
        berechnungsparameterElement.append(blutzuckerzielElement)
        berechnungsparameterElement.append(korrekturElement)
        berechnungsparameterElement.append(einheitElement)
        berechnungsparameterElement.append(befaktorenElement)
        berechnungsparameterElement.append(defaultInsulinElement)
        berechnungsparameterElement.append(anzahlblutzuckerbereichsstufenElement)
        berechnungsparameterElement.append(untersteblutzuckerstufeElement)
        berechnungsparameterElement.append(bereichsstufengroesseElement)
        mahlzeiteninsulinElement = ElementTree.Element("mahlzeiteninsulin")
        nameMElement = ElementTree.Element("name")
        nameMElement.text = self.lineEditMiName.text()
        basalinsulinElement = ElementTree.Element("basalinsulin")
        nameBElement = ElementTree.Element("name")
        nameBElement.text = self.lineEditBiName.text()
        dosisElement = ElementTree.Element("dosis")
        dosisElement.text = self.lineEditBiDosis.text()
        verabreichungsintervallElement = ElementTree.Element("verabreichungsintervall")
        verabreichungsintervallElement.text = self.comboBoxVerabreichung.currentText()
        moMiAbElement = ElementTree.Element("momiab")
        if self.radioButtonMorgens.isChecked():
            moMiAbElement.text = "morgens"
        elif self.radioButtonMittags.isChecked():
            moMiAbElement.text = "mittags"
        else:
            moMiAbElement.text = "abends"
        mahlzeiteninsulinElement.append(nameMElement)
        basalinsulinElement.append(nameBElement)
        basalinsulinElement.append(dosisElement)
        basalinsulinElement.append(verabreichungsintervallElement)
        basalinsulinElement.append(moMiAbElement)
        insulinplanElement.append(berechnungsparameterElement)
        insulinplanElement.append(mahlzeiteninsulinElement)
        insulinplanElement.append(basalinsulinElement)
        return insulinplanElement

    def getInsulinplan(self):
        blutzuckerziel = float(self.lineEditBlutzuckerziel.text().replace(",", "."))
        befaktoren = []
        for i in range(3):
            befaktoren.append(self.doubleSpinBoxBeFaktoren[i].value())
        defaultinsulinmengen = []
        for i in range(3):
            defaultinsulinmengen.append(float(self.lineEditDefaultInsulin[i].text()))
        korrektur = float(self.lineEditKorrektur.text().replace(",", "."))
        einheit = self.blutzuckereinheit
        anzahlBereichsstufen = int(self.lineEditAnzahlBlutzuckerbereichsstufen.text())
        untersteBereichsstufe = float(self.lineEditUntersteBereichsstufe.text().replace(",", "."))
        stufengroesse = float(self.lineEditBereichsstufengroesse.text().replace(",", "."))
        insulinplan = class_insulinplan.Insulinplan(blutzuckerziel, befaktoren, korrektur, einheit)
        insulinplan.setDefaultInsulinEinheiten(defaultinsulinmengen)
        insulinplan.setAnzahlStufen(anzahlBereichsstufen)
        insulinplan.setUntersteStufe(untersteBereichsstufe)
        insulinplan.setStufengroesse(stufengroesse)
        insulinplan.setMiName(self.lineEditMiName.text())
        insulinplan.setBiName(self.lineEditBiName.text())
        insulinplan.setBiDosis(int(self.lineEditBiDosis.text()))
        insulinplan.setBiVerabreichungsintervall(class_enums.Verabreichungsintervall(self.comboBoxVerabreichung.currentText()))
        if self.radioButtonMorgens.isChecked():
            insulinplan.setMoMiAb(class_enums.MoMiAb.MORGENS)
        elif self.radioButtonMittags.isChecked():
            insulinplan.setMoMiAb(class_enums.MoMiAb.MITTAGS)
        else:
            insulinplan.setMoMiAb(class_enums.MoMiAb.ABENDS)
        return insulinplan
    
    def pushButtonVorschauClicked(self):
        self.textEditVorschau.clear()
        fehler = self.formularPruefen()
        if len(fehler) != 0:
            text = ""
            for f in fehler:
                text += "\u26a0" + " " + f + "<br />"
            html = "<span style='font-weight:normal;color:rgb(200,0,0)'>" + text + "</span>"
            self.textEditVorschau.setHtml(html)
        else:
            insulinplan = self.getInsulinplan()
            if len(insulinplan.getZeilen()) > 0:
                text = "<style>table.insulinplan { margin-top:6px;border-collapse:collapse } table.insulinplan td { padding:2px;border:1px solid rgb(0,0,0);font-weight:normal; } table.insulinplan td.zentriert { padding:2px;border:1px solid rgb(0,0,0);font-weight:normal;text-align:center }</style>"
                text += "<div style='font-weight:bold;text-align:center'>Insulinspritzplan:</div>"
                intervall = insulinplan.getBiVerabreichungsintervall().value 
                if intervall[-1] == "s":
                    intervall = intervall[:-1]
                elif intervall == "täglich":
                    intervall += " "
                text += "<div style='text-align:left;margin-top:20px'><b>Basalinsulin:</b><br />" + self.lineEditBiName.text() + ": " + self.lineEditBiDosis.text() + " IE " + intervall + insulinplan.getMoMiAb().value + "</div>"
                text += "<div style='text-align:left;margin-top:20px'><b>Mahlzeiteninsulin:</b><br />" + self.lineEditMiName.text() + " (siehe Tabelle):</div>"
                text += "<table class='insulinplan'>"
                text += "<tr><td><b>Blutzucker</b></td><td class='zentriert'><b>Morgens [IE]</b></td><td class='zentriert'><b>Mittags [IE]</b></td><td class='zentriert'><b>Abends [IE]</b></td><td><b style='font-style:italic'>Summe [IE]<sup>*</sup></i></td></tr>"
                for zeile in insulinplan.getZeilen():
                    text += "<tr><td>" + zeile[0] + "</td><td class='zentriert'>" + str(zeile[1][0]).replace(".", ",") + "</td><td class='zentriert'>" + str(zeile[1][1]).replace(".", ",") + "</td><td class='zentriert'>" + str(zeile[1][2]).replace(".", ",") + "</td><td class='zentriert'><i>" + str(zeile[2]) + "</i></td></tr>"
                text += "</table>"
                text += "<br /><sup>*</sup> Erscheint nicht auf dem Ausdruck"
                
                self.textEditVorschau.clear()
                self.textEditVorschau.setHtml(text)
                self.pushButtonSenden.setEnabled(True)

    def pushButtonSendenClicked(self):
        untdatDatetime = datetime.datetime.now()
        fehler = self.formularPruefen()
        if len(fehler) == 0:
            insulinplan = self.getInsulinplan()
            # PDF erstellen
            pdf = FPDF()
            logger.logger.info("FPDF-Instanz erzeugt")
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 20)
            pdf.cell(0, 10, "Insulinspritzplan", align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 14)
            pdf.cell(0, 10, "für " + self.vorname + " " + self.nachname + " (*" + self.gebdat + ")", align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            erstelltAmText = "Erstellt am " + untdatDatetime.strftime("%d.%m.%Y")
            if self.configIni["Allgemein"]["einrichtungaufpdf"] == "1":
                erstelltAmText += " von " + self.configIni["Allgemein"]["einrichtungsname"]
            pdf.cell(0,6, erstelltAmText, align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 14)
            pdf.cell(0, 10, "", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 0, "Basalinsulin", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 12)
            intervall = insulinplan.getBiVerabreichungsintervall().value 
            if intervall[-1] == "s":
                intervall = intervall[:-1]
            elif intervall == "täglich":
                    intervall += " "
            pdf.cell(0, 10, insulinplan.getBiName() + ": " + str(insulinplan.getBiDosis()) + " IE " + intervall + insulinplan.getMoMiAb().value)
            pdf.cell(0, 14, "", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 10, "Mahlzeiteninsulin", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 12)
            pdf.cell(0, 0, insulinplan.getMiName() + " (siehe Tabelle):", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, "", new_x="LMARGIN", new_y="NEXT")
            titelzeile = ["Blutzucker [" + self.blutzuckereinheit.value + "]", "Morgens [IE]", "Mittags [IE]", "Abends [IE]"]
            colWidths = (25,25,25,25)
            with pdf.table(v_align=enums.VAlign.T, line_height=2 * pdf.font_size, cell_fill_color=(230,230,230), cell_fill_mode="ROWS", col_widths=colWidths) as table: # type: ignore
                pdf.set_font("Helvetica", "", 12)
                row = table.row()
                i = 0
                for titel in titelzeile:
                    if i == 0:
                        row.cell(text=titel)
                    else:
                        row.cell(text=titel, align="C")
                    i += 1
                for zeile in insulinplan.getZeilen():
                    row = table.row()
                    row.cell(text=zeile[0])
                    for i in range(3):
                        row.cell(text=str(zeile[1][i]), align="C")
            pdf.set_y(-30)
            pdf.set_font("Helvetica", "I", 10)
            pdf.cell(0, 10, "Generiert von InsuGDT V" + self.version + " (\u00a9 GDT-Tools " + str(datetime.date.today().year) + ")", align="R")
            logger.logger.info("PDF-Seite aufgebaut")
            if self.configIni["Allgemein"]["pdferstellen"] == "1":
                try:
                    pdf.output(os.path.join(basedir, "pdf/insulinspritzplan_temp.pdf"))
                    logger.logger.info("PDF-Output nach " + os.path.join(basedir, "pdf/insulinspritzplan_temp.pdf") + " erfolgreich")
                    self.setStatusMessage("PDF-Datei erstellt")
                except Exception as e:
                    self.setStatusMessage("Fehler bei PDF-Datei-Erstellung: " + e.args[1])
                    logger.logger.error("Fehler bei PDF-Erstellung nach " + os.path.join(basedir, "pdf/insulinplan_temp.pdf"))
            
            # GDT-Datei erzeugen
            sh = gdt.SatzHeader(gdt.Satzart.DATEN_EINER_UNTERSUCHUNG_UEBERMITTELN_6310, self.configIni["GDT"]["idpraxisedv"], self.configIni["GDT"]["idinsugdt"], self.zeichensatz, "2.10", "Fabian Treusch - GDT-Tools", "InsuGDT", self.version, self.patId)
            gd = gdt.GdtDatei()
            logger.logger.info("GdtDatei-Instanz erzeugt")
            gd.erzeugeGdtDatei(sh.getSatzheader())
            logger.logger.info("Satzheader 6310 erzeugt")
            gd.addZeile("6200", untdatDatetime.strftime("%d%m%Y"))
            gd.addZeile("6201", untdatDatetime.strftime("%H%M%S"))
            gd.addZeile("8402", "ALLG01")
            # PDF hinzufügen
            if self.configIni["Allgemein"]["pdferstellen"] == "1" and (gdttoolsL.GdtToolsLizenzschluessel.lizenzErteilt(self.lizenzschluessel, self.lanr, gdttoolsL.SoftwareId.INSUGDT) or gdttoolsL.GdtToolsLizenzschluessel.lizenzErteilt(self.lizenzschluessel, self.lanr, gdttoolsL.SoftwareId.INSUGDTPSEUDO)):
                gd.addZeile("6302", "insulinspritzplan")
                gd.addZeile("6303", "pdf")
                gd.addZeile("6304", self.configIni["Allgemein"]["pdfbezeichnung"])
                gd.addZeile("6305", os.path.join(basedir, "pdf/insulinspritzplan_temp.pdf"))
            gd.addZeile("6220", "Insulinspritzplan")
            intervall = insulinplan.getBiVerabreichungsintervall().value 
            if intervall[-1] == "s":
                intervall = intervall[:-1]
            elif intervall == "täglich":
                    intervall += " "
            gd.addZeile("6228", "Basalinsulin: " + insulinplan.getBiName() + ": " + str(insulinplan.getBiDosis()) + " IE " + intervall + insulinplan.getMoMiAb().value)
            gd.addZeile("6228", "Mahlzeiteninsulin: " + insulinplan.getMiName() + " (siehe Tabelle):")
            space = "          "
            gd.addZeile("6228", "Blutzucker [" + self.blutzuckereinheit.value + "]" + space + "Morgens [IE]" + space + "Mittags [IE]" + space + "Abends [IE]")
            for zeile in insulinplan.getZeilen():
                befundzeile = zeile[0]
                for i in range(3):
                    befundzeile += space + str(zeile[1][i])
                gd.addZeile("6228", befundzeile)
            # GDT-Datei exportieren
            if not gd.speichern(self.gdtExportVerzeichnis + "/" + self.kuerzelpraxisedv + self.kuerzelinsugdt + ".gdt", self.zeichensatz):
                logger.logger.error("Fehler bei GDT-Dateiexport nach " + self.gdtExportVerzeichnis + "/" + self.kuerzelpraxisedv + self.kuerzelinsugdt + ".gdt")
                self.setStatusMessage("Fehler beim GDT-Export")
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InsuGDT", "GDT-Export nicht möglich.\nBitte überprüfen Sie die Angabe des Exportverzeichnisses.", QMessageBox.StandardButton.Ok)
                mb.exec()
            else:    
                self.setStatusMessage("GDT-Export erfolgreich")
                logger.logger.info("GDT-Datei " + self.gdtExportVerzeichnis + "/" + self.kuerzelpraxisedv + self.kuerzelinsugdt + ".gdt gespeichert")
                if self.dokuVerzeichnis != "":
                    if os.path.exists(self.dokuVerzeichnis):
                        speicherdatum = untdatDatetime.strftime("%Y%m%d")
                        if not os.path.exists(self.dokuVerzeichnis + os.sep + self.patId):
                            os.mkdir(self.dokuVerzeichnis + os.sep + self.patId, 0o777)
                            logger.logger.info("Dokuverzeichnis für PatId " + self.patId + " erstellt")
                        insulinplanElement = self.getInsulinplanXml()
                        et = ElementTree.ElementTree(insulinplanElement)
                        ElementTree.indent(et)
                        try:
                            dateiname = self.dokuVerzeichnis + os.sep + self.patId + os.sep + speicherdatum + "_" + self.patId + ".igv"
                            et.write(dateiname, "utf-8", True)
                            logger.logger.info("Insulinplan für PatId " + self.patId + " archiviert")
                        except IOError as e:
                            logger.logger.error("IO-Fehler beim Archivieren des Insulinplans von PatId " + self.patId)
                            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InsuGDT", "Fehler beim Archivieren des Insulinplans\n" + str(e), QMessageBox.StandardButton.Ok)
                            mb.exec()
                        except:
                            logger.logger.error("Nicht-IO-Fehler beim Archivieren des Insulinplans von PatId " + self.patId)
                            raise
                    else:
                        logger.logger.warning("Dokuverzeichnis existiert nicht")
                        mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InsuGDT", "Archivieren der Insulinplans nicht möglich\nBitte überprüfen Sie die Angabe des Dokumentations-Speicherverzeichnisses.", QMessageBox.StandardButton.Ok)
                        mb.exec()
            sys.exit()

        else:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InsuGDT", "Der Insulinspritzplan kann nicht gesendet werden, da das Formular Fehler enthält.", QMessageBox.StandardButton.Ok)
            mb.setTextFormat(Qt.TextFormat.RichText)
            mb.exec()

    def vorlagenMenu(self, checked, name):
        self.setPreFormularXml(os.path.join(self.vorlagenverzeichnis, name + ".igv"))

    def vorlagenMenuVorlagenVerwalten(self):
        if self.vorlagenverzeichnis != "" and os.path.exists(self.vorlagenverzeichnis):
            defaultxmlkopie = self.defaultXml
            vorlagenkopie = []
            for vorlage in self.vorlagen:
                vorlagenkopie.append(vorlage)
            dv = dialogVorlagenVerwalten.VorlagenVerwalten(vorlagenkopie, defaultxmlkopie)
            if dv.exec() == 1:
                i = 0
                for neueVorlage in dv.vorlagen:
                    if neueVorlage != self.vorlagen[i] and not dv.listWidgetVorlagen.item(i).font().strikeOut():
                        os.rename(os.path.join(self.vorlagenverzeichnis, self.vorlagen[i] + ".igv"), os.path.join(self.vorlagenverzeichnis, neueVorlage + ".igv"))
                        if self.vorlagen[i] == self.defaultXml[0:-4]:
                            self.configIni["Allgemein"]["defaultxml"] = neueVorlage + ".igv"
                        self.vorlagen[i] = neueVorlage
                    elif dv.listWidgetVorlagen.item(i).font().strikeOut():
                        os.remove(os.path.join(self.vorlagenverzeichnis, self.vorlagen[i] + ".igv"))
                        if self.vorlagen[i] == self.defaultXml[0:-4]:
                            self.configIni["Allgemein"]["defaultxml"] = ""
                    i += 1
                if dv.defaultxml != self.defaultXml:
                    self.defaultXml = dv.defaultxml
                    self.configIni["Allgemein"]["defaultxml"] = dv.defaultxml
                with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                    self.configIni.write(configfile)
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von InsuGDT", "Damit die Vorlagen in der Menüleiste aktualisiert werden, muss InsuGDT neu gestartet werden.\nSoll InsuGDT jetzt neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    os.execl(sys.executable, __file__, *sys.argv)
        else:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InsuGDT", "Bitte legen Sie in den Allgemeinen Einstellungen ein gültiges Vorlagenverzeichnis an.", QMessageBox.StandardButton.Ok)
            mb.setTextFormat(Qt.TextFormat.RichText)
            mb.exec()
        
    def einstellungenAllgemein(self, checked, neustartfrage):
        de = dialogEinstellungenAllgemein.EinstellungenAllgemein(self.configPath)
        if de.exec() == 1:
            self.configIni["Allgemein"]["einrichtungsname"] = de.lineEditEinrichtungsname.text()
            if de.radioButtonBlutzuckereinheitMg.isChecked():
                self.configIni["Allgemein"]["blutzuckereinheit"] = class_enums.Blutzuckereinheit.MG_DL.value
            else: 
                self.configIni["Allgemein"]["blutzuckereinheit"] = class_enums.Blutzuckereinheit.MMOL_L.value
            self.configIni["Allgemein"]["befaktorstandardschritt"] = de.lineEditBeFaktorStandardschritt.text().replace(",", ".")
            self.configIni["Allgemein"]["dokuverzeichnis"] = de.lineEditArchivierungsverzeichnis.text()
            self.configIni["Allgemein"]["vorherigedokuladen"] = "0"
            if de.checkboxVorherigeDokuLaden.isChecked():
                self.configIni["Allgemein"]["vorherigedokuladen"] = "1"
            self.configIni["Allgemein"]["pdferstellen"] = "0"
            if de.checkboxPdfErstellen.isChecked():
                self.configIni["Allgemein"]["pdferstellen"] = "1"  
            self.configIni["Allgemein"]["pdfbezeichnung"] = de.lineEditPdfBezeichnung.text()
            self.configIni["Allgemein"]["einrichtungAufPdf"] = "0"
            if de.checkboxEinrichtungAufPdf.isChecked():
                self.configIni["Allgemein"]["einrichtungAufPdf"] = "1"
            self.configIni["Allgemein"]["vorlagenverzeichnis"] = de.lineEditVorlagenverzeichnis.text()
            self.configIni["Allgemein"]["updaterpfad"] = de.lineEditUpdaterPfad.text()
            self.configIni["Allgemein"]["autoupdate"] = str(de.checkBoxAutoUpdate.isChecked())  
            with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                self.configIni.write(configfile)
            if neustartfrage:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von InsuGDT", "Damit die Einstellungsänderungen wirksam werden, sollte InsuGDT neu gestartet werden.\nSoll InsuGDT jetzt neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    os.execl(sys.executable, __file__, *sys.argv)
        
    def einstellungenGdt(self, checked, neustartfrage):
        de = dialogEinstellungenGdt.EinstellungenGdt(self.configPath)
        if de.exec() == 1:
            self.configIni["GDT"]["idinsugdt"] = de.lineEditInsuGdtId.text()
            self.configIni["GDT"]["idpraxisedv"] = de.lineEditPraxisEdvId.text()
            self.configIni["GDT"]["gdtimportverzeichnis"] = de.lineEditImport.text()
            self.configIni["GDT"]["gdtexportverzeichnis"] = de.lineEditExport.text()
            self.configIni["GDT"]["kuerzelinsugdt"] = de.lineEditInsuGdtKuerzel.text()
            self.configIni["GDT"]["kuerzelpraxisedv"] = de.lineEditPraxisEdvKuerzel.text()
            self.configIni["GDT"]["zeichensatz"] = str(de.aktuelleZeichensatznummer + 1)
            with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                self.configIni.write(configfile)
            if neustartfrage:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von InsuGDT", "Damit die Einstellungsänderungen wirksam werden, sollte InsuGDT neu gestartet werden.\nSoll InsuGDT jetzt neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    os.execl(sys.executable, __file__, *sys.argv)
    
    ## Nur mit Lizenz
    def einstellungenLanrLizenzschluessel(self, checked, neustartfrage):
        de = dialogEinstellungenLanrLizenzschluessel.EinstellungenProgrammerweiterungen(self.configPath)
        if de.exec() == 1:
            self.configIni["Erweiterungen"]["lanr"] = de.lineEditLanr.text()
            self.configIni["Erweiterungen"]["lizenzschluessel"] = gdttoolsL.GdtToolsLizenzschluessel.krypt(de.lineEditLizenzschluessel.text())
            if de.lineEditLanr.text() == "" and de.lineEditLizenzschluessel.text() == "":
                self.configIni["Allgemein"]["pdferstellen"] = "0"
                self.configIni["Allgemein"]["einrichtungaufpdf"] = "0"
                self.configIni["Allgemein"]["pdfbezeichnung"] = "Insulinspritzplan"
            with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
                self.configIni.write(configfile)
            if neustartfrage:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von InsuGDT", "Damit die Einstellungsänderungen wirksam werden, sollte InsuGDT neu gestartet werden.\nSoll InsuGDT jetzt neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    os.execl(sys.executable, __file__, *sys.argv)

    def einstellungenImportExport(self):
        de = dialogEinstellungenImportExport.EinstellungenImportExport(self.configPath)
        if de.exec() == 1:
            pass    
    ## /Nur mit Lizenz

    def insugdtWiki(self, link):
        QDesktopServices.openUrl("https://github.com/retconx/insugdt/wiki")

    def logExportieren(self):
        if (os.path.exists(os.path.join(basedir, "log"))):
            downloadPath = ""
            if sys.platform == "win32":
                downloadPath = os.path.expanduser("~\\Downloads")
            else:
                downloadPath = os.path.expanduser("~/Downloads")
            try:
                if shutil.copytree(os.path.join(basedir, "log"), os.path.join(downloadPath, "Log_InsuGDT"), dirs_exist_ok=True):
                    shutil.make_archive(os.path.join(downloadPath, "Log_InsuGDT"), "zip", root_dir=os.path.join(downloadPath, "Log_InsuGDT"))
                    shutil.rmtree(os.path.join(downloadPath, "Log_InsuGDT"))
                    mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InsuGDT", "Das Log-Verzeichnis wurde in den Ordner " + downloadPath + " kopiert.", QMessageBox.StandardButton.Ok)
                    mb.exec()
            except Exception as e:
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InsuGDT", "Problem beim Download des Log-Verzeichnisses: " + str(e), QMessageBox.StandardButton.Ok)
                mb.exec()
        else:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InsuGDT", "Das Log-Verzeichnis wurde nicht gefunden.", QMessageBox.StandardButton.Ok)
            mb.exec() 
                
    # def updatePruefung(self, meldungNurWennUpdateVerfuegbar = False):
    #     response = requests.get("https://api.github.com/repos/retconx/insugdt/releases/latest")
    #     githubRelaseTag = response.json()["tag_name"]
    #     latestVersion = githubRelaseTag[1:] # ohne v
    #     if versionVeraltet(self.version, latestVersion):
    #         mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InsuGDT", "Die aktuellere InsuGDT-Version " + latestVersion + " ist auf <a href='https://github.com/retconx/insugdt/releases'>Github</a> verfügbar.", QMessageBox.StandardButton.Ok)
    #         mb.setTextFormat(Qt.TextFormat.RichText)
    #         mb.exec()
    #     elif not meldungNurWennUpdateVerfuegbar:
    #         mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InsuGDT", "Sie nutzen die aktuelle InsuGDT-Version.", QMessageBox.StandardButton.Ok)
    #         mb.exec()
    
    def autoUpdatePruefung(self, checked):
        self.autoupdate = checked
        self.configIni["Allgemein"]["autoupdate"] = str(checked)
        with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
            self.configIni.write(configfile)

    def updatePruefung(self, meldungNurWennUpdateVerfuegbar = False):
        logger.logger.info("Updateprüfung")
        response = requests.get("https://api.github.com/repos/retconx/insugdt/releases/latest")
        githubRelaseTag = response.json()["tag_name"]
        latestVersion = githubRelaseTag[1:] # ohne v
        if versionVeraltet(self.version, latestVersion):
            logger.logger.info("Bisher: " + self.version + ", neu: " + latestVersion)
            if os.path.exists(self.updaterpfad):
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von InsuGDT", "Die aktuellere InsuGDT-Version " + latestVersion + " ist auf Github verfügbar.\nSoll der GDT-Tools Updater geladen werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    logger.logger.info("Updater wird geladen")
                    atexit.register(self.updaterLaden)
                    sys.exit()
            else:
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InsuGDT", "Die aktuellere InsuGDT-Version " + latestVersion + " ist auf <a href='https://github.com/retconx/insugdt/releases'>Github</a> verfügbar.<br />Bitte beachten Sie auch die Möglichkeit, den Updateprozess mit dem <a href='https://github.com/retconx/gdttoolsupdater/wiki'>GDT-Tools Updater</a> zu automatisieren.", QMessageBox.StandardButton.Ok)
                mb.setTextFormat(Qt.TextFormat.RichText)
                mb.exec()
        elif not meldungNurWennUpdateVerfuegbar:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InsuGDT", "Sie nutzen die aktuelle InsuGDT-Version.", QMessageBox.StandardButton.Ok)
            mb.exec()

    def updaterLaden(self):
        sex = sys.executable
        programmverzeichnis = ""
        logger.logger.info("sys.executable: " + sex)
        if "win32" in sys.platform:
            programmverzeichnis = sex[:sex.rfind("insugdt.exe")]
        elif "darwin" in sys.platform:
            programmverzeichnis = sex[:sex.find("InsuGDT.app")]
        elif "win32" in sys.platform:
            programmverzeichnis = sex[:sex.rfind("insugdt")]
        logger.logger.info("Programmverzeichnis: " + programmverzeichnis)
        try:
            if "win32" in sys.platform:
                subprocess.Popen([self.updaterpfad, "insugdt", self.version, programmverzeichnis], creationflags=subprocess.DETACHED_PROCESS) # type: ignore
            elif "darwin" in sys.platform:
                subprocess.Popen(["open", "-a", self.updaterpfad, "--args", "insugdt", self.version, programmverzeichnis])
            elif "linux" in sys.platform:
                subprocess.Popen([self.updaterpfad, "insugdt", self.version, programmverzeichnis])
        except Exception as e:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von InsuGDT", "Der GDT-Tools Updater konnte nicht gestartet werden", QMessageBox.StandardButton.Ok)
            logger.logger.error("Fehler beim Starten des GDT-Tools Updaters: " + str(e))
            mb.exec()
    
    def ueberInsuGdt(self):
        de = dialogUeberInsuGdt.UeberInsuGdt()
        de.exec()
    
    def eula(self):
        QDesktopServices.openUrl("https://gdttools.de/Lizenzvereinbarung_InsuGDT.pdf")

app = QApplication(sys.argv)
qt = QTranslator()
filename = "qtbase_de"
directory = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
qt.load(filename, directory)
app.installTranslator(qt)
app.setWindowIcon(QIcon(os.path.join(basedir, "icons", "program.png")))
window = MainWindow()
window.show()

app.exec()