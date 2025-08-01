import configparser, os, gdttoolsL, re, sys
import class_enums
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QFileDialog,
    QMessageBox,
    QRadioButton
)

class EinstellungenAllgemein(QDialog):
    def __init__(self, configPath):
        super().__init__()
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)
        self.fontItalic = QFont()
        self.fontItalic.setItalic(True)
        self.fontItalic.setBold(False)

        #config.ini lesen
        configIni = configparser.ConfigParser()
        configIni.read(os.path.join(configPath, "config.ini"))
        self.version = configIni["Allgemein"]["version"]
        self.releasedatum = configIni["Allgemein"]["releasedatum"]
        self.einrichtungsname = configIni["Allgemein"]["einrichtungsname"]
        self.pdfErstellen = configIni["Allgemein"]["pdferstellen"] == "1"
        self.pdfbezeichnung = configIni["Allgemein"]["pdfbezeichnung"] 
        self.einrichtungAufPdf = configIni["Allgemein"]["einrichtungaufpdf"] == "1"
        self.defaultxml = configIni["Allgemein"]["defaultxml"]
        self.vorlagenverzeichnis = ""
        if configIni.has_option("Allgemein", "vorlagenverzeichnis"): # wurde erst mit 1.1.0 eingeführt
            self.vorlagenverzeichnis = configIni["Allgemein"]["vorlagenverzeichnis"]
        self.autoupdate = configIni["Allgemein"]["autoupdate"] == "True"
        self.updaterpfad = configIni["Allgemein"]["updaterpfad"]
        self.dokuverzeichnis = configIni["Allgemein"]["dokuverzeichnis"]
        self.vorherigeDokuLaden = configIni["Allgemein"]["vorherigedokuladen"] == "1"
        self.blutzuckereinheit = class_enums.Blutzuckereinheit(configIni["Allgemein"]["blutzuckereinheit"])
        self.beFaktorStandardschritt = configIni["Allgemein"]["befaktorstandardschritt"]

        self.setWindowTitle("Allgemeine Einstellungen")
        self.setMinimumWidth(500)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type: ignore
        self.buttonBox.rejected.connect(self.reject) # type: ignore

        # Prüfen, ob Lizenzschlüssel verschlüsselt in config.ini
        lizenzschluessel = configIni["Erweiterungen"]["lizenzschluessel"]
        if len(lizenzschluessel) != 29:
            lizenzschluessel = gdttoolsL.GdtToolsLizenzschluessel.dekrypt(lizenzschluessel)

        dialogLayoutV = QVBoxLayout() 

        # Groupox Name der Einrichtung
        groupboxEinrichtung = QGroupBox("Name der Einrichtung")
        groupboxEinrichtung.setFont(self.fontBold)
        self.lineEditEinrichtungsname = QLineEdit(self.einrichtungsname)
        self.lineEditEinrichtungsname.setPlaceholderText("Hausarztpraxis XY")
        self.lineEditEinrichtungsname.setFont(self.fontNormal)
        groupboxLayoutEinrichtung = QVBoxLayout()
        groupboxLayoutEinrichtung.addWidget(self.lineEditEinrichtungsname)
        groupboxEinrichtung.setLayout(groupboxLayoutEinrichtung)

        # Groupbox Formularvorgaben
        groupboxForomularvorgaben = QGroupBox("Formularvorgaben")
        groupboxForomularvorgaben.setFont(self.fontBold)    
        labelBlutzuckereinheit = QLabel("Blutzuckereinheit:")
        labelBlutzuckereinheit.setFont(self.fontNormal)
        self.radioButtonBlutzuckereinheitMg = QRadioButton(class_enums.Blutzuckereinheit.MG_DL.value)
        self.radioButtonBlutzuckereinheitMg.setFont(self.fontNormal)
        self.radioButtonBlutzuckereinheitMMol = QRadioButton(class_enums.Blutzuckereinheit.MMOL_L.value)
        self.radioButtonBlutzuckereinheitMMol.setFont(self.fontNormal)
        if self.blutzuckereinheit == class_enums.Blutzuckereinheit.MG_DL:
            self.radioButtonBlutzuckereinheitMg.setChecked(True)
        else:
            self.radioButtonBlutzuckereinheitMMol.setChecked(True)
        labelBeFaktorStandardschritt = QLabel("BE-Faktor-Standardänderungsschritt:")
        labelBeFaktorStandardschritt.setFont(self.fontNormal)
        self.lineEditBeFaktorStandardschritt = QLineEdit(self.beFaktorStandardschritt.replace(".", ","))
        self.lineEditBeFaktorStandardschritt.setFont(self.fontNormal)
        labelMax2Nachkommastellen = QLabel("(maximal zwei Nachkommastellen)")
        labelMax2Nachkommastellen.setFont(self.fontNormal)
        
        groupboxLayoutFormularvorgaben = QGridLayout()
        groupboxLayoutFormularvorgaben.addWidget(labelBlutzuckereinheit, 0, 0, 1, 2)
        groupboxLayoutFormularvorgaben.addWidget(self.radioButtonBlutzuckereinheitMg, 1, 0, 1, 1)
        groupboxLayoutFormularvorgaben.addWidget(self.radioButtonBlutzuckereinheitMMol, 1, 1, 1, 1)
        groupboxLayoutFormularvorgaben.addWidget(labelBeFaktorStandardschritt, 2, 0, 1, 2)
        groupboxLayoutFormularvorgaben.addWidget(self.lineEditBeFaktorStandardschritt, 3, 0, 1, 1)
        groupboxLayoutFormularvorgaben.addWidget(labelMax2Nachkommastellen, 3, 1, 1, 1)
        groupboxForomularvorgaben.setLayout(groupboxLayoutFormularvorgaben)
        # Groupbox Dokumentationsverwaltung
        groupboxDokumentationsverwaltung = QGroupBox("Dokumentationsverwaltung")
        groupboxDokumentationsverwaltung.setFont(self.fontBold)
        labelArchivierungsverzeichnis = QLabel("Archivierungsverzeichnis:")
        labelArchivierungsverzeichnis.setFont(self.fontNormal)
        self.lineEditArchivierungsverzeichnis= QLineEdit(self.dokuverzeichnis)
        self.lineEditArchivierungsverzeichnis.setFont(self.fontNormal)
        buttonDurchsuchenArchivierungsverzeichnis = QPushButton("Durchsuchen")
        buttonDurchsuchenArchivierungsverzeichnis.setFont(self.fontNormal)
        buttonDurchsuchenArchivierungsverzeichnis.clicked.connect(self.durchsuchenArchivierungsverzeichnis) # type: ignore
        groupboxLayoutArchivierungsverzeichnis = QGridLayout()
        groupboxLayoutArchivierungsverzeichnis.addWidget(labelArchivierungsverzeichnis, 0, 0, 1, 2)
        groupboxLayoutArchivierungsverzeichnis.addWidget(self.lineEditArchivierungsverzeichnis, 1, 0)
        groupboxLayoutArchivierungsverzeichnis.addWidget(buttonDurchsuchenArchivierungsverzeichnis, 1, 1)
        labelVorherigeDokuLaden = QLabel("Vorherige Dokumentation laden (falls vorhanden)")
        labelVorherigeDokuLaden.setFont(self.fontNormal)
        labelVorrang = QLabel("Diese Funktion hat Vorrang vor einer Standardvorlage.")
        labelVorrang.setFont(self.fontItalic)
        self.checkboxVorherigeDokuLaden = QCheckBox()
        self.checkboxVorherigeDokuLaden.setChecked(self.vorherigeDokuLaden)
        groupboxLayoutArchivierungsverzeichnis.addWidget(labelVorherigeDokuLaden, 2, 0)
        groupboxLayoutArchivierungsverzeichnis.addWidget(self.checkboxVorherigeDokuLaden, 2, 1)
        groupboxLayoutArchivierungsverzeichnis.addWidget(labelVorrang, 3, 0)
        groupboxDokumentationsverwaltung.setLayout(groupboxLayoutArchivierungsverzeichnis)

        # Groupbox PDF-Erstellung
        groupboxPdfErstellung = QGroupBox("PDF-Erstellung")
        groupboxPdfErstellung.setFont(self.fontBold)
        labelKeineRegistrierung = QLabel("Für diese Funktion ist eine gültige LANR/Lizenzschlüsselkombination erforderlich.")
        labelKeineRegistrierung.setStyleSheet("font-weight:normal;color:rgb(0,0,200)")
        labelKeineRegistrierung.setVisible(False)
        labelPdfErstellen = QLabel("PDF erstellen und per GDT übertragen")
        labelPdfErstellen.setFont(self.fontNormal)
        self.checkboxPdfErstellen = QCheckBox()
        self.checkboxPdfErstellen.setChecked(self.pdfErstellen)
        self.checkboxPdfErstellen.stateChanged.connect(self.checkboxPdfErstellenChanged) # type: ignore
        labelEinrichtungAufPdf = QLabel("Einrichtungsname übernehmen")
        labelEinrichtungAufPdf.setFont(self.fontNormal)
        self.checkboxEinrichtungAufPdf = QCheckBox()
        self.checkboxEinrichtungAufPdf.setChecked(self.einrichtungAufPdf)
        self.checkboxEinrichtungAufPdf.stateChanged.connect(self.checkboxEinrichtungAufPdfChanged) # type: ignore
        labelPdfBezeichnung = QLabel("PDF-Bezeichnung in Karteikarte:")
        labelPdfBezeichnung.setFont(self.fontNormal)
        self.lineEditPdfBezeichnung = QLineEdit(self.pdfbezeichnung)
        self.lineEditPdfBezeichnung.setFont(self.fontNormal)
        self.lineEditPdfBezeichnung.setPlaceholderText("Insulinspritzplan")
        # PDF-Erstellung daktivieren, falls nicht lizensiert
        if not gdttoolsL.GdtToolsLizenzschluessel.lizenzErteilt(lizenzschluessel, configIni["Erweiterungen"]["lanr"], gdttoolsL.SoftwareId.INSUGDT):
            labelKeineRegistrierung.setVisible(True)
            self.checkboxPdfErstellen.setEnabled(False)
            self.checkboxPdfErstellen.setChecked(False)
            self.lineEditPdfBezeichnung.setText("")
            self.checkboxEinrichtungAufPdf.setEnabled(False)
            self.checkboxEinrichtungAufPdf.setChecked(False)
        groupboxLayoutPdfErstellung = QGridLayout()
        groupboxLayoutPdfErstellung.addWidget(labelKeineRegistrierung, 0, 0, 1, 2)
        groupboxLayoutPdfErstellung.addWidget(labelPdfErstellen, 1, 0)
        groupboxLayoutPdfErstellung.addWidget(self.checkboxPdfErstellen, 1, 1)
        groupboxLayoutPdfErstellung.addWidget(labelEinrichtungAufPdf, 3, 0)
        groupboxLayoutPdfErstellung.addWidget(self.checkboxEinrichtungAufPdf, 3, 1)
        groupboxLayoutPdfErstellung.addWidget(labelPdfBezeichnung, 4, 0)
        groupboxLayoutPdfErstellung.addWidget(self.lineEditPdfBezeichnung, 5, 0)
        groupboxPdfErstellung.setLayout(groupboxLayoutPdfErstellung)

        # Groupox Vorlagen
        groupboxVorlagen = QGroupBox("Insulinspritzplan-Vorlagen")
        groupboxVorlagen.setFont(self.fontBold)
        labelVorlagenverzeichnis = QLabel("Vorlagenverzeichnis:")
        labelVorlagenverzeichnis.setFont(self.fontNormal)
        self.lineEditVorlagenverzeichnis= QLineEdit(self.vorlagenverzeichnis)
        self.lineEditVorlagenverzeichnis.setFont(self.fontNormal)
        buttonDurchsuchenVorlagenverzeichnis = QPushButton("Durchsuchen")
        buttonDurchsuchenVorlagenverzeichnis.setFont(self.fontNormal)
        buttonDurchsuchenVorlagenverzeichnis.clicked.connect(self.durchsuchenVorlagenverzeichnis) # type: ignore
        groupboxLayoutVorlagen = QGridLayout()
        groupboxLayoutVorlagen.addWidget(labelVorlagenverzeichnis, 0, 0, 1, 2)
        groupboxLayoutVorlagen.addWidget(self.lineEditVorlagenverzeichnis, 1, 0)
        groupboxLayoutVorlagen.addWidget(buttonDurchsuchenVorlagenverzeichnis, 1, 1)
        groupboxVorlagen.setLayout(groupboxLayoutVorlagen)

        # GroupBox Updates
        groupBoxUpdatesLayoutG = QGridLayout()
        groupBoxUpdates = QGroupBox("Updates")
        groupBoxUpdates.setFont(self.fontBold)
        labelUpdaterPfad = QLabel("Updater-Pfad")
        labelUpdaterPfad.setFont(self.fontNormal)
        self.lineEditUpdaterPfad= QLineEdit(self.updaterpfad)
        self.lineEditUpdaterPfad.setFont(self.fontNormal)
        self.lineEditUpdaterPfad.setToolTip(self.updaterpfad)
        if not os.path.exists(self.updaterpfad):
            self.lineEditUpdaterPfad.setStyleSheet("background:rgb(255,200,200)")
        self.pushButtonUpdaterPfad = QPushButton("...")
        self.pushButtonUpdaterPfad.setFont(self.fontNormal)
        self.pushButtonUpdaterPfad.setToolTip("Pfad zum GDT-Tools Updater auswählen")
        self.pushButtonUpdaterPfad.clicked.connect(self.pushButtonUpdaterPfadClicked)
        self.checkBoxAutoUpdate = QCheckBox("Automatisch auf Update prüfen")
        self.checkBoxAutoUpdate.setFont(self.fontNormal)
        self.checkBoxAutoUpdate.setChecked(self.autoupdate)
        groupBoxUpdatesLayoutG.addWidget(labelUpdaterPfad, 0, 0)
        groupBoxUpdatesLayoutG.addWidget(self.lineEditUpdaterPfad, 0, 1)
        groupBoxUpdatesLayoutG.addWidget(self.pushButtonUpdaterPfad, 0, 2)
        groupBoxUpdatesLayoutG.addWidget(self.checkBoxAutoUpdate, 1, 0)
        groupBoxUpdates.setLayout(groupBoxUpdatesLayoutG)

        dialogLayoutV.addWidget(groupboxEinrichtung)
        dialogLayoutV.addWidget(groupboxForomularvorgaben)
        dialogLayoutV.addWidget(groupboxDokumentationsverwaltung)
        dialogLayoutV.addWidget(groupboxPdfErstellung)
        dialogLayoutV.addWidget(groupboxVorlagen)
        dialogLayoutV.addWidget(groupBoxUpdates)
        dialogLayoutV.addWidget(self.buttonBox)
        dialogLayoutV.setContentsMargins(10, 10, 10, 10)
        dialogLayoutV.setSpacing(20)
        self.setLayout(dialogLayoutV)

    def durchsuchenArchivierungsverzeichnis(self):
        fd = QFileDialog(self)
        fd.setFileMode(QFileDialog.FileMode.Directory)
        fd.setWindowTitle("Dokumentationsarchivierungsverzeichnis")
        fd.setDirectory(self.dokuverzeichnis)
        fd.setModal(True)
        fd.setLabelText(QFileDialog.DialogLabel.Accept, "Ok")
        fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
        if fd.exec() == 1:
            self.dokuverzeichnis = fd.directory()
            self.lineEditArchivierungsverzeichnis.setText(os.path.abspath(fd.directory().path()))
            self.lineEditArchivierungsverzeichnis.setToolTip(os.path.abspath(fd.directory().path()))

    def checkboxPdfErstellenChanged(self, newState):
        if not newState:
            self.lineEditPdfBezeichnung.setText("")
            self.checkboxEinrichtungAufPdf.setChecked(False)

    def checkboxEinrichtungAufPdfChanged(self, newState):
        if newState:
            self.checkboxPdfErstellen.setChecked(True)
    
    def durchsuchenVorlagenverzeichnis(self):
        fd = QFileDialog(self)
        fd.setFileMode(QFileDialog.FileMode.Directory)
        fd.setWindowTitle("Vorlagenverzeichnis")
        fd.setDirectory(self.vorlagenverzeichnis)
        fd.setModal(True)
        fd.setLabelText(QFileDialog.DialogLabel.Accept, "Ok")
        fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
        if fd.exec() == 1:
            self.dokuverzeichnis = fd.directory()
            self.lineEditVorlagenverzeichnis.setText(os.path.abspath(fd.directory().path()))
            self.lineEditVorlagenverzeichnis.setToolTip(os.path.abspath(fd.directory().path()))

    def pushButtonUpdaterPfadClicked(self):
        fd = QFileDialog(self)
        fd.setFileMode(QFileDialog.FileMode.ExistingFile)
        if os.path.exists(self.lineEditUpdaterPfad.text()):
            fd.setDirectory(os.path.dirname(self.lineEditUpdaterPfad.text()))
        fd.setWindowTitle("Updater-Pfad auswählen")
        fd.setModal(True)
        if "win32" in sys.platform:
            fd.setNameFilters(["exe-Dateien (*.exe)"])
        elif "darwin" in sys.platform:
            fd.setNameFilters(["app-Bundles (*.app)"])
        fd.setLabelText(QFileDialog.DialogLabel.Accept, "Auswählen")
        fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
        if fd.exec() == 1:
            self.lineEditUpdaterPfad.setText(os.path.abspath(fd.selectedFiles()[0]))
            self.lineEditUpdaterPfad.setToolTip(os.path.abspath(fd.selectedFiles()[0]))
            self.lineEditUpdaterPfad.setStyleSheet("background:rgb(255,255,255)")

    def accept(self):
        regexPattern = "[/.,]"
        beFaktorSchrittPattern = r"^\d([.,]\d{1,2})?$"
        if re.search(regexPattern, self.lineEditPdfBezeichnung.text()) != None:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InsuGDT", "Die PDF-Bezeichnung enthält unerlaubte Zeichen (" + regexPattern[1:-1] + ")", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditPdfBezeichnung.setFocus()
            self.lineEditPdfBezeichnung.selectAll()
        elif re.match(beFaktorSchrittPattern, self.lineEditBeFaktorStandardschritt.text()) == None:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InsuGDT", "Der BE-Faktor-Standardänderungsschritt ist unzulässig.", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditBeFaktorStandardschritt.setFocus()
            self.lineEditBeFaktorStandardschritt.selectAll()
        else:
            if self.lineEditPdfBezeichnung.text() == "":
                self.lineEditPdfBezeichnung.setText(self.lineEditPdfBezeichnung.placeholderText())
            if self.lineEditEinrichtungsname.text() == "":
                self.lineEditEinrichtungsname.setText(self.lineEditEinrichtungsname.placeholderText())
            self.done(1)
