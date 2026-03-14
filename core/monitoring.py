import os
import paramiko
import socket
from core.database import get_all_equipments, insert_metrics, insert_service_status
from dotenv import load_dotenv

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
        # Timeout de connexion de 5 secondes pour éviter de bloquer le script
        ssh.connect(ip, username=username, key_filename=key_path, timeout=5)
        
        os_str = str(os_name).upper() # On gère 'DEBIAN-13' ou 'WINDOWS-11'

        if "DEBIAN" in os_str or "LINUX" in os_str:
            # Commande ultra-rapide qui ne bloque jamais
            cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d',' -f1; " \
                  "free | grep Mem | awk '{print $3/$2 * 100.0}'; " \
                  "df / | tail -1 | awk '{print $5}' | sed 's/%//'; " \
                  "uptime -p"
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=5)
            res = stdout.read().decode().splitlines()
            return float(res[0]), float(res[1]), float(res[2]), res[3]

        elif "WINDOWS" in os_str:
            # Commande PowerShell optimisée
            cmd = "powershell -Command \"$cpu = (Get-CimInstance Win32_Processor).LoadPercentage; $os = Get-CimInstance Win32_OperatingSystem; $ram = [math]::Round((($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / $os.TotalVisibleMemorySize) * 100, 2); $disk = Get-CimInstance Win32_LogicalDisk -Filter \\\"DeviceID='C:'\\\"; $disk_p = [math]::Round((($disk.Size - $disk.FreeSpace) / $disk.Size) * 100, 2); $up = (New-TimeSpan -Start $os.LastBootUpTime -End (Get-Date)).Hours; Write-Output $cpu; Write-Output $ram; Write-Output $disk_p; Write-Output $up\""
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=8)
            res = stdout.read().decode().splitlines()
            return float(res[0]), float(res[1]), float(res[2]), f"up {res[3]} hours"

    except Exception as e:
        # En cas d'erreur SSH, on retourne None pour ne pas faire planter le feeder
        return None
    finally:
        ssh.close()

def run_system_monitoring():
    equipments = get_all_equipments()
    for eq in equipments:
        # 1. On vérifie d'abord si le port SSH répond (Vérification de vie)
        status = check_port(eq['IPv4'], 22)
        insert_service_status(eq['ID'], 'Serveur (SSH)', status)
        
        if status == "UP":
            # 2. Si UP, on tente la collecte SSH
            metrics = get_ssh_metrics(eq['IPv4'], eq['SSH_User'], eq['OS'])
            if metrics:
                cpu, ram, disk, uptime = metrics
                insert_metrics(eq['ID'], cpu, ram, disk, uptime)
                print(f"    [OK] Metrics collectées pour {eq['Nom']}")
            else:
                print(f"    [!] Erreur SSH (Clé/Auth) sur {eq['Nom']}")
        else:
            print(f"    [X] {eq['Nom']} est injoignable (Port 22 fermé)")