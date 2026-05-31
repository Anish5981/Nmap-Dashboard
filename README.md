# 🛡️ Nmap Scan Parser & Dashboard System

A web-based **Network Asset Discovery and Nmap Scan Management System** built with Python, Flask, MySQL, and Bootstrap 5.

## 📋 Features

- **15 Nmap Scan Types** — Execute predefined scans from the browser UI
- **XML Parsing** — Automatically parses Nmap XML output into structured data
- **MySQL Storage** — Relational schema with scans, hosts, and ports tables
- **Searchable Dashboard** — Filter results by IP, port, service, and status
- **Scan History** — Full history with pagination and filtering
- **Host Detail Views** — Drill down into host and port information
- **Input Validation** — Strict sanitization to prevent command injection
- **Responsive Design** — Premium dark theme with Bootstrap 5

## 📸 Screenshots

*(Add your screenshots here before submission!)*
- `![Dashboard](docs/dashboard.png)`
- `![New Scan](docs/new_scan.png)`
- `![Scan Results](docs/scan_results.png)`

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.12 + Flask 3.x |
| Database | MySQL 8.0 |
| ORM | Flask-SQLAlchemy |
| Frontend | Bootstrap 5.3, HTML5, CSS3, JavaScript |
| Scanner | Nmap 7.99 |
| XML Parser | Python xml.etree.ElementTree |

## 📦 Prerequisites

- Python 3.10+
- MySQL 8.0+
- Nmap 7.x+ ([Download](https://nmap.org/download.html))

## 🚀 Setup & Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd "Nmap Scan Parser Ans Dashboard System"
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Edit the `.env` file with your MySQL credentials:

```env
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=nmap_dashboard
```

### 4. Create the Database

```bash
mysql -u root -p < schema.sql
```

Or the tables will be auto-created when the app starts.

### 5. Run the Application

```bash
python app.py
```

Visit **http://localhost:5000** in your browser.

## 📖 Usage Guide

1. **Dashboard Overview**: When you open the application, you'll see the main dashboard with high-level statistics (Total Scans, Hosts Discovered, Open Ports) and a table of your recent scans.
2. **Running a Scan**: 
   - Navigate to **New Scan** via the top navbar.
   - Enter your target IP or hostname (e.g., `127.0.0.1` or `scanme.nmap.org`).
   - Select one or more scan types by clicking the cards (e.g., *Fast Scan* or *OS Detection*).
   - Click **Execute Scan**. 
   - *Note: Multiple selections will run in the background concurrently.*
3. **Viewing Results**: 
   - Once a scan completes, click on it in the dashboard or history page.
   - You will see a detailed view of all hosts discovered during that scan.
   - Click **Details** on any specific host to view its operating system, MAC address, and a full breakdown of all open ports and services detected.
4. **Scan History**: Use the **History** tab to filter past scans by Target IP, Scan Type, or Status.

## 📁 Project Structure

```
├── app.py                  # Flask app entry point
├── config.py               # Configuration
├── models.py               # SQLAlchemy ORM models
├── schema.sql              # MySQL schema DDL
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
│
├── modules/
│   ├── scanner.py          # Nmap command execution
│   └── parser.py           # XML parsing logic
│
├── routes/
│   ├── dashboard.py        # Dashboard & history views
│   ├── scan.py             # Scan execution & detail views
│   └── api.py              # JSON API endpoints
│
├── templates/
│   ├── base.html           # Base layout
│   ├── dashboard.html      # Dashboard homepage
│   ├── new_scan.html       # New scan form
│   ├── scan_detail.html    # Scan results
│   ├── host_detail.html    # Host information
│   └── history.html        # Scan history
│
├── static/
│   ├── css/style.css       # Custom dark theme
│   └── js/app.js           # Frontend JavaScript
│
└── scans/                  # XML output files
```

## 🔍 Supported Nmap Scan Types

| # | Scan Type | Command |
|---|-----------|---------|
| 1 | Ping Scan | `nmap -sn <target>` |
| 2 | Fast Scan | `nmap -F <target>` |
| 3 | Service Version Detection | `nmap -sV <target>` |
| 4 | OS Detection | `nmap -O <target>` |
| 5 | TCP SYN Scan | `nmap -sS <target>` |
| 6 | TCP Connect Scan | `nmap -sT <target>` |
| 7 | UDP Scan | `nmap -sU <target>` |
| 8 | Aggressive Scan | `nmap -A <target>` |
| 9 | Scan Specific Ports | `nmap -p 22,80,443 <target>` |
| 10 | Top 100 Ports | `nmap --top-ports 100 <target>` |
| 11 | Full Port Scan | `nmap -p- <target>` |
| 12 | HTTP Title Detection | `nmap --script http-title <target>` |
| 13 | Vulnerability Scan | `nmap --script vuln <target>` |
| 14 | Network Range Scan | `nmap <CIDR range>` |
| 15 | Service Scan + XML | `nmap -sV <target> -oX scan.xml` |

## 🗄️ Database Schema

```
scans (id, target, scan_type, command_used, scan_time, raw_xml_path, duration_seconds, status)
  └── hosts (id, scan_id, ip_address, hostname, host_status, os_details)
        └── ports (id, host_id, port_number, protocol, port_state, service_name, service_version, script_output)
```

## ⚠️ Security Notes

- **Input Validation**: All target inputs are validated with strict regex patterns
- **No Shell Execution**: Commands use `subprocess.run()` with `shell=False`
- **SQL Injection Protection**: All queries use SQLAlchemy ORM with parameterized queries
- **XSS Protection**: Jinja2 auto-escaping is enabled
- **Scan only authorized networks**: Do not scan public internet targets

## 📄 License

This project is for educational purposes only.
