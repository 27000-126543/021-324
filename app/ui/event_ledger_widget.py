from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox, QLabel, QSplitter,
                             QTextEdit, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from app.db.dao import EventDAO
from app.ui.dialogs.event_dialog import EventDialog
from app.ui.dialogs.photo_dialog import PhotoDialog
from app.ui.dialogs.machinery_dialog import MachineryDialog
from app.ui.dialogs.labor_dialog import LaborDialog


class EventLedgerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        self.btn_add = QPushButton('新增事件')
        self.btn_edit = QPushButton('编辑事件')
        self.btn_del = QPushButton('删除事件')
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_del.clicked.connect(self._delete)

        self.btn_photo = QPushButton('补录照片')
        self.btn_machine = QPushButton('机械停置清单')
        self.btn_labor = QPushButton('劳务班组人数')
        self.btn_photo.clicked.connect(self._open_photo)
        self.btn_machine.clicked.connect(self._open_machine)
        self.btn_labor.clicked.connect(self._open_labor)

        for b in [self.btn_add, self.btn_edit, self.btn_del]:
            top.addWidget(b)
        top.addSpacing(20)
        for b in [self.btn_photo, self.btn_machine, self.btn_labor]:
            top.addWidget(b)
        top.addStretch(1)
        layout.addLayout(top)

        splitter = QSplitter(Qt.Vertical)

        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels([
            'ID', '事件类型', '合同段', '影响部位', '开始日期', '结束日期',
            '责任方', '监理通知', '业主指令', '资料完整性'
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setColumnHidden(0, True)
        self.table.itemSelectionChanged.connect(self._update_detail)
        splitter.addWidget(self.table)

        detail_group = QGroupBox('事件详情 / 支撑材料提醒')
        dlayout = QVBoxLayout(detail_group)
        self.txt_detail = QTextEdit()
        self.txt_detail.setReadOnly(True)
        dlayout.addWidget(self.txt_detail)
        self.lbl_alert = QLabel('支撑材料提醒：请选择事件查看')
        self.lbl_alert.setStyleSheet('color:#c0392b; font-weight:bold; padding:4px;')
        dlayout.addWidget(self.lbl_alert)
        splitter.addWidget(detail_group)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, 1)

    def refresh(self):
        self.table.blockSignals(True)
        rows = EventDAO.get_all()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(r['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(r.get('event_type', '')))
            self.table.setItem(i, 2, QTableWidgetItem(r.get('contract_section', '')))
            self.table.setItem(i, 3, QTableWidgetItem(r.get('affected_area', '')))
            self.table.setItem(i, 4, QTableWidgetItem(r.get('start_date', '')))
            self.table.setItem(i, 5, QTableWidgetItem(r.get('end_date', '')))
            self.table.setItem(i, 6, QTableWidgetItem(r.get('responsible_party', '')))
            self.table.setItem(i, 7, QTableWidgetItem(r.get('supervision_notice_no', '')))
            self.table.setItem(i, 8, QTableWidgetItem(r.get('owner_order_no', '')))

            missing = EventDAO.get_missing_docs(r['id'])
            if not missing:
                status_item = QTableWidgetItem('✔ 齐全')
                status_item.setForeground(QColor('#27ae60'))
            else:
                status_item = QTableWidgetItem(f'缺：{"、".join(missing)}')
                status_item.setForeground(QColor('#c0392b'))
            self.table.setItem(i, 9, status_item)
        self.table.blockSignals(False)
        self._update_detail()

    def _get_current_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def _add(self):
        dlg = EventDialog(self)
        if dlg.exec_():
            self.refresh()

    def _edit(self):
        eid = self._get_current_id()
        if not eid:
            QMessageBox.information(self, '提示', '请选择一条事件')
            return
        dlg = EventDialog(self, event_id=eid)
        if dlg.exec_():
            self.refresh()

    def _delete(self):
        eid = self._get_current_id()
        if not eid:
            QMessageBox.information(self, '提示', '请选择一条事件')
            return
        if QMessageBox.question(self, '确认', '确定删除该事件及关联的所有照片、清单和费用数据？') == QMessageBox.Yes:
            EventDAO.delete(eid)
            self.refresh()

    def _open_photo(self):
        eid = self._get_current_id()
        if not eid:
            QMessageBox.information(self, '提示', '请选择一条事件')
            return
        PhotoDialog(self, event_id=eid).exec_()
        self.refresh()

    def _open_machine(self):
        eid = self._get_current_id()
        if not eid:
            QMessageBox.information(self, '提示', '请选择一条事件')
            return
        MachineryDialog(self, event_id=eid).exec_()
        self.refresh()

    def _open_labor(self):
        eid = self._get_current_id()
        if not eid:
            QMessageBox.information(self, '提示', '请选择一条事件')
            return
        LaborDialog(self, event_id=eid).exec_()
        self.refresh()

    def _update_detail(self):
        eid = self._get_current_id()
        if not eid:
            self.txt_detail.clear()
            self.lbl_alert.setText('支撑材料提醒：请选择事件查看')
            return
        data = EventDAO.get_by_id(eid)
        if not data:
            return
        detail = (
            f"【事件类型】{data.get('event_type', '')}\n"
            f"【合同段】{data.get('contract_section', '')}\n"
            f"【影响部位】{data.get('affected_area', '')}\n"
            f"【起止时间】{data.get('start_date', '')} 至 {data.get('end_date', '')}\n"
            f"【责任方初判】{data.get('responsible_party', '')}\n"
            f"【监理通知编号】{data.get('supervision_notice_no', '')}\n"
            f"【业主指令编号】{data.get('owner_order_no', '')}\n"
            f"【签证单】{'已收' if data.get('visa_received') else '未收'}\n"
            f"【复工令】{'已收' if data.get('resume_order_received') else '未收'}\n"
            f"【事件描述】\n{data.get('description', '')}"
        )
        self.txt_detail.setPlainText(detail)

        missing = EventDAO.get_missing_docs(eid)
        if missing:
            self.lbl_alert.setText(f"⚠ 支撑材料提醒：还缺少 {'、'.join(missing)}")
            self.lbl_alert.setStyleSheet('color:#c0392b; font-weight:bold; padding:4px; background:#fef0f0;')
        else:
            self.lbl_alert.setText('✔ 支撑材料齐全')
            self.lbl_alert.setStyleSheet('color:#27ae60; font-weight:bold; padding:4px; background:#eafaf1;')
