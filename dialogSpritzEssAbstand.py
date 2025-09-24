import class_enums
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit, 
    QRadioButton, 
    QButtonGroup
)
abstaende = ["0", "5", "10", "15", "20", "25", "30"]

class SpritzEssAbstand(QDialog):
    def __init__(self, untersteStufe:str, stufengroesse:str, anzahlStufen:str, blutzuckereinheit:class_enums.Blutzuckereinheit, saeListe:list):
        super().__init__()
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)
        self.untersteStufe = float(untersteStufe.replace(",", "."))
        self.stufengroesse = float(stufengroesse.replace(",", "."))
        self.anzahlStufen = int(anzahlStufen)
        self.blutzuckereinheit = blutzuckereinheit
        self.saeListe = saeListe

        self.setWindowTitle("Spritz-Ess-Abstände festlegen")
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setText("Ok")
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type: ignore
        self.buttonBox.rejected.connect(self.reject) # type: ignore

        mainLayoutV = QVBoxLayout()
        saeLayout = QGridLayout()
        labelBzBereich = QLabel("Blutzuckerbereich [" + blutzuckereinheit.value + "]")
        labelBzBereich.setFont(self.fontBold)
        saeLayout.addWidget(labelBzBereich, 0, 0)
        labelSea = QLabel("Spritz-Ess-Abstand [min]")
        labelSea.setFont(self.fontBold)
        saeLayout.addWidget(labelSea, 0, 1, 1, len(abstaende))
        lineEditBzBereich = []
        self.radioButtonSea = []
        self.radioButtonSeaGroup = []
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
            lineEditBzBereich.append(QLineEdit(blutzuckerbereich))
            lineEditBzBereich[stufe + 1].setFont(self.fontNormal)
            lineEditBzBereich[stufe + 1].setReadOnly(True)
            saeLayout.addWidget(lineEditBzBereich[stufe + 1], stufe + 2, 0)
            self.radioButtonSeaGroup.append(QButtonGroup(self))
            for seaNummer in range(len(abstaende)):
                self.radioButtonSea.append(QRadioButton(abstaende[seaNummer]))
                self.radioButtonSeaGroup[len(self.radioButtonSeaGroup) - 1].addButton(self.radioButtonSea[len(self.radioButtonSea) - 1])
                if seaNummer == 0:
                    self.radioButtonSea[len(self.radioButtonSea) - 1].setChecked(True)
                else:
                    if (stufe + 1 + 1) < len(self.saeListe) and abstaende[seaNummer] == self.saeListe[stufe + 1 + 1]:
                        self.radioButtonSea[len(self.radioButtonSea) - 1].setChecked(True)
                self.radioButtonSea[len(self.radioButtonSea) - 1].setFont(self.fontNormal)
                saeLayout.addWidget(self.radioButtonSea[len(self.radioButtonSea) - 1], stufe + 2, seaNummer + 1)
        
        mainLayoutV.addLayout(saeLayout)
        mainLayoutV.addWidget(self.buttonBox)
        self.setLayout(mainLayoutV)
