import configparser, os, re
## Nur mit Lizenz
import gdttoolsL
## /Nur mit Lizenz
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QGroupBox,
    QLineEdit,
    QMessageBox
)

reLanr = "^\\d{9}$"
reLizenzschluessel = "^([A-Z0-9]{5}-){4}[A-Z0-9]{5}$"

class EinstellungenProgrammerweiterungen(QDialog):
    def __init__(self, configPath):
        super().__init__()

        #config.ini lesen
        configIni = configparser.ConfigParser()
        configIni.read(os.path.join(configPath, "config.ini"))
        self.lanr = configIni["Erweiterungen"]["lanr"]
        self.lizenzschluessel = gdttoolsL.GdtToolsLizenzschluessel.dekrypt(configIni["Erweiterungen"]["lizenzschluessel"])

        self.setWindowTitle("LANR und Lizenzschlüssel")
        self.setMinimumWidth(460)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type:ignore
        self.buttonBox.rejected.connect(self.reject) # type:ignore

        dialogLayoutV = QVBoxLayout()
        # Groupbox LANR
        groupboxLayoutLanr = QVBoxLayout()
        groupboxLanr = QGroupBox("LANR (9 Ziffern)")
        groupboxLanr.setStyleSheet("font-weight:bold")
        self.lineEditLanr = QLineEdit(self.lanr)
        self.lineEditLanr.setStyleSheet("font-weight:normal")
        groupboxLayoutLanr.addWidget(self.lineEditLanr)
        groupboxLanr.setLayout(groupboxLayoutLanr)
        # Groupbox Lizenzschlüssel
        groupboxLayoutLizenzschluessel = QVBoxLayout()
        groupboxLizenzschluessel = QGroupBox("Lizenzschlüssel")
        groupboxLizenzschluessel.setStyleSheet("font-weight:bold")
        self.lineEditLizenzschluessel = QLineEdit(self.lizenzschluessel)
        self.lineEditLizenzschluessel.setStyleSheet("font-weight:normal")
        self.lineEditLizenzschluessel.textEdited.connect(self.lineEditLizenzschluesselTextEdited)
        groupboxLayoutLizenzschluessel.addWidget(self.lineEditLizenzschluessel)
        groupboxLizenzschluessel.setLayout(groupboxLayoutLizenzschluessel)
        dialogLayoutV.addWidget(groupboxLanr)
        dialogLayoutV.addWidget(groupboxLizenzschluessel)
        dialogLayoutV.addWidget(self.buttonBox)
        dialogLayoutV.setContentsMargins(10, 10, 10, 10)
        dialogLayoutV.setSpacing(20)
        self.setLayout(dialogLayoutV)
        if re.match(reLizenzschluessel, self.lineEditLizenzschluessel.text()) != None and gdttoolsL.GdtToolsLizenzschluessel.nochTageGueltig(self.lizenzschluessel) <= 0:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InsuGDT", "Der eingetragene Lizenzschlüssel ist abgelaufen.", QMessageBox.StandardButton.Ok)
            mb.exec()  
            self.lineEditLizenzschluessel.setStyleSheet("font-weight:normal;background:rgb(255,220,220)")
            self.lineEditLizenzschluessel.setFocus()
            self.lineEditLizenzschluessel.selectAll()
        else:
            self.lineEditLanr.setFocus()
            self.lineEditLanr.selectAll()

    def lineEditLizenzschluesselTextEdited(self):
        self.lineEditLizenzschluessel.setStyleSheet("font-weight:normal;background:rgb(255,255,255)")

    def accept(self):
        if self.lineEditLanr.text() == "" and self.lineEditLizenzschluessel.text() == "":
            self.done(1)
        elif not re.match(reLanr, self.lineEditLanr.text()) or not gdttoolsL.GdtToolsLizenzschluessel.checksummeLanrKorrekt(self.lineEditLanr.text()):
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InsuGDT", "Die LANR ist ungültig.", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditLanr.setFocus()
            self.lineEditLanr.selectAll()
        elif re.match(reLizenzschluessel, self.lineEditLizenzschluessel.text()) == None or (not gdttoolsL.GdtToolsLizenzschluessel.lizenzErteilt(self.lineEditLizenzschluessel.text().upper(), self.lineEditLanr.text(), gdttoolsL.SoftwareId.INSUGDT) and not gdttoolsL.GdtToolsLizenzschluessel.lizenzErteilt(self.lineEditLizenzschluessel.text().upper(), self.lineEditLanr.text(), gdttoolsL.SoftwareId.INSUGDTPSEUDO)):
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von InsuGDT", "Die LANR/Lizenzschlüssel-Kombination ist ungültig.", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditLizenzschluessel.setFocus()
            self.lineEditLizenzschluessel.selectAll()
        else:
            self.done(1)