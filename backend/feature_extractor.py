"""
backend/feature_extractor.py
=============================
Extracts NSL-KDD-compatible features from live Scapy packets.
Maintains a per-source-IP sliding 2-second window for statistical features.
"""

import time
from collections import defaultdict, deque
from scapy.all import IP, TCP, UDP, ICMP, ARP

_conn_tracker = defaultdict(lambda: {
    'timestamps': deque(maxlen=200),
    'dst_ports':  deque(maxlen=200),
    'services':   deque(maxlen=200),
    'syn_errors': deque(maxlen=200),
    'rst_errors': deque(maxlen=200),
})

PORT_TO_SERVICE = {
    80: 35, 8080: 35, 8443: 35,
    443: 35, 21: 16, 22: 48,
    23: 50, 25: 28, 53: 13,
    110: 38, 143: 24, 3306: 41,
    5432: 41, 6379: 60, 27017: 60,
    135: 5, 137: 5, 138: 5, 139: 5, 445: 5, # SMB/NetBIOS
    161: 3, 162: 3, # SNMP
    514: 43, # Syslog
    1521: 41, # Oracle
    3389: 42, # RDP
    5900: 42  # VNC
}

FLAG_ENCODING = {
    'SF': 2, 'S0': 8, 'REJ': 3, 'RSTO': 4,
    'RSTR': 5, 'SH': 6, 'OTH': 7, 'S': 0, 'SA': 1
}


def _encode_tcp_flags(tcp_flags) -> int:
    flag_str = str(tcp_flags)
    if 'S' in flag_str and 'A' not in flag_str and 'F' not in flag_str:
        return FLAG_ENCODING.get('S0', 8)
    if 'S' in flag_str and 'A' in flag_str:
        return FLAG_ENCODING.get('SA', 1)
    if 'F' in flag_str and 'A' in flag_str:
        return FLAG_ENCODING.get('SF', 2)
    if 'R' in flag_str:
        return FLAG_ENCODING.get('RSTO', 4)
    return FLAG_ENCODING.get('OTH', 7)


def _get_protocol_code(packet) -> int:
    if packet.haslayer(TCP):  return 0
    if packet.haslayer(ICMP): return 1
    if packet.haslayer(UDP):  return 2
    return 0


def _update_tracker(src_ip: str, dst_port: int, service: int,
                    is_syn_error: bool, is_rst_error: bool):
    now     = time.time()
    tracker = _conn_tracker[src_ip]
    tracker['timestamps'].append(now)
    tracker['dst_ports'].append(dst_port)
    tracker['services'].append(service)
    tracker['syn_errors'].append(1 if is_syn_error else 0)
    tracker['rst_errors'].append(1 if is_rst_error else 0)


def _compute_window_stats(src_ip: str, current_service: int) -> dict:
    tracker = _conn_tracker[src_ip]
    now     = time.time()

    recent_mask = [
        i for i, t in enumerate(tracker['timestamps'])
        if now - t <= 2.0
    ]

    if not recent_mask:
        return {
            'count': 0, 'srv_count': 0,
            'serror_rate': 0.0, 'srv_serror_rate': 0.0,
            'rerror_rate': 0.0, 'srv_rerror_rate': 0.0,
            'same_srv_rate': 0.0, 'diff_srv_rate': 0.0
        }

    count    = len(recent_mask)
    services = [list(tracker['services'])[i] for i in recent_mask]
    syn_errs = [list(tracker['syn_errors'])[i] for i in recent_mask]
    rst_errs = [list(tracker['rst_errors'])[i] for i in recent_mask]

    srv_count     = sum(1 for s in services if s == current_service)
    serror_rate   = sum(syn_errs) / count
    rerror_rate   = sum(rst_errs) / count
    same_srv_rate = srv_count / count
    diff_srv_rate = 1.0 - same_srv_rate

    srv_indices = [i for i, s in enumerate(services) if s == current_service]
    if srv_indices:
        srv_serror = sum(syn_errs[i] for i in srv_indices) / len(srv_indices)
        srv_rerror = sum(rst_errs[i] for i in srv_indices) / len(srv_indices)
    else:
        srv_serror = srv_rerror = 0.0

    return {
        'count':           min(count, 511),
        'srv_count':       min(srv_count, 511),
        'serror_rate':     round(serror_rate, 4),
        'srv_serror_rate': round(srv_serror, 4),
        'rerror_rate':     round(rerror_rate, 4),
        'srv_rerror_rate': round(srv_rerror, 4),
        'same_srv_rate':   round(same_srv_rate, 4),
        'diff_srv_rate':   round(diff_srv_rate, 4),
    }


def extract_features(packet) -> dict:
    """Takes a Scapy packet and returns a dict of 41 NSL-KDD-compatible features."""
    features = {}

    for col in [
        'duration', 'land', 'wrong_fragment', 'urgent', 'hot',
        'num_failed_logins', 'logged_in', 'num_compromised', 'root_shell',
        'su_attempted', 'num_root', 'num_file_creations', 'num_shells',
        'num_access_files', 'num_outbound_cmds', 'is_host_login',
        'is_guest_login', 'srv_diff_host_rate',
        'dst_host_count', 'dst_host_srv_count',
        'dst_host_same_srv_rate', 'dst_host_diff_srv_rate',
        'dst_host_same_src_port_rate', 'dst_host_srv_diff_host_rate',
        'dst_host_serror_rate', 'dst_host_srv_serror_rate',
        'dst_host_rerror_rate', 'dst_host_srv_rerror_rate',
        'src_bytes', 'dst_bytes', 'flag'
    ]:
        features[col] = 0

    src_ip       = '0.0.0.0'
    dst_port     = 0
    service      = 60
    is_syn_error = False
    is_rst_error = False

    features['protocol_type'] = _get_protocol_code(packet)

    if packet.haslayer(IP):
        ip = packet[IP]
        src_ip = ip.src
        features['wrong_fragment'] = ip.frag
        features['land']           = 1 if ip.src == ip.dst else 0
        features['src_bytes']      = len(ip.payload)
        features['dst_bytes']      = 0

    if packet.haslayer(TCP):
        tcp          = packet[TCP]
        dst_port     = tcp.dport
        service      = PORT_TO_SERVICE.get(dst_port, 60)
        features['flag']      = _encode_tcp_flags(tcp.flags)
        features['urgent']    = 1 if 'U' in str(tcp.flags) else 0
        features['src_bytes'] = len(tcp.payload)
        is_syn_error = ('S' in str(tcp.flags) and 'A' not in str(tcp.flags))
        is_rst_error = 'R' in str(tcp.flags)

    elif packet.haslayer(UDP):
        udp           = packet[UDP]
        dst_port      = udp.dport
        service       = PORT_TO_SERVICE.get(dst_port, 60)
        features['flag']      = 0
        features['src_bytes'] = len(udp.payload)

    elif packet.haslayer(ICMP):
        features['flag']      = 0
        features['src_bytes'] = len(packet[ICMP].payload) if packet.haslayer(ICMP) else 0

    features['service'] = service

    _update_tracker(src_ip, dst_port, service, is_syn_error, is_rst_error)
    window_stats = _compute_window_stats(src_ip, service)
    features.update(window_stats)

    return features
