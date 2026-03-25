"""
backend/app.py
==============
Flask REST API for NIDS Sentinel.
  GET /api/health  — system health check
  GET /api/stats   — live statistics
  GET /api/alerts  — paginated alert history
  GET /api/stream  — Server-Sent Events (real-time alerts)
"""

import os
import json
import time
import threading
from flask import Flask, jsonify, Response, request
from flask_cors import CORS
import subprocess
import signal

from model.predict import MODEL_LOADED
from db.database import get_recent_alerts, get_attack_counts
from sniffer import start_sniffer_thread, get_stats, get_timeline, alert_queue
from utils.logger import get_logger

logger = get_logger('api')
app    = Flask(__name__)
CORS(app, origins='*')


@app.route('/api/timeline', methods=['GET'])
def timeline():
    """Returns rotating 60-bucket traffic rate data."""
    return jsonify(get_timeline())

NETWORK_INTERFACE = os.environ.get('NETWORK_INTERFACE', None)
_sniffer_thread   = None

# ── Feature 2: Simulation state ──────────────────────────────────
_sim_process     = None
_sim_type        = None
_sim_start       = None
_sim_lock        = threading.Lock()

SIMULATION_COMMANDS = {
    'port_scan':   ['nmap', '-sT', '-T3', '-p', '1-1000', 'localhost'],
    'syn_flood':   ['hping3', '-S', '-p', '80', '--count', '500', '--fast', 'localhost'],
    'brute_force': ['bash', '-c', 'for i in $(seq 1 60); do ssh -o ConnectTimeout=1 -o StrictHostKeyChecking=no -o BatchMode=yes x@localhost 2>/dev/null; done']
}


@app.before_request
def ensure_sniffer_running():
    global _sniffer_thread
    if _sniffer_thread is None or not _sniffer_thread.is_alive():
        try:
            _sniffer_thread = start_sniffer_thread(NETWORK_INTERFACE)
            logger.info(f"Sniffer started on {NETWORK_INTERFACE}")
        except Exception as e:
            logger.error(f"Could not start sniffer: {e}")


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'message': 'NIDS Sentinel API is running. Access the dashboard at http://localhost',
        'health_check': '/api/health'
    })


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status':         'running',
        'model_loaded':   MODEL_LOADED,
        'sniffer_active': _sniffer_thread is not None and _sniffer_thread.is_alive(),
        'interface':      NETWORK_INTERFACE,
        'timestamp':      time.time()
    })


@app.route('/api/stats', methods=['GET'])
def stats():
    live_stats = get_stats()
    db_counts  = get_attack_counts()

    for k, v in db_counts.items():
        if k in live_stats['attack_breakdown']:
            live_stats['attack_breakdown'][k] = max(
                live_stats['attack_breakdown'][k], v
            )

    return jsonify(live_stats)


@app.route('/api/alerts', methods=['GET'])
def alerts():
    limit       = min(int(request.args.get('limit', 50)), 200)
    offset      = int(request.args.get('offset', 0))
    attack_type = request.args.get('type', None)

    rows = get_recent_alerts(limit=limit, offset=offset, attack_type=attack_type)
    return jsonify({'alerts': rows, 'count': len(rows), 'offset': offset})


@app.route('/api/stream', methods=['GET'])
def stream():
    def event_generator():
        yield f"data: {json.dumps({'type': 'connected', 'timestamp': time.time()})}\n\n"

        while True:
            try:
                # Wait for an alert with a shorter timeout to allow periodic stats push
                alert = alert_queue.get(timeout=2)
                alert_data = {k: v for k, v in alert.items() if k != 'features'}
                alert_data['type'] = 'alert'
                yield f"data: {json.dumps(alert_data)}\n\n"
            except Exception:
                # Push periodic stats update when idle
                live_stats = get_stats()
                live_stats['type'] = 'stats_update'
                yield f"data: {json.dumps(live_stats)}\n\n"

    return Response(
        event_generator(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control':     'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection':        'keep-alive'
        }
    )


@app.route('/api/simulate/<attack_type>', methods=['POST'])
def simulate_attack(attack_type):
    global _sim_process, _sim_type, _sim_start
    if attack_type not in SIMULATION_COMMANDS:
        return jsonify({'error': 'Unknown attack type'}), 400
    with _sim_lock:
        if _sim_process and _sim_process.poll() is None:
            _sim_process.terminate()
        _sim_process = subprocess.Popen(SIMULATION_COMMANDS[attack_type], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _sim_type, _sim_start = attack_type, time.time()
    return jsonify({'started': True, 'attack_type': attack_type})


@app.route('/api/simulate/status', methods=['GET'])
def simulate_status():
    with _sim_lock:
        running = _sim_process and _sim_process.poll() is None
        return jsonify({'running': running, 'attack_type': _sim_type if running else None, 'elapsed_s': int(time.time() - _sim_start) if running else 0})


@app.route('/api/simulate/stop', methods=['POST'])
def simulate_stop():
    global _sim_process
    with _sim_lock:
        if _sim_process and _sim_process.poll() is None:
            _sim_process.terminate()
            _sim_process = None
    return jsonify({'stopped': True})


@app.route('/api/alerts/clear', methods=['POST'])
def clear_alerts():
    cleared = 0
    while not alert_queue.empty():
        try: alert_queue.get_nowait(); cleared += 1
        except: break
    return jsonify({'cleared': cleared})


if __name__ == '__main__':
    logger.info("Starting NIDS Sentinel API...")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
