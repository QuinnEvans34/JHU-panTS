"""Narrow read-only adapter for the pinned PanTS metadata workbook, not general Excel."""
import ast
import hashlib
from io import BytesIO
import math
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from src.data.protected_identity import pants_identity

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
REQUIRED = ('PanTS ID', 'shape', 'spacing', 'tumor?')
MAX_XML = 32 * 1024**2


def triple(text, integer=False):
    if not text:
        return None
    if len(text) > 160:
        raise ValueError('Oversized numeric tuple')
    try:
        values = ast.literal_eval(text)
    except (SyntaxError, ValueError) as exc:
        raise ValueError('Malformed numeric tuple') from exc
    if (not isinstance(values, (tuple, list)) or len(values) != 3
            or any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0
                   or (integer and type(v) is not int) for v in values)):
        raise ValueError('Expected three positive finite values')
    return list(values)


def read_metadata(raw, expected_sha256):
    """Verify source bytes, return ID-keyed measurements with unknowns preserved."""
    if len(raw) > 16 * 1024**2 or hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError('Metadata size/hash does not match approved input')
    with ZipFile(BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate workbook ZIP member')
        def xml(name):
            if archive.getinfo(name).file_size > MAX_XML:
                raise ValueError('Workbook XML resource limit exceeded')
            data = archive.read(name)
            if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
                raise ValueError('XML declarations are unsupported')
            return ET.fromstring(data)
        sheets = xml('xl/workbook.xml').findall('m:sheets/m:sheet', NS)
        if len(sheets) != 1 or sheets[0].get('name') != 'PanTS_metadata':
            raise ValueError('Expected single PanTS_metadata worksheet')
        relations = list(xml('xl/_rels/workbook.xml.rels'))
        matches = [r for r in relations if r.get('Id') == sheets[0].get(REL)]
        if (len(matches) != 1 or matches[0].get('Target') != 'worksheets/sheet1.xml'
                or matches[0].get('TargetMode') == 'External'):
            raise ValueError('Unsupported worksheet relationship')
        shared = []
        if 'xl/sharedStrings.xml' in names:
            shared = [''.join(t.text or '' for t in s.findall('.//m:t', NS))
                      for s in xml('xl/sharedStrings.xml').findall('m:si', NS)]
        rows = xml('xl/worksheets/sheet1.xml').findall('m:sheetData/m:row', NS)
        if not rows or len(rows) > 10001:
            raise ValueError('Missing or excessive metadata rows')
        def cells(row):
            result = {}
            for cell in row.findall('m:c', NS):
                address = re.fullmatch(r'([A-Z]+)([1-9][0-9]*)', cell.get('r', ''))
                if not address or address[2] != row.get('r') or address[1] in result:
                    raise ValueError('Invalid or duplicate cell address')
                if cell.find('m:f', NS) is not None:
                    raise ValueError('Formula cells are not accepted as source evidence')
                value = cell.find('m:v', NS)
                text = value.text if value is not None and value.text is not None else ''
                kind = cell.get('t', 'n')
                if kind == 's':
                    if not re.fullmatch(r'[0-9]+', text) or int(text) >= len(shared):
                        raise ValueError('Invalid shared string reference')
                    text = shared[int(text)]
                elif kind == 'inlineStr':
                    text = ''.join(t.text or '' for t in cell.findall('m:is//m:t', NS))
                elif kind not in ('n', 'str', 'b'):
                    raise ValueError('Unsupported metadata cell type')
                result[address[1]] = text
            return result
        headers = cells(rows[0])
        labels = [v for v in headers.values() if v]
        if len(labels) != len(set(labels)) or not set(REQUIRED).issubset(labels):
            raise ValueError('Missing or duplicate metadata columns')
        records, row_numbers = {}, set()
        for row in rows[1:]:
            if row.get('r') in row_numbers:
                raise ValueError('Duplicate worksheet row')
            row_numbers.add(row.get('r'))
            values = cells(row)
            if not any(values.values()):
                continue
            if any(v and not headers.get(k) for k, v in values.items()):
                raise ValueError('Value in unnamed metadata column')
            fields = {name: values.get(col) or None for col, name in headers.items() if name}
            raw_id = fields['PanTS ID']
            pants_identity(raw_id)
            if raw_id in records:
                raise ValueError('Duplicate metadata study')
            tumour = fields['tumor?']
            if tumour not in (None, '0', '1'):
                raise ValueError('Ambiguous source tumour flag')
            records[raw_id] = dict(source_study_id=raw_id,
                                  shape=triple(fields['shape'], integer=True),
                                  spacing_native=triple(fields['spacing']),
                                  spatial_units=None,
                                  source_tumor_status={None: 'unknown', '0': 'negative', '1': 'positive'}[tumour],
                                  source_fields=fields,
                                  evidence=dict(content_sha256=expected_sha256,
                                                worksheet='PanTS_metadata', row=int(row.get('r'))))
        return records


def join_studies(records, requested_ids):
    """No missing-row fallback, deduplication or silent sample reduction."""
    ids = list(requested_ids)
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate requested study')
    if any(i not in records for i in ids):
        raise ValueError('Study missing from source metadata')
    return [records[i] for i in sorted(ids)]
