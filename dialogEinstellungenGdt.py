import configparser, os
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
    QMessageBox,
    QFileDialog,
    QComboBox
)

zeichensatz = ["7Bit", "IBM (Standard) CP 437", "ISO8859-1 (ANSI) CP 1252"]

class EinstellungenGdt(QDialog):
    def __init__(self, configPath):
        super().__init__()

        #config.ini lesen
        configIni = configparser.ConfigParser()
        configIni.read(os.path.join(configPath, "config.ini"))
        self.gdtImportVerzeichnis = configIni["GDT"]["gdtimportverzeichnis"]
        if self.gdtImportVerzeichnis == "":
            self.gdtImportVerzeichnis = os.getcwd()
        self.gdtExportVerzeichnis = configIni["GDT"]["gdtexportverzeichnis"]
        if self.gdtExportVerzeichnis == "":
            self.gdtExportVerzeichnis = os.getcwd()
        self.idInsuGdt = configIni["GDT"]["idinsugdt"]
        self.idPraxisEdv = configIni["GDT"]["idpraxisedv"]
        self.kuerzeltInsuGdt = configIni["GDT"]["kuerzelinsugdt"]
        self.kuerzeltPraxisEdv= configIni["GDT"]["kuerzelpraxisedv"]
        self.aktuelleZeichensatznummer = int(configIni["GDT"]["zeichensatz"]) - 1

        self.setWindowTitle("GDT-Einstellungen")
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type:ignore
        self.buttonBox.rejected.connect(self.reject) # type:ignore

        dialogLayoutV = QVBoxLayout()
        groupboxLayoutH = QHBoxLayout()
        groupboxLayoutG = QGridLayout()
        # Groupbox GDT-IDs
        groupboxGdtIds = QGroupBox("GDT-IDs (8 Zeichen)")
        groupboxGdtIds.setStyleSheet("font-weight:bold")
        labelInsuGdt = QLabel("InsuGDT:")
        labelInsuGdt.setStyleSheet("font-weight:normal")
        labelPraxisEdv = QLabel("Praxis-EDV:")
        labelPraxisEdv.setStyleSheet("font-weight:normal")
        labelGdtIdHinweis = QLabel("Hinweis: Wird keine Praxis-EDV-ID eingetragen, erfolgt beim Empfang der \nGDT-Datei von der Praxis-EDV keine Übereinstimmungsprüfung der ID.")
        labelGdtIdHinweis.setStyleSheet("font-weight:normal")
        self.lineEditInsuGdtId = QLineEdit(self.idInsuGdt)
        self.lineEditInsuGdtId.setStyleSheet("font-weight:normal")
        self.lineEditInsuGdtId.setEnabled(False)
        self.lineEditPraxisEdvId = QLineEdit(self.idPraxisEdv)
        self.lineEditPraxisEdvId.setStyleSheet("font-weight:normal")
        groupboxLayoutG.addWidget(labelInsuGdt, 0, 0)
        groupboxLayoutG.addWidget(self.lineEditInsuGdtId, 0, 1)
        groupboxLayoutG.addWidget(labelPraxisEdv, 0, 2)
        groupboxLayoutG.addWidget(self.lineEditPraxisEdvId, 0, 3)
        groupboxLayoutG.addWidget(labelGdtIdHinweis, 1, 0, 1, 4)
        groupboxGdtIds.setLayout(groupboxLayoutG)
        # Groupbox Austauschverzeichnisse
        groupboxLayoutG = QGridLayout()
        groupboxAustauschverzeichnisse = QGroupBox("Austauschverzeichnisse")
        groupboxAustauschverzeichnisse.setStyleSheet("font-weight:bold")
        labelImport = QLabel("Import:")
        labelImport.setStyleSheet("font-weight:normal")
        labelExport = QLabel("Export:")
        labelExport.setStyleSheet("font-weight:normal")
        self.lineEditImport = QLineEdit(self.gdtImportVerzeichnis)
        self.lineEditImport.setStyleSheet("font-weight:normal")
        self.lineEditExport = QLineEdit(self.gdtExportVerzeichnis)
        self.lineEditExport.setStyleSheet("font-weight:normal")
        buttonDurchsuchenImport = QPushButton("Durchsuchen")
        buttonDurchsuchenImport.setStyleSheet("font-weight:normal")
        buttonDurchsuchenImport.clicked.connect(self.durchsuchenImport) # type:ignore
        buttonDurchsuchenExport = QPushButton("Durchsuchen")
        buttonDurchsuchenExport.setStyleSheet("font-weight:normal")
        buttonDurchsuchenExport.clicked.connect(self.durchsuchenExport) # type:ignore
        groupboxLayoutG.addWidget(labelImport, 0, 0, 1, 2)
        groupboxLayoutG.addWidget(self.lineEditImport, 1, 0)
        groupboxLayoutG.addWidget(buttonDurchsuchenImport, 1, 1)
        groupboxLayoutG.addWidget(labelExport, 2, 0, 1, 2)
        groupboxLayoutG.addWidget(self.lineEditExport, 3, 0)
        groupboxLayoutG.addWidget(buttonDurchsuchenExport, 3, 1)
        groupboxAustauschverzeichnisse.setLayout(groupboxLayoutG)
        # Groupbox Kuerzel
        groupboxLayoutG = QGridLayout()
        groupboxKuerzel = QGroupBox("Kürzel für Austauschdateien (4 Zeichen)")
        groupboxKuerzel.setStyleSheet("font-weight:bold")
        labelInsuGdtKuerzel = QLabel("InsuGDT:")
        labelInsuGdtKuerzel.setStyleSheet("font-weight:normal")
        labelPraxisEdvKuerzel = QLabel("Praxis-EDV:")
        labelPraxisEdvKuerzel.setStyleSheet("font-weight:normal")
        self.lineEditInsuGdtKuerzel = QLineEdit(self.kuerzeltInsuGdt)
        self.lineEditInsuGdtKuerzel.textChanged.connect(self.kuerzelGeaendert) # type:ignore
        self.lineEditInsuGdtKuerzel.setStyleSheet("font-weight:normal")
        self.lineEditInsuGdtKuerzel.setEnabled(False)
        self.lineEditPraxisEdvKuerzel = QLineEdit(self.kuerzeltPraxisEdv)
        self.lineEditPraxisEdvKuerzel.textChanged.connect(self.kuerzelGeaendert) # type:ignore
        self.lineEditPraxisEdvKuerzel.setStyleSheet("font-weight:normal")
        self.labelImportDateiname = QLabel("Import-Dateiname: " + self.lineEditInsuGdtKuerzel.text() + self.lineEditPraxisEdvKuerzel.text() + ".gdt")
        self.labelImportDateiname.setStyleSheet("font-weight:normal")
        self.labelExportDateiname = QLabel("Export-Dateiname: " + self.lineEditPraxisEdvKuerzel.text() + self.lineEditInsuGdtKuerzel.text() + ".gdt")
        self.labelExportDateiname.setStyleSheet("font-weight:normal")
        groupboxLayoutG.addWidget(labelInsuGdtKuerzel, 0, 0)
        groupboxLayoutG.addWidget(self.lineEditInsuGdtKuerzel, 0, 1)
        groupboxLayoutG.addWidget(labelPraxisEdvKuerzel, 0, 2)
        groupboxLayoutG.addWidget(self.lineEditPraxisEdvKuerzel, 0, 3)
        groupboxLayoutG.addWidget(self.labelImportDateiname, 1, 0, 1, 4)
        groupboxLayoutG.addWidget(self.labelExportDateiname, 2, 0, 1, 4)
        groupboxKuerzel.setLayout(groupboxLayoutG)
        # Groupbox Zeichensatz
        groupboxLayoutZeichensatz = QVBoxLayout()
        groupboxZeichensatz = QGroupBox("Zeichensatz")
        groupboxZeichensatz.setStyleSheet("font-weight:bold")
        self.combobxZeichensatz = QComboBox()
        for zs in zeichensatz:
            self.combobxZeichensatz.addItem(zs)
        self.combobxZeichensatz.setStyleSheet("font-weight:normal")
        self.combobxZeichensatz.setCurrentIndex(self.aktuelleZeichensatznummer)
        self.combobxZeichensatz.currentIndexChanged.connect(self.zeichensatzGewechselt) # type:ignore
        groupboxLayoutZeichensatz.addWidget(self.combobxZeichensatz)
        groupboxZeichensatz.setLayout(groupboxLayoutZeichensatz)

        dialogLayoutV.addWidget(groupboxGdtIds)
        dialogLayoutV.addWidget(groupboxAustauschverzeichnisse)
        dialogLayoutV.addWidget(groupboxKuerzel)
        dialogLayoutV.addWidget(groupboxZeichensatz)
        dialogLayoutV.addWidget(self.buttonBox)
        dialogLayoutV.setContentsMargins(10, 10, 10, 10)
        dialogLayoutV.setSpacing(20)
        self.setLayout(dialogLayoutV)
        self.lineEditInsuGdtId.setFocus()
        self.lineEditInsuGdtId.selectAll()

    def kuerzelGeaendert(self):
        kuerzelInsuGdt = self.lineEditInsuGdtKuerzel.text()
        kuerzelPraxisEdv = self.lineEditPraxisEdvKuerzel.text()
        self.labelImportDateiname.setText("Import-Dateiname: " + kuerzelInsuGdt + kuerzelPraxisEdv + ".gdt")
        self.labelExportDateiname.setText("Export-Dateiname: " + kuerzelPraxisEdv + kuerzelInsuGdt + ".gdt")

    def durchsuchenImport(self):
        fd = QFileDialog(self)
        fd.setFileMode(QFileDialog.FileMode.Directory)
        fd.setWindowTitle("GDT-Importverzeichnis")
        fd.setDirectory(self.gdtImportVerzeichnis)
        fd.setModal(True)
        fd.setLabelText(QFileDialog.DialogLabel.Accept, "Ok")
        fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
        if fd.exec() == 1:
            self.gdtImportVerzeichnis = fd.directory()
            self.lineEditImport.setText(os.path.abspath(fd.directory().path()))
            self.lineEditImport.setToolTip(os.path.abspath(fd.directory().path()))

    def durchsuchenExport(self):
        fd = QFileDialog(self)
        fd.setFileMode(QFileDialog.FileMode.Directory)
        fd.setWindowTitle("GDT-Exportverzeichnis")
        fd.setDirectory(self.gdtExportVerzeichnis)
        fd.setModal(True)
        fd.setLabelText(QFileDialog.DialogLabel.Accept, "Ok")
        fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
        if fd.exec() == 1:
            self.gdtExportVerzeichnis = fd.directory()
            self.lineEditExport.setText(os.path.abspath(fd.directory().path()))
            self.lineEditExport.setToolTip(os.path.abspath(fd.directory().path()))

    def zeichensatzGewechselt(self):
        self.aktuelleZeichensatznummer = self.combobxZeichensatz.currentIndex()

    def accept(self):
        if len(self.lineEditPraxisEdvId.text()) != 8 and len(self.lineEditPraxisEdvId.text()) != 0:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis", "Die GDT-ID muss aus acht Zeichen bestehen.", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditPraxisEdvId.setFocus()
            self.lineEditPraxisEdvId.selectAll()
        elif len(self.lineEditPraxisEdvKuerzel.text()) != 4:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis", "Das Kürzel für Austauschdateien muss aus vier Zeichen bestehen.", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditPraxisEdvKuerzel.setFocus()
            self.lineEditPraxisEdvKuerzel.selectAll()
        else:
            self.done(1)