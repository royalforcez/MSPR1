-- Backup SQL Automatique
-- Base: ntlsystools

DROP TABLE IF EXISTS `tb_end_of_life`;
CREATE TABLE `tb_end_of_life` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_os` int(11) NOT NULL,
  `date_expiration` date DEFAULT NULL,
  `fin_support` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_eol_os` (`id_os`),
  CONSTRAINT `fk_eol_os` FOREIGN KEY (`id_os`) REFERENCES `tb_os` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

DROP TABLE IF EXISTS `tb_equipements`;
CREATE TABLE `tb_equipements` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) NOT NULL,
  `ipv4` varchar(50) NOT NULL,
  `serial_number` varchar(100) DEFAULT NULL,
  `est_actif` tinyint(1) DEFAULT 1,
  `ssh_user` varchar(50) DEFAULT 'ntl_monitor',
  `id_site` int(11) DEFAULT NULL,
  `id_os` int(11) DEFAULT NULL,
  `id_eol` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_equip_site` (`id_site`),
  KEY `fk_equip_os` (`id_os`),
  KEY `fk_equip_eol` (`id_eol`),
  CONSTRAINT `fk_equip_eol` FOREIGN KEY (`id_eol`) REFERENCES `tb_end_of_life` (`id`),
  CONSTRAINT `fk_equip_os` FOREIGN KEY (`id_os`) REFERENCES `tb_os` (`id`),
  CONSTRAINT `fk_equip_site` FOREIGN KEY (`id_site`) REFERENCES `tb_sites` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

DROP TABLE IF EXISTS `tb_etat_services`;
CREATE TABLE `tb_etat_services` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom_service` varchar(50) DEFAULT NULL,
  `etat` varchar(20) DEFAULT NULL,
  `date_heure` datetime DEFAULT current_timestamp(),
  `id_equipement` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_etat_equip` (`id_equipement`),
  CONSTRAINT `fk_etat_equip` FOREIGN KEY (`id_equipement`) REFERENCES `tb_equipements` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=664 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

DROP TABLE IF EXISTS `tb_os`;
CREATE TABLE `tb_os` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom_os` varchar(100) NOT NULL,
  `version_os` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_os` (`nom_os`,`version_os`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

DROP TABLE IF EXISTS `tb_sites`;
CREATE TABLE `tb_sites` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(50) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

DROP TABLE IF EXISTS `tb_utilisation_ressources`;
CREATE TABLE `tb_utilisation_ressources` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cpu_percent` int(11) DEFAULT NULL,
  `ram_usage_percent` decimal(5,2) DEFAULT NULL,
  `disk_usage_percent` decimal(5,2) DEFAULT NULL,
  `date_heure` datetime DEFAULT current_timestamp(),
  `uptime` varchar(50) DEFAULT NULL,
  `id_equipement` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_util_equip` (`id_equipement`),
  CONSTRAINT `fk_util_equip` FOREIGN KEY (`id_equipement`) REFERENCES `tb_equipements` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=214 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

