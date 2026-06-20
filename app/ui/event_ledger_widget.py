from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox, QLabel, QSplitter,
                             QTextEdit, QGroupBox, QComboBox, QDateEdit, QLineEdit, QCheckBox,
                             QFormLayout)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from app.db.dao import EventDAO, DocumentDAO
from app.ui.dialogs.event_dialog import EventDialog
from app.ui.dialogs.photo_dialog import PhotoDialog
from app.ui.dialogs.machinery_dialog import MachineryDialog
from app.ui.dialogs.labor_dialog import LaborDialog
from app.ui.dialogs.document_dialog import DocumentDialog


class EventLedgerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        filter_group = QGroupBox('筛选检索')
        flayout = QFormLayout(filter_group)
        frow1 = QHBoxLayout()

        self.cmb_type = QComboBox()
        self.cmb_type.addItems(['全部', '停工', '窝工', '间歇施工'])
        self.cmb_type.currentIndexChanged.connect(self._on_filter_changed)

        self.cmb_contract = QComboBox()
        self.cmb_contract.setEditable(True)
        self.cmb_contract.setMinimumWidth(140)
        self.cmb_contract.lineEdit().setPlaceholderText('合同段')
        self.cmb_contract.currentTextChanged.connect(self._on_filter_changed)

        self.cmb_resp = QComboBox()
        self.cmb_resp.addItems(['全部', '业主', '监理', '设计', '施工方', '第三方', '待确认'])
        self.cmb_resp.currentIndexChanged.connect(self._on_filter_changed)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat('yyyy-MM-dd')
        self.date_from.setDate(QDate.currentDate().addMonths(-3))
        self.date_from.setSpecialValueText(' ')
        self.date_from.dateChanged.connect(self._on_filter_changed)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat('yyyy-MM-dd')
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setSpecialValueText(' ')
        self.date_to.dateChanged.connect(self._on_filter_changed)

        self.txt_keyword = QLineEdit()
        self.txt_keyword.setPlaceholderText('关键字搜索（部位/描述/通知号）')
        self.txt_keyword.textChanged.connect(self._on_filter_changed)

        self.chk_missing = QCheckBox('仅看待补资料事件')
        self.chk_missing.stateChanged.connect(self._on_filter_changed)

        self.btn_reset_filter = QPushButton('重置筛选')
        self.btn_reset_filter.clicked.connect(self._reset_filter)

        frow1.addWidget(QLabel('事件类型：'))
        frow1.addWidget(self.cmb_type)
        frow1.addWidget(QLabel('合同段：'))
        frow1.addWidget(self.cmb_contract, 1)
        frow1.addWidget(QLabel('责任方：'))
        frow1.addWidget(self.cmb_resp)
        frow1.addWidget(QLabel('开始日期：'))
        frow1.addWidget(self.date_from)
        frow1.addWidget(QLabel('至：'))
        frow1.addWidget(self.date_to)
        frow1.addWidget(self.txt_keyword, 2)
        frow1.addWidget(self.chk_missing)
        frow1.addWidget(self.btn_reset_filter)
        flayout.addRow(frow1)
        layout.addWidget(filter_group)

        btn_bar = QHBoxLayout()
        self.btn_add = QPushButton('新增事件')
        self.btn_edit = QPushButton('编辑事件')
        self.btn_del = QPushButton('删除事件')
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_del.clicked.connect(self._delete)

        self.btn_doc = QPushButton('📁 支撑材料档案')
        self.btn_photo = QPushButton('补录照片')
        self.btn_machine = QPushButton('机械停置清单')
        self.btn_labor = QPushButton('劳务班组人数')
        self.btn_doc.clicked.connect(self._open_doc)
        self.btn_photo.clicked.connect(self._open_photo)
        self.btn_machine.clicked.connect(self._open_machine)
        self.btn_labor.clicked.connect(self._open_labor)

        for b in [self.btn_add, self.btn_edit, self.btn_del]:
            btn_bar.addWidget(b)
        btn_bar.addSpacing(20)
        for b in [self.btn_doc, self.btn_photo, self.btn_machine, self.btn_labor]:
            btn_bar.addWidget(b)
        btn_bar.addStretch(1)
        self.lbl_count = QLabel('共 0 条记录')
        btn_bar.addWidget(self.lbl_count)
        layout.addLayout(btn_bar)

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

        detail_group = QGroupBox('事件详情 / 支撑材料档案')
        dlayout = QVBoxLayout(detail_group)

        doc_status_row = QHBoxLayout()
        self.doc_status_labels = {}
        for t in DocumentDAO.TYPES:
            lbl = QLabel(f'{t}: -')
            lbl.setStyleSheet('padding:2px 6px;')
            self.doc_status_labels[t] = lbl
            doc_status_row.addWidget(lbl)
        dlayout.addLayout(doc_status_row)

        self.txt_detail = QTextEdit()
        self.txt_detail.setReadOnly(True)
        dlayout.addWidget(self.txt_detail, 1)

        self.lbl_alert = QLabel('支撑材料提醒：请选择事件查看')
        self.lbl_alert.setStyleSheet('color:#c0392b; font-weight:bold; padding:4px;')
        dlayout.addWidget(self.lbl_alert)
        splitter.addWidget(detail_group)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, 1)

    def refresh(self):
        self._refresh_contract_options()
        self._do_filter()

    def _refresh_contract_options(self):
        current = self.cmb_contract.currentText()
        self.cmb_contract.blockSignals(True)
        sections = EventDAO.get_unique_contract_sections()
        self.cmb_contract.clear()
        self.cmb_contract.addItem('全部')
        for s in sections:
            self.cmb_contract.addItem(s)
        if current:
            idx = self.cmb_contract.findText(current)
            if idx >= 0:
                self.cmb_contract.setCurrentIndex(idx)
        self.cmb_contract.blockSignals(False)

    def _reset_filter(self):
        self.cmb_type.setCurrentIndex(0)
        self.cmb_contract.setCurrentIndex(0)
        self.cmb_resp.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate().addMonths(-3))
        self.date_to.setDate(QDate.currentDate())
        self.txt_keyword.clear()
        self.chk_missing.setChecked(False)

    def _on_filter_changed(self):
        self._do_filter()

    def _do_filter(self):
        event_type = self.cmb_type.currentText()
        contract = self.cmb_contract.currentText().strip()
        resp = self.cmb_resp.currentText()
        date_from = self.date_from.date().toString('yyyy-MM-dd') if self.date_from.date().isValid() else None
        date_to = self.date_to.date().toString('yyyy-MM-dd') if self.date_to.date().isValid() else None
        keyword = self.txt_keyword.text().strip() or None
        missing_only = self.chk_missing.isChecked()

        rows = EventDAO.filter(
            event_type=event_type,
            contract_section=contract,
            responsible_party=resp,
            date_from=date_from,
            date_to=date_to,
            missing_only=missing_only,
            keyword=keyword
        )

        self.table.blockSignals(True)
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
                status_item = QTableWidgetItem(f'缺：{"、".join(missing[:3])}...' if len(missing) > 3 else f'缺：{"、".join(missing)}')
                status_item.setForeground(QColor('#c0392b'))
            self.table.setItem(i, 9, status_item)
        self.table.blockSignals(False)

        self.lbl_count.setText(f'共 {len(rows)} 条记录')
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
        if QMessageBox.question(self, '确认', '确定删除该事件及关联的所有照片、清单、档案和费用数据？') == QMessageBox.Yes:
            EventDAO.delete(eid)
            self.refresh()

    def _open_doc(self):
        eid = self._get_current_id()
        if not eid:
            QMessageBox.information(self, '提示', '请选择一条事件')
            return
        DocumentDialog(self, event_id=eid).exec_()
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
            for t in DocumentDAO.TYPES:
                self.doc_status_labels[t].setText(f'{t}: -')
                self.doc_status_labels[t].setStyleSheet('padding:2px 6px;')
            return
        data = EventDAO.get_by_id(eid)
        if not data:
            return

        for t in DocumentDAO.TYPES:
            docs = DocumentDAO.get_by_event_and_type(eid, t)
            if docs:
                self.doc_status_labels[t].setText(f'✔ {t} ({len(docs)}份)')
                self.doc_status_labels[t].setStyleSheet('padding:2px 6px; color:#27ae60; background:#eafaf1; border-radius:4px;')
            else:
                self.doc_status_labels[t].setText(f'✘ {t}')
                self.doc_status_labels[t].setStyleSheet('padding:2px 6px; color:#c0392b; background:#fef0f0; border-radius:4px;')

        detail = (
            f"【事件类型】{data.get('event_type', '')}\n"
            f"【合同段】{data.get('contract_section', '')}\n"
            f"【影响部位】{data.get('affected_area', '')}\n"
            f"【起止时间】{data.get('start_date', '')} 至 {data.get('end_date', '')}\n"
            f"【责任方初判】{data.get('responsible_party', '')}\n"
            f"【监理通知编号】{data.get('supervision_notice_no', '')}\n"
            f"【业主指令编号】{data.get('owner_order_no', '')}\n"
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
