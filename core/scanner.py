import os
import nmap
from core.database import add_equipment
from dotenv import load_dotenv

load_dotenv()

def run_network_scan():
    network_range = os.getenv('NETWORK_RANGE', '192.168.1.0/24')
    ssh_user_default = os.getenv('SSH_USER', 'ntl_monitor') # Défini dans le .env
    
    print(f"[*] Démarrage du scan Nmap sur {network_range}...")
    
    nm = nmap.PortScanner()
    nm.scan(hosts=network_range, arguments='-sn -n -T4') 
    
    new_hosts = 0
    for host in nm.all_hosts():
        if nm[host].state() == 'up':
            hostname = nm[host].hostname() if nm[host].hostname() else f"Unknown-{host}"
            
            # Ajout BDD avec est_actif = 1
            if add_equipment(nom=hostname, ip=host, ssh_user=ssh_user_default):
                new_hosts += 1
                print(f"    [+] Nouvel équipement découvert : {hostname} ({host})")
                
    print(f"[*] Scan terminé. {new_hosts} nouvelles machines ajoutées.")