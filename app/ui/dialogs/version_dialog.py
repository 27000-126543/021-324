from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
                             QListWidgetItem, QFormLayout, QLineEdit, QTextEdit,
                             QMessageBox, QLabel, QInputDialog, QGroupBox)
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

        comp_group = QGroupBox('版本对比（与当前版本）')
        complayout = QVBoxLayout(comp_group)
        self.lbl_compare = QLabel('请在左侧选择要对比的版本')
        self.lbl_compare.setWordWrap(True)
        complayout.addWidget(self.lbl_compare)

        btn_comp = QPushButton('⏱ 与选中版本对比金额变化')
        btn_comp.clicked.connect(self._compare)
        complayout.addWidget(btn_comp)
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
        vid = CostVersionDAO.create_version(self.event_id, name.strip(), desc.strip())
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

    def _compare(self):
        item = self.version_list.currentItem()
        if not item or item.data(Qt.UserRole) is None:
            QMessageBox.information(self, '提示', '请选择要对比的版本')
            return
        vid1 = item.data(Qt.UserRole)
        cur = CostVersionDAO.get_current_version(self.event_id)
        if not cur:
            QMessageBox.information(self, '提示', '当前还没有版本，无法对比')
            return
        vid2 = cur['id']
        diff, cat_diff, g1, g2 = CostVersionDAO.compare_versions(self.event_id, vid1, vid2)
        lines = []
        v1_name = item.text().split(' - ')[0]
        v2_name = cur['version_name']
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
