-- Backup SQL Automatique
-- Base: ntlsystools

DROP TABLE IF EXISTS `endoflife`;
CREATE TABLE `endoflife` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `OS` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `Version` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `Date_expiration` date DEFAULT NULL,
  `Fin_Support` date DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

DROP TABLE IF EXISTS `equipements`;
CREATE TABLE `equipements` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Nom` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `OS` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `IPv4` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `ID_Site` int DEFAULT NULL,
  `ID_EOL` int DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `fk_equip_site` (`ID_Site`),
  KEY `fk_equip_eol` (`ID_EOL`),
  CONSTRAINT `fk_equip_eol` FOREIGN KEY (`ID_EOL`) REFERENCES `endoflife` (`ID`),
  CONSTRAINT `fk_equip_site` FOREIGN KEY (`ID_Site`) REFERENCES `sites` (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

DROP TABLE IF EXISTS `etatservices`;
CREATE TABLE `etatservices` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Nom_Service` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `Etat` varchar(20) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `Date_Heure` datetime DEFAULT CURRENT_TIMESTAMP,
  `ID_Equipement` int DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `fk_etat_equip` (`ID_Equipement`),
  CONSTRAINT `fk_etat_equip` FOREIGN KEY (`ID_Equipement`) REFERENCES `equipements` (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

DROP TABLE IF EXISTS `sites`;
CREATE TABLE `sites` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Nom` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

DROP TABLE IF EXISTS `utilisationressources`;
CREATE TABLE `utilisationressources` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `CPU_Percent` int DEFAULT NULL,
  `RAM_Usage_Percent` decimal(5,2) DEFAULT NULL,
  `Disk_Usage_Percent` decimal(5,2) DEFAULT NULL,
  `Date_Heure` datetime DEFAULT CURRENT_TIMESTAMP,
  `uptime` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `ID_Equipement` int DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `fk_util_equip` (`ID_Equipement`),
  CONSTRAINT `fk_util_equip` FOREIGN KEY (`ID_Equipement`) REFERENCES `equipements` (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

