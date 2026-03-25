from scapy.all import IP, TCP, ARP, send, Ether
import time
import sys

def test_syn_flood(target_ip="127.0.0.1"):
    print(f"[*] Sending SYN Flood to {target_ip}...")
    pkts = [IP(dst=target_ip)/TCP(dport=80, flags="S") for _ in range(200)]
    send(pkts, verbose=False)

def test_port_scan(target_ip="127.0.0.1"):
    print(f"[*] Sending Port Scan to {target_ip}...")
    ports = [21, 22, 23, 25, 53, 80, 110, 135, 443, 445]
    pkts = [IP(dst=target_ip)/TCP(dport=p, flags="S") for p in ports] * 5
    send(pkts, verbose=False)

def test_arp_spoof():
    print("[*] Sending ARP Spoof packet...")
    pkt = ARP(op=2, psrc="192.168.1.1", pdst="192.168.1.10")
    send(pkt, iface="lo", verbose=False)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        atk = sys.argv[1]
        if atk == "syn": test_syn_flood()
        elif atk == "scan": test_port_scan()
        elif atk == "arp": test_arp_spoof()
        else:
            test_syn_flood()
            test_port_scan()
            test_arp_spoof()
    else:
        test_syn_flood()
        time.sleep(1)
        test_port_scan()
        time.sleep(1)
        test_arp_spoof()
    print("[+] Done.")
