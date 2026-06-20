from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox, QComboBox, QLabel,
                             QLineEdit, QDoubleSpinBox, QFormLayout, QSplitter, QGroupBox,
                             QTextEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from app.db.dao import CostItemDAO, EventDAO, MachineryDAO, LaborDAO


class CostCalcWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel('选择事件：'))
        self.cmb_events = QComboBox()
        self.cmb_events.setMinimumWidth(360)
        self.cmb_events.currentIndexChanged.connect(self._on_event_changed)
        top.addWidget(self.cmb_events, 1)

        btn_refresh = QPushButton('刷新事件列表')
        btn_refresh.clicked.connect(self._refresh_events)
        top.addWidget(btn_refresh)

        layout.addLayout(top)

        splitter = QSplitter(Qt.Vertical)

        input_group = QGroupBox('费用明细录入（人工费 / 机械费 / 周转材料费 / 管理费）')
        ilayout = QVBoxLayout(input_group)
        form = QFormLayout()
        row = QHBoxLayout()

        self.cmb_cat = QComboBox()
        self.cmb_cat.addItems(CostItemDAO.CATEGORIES)

        self.txt_item = QLineEdit()
        self.txt_item.setPlaceholderText('项目名称，如：普工窝工、挖机停置')

        self.spin_price = QDoubleSpinBox()
        self.spin_price.setRange(0, 999999.99)
        self.spin_price.setDecimals(2)
        self.spin_price.setPrefix('￥')
        self.spin_price.setSuffix(' /单位')

        self.spin_qty = QDoubleSpinBox()
        self.spin_qty.setRange(0, 999999.99)
        self.spin_qty.setDecimals(2)

        self.txt_unit = QLineEdit()
        self.txt_unit.setPlaceholderText('单位，如：工日、台·天')
        self.txt_unit.setMaximumWidth(100)

        self.txt_remark = QLineEdit()
        self.txt_remark.setPlaceholderText('备注')

        btn_add = QPushButton('添加')
        btn_add.clicked.connect(self._add_item)

        row.addWidget(QLabel('类别：'))
        row.addWidget(self.cmb_cat)
        row.addWidget(QLabel('项目：'))
        row.addWidget(self.txt_item, 1)
        row.addWidget(QLabel('单价：'))
        row.addWidget(self.spin_price)
        row.addWidget(QLabel('数量：'))
        row.addWidget(self.spin_qty)
        row.addWidget(QLabel('单位：'))
        row.addWidget(self.txt_unit)
        row.addWidget(QLabel('备注：'))
        row.addWidget(self.txt_remark, 1)
        row.addWidget(btn_add)
        form.addRow(row)
        ilayout.addLayout(form)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            'ID', '费用类别', '项目名称', '单价(元)', '数量', '单位', '金额(元)', '备注'
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.DoubleClicked)
        self.table.setColumnHidden(0, True)
        self.table.itemChanged.connect(self._on_item_changed)
        ilayout.addWidget(self.table, 1)

        btn_row = QHBoxLayout()
        btn_import_mach = QPushButton('⬇ 从机械清单导入')
        btn_import_mach.clicked.connect(self._import_machinery)
        btn_import_labor = QPushButton('⬇ 从劳务班组导入')
        btn_import_labor.clicked.connect(self._import_labor)
        btn_del = QPushButton('删除选中')
        btn_del.clicked.connect(self._delete_item)
        btn_row.addWidget(btn_import_mach)
        btn_row.addWidget(btn_import_labor)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_del)
        ilayout.addLayout(btn_row)

        splitter.addWidget(input_group)

        summary_group = QGroupBox('索赔金额汇总表（一页纸口径）')
        slayout = QVBoxLayout(summary_group)

        self.txt_summary = QTextEdit()
        self.txt_summary.setReadOnly(True)
        self.txt_summary.setStyleSheet('font-family: "Microsoft YaHei"; font-size: 11pt; background: #fefefe;')
        slayout.addWidget(self.txt_summary)

        sbtn = QHBoxLayout()
        self.btn_export = QPushButton('导出 Excel 汇总表')
        self.btn_export.clicked.connect(self._export)
        sbtn.addStretch(1)
        sbtn.addWidget(self.btn_export)
        slayout.addLayout(sbtn)

        splitter.addWidget(summary_group)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter, 1)
        self._refresh_events()

    def _refresh_events(self):
        self.cmb_events.blockSignals(True)
        self.cmb_events.clear()
        events = EventDAO.get_all()
        for e in events:
            label = f"[{e.get('event_type','')}] {e.get('start_date','')} {e.get('affected_area','')} {e.get('contract_section','')}"
            self.cmb_events.addItem(label, e['id'])
        self.cmb_events.blockSignals(False)
        self._on_event_changed()

    def _get_current_event_id(self):
        return self.cmb_events.currentData()

    def _on_event_changed(self):
        eid = self._get_current_event_id()
        if not eid:
            self.table.setRowCount(0)
            self.txt_summary.clear()
            return
        self._refresh_items()
        self._update_summary()

    def _refresh_items(self):
        eid = self._get_current_event_id()
        if not eid:
            return
        self.table.blockSignals(True)
        items = CostItemDAO.get_by_event(eid)
        self.table.setRowCount(len(items))
        for i, it in enumerate(items):
            self.table.setItem(i, 0, QTableWidgetItem(str(it['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(it['cost_category']))
            self.table.setItem(i, 2, QTableWidgetItem(it['item_name']))
            self.table.setItem(i, 3, QTableWidgetItem(f"{it['unit_price']:.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem(f"{it['quantity']:.2f}"))
            self.table.setItem(i, 5, QTableWidgetItem(it.get('unit', '')))
            amount = it['unit_price'] * it['quantity']
            amt_item = QTableWidgetItem(f"{amount:.2f}")
            amt_item.setForeground(QColor('#2980b9'))
            self.table.setItem(i, 6, amt_item)
            self.table.setItem(i, 7, QTableWidgetItem(it.get('remark', '')))
        self.table.blockSignals(False)

    def _add_item(self):
        eid = self._get_current_event_id()
        if not eid:
            QMessageBox.information(self, '提示', '请先选择一个事件')
            return
        if not self.txt_item.text().strip():
            QMessageBox.information(self, '提示', '请填写项目名称')
            return
        CostItemDAO.create({
            'event_id': eid,
            'cost_category': self.cmb_cat.currentText(),
            'item_name': self.txt_item.text().strip(),
            'unit_price': self.spin_price.value(),
            'quantity': self.spin_qty.value(),
            'unit': self.txt_unit.text().strip(),
            'remark': self.txt_remark.text().strip(),
        })
        self.txt_item.clear()
        self.txt_remark.clear()
        self.spin_price.setValue(0)
        self.spin_qty.setValue(0)
        self._refresh_items()
        self._update_summary()

    def _delete_item(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, '提示', '请选择一行')
            return
        cid = int(self.table.item(row, 0).text())
        if QMessageBox.question(self, '确认', '确定删除该费用项？') == QMessageBox.Yes:
            CostItemDAO.delete(cid)
            self._refresh_items()
            self._update_summary()

    def _on_item_changed(self, item):
        row = item.row()
        if self.table.item(row, 0) is None:
            return
        cid = int(self.table.item(row, 0).text())

        col = item.column()
        is_numeric_col = col in (3, 4)
        price_text = self.table.item(row, 3).text().strip()
        qty_text = self.table.item(row, 4).text().strip()

        if is_numeric_col:
            try:
                price = float(price_text) if price_text else 0.0
            except ValueError:
                price = None
            try:
                qty = float(qty_text) if qty_text else 0.0
            except ValueError:
                qty = None

            if price is None or qty is None:
                QMessageBox.warning(self, '输入有误', '单价和数量必须是数字，请重新输入！\n已恢复为原来的数值。')
                self.table.blockSignals(True)
                items = CostItemDAO.get_by_event(self._get_current_event_id())
                for it in items:
                    if it['id'] == cid:
                        self.table.item(row, 3).setText(f"{it['unit_price']:.2f}")
                        self.table.item(row, 4).setText(f"{it['quantity']:.2f}")
                        break
                self.table.blockSignals(False)
                return
        else:
            price = float(price_text) if price_text else 0.0
            qty = float(qty_text) if qty_text else 0.0

        data = {
            'cost_category': self.table.item(row, 1).text(),
            'item_name': self.table.item(row, 2).text(),
            'unit_price': price,
            'quantity': qty,
            'unit': self.table.item(row, 5).text(),
            'remark': self.table.item(row, 7).text(),
        }
        CostItemDAO.update(cid, data)
        self._refresh_items()
        self._update_summary()

    def _update_summary(self):
        eid = self._get_current_event_id()
        if not eid:
            self.txt_summary.clear()
            return
        event = EventDAO.get_by_id(eid)
        items_by_cat, totals, grand = CostItemDAO.get_summary(eid)

        lines = []
        lines.append(' ' * 30 + '停窝工索赔费用汇总表')
        lines.append('')
        lines.append(f"事件编号：{event.get('id', '')}")
        lines.append(f"事件类型：{event.get('event_type', '')}")
        lines.append(f"合同段：{event.get('contract_section', '')}    影响部位：{event.get('affected_area', '')}")
        lines.append(f"起止时间：{event.get('start_date', '')} 至 {event.get('end_date', '（进行中）')}")
        lines.append(f"责任方：{event.get('responsible_party', '')}")
        lines.append(f"监理通知：{event.get('supervision_notice_no', '')}   业主指令：{event.get('owner_order_no', '')}")
        lines.append('—' * 70)

        for cat in CostItemDAO.CATEGORIES:
            lines.append(f"【{cat}】")
            lines.append(f"  {'序号':<4}{'项目名称':<20}{'单价(元)':<12}{'数量':<10}{'单位':<8}{'金额(元)':<12}{'备注'}")
            cat_items = items_by_cat.get(cat, [])
            if not cat_items:
                lines.append('  ' + '(无)')
            for i, it in enumerate(cat_items, 1):
                lines.append(
                    f"  {i:<4}{it['item_name']:<20}{it['unit_price']:<12.2f}{it['quantity']:<10.2f}"
                    f"{it.get('unit',''):<8}{it['amount']:<12.2f}{it.get('remark','')}"
                )
            lines.append(f"  【{cat}小计】￥{totals[cat]:,.2f}")
            lines.append('')

        lines.append('—' * 70)
        lines.append(f"  索赔金额合计（大写）：{self._num_to_chinese(grand)}")
        lines.append(f"  索赔金额合计（小写）：￥{grand:,.2f}")
        lines.append('')
        missing = EventDAO.get_missing_docs(eid)
        if missing:
            lines.append(f"  ⚠ 支撑材料待补：{'、'.join(missing)}")
        else:
            lines.append('  ✔ 支撑材料齐全，可提交确认')
        lines.append('')
        lines.append('  商务经理：              项目经理：              日期：')
        self.txt_summary.setPlainText('\n'.join(lines))

    @staticmethod
    def _num_to_chinese(n):
        if not n:
            return '零元整'
        digits = '零壹贰叁肆伍陆柒捌玖'
        units = ['', '拾', '佰', '仟', '万', '拾', '佰', '仟', '亿']
        integer_part = int(n)
        dec_part = round((n - integer_part) * 100)
        result = ''
        s = str(integer_part)
        for i, c in enumerate(reversed(s)):
            d = int(c)
            if d:
                result = digits[d] + units[i] + result
            else:
                if result and not result.startswith('零'):
                    result = '零' + result
        result = result.rstrip('零') + '元'
        if dec_part == 0:
            result += '整'
        else:
            jiao = dec_part // 10
            fen = dec_part % 10
            if jiao:
                result += digits[jiao] + '角'
            if fen:
                result += digits[fen] + '分'
        return result

    def _import_machinery(self):
        eid = self._get_current_event_id()
        if not eid:
            QMessageBox.information(self, '提示', '请先选择一个事件')
            return
        machines = MachineryDAO.get_by_event(eid)
        if not machines:
            QMessageBox.information(self, '提示', '该事件暂无机械停置清单记录')
            return

        existing = CostItemDAO.get_by_event(eid)
        existing_names = {it['item_name'] for it in existing if it['cost_category'] == '机械费'}

        added = 0
        skipped = 0
        for m in machines:
            name = f"{m['machine_name']}停置"
            if m.get('specification'):
                name = f"{m['machine_name']}（{m['specification']}）停置"
            if name in existing_names:
                skipped += 1
                continue
            CostItemDAO.create({
                'event_id': eid,
                'cost_category': '机械费',
                'item_name': name,
                'unit_price': 0,
                'quantity': m.get('quantity', 0),
                'unit': m.get('unit', '台·天'),
                'remark': f"来自机械清单（{m['record_date']}）",
            })
            existing_names.add(name)
            added += 1

        self._refresh_items()
        self._update_summary()
        QMessageBox.information(self, '导入完成', f'成功导入 {added} 项，跳过重复 {skipped} 项\n请在表格中补充单价后即可计算金额')

    def _import_labor(self):
        eid = self._get_current_event_id()
        if not eid:
            QMessageBox.information(self, '提示', '请先选择一个事件')
            return
        labors = LaborDAO.get_by_event(eid)
        if not labors:
            QMessageBox.information(self, '提示', '该事件暂无劳务班组人数记录')
            return

        existing = CostItemDAO.get_by_event(eid)
        existing_names = {it['item_name'] for it in existing if it['cost_category'] == '人工费'}

        added = 0
        skipped = 0
        for l in labors:
            work_type = l.get('work_type', '') or '普工'
            name = f"{l['team_name']}（{work_type}）窝工"
            if name in existing_names:
                skipped += 1
                continue
            CostItemDAO.create({
                'event_id': eid,
                'cost_category': '人工费',
                'item_name': name,
                'unit_price': 0,
                'quantity': l.get('worker_count', 0),
                'unit': '工日',
                'remark': f"来自劳务清单（{l['record_date']}）",
            })
            existing_names.add(name)
            added += 1

        self._refresh_items()
        self._update_summary()
        QMessageBox.information(self, '导入完成', f'成功导入 {added} 项，跳过重复 {skipped} 项\n请在表格中补充单价后即可计算金额')

    def _export(self):
        from app.utils.exporter import export_summary
        eid = self._get_current_event_id()
        if not eid:
            QMessageBox.information(self, '提示', '请先选择一个事件')
            return
        path = export_summary(eid)
        if path:
            QMessageBox.information(self, '成功', f'已导出：\n{path}')
