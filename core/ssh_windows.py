import base64

def get_windows_metrics(ssh, ip, check_type="all"):
    """
    Exécute le script PowerShell selon la fréquence demandée.
    """
    # Blocs conditionnels PowerShell
    ps_cpu_ram = """
    $cpu = (Get-CimInstance Win32_Processor).LoadPercentage
    if ($null -eq $cpu) { $cpu = 0 }
    $ram_raw = Get-CimInstance Win32_OperatingSystem
    $ram = [math]::Round((($ram_raw.TotalVisibleMemorySize - $ram_raw.FreePhysicalMemory) / $ram_raw.TotalVisibleMemorySize) * 100, 2)
    """ if check_type in ["all", "cpu_ram"] else "$cpu = 0; $ram = 0;"

    ps_disk = """
    $disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
    $disk_p = [math]::Round((($disk.Size - $disk.FreeSpace) / $disk.Size) * 100, 2)
    """ if check_type in ["all", "disk"] else "$disk_p = 0;"

    # Script final
    ps_script = f"""
    $ErrorActionPreference = 'SilentlyContinue'
    {ps_cpu_ram}
    {ps_disk}
    $os_info = Get-CimInstance Win32_OperatingSystem
    $up = (New-TimeSpan -Start $os_info.LastBootUpTime -End (Get-Date)).Hours
    $sn = (Get-CimInstance Win32_BIOS).SerialNumber
    
    Write-Output $env:COMPUTERNAME
    Write-Output $cpu
    Write-Output $ram
    Write-Output $disk_p
    Write-Output ("up " + $up + " hours")
    Write-Output $os_info.Caption
    Write-Output $os_info.Version
    Write-Output $sn
    """
    
    try:
        encoded_ps = base64.b64encode(ps_script.encode('utf-16-le')).decode('utf-8')
        cmd_win = f"powershell.exe -NonInteractive -NoProfile -EncodedCommand {encoded_ps}"
        
        stdin, stdout, stderr = ssh.exec_command(cmd_win, timeout=20)
        res_win = stdout.read().decode('utf-8', errors='replace').strip().splitlines()
        
        if len(res_win) >= 7:
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
            print(f"        [ERR-1003] SSH Fail : PowerShell n'a pas renvoyé les données attendues sur {ip}. ({err})")
            return None
            
    except Exception as e:
        print(f"        [ERR-1003] SSH Fail : Erreur d'exécution WMI/PowerShell sur {ip} ({e})")
        return None