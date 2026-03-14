import time
import sys
from core.scanner import run_network_scan
from core.monitoring import run_system_monitoring

# Configuration des intervalles (en secondes)
INTERVAL_MONITORING = 300    # 5 minutes
INTERVAL_SCAN = 604800       # 7 jours

def main():
    print("=========================================")
    print("   NTL-SysToolbox Gatherer Service")
    print("=========================================")
    
    # On initialise à 0 pour forcer une exécution immédiate au démarrage
    last_monitoring = 0
    last_scan = 0

    try:
        while True:
            current_time = time.time()

            # Tâche 1 : Scan réseau (Auto-discovery)
            if current_time - last_scan >= INTERVAL_SCAN:
                run_network_scan()
                last_scan = current_time

            # Tâche 2 : Monitoring des ressources
            if current_time - last_monitoring >= INTERVAL_MONITORING:
                run_system_monitoring()
                last_monitoring = current_time

            # Le script dort 10 secondes avant de re-vérifier ses chronomètres
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n[*] Arrêt manuel du service NTL-SysToolbox.")
        sys.exit(0)

if __name__ == "__main__":
    main()