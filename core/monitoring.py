import os
import paramiko
import socket
from dotenv import load_dotenv

from core.database import get_all_active_equipments, insert_metrics, insert_service_status, update_equipment_info, get_or_create_os
from core.dnspython import check_dns
from core.adpython import check_ad
from core.ssh_linux import get_linux_metrics
from core.ssh_windows import get_windows_metrics

load_dotenv()

def check_port(ip, port):
    """Vérifie si un port TCP spécifique est ouvert sur une IP donnée."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect((ip, port))
        return "UP"
    except:
        return "DOWN"
    finally:
        s.close()

def get_ssh_metrics(ip, username, check_type="all"):
    """
    Transmet le type de check (cpu, ram, disk) aux modules OS.
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key_path = os.getenv('SSH_KEY_PATH', '/root/.ssh/id_rsa')
    
    try:
        ssh.connect(ip, username=username, key_filename=key_path, timeout=10)
        
        metrics = get_linux_metrics(ssh, ip, check_type)
        if not metrics:
            metrics = get_windows_metrics(ssh, ip, check_type)
            
        return metrics

    except paramiko.AuthenticationException:
        print(f"        [ERR-1002] SSH Fail : Échec d'authentification (Clé/Mot de passe) sur {ip}.")
        return None
    except socket.timeout:
        print(f"        [ERR-1004] SSH Fail : Timeout de connexion sur {ip}.")
        return None
    except Exception as e:
        print(f"        [ERR-1004] SSH Fail : Échec critique sur {ip} ({e})")
        return None
    finally:
        ssh.close()

def run_system_monitoring(check_type="all"):
    equipments = get_all_active_equipments()
    if not equipments:
        print("[ERR-3001] Get BDD Fail : Aucun équipement actif trouvé ou erreur BDD.")
        return

    ad_domain = os.getenv('AD_DOMAIN', 'NTL')
    ad_user = os.getenv('AD_USER', 'Administrateur')
    ad_pass = os.getenv('AD_PASS', 'Formation2025')
    
    for eq in equipments:
        status = check_port(eq['ipv4'], 22)
        
        # On ne met à jour l'état du service SSH que lors d'un check fréquent (cpu_ram) ou global
        if check_type in ["all", "cpu_ram"]:
            insert_service_status(eq['id'], 'Serveur (SSH)', status)
        
        # Initialisation des drapeaux de vérification des services
        check_ad_dns = False
        check_bdd = False
        nom_machine_bdd = eq.get('nom', '').upper()
        
        if status == "UP":
            metrics = get_ssh_metrics(eq['ipv4'], eq['ssh_user'], check_type)
            if metrics:
                if check_type in ["all", "cpu_ram"]:
                    id_os = get_or_create_os(metrics['os_name'], metrics['os_version'])
                    update_equipment_info(eq['id'], metrics['host'], metrics['sn'], id_os)
                
                insert_metrics(eq['id'], metrics['cpu'], metrics['ram'], metrics['disk'], metrics['uptime'])
                print(f"    [OK] Metrics poussées pour {metrics['host']} (Mode: {check_type})")
                
                nom_machine = metrics['host'].upper()
                
                # Détection des mots clés via le hostname réel
                if metrics['os_type'] == "WINDOWS" or "DC" in nom_machine or "AD" in nom_machine or "DNS" in nom_machine:
                    check_ad_dns = True
                if "BDD" in nom_machine:
                    check_bdd = True
            else:
                if check_type in ["all", "cpu_ram"]:
                    print(f"    [!] Impossible de récupérer les métriques de {nom_machine_bdd} ({eq['ipv4']})")
                
                # Détection de secours via le nom en base de données (si SSH échoue)
                if "WIN" in nom_machine_bdd or "DC" in nom_machine_bdd or "AD" in nom_machine_bdd or "DNS" in nom_machine_bdd:
                    check_ad_dns = True
                if "BDD" in nom_machine_bdd:
                    check_bdd = True
        else:
            if check_type in ["all", "cpu_ram"]:
                print(f"    [ERR-1001] SSH Fail : {nom_machine_bdd} est injoignable (Port 22 fermé sur {eq['ipv4']})")
            
            # Détection de secours via le nom en base de données
            if "WIN" in nom_machine_bdd or "DC" in nom_machine_bdd or "AD" in nom_machine_bdd or "DNS" in nom_machine_bdd:
                check_ad_dns = True
            if "BDD" in nom_machine_bdd:
                check_bdd = True

        # === VERIFICATION DNS ET AD ===
        if check_ad_dns and check_type in ["all", "cpu_ram"]:
            print(f"    -> Test des services AD/DNS pour {nom_machine_bdd} ({eq['ipv4']})...")
            
            etat_dns = check_dns(eq['ipv4'])
            if etat_dns == "DOWN":
                print(f"        [ERR-2001] Service Fail : Le service DNS ne répond pas sur {eq['ipv4']}")
            insert_service_status(eq['id'], 'DNS', etat_dns)
            
            etat_ad = check_ad(eq['ipv4'], ad_domain, ad_user, ad_pass)
            if etat_ad == "DOWN":
                print(f"        [ERR-2002] Service Fail : Connexion Active Directory (LDAP) refusée sur {eq['ipv4']}")
            insert_service_status(eq['id'], 'Active Directory', etat_ad)

        # === VERIFICATION BASE DE DONNÉES (NOUVEAU) ===
        if check_bdd and check_type in ["all", "cpu_ram"]:
            print(f"    -> Test du service BDD (MySQL) pour {nom_machine_bdd} ({eq['ipv4']})...")
            
            # On vérifie si le port 3306 (MySQL/MariaDB) est ouvert et répond
            etat_bdd = check_port(eq['ipv4'], 3306)
            
            if etat_bdd == "DOWN":
                print(f"        [ERR-2003] Service Fail : Le service MySQL (port 3306) ne répond pas sur {eq['ipv4']}")
            
            # On insère le statut en BDD
            insert_service_status(eq['id'], 'Base de Données', etat_bdd)