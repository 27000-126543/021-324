from PyQt5.QtWidgets import QMainWindow, QTabWidget, QStatusBar
from PyQt5.QtGui import QIcon
from app.ui.event_ledger_widget import EventLedgerWidget
from app.ui.cost_calc_widget import CostCalcWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('停窝工索赔台账管理系统')
        self.setMinimumSize(1180, 720)

        self.tabs = QTabWidget()
        self.ledger = EventLedgerWidget()
        self.cost = CostCalcWidget()
        self.tabs.addTab(self.ledger, '📋 事件台账')
        self.tabs.addTab(self.cost, '💰 费用测算')
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.setCentralWidget(self.tabs)

        status = QStatusBar()
        status.showMessage('就绪 | 数据本地离线保存，支持随时补录')
        self.setStatusBar(status)

    def _on_tab_changed(self, idx):
        if idx == 1:
            self.cost._refresh_events()
        else:
            self.ledger.refresh()
