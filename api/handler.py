import json
import sqlite3
from pathlib import Path
from flask import Flask, request, make_response

app = Flask(__name__)
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / 'data.db'

ALLOWED_MEASURES = {
    'Violent crime rate', 'Unemployment', 'Children in poverty', 'Diabetic screening',
    'Mammography screening', 'Preventable hospital stays', 'Uninsured',
    'Sexually transmitted infections', 'Physical inactivity', 'Adult obesity',
    'Premature Death', 'Daily fine particulate matter'
}

FILES = {
    'obesity': ROOT / 'obesity.json',
    'poverty': ROOT / 'poverty.json',
    'fpm': ROOT / 'fpm.json'
}

def _json(data, status=200):
    resp = make_response(json.dumps(data), status)
    resp.headers['Content-Type'] = 'application/json'
    return resp

def _coffee_teapot_trigger():
    """Check for coffee=teapot in query params or JSON body."""
    try:
        if request.args.get('coffee') == 'teapot':
            return True
        body = request.get_json(silent=True)
        if isinstance(body, dict) and body.get('coffee') == 'teapot':
            return True
    except Exception:
        pass
    return False

def _load_array(path: Path):
    """Load a JSON file and ensure it returns an array."""
    if not path.exists():
        return None
    with path.open('r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception:
            return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get('data'), list):
            return data['data']
        return []
    return []

# County data endpoint
@app.route('/api/county_data', methods=['POST', 'GET'])
@app.route('/county_data', methods=['POST', 'GET'])
def county_data():
    if request.method != 'POST':
        if _coffee_teapot_trigger():
            return _json({'error': 'I am a teapot'}, 418)
        return _json({'error': 'POST required'}, 400)

    if _coffee_teapot_trigger():
        return _json({'error': 'I am a teapot'}, 418)

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _json({'error': 'JSON body required'}, 400)

    zip_code = str(data.get('zip', '')).strip()
    measure_name = str(data.get('measure_name', '')).strip()

    if not zip_code or not measure_name:
        return _json({'error': 'Both zip and measure_name are required'}, 400)

    if len(zip_code) != 5 or not zip_code.isdigit():
        return _json({'error': 'zip must be a 5-digit string'}, 400)

    if measure_name not in ALLOWED_MEASURES:
        return _json({'error': 'Not found'}, 404)

    if not DB_PATH.exists():
        return _json({'error': 'data.db not found'}, 404)

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        sql = '''
        WITH z AS (
            SELECT county, state_abbreviation AS state
            FROM zip_county
            WHERE zip = ?
            GROUP BY county, state
        )
        SELECT
            chr.state AS state,
            chr.county AS county,
            chr.state_code AS state_code,
            chr.county_code AS county_code,
            chr.year_span AS year_span,
            chr.measure_name AS measure_name,
            chr.measure_id AS measure_id,
            chr.numerator AS numerator,
            chr.denominator AS denominator,
            chr.raw_value AS raw_value,
            chr.confidence_interval_lower_bound AS confidence_interval_lower_bound,
            chr.confidence_interval_upper_bound AS confidence_interval_upper_bound,
            chr.data_release_year AS data_release_year,
            chr.fipscode AS fipscode
        FROM county_health_rankings chr
        JOIN z ON z.county = chr.county AND z.state = chr.state
        WHERE chr.measure_name = ?
        ORDER BY chr.data_release_year, chr.year_span, chr.measure_id
        '''
        cur.execute(sql, (zip_code, measure_name))
        rows = cur.fetchall()
    except sqlite3.Error as e:
        return _json({'error': f'Database error'}, 500)
    finally:
        try:
            conn.close()
        except Exception:
            pass

    if not rows:
        return _json({'error': 'Not found'}, 404)

    out = []
    for r in rows:
        out.append({k: ('' if r[k] is None else str(r[k])) for k in r.keys()})
    return _json(out, 200)

# Quirky paths
@app.route('/@../obesity.json', methods=['GET', 'POST'])
@app.route('/@../poverty.json', methods=['GET', 'POST'])
@app.route('/@../fpm.json', methods=['GET', 'POST'])
def serve_quirky():
    if _coffee_teapot_trigger():
        return _json({'error': 'I am a teapot'}, 418)
    
    if request.path == '/@../obesity.json':
        name = 'obesity'
    elif request.path == '/@../poverty.json':
        name = 'poverty'
    elif request.path == '/@../fpm.json':
        name = 'fpm'
    else:
        return _json({'error': 'Not found'}, 404)
    
    path = FILES.get(name)
    data = _load_array(path) if path else None
    if data is None:
        return _json({'error': 'Not found'}, 404)
    return _json(data, 200)

# List endpoints
@app.route('/api/obesity', methods=['GET', 'POST'])
@app.route('/api/poverty', methods=['GET', 'POST'])
@app.route('/api/fpm', methods=['GET', 'POST'])
@app.route('/obesity', methods=['GET', 'POST'])
@app.route('/poverty', methods=['GET', 'POST'])
@app.route('/fpm', methods=['GET', 'POST'])
def serve_list():
    if _coffee_teapot_trigger():
        return _json({'error': 'I am a teapot'}, 418)
    
    name = request.path.strip('/').replace('api/', '')
    path = FILES.get(name)
    data = _load_array(path) if path else None
    if data is None:
        return _json({'error': 'Not found'}, 404)
    return _json(data, 200)

# Catch-all
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if _coffee_teapot_trigger():
        return _json({'error': 'I am a teapot'}, 418)
    return _json({'error': 'Not found'}, 404)

@app.errorhandler(404)
def not_found(_):
    return _json({'error': 'Not found'}, 404)

# Vercel needs this
handler = app
