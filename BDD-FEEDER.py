import time
import sys
from core.scanner import run_network_scan
from core.monitoring import run_system_monitoring

# === CONFIGURATION DES INTERVALLES (en secondes) ===
INTERVAL_CPU_RAM = 60          # Fréquent : 1 minute
INTERVAL_DISK = 3600           # Peu fréquent : 1 heure
INTERVAL_SCAN = 86400          # Scan Nmap : 24 heures

def main():
    print("=========================================")
    print("   NTL-SysToolbox Gatherer Service")
    print("=========================================")
    
    # On initialise à 0 pour forcer une exécution immédiate au démarrage
    last_cpu_ram = 0
    last_disk = 0
    last_scan = 0

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

            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n[*] Arrêt manuel du service NTL-SysToolbox.")
        sys.exit(0)

if __name__ == "__main__":
    main()