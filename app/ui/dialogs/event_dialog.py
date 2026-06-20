from PyQt5.QtWidgets import (QDialog, QFormLayout, QLineEdit, QComboBox, QDateEdit,
                             QTextEdit, QCheckBox, QDialogButtonBox, QVBoxLayout,
                             QMessageBox)
from PyQt5.QtCore import QDate, Qt
from app.db.dao import EventDAO


class EventDialog(QDialog):
    EVENT_TYPES = ['停工', '窝工', '间歇施工']
    RESPONSIBLE_PARTIES = ['业主', '监理', '设计', '施工方', '第三方', '待确认']

    def __init__(self, parent=None, event_id=None):
        super().__init__(parent)
        self.event_id = event_id
        self.setWindowTitle('编辑事件' if event_id else '新增事件')
        self.setMinimumWidth(520)
        self._init_ui()
        if event_id:
            self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.cmb_type = QComboBox()
        self.cmb_type.addItems(self.EVENT_TYPES)
        form.addRow('事件类型：', self.cmb_type)

        self.txt_contract = QLineEdit()
        self.txt_contract.setPlaceholderText('如：K0+000~K5+000')
        form.addRow('合同段：', self.txt_contract)

        self.txt_area = QLineEdit()
        self.txt_area.setPlaceholderText('如：1#桥墩、主桥箱梁')
        form.addRow('影响部位：', self.txt_area)

        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDisplayFormat('yyyy-MM-dd')
        self.date_start.setDate(QDate.currentDate())
        form.addRow('开始日期：', self.date_start)

        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDisplayFormat('yyyy-MM-dd')
        self.date_end.setDate(QDate.currentDate())
        self.date_end.setSpecialValueText(' ')
        form.addRow('结束日期：', self.date_end)

        self.cmb_responsible = QComboBox()
        self.cmb_responsible.addItems(self.RESPONSIBLE_PARTIES)
        form.addRow('责任方初判：', self.cmb_responsible)

        self.txt_notice = QLineEdit()
        self.txt_notice.setPlaceholderText('监理通知编号')
        form.addRow('监理通知编号：', self.txt_notice)

        self.txt_order = QLineEdit()
        self.txt_order.setPlaceholderText('业主指令编号')
        form.addRow('业主指令编号：', self.txt_order)

        self.chk_visa = QCheckBox('已收到现场签证单')
        self.chk_resume = QCheckBox('已收到复工令')
        form.addRow('', self.chk_visa)
        form.addRow('', self.chk_resume)

        self.cmb_follow = QComboBox()
        for code, label in EventDAO.FOLLOW_STATUSES:
            self.cmb_follow.addItem(label, code)
        form.addRow('跟进状态：', self.cmb_follow)

        self.txt_desc = QTextEdit()
        self.txt_desc.setPlaceholderText('事件详细描述，包括原因、影响范围、处理过程等')
        self.txt_desc.setMaximumHeight(100)
        form.addRow('事件描述：', self.txt_desc)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_data(self):
        data = EventDAO.get_by_id(self.event_id)
        if data:
            idx = self.cmb_type.findText(data.get('event_type', ''))
            if idx >= 0:
                self.cmb_type.setCurrentIndex(idx)
            self.txt_contract.setText(data.get('contract_section', ''))
            self.txt_area.setText(data.get('affected_area', ''))
            if data.get('start_date'):
                self.date_start.setDate(QDate.fromString(data['start_date'], 'yyyy-MM-dd'))
            if data.get('end_date'):
                self.date_end.setDate(QDate.fromString(data['end_date'], 'yyyy-MM-dd'))
            idx = self.cmb_responsible.findText(data.get('responsible_party', ''))
            if idx >= 0:
                self.cmb_responsible.setCurrentIndex(idx)
            self.txt_notice.setText(data.get('supervision_notice_no', ''))
            self.txt_order.setText(data.get('owner_order_no', ''))
            self.chk_visa.setChecked(bool(data.get('visa_received')))
            self.chk_resume.setChecked(bool(data.get('resume_order_received')))
            fs = data.get('follow_status', '')
            idx = self.cmb_follow.findData(fs)
            if idx >= 0:
                self.cmb_follow.setCurrentIndex(idx)
            self.txt_desc.setPlainText(data.get('description', ''))

    def _on_accept(self):
        if not self.date_start.date().isValid():
            QMessageBox.warning(self, '提示', '请填写开始日期')
            return
        data = {
            'event_type': self.cmb_type.currentText(),
            'contract_section': self.txt_contract.text().strip(),
            'affected_area': self.txt_area.text().strip(),
            'start_date': self.date_start.date().toString('yyyy-MM-dd'),
            'end_date': self.date_end.date().toString('yyyy-MM-dd') if self.date_end.date().isValid() else '',
            'responsible_party': self.cmb_responsible.currentText(),
            'supervision_notice_no': self.txt_notice.text().strip(),
            'owner_order_no': self.txt_order.text().strip(),
            'description': self.txt_desc.toPlainText().strip(),
            'visa_received': 1 if self.chk_visa.isChecked() else 0,
            'resume_order_received': 1 if self.chk_resume.isChecked() else 0,
            'follow_status': self.cmb_follow.currentData(),
        }
        if self.event_id:
            EventDAO.update(self.event_id, data)
        else:
            EventDAO.create(data)
        self.accept()
