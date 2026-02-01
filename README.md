    
    
    ███╗   ██╗████████╗██╗
    ████╗  ██║╚══██╔══╝██║
    ██╔██╗ ██║   ██║   ██║
    ██║╚██╗██║   ██║   ██║
    ██║ ╚████║   ██║   ███████╗
    ╚═╝  ╚═══╝   ╚═╝   ╚══════╝
    ███████╗██╗   ██╗███████╗
    ██╔════╝╚██╗ ██╔╝██╔════╝
    ███████╗ ╚████╔╝ ███████╗
    ╚════██║  ╚██╔╝  ╚════██║
    ███████║   ██║   ███████║
    ╚══════╝   ╚═╝   ╚══════╝
    ████████╗ ██████╗  ██████╗ ██╗     ██████╗  ██████╗ ██╗  ██╗
    ╚══██╔══╝██╔═══██╗██╔═══██╗██║     ██╔══██╗██╔═══██╗╚██╗██╔╝
       ██║   ██║   ██║██║   ██║██║     ██████╔╝██║   ██║ ╚███╔╝ 
       ██║   ██║   ██║██║   ██║██║     ██╔══██╗██║   ██║ ██╔██╗ 
       ██║   ╚██████╔╝╚██████╔╝███████╗██████╔╝╚██████╔╝██╔╝ ██╗
       ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝╚═════╝  ╚═════╝ ╚═╝  ╚═╝

Arborescence :


NTLSysToolbox/
│
├── main.py
├── ui.py                # loading_screen + draw_frame + couleurs
├── home.py              # écran d’accueil / menu
├── diagnostic.py        # module 1
├── sauvegarde.py        # module 2
└── obsolescence.py      # module 3

how to start ?

...\NTLSysToolbox>python main.py

bibliothèque utilisée :



CURSES ----- Utilité ---->

Gérer l’interface terminal “text-based”.
Permet de faire :
Fenêtres, cadres, bordures (draw_frame)
Couleurs (curses.init_pair)
Positionnement du texte (addstr)
Gestion du clavier (getch)
Masquer le curseur (curs_set(0))

curses fait partie de la stdlib Python, donc il n’a pas de date de fin de support tant que Python le maintient.
Tant que Python existe et est mis à jour, curses fonctionne.


TIME ----- Utilité ---->

Gérer les delays pour les animations :
time.sleep(0.01) pour la barre de chargement
Permet de ralentir l’interface afin que l’utilisateur voie la progression.


Partie de la stdlib Python, donc pas de date de fin.
Très stable, largement utilisé dans tous les projets Python.

