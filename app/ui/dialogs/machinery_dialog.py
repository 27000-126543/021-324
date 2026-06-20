from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QFormLayout, QLineEdit, QDateEdit,
                             QDoubleSpinBox, QHeaderView, QMessageBox, QDialog)
from PyQt5.QtCore import QDate
from app.db.dao import MachineryDAO


class MachineryDialog(QDialog):
    def __init__(self, parent=None, event_id=None):
        super().__init__(parent)
        self.event_id = event_id
        self.setWindowTitle('机械停置清单')
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

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText('机械名称，如挖机、塔吊')
        self.txt_spec = QLineEdit()
        self.txt_spec.setPlaceholderText('规格型号，如PC200、QTZ80')
        self.spin_qty = QDoubleSpinBox()
        self.spin_qty.setRange(0, 99999)
        self.spin_qty.setDecimals(1)
        self.txt_unit = QLineEdit()
        self.txt_unit.setText('台·天')
        self.txt_remark = QLineEdit()
        self.txt_remark.setPlaceholderText('备注')
        btn_add = QPushButton('添加')
        btn_add.clicked.connect(self._add)

        row.addWidget(self.date_edit)
        row.addWidget(self.txt_name)
        row.addWidget(self.txt_spec)
        row.addWidget(self.spin_qty)
        row.addWidget(self.txt_unit)
        row.addWidget(self.txt_remark)
        row.addWidget(btn_add)
        form.addRow('日期/名称/规格/数量/单位/备注：', row)
        layout.addLayout(form)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(['ID', '记录日期', '机械名称', '规格型号', '数量', '单位', '备注'])
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
        rows = MachineryDAO.get_by_event(self.event_id)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(r['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(r['record_date']))
            self.table.setItem(i, 2, QTableWidgetItem(r['machine_name']))
            self.table.setItem(i, 3, QTableWidgetItem(r.get('specification', '')))
            self.table.setItem(i, 4, QTableWidgetItem(str(r.get('quantity', 0))))
            self.table.setItem(i, 5, QTableWidgetItem(r.get('unit', '台·天')))
            self.table.setItem(i, 6, QTableWidgetItem(r.get('remark', '')))
        self.table.blockSignals(False)

    def _add(self):
        if not self.txt_name.text().strip():
            QMessageBox.information(self, '提示', '请填写机械名称')
            return
        MachineryDAO.create({
            'event_id': self.event_id,
            'record_date': self.date_edit.date().toString('yyyy-MM-dd'),
            'machine_name': self.txt_name.text().strip(),
            'specification': self.txt_spec.text().strip(),
            'quantity': self.spin_qty.value(),
            'unit': self.txt_unit.text().strip() or '台·天',
            'remark': self.txt_remark.text().strip(),
        })
        self.txt_name.clear()
        self.txt_spec.clear()
        self.txt_remark.clear()
        self.spin_qty.setValue(0)
        self._refresh()

    def _on_item_changed(self, item):
        row = item.row()
        if self.table.item(row, 0) is None:
            return
        mid = int(self.table.item(row, 0).text())

        qty_text_original = self.table.item(row, 4).text()
        qty_text = qty_text_original.strip()
        quantity = None
        if not qty_text:
            is_valid = False
        else:
            try:
                quantity = float(qty_text)
                is_valid = True
            except ValueError:
                is_valid = False

        if not is_valid:
            QMessageBox.warning(self, '输入有误', '数量必须是数字，不能是文字或空格！\n已恢复为原来的数值。')
            self.table.blockSignals(True)
            records = MachineryDAO.get_by_event(self.event_id)
            for r in records:
                if r['id'] == mid:
                    self.table.item(row, 4).setText(str(r.get('quantity', 0)))
                    break
            self.table.blockSignals(False)
            return

        data = {
            'record_date': self.table.item(row, 1).text(),
            'machine_name': self.table.item(row, 2).text(),
            'specification': self.table.item(row, 3).text(),
            'quantity': quantity,
            'unit': self.table.item(row, 5).text(),
            'remark': self.table.item(row, 6).text(),
        }
        MachineryDAO.update(mid, data)

    def _delete(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, '提示', '请选择一行')
            return
        mid = int(self.table.item(row, 0).text())
        if QMessageBox.question(self, '确认', '确定删除该记录？') == QMessageBox.Yes:
            MachineryDAO.delete(mid)
            self._refresh()
