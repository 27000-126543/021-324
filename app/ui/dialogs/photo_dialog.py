import os
import shutil
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QFileDialog, QDateEdit, QLineEdit, QFormLayout,
                             QHeaderView, QMessageBox, QLabel)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QPixmap
from app.db.dao import PhotoDAO


class PhotoDialog(QDialog):
    def __init__(self, parent=None, event_id=None):
        super().__init__(parent)
        self.event_id = event_id
        self.setWindowTitle('现场照片管理')
        self.setMinimumSize(720, 480)
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
        self.txt_remark = QLineEdit()
        self.txt_remark.setPlaceholderText('照片备注')
        btn_browse = QPushButton('选择照片...')
        btn_browse.clicked.connect(self._browse)
        row.addWidget(QLabel('拍摄日期：'))
        row.addWidget(self.date_edit)
        row.addWidget(QLabel('备注：'))
        row.addWidget(self.txt_remark, 1)
        row.addWidget(btn_browse)
        form.addRow(row)
        layout.addLayout(form)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(['ID', '拍摄日期', '文件路径', '备注'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table, 1)

        self.preview_label = QLabel('双击行预览照片')
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedHeight(120)
        self.preview_label.setStyleSheet('border:1px solid #ccc; background:#fafafa;')
        layout.addWidget(self.preview_label)
        self.table.doubleClicked.connect(self._preview)

        btn_row = QHBoxLayout()
        btn_del = QPushButton('删除选中')
        btn_del.clicked.connect(self._delete)
        btn_close = QPushButton('关闭')
        btn_close.clicked.connect(self.accept)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_del)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _browse(self):
        files, _ = QFileDialog.getOpenFileNames(self, '选择照片', '', '图片文件 (*.jpg *.jpeg *.png *.bmp)')
        if not files:
            return
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '..', 'data', 'photos')
        data_dir = os.path.abspath(data_dir)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        record_date = self.date_edit.date().toString('yyyy-MM-dd')
        remark = self.txt_remark.text().strip()
        for f in files:
            basename = os.path.basename(f)
            dest = os.path.join(data_dir, f'{self.event_id}_{record_date}_{basename}')
            if not os.path.exists(dest):
                shutil.copy(f, dest)
            PhotoDAO.create({
                'event_id': self.event_id,
                'record_date': record_date,
                'file_path': dest,
                'remark': remark
            })
        self.txt_remark.clear()
        self._refresh()

    def _refresh(self):
        rows = PhotoDAO.get_by_event(self.event_id)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(r['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(r['record_date']))
            self.table.setItem(i, 2, QTableWidgetItem(r['file_path']))
            self.table.setItem(i, 3, QTableWidgetItem(r.get('remark', '')))

    def _delete(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, '提示', '请选择一行')
            return
        pid = int(self.table.item(row, 0).text())
        if QMessageBox.question(self, '确认', '确定删除该照片记录？') == QMessageBox.Yes:
            PhotoDAO.delete(pid)
            self._refresh()

    def _preview(self, index):
        row = index.row()
        path = self.table.item(row, 2).text()
        pix = QPixmap(path)
        if not pix.isNull():
            self.preview_label.setPixmap(pix.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
