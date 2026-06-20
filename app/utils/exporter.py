import os
from datetime import datetime
from PyQt5.QtWidgets import QFileDialog
from app.db.dao import CostItemDAO, EventDAO


def export_summary(event_id):
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

    event = EventDAO.get_by_id(event_id)
    if not event:
        return None

    default_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'data', 'exports')
    default_dir = os.path.abspath(default_dir)
    if not os.path.exists(default_dir):
        os.makedirs(default_dir)
    default_name = f"索赔汇总表_{event.get('contract_section','')}_{event.get('start_date','')}.xlsx".replace('/', '-')
    path, _ = QFileDialog.getSaveFileName(None, '导出汇总表', os.path.join(default_dir, default_name), 'Excel 文件 (*.xlsx)')
    if not path:
        return None

    wb = Workbook()
    ws = wb.active
    ws.title = '索赔汇总'

    thin = Side(border_style='thin', color='000000')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    center = Alignment(horizontal='center', vertical='center', wrap_text=True)
    left = Alignment(horizontal='left', vertical='center', wrap_text=True)
    title_font = Font(name='微软雅黑', size=16, bold=True)
    header_font = Font(name='微软雅黑', size=11, bold=True)
    normal_font = Font(name='微软雅黑', size=10)
    header_fill = PatternFill('solid', fgColor='DCE6F1')
    total_fill = PatternFill('solid', fgColor='FCE4D6')

    ws.merge_cells('A1:G1')
    c = ws['A1']
    c.value = '停窝工索赔费用汇总表'
    c.font = title_font
    c.alignment = center

    row = 3
    info = [
        ('事件编号', event.get('id', '')),
        ('事件类型', event.get('event_type', '')),
        ('合同段', event.get('contract_section', '')),
        ('影响部位', event.get('affected_area', '')),
        ('起止时间', f"{event.get('start_date', '')} 至 {event.get('end_date', '（进行中）')}"),
        ('责任方', event.get('responsible_party', '')),
        ('监理通知', event.get('supervision_notice_no', '')),
        ('业主指令', event.get('owner_order_no', '')),
    ]
    for k, v in info:
        ws.cell(row=row, column=1, value=k).font = header_font
        ws.cell(row=row, column=1).alignment = left
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=7)
        c = ws.cell(row=row, column=2, value=v)
        c.font = normal_font
        c.alignment = left
        row += 1

    row += 1

    items_by_cat, totals, grand = CostItemDAO.get_summary(event_id)
    for cat in CostItemDAO.CATEGORIES:
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=7)
        c = ws.cell(row=row, column=1, value=f'【{cat}】')
        c.font = header_font
        c.fill = header_fill
        c.alignment = left
        for col in range(1, 8):
            ws.cell(row=row, column=col).border = border
        row += 1

        headers = ['序号', '项目名称', '单价(元)', '数量', '单位', '金额(元)', '备注']
        for col, h in enumerate(headers, 1):
            c = ws.cell(row=row, column=col, value=h)
            c.font = header_font
            c.alignment = center
            c.border = border
        row += 1

        cat_items = items_by_cat.get(cat, [])
        if not cat_items:
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=7)
            c = ws.cell(row=row, column=1, value='（无）')
            c.font = normal_font
            c.alignment = center
            for col in range(1, 8):
                ws.cell(row=row, column=col).border = border
            row += 1
        for i, it in enumerate(cat_items, 1):
            values = [i, it['item_name'], it['unit_price'], it['quantity'],
                      it.get('unit', ''), it['amount'], it.get('remark', '')]
            for col, val in enumerate(values, 1):
                c = ws.cell(row=row, column=col, value=val)
                c.font = normal_font
                c.alignment = center if col in (1, 3, 4, 5, 6) else left
                c.border = border
                if col in (3, 6):
                    c.number_format = '0.00'
            row += 1

        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
        c = ws.cell(row=row, column=1, value=f'{cat} 小计')
        c.font = header_font
        c.fill = total_fill
        c.alignment = Alignment(horizontal='right', vertical='center')
        for col in range(1, 6):
            ws.cell(row=row, column=col).border = border
            ws.cell(row=row, column=col).fill = total_fill
        c6 = ws.cell(row=row, column=6, value=totals[cat])
        c6.font = header_font
        c6.fill = total_fill
        c6.alignment = center
        c6.number_format = '0.00'
        c6.border = border
        ws.cell(row=row, column=7).fill = total_fill
        ws.cell(row=row, column=7).border = border
        row += 2

    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=7)
    c = ws.cell(row=row, column=1, value='索赔金额合计（大写）：' + CostCalcWidget_num2chinese(grand))
    c.font = Font(name='微软雅黑', size=11, bold=True)
    c.alignment = left
    row += 1
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=7)
    c = ws.cell(row=row, column=1, value=f'索赔金额合计（小写）：￥{grand:,.2f}')
    c.font = Font(name='微软雅黑', size=14, bold=True, color='C00000')
    c.alignment = left
    row += 2

    missing = EventDAO.get_missing_docs(event_id)
    if missing:
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=7)
        c = ws.cell(row=row, column=1, value='⚠ 支撑材料待补：' + '、'.join(missing))
        c.font = Font(name='微软雅黑', size=10, color='C00000')
        row += 1
    else:
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=7)
        c = ws.cell(row=row, column=1, value='✔ 支撑材料齐全，可提交确认')
        c.font = Font(name='微软雅黑', size=10, color='008000')
        row += 1

    row += 1
    sign = ['商务经理签字：______________', '项目经理签字：______________', f"日期：{datetime.now().strftime('%Y年%m月%d日')}"]
    for s in sign:
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
        ws.cell(row=row, column=1, value=s).font = normal_font
        row += 1

    widths = [8, 28, 12, 10, 8, 14, 20]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + i)].width = w

    wb.save(path)
    return path


def CostCalcWidget_num2chinese(n):
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
