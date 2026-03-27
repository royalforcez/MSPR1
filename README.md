    
    
      ███╗   ██╗████████╗██╗         ███████╗██╗   ██╗███████╗
      ████╗  ██║╚══██╔══╝██║         ██╔════╝╚██╗ ██╔╝██╔════╝
      ██╔██╗ ██║   ██║   ██║         ███████╗ ╚████╔╝ ███████╗
      ██║╚██╗██║   ██║   ██║         ╚════██║  ╚██╔╝  ╚════██║
      ██║ ╚████║   ██║   ███████╗    ███████║   ██║   ███████║
      ╚═╝  ╚═══╝   ╚═╝   ╚══════╝    ╚══════╝   ╚═╝   ╚══════╝
    ████████╗ ██████╗  ██████╗ ██╗     ██████╗  ██████╗ ██╗  ██╗
    ╚══██╔══╝██╔═══██╗██╔═══██╗██║     ██╔══██╗██╔═══██╗╚██╗██╔╝
       ██║   ██║   ██║██║   ██║██║     ██████╔╝██║   ██║ ╚███╔╝ 
       ██║   ██║   ██║██║   ██║██║     ██╔══██╗██║   ██║ ██╔██╗ 
       ██║   ╚██████╔╝╚██████╔╝███████╗██████╔╝╚██████╔╝██╔╝ ██╗
       ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝╚═════╝  ╚═════╝ ╚═╝  ╚═╝

Arborescence :


```
NTL-SysToolbox CLI
├── __pycache__
├── assets
├── diagnostic
│   ├── data_manager.py
│   ├── diagnostic_view.py
│   └── services.py
├── obsolescence
│   ├── __init__.py
│   └── eol_api.py
├── .gitignore
├── diagnostic_module.py
├── home.py
├── Lancer_Toolbox.bat
├── main.py
├── obsolescence_screen.py
├── README.md
├── requirements.txt
├── session_manager.py
├── ui.py
└── wms_backup.py
```





how to start ?

installer les dépendances : pip install -r requirements.txt

...\NTLSysToolbox>python main.py

bibliothèque utilisée :



Le projet s'appuie sur une sélection de bibliothèques ciblées :

mysql-connector-python : Pilotage natif des échanges avec la base de données.

curses : Gestion de l'affichage matriciel et des événements clavier.

json & csv : Modules standards pour la sérialisation des données et la génération de rapports interopérables.

decimal (Decimal) : Crucial pour la précision financière et technique. Par défaut, le format JSON ne supporte pas le type Decimal provenant de MySQL. L'import de ce module permet de convertir les données de stockage en types numériques sérialisables (float) sans perdre de précision lors du traitement.

time & datetime : Utilisées pour le rafraîchissement automatique (5s) et l'horodatage précis des rapports d'export.

mysql-connector-python : Driver officiel permettant la communication sécurisée avec les serveurs MariaDB et MySQL. Il gère l'exécution des requêtes de diagnostic.

smbclient : Permet au logiciel d'interagir avec des partages réseau (NAS) via le protocole SMB/CIFS (utilisé pour NAS_CONFIG).

os :  Utilisé pour la manipulation des dossiers système, notamment la création automatique du répertoire /exports.

L'ajout du module requests dans NTL‑SysToolbox permet au logiciel de dépasser le cadre du réseau local pour interagir avec des ressources distantes via le protocole HTTP/HTTPS.

dataclasses (dataclass) : Permet de définir des structures de données (objets) claires et typées pour représenter les équipements et les services. Cela remplace avantageusement les dictionnaires classiques en rendant le code plus lisible, plus facile à maintenir et en réduisant les erreurs de manipulation des données issues de la base SQL.

typing (Optional) : Utilisé pour le "Type Hinting" (indices de type) afin de sécuriser le développement. Le type Optional est crucial pour gérer les données qui peuvent être nulles (None), comme lorsqu'un serveur ne répond pas à une requête de performance, évitant ainsi des plantages lors du traitement des résultats.

ipaddress : Bibliothèque standard utilisée pour la validation et la manipulation des adresses réseaux. Elle garantit que les données importées (via SQL ou CSV) sont des adresses IPv4/IPv6 valides, évitant ainsi des erreurs lors des tests de connectivité ou des scans d'audit.

PyInstaller : Contrairement aux bibliothèques de code, PyInstaller est un utilitaire de packaging "hors-code". Son rôle est de transformer le script Python et toutes ses dépendances (modules, icônes, configurations) en un fichier exécutable unique (.exe). Cela permet de distribuer NTL‑SysToolbox sur des postes de travail n'ayant pas Python installé, garantissant ainsi une portabilité totale et une exécution isolée du système hôte.


