-- ============================================
-- Nmap Scan Parser & Dashboard System
-- Database Schema
-- ============================================

CREATE DATABASE IF NOT EXISTS nmap_dashboard
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE nmap_dashboard;

-- -------------------------------------------
-- Table: scans
-- Stores metadata about each Nmap scan run
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS scans (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    target          VARCHAR(255) NOT NULL,
    scan_type       VARCHAR(100) NOT NULL,
    command_used    VARCHAR(500) NOT NULL,
    scan_time       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    raw_xml_path    VARCHAR(500) NOT NULL,
    duration_seconds FLOAT DEFAULT NULL,
    status          ENUM('running', 'completed', 'failed', 'timeout') NOT NULL DEFAULT 'running',

    INDEX idx_scans_target (target),
    INDEX idx_scans_time (scan_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------
-- Table: hosts
-- Stores discovered hosts from each scan
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS hosts (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    scan_id         INT NOT NULL,
    ip_address      VARCHAR(45) NOT NULL,
    hostname        VARCHAR(255) DEFAULT NULL,
    host_status     ENUM('up', 'down') NOT NULL DEFAULT 'up',
    os_details      TEXT DEFAULT NULL,

    INDEX idx_hosts_ip (ip_address),
    CONSTRAINT fk_hosts_scan FOREIGN KEY (scan_id)
        REFERENCES scans(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------
-- Table: ports
-- Stores port information for each host
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS ports (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    host_id         INT NOT NULL,
    port_number     INT NOT NULL,
    protocol        VARCHAR(10) NOT NULL DEFAULT 'tcp',
    port_state      ENUM('open', 'closed', 'filtered') NOT NULL DEFAULT 'open',
    service_name    VARCHAR(100) DEFAULT NULL,
    service_version VARCHAR(255) DEFAULT NULL,
    script_output   TEXT DEFAULT NULL,

    INDEX idx_ports_number (port_number),
    INDEX idx_ports_service (service_name),
    CONSTRAINT fk_ports_host FOREIGN KEY (host_id)
        REFERENCES hosts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
