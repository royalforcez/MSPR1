import os
import paramiko
import socket
import base64
from dotenv import load_dotenv

from core.database import get_all_active_equipments, insert_metrics, insert_service_status, update_equipment_info, get_or_create_os
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

def get_ssh_metrics(ip, username):
    """Connexion SSH Aveugle : Tente Linux, puis Windows si échec."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key_path = os.getenv('SSH_KEY_PATH', '/root/.ssh/id_rsa')
    
    try:
        ssh.connect(ip, username=username, key_filename=key_path, timeout=10)
        
        # 1. TENTATIVE LINUX (La commande robuste qui a fait ses preuves)
        cmd_linux = "hostname; " \
                    "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d',' -f1; " \
                    "free | grep Mem | awk '{print $3/$2 * 100.0}'; " \
                    "df / | tail -1 | awk '{print $5}' | sed 's/%//'; " \
                    "uptime -p; " \
                    "source /etc/os-release && echo $NAME; " \
                    "source /etc/os-release && echo ${DEBIAN_VERSION_FULL:-$VERSION_ID}; " \
                    "cat /sys/class/dmi/id/product_serial 2>/dev/null || echo 'N/A'"
        
        stdin, stdout, stderr = ssh.exec_command(cmd_linux, timeout=5)
        res_linux = stdout.read().decode('utf-8', errors='replace').strip().splitlines()
        
        # Si on a bien nos lignes, on valide
        if len(res_linux) >= 8 and "non reconnu" not in res_linux[0].lower() and "not recognized" not in res_linux[0].lower():
            cpu_val = res_linux[1].strip().replace(',', '.')
            cpu_final = float(cpu_val) if cpu_val else 0.0
            return {
                "host": res_linux[0].strip(), 
                "cpu": cpu_final, 
                "ram": float(res_linux[2].strip().replace(',', '.')), 
                "disk": float(res_linux[3].strip().replace(',', '.')),
                "uptime": res_linux[4], 
                "os_name": res_linux[5].strip(), 
                "os_version": res_linux[6].strip(), 
                "sn": res_linux[7].strip(), 
                "os_type": "LINUX"
            }

        # --- TENTATIVE WINDOWS (Immunisée via Encodage Base64) ---
        ps_script = """
        $ErrorActionPreference = 'SilentlyContinue'
        $cpu = (Get-CimInstance Win32_Processor).LoadPercentage
        if ($null -eq $cpu) { $cpu = 0 }
        $os = Get-CimInstance Win32_OperatingSystem
        $ram = [math]::Round((($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / $os.TotalVisibleMemorySize) * 100, 2)
        $disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
        $disk_p = [math]::Round((($disk.Size - $disk.FreeSpace) / $disk.Size) * 100, 2)
        $up = (New-TimeSpan -Start $os.LastBootUpTime -End (Get-Date)).Hours
        $sn = (Get-CimInstance Win32_BIOS).SerialNumber
        
        Write-Output $env:COMPUTERNAME
        Write-Output $cpu
        Write-Output $ram
        Write-Output $disk_p
        Write-Output ("up " + $up + " hours")
        Write-Output $os.Caption
        Write-Output $os.Version
        Write-Output $sn
        """
        
        # On l'encode en Base64 (UTF-16LE est obligatoire pour PowerShell)
        encoded_ps = base64.b64encode(ps_script.encode('utf-16-le')).decode('utf-8')
        cmd_win = f"powershell.exe -NonInteractive -NoProfile -EncodedCommand {encoded_ps}"
        
        # On passe le timeout à 20 secondes (Windows WMI est lent)
        stdin, stdout, stderr = ssh.exec_command(cmd_win, timeout=20)
        
        res_win = stdout.read().decode('utf-8', errors='replace').strip().splitlines()
        
        # LE FIX EST ICI : On accepte 7 lignes (car le Numéro de Série peut être vide sur une VM Windows)
        if len(res_win) >= 7:
            # Si le SN est fourni (8 éléments ou plus), on le prend. Sinon, "N/A"
            sn_val = res_win[7].strip() if len(res_win) >= 8 else "N/A"
            return {
                "host": res_win[0].strip(), 
                "cpu": float(res_win[1].strip().replace(',', '.')), 
                "ram": float(res_win[2].strip().replace(',', '.')), 
                "disk": float(res_win[3].strip().replace(',', '.')),
                "uptime": res_win[4], 
                "os_name": res_win[5].strip(), 
                "os_version": res_win[6].strip(), 
                "sn": sn_val, 
                "os_type": "WINDOWS"
            }
        else:
            err = stderr.read().decode('utf-8', errors='replace').strip()
            if err or res_win:
                print(f"        [DEBUG WIN] Renvoyé par Windows -> {res_win} | Erreur: {err}")

        return None

    except Exception as e:
        # DEBUG : Affiche la VRAIE raison pour laquelle ça plante
        print(f"        [DEBUG] Échec critique sur {ip} : {e}")
        return None
    finally:
        ssh.close()

def run_system_monitoring():
    equipments = get_all_active_equipments()
    ad_domain = os.getenv('AD_DOMAIN', 'NTL')
    ad_user = os.getenv('AD_USER', 'Administrateur')
    ad_pass = os.getenv('AD_PASS', 'Formation2025')
    
    print(f"[*] Début du monitoring sur {len(equipments)} équipements actifs...")
    
    for eq in equipments:
        # === 1. VERIFICATION SSH ET RESSOURCES ===
        status = check_port(eq['ipv4'], 22)
        insert_service_status(eq['id'], 'Serveur (SSH)', status)
        
        # Variable pour déterminer si on doit lancer les tests AD/DNS
        check_ad_dns = False
        # Nom de la machine en base de données (sécurité si le SSH est DOWN)
        nom_machine_bdd = eq.get('nom', '').upper()
        
        if status == "UP":
            metrics = get_ssh_metrics(eq['ipv4'], eq['ssh_user'])
            if metrics:
                # Création/Récupération de l'OS
                id_os = get_or_create_os(metrics['os_name'], metrics['os_version'])
                
                # Mise à jour complète de la machine (Nom, SN, OS)
                update_equipment_info(eq['id'], metrics['host'], metrics['sn'], id_os)
                print(f"    [+] BDD à jour : {metrics['host']} | OS: {metrics['os_name']} | SN: {metrics['sn']}")
                
                # Poussée des ressources CPU/RAM
                insert_metrics(eq['id'], metrics['cpu'], metrics['ram'], metrics['disk'], metrics['uptime'])
                print(f"    [OK] Metrics collectées pour {metrics['host']}")
                
                # On détermine avec les métriques SSH s'il faut checker l'AD/DNS
                nom_machine = metrics['host'].upper()
                if metrics['os_type'] == "WINDOWS" or "DC" in nom_machine or "AD" in nom_machine or "DNS" in nom_machine:
                    check_ad_dns = True
            else:
                print(f"    [!] Erreur SSH (Clé/Auth) sur {eq['nom']} ({eq['ipv4']})")
                # Fallback : Si echec SSH mais qu'on sait que c'est du Windows via le nom BDD
                if "WIN" in nom_machine_bdd or "DC" in nom_machine_bdd or "AD" in nom_machine_bdd or "DNS" in nom_machine_bdd:
                    check_ad_dns = True
        else:
            print(f"    [X] {eq['nom']} est injoignable (Port 22 fermé)")
            # Fallback : Si SSH est DOWN, on se fie au nom BDD pour quand même tester l'AD/DNS
            if "WIN" in nom_machine_bdd or "DC" in nom_machine_bdd or "AD" in nom_machine_bdd or "DNS" in nom_machine_bdd:
                check_ad_dns = True

        # === 2. VERIFICATION DNS ET AD (Maintenant indépendante du SSH) ===
        if check_ad_dns:
            print(f"    -> Test des services AD/DNS pour {eq['nom']} ({eq['ipv4']})...")
            
            etat_dns = check_dns(eq['ipv4'])
            insert_service_status(eq['id'], 'DNS', etat_dns)
            
            etat_ad = check_ad(eq['ipv4'], ad_domain, ad_user, ad_pass)
            insert_service_status(eq['id'], 'Active Directory', etat_ad)