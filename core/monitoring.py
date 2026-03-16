import os
import paramiko
import socket
from core.database import get_all_equipments, insert_metrics, insert_service_status, update_equipment_name
from dotenv import load_dotenv

# Imports des scripts de tes collègues
from core.dnspython import check_dns
from core.adpython import check_ad

load_dotenv()

def check_port(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect((ip, port))
        return "UP"
    except:
        return "DOWN"
    finally:
        s.close()

def get_ssh_metrics(ip, username, os_name):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key_path = os.getenv('SSH_KEY_PATH', '/root/.ssh/id_rsa')
    
    try:
        ssh.connect(ip, username=username, key_filename=key_path, timeout=5)
        os_str = str(os_name).upper()

        if "DEBIAN" in os_str or "LINUX" in os_str:
            # On ajoute 'hostname' au tout début de la commande
            cmd = "hostname; " \
                  "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d',' -f1; " \
                  "free | grep Mem | awk '{print $3/$2 * 100.0}'; " \
                  "df / | tail -1 | awk '{print $5}' | sed 's/%//'; " \
                  "uptime -p"
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=5)
            res = stdout.read().decode().splitlines()
            # On retourne 5 valeurs maintenant (Nom, CPU, RAM, Disk, Uptime)
            return res[0].strip(), float(res[1]), float(res[2]), float(res[3]), res[4]

        elif "WINDOWS" in os_str:
            # On ajoute $env:COMPUTERNAME pour Windows
            cmd = "powershell -Command \"Write-Output $env:COMPUTERNAME; $cpu = (Get-CimInstance Win32_Processor).LoadPercentage; $os = Get-CimInstance Win32_OperatingSystem; $ram = [math]::Round((($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / $os.TotalVisibleMemorySize) * 100, 2); $disk = Get-CimInstance Win32_LogicalDisk -Filter \\\"DeviceID='C:'\\\"; $disk_p = [math]::Round((($disk.Size - $disk.FreeSpace) / $disk.Size) * 100, 2); $up = (New-TimeSpan -Start $os.LastBootUpTime -End (Get-Date)).Hours; Write-Output $cpu; Write-Output $ram; Write-Output $disk_p; Write-Output $up\""
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=8)
            res = stdout.read().decode().strip().splitlines()
            return res[0].strip(), float(res[1]), float(res[2]), float(res[3]), f"up {res[4]} hours"

    except Exception as e:
        return None
    finally:
        ssh.close()

def run_system_monitoring():
    equipments = get_all_equipments()
    for eq in equipments:
        status = check_port(eq['IPv4'], 22)
        insert_service_status(eq['ID'], 'Serveur (SSH)', status)
        
        if status == "UP":
            metrics = get_ssh_metrics(eq['IPv4'], eq['SSH_User'], eq['OS'])
            if metrics:
                real_host, cpu, ram, disk, uptime = metrics
                
                # LA MAGIE EST ICI : Si le nom commence par Unknown, on le met à jour !
                if eq['Nom'].startswith("Unknown-") and real_host:
                    print(f"    [+] Nom mis à jour en BDD : {eq['Nom']} -> {real_host}")
                    update_equipment_name(eq['ID'], real_host)
                    eq['Nom'] = real_host # On met à jour l'affichage en cours
                
                insert_metrics(eq['ID'], cpu, ram, disk, uptime)
                print(f"    [OK] Metrics collectées pour {eq['Nom']}")
            else:
                print(f"    [!] Erreur SSH (Clé/Auth) sur {eq['Nom']}")
        else:
            print(f"    [X] {eq['Nom']} est injoignable (Port 22 fermé)")
            
def run_system_monitoring():
    equipments = get_all_equipments()
    
    # Identifiants AD récupérés depuis le .env
    ad_domain = os.getenv('AD_DOMAIN', 'NTL')
    ad_user = os.getenv('AD_USER', 'Administrateur')
    ad_pass = os.getenv('AD_PASS', 'Formation2025')
    
    print(f"[*] Début du monitoring sur {len(equipments)} équipements...")
    
    for eq in equipments:
        # =========================================================
        # 1. VERIFICATION SSH ET RESSOURCES
        # =========================================================
        status = check_port(eq['IPv4'], 22)
        insert_service_status(eq['ID'], 'Serveur (SSH)', status)
        
        if status == "UP":
            metrics = get_ssh_metrics(eq['IPv4'], eq['SSH_User'], eq['OS'])
            if metrics:
                real_host, cpu, ram, disk, uptime = metrics
                
                # Auto-correction du nom si on a un "Unknown-"
                if eq['Nom'].startswith("Unknown-") and real_host:
                    print(f"    [+] Nom mis à jour en BDD : {eq['Nom']} -> {real_host}")
                    update_equipment_name(eq['ID'], real_host)
                    eq['Nom'] = real_host 
                
                insert_metrics(eq['ID'], cpu, ram, disk, uptime)
                print(f"    [OK] Metrics collectées pour {eq['Nom']}")
            else:
                print(f"    [!] Erreur SSH (Clé/Auth) sur {eq['Nom']}")
        else:
            print(f"    [X] {eq['Nom']} est injoignable (Port 22 fermé)")
            
        # =========================================================
        # 2. VERIFICATION DNS ET ACTIVE DIRECTORY
        # =========================================================
        nom_machine = eq['Nom'].upper()
        os_machine = str(eq['OS']).upper()
        
        # On ne lance les tests AD/DNS que sur les machines Windows
        if "WIN" in os_machine or "DC" in nom_machine or "AD" in nom_machine or "DNS" in nom_machine:
            print(f"    -> Test des services AD/DNS pour {eq['Nom']}...")
            
            # Test DNS
            etat_dns = check_dns(eq['IPv4'])
            insert_service_status(eq['ID'], 'DNS', etat_dns)
            if etat_dns == "UP":
                print(f"       [OK] Service DNS joignable")
            else:
                print(f"       [!] Service DNS injoignable")
            
            # Test AD
            etat_ad = check_ad(eq['IPv4'], ad_domain, ad_user, ad_pass)
            insert_service_status(eq['ID'], 'Active Directory', etat_ad)
            if etat_ad == "UP":
                print(f"       [OK] Service AD joignable")
            else:
                print(f"       [!] Service AD injoignable")