from collections import defaultdict
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox, QLabel, QSplitter,
                             QTextEdit, QGroupBox, QComboBox, QDateEdit, QLineEdit, QCheckBox,
                             QFormLayout, QStackedWidget, QScrollArea, QGridLayout)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from app.db.dao import EventDAO, DocumentDAO
from app.ui.dialogs.event_dialog import EventDialog
from app.ui.dialogs.photo_dialog import PhotoDialog
from app.ui.dialogs.machinery_dialog import MachineryDialog
from app.ui.dialogs.labor_dialog import LaborDialog
from app.ui.dialogs.document_dialog import DocumentDialog
from app.utils.exporter import export_monthly_archive


MIN_DATE = QDate(2000, 1, 1)


class EventCard(QWidget):
    FOLLOW_STATUS_MAP = {
        'pending_commercial': ('待商务补', '#e67e22', '#fef9e7'),
        'pending_site': ('待现场补', '#3498db', '#eaf2f8'),
        'reminded': ('已催办', '#9b59b6', '#f5eef8'),
        'closed': ('已闭合', '#27ae60', '#eafaf1'),
        '': ('未设置', '#95a5a6', '#f4f6f7'),
    }

    def __init__(self, event_data, missing_docs, parent_widget=None):
        super().__init__()
        self.event_id = event_data['id']
        self.parent_widget = parent_widget
        self._build_ui(event_data, missing_docs)

    def _build_ui(self, ev, missing):
        self.setStyleSheet('QWidget { background: #fff; border: 1px solid #ddd; border-radius: 6px; }'
                          'QWidget:hover { border-color: #3498db; }')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        header = QHBoxLayout()
        typelbl = QLabel(f"【{ev.get('event_type', '')}】")
        typelbl.setStyleSheet('font-weight: bold; color: #2980b9;')
        title = QLabel(f"{ev.get('start_date', '')}  {ev.get('affected_area', '')}")
        title.setStyleSheet('font-weight: bold;')
        header.addWidget(typelbl)
        header.addWidget(title, 1)

        if missing:
            status = QLabel(f'✘ 缺{len(missing)}项')
            status.setStyleSheet('color: #c0392b; font-weight: bold;')
        else:
            status = QLabel('✔ 资料齐全')
            status.setStyleSheet('color: #27ae60; font-weight: bold;')
        header.addWidget(status)
        layout.addLayout(header)

        fs = ev.get('follow_status', '') or ''
        fs_label, fs_color, fs_bg = self.FOLLOW_STATUS_MAP.get(fs, self.FOLLOW_STATUS_MAP[''])
        if fs:
            fs_tag = QLabel(f'⚑ {fs_label}')
            fs_tag.setStyleSheet(f'color: {fs_color}; background: {fs_bg}; padding: 2px 6px; border-radius: 3px; font-size: 8pt; font-weight: bold;')
            layout.addWidget(fs_tag)

        sub = QLabel(f"{ev.get('contract_section', '')} | {ev.get('responsible_party', '')}")
        sub.setStyleSheet('color: #7f8c8d; font-size: 9pt;')
        layout.addWidget(sub)

        if missing:
            misslbl = QLabel('待补：' + '、'.join(missing[:4]))
            misslbl.setStyleSheet('color: #c0392b; font-size: 9pt;')
            misslbl.setWordWrap(True)
            layout.addWidget(misslbl)

        btnrow = QHBoxLayout()
        btn_doc = QPushButton('📁 档案')
        btn_photo = QPushButton('📷 照片')
        btn_mach = QPushButton('⚙ 机械')
        btn_labor = QPushButton('👷 劳务')
        btn_edit = QPushButton('✏ 编辑')
        for b in [btn_doc, btn_photo, btn_mach, btn_labor, btn_edit]:
            b.setStyleSheet('QPushButton { padding: 2px 8px; font-size: 9pt; }')
            b.setCursor(Qt.PointingHandCursor)
        btn_doc.clicked.connect(self._open_doc)
        btn_photo.clicked.connect(self._open_photo)
        btn_mach.clicked.connect(self._open_machine)
        btn_labor.clicked.connect(self._open_labor)
        btn_edit.clicked.connect(self._edit)
        btnrow.addWidget(btn_doc)
        btnrow.addWidget(btn_photo)
        btnrow.addWidget(btn_mach)
        btnrow.addWidget(btn_labor)
        btnrow.addWidget(btn_edit)
        btnrow.addStretch(1)
        layout.addLayout(btnrow)

    def _refresh(self):
        if self.parent_widget:
            self.parent_widget.refresh()

    def _open_doc(self):
        DocumentDialog(self, event_id=self.event_id).exec_()
        self._refresh()

    def _open_photo(self):
        PhotoDialog(self, event_id=self.event_id).exec_()
        self._refresh()

    def _open_machine(self):
        MachineryDialog(self, event_id=self.event_id).exec_()
        self._refresh()

    def _open_labor(self):
        LaborDialog(self, event_id=self.event_id).exec_()
        self._refresh()

    def _edit(self):
        dlg = EventDialog(self, event_id=self.event_id)
        if dlg.exec_():
            self._refresh()


class MonthGroup(QGroupBox):
    def __init__(self, month, events_data, parent_widget=None):
        super().__init__()
        self.parent_widget = parent_widget
        self.events = events_data
        self._build_ui(month)

    def _build_ui(self, month):
        total = len(self.events)
        complete = sum(1 for e in self.events if not e['_missing'])
        missing_count = total - complete

        fs_counts = {}
        for e in self.events:
            fs = e.get('follow_status', '') or ''
            fs_counts[fs] = fs_counts.get(fs, 0) + 1

        fs_map = EventCard.FOLLOW_STATUS_MAP
        fs_parts = []
        for code, (label, _, _) in fs_map.items():
            if code in fs_counts and fs_counts[code] > 0:
                fs_parts.append(f'{label}:{fs_counts[code]}')
        fs_summary = '  |  '.join(fs_parts) if fs_parts else ''

        self.setTitle(f'{month}  |  共 {total} 个事件  |  ✔ 齐全 {complete}  |  ✘ 待补 {missing_count}' +
                      (f'  |  状态: {fs_summary}' if fs_summary else ''))
        self.setStyleSheet('QGroupBox { font-weight: bold; border: 2px solid #bbb; border-radius: 8px; margin-top: 12px; padding-top: 10px; }'
                          'QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }')

        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        if missing_count > 0:
            self.setStyleSheet(self.styleSheet().replace('#bbb', '#e67e22'))
        else:
            self.setStyleSheet(self.styleSheet().replace('#bbb', '#27ae60'))

        grid = QGridLayout()
        grid.setSpacing(8)
        for i, ev in enumerate(self.events):
            card = EventCard(ev, ev['_missing'], self.parent_widget)
            row, col = divmod(i, 2)
            grid.addWidget(card, row, col)
        layout.addLayout(grid)


class MonthlyView(QWidget):
    def __init__(self, parent_widget=None):
        super().__init__()
        self.parent_widget = parent_widget
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.scroll.setWidget(self.content)
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.addStretch(1)
        layout.addWidget(self.scroll)

    def set_events(self, filtered_events):
        while self.content_layout.count() > 0:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        by_month = defaultdict(list)
        for ev in filtered_events:
            missing = EventDAO.get_missing_docs(ev['id'])
            ev['_missing'] = missing
            month = ev['start_date'][:7] if ev.get('start_date') else '未知月份'
            by_month[month].append(ev)

        sorted_months = sorted(by_month.keys(), reverse=True)
        for month in sorted_months:
            group = MonthGroup(month, by_month[month], self.parent_widget)
            self.content_layout.insertWidget(self.content_layout.count() - 1, group)

        if not filtered_events:
            lbl = QLabel('无符合筛选条件的事件')
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet('color: #999; padding: 40px;')
            self.content_layout.insertWidget(0, lbl)


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

        self.cmb_view = QComboBox()
        self.cmb_view.addItems(['📋 事件列表', '📅 月度资料包'])
        self.cmb_view.currentIndexChanged.connect(self._switch_view)

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

        self.chk_date_enable = QCheckBox('启用日期筛选')
        self.chk_date_enable.stateChanged.connect(self._toggle_date_filter)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat('yyyy-MM-dd')
        self.date_from.setSpecialValueText('不限')
        self.date_from.setMinimumDate(MIN_DATE)
        self.date_from.setDate(MIN_DATE)
        self.date_from.dateChanged.connect(self._on_filter_changed)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat('yyyy-MM-dd')
        self.date_to.setSpecialValueText('不限')
        self.date_to.setMinimumDate(MIN_DATE)
        self.date_to.setDate(MIN_DATE)
        self.date_to.dateChanged.connect(self._on_filter_changed)

        self.txt_keyword = QLineEdit()
        self.txt_keyword.setPlaceholderText('关键字搜索')
        self.txt_keyword.textChanged.connect(self._on_filter_changed)

        self.chk_missing = QCheckBox('仅看待补资料事件')
        self.chk_missing.stateChanged.connect(self._on_filter_changed)

        self.btn_reset_filter = QPushButton('重置筛选')
        self.btn_reset_filter.clicked.connect(self._reset_filter)

        frow1.addWidget(QLabel('视图：'))
        frow1.addWidget(self.cmb_view)
        frow1.addSpacing(15)
        frow1.addWidget(QLabel('事件类型：'))
        frow1.addWidget(self.cmb_type)
        frow1.addWidget(QLabel('合同段：'))
        frow1.addWidget(self.cmb_contract, 1)
        frow1.addWidget(QLabel('责任方：'))
        frow1.addWidget(self.cmb_resp)
        frow1.addWidget(self.chk_date_enable)
        frow1.addWidget(self.date_from)
        frow1.addWidget(QLabel('至：'))
        frow1.addWidget(self.date_to)
        frow1.addWidget(self.txt_keyword, 2)
        frow1.addWidget(self.chk_missing)
        frow1.addWidget(self.btn_reset_filter)
        flayout.addRow(frow1)
        layout.addWidget(filter_group)

        self.date_from.setEnabled(False)
        self.date_to.setEnabled(False)

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

        self.btn_export_archive = QPushButton('📊 导出月度归档清单')
        self.btn_export_archive.clicked.connect(self._export_archive)

        for b in [self.btn_add, self.btn_edit, self.btn_del]:
            btn_bar.addWidget(b)
        btn_bar.addSpacing(20)
        for b in [self.btn_doc, self.btn_photo, self.btn_machine, self.btn_labor]:
            btn_bar.addWidget(b)
        btn_bar.addSpacing(20)
        btn_bar.addWidget(self.btn_export_archive)
        btn_bar.addStretch(1)
        self.lbl_count = QLabel('共 0 条记录')
        btn_bar.addWidget(self.lbl_count)
        layout.addLayout(btn_bar)

        self.stack = QStackedWidget()

        list_page = QWidget()
        lsplitter = QSplitter(Qt.Vertical)

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
        lsplitter.addWidget(self.table)

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
        lsplitter.addWidget(detail_group)
        lsplitter.setStretchFactor(0, 3)
        lsplitter.setStretchFactor(1, 2)

        llayout = QVBoxLayout(list_page)
        llayout.addWidget(lsplitter)
        self.stack.addWidget(list_page)

        self.monthly_view = MonthlyView(self)
        self.stack.addWidget(self.monthly_view)

        layout.addWidget(self.stack, 1)

    def refresh(self):
        self._refresh_contract_options()
        self._do_filter()

    def _switch_view(self, idx):
        self.stack.setCurrentIndex(idx)
        if idx == 1:
            for b in [self.btn_edit, self.btn_del, self.btn_doc, self.btn_photo, self.btn_machine, self.btn_labor]:
                b.setEnabled(False)
        else:
            for b in [self.btn_edit, self.btn_del, self.btn_doc, self.btn_photo, self.btn_machine, self.btn_labor]:
                b.setEnabled(True)
        self._do_filter()

    def _toggle_date_filter(self, state):
        enabled = bool(state)
        self.date_from.setEnabled(enabled)
        self.date_to.setEnabled(enabled)
        if enabled:
            if self.date_from.date() == MIN_DATE:
                self.date_from.setDate(QDate.currentDate().addMonths(-3))
            if self.date_to.date() == MIN_DATE:
                self.date_to.setDate(QDate.currentDate())
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
        self.chk_date_enable.setChecked(False)
        self.date_from.setDate(MIN_DATE)
        self.date_to.setDate(MIN_DATE)
        self.date_from.setEnabled(False)
        self.date_to.setEnabled(False)
        self.txt_keyword.clear()
        self.chk_missing.setChecked(False)

    def _on_filter_changed(self):
        self._do_filter()

    def _do_filter(self):
        event_type = self.cmb_type.currentText()
        contract = self.cmb_contract.currentText().strip()
        resp = self.cmb_resp.currentText()
        date_from = None
        date_to = None
        if self.chk_date_enable.isChecked():
            if self.date_from.date().isValid() and self.date_from.date() != MIN_DATE:
                date_from = self.date_from.date().toString('yyyy-MM-dd')
            if self.date_to.date().isValid() and self.date_to.date() != MIN_DATE:
                date_to = self.date_to.date().toString('yyyy-MM-dd')

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
                if len(missing) > 3:
                    status_item = QTableWidgetItem('缺：' + '、'.join(missing[:3]) + '...')
                else:
                    status_item = QTableWidgetItem('缺：' + '、'.join(missing))
                status_item.setForeground(QColor('#c0392b'))
            self.table.setItem(i, 9, status_item)
        self.table.blockSignals(False)

        self.monthly_view.set_events(rows)

        self.lbl_count.setText(f'共 {len(rows)} 条记录')
        self._update_detail()

    def _get_current_id(self):
        if self.stack.currentIndex() == 1:
            return None
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

    def _export_archive(self):
        from PyQt5.QtWidgets import QInputDialog
        ym_list = {e.get('start_date', '')[:7] for e in EventDAO.get_all() if e.get('start_date', '')}
        ym_list = sorted({ym for ym in ym_list if len(ym) == 7}, reverse=True)
        items = ['全部月份'] + ym_list
        choice, ok = QInputDialog.getItem(self, '选择月份', '请选择要导出的月份：', items, 0, False)
        if not ok:
            return
        ym = None if choice == '全部月份' else choice
        path = export_monthly_archive(ym)
        if path:
            QMessageBox.information(self, '成功', f'已导出：\n{path}')

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
            self.lbl_alert.setText("⚠ 支撑材料提醒：还缺少 " + '、'.join(missing))
            self.lbl_alert.setStyleSheet('color:#c0392b; font-weight:bold; padding:4px; background:#fef0f0;')
        else:
            self.lbl_alert.setText('✔ 支撑材料齐全')
            self.lbl_alert.setStyleSheet('color:#27ae60; font-weight:bold; padding:4px; background:#eafaf1;')
