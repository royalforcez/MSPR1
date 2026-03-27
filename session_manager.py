import curses
import os
import logging
import mysql.connector

# --- STOCKAGE RAM ---
DB_NTL = {"host": "", "user": "", "password": "", "database": "ntlsystools"}
DB_ENTREPRISE = {"host": "", "user": "", "password": "", "database": "wms_db"}
NAS_CONFIG = {"ip": "", "user": "", "password": "", "share": ""}

def load_from_file(filepath):
    """Charge les données depuis un fichier texte. Retourne (Bool, Message)."""
    if not os.path.exists(filepath):
        logging.warning(f"Tentative de chargement : Fichier introuvable ({filepath})")
        return False, "Fichier introuvable."
    try:
        data = {}
        with open(filepath, 'r') as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split('=', 1)
                    data[k] = v
        
        DB_NTL.update({"host": data.get('NTL_HOST', ''), "user": data.get('NTL_USER', ''), "password": data.get('NTL_PASS', '')})
        DB_ENTREPRISE.update({"host": data.get('ENT_HOST', ''), "user": data.get('ENT_USER', ''), "password": data.get('ENT_PASS', '')})
        NAS_CONFIG.update({"ip": data.get('NAS_IP', ''), "user": data.get('NAS_USER', ''), "password": data.get('NAS_PASS', ''), "share": data.get('NAS_SHARE', '')})
        
        logging.info(f"Configuration chargée avec succès depuis {filepath}")
        return True, "Importation réussie."
    except Exception as e:
        logging.error(f"Erreur lors de la lecture du fichier {filepath}: {e}")
        return False, f"Erreur : {str(e)}"

def get_input(stdscr, y, x, prompt, mask=False):
    """Saisie de texte sécurisée."""
    try:
        stdscr.addstr(y, x, prompt)
        stdscr.refresh()
        if mask:
            curses.noecho()
        else:
            curses.echo()
        
        # Capture et décodage sécurisé
        res_bytes = stdscr.getstr(y, x + len(prompt), 30)
        res = res_bytes.decode('utf-8').strip()
        curses.noecho()
        return res
    except Exception:
        return ""

def ask_credentials(stdscr):
    """Gère l'authentification. Retourne 0 si OK, 1 si Erreur."""
    global DB_NTL, DB_ENTREPRISE, NAS_CONFIG
    try:
        logging.info("Ouverture du module de configuration des accès.")
        curses.curs_set(1)
        h, w = stdscr.getmaxyx()
        
        stdscr.clear()
        stdscr.attron(curses.A_BOLD)
        stdscr.addstr(1, (w - 38) // 2, "   CONFIGURATION DES ACCÈS RÉSEAU")
        stdscr.attroff(curses.A_BOLD)
        stdscr.addstr(3, 2, " [F12] Charger config.txt | [ENTRÉE] Saisie Manuelle ", curses.A_DIM)
        stdscr.refresh()

        key = stdscr.getch()

        # --- OPTION F12 : CHARGEMENT FICHIER ---
        if key == curses.KEY_F12:
            stdscr.addstr(h-3, 4, "  CHEMIN DU FICHIER : ", curses.A_BOLD)
            curses.echo()
            path = stdscr.getstr(h-3, 27).decode('utf-8').strip()
            curses.noecho()
            
            success, msg = load_from_file(path)
            if success:
                stdscr.addstr(h-2, 4, f"✅ {msg}", curses.A_BOLD)
                stdscr.refresh()
                curses.napms(1000)
                return 0 # Code VALIDE
            else:
                stdscr.addstr(h-2, 4, f"❌ {msg}", curses.A_BOLD)
                stdscr.refresh()
                curses.napms(1500)
                # On ne quitte pas forcément, on laisse l'utilisateur passer à la saisie manuelle
                logging.warning("Échec F12, passage à la saisie manuelle.")

        # --- SAISIE MANUELLE ---
        stdscr.clear()
        
        # Section NTL
        stdscr.addstr(1, 2, "[ 1. BASE DE DONNÉES NTL ]", curses.A_REVERSE)
        DB_NTL["host"] = get_input(stdscr, 3, 4, "IP Serveur   : ")
        DB_NTL["user"] = get_input(stdscr, 4, 4, "Utilisateur  : ")
        DB_NTL["password"] = get_input(stdscr, 5, 4, "Mot de passe : ", mask=True)

        # Section ENTREPRISE
        stdscr.addstr(7, 2, "[ 2. BASE ENTREPRISE ]", curses.A_REVERSE)
        DB_ENTREPRISE["host"] = get_input(stdscr, 9, 4, "IP Serveur   : ")
        DB_ENTREPRISE["user"] = get_input(stdscr, 10, 4, "Utilisateur  : ")
        DB_ENTREPRISE["password"] = get_input(stdscr, 11, 4, "Mot de passe : ", mask=True)

        # Section NAS
        stdscr.addstr(13, 2, "[ 3. CONFIGURATION NAS ]", curses.A_REVERSE)
        NAS_CONFIG["ip"] = get_input(stdscr, 15, 4, "IP du NAS    : ")
        NAS_CONFIG["user"] = get_input(stdscr, 16, 4, "Utilisateur  : ")
        NAS_CONFIG["password"] = get_input(stdscr, 17, 4, "Mot de passe : ", mask=True)
        NAS_CONFIG["share"] = get_input(stdscr, 18, 4, "Nom Partage  : ")

        # Vérification minimale (ex: l'hôte NTL ne doit pas être vide)
        if not DB_NTL["host"]:
            logging.error("Saisie incomplète : l'hôte NTL est vide.")
            return 1 # Code INVALIDE

        stdscr.clear()
        stdscr.addstr(h // 2, (w - 20) // 2, "✅ CONFIGURATION TERMINEE", curses.A_BOLD)
        stdscr.refresh()
        curses.napms(1200)
        
        logging.info("Configuration manuelle terminée avec succès.")
        return 0 # Code VALIDE

    except Exception as e:
        logging.error(f"Erreur fatale dans ask_credentials : {e}")
        return 1

def get_db_connection_ntl():
    """Tente une connexion et logue le résultat."""
    try:
        conn = mysql.connector.connect(
            host=DB_NTL["host"],
            user=DB_NTL["user"],
            password=DB_NTL["password"],
            database=DB_NTL["database"]
        )
        logging.info("Connexion DB NTL réussie.")
        return conn
    except mysql.connector.Error as err:
        logging.error(f"Échec de connexion DB NTL : {err}")
        return None