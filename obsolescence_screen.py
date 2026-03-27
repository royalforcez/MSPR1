import curses
import ipaddress
import os
import csv
import re
from datetime import datetime
import logging

from session_manager import get_db_connection_ntl
from obsolescence.eol_api import EOLClient


EXPORT_DIR = "exports"


# =====================================================
# EXPORT CSV
# =====================================================

def export_csv(data, prefix="audit"):
    """
    Exporte les données dans backups/csv/ avec création automatique du dossier.
    """
    # 1. Définition du chemin cible
    target_dir = os.path.join("backups", "csv")
    
    try:
        # 2. Création du dossier s'il n'existe pas
        # exist_ok=True évite de lever une erreur si le dossier est déjà là
        os.makedirs(target_dir, exist_ok=True)
        
        # 3. Génération du nom de fichier avec horodatage
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.csv"
        filepath = os.path.join(target_dir, filename)
        
        # 4. Écriture du fichier
        if not data:
            logging.warning("Export CSV : Aucune donnée à exporter.")
            return None

        header = ["Hostname", "IP", "OS", "Version", "EOL Date", "Statut"]
        
        with open(filepath, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(data)
            
        logging.info(f"Export réussi : {filepath}")
        return filepath

    except Exception as e:
        logging.error(f"Erreur lors de l'export CSV dans {target_dir} : {e}")
        return None


# =====================================================
# STATUT EOL
# =====================================================

def get_status(eol_date):
    if not eol_date or eol_date == "N/A":
        return "INCONNU"

    try:
        if isinstance(eol_date, str):
            eol = datetime.strptime(eol_date, "%Y-%m-%d")
        else:
            eol = eol_date

        today = datetime.today()
        diff = (eol - today).days

        if diff < 0:
            return "OBSOLETE"
        if diff < 365:
            return "EOL < 1 AN"
        return "SUPPORTE"

    except Exception as e:
        logging.warning(f"Format de date invalide ou calcul impossible pour '{eol_date}' : {e}")
        return "INCONNU"


# =====================================================
# NORMALISATION OS / VERSION
# =====================================================

def normalize_os(os_name):
    if not os_name:
        logging.debug("normalize_os reçu une valeur vide.")
        return None

    os_name = os_name.lower()
    
    if "debian" in os_name: return "debian"
    if "ubuntu" in os_name: return "ubuntu"
    if "windows server" in os_name: return "windows-server"

    logging.debug(f"OS non géré par la normalisation : {os_name}")
    return None

def normalize_version(version, os_name=None):
    if not version:
        return None

    try:
        if os_name and "windows server" in os_name.lower():
            match = re.search(r"\b(20\d{2})\b", os_name)
            if match:
                return match.group(1)

        version = str(version).strip()
        if "." in version:
            return version.split(".")[0]
        return version
    except Exception as e:
        logging.error(f"Erreur lors de la normalisation de version '{version}' : {e}")
        return None


def extract_eol_date(release):
    eol = release.get("eol")
    
    # Log si l'objet release est vide ou mal formé
    if not release:
        logging.debug("extract_eol_date reçu un objet release vide.")

    if isinstance(eol, dict):
        return eol.get("date", "N/A")

    if isinstance(eol, str):
        return eol

    return (
        release.get("eolFrom")
        or release.get("eolDate")
        or release.get("extendedSupport")
        or "N/A"
    )


# =====================================================
# FETCH BDD
# =====================================================

def fetch_all_assets():
    try:
        logging.info("Tentative de connexion à la BDD NTL...")
        conn = get_db_connection_ntl()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                e.nom, e.ipv4, o.nom_os, o.version_os, el.date_expiration
            FROM tb_equipements e
            JOIN tb_os o ON e.id_os = o.id
            LEFT JOIN tb_end_of_life el ON o.id = el.id_os
            WHERE e.est_actif = 1
        """)

        rows = cursor.fetchall()
        conn.close()
        logging.info(f"Récupération BDD réussie : {len(rows)} équipements actifs trouvés.")
        return rows
    except Exception as e:
        logging.error(f"ECHEC FETCH BDD : {e}", exc_info=True)
        # On relance l'exception pour que l'interface puisse afficher le message d'erreur
        raise


# =====================================================
# LECTURE CSV
# =====================================================

def read_assets_from_csv(path):
    if not os.path.exists(path):
        logging.error(f"Fichier introuvable pour lecture : {path}")
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    assets = []
    try:
        with open(path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required_fields = ["hostname", "ip", "os_name", "os_version"]

            if not reader.fieldnames:
                logging.error(f"Le fichier CSV est vide ou sans entête : {path}")
                raise ValueError("CSV vide ou mal formaté")

            missing = [field for field in required_fields if field not in reader.fieldnames]
            if missing:
                logging.error(f"Colonnes manquantes dans {path} : {missing}")
                raise ValueError(f"Colonnes manquantes : {missing}")

            for line in reader:
                assets.append({
                    "hostname": (line.get("hostname") or "UNKNOWN").strip(),
                    "ip": (line.get("ip") or "").strip(),
                    "os_name": (line.get("os_name") or "UNKNOWN").strip(),
                    "os_version": (line.get("os_version") or "UNKNOWN").strip()
                })
        
        logging.info(f"Lecture CSV réussie : {len(assets)} lignes importées depuis {path}")
        return assets
    except Exception as e:
        logging.error(f"Erreur lors de la lecture du CSV {path} : {e}")
        raise


# =====================================================
# AUDIT CSV
# =====================================================

def audit_csv_assets(assets, client):
    results = []
    logging.info(f"Début de l'audit pour {len(assets)} assets.")

    for asset in assets:
        h, ip = asset["hostname"], asset["ip"]
        os_n, os_v = asset["os_name"], asset["os_version"]

        try:
            product = normalize_os(os_n)
            if not product:
                logging.warning(f"Audit impossible pour {h} : OS '{os_n}' non reconnu.")
                results.append([h, ip, os_n, os_v, "N/A", "INCONNU"])
                continue

            releases = client.list_releases(product)
            normalized_v = normalize_version(os_v, os_n)

            matched = next((r for r in releases if str(r.get("cycle") or r.get("name")) == normalized_v), None)

            if not matched:
                logging.warning(f"Version '{os_v}' (norm: '{normalized_v}') non trouvée pour {product} ({h}).")
                results.append([h, ip, os_n, os_v, "N/A", "INCONNU"])
                continue

            eol = extract_eol_date(matched)
            status = get_status(eol)
            results.append([h, ip, os_n, os_v, eol, status])

        except Exception as e:
            logging.error(f"Erreur critique lors de l'audit de {h} ({ip}) : {e}")
            results.append([h, ip, os_n, os_v, "N/A", "INCONNU"])

    return results


# =====================================================
# FILTRAGE RESEAU
# =====================================================

def filter_by_network(network_cidr, rows):
    try:
        network = ipaddress.ip_network(network_cidr, strict=False)
        filtered = [
            r for r in rows
            if r[1] and ipaddress.ip_address(r[1]) in network
        ]
        logging.info(f"Filtrage réseau {network_cidr} : {len(filtered)}/{len(rows)} équipements retenus.")
        return filtered
    except ValueError as e:
        logging.error(f"Format de réseau CIDR invalide : {network_cidr} ({e})")
        return []


# =====================================================
# INTERFACE PRINCIPALE
# =====================================================

def screen_obsolescence_audit(stdscr):
    # --- INITIALISATION ---
    logging.info("Entrée dans le module Audit d'Obsolescence.")
    
    # Configuration Curses
    stdscr.keypad(True)
    curses.curs_set(0)  # Masquer le curseur
    
    # Initialisation des couleurs (une seule fois au début)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1) # Texte normal
    curses.init_pair(2, curses.COLOR_GREEN, -1) # Sélection (Vert)
    curses.init_pair(3, curses.COLOR_CYAN, -1)  # Titre
    
    client = EOLClient()
    current_row = 0
    
    MODULES = [
        "Lister les versions d’un OS et leurs dates de fin de vie",
        "Lister les composants d’une plage réseau",
        "Lancer un audit depuis la base de données",
        "Lancer un audit depuis un fichier CSV",
        "Retour au menu principal"
    ]

    while True:
        try:
            stdscr.clear()
            h, w = stdscr.getmaxyx()

            # --- AFFICHAGE DU TITRE ---
            title = "--- MODULE AUDIT D'OBSOLESCENCE ---"
            stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(2, max(0, (w - len(title)) // 2), title)
            stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

            # --- AFFICHAGE DU MENU ---
            for i, module in enumerate(MODULES):
                x = 4
                y = 6 + i
                
                if i == current_row:
                    # STYLE SÉLECTIONNÉ : Vert + Gras + Indicateur ">"
                    stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
                    stdscr.addstr(y, x, f" > {module}")
                    stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
                else:
                    # STYLE NORMAL : Blanc
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(y, x, f"   {module}")
                    stdscr.attroff(curses.color_pair(1))

            # --- FOOTER ---
            footer = "↑/↓ : Naviguer | ENTER : Sélectionner | ESC : Retour"
            if h > 10: # Évite de crash sur de très petites fenêtres
                stdscr.addstr(h - 1, max(0, (w - len(footer)) // 2), footer)
            
            stdscr.refresh()

            # --- GESTION DES TOUCHES ---
            key = stdscr.getch()

            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(MODULES) - 1:
                current_row += 1
            elif key == 27: # ESC
                logging.info("Sortie du module via touche ESC.")
                break
            
            elif key in (curses.KEY_ENTER, 10, 13):
                logging.info(f"Exécution de : {MODULES[current_row]}")
                
                # --- LOGIQUE DES OPTIONS ---
                
                if current_row == 0: # API EOL DIRECT
                    stdscr.clear()
                    prompt = "Produit (ex: ubuntu, debian, windows-server) : "
                    stdscr.addstr(5, 4, prompt)
                    curses.echo()
                    product = stdscr.getstr(5, 4 + len(prompt)).decode('utf-8').strip().lower()
                    curses.noecho()

                    if product:
                        try:
                            releases = client.list_releases(product)
                            stdscr.clear()
                            stdscr.addstr(2, 4, f"Versions pour {product.upper()} :", curses.A_BOLD)
                            stdscr.addstr(4, 4, f"{'VERSION':<15} {'EOL DATE':<15} {'STATUT'}")
                            
                            for idx, r in enumerate(releases):
                                if 6 + idx >= h - 2: break
                                ver = r.get("cycle") or r.get("name") or "N/A"
                                eol = extract_eol_date(r)
                                stat = get_status(eol)
                                stdscr.addstr(6 + idx, 4, f"{ver:<15} {eol:<15} {stat}")
                            
                            stdscr.addstr(h-1, 4, "Appuyez sur une touche...")
                            stdscr.getch()
                        except Exception as e:
                            logging.error(f"Erreur API : {e}")
                            stdscr.addstr(7, 4, "Erreur : Produit introuvable ou problème réseau.")
                            stdscr.getch()

                elif current_row == 1: # RÉSEAU CIDR
                    stdscr.clear()
                    prompt = "Entrez le réseau CIDR (ex: 192.168.1.0/24) : "
                    stdscr.addstr(5, 4, prompt)
                    curses.echo()
                    cidr = stdscr.getstr(5, 4 + len(prompt)).decode('utf-8').strip()
                    curses.noecho()

                    try:
                        all_data = fetch_all_assets()
                        filtered = filter_by_network(cidr, all_data)
                        
                        stdscr.clear()
                        stdscr.addstr(2, 4, f"Résultats pour {cidr} ({len(filtered)} machines) :", curses.A_BOLD)
                        
                        display_rows = []
                        for idx, r in enumerate(filtered):
                            row_info = [r[0], r[1], r[2], r[3], "N/A", "INCONNU"]
                            display_rows.append(row_info)
                            if 4 + idx < h - 4:
                                stdscr.addstr(4 + idx, 4, f"{r[0]:<15} {r[1]:<15} {r[2]:<15}")
                        
                        stdscr.addstr(h-2, 4, "F3 : Export CSV | Autre touche : Retour")
                        k = stdscr.getch()
                        if k == curses.KEY_F3:
                            path = export_csv(display_rows, "network")
                            stdscr.addstr(h-3, 4, f"Exporté dans : {path}", curses.color_pair(2))
                            stdscr.getch()
                    except Exception as e:
                        stdscr.addstr(7, 4, f"Erreur : {e}")
                        stdscr.getch()

                elif current_row == 2: # AUDIT BDD
                    stdscr.clear()
                    stdscr.addstr(5, 4, "Analyse de la base de données...")
                    stdscr.refresh()
                    try:
                        data = fetch_all_assets()
                        results = [[r[0], r[1], r[2], r[3], str(r[4]), get_status(r[4])] for r in data]
                        path = export_csv(results, "db_audit")
                        stdscr.addstr(7, 4, f"Audit terminé ! Fichier : {path}")
                        stdscr.getch()
                    except Exception as e:
                        logging.error(f"Audit BDD failed : {e}")
                        stdscr.getch()

                elif current_row == 3: # AUDIT CSV
                    stdscr.clear()
                    prompt = "Chemin du fichier CSV : "
                    stdscr.addstr(5, 4, prompt)
                    curses.echo()
                    path_in = stdscr.getstr(5, 4 + len(prompt)).decode('utf-8').strip()
                    curses.noecho()
                    try:
                        assets = read_assets_from_csv(path_in)
                        results = audit_csv_assets(assets, client)
                        path_out = export_csv(results, "csv_audit")
                        stdscr.addstr(8, 4, f"Audit CSV terminé. Résultats dans : {path_out}")
                        stdscr.getch()
                    except Exception as e:
                        stdscr.addstr(8, 4, f"Erreur : {e}")
                        stdscr.getch()

                elif current_row == 4: # RETOUR
                    return

        except curses.error as e:
            logging.error(f"Erreur d'affichage Curses : {e}")