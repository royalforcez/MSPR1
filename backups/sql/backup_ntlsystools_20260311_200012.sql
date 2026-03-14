-- Backup SQL Automatique
-- Date: 2026-03-11 20:00:12.812776

CREATE DATABASE IF NOT EXISTS `ntlsystools`;
USE `ntlsystools`;

DROP TABLE IF EXISTS `EndOfLife`;
CREATE TABLE `EndOfLife` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `OS` varchar(50) DEFAULT NULL,
  `Version` varchar(50) DEFAULT NULL,
  `Date_expiration` date DEFAULT NULL,
  `Fin_Support` date DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

DROP TABLE IF EXISTS `Equipements`;
CREATE TABLE `Equipements` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `Nom` varchar(50) NOT NULL,
  `OS` varchar(50) DEFAULT NULL,
  `IPv4` varchar(50) DEFAULT NULL,
  `ID_Site` int(11) DEFAULT NULL,
  `ID_EOL` int(11) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `fk_equip_site` (`ID_Site`),
  KEY `fk_equip_eol` (`ID_EOL`),
  CONSTRAINT `fk_equip_eol` FOREIGN KEY (`ID_EOL`) REFERENCES `EndOfLife` (`ID`),
  CONSTRAINT `fk_equip_site` FOREIGN KEY (`ID_Site`) REFERENCES `Sites` (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

INSERT INTO `Equipements` VALUES 
(2, 'ROG-STRIX-REMI', 'WINDOWS-11', '192.168.1.180', 1, NULL),
(3, 'BDD-SQL', 'DEBIAN-13', '192.168.1.137', 1, NULL);

DROP TABLE IF EXISTS `EtatServices`;
CREATE TABLE `EtatServices` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `Nom_Service` varchar(50) DEFAULT NULL,
  `Etat` varchar(20) DEFAULT NULL,
  `Date_Heure` datetime DEFAULT current_timestamp(),
  `ID_Equipement` int(11) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `fk_etat_equip` (`ID_Equipement`),
  CONSTRAINT `fk_etat_equip` FOREIGN KEY (`ID_Equipement`) REFERENCES `Equipements` (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

INSERT INTO `EtatServices` VALUES 
(1, 'DNS', 'DOWN', '2026-02-17 22:08:16', 2),
(2, 'MySQL', 'DOWN', '2026-02-17 22:08:16', 2),
(3, 'DNS', 'DOWN', '2026-02-17 22:10:27', 2),
(4, 'MySQL', 'DOWN', '2026-02-17 22:10:27', 2),
(5, 'DNS', 'DOWN', '2026-02-17 22:10:27', 3),
(6, 'MySQL', 'UP', '2026-02-17 22:10:27', 3),
(7, 'DNS', 'DOWN', '2026-02-19 21:00:59', 2),
(8, 'MySQL', 'DOWN', '2026-02-19 21:00:59', 2),
(9, 'DNS', 'DOWN', '2026-02-19 21:00:59', 3),
(10, 'MySQL', 'UP', '2026-02-19 21:00:59', 3),
(13, 'DNS', 'DOWN', '2026-02-25 09:35:18', 2),
(14, 'MySQL', 'DOWN', '2026-02-25 09:35:18', 2),
(15, 'DNS', 'DOWN', '2026-02-25 09:35:18', 3),
(16, 'MySQL', 'UP', '2026-02-25 09:35:18', 3);

DROP TABLE IF EXISTS `Sites`;
CREATE TABLE `Sites` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `Nom` varchar(50) NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

INSERT INTO `Sites` VALUES 
(1, 'APPART-REMI');

DROP TABLE IF EXISTS `UtilisationRessources`;
CREATE TABLE `UtilisationRessources` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `CPU_Percent` int(11) DEFAULT NULL,
  `RAM_Usage_Percent` decimal(5,2) DEFAULT NULL,
  `Disk_Usage_Percent` decimal(5,2) DEFAULT NULL,
  `Date_Heure` datetime DEFAULT current_timestamp(),
  `uptime` varchar(50) DEFAULT NULL,
  `ID_Equipement` int(11) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `fk_util_equip` (`ID_Equipement`),
  CONSTRAINT `fk_util_equip` FOREIGN KEY (`ID_Equipement`) REFERENCES `Equipements` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

