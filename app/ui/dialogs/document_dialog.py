import os
import shutil
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QFileDialog, QComboBox, QLineEdit, QFormLayout,
                             QHeaderView, QMessageBox, QLabel, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from app.db.dao import DocumentDAO


class DocumentDialog(QDialog):
    def __init__(self, parent=None, event_id=None):
        super().__init__(parent)
        self.event_id = event_id
        self.setWindowTitle('支撑材料档案管理')
        self.setMinimumSize(820, 520)
        self._init_ui()
        self._refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        row = QHBoxLayout()
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(DocumentDAO.TYPES)
        self.txt_doc_no = QLineEdit()
        self.txt_doc_no.setPlaceholderText('文件/通知单编号')
        self.txt_remark = QLineEdit()
        self.txt_remark.setPlaceholderText('备注')
        btn_upload = QPushButton('上传文件...')
        btn_upload.clicked.connect(self._upload)
        btn_register = QPushButton('仅登记路径')
        btn_register.clicked.connect(self._register)

        row.addWidget(QLabel('材料类型：'))
        row.addWidget(self.cmb_type)
        row.addWidget(QLabel('编号：'))
        row.addWidget(self.txt_doc_no)
        row.addWidget(QLabel('备注：'))
        row.addWidget(self.txt_remark, 1)
        row.addWidget(btn_upload)
        row.addWidget(btn_register)
        form.addRow(row)
        layout.addLayout(form)

        summary_group = QGroupBox('归档状态')
        self.summary_label = QLabel('')
        self.summary_label.setStyleSheet('font-weight:bold;')
        slayout = QHBoxLayout(summary_group)
        slayout.addWidget(self.summary_label)
        layout.addWidget(summary_group)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(['ID', '材料类型', '编号', '文件路径', '备注', '归档时间'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.DoubleClicked)
        self.table.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.table, 1)

        btn_row = QHBoxLayout()
        btn_open = QPushButton('打开文件/文件夹')
        btn_open.clicked.connect(self._open_file)
        btn_del = QPushButton('删除选中')
        btn_del.clicked.connect(self._delete)
        btn_close = QPushButton('关闭')
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_open)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_del)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _get_doc_dir(self):
        base = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '..', 'data', 'documents')
        return os.path.abspath(base)

    def _upload(self):
        files, _ = QFileDialog.getOpenFileNames(self, '选择支撑材料文件', '', '所有文件 (*.*)')
        if not files:
            return
        doc_dir = self._get_doc_dir()
        if not os.path.exists(doc_dir):
            os.makedirs(doc_dir)
        doc_type = self.cmb_type.currentText()
        doc_no = self.txt_doc_no.text().strip()
        remark = self.txt_remark.text().strip()
        for f in files:
            basename = os.path.basename(f)
            dest = os.path.join(doc_dir, f'{self.event_id}_{doc_type}_{basename}')
            if not os.path.exists(dest):
                shutil.copy(f, dest)
            DocumentDAO.create({
                'event_id': self.event_id,
                'doc_type': doc_type,
                'doc_no': doc_no,
                'file_path': dest,
                'remark': remark
            })
        self.txt_doc_no.clear()
        self.txt_remark.clear()
        self._refresh()

    def _register(self):
        path, _ = QFileDialog.getOpenFileName(self, '选择文件（仅登记路径，不复制）', '', '所有文件 (*.*)')
        if not path:
            return
        doc_type = self.cmb_type.currentText()
        doc_no = self.txt_doc_no.text().strip()
        remark = self.txt_remark.text().strip()
        DocumentDAO.create({
            'event_id': self.event_id,
            'doc_type': doc_type,
            'doc_no': doc_no,
            'file_path': path,
            'remark': remark
        })
        self.txt_doc_no.clear()
        self.txt_remark.clear()
        self._refresh()

    def _refresh(self):
        self.table.blockSignals(True)
        rows = DocumentDAO.get_by_event(self.event_id)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(r['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(r['doc_type']))
            self.table.setItem(i, 2, QTableWidgetItem(r.get('doc_no', '')))
            self.table.setItem(i, 3, QTableWidgetItem(r.get('file_path', '')))
            self.table.setItem(i, 4, QTableWidgetItem(r.get('remark', '')))
            self.table.setItem(i, 5, QTableWidgetItem(r.get('created_at', '')))
        self.table.blockSignals(False)
        self._update_summary()

    def _update_summary(self):
        status = []
        for t in DocumentDAO.TYPES:
            docs = DocumentDAO.get_by_event_and_type(self.event_id, t)
            if docs:
                status.append(f'✔ {t} ({len(docs)}份)')
            else:
                status.append(f'✘ {t} (未归档)')
        self.summary_label.setText('   |   '.join(status))

    def _on_item_changed(self, item):
        row = item.row()
        if self.table.item(row, 0) is None:
            return
        did = int(self.table.item(row, 0).text())
        data = {
            'doc_type': self.table.item(row, 1).text(),
            'doc_no': self.table.item(row, 2).text(),
            'file_path': self.table.item(row, 3).text(),
            'remark': self.table.item(row, 4).text(),
        }
        DocumentDAO.update(did, data)
        self._update_summary()

    def _delete(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, '提示', '请选择一行')
            return
        did = int(self.table.item(row, 0).text())
        if QMessageBox.question(self, '确认', '确定删除该档案记录？（文件本身不会被删除）') == QMessageBox.Yes:
            DocumentDAO.delete(did)
            self._refresh()

    def _open_file(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, '提示', '请选择一行')
            return
        path = self.table.item(row, 3).text()
        if path and os.path.exists(path):
            os.startfile(path)
        elif path:
            QMessageBox.warning(self, '提示', '文件路径不存在：\n' + path)
        else:
            QMessageBox.information(self, '提示', '该记录未关联文件')
