from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
                             QListWidgetItem, QFormLayout, QLineEdit, QTextEdit,
                             QMessageBox, QLabel, QInputDialog, QGroupBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QSplitter)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from app.db.dao import CostVersionDAO, CostItemDAO


class VersionDialog(QDialog):
    def __init__(self, parent=None, event_id=None, current_version_id=None):
        super().__init__(parent)
        self.event_id = event_id
        self.selected_version_id = current_version_id
        self.setWindowTitle('测算版本管理')
        self.setMinimumSize(680, 480)
        self._init_ui()
        self._refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        top = QHBoxLayout()

        left = QGroupBox('版本列表')
        llayout = QVBoxLayout(left)
        self.version_list = QListWidget()
        self.version_list.itemSelectionChanged.connect(self._on_select)
        self.version_list.itemDoubleClicked.connect(self._on_double_click)
        llayout.addWidget(self.version_list)

        btn_row = QHBoxLayout()
        btn_new = QPushButton('📌 保存当前为新版本')
        btn_new.clicked.connect(self._new_version)
        btn_set_cur = QPushButton('设为当前版本')
        btn_set_cur.clicked.connect(self._set_current)
        btn_del = QPushButton('删除版本')
        btn_del.clicked.connect(self._delete)
        btn_row.addWidget(btn_new)
        btn_row.addWidget(btn_set_cur)
        btn_row.addWidget(btn_del)
        llayout.addLayout(btn_row)

        right = QGroupBox('版本详情')
        rlayout = QFormLayout(right)
        self.lbl_name = QLabel('-')
        self.lbl_created = QLabel('-')
        self.lbl_desc = QLabel('-')
        self.lbl_totals = QLabel('-')
        self.lbl_totals.setWordWrap(True)
        self.lbl_grand = QLabel('-')
        self.lbl_grand.setStyleSheet('font-size:14pt; font-weight:bold; color:#2980b9;')
        rlayout.addRow('版本名称：', self.lbl_name)
        rlayout.addRow('创建时间：', self.lbl_created)
        rlayout.addRow('版本说明：', self.lbl_desc)
        rlayout.addRow('明细合计：', self.lbl_totals)
        rlayout.addRow('金额总计：', self.lbl_grand)

        comp_group = QGroupBox('版本对比（任选两个版本）')
        complayout = QVBoxLayout(comp_group)

        comp_sel_row = QHBoxLayout()
        comp_sel_row.addWidget(QLabel('版本A：'))
        self.cmb_comp_v1 = QComboBox()
        comp_sel_row.addWidget(self.cmb_comp_v1, 1)
        comp_sel_row.addWidget(QLabel('→ 版本B：'))
        self.cmb_comp_v2 = QComboBox()
        comp_sel_row.addWidget(self.cmb_comp_v2, 1)
        complayout.addLayout(comp_sel_row)

        self.lbl_compare = QLabel('请选择两个版本进行对比')
        self.lbl_compare.setWordWrap(True)
        complayout.addWidget(self.lbl_compare)

        comp_btn_row = QHBoxLayout()
        btn_comp = QPushButton('⏱ 对比金额变化')
        btn_comp.clicked.connect(self._compare)
        btn_comp_detail = QPushButton('📊 明细对比')
        btn_comp_detail.clicked.connect(self._compare_detail)
        comp_btn_row.addWidget(btn_comp)
        comp_btn_row.addWidget(btn_comp_detail)
        complayout.addLayout(comp_btn_row)
        rlayout.addRow(comp_group)

        top.addWidget(left, 1)
        top.addWidget(right, 1)
        layout.addLayout(top)

        bottom = QHBoxLayout()
        btn_ok = QPushButton('确定（载入选中版本）')
        btn_ok.clicked.connect(self._on_ok)
        btn_cancel = QPushButton('关闭')
        btn_cancel.clicked.connect(self.reject)
        bottom.addStretch(1)
        bottom.addWidget(btn_ok)
        bottom.addWidget(btn_cancel)
        layout.addLayout(bottom)

    def _refresh(self):
        self.version_list.clear()
        versions = CostVersionDAO.get_versions(self.event_id)
        for v in versions:
            _, totals, grand = CostItemDAO.get_summary(self.event_id, v['id'])
            text = f"{v['version_name']}  -  ￥{grand:,.2f}"
            if v.get('is_current'):
                text += '   ✅ 当前版本'
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, v['id'])
            item.setData(Qt.UserRole + 1, v)
            self.version_list.addItem(item)
        if not versions:
            item = QListWidgetItem('（尚未保存任何测算版本，请先编辑费用然后点击"保存新版本"）')
            item.setFlags(Qt.NoItemFlags)
            self.version_list.addItem(item)

        self.cmb_comp_v1.clear()
        self.cmb_comp_v2.clear()
        if versions:
            for v in versions:
                label = f"{v['version_name']}（￥{CostItemDAO.get_summary(self.event_id, v['id'])[2]:,.0f}）"
                self.cmb_comp_v1.addItem(label, v['id'])
                self.cmb_comp_v2.addItem(label, v['id'])
            if len(versions) >= 2:
                self.cmb_comp_v2.setCurrentIndex(1)
        else:
            self.cmb_comp_v1.addItem('（无版本）', None)
            self.cmb_comp_v2.addItem('（无版本）', None)

    def _on_select(self):
        item = self.version_list.currentItem()
        if not item or item.data(Qt.UserRole) is None:
            return
        v = item.data(Qt.UserRole + 1)
        self.lbl_name.setText(v.get('version_name', ''))
        self.lbl_created.setText(v.get('created_at', ''))
        self.lbl_desc.setText(v.get('version_desc', '') or '-')
        _, totals, grand = CostItemDAO.get_summary(self.event_id, v['id'])
        lines = []
        for cat in CostItemDAO.CATEGORIES:
            lines.append(f'{cat}: ￥{totals[cat]:,.2f}')
        self.lbl_totals.setText('   |   '.join(lines))
        self.lbl_grand.setText(f'￥{grand:,.2f}')
        self.lbl_compare.setText('点击下方按钮与当前版本对比金额变化')

    def _on_double_click(self, item):
        if item.data(Qt.UserRole) is not None:
            self.selected_version_id = item.data(Qt.UserRole)
            self.accept()

    def _on_ok(self):
        item = self.version_list.currentItem()
        if item and item.data(Qt.UserRole) is not None:
            self.selected_version_id = item.data(Qt.UserRole)
        self.accept()

    def _new_version(self):
        name, ok = QInputDialog.getText(self, '保存新版本', '请输入版本名称（如"初稿V1"、"监理沟通后"）:')
        if not ok or not name.strip():
            return
        desc, ok = QInputDialog.getMultiLineText(self, '版本说明', '可选：说明与上一版相比调整了什么：', '')
        if not ok:
            return

        source_vid = None
        item = self.version_list.currentItem()
        if item and item.data(Qt.UserRole) is not None:
            source_vid = item.data(Qt.UserRole)
            src_v = item.data(Qt.UserRole + 1)
            reply = QMessageBox.question(
                self, '确认',
                f'是否以「{src_v["version_name"]}」为基础创建新版本？\n'
                f'是 - 复制该版本全部明细\n'
                f'否 - 从当前草稿创建',
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Cancel:
                return
            if reply == QMessageBox.No:
                source_vid = None

        vid = CostVersionDAO.create_version(self.event_id, name.strip(), desc.strip(), source_version_id=source_vid)
        QMessageBox.information(self, '成功', f'版本已保存，ID: {vid}')
        self._refresh()

    def _set_current(self):
        item = self.version_list.currentItem()
        if not item or item.data(Qt.UserRole) is None:
            QMessageBox.information(self, '提示', '请选择一个版本')
            return
        vid = item.data(Qt.UserRole)
        CostVersionDAO.set_current_version(self.event_id, vid)
        self._refresh()
        QMessageBox.information(self, '成功', '已设为当前版本')

    def _delete(self):
        item = self.version_list.currentItem()
        if not item or item.data(Qt.UserRole) is None:
            QMessageBox.information(self, '提示', '请选择一个版本')
            return
        vid = item.data(Qt.UserRole)
        if QMessageBox.question(self, '确认', '确定删除该版本？该版本下的所有费用项将被删除。') == QMessageBox.Yes:
            CostVersionDAO.delete_version(vid)
            self._refresh()

    def _get_compare_versions(self):
        vid1 = self.cmb_comp_v1.currentData()
        vid2 = self.cmb_comp_v2.currentData()
        v1_name = self.cmb_comp_v1.currentText()
        v2_name = self.cmb_comp_v2.currentText()
        return vid1, vid2, v1_name, v2_name

    def _compare(self):
        vid1, vid2, v1_name, v2_name = self._get_compare_versions()
        if not vid1 or not vid2:
            QMessageBox.information(self, '提示', '请选择两个版本进行对比')
            return
        diff, cat_diff, g1, g2 = CostVersionDAO.compare_versions(self.event_id, vid1, vid2)
        lines = []
        lines.append(f'对比：{v1_name}  →  {v2_name}')
        lines.append(f'')
        lines.append(f'原金额：￥{g1:,.2f}')
        lines.append(f'新金额：￥{g2:,.2f}')
        sign = '+' if diff >= 0 else ''
        color = '#27ae60' if diff >= 0 else '#c0392b'
        lines.append(f'变动额：<span style=\"color:{color}\">{sign}￥{diff:,.2f}</span>')
        lines.append('')
        lines.append('分类变动：')
        for cat in CostItemDAO.CATEGORIES:
            d = cat_diff[cat]
            sign2 = '+' if d >= 0 else ''
            lines.append(f'  {cat}: {sign2}￥{d:,.2f}')
        self.lbl_compare.setText('<br>'.join(lines))

    def _compare_detail(self):
        vid1, vid2, v1_name, v2_name = self._get_compare_versions()
        if not vid1 or not vid2:
            QMessageBox.information(self, '提示', '请选择两个版本进行对比')
            return
        dlg = CompareDetailDialog(self, self.event_id, vid1, vid2, v1_name, v2_name)
        dlg.exec_()


class CompareDetailDialog(QDialog):
    def __init__(self, parent=None, event_id=None, vid1=None, vid2=None, v1_name='', v2_name=''):
        super().__init__(parent)
        self.event_id = event_id
        self.vid1 = vid1
        self.vid2 = vid2
        self.v1_name = v1_name
        self.v2_name = v2_name
        self.setWindowTitle(f'版本明细对比：{v1_name} → {v2_name}')
        self.resize(980, 640)
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Vertical)

        added_group = QGroupBox(f'✅ 新增项（{self.v2_name} 有，{self.v1_name} 无）')
        alayout = QVBoxLayout(added_group)
        self.table_added = self._create_table(['类别', '项目名称', '单价', '数量', '金额', '备注'])
        alayout.addWidget(self.table_added)
        splitter.addWidget(added_group)

        removed_group = QGroupBox(f'❌ 删除项（{self.v1_name} 有，{self.v2_name} 无）')
        rlayout = QVBoxLayout(removed_group)
        self.table_removed = self._create_table(['类别', '项目名称', '单价', '数量', '金额', '备注'])
        rlayout.addWidget(self.table_removed)
        splitter.addWidget(removed_group)

        changed_group = QGroupBox(f'🔄 变动项（单价或数量有变化）')
        clayout = QVBoxLayout(changed_group)
        self.table_changed = self._create_table(['类别', '项目名称', '变动说明', '原金额', '新金额', '变动额'])
        clayout.addWidget(self.table_changed)
        splitter.addWidget(changed_group)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 2)
        layout.addWidget(splitter, 1)

        summary_row = QHBoxLayout()
        self.lbl_summary = QLabel('')
        self.lbl_summary.setStyleSheet('font-size:11pt; font-weight:bold;')
        summary_row.addWidget(self.lbl_summary)
        summary_row.addStretch(1)
        btn_close = QPushButton('关闭')
        btn_close.clicked.connect(self.accept)
        summary_row.addWidget(btn_close)
        layout.addLayout(summary_row)

    def _create_table(self, headers):
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        return table

    def _load_data(self):
        added, removed, changed = CostVersionDAO.compare_versions_detail(
            self.event_id, self.vid1, self.vid2
        )

        self._fill_table(self.table_added, added, ['category', 'item_name', 'price', 'qty', 'amount', ''], True)
        self._fill_table(self.table_removed, removed, ['category', 'item_name', 'price', 'qty', 'amount', ''], False)

        for c in changed:
            row = self.table_changed.rowCount()
            self.table_changed.insertRow(row)
            values = [c['category'], c['item_name'], c['change_desc'],
                      f"￥{c['amount_old']:,.2f}", f"￥{c['amount_new']:,.2f}"]
            for col, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                if col < 3:
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table_changed.setItem(row, col, item)
            diff_item = QTableWidgetItem(f"{c['amount_change']:+,.2f}")
            diff_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if c['amount_change'] > 0:
                diff_item.setForeground(QColor('#c0392b'))
            elif c['amount_change'] < 0:
                diff_item.setForeground(QColor('#27ae60'))
            diff_item.setFont(self._bold_font())
            self.table_changed.setItem(row, 5, diff_item)

        total_added = sum(a['amount'] for a in added)
        total_removed = sum(r['amount'] for r in removed)
        total_changed = sum(c['amount_change'] for c in changed)
        total_diff = total_added - total_removed + total_changed

        summary_parts = []
        if added:
            summary_parts.append(f'新增 {len(added)} 项 +￥{total_added:,.2f}')
        if removed:
            summary_parts.append(f'删除 {len(removed)} 项 -￥{total_removed:,.2f}')
        if changed:
            sign = '+' if total_changed >= 0 else ''
            summary_parts.append(f'变动 {len(changed)} 项 {sign}￥{total_changed:,.2f}')

        total_sign = '+' if total_diff >= 0 else ''
        color = '#c0392b' if total_diff > 0 else '#27ae60' if total_diff < 0 else '#333'
        self.lbl_summary.setText(
            '  |  '.join(summary_parts) +
            f'  |  <span style=\"color:{color}\">净变动：{total_sign}￥{total_diff:,.2f}</span>'
        )

    def _fill_table(self, table, data, fields, is_added):
        for d in data:
            row = table.rowCount()
            table.insertRow(row)
            for col, f in enumerate(fields):
                val = d.get(f, '') if f else ''
                item = QTableWidgetItem(str(val))
                if col in (2, 3, 4) and f and isinstance(d.get(f, ''), (int, float)):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    if col == 4:
                        if is_added:
                            item.setForeground(QColor('#c0392b'))
                        else:
                            item.setForeground(QColor('#27ae60'))
                        item.setFont(self._bold_font())
                else:
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                table.setItem(row, col, item)

    def _bold_font(self):
        from PyQt5.QtGui import QFont
        f = QFont()
        f.setBold(True)
        return f
