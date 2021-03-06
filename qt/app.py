# Created By: Virgil Dupras
# Created On: 2009-10-31
# Copyright 2013 Hardcoded Software (http://www.hardcoded.net)
# 
# This software is licensed under the "BSD" License as described in the "LICENSE" file, 
# which should be included with this package. The terms are also available at 
# http://www.hardcoded.net/licenses/bsd_license

import sys
import os.path as op

from PyQt4.QtCore import pyqtSignal, SIGNAL, QCoreApplication, QLocale, QUrl
from PyQt4.QtGui import QDialog, QDesktopServices, QApplication, QMessageBox

from qtlib.about_box import AboutBox
from qtlib.app import Application as ApplicationBase
from qtlib.reg import Registration
from qtlib.util import getAppData

from core.app import Application as MoneyGuruModel

from .controller.document import Document
from .controller.main_window import MainWindow
from .controller.import_.window import ImportWindow
from .controller.import_.csv_options import CSVOptionsWindow
from .controller.preferences_panel import PreferencesPanel
from .support.date_edit import DateEdit
from .preferences import Preferences
from .plat import HELP_PATH, BASE_PATH

class MoneyGuru(ApplicationBase):
    VERSION = MoneyGuruModel.VERSION
    LOGO_NAME = 'logo'
    
    def __init__(self):
        ApplicationBase.__init__(self)
        global APP_INSTANCE
        APP_INSTANCE = self
        self.prefs = Preferences()
        self.prefs.load()
        locale = QLocale.system()
        dateFormat = self.prefs.dateFormat
        decimalSep = locale.decimalPoint()
        groupingSep = locale.groupSeparator()
        cachePath = QDesktopServices.storageLocation(QDesktopServices.CacheLocation)
        appdata = getAppData()
        plugin_model_path = op.join(BASE_PATH, 'plugin_examples')
        DateEdit.DATE_FORMAT = dateFormat
        self.model = MoneyGuruModel(view=self, date_format=dateFormat, decimal_sep=decimalSep,
            grouping_sep=groupingSep, cache_path=cachePath, appdata_path=appdata,
            plugin_model_path=plugin_model_path)
        # on the Qt side, we're single document based, so it's one doc per app.
        self.doc = Document(app=self)
        self.doc.model.connect()
        self.mainWindow = MainWindow(doc=self.doc)
        self.importWindow = ImportWindow(self.mainWindow, doc=self.doc)
        self.csvOptionsWindow = CSVOptionsWindow(self.mainWindow, doc=self.doc)
        self.preferencesPanel = PreferencesPanel(self.mainWindow, app=self)
        self.aboutBox = AboutBox(self.mainWindow, self, withreg=False)
        if sys.argv[1:] and op.exists(sys.argv[1]):
            self.doc.open(sys.argv[1])
        elif self.prefs.recentDocuments:
            self.doc.open(self.prefs.recentDocuments[0])
        
        self.connect(self, SIGNAL('applicationFinishedLaunching()'), self.applicationFinishedLaunching)
        QCoreApplication.instance().aboutToQuit.connect(self.applicationWillTerminate)

        self.prefsChanged.emit()
    
    #--- Public
    def showAboutBox(self):
        self.aboutBox.show()
    
    def showHelp(self):
        url = QUrl.fromLocalFile(op.abspath(op.join(HELP_PATH, 'index.html')))
        QDesktopServices.openUrl(url)
    
    def showPreferences(self):
        self.preferencesPanel.load()
        if self.preferencesPanel.exec_() == QDialog.Accepted:
            self.preferencesPanel.save()
            self.prefsChanged.emit()
    
    #--- Event Handling
    def applicationFinishedLaunching(self):
        self.prefs.restoreGeometry('mainWindowGeometry', self.mainWindow)
        self.prefs.restoreGeometry('importWindowGeometry', self.importWindow)
        self.mainWindow.show()
    
    def applicationWillTerminate(self):
        self.doc.close()
        self.willSavePrefs.emit()
        self.prefs.saveGeometry('mainWindowGeometry', self.mainWindow)
        self.prefs.saveGeometry('importWindowGeometry', self.importWindow)
        self.prefs.save()
        self.model.shutdown()
    
    #--- Signals
    prefsChanged = pyqtSignal()
    willSavePrefs = pyqtSignal()
    
    #--- model --> view
    def get_default(self, key):
        return self.prefs.get_value(key)
    
    def set_default(self, key, value):
        self.prefs.set_value(key, value)
    
    def show_fairware_nag(self, prompt):
        reg = Registration(self.model)
        reg.show_fairware_nag(prompt)
    
    def show_demo_nag(self, prompt):
        reg = Registration(self.model)
        reg.show_demo_nag(prompt)
    
    def show_message(self, msg):
        window = QApplication.activeWindow()
        QMessageBox.information(window, '', msg)
    
    def open_url(self, url):
        url = QUrl(url)
        QDesktopServices.openUrl(url)
    
    def reveal_path(self, path):
        url = QUrl.fromLocalFile(str(path))
        QDesktopServices.openUrl(url)
    
