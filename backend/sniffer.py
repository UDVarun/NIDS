"""
backend/sniffer.py
==================
Live packet capture using Scapy. Runs in a background daemon thread.
Calls feature_extractor and ML model for every packet, queues attack alerts.
"""

import time
import queue
import threading
from scapy.all import sniff, IP, TCP, UDP, ICMP, ARP

# ── Feature 1: Timeline tracking ──────────────────────────────────
# ... existing timeline code ...

from feature_extractor import extract_features
from model.predict import predict, MODEL_LOADED
from db.database import log_alert
from utils.logger import get_logger
from utils.geoip import lookup as geo_lookup

# ── Feature 1: Timeline tracking ──────────────────────────────────
from collections import deque
_timeline        = deque(maxlen=60)
_timeline_lock   = threading.Lock()
_current_bucket  = {'t': int(time.time()), 'normal': 0, 'attack': 0}
_bucket_lock     = threading.Lock()

def _tick_timeline():
    """Background thread closes current 1s bucket and opens new one."""
    global _current_bucket
    while True:
        time.sleep(1.0)
        with _bucket_lock:
            closed_bucket = dict(_current_bucket)
            with _timeline_lock:
                _timeline.append(closed_bucket)
            _current_bucket = {'t': int(time.time()), 'normal': 0, 'attack': 0}

_ticker_thread = threading.Thread(target=_tick_timeline, daemon=True, name='TimelineTicker')
_ticker_thread.start()

logger      = get_logger('sniffer')
alert_queue = queue.Queue(maxsize=1000)

_stats = {
    'total_packets':   0,
    'total_attacks':   0,
    'attack_counts':   {
        'SYN_FLOOD': 0, 'PORT_SCAN': 0,
        'BRUTE_FORCE': 0, 'ARP_SPOOF': 0, 'ANOMALY': 0
    },
    'start_time':      time.time(),
    'last_confidence': 0.0
}
_stats_lock = threading.Lock()

# ── Feature 4: IP Filtering & Whitelisting ───────────────────────
IGNORED_DST_IPS = {
    '255.255.255.255',
    '224.0.0.1', '224.0.0.2', '224.0.0.5', '224.0.0.6',
    '224.0.0.7', '224.0.0.9', '224.0.0.13', '224.0.0.22',
    '224.0.0.251', '224.0.0.252', '224.0.1.1',
}

WHITELISTED_SRC_IPS = {
    '192.168.1.1',  # Router
}

def _is_ignored(dst_ip: str, src_ip: str = '') -> bool:
    """Returns True for traffic that should NEVER be analyzed."""
    if dst_ip in IGNORED_DST_IPS:
        return True
    if dst_ip.startswith('239.') or dst_ip.startswith('224.'):
        return True
    if dst_ip.endswith('.255'):
        return True
    if dst_ip.startswith('127.') or src_ip.startswith('127.'):
        return True
    for prefix in ('172.17.', '172.18.', '172.19.', '172.20.'):
        if dst_ip.startswith(prefix) or src_ip.startswith(prefix):
            return True
    if dst_ip.startswith('169.254.') or src_ip.startswith('169.254.'):
        return True
    return False

def _is_whitelisted(src_ip: str) -> bool:
    """Returns True if this source IP should never be flagged."""
    return src_ip in WHITELISTED_SRC_IPS


def classify_attack_type(features: dict) -> str:
    """Rule-based attack type classifier applied after ML detects anomaly."""
    count         = features.get('count', 0)
    serror_rate   = features.get('serror_rate', 0.0)
    diff_srv_rate = features.get('diff_srv_rate', 0.0)
    same_srv_rate = features.get('same_srv_rate', 0.0)

    if count > 100 and serror_rate > 0.5:
        return 'SYN_FLOOD'
    if diff_srv_rate > 0.3 and count > 20:
        return 'PORT_SCAN'
    if same_srv_rate > 0.85 and count > 150:
        return 'BRUTE_FORCE'
    return 'ANOMALY'


def handle_arp_packet(packet) -> None:
    """Detects unsolicited ARP replies as potential ARP spoofing."""
    arp = packet[ARP]
    if arp.op == 2:  # ARP REPLY
        alert = {
            'timestamp':    time.time(),
            'src_ip':       arp.psrc,
            'dst_ip':       arp.pdst,
            'protocol':     'ARP',
            'prediction':   'ATTACK',
            'attack_type':  'ARP_SPOOF',
            'confidence':   0.85,
            'anomaly_score': -0.4,
            'is_attack':    True
        }
        log_alert(alert)
        try:
            alert_queue.put_nowait(alert)
        except queue.Full:
            pass
        with _stats_lock:
            _stats['total_attacks'] += 1
            _stats['attack_counts']['ARP_SPOOF'] += 1


def packet_callback(packet) -> None:
    """Main packet processing callback called by Scapy for every captured packet."""
    with _stats_lock:
        _stats['total_packets'] += 1

    try:
        if packet.haslayer(ARP) and not packet.haslayer(IP):
            handle_arp_packet(packet)
            return

        if not packet.haslayer(IP):
            return

        src_ip = packet[IP].src
        dst_ip = packet[IP].dst

        # Skip ignored traffic (broadcast, loopback, docker bridge)
        if _is_ignored(dst_ip, src_ip):
            return

        # Skip whitelisted sources
        if _is_whitelisted(src_ip):
            return

        features = extract_features(packet)
        result   = predict(features)

        # ── Timeline bucket update ─────────────────────────────────
        # Increment counters based on prediction result
        with _bucket_lock:
            if result['is_attack']:
                _current_bucket['attack'] += 1
            else:
                _current_bucket['normal'] += 1

        protocol = ('TCP'  if packet.haslayer(TCP)  else
                    'UDP'  if packet.haslayer(UDP)   else
                    'ICMP' if packet.haslayer(ICMP)  else 'OTHER')

        attack_type = classify_attack_type(features) if result['is_attack'] else None

        alert = {
            'timestamp':    time.time(),
            'src_ip':       src_ip,
            'dst_ip':       dst_ip,
            'protocol':     protocol,
            'prediction':   result['prediction'],
            'attack_type':  attack_type,
            'confidence':   result['confidence'],
            'anomaly_score': result['anomaly_score'],
            'is_attack':    result['is_attack'],
            'features':     features
        }

        log_alert(alert)

        if result['is_attack']:
            # Feature 3: Enrich alert with geolocation
            geo = geo_lookup(src_ip)
            if geo: alert['geo'] = geo

            with _stats_lock:
                _stats['total_attacks'] += 1
                key = attack_type or 'ANOMALY'
                _stats['attack_counts'][key] = \
                    _stats['attack_counts'].get(key, 0) + 1
                _stats['last_confidence'] = result['confidence']

                # Feature 3: Track top countries
                if geo and not geo['private']:
                    country = geo['country']
                    if 'top_countries' not in _stats: _stats['top_countries'] = {}
                    _stats['top_countries'][country] = _stats['top_countries'].get(country, 0) + 1
            try:
                alert_queue.put_nowait(alert)
            except queue.Full:
                logger.warning("Alert queue full — dropping alert")

    except Exception as e:
        logger.error(f"Packet processing error: {e}", exc_info=True)


def get_stats() -> dict:
    """Returns thread-safe copy of current statistics."""
    with _stats_lock:
        return {
            'total_packets':    _stats['total_packets'],
            'total_attacks':    _stats['total_attacks'],
            'attack_breakdown': dict(_stats['attack_counts']),
            'normal_count':     _stats['total_packets'] - _stats['total_attacks'],
            'uptime_seconds':   int(time.time() - _stats['start_time']),
            'avg_confidence':   round(_stats['last_confidence'], 3),
            'top_countries':    dict(_stats.get('top_countries', {}))
        }


def get_timeline() -> list:
    """Returns rolling 60-second window of traffic stats."""
    with _timeline_lock:
        now = int(time.time())
        res = {b['t']: b for b in list(_timeline)}
        return [res.get(now - i, {'t': now - i, 'normal': 0, 'attack': 0}) 
                for i in range(59, -1, -1)]


def start_sniffer(interface: str = None) -> None:
    """Blocking Scapy sniff loop. Run in background thread."""
    # If no interface is specified, we try to sniff on loopback and any others
    # Using a list of interfaces if supported, or falling back to 'any'
    iface_list = interface if interface else ['lo', 'eth0', 'wlan0', 'any']
    
    # Filter out interfaces that don't exist to avoid errors
    from scapy.all import get_if_list
    available_ifs = get_if_list()
    if isinstance(iface_list, list):
        iface_list = [i for i in iface_list if i in available_ifs]
        if not iface_list: iface_list = None # fallback to scapy's default

    iface_name = str(iface_list) if iface_list else 'ALL INTERFACES'
    logger.info(f"Starting packet sniffer on: {iface_name}")
    try:
        sniff(
            iface=iface_list,
            prn=packet_callback,
            store=False,
            filter='ip or arp',
            quiet=True # reduce noise if many interfaces
        )
    except PermissionError:
        logger.error("Permission denied. Run with sudo or as root.")
        raise
    except Exception as e:
        logger.error(f"Sniffer error: {e}")
        raise


def start_sniffer_thread(interface: str = None) -> threading.Thread:
    """Starts the sniffer as a daemon background thread."""
    t = threading.Thread(
        target=start_sniffer,
        args=(interface,),
        daemon=True,
        name='PacketSnifferThread'
    )
    t.start()
    logger.info("Sniffer thread started")
    return t
