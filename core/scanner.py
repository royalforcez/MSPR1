import os
import nmap
from core.database import add_equipment
from dotenv import load_dotenv

load_dotenv()

def run_network_scan():
    network_range = os.getenv('NETWORK_RANGE', '192.168.1.0/24')
    print(f"[*] Démarrage du scan Nmap sur {network_range}...")
    
    nm = nmap.PortScanner()
    nm.scan(hosts=network_range, arguments='-sn -n -T4') # Scan Ping rapide
    
    new_hosts = 0
    for host in nm.all_hosts():
        if nm[host].state() == 'up':
            hostname = nm[host].hostname() if nm[host].hostname() else f"Unknown-{host}"
            
            # Tente d'ajouter à la BDD. add_equipment gère les doublons.
            if add_equipment(nom=hostname, ip=host):
                new_hosts += 1
                print(f"    [+] Nouvel équipement découvert et ajouté : {hostname} ({host})")
                
    print(f"[*] Scan terminé. {new_hosts} nouvelles machines ajoutées.")