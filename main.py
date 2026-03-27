import curses
import logging
import sys
from datetime import datetime

from home import screen_home
from ui import loading_screen
from session_manager import ask_credentials

# Configuration du logging
logging.basicConfig(
    filename='systoolbox.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main(stdscr):
    try:
        logging.info("--- DÉMARRAGE NTL SYSTOOLBOX ---")

        # Configuration curses
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()

        curses.init_pair(1, curses.COLOR_WHITE, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_CYAN, -1)

        # 1. Barre de chargement
        loading_screen(stdscr)
        logging.info("Interface UI initialisée.")

        # 2. Authentification (On attend 0 pour succès)
        auth_status = ask_credentials(stdscr)
        if auth_status != 0:
            logging.warning(f"Sortie : Authentification échouée ou annulée (Code: {auth_status})")
            return auth_status # On renvoie le code d'erreur spécifique de l'auth

        # 3. Lancement de l'interface principale
        logging.info("Utilisateur authentifié. Accès Home.")
        screen_home(stdscr)
        
        logging.info("Fermeture normale demandée par l'utilisateur.")
        return 0 # Succès total

    except KeyboardInterrupt:
        logging.info("Interruption manuelle (Ctrl+C).")
        return 0
    except Exception as e:
        logging.error(f"CRASH SYSTÈME : {str(e)}", exc_info=True)
        return 1 # Code 1 pour toute erreur non prévue

if __name__ == "__main__":
    # On récupère le code de sortie renvoyé par main() via wrapper
    exit_code = curses.wrapper(main)
    
    # Horodatage final dans la console (hors curses)
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    if exit_code == 0:
        print(f"[{timestamp}] [OK] NTL SysToolbox s'est terminé proprement.")
    else:
        print(f"[{timestamp}] [ERREUR] Sortie avec le code {exit_code}. Vérifiez 'systoolbox.log'.")
    
    sys.exit(exit_code)