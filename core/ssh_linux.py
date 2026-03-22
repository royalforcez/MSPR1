def get_linux_metrics(ssh, ip, check_type="all"):
    """
    Exécute les commandes bash selon la fréquence demandée.
    """
    # Commandes dynamiques selon le check_type
    cmd_cpu = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d',' -f1" if check_type in ["all", "cpu_ram"] else "echo 0"
    cmd_ram = "free | grep Mem | awk '{print $3/$2 * 100.0}'" if check_type in ["all", "cpu_ram"] else "echo 0"
    cmd_disk = "df / | tail -1 | awk '{print $5}' | sed 's/%//'" if check_type in ["all", "disk"] else "echo 0"
    
    # Concaténation de la commande finale
    cmd_linux = f"hostname; {cmd_cpu}; {cmd_ram}; {cmd_disk}; uptime -p; source /etc/os-release && echo $NAME; source /etc/os-release && echo ${{DEBIAN_VERSION_FULL:-$VERSION_ID}}; cat /sys/class/dmi/id/product_serial 2>/dev/null || echo 'N/A'"
    
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd_linux, timeout=5)
        res_linux = stdout.read().decode('utf-8', errors='replace').strip().splitlines()
        
        if len(res_linux) >= 8 and "non reconnu" not in res_linux[0].lower() and "not recognized" not in res_linux[0].lower():
            cpu_val = res_linux[1].strip().replace(',', '.')
            return {
                "host": res_linux[0].strip(), 
                "cpu": float(cpu_val) if cpu_val else 0.0, 
                "ram": float(res_linux[2].strip().replace(',', '.')), 
                "disk": float(res_linux[3].strip().replace(',', '.')),
                "uptime": res_linux[4], 
                "os_name": res_linux[5].strip(), 
                "os_version": res_linux[6].strip(), 
                "sn": res_linux[7].strip(), 
                "os_type": "LINUX"
            }
        return None
        
    except Exception as e:
        print(f"        [ERR-1003] SSH Fail : Erreur d'exécution des commandes Linux sur {ip} ({e})")
        return None