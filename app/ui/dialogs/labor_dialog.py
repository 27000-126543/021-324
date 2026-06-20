from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QFormLayout, QLineEdit, QDateEdit,
                             QSpinBox, QHeaderView, QMessageBox)
from PyQt5.QtCore import QDate
from app.db.dao import LaborDAO


class LaborDialog(QDialog):
    def __init__(self, parent=None, event_id=None):
        super().__init__(parent)
        self.event_id = event_id
        self.setWindowTitle('劳务班组人数')
        self.setMinimumSize(780, 480)
        self._init_ui()
        self._refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        row = QHBoxLayout()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat('yyyy-MM-dd')
        self.date_edit.setDate(QDate.currentDate())

        self.txt_team = QLineEdit()
        self.txt_team.setPlaceholderText('班组名称，如钢筋班、模板班')
        self.spin_count = QSpinBox()
        self.spin_count.setRange(0, 9999)
        self.txt_type = QLineEdit()
        self.txt_type.setPlaceholderText('工种，如普工、技工')
        self.txt_remark = QLineEdit()
        self.txt_remark.setPlaceholderText('备注')
        btn_add = QPushButton('添加')
        btn_add.clicked.connect(self._add)

        row.addWidget(self.date_edit)
        row.addWidget(self.txt_team)
        row.addWidget(self.spin_count)
        row.addWidget(self.txt_type)
        row.addWidget(self.txt_remark)
        row.addWidget(btn_add)
        form.addRow('日期/班组/人数/工种/备注：', row)
        layout.addLayout(form)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(['ID', '记录日期', '班组名称', '人数', '工种', '备注'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.DoubleClicked)
        self.table.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.table, 1)

        btn_row = QHBoxLayout()
        btn_del = QPushButton('删除选中')
        btn_del.clicked.connect(self._delete)
        btn_close = QPushButton('关闭')
        btn_close.clicked.connect(self.accept)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_del)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _refresh(self):
        self.table.blockSignals(True)
        rows = LaborDAO.get_by_event(self.event_id)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(r['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(r['record_date']))
            self.table.setItem(i, 2, QTableWidgetItem(r['team_name']))
            self.table.setItem(i, 3, QTableWidgetItem(str(r.get('worker_count', 0))))
            self.table.setItem(i, 4, QTableWidgetItem(r.get('work_type', '')))
            self.table.setItem(i, 5, QTableWidgetItem(r.get('remark', '')))
        self.table.blockSignals(False)

    def _add(self):
        if not self.txt_team.text().strip():
            QMessageBox.information(self, '提示', '请填写班组名称')
            return
        LaborDAO.create({
            'event_id': self.event_id,
            'record_date': self.date_edit.date().toString('yyyy-MM-dd'),
            'team_name': self.txt_team.text().strip(),
            'worker_count': self.spin_count.value(),
            'work_type': self.txt_type.text().strip(),
            'remark': self.txt_remark.text().strip(),
        })
        self.txt_team.clear()
        self.txt_type.clear()
        self.txt_remark.clear()
        self.spin_count.setValue(0)
        self._refresh()

    def _on_item_changed(self, item):
        row = item.row()
        if self.table.item(row, 0) is None:
            return
        lid = int(self.table.item(row, 0).text())

        count_text = self.table.item(row, 3).text().strip()
        try:
            count_text_clean = count_text.replace('.', '')
            worker_count = int(count_text_clean) if count_text_clean else 0
            if worker_count < 0:
                raise ValueError
        except (ValueError, TypeError):
            QMessageBox.warning(self, '输入有误', '人数必须是整数，请重新输入！\n已恢复为原来的数值。')
            self.table.blockSignals(True)
            records = LaborDAO.get_by_event(self.event_id)
            for r in records:
                if r['id'] == lid:
                    self.table.item(row, 3).setText(str(r.get('worker_count', 0)))
                    break
            self.table.blockSignals(False)
            return

        data = {
            'record_date': self.table.item(row, 1).text(),
            'team_name': self.table.item(row, 2).text(),
            'worker_count': worker_count,
            'work_type': self.table.item(row, 4).text(),
            'remark': self.table.item(row, 5).text(),
        }
        LaborDAO.update(lid, data)

    def _delete(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, '提示', '请选择一行')
            return
        lid = int(self.table.item(row, 0).text())
        if QMessageBox.question(self, '确认', '确定删除该记录？') == QMessageBox.Yes:
            LaborDAO.delete(lid)
            self._refresh()
