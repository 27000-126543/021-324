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
    def filter(event_type=None, contract_section=None, responsible_party=None,
               date_from=None, date_to=None, missing_only=False, keyword=None):
        conn = get_connection()
        cursor = conn.cursor()
        sql = 'SELECT * FROM events WHERE 1=1'
        params = []
        if event_type and event_type != '全部':
            sql += ' AND event_type=?'
            params.append(event_type)
        if contract_section and contract_section != '全部':
            sql += ' AND contract_section LIKE ?'
            params.append(f'%{contract_section}%')
        if responsible_party and responsible_party != '全部':
            sql += ' AND responsible_party=?'
            params.append(responsible_party)
        if date_from:
            sql += ' AND start_date >= ?'
            params.append(date_from)
        if date_to:
            sql += ' AND start_date <= ?'
            params.append(date_to)
        if keyword:
            sql += ' AND (affected_area LIKE ? OR description LIKE ? OR supervision_notice_no LIKE ? OR owner_order_no LIKE ?)'
            k = f'%{keyword}%'
            params.extend([k, k, k, k])
        sql += ' ORDER BY start_date DESC, id DESC'
        cursor.execute(sql, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        if missing_only:
            rows = [r for r in rows if EventDAO.get_missing_docs(r['id'])]
        return rows

    @staticmethod
    def get_unique_contract_sections():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT contract_section FROM events WHERE contract_section IS NOT NULL AND contract_section <> '' ORDER BY contract_section")
        rows = [r[0] for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_missing_docs(event_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM events WHERE id=?', (event_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return []

        cursor.execute('SELECT doc_type, COUNT(*) as cnt FROM documents WHERE event_id=? GROUP BY doc_type', (event_id,))
        doc_counts = {r['doc_type']: r['cnt'] for r in cursor.fetchall()}

        cursor.execute('SELECT COUNT(*) as cnt FROM photos WHERE event_id=?', (event_id,))
        photo_count = cursor.fetchone()['cnt']

        cursor.execute('SELECT COUNT(*) as cnt FROM machinery WHERE event_id=?', (event_id,))
        machine_count = cursor.fetchone()['cnt']

        cursor.execute('SELECT COUNT(*) as cnt FROM labor WHERE event_id=?', (event_id,))
        labor_count = cursor.fetchone()['cnt']
        conn.close()

        missing = []
        if doc_counts.get('现场签证单', 0) == 0:
            missing.append('现场签证单')
        if doc_counts.get('复工令', 0) == 0:
            missing.append('复工令')
        if doc_counts.get('监理通知', 0) == 0:
            missing.append('监理通知')
        if doc_counts.get('业主指令', 0) == 0:
            missing.append('业主指令')
        if photo_count == 0:
            missing.append('现场照片')
        if machine_count == 0:
            missing.append('机械停置清单')
        if labor_count == 0:
            missing.append('劳务班组人数记录')
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
            INSERT INTO cost_items (event_id, version_id, cost_category, item_name, unit_price, quantity, unit, remark, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['event_id'], data.get('version_id'), data['cost_category'], data['item_name'],
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
            UPDATE cost_items SET version_id=?, cost_category=?, item_name=?, unit_price=?, quantity=?, unit=?, remark=?, updated_at=?
            WHERE id=?
        ''', (data.get('version_id'), data['cost_category'], data['item_name'], data.get('unit_price', 0),
              data.get('quantity', 0), data.get('unit', ''), data.get('remark', ''), now, cid))
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_event(event_id, version_id=None):
        conn = get_connection()
        cursor = conn.cursor()
        if version_id:
            cursor.execute('SELECT * FROM cost_items WHERE event_id=? AND version_id=? ORDER BY cost_category, id',
                           (event_id, version_id))
            rows = cursor.fetchall()
        else:
            cursor.execute('SELECT * FROM cost_items WHERE event_id=? AND (version_id IS NULL OR version_id IN (SELECT id FROM cost_versions WHERE event_id=? AND is_current=1)) ORDER BY cost_category, id',
                           (event_id, event_id))
            rows = cursor.fetchall()
            if not rows:
                cursor.execute('SELECT * FROM cost_items WHERE event_id=? AND version_id IS NULL ORDER BY cost_category, id',
                               (event_id,))
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
    def get_summary(event_id, version_id=None):
        items = CostItemDAO.get_by_event(event_id, version_id)
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


class CostVersionDAO:
    @staticmethod
    def create_version(event_id, version_name, version_desc=''):
        conn = get_connection()
        cursor = conn.cursor()
        now = _now()
        cursor.execute('UPDATE cost_versions SET is_current=0 WHERE event_id=?', (event_id,))
        cursor.execute('''
            INSERT INTO cost_versions (event_id, version_name, version_desc, is_current, created_at)
            VALUES (?, ?, ?, 1, ?)
        ''', (event_id, version_name, version_desc, now))
        vid = cursor.lastrowid
        existing_items = CostItemDAO.get_by_event(event_id, version_id=None)
        for it in existing_items:
            cursor.execute('''
                INSERT INTO cost_items (event_id, version_id, cost_category, item_name, unit_price, quantity, unit, remark, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (event_id, vid, it['cost_category'], it['item_name'],
                  it['unit_price'], it['quantity'], it.get('unit', ''),
                  it.get('remark', ''), now, now))
        conn.commit()
        conn.close()
        return vid

    @staticmethod
    def get_versions(event_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cost_versions WHERE event_id=? ORDER BY id DESC', (event_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_current_version(event_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cost_versions WHERE event_id=? AND is_current=1 ORDER BY id DESC LIMIT 1', (event_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def set_current_version(event_id, version_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE cost_versions SET is_current=0 WHERE event_id=?', (event_id,))
        cursor.execute('UPDATE cost_versions SET is_current=1 WHERE id=? AND event_id=?', (version_id, event_id))
        conn.commit()
        conn.close()

    @staticmethod
    def delete_version(version_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cost_items WHERE version_id=?', (version_id,))
        cursor.execute('DELETE FROM cost_versions WHERE id=?', (version_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def compare_versions(event_id, version_id1, version_id2):
        _, t1, g1 = CostItemDAO.get_summary(event_id, version_id1)
        _, t2, g2 = CostItemDAO.get_summary(event_id, version_id2)
        diff = {cat: t2[cat] - t1[cat] for cat in CostItemDAO.CATEGORIES}
        return g2 - g1, diff, g1, g2


class DocumentDAO:
    TYPES = ['现场签证单', '复工令', '监理通知', '业主指令']

    @staticmethod
    def create(data):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO documents (event_id, doc_type, doc_no, file_path, remark, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['event_id'], data['doc_type'], data.get('doc_no', ''),
              data.get('file_path', ''), data.get('remark', ''), _now()))
        conn.commit()
        did = cursor.lastrowid
        conn.close()
        return did

    @staticmethod
    def update(did, data):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE documents SET doc_type=?, doc_no=?, file_path=?, remark=?
            WHERE id=?
        ''', (data['doc_type'], data.get('doc_no', ''), data.get('file_path', ''),
              data.get('remark', ''), did))
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_event(event_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents WHERE event_id=? ORDER BY doc_type, id', (event_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_event_and_type(event_id, doc_type):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents WHERE event_id=? AND doc_type=? ORDER BY id', (event_id, doc_type))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def delete(did):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM documents WHERE id=?', (did,))
        conn.commit()
        conn.close()
