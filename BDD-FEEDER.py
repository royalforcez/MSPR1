import time
import sys
from core.scanner import run_network_scan
from core.monitoring import run_system_monitoring
from core.eol import run_eol_feed
from core.wms_backup import run_auto_backup

# === CONFIGURATION DES INTERVALLES (en secondes) ===
INTERVAL_CPU_RAM = 60          # Fréquent : 1 minute
INTERVAL_DISK = 86400          # Peu fréquent : 24 heures
INTERVAL_SCAN = 86400          # Peu fréquent : 24 heures
INTERVAL_EOL = 86400           # Peu fréquent : 24 heures
INTERVAL_BACKUP = 86400        # Sauvegarde : 24 heures

def main():
    print("=========================================")
    print("   NTL-SysToolbox Gatherer Service")
    print("=========================================")
    
    # On initialise à 0 pour forcer une exécution immédiate au démarrage
    last_cpu_ram = 0
    last_disk = 0
    last_scan = 0
    last_eol = 0
    last_backup = 0
    try:
        while True:
            current_time = time.time()

            # 1. Scan réseau
            if current_time - last_scan >= INTERVAL_SCAN:
                print("\n[*] Lancement de la tâche : AUTO-DISCOVERY (Scan Réseau)")
                run_network_scan()
                last_scan = current_time

            # 2. Check CPU / RAM (Fréquent)
            if current_time - last_cpu_ram >= INTERVAL_CPU_RAM:
                print("\n[*] Lancement de la tâche : MONITORING (CPU & RAM)")
                run_system_monitoring(check_type="cpu_ram")
                last_cpu_ram = current_time

            # 3. Check Disk (Peu fréquent)
            if current_time - last_disk >= INTERVAL_DISK:
                print("\n[*] Lancement de la tâche : MONITORING (DISK)")
                run_system_monitoring(check_type="disk")
                last_disk = current_time

            # 4. Check EOL (Peu fréquent)
            if current_time - last_eol >= INTERVAL_EOL:
                print("\n[*] Lancement de la tâche : EOL UPDATE")
                run_eol_feed() 
                print("[*] EOL update terminé")
                last_eol = current_time

            # 5. Lancement du Backup automatique (NOUVEAU)
            if current_time - last_backup >= INTERVAL_BACKUP:
                print("\n[*] Lancement de la tâche : DATABASE BACKUP")
                run_auto_backup() 
                print("[*] Backup terminé")
                last_backup = current_time

            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n[*] Arrêt manuel du service NTL-SysToolbox.")
        sys.exit(0)

if __name__ == "__main__":
    main()