"""Converts LLDP/CDP neighbours (lldpcli) into Prometheus metrics for the textfile collector (NetCockpit agent)."""
import json, os, subprocess, sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "/var/lib/alloy/textfile/lldp.prom"

def val(x):
    """Unwraps the lists and {"value": ...} objects of the lldpcli json0 format."""
    while isinstance(x, list):
        x = x[0] if x else None
    if isinstance(x, dict):
        return x.get("value")
    return x

def esc(s):
    return str(s or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")

try:
    raw = subprocess.run(["lldpcli", "-f", "json0", "show", "neighbors"], capture_output=True, text=True, timeout=20).stdout
    data = json.loads(raw or "{}")
except Exception:
    data = {}
lines = ["# HELP lldp_neighbor_info LLDP/CDP neighbour seen on an interface", "# TYPE lldp_neighbor_info gauge"]
for lldp in data.get("lldp", []) or []:
    for itf in lldp.get("interface", []) or []:
        ch = (itf.get("chassis") or [{}])[0]
        pt = (itf.get("port") or [{}])[0]
        labels = {
            "interface": itf.get("name"), "protocol": itf.get("via"),
            "chassis_name": val(ch.get("name")), "chassis_id": val(ch.get("id")),
            "mgmt_ip": val(ch.get("mgmt-ip")), "port_id": val(pt.get("id")), "port_descr": val(pt.get("descr")),
        }
        lines.append("lldp_neighbor_info{" + ",".join(f'{k}="{esc(v)}"' for k, v in labels.items()) + "} 1")
tmp = OUT + ".tmp"
with open(tmp, "w") as f:
    f.write("\n".join(lines) + "\n")
os.chmod(tmp, 0o644)
os.replace(tmp, OUT)
