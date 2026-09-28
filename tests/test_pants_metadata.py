import hashlib
from io import BytesIO
from zipfile import ZipFile
from xml.sax.saxutils import escape

import pytest
from src.data.pants_metadata import read_metadata, join_studies

pytestmark = pytest.mark.unit


def workbook(rows=None, headers=None):
    headers = headers or ['PanTS ID', 'shape', 'spacing', 'tumor?']
    rows = rows if rows is not None else [['PanTS_00000001', '(3, 4, 5)', '(1, 2, 3)', '0']]
    buffer = BytesIO()
    with ZipFile(buffer, 'w') as z:
        z.writestr('xl/workbook.xml', '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="PanTS_metadata" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels', '<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        body = ''
        for n, row in enumerate([headers] + rows, 1):
            body += f'<row r="{n}">'
            for c, value in enumerate(row):
                body += f'<c r="{chr(65+c)}{n}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
            body += '</row>'
        z.writestr('xl/worksheets/sheet1.xml', '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'+body+'</sheetData></worksheet>')
    return buffer.getvalue()


def parse(raw):
    return read_metadata(raw, hashlib.sha256(raw).hexdigest())


def test_values_and_evidence():
    row = parse(workbook())['PanTS_00000001']
    assert row['shape'] == [3, 4, 5]
    assert row['spacing_native'] == [1, 2, 3]
    assert row['spatial_units'] is None
    assert row['source_tumor_status'] == 'negative'
    assert row['evidence']['row'] == 2


def test_hash_mismatch():
    with pytest.raises(ValueError, match='hash'):
        read_metadata(workbook(), '0'*64)


def test_missing_flag_stays_unknown():
    row = parse(workbook([['PanTS_00000001', '', '', '']]))['PanTS_00000001']
    assert row['source_tumor_status'] == 'unknown' and row['shape'] is None


@pytest.mark.parametrize('flag', ['yes', '2', 'false'])
def test_ambiguous_flag(flag):
    with pytest.raises(ValueError, match='Ambiguous'):
        parse(workbook([['PanTS_00000001', '', '', flag]]))


def test_duplicate_study():
    row = ['PanTS_00000001', '', '', '0']
    with pytest.raises(ValueError, match='Duplicate metadata study'):
        parse(workbook([row, row]))


@pytest.mark.parametrize('shape', ['(1, 2)', '(1, -2, 3)', '(1.0, 2, 3)', 'nonsense'])
def test_bad_shape(shape):
    with pytest.raises(ValueError):
        parse(workbook([['PanTS_00000001', shape, '', '0']]))


def test_reordered_columns():
    raw = workbook([['1','(3,4,5)','PanTS_00000001','(1,2,3)']],
                   ['tumor?','shape','PanTS ID','spacing'])
    assert parse(raw)['PanTS_00000001']['source_tumor_status'] == 'positive'


@pytest.mark.parametrize('headers', [['PanTS ID','shape','spacing','spacing'],
                                   ['PanTS ID','shape','spacing','other']])
def test_bad_columns(headers):
    with pytest.raises(ValueError, match='columns'): parse(workbook(headers=headers))


def test_join_fails_closed():
    records = parse(workbook())
    assert len(join_studies(records, ['PanTS_00000001'])) == 1
    with pytest.raises(ValueError, match='missing'): join_studies(records, ['PanTS_00000002'])
    with pytest.raises(ValueError, match='Duplicate'): join_studies(records, ['PanTS_00000001']*2)


def change_sheet(transform, extra=None):
    output = BytesIO()
    with ZipFile(BytesIO(workbook())) as source, ZipFile(output, 'w') as dest:
        for name in source.namelist():
            data = source.read(name)
            if name == 'xl/worksheets/sheet1.xml': data = transform(data.decode()).encode()
            dest.writestr(name, data)
        if extra: dest.writestr('xl/sharedStrings.xml', extra)
    return output.getvalue()


def test_shared_string_and_numeric_cells():
    raw = change_sheet(lambda s: s.replace(
        '<c r="A2" t="inlineStr"><is><t>PanTS_00000001</t></is></c>',
        '<c r="A2" t="s"><v>0</v></c>').replace(
        '<c r="D2" t="inlineStr"><is><t>0</t></is></c>', '<c r="D2"><v>0</v></c>'),
        '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>PanTS_00000001</t></si></sst>')
    assert parse(raw)['PanTS_00000001']['source_tumor_status'] == 'negative'


def test_formula_rejected_even_with_cached_value():
    raw = change_sheet(lambda s: s.replace('<c r="D2" t="inlineStr">',
                                            '<c r="D2" t="inlineStr"><f>1-1</f>'))
    with pytest.raises(ValueError, match='Formula'): parse(raw)
