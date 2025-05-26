from concurrent.futures import ThreadPoolExecutor
import socket
import ipaddress
import time
import threading

# --- בדיקת פורט ---
def check_port(ip, port, timeout=0.5):
    try:
        s = socket.socket()
        s.settimeout(timeout)
        s.connect((ip, port))
        s.close()
        return True
    except:
        return False

# --- קריאת קובץ קונפיגורציה ---
def read_config(filename):
    network = ""
    ports = []
    with open(filename, "r") as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if line.startswith("network="):
            network = line.split("=")[1].strip()
        elif line.startswith("ports="):
            ports = line.split("=")[1].split(",")
            ports = [int(p.strip()) for p in ports]
    return network, ports

# --- סריקה מקבילה ---
def run_parallel_scan(network_cidr, ports_to_scan, max_workers=50):
    network = ipaddress.IPv4Network(network_cidr, strict=False)
    results = {}
    lock = threading.Lock()

    def scan_task(ip, port):
        with lock:
            print(f"🔄 Currently scanning: {ip}:{port} ", end="\r", flush=True)

        if check_port(ip, port):
            with lock:
                if ip not in results:
                    results[ip] = []
                results[ip].append(port)

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for ip in network.hosts():
            for port in ports_to_scan:
                executor.submit(scan_task, str(ip), port)

    end_time = time.time()
    elapsed = end_time - start_time

    # ניקוי שורת התקדמות בסיום
    print(" " * 60, end="\r")
    return results, elapsed

# --- הרצת הסריקה ---
if __name__ == "__main__":
    network_cidr, ports_to_scan = read_config("config.txt")

    print(f"\n🔍 Scanning network: {network_cidr}")
    print(f"🛑 Ports: {', '.join(str(p) for p in ports_to_scan)}\n")

    scan_results, elapsed_time = run_parallel_scan(network_cidr, ports_to_scan)

    if scan_results:
        for ip, ports in scan_results.items():
            ports_str = ", ".join(str(p) for p in sorted(ports))
            print(f"{ip:<15} | OPEN PORTS: {ports_str}")
    else:
        print("✅ No open ports found.")

    print(f"\n⏱️ Scan completed in {elapsed_time:.2f} seconds.")
