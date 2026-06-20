from datetime import datetime
from .database import get_connection


def _now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


class EventDAO:
    @staticmethod
    def create(data):
        conn = get_connection()
        cursor = conn.cursor()
        now = _now()
        cursor.execute('''
            INSERT INTO events (event_type, contract_section, affected_area, start_date, end_date,
                                responsible_party, supervision_notice_no, owner_order_no, description,
                                visa_received, resume_order_received, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('event_type', ''),
            data.get('contract_section', ''),
            data.get('affected_area', ''),
            data.get('start_date', ''),
            data.get('end_date', ''),
            data.get('responsible_party', ''),
            data.get('supervision_notice_no', ''),
            data.get('owner_order_no', ''),
            data.get('description', ''),
            data.get('visa_received', 0),
            data.get('resume_order_received', 0),
            now, now
        ))
        conn.commit()
        event_id = cursor.lastrowid
        conn.close()
        return event_id

    @staticmethod
    def update(event_id, data):
        conn = get_connection()
        cursor = conn.cursor()
        now = _now()
        cursor.execute('''
            UPDATE events SET event_type=?, contract_section=?, affected_area=?, start_date=?, end_date=?,
                              responsible_party=?, supervision_notice_no=?, owner_order_no=?, description=?,
                              visa_received=?, resume_order_received=?, updated_at=?
            WHERE id=?
        ''', (
            data.get('event_type', ''),
            data.get('contract_section', ''),
            data.get('affected_area', ''),
            data.get('start_date', ''),
            data.get('end_date', ''),
            data.get('responsible_party', ''),
            data.get('supervision_notice_no', ''),
            data.get('owner_order_no', ''),
            data.get('description', ''),
            data.get('visa_received', 0),
            data.get('resume_order_received', 0),
            now, event_id
        ))
        conn.commit()
        conn.close()

    @staticmethod
    def delete(event_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM events WHERE id=?', (event_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_id(event_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM events WHERE id=?', (event_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_all():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM events ORDER BY start_date DESC, id DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_missing_docs(event_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM events WHERE id=?', (event_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return []
        missing = []
        if not row['visa_received']:
            missing.append('现场签证单')
        if not row['resume_order_received']:
            missing.append('复工令')
        cursor2 = get_connection().cursor()
        cursor2.execute('SELECT COUNT(*) as cnt FROM photos WHERE event_id=?', (event_id,))
        if cursor2.fetchone()['cnt'] == 0:
            missing.append('现场照片')
        cursor2.execute('SELECT COUNT(*) as cnt FROM machinery WHERE event_id=?', (event_id,))
        if cursor2.fetchone()['cnt'] == 0:
            missing.append('机械停置清单')
        cursor2.execute('SELECT COUNT(*) as cnt FROM labor WHERE event_id=?', (event_id,))
        if cursor2.fetchone()['cnt'] == 0:
            missing.append('劳务班组人数记录')
        cursor2.close()
        cursor2.connection.close()
        return missing


class PhotoDAO:
    @staticmethod
    def create(data):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO photos (event_id, record_date, file_path, remark, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['event_id'], data['record_date'], data['file_path'], data.get('remark', ''), _now()))
        conn.commit()
        pid = cursor.lastrowid
        conn.close()
        return pid

    @staticmethod
    def get_by_event(event_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM photos WHERE event_id=? ORDER BY record_date DESC', (event_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def delete(photo_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM photos WHERE id=?', (photo_id,))
        conn.commit()
        conn.close()


class MachineryDAO:
    @staticmethod
    def create(data):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO machinery (event_id, record_date, machine_name, specification, quantity, unit, remark, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['event_id'], data['record_date'], data['machine_name'], data.get('specification', ''),
              data.get('quantity', 0), data.get('unit', '台·天'), data.get('remark', ''), _now()))
        conn.commit()
        mid = cursor.lastrowid
        conn.close()
        return mid

    @staticmethod
    def update(mid, data):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE machinery SET record_date=?, machine_name=?, specification=?, quantity=?, unit=?, remark=?
            WHERE id=?
        ''', (data['record_date'], data['machine_name'], data.get('specification', ''),
              data.get('quantity', 0), data.get('unit', '台·天'), data.get('remark', ''), mid))
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_event(event_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM machinery WHERE event_id=? ORDER BY record_date DESC', (event_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def delete(mid):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM machinery WHERE id=?', (mid,))
        conn.commit()
        conn.close()


class LaborDAO:
    @staticmethod
    def create(data):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO labor (event_id, record_date, team_name, worker_count, work_type, remark, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (data['event_id'], data['record_date'], data['team_name'], data.get('worker_count', 0),
              data.get('work_type', ''), data.get('remark', ''), _now()))
        conn.commit()
        lid = cursor.lastrowid
        conn.close()
        return lid

    @staticmethod
    def update(lid, data):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE labor SET record_date=?, team_name=?, worker_count=?, work_type=?, remark=?
            WHERE id=?
        ''', (data['record_date'], data['team_name'], data.get('worker_count', 0),
              data.get('work_type', ''), data.get('remark', ''), lid))
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_event(event_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM labor WHERE event_id=? ORDER BY record_date DESC', (event_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def delete(lid):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM labor WHERE id=?', (lid,))
        conn.commit()
        conn.close()


class CostItemDAO:
    CATEGORIES = ['人工费', '机械费', '周转材料费', '管理费']

    @staticmethod
    def create(data):
        conn = get_connection()
        cursor = conn.cursor()
        now = _now()
        cursor.execute('''
            INSERT INTO cost_items (event_id, cost_category, item_name, unit_price, quantity, unit, remark, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['event_id'], data['cost_category'], data['item_name'],
              data.get('unit_price', 0), data.get('quantity', 0), data.get('unit', ''),
              data.get('remark', ''), now, now))
        conn.commit()
        cid = cursor.lastrowid
        conn.close()
        return cid

    @staticmethod
    def update(cid, data):
        conn = get_connection()
        cursor = conn.cursor()
        now = _now()
        cursor.execute('''
            UPDATE cost_items SET cost_category=?, item_name=?, unit_price=?, quantity=?, unit=?, remark=?, updated_at=?
            WHERE id=?
        ''', (data['cost_category'], data['item_name'], data.get('unit_price', 0),
              data.get('quantity', 0), data.get('unit', ''), data.get('remark', ''), now, cid))
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_event(event_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cost_items WHERE event_id=? ORDER BY cost_category, id', (event_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def delete(cid):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cost_items WHERE id=?', (cid,))
        conn.commit()
        conn.close()

    @staticmethod
    def get_summary(event_id):
        items = CostItemDAO.get_by_event(event_id)
        result = {cat: [] for cat in CostItemDAO.CATEGORIES}
        totals = {cat: 0.0 for cat in CostItemDAO.CATEGORIES}
        for item in items:
            cat = item['cost_category']
            if cat in result:
                amount = item['unit_price'] * item['quantity']
                item['amount'] = amount
                result[cat].append(item)
                totals[cat] += amount
        grand_total = sum(totals.values())
        return result, totals, grand_total
