# Copyright (C) 2025 JECI SARL
#
# This file is part of Pristy Support.
#
# Pristy Support is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pristy Support is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Pristy Support.  If not, see <https://www.gnu.org/licenses/>.

"""HTML exporter for Pristy support tool."""

import os
import re
from datetime import datetime, timezone
from typing import Dict
from jinja2 import Environment, FileSystemLoader, select_autoescape

try:
    from dateutil import parser as dateutil_parser
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False


def get_template_dir() -> str:
    """Get path to templates directory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    return os.path.join(parent_dir, "templates")


def format_status_class(status: str) -> str:
    """Get CSS class for status."""
    classes = {
        "OK": "status-ok",
        "WARNING": "status-warning",
        "ERROR": "status-error",
        "CRITICAL": "status-critical",
    }
    return classes.get(status, "status-unknown")


def format_time_ago(created_str: str) -> str:
    """Format time elapsed since container creation."""
    if not created_str or created_str == "N/A":
        return ""

    if not HAS_DATEUTIL:
        return ""

    try:
        # Clean up the date string (remove timezone abbreviations like CEST, UTC, etc.)
        # Docker returns format like "2025-09-29 09:55:14 +0200 CEST"
        # We keep only the part before the timezone abbreviation
        cleaned_str = re.sub(r'\s+[A-Z]{3,4}$', '', created_str.strip())

        # Parse the date string
        created_date = dateutil_parser.parse(cleaned_str)

        # Make sure both dates are timezone aware
        now = datetime.now(timezone.utc)
        if created_date.tzinfo is None:
            created_date = created_date.replace(tzinfo=timezone.utc)
        else:
            created_date = created_date.astimezone(timezone.utc)

        # Calculate difference
        delta = now - created_date
        total_seconds = delta.total_seconds()

        if total_seconds < 3600:  # Less than 1 hour
            minutes = int(total_seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif total_seconds < 86400:  # Less than 1 day
            hours = int(total_seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif total_seconds < 2592000:  # Less than 30 days
            days = int(total_seconds / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        elif total_seconds < 31536000:  # Less than 1 year
            months = int(total_seconds / 2592000)
            return f"{months} month{'s' if months != 1 else ''} ago"
        else:
            years = int(total_seconds / 31536000)
            return f"{years} year{'s' if years != 1 else ''} ago"
    except Exception:
        return ""


def export_to_html(audit_data: Dict) -> str:
    """Export complete audit data to HTML format."""
    template_dir = get_template_dir()

    # Check if template exists, if not create inline template
    template_path = os.path.join(template_dir, "report.html.j2")

    if os.path.exists(template_path):
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )
        template = env.get_template("report.html.j2")
    else:
        # Use inline template
        template_str = get_inline_template()
        env = Environment(autoescape=select_autoescape(["html", "xml"]))
        template = env.from_string(template_str)

    # Add helper functions to template context
    from zoneinfo import ZoneInfo

    # Local time with timezone
    now_local = datetime.now().astimezone()
    timestamp_local = now_local.strftime("%Y-%m-%d %H:%M:%S %z")

    # Paris time
    now_paris = datetime.now(ZoneInfo("Europe/Paris"))
    timestamp_paris = now_paris.strftime("%H:%M:%S")

    timestamp = f"{timestamp_local} (Paris: {timestamp_paris})"

    return template.render(
        data=audit_data,
        timestamp=timestamp,
        status_class=format_status_class,
        time_ago=format_time_ago,
    )


def get_inline_template() -> str:
    """Get inline HTML template."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pristy Support Audit Report</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        html {
            scroll-behavior: smooth;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 10px;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #2c3e50;
            margin-top: 40px;
            margin-bottom: 20px;
            padding: 15px 20px;
            background: linear-gradient(135deg, #fff 60%, #3498db 80%);
            border-radius: 6px;
            border-left: 6px solid #5a67d8;
            color: white;
            font-size: 1.5em;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        }
        h3 {
            color: #2c3e50;
            margin-top: 30px;
            margin-bottom: 15px;
            padding: 10px 15px;
            background: linear-gradient(135deg, #eaeaea 40%, #6899b9 100%);
            border-left: 4px solid #3498db;
            border-radius: 4px;
            font-size: 1.2em;
            font-weight: 600;
        }
        h4 {
            color: #4a5568;
            margin-top: 20px;
            margin-bottom: 10px;
            padding: 5px 0;
            padding-left: 10px;
            border-left: 3px solid #cbd5e0;
            font-size: 1.1em;
            font-weight: 600;
        }
        .meta {
            color: #7f8c8d;
            margin-bottom: 30px;
        }
        .status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 0.9em;
        }
        .status-ok {
            background-color: #27ae60;
            color: white;
        }
        .status-warning {
            background-color: #f39c12;
            color: white;
        }
        .status-error, .status-critical {
            background-color: #e74c3c;
            color: white;
        }
        .status-unknown {
            background-color: #95a5a6;
            color: white;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }
        th {
            background-color: #3498db1c;
            color: #2c3e50;
            font-weight: 600;
        }
        tr:hover {
            background-color: #f8f9fa;
        }
        .metric {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }
        .metric-card {
            padding: 15px;
            border-radius: 3px;
            border-left: 4px solid #3498db;
        }
        .metric-label {
            font-weight: 600;
            color: #34495e;
            margin-bottom: 5px;
        }
        .metric-value {
            font-size: 1.5em;
            color: #2c3e50;
        }
        .issue {
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            border-left: 4px solid #e74c3c;
            background-color: #ffeaea;
        }
        .warning {
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            border-left: 4px solid #f39c12;
            background-color: #fff8e6;
        }
        .section {
            background-color: #ffffff;
            border-radius: 8px;
        }
        code {
            background-color: #ecf0f1;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        ul {
            margin-left: 20px;
            margin-top: 10px;
        }
        li {
            margin-bottom: 5px;
        }
        .log-sample {
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 6px;
            margin: 15px 0;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            overflow-x: auto;
            word-wrap: break-word;
            line-height: 1.3;
        }
        .log-sample div {
            margin-bottom: 0.8rem;
        }
        .log-sample h4 {
            color: #3498db;
            margin-top: 0;
        }
        .collapsible {
            background-color: #3498db;
            color: white;
            cursor: pointer;
            padding: 12px;
            width: 100%;
            border: none;
            text-align: left;
            outline: none;
            font-size: 1em;
            font-weight: 600;
            border-radius: 6px;
            margin-top: 10px;
            transition: background-color 0.3s;
        }
        .collapsible:hover {
            background-color: #2980b9;
        }
        .collapsible:after {
            content: '▼';
            float: right;
            margin-left: 10px;
        }
        .collapsible.active:after {
            content: '▲';
        }
        .collapsible-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }
        .collapsible-content.active {
            max-height: 5000px;
            transition: max-height 0.5s ease-in;
        }
        .header-with-logo {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
        }
        .header-with-logo h1 {
            margin: 0;
            border-bottom: none;
        }
        .pristy-logo {
            height: 60px;
            width: auto;
        }
        .toc {
            background-color: #ecf0f1;
            padding: 1rem 3rem;
        }
        .toc h2 {
            margin-top: 0;
            font-size: 1.2em;
            color: #2c3e50;
            background: none;
            padding: 0;
            border: none;
            box-shadow: none;
        }
        .toc ul {
            list-style: none;
            margin: 10px 0 0 0;
            padding: 0;
        }
        .toc li {
            margin: 8px 0;
        }
        .toc > ul > li {
            margin: 12px 0;
        }
        .toc-subsection {
            list-style: none;
            margin: 8px 0 0 20px !important;
            padding: 0;
            padding-left: 15px;
        }
        .toc-subsection li {
            margin: 6px 0;
            font-size: 0.95em;
        }
        .toc a {
            color: #1f2e37;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.2s;
            display: inline-block;
        }
        .toc > ul > li > a {
            font-weight: 600;
            font-size: 1.05em;
            color: #2c3e50;
        }
        .toc-subsection a {
            color: #4a90e2;
            font-weight: 400;
        }
        .toc a:hover {
            color: #2980b9;
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-with-logo">
            <h1>Pristy Support Audit Report</h1>
            <img src="https://pristy.fr/logos/logo-pristy-s.svg" alt="Pristy Logo" class="pristy-logo">
        </div>
        <div class="meta">
            <strong>Generated:</strong> {{ timestamp }}
        </div>

        {% if data.system and data.system.system_info %}
        <div class="section" id="system-overview">
            <h2>System Overview</h2>
            <div class="metric">
                <div class="metric-card">
                    <div class="metric-label">Hostname</div>
                    <div class="metric-value" style="font-size: 1.2em;">{{ data.system.system_info.hostname }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Operating System</div>
                    <div class="metric-value" style="font-size: 1em;">{{ data.system.system_info.os_distribution }}</div>
                </div>
                {% if data.system.cpu_info %}
                <div class="metric-card">
                    <div class="metric-label">CPU</div>
                    <div class="metric-value">{{ data.system.cpu_info.count }} cores</div>
                    <small style="color: #7f8c8d;">{{ data.system.cpu_info.model }}</small>
                </div>
                {% endif %}
                {% if data.system.memory_info %}
                <div class="metric-card">
                    <div class="metric-label">Memory</div>
                    <div class="metric-value">{{ data.system.memory_info.used_gb }} / {{ data.system.memory_info.total_gb }} GB</div>
                    <small style="color: #7f8c8d;">{{ data.system.memory_info.percent_used }}% used</small>
                </div>
                {% endif %}
                {% if data.system.memory_info and data.system.memory_info.swap_total_gb > 0 %}
                <div class="metric-card">
                    <div class="metric-label">Swap</div>
                    <div class="metric-value">{{ data.system.memory_info.swap_used_gb }} / {{ data.system.memory_info.swap_total_gb }} GB</div>
                    <small style="color: #7f8c8d;">{{ data.system.memory_info.swap_percent_used }}% used</small>
                </div>
                {% endif %}
            </div>

            {% if data.system.network_interfaces %}
            <h3>Network Interfaces</h3>
            <table>
                <thead>
                    <tr>
                        <th>Interface</th>
                        <th>IPv4 Address</th>
                        <th>IPv6 Address</th>
                    </tr>
                </thead>
                <tbody>
                    {% for interface in data.system.network_interfaces %}
                    <tr>
                        <td><code>{{ interface.name }}</code></td>
                        <td>{{ interface.ipv4 }}</td>
                        <td>{{ interface.ipv6 }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}
        </div>
        {% endif %}

        <div class="toc">
            <h2>Table of Contents</h2>
            <ul>
                {% if data.system and data.system.system_info %}
                <li><a href="#system-overview">System Overview</a></li>
                {% endif %}
                {% if data.system %}
                <li>
                    <a href="#system-checks">System Checks</a>
                    <ul class="toc-subsection">
                        {% if data.system.systemd_services %}
                        <li><a href="#systemd-services">Systemd Services</a></li>
                        {% endif %}
                        {% if data.system.docker_info and data.system.docker_info.available %}
                        <li><a href="#docker-information">Docker Information</a></li>
                        {% endif %}
                        {% if data.system.docker_networks %}
                        <li><a href="#docker-networks">Docker Networks</a></li>
                        {% endif %}
                        {% if data.system.docker_containers %}
                        <li><a href="#docker-containers">Docker Containers</a></li>
                        {% endif %}
                        {% if data.system.memory_limits %}
                        <li><a href="#memory-configuration">Memory Configuration</a></li>
                        {% endif %}
                        {% if data.system.disk_space %}
                        <li><a href="#disk-space">Disk Space</a></li>
                        {% endif %}
                        {% if data.system.firewall %}
                        <li><a href="#firewall">Firewall</a></li>
                        {% endif %}
                    </ul>
                </li>
                {% endif %}
                {% if data.database %}
                <li>
                    <a href="#database-statistics">Database Statistics</a>
                    <ul class="toc-subsection">
                        {% if data.database.statistics %}
                        <li><a href="#node-statistics">Node Statistics</a></li>
                        {% endif %}
                        {% if data.database.ratios %}
                        <li><a href="#ratios">Ratios</a></li>
                        {% endif %}
                        {% if data.database.statistics %}
                        <li><a href="#user-statistics">User Statistics</a></li>
                        <li><a href="#group-site-statistics">Group and Site Statistics</a></li>
                        {% endif %}
                        <li><a href="#storage-statistics">Storage Statistics</a></li>
                        {% if data.database.table_sizes %}
                        <li><a href="#table-sizes">Table Sizes</a></li>
                        {% endif %}
                        {% if data.database.nodes_by_store %}
                        <li><a href="#nodes-by-store">Nodes by Store</a></li>
                        {% endif %}
                        {% if data.database.nodes_by_type_top10 %}
                        <li><a href="#top-node-types">Top 10 Node Types</a></li>
                        {% endif %}
                    </ul>
                </li>
                {% endif %}
                {% if data.logs %}
                <li>
                    <a href="#logs-analysis">Logs Analysis</a>
                    <ul class="toc-subsection">
                        {% if data.logs.services %}
                        <li><a href="#service-log-summary">Service Log Summary</a></li>
                        <li><a href="#log-samples">Log Samples</a></li>
                        {% endif %}
                    </ul>
                </li>
                {% endif %}
                {% if data.config %}
                <li>
                    <a href="#configuration-review">Configuration Review</a>
                    <ul class="toc-subsection">
                        {% if data.config.alfresco %}
                        <li><a href="#alfresco-configuration">Alfresco Configuration</a></li>
                        {% endif %}
                        {% if data.config.pristy_apps %}
                        <li><a href="#pristy-apps-configuration">Pristy Applications Configuration</a></li>
                        {% endif %}
                    </ul>
                </li>
                {% endif %}
            </ul>
        </div>

        {% if data.system %}
        <div class="section" id="system-checks">
            <h2>System Checks</h2>

            {% if data.system.systemd_services %}
            <h3 id="systemd-services">Systemd Services</h3>
            <table>
                <thead>
                    <tr>
                        <th>Service</th>
                        <th>Enabled</th>
                        <th>Active</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for service in data.system.systemd_services %}
                    <tr>
                        <td>{{ service.name }}</td>
                        <td>{{ service.enabled }}</td>
                        <td>{{ service.active }}</td>
                        <td><span class="status {{ status_class(service.status) }}">{{ service.status }}</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}

            {% if data.system.docker_info and data.system.docker_info.available %}
            <h3 id="docker-information">Docker Information</h3>
            <ul>
                <li><strong>Docker Version:</strong> {{ data.system.docker_info.version }}</li>
            </ul>

            {% if data.system.docker_info.daemon_config %}
            <h4>Docker Daemon Configuration</h4>
            <p><strong>File:</strong> <code>{{ data.system.docker_info.daemon_config_path }}</code></p>
            <table>
                <thead>
                    <tr>
                        <th>Parameter</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    {% for key, value in data.system.docker_info.daemon_config.items() %}
                    <tr>
                        <td><code>{{ key }}</code></td>
                        <td><code>{{ value }}</code></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}
            {% endif %}

            {% if data.system.docker_networks %}
            <h3 id="docker-networks">Docker Networks</h3>
            <table>
                <thead>
                    <tr>
                        <th>Network</th>
                        <th>Driver</th>
                        <th>Scope</th>
                        <th>Subnets</th>
                        <th>Gateways</th>
                    </tr>
                </thead>
                <tbody>
                    {% for network in data.system.docker_networks %}
                    <tr>
                        <td><code>{{ network.name }}</code></td>
                        <td>{{ network.driver }}</td>
                        <td>{{ network.scope }}</td>
                        <td>
                            {% if network.subnets %}
                                {% for subnet in network.subnets %}
                                    <code>{{ subnet }}</code>{% if not loop.last %}<br>{% endif %}
                                {% endfor %}
                            {% else %}
                                N/A
                            {% endif %}
                        </td>
                        <td>
                            {% if network.gateways %}
                                {% for gateway in network.gateways %}
                                    <code>{{ gateway }}</code>{% if not loop.last %}<br>{% endif %}
                                {% endfor %}
                            {% else %}
                                N/A
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}

            {% if data.system.docker_containers %}
            <h3 id="docker-containers">Docker Containers</h3>
            <table>
                <thead>
                    <tr>
                        <th>Container</th>
                        <th>Image</th>
                        <th>Created</th>
                        <th>State</th>
                        <th>Health</th>
                    </tr>
                </thead>
                <tbody>
                    {% for container in data.system.docker_containers %}
                    <tr>
                        <td>{{ container.name }}</td>
                        <td>
                            {% set parts = container.image.split(':') %}
                            <code>{{ parts[0] }}{% if parts|length > 1 %}:<strong>{{ parts[1] }}</strong>{% endif %}</code>
                        </td>
                        <td>
                            {{ container.created }}
                            {% set elapsed = time_ago(container.created) %}
                            {% if elapsed %}
                            <br><small style="color: #7f8c8d;">({{ elapsed }})</small>
                            {% endif %}
                        </td>
                        <td>{{ container.state }}</td>
                        <td><span class="status {{ status_class(container.health) }}">{{ container.health }}</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}

            {% if data.system.memory_limits %}
            <h3 id="memory-configuration">Memory Configuration</h3>
            <div class="metric">
                <div class="metric-card">
                    <div class="metric-label">Total RAM</div>
                    <div class="metric-value">{{ data.system.memory_limits.total_ram_gb }} GB</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Available RAM</div>
                    <div class="metric-value">{{ data.system.memory_limits.available_ram_gb }} GB</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total Swap</div>
                    <div class="metric-value">{{ data.system.memory_limits.total_swap_gb }} GB</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Container Limits Sum</div>
                    <div class="metric-value">{{ data.system.memory_limits.total_limit_gb }} GB</div>
                </div>
            </div>
            {% if data.system.memory_limits.issues %}
                {% for issue in data.system.memory_limits.issues %}
                <div class="issue">{{ issue }}</div>
                {% endfor %}
            {% endif %}
            {% endif %}

            {% if data.system.disk_space %}
            <h3 id="disk-space">Disk Space</h3>
            <table>
                <thead>
                    <tr>
                        <th>Path</th>
                        <th>Total</th>
                        <th>Free</th>
                        <th>Free %</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for disk in data.system.disk_space %}
                    <tr>
                        <td><code>{{ disk.path }}</code></td>
                        <td>{{ disk.total_gb }} GB</td>
                        <td>{{ disk.free_gb }} GB</td>
                        <td>{{ disk.percent_free }}%</td>
                        <td><span class="status {{ status_class(disk.status) }}">{{ disk.status }}</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}

            {% if data.system.firewall %}
            <h3 id="firewall">Firewall</h3>
            <ul>
                <li><strong>Type:</strong> {{ data.system.firewall.type }}</li>
                <li><strong>Status:</strong> {{ data.system.firewall.status }}</li>
                <li><strong>Health:</strong> <span class="status {{ status_class(data.system.firewall.health) }}">{{ data.system.firewall.health }}</span></li>
            </ul>
            {% endif %}
        </div>
        {% endif %}

        {% if data.database %}
        <div class="section" id="database-statistics">
            <h2>Database Statistics</h2>
            <p><strong>Status:</strong> <span class="status {{ status_class(data.database.status) }}">{{ data.database.status }}</span></p>

            {% if data.database.statistics %}

            <h3 id="node-statistics">Node Statistics</h3>
            <div class="metric">
                <div class="metric-card">
                    <div class="metric-label">Nodes</div>
                    <div class="metric-value">{{ "{:,}".format(data.database.statistics.nodes) if data.database.statistics.nodes else 'N/A' }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Properties</div>
                    <div class="metric-value">{{ "{:,}".format(data.database.statistics.properties) if data.database.statistics.properties else 'N/A' }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Aspects</div>
                    <div class="metric-value">{{ "{:,}".format(data.database.statistics.aspects) if data.database.statistics.aspects else 'N/A' }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Content URLs</div>
                    <div class="metric-value">{{ "{:,}".format(data.database.statistics.content_urls) if data.database.statistics.content_urls else 'N/A' }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Content Data</div>
                    <div class="metric-value">{{ "{:,}".format(data.database.statistics.content_data) if data.database.statistics.content_data else 'N/A' }}</div>
                </div>
            </div>
            
            {% if data.database.ratios %}
            <h3 id="ratios">Ratios</h3>
            <ul>
                <li><strong>Properties per node:</strong> {{ data.database.ratios.properties_per_node }}</li>
                <li><strong>Aspects per node:</strong> {{ data.database.ratios.aspects_per_node }}</li>
            </ul>
            {% endif %}

            <h3 id="user-statistics">User Statistics</h3>
            <div class="metric">
                <div class="metric-card">
                    <div class="metric-label">Total Users</div>
                    <div class="metric-value">{{ "{:,}".format(data.database.statistics.users) if data.database.statistics.users else 'N/A' }}</div>
                </div>
                {% if data.database.statistics.internal_users is not none %}
                <div class="metric-card">
                    <div class="metric-label">Internal Users</div>
                    <div class="metric-value">{{ "{:,}".format(data.database.statistics.internal_users) }}</div>
                    <small style="color: #7f8c8d;">with password</small>
                </div>
                {% endif %}
                {% if data.database.statistics.external_users is not none %}
                <div class="metric-card">
                    <div class="metric-label">External Users</div>
                    <div class="metric-value">{{ "{:,}".format(data.database.statistics.external_users) }}</div>
                    <small style="color: #7f8c8d;">SSO/LDAP</small>
                </div>
                {% endif %}
            </div>

            {% if data.database.statistics.internal_users_list %}
            <h4>Internal Users List ({{ data.database.statistics.internal_users_list|length }})</h4>
            <ul>
                {% for user in data.database.statistics.internal_users_list[:10] %}
                <li><code>{{ user }}</code></li>
                {% endfor %}
            </ul>
            {% if data.database.statistics.internal_users_list|length > 10 %}
            <button class="collapsible">Show {{ data.database.statistics.internal_users_list|length - 10 }} more internal users</button>
            <div class="collapsible-content">
                <ul>
                    {% for user in data.database.statistics.internal_users_list[10:] %}
                    <li><code>{{ user }}</code></li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}
            {% endif %}

            <h3 id="group-site-statistics">Group and Site Statistics</h3>
            <div class="metric">
                <div class="metric-card">
                    <div class="metric-label">Groups (non-site)</div>
                    <div class="metric-value">{{ "{:,}".format(data.database.statistics.groups) if data.database.statistics.groups else 'N/A' }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Sites</div>
                    <div class="metric-value">{{ "{:,}".format(data.database.statistics.sites_count) if data.database.statistics.sites_count else 'N/A' }}</div>
                </div>
            </div>

            {% if data.database.statistics.groups_list %}
            <h3>Groups List ({{ data.database.statistics.groups_list|length }})</h3>
            <ul>
                {% for group in data.database.statistics.groups_list[:10] %}
                <li><code>{{ group }}</code></li>
                {% endfor %}
            </ul>
            {% if data.database.statistics.groups_list|length > 10 %}
            <button class="collapsible">Show {{ data.database.statistics.groups_list|length - 10 }} more groups</button>
            <div class="collapsible-content">
                <ul>
                    {% for group in data.database.statistics.groups_list[10:] %}
                    <li><code>{{ group }}</code></li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}
            {% endif %}

            {% if data.database.statistics.sites %}
            <h3>Sites List ({{ data.database.statistics.sites|length }})</h3>
            <ul>
                {% for site in data.database.statistics.sites[:10] %}
                <li><code>{{ site }}</code></li>
                {% endfor %}
            </ul>
            {% if data.database.statistics.sites|length > 10 %}
            <button class="collapsible">Show {{ data.database.statistics.sites|length - 10 }} more sites</button>
            <div class="collapsible-content">
                <ul>
                    {% for site in data.database.statistics.sites[10:] %}
                    <li><code>{{ site }}</code></li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}
            {% endif %}
            {% endif %}

            <h3 id="storage-statistics">Storage Statistics</h3>
            <div class="metric">
                {% if data.database.database_size %}
                <div class="metric-card">
                    <div class="metric-label">Database Size</div>
                    <div class="metric-value">{{ data.database.database_size }}</div>
                </div>
                {% endif %}
            </div>



            {% if data.database.table_sizes %}
            <h3 id="table-sizes">Table Sizes</h3>
            <table>
                <thead>
                    <tr>
                        <th>Table</th>
                        <th>Size</th>
                    </tr>
                </thead>
                <tbody>
                    {% for table, size in data.database.table_sizes.items() %}
                    <tr>
                        <td><code>{{ table }}</code></td>
                        <td>{{ size }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}

            {% if data.database.nodes_by_store %}
            <h3 id="nodes-by-store">Nodes by Store</h3>
            <table>
                <thead>
                    <tr>
                        <th>Store</th>
                        <th>Node Count</th>
                    </tr>
                </thead>
                <tbody>
                    {% for store, count in data.database.nodes_by_store.items() %}
                    <tr>
                        <td><code>{{ store }}</code></td>
                        <td>{{ "{:,}".format(count) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}

            {% if data.database.nodes_by_type_top10 %}
            <h3 id="top-node-types">Top 10 Node Types</h3>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Node Type</th>
                        <th>Count</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in data.database.nodes_by_type_top10 %}
                    <tr>
                        <td>{{ loop.index }}</td>
                        <td><code>{{ item.type }}</code></td>
                        <td>{{ "{:,}".format(item.count) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}
        </div>
        {% endif %}

        {% if data.logs %}
        <div class="section" id="logs-analysis">
            <h2>Logs Analysis</h2>
            <p><strong>Status:</strong> <span class="status {{ status_class(data.logs.status) }}">{{ data.logs.status }}</span></p>
            <p><strong>Period:</strong> Last {{ data.logs.since }}</p>

            {% if data.logs.services %}
            <h3 id="service-log-summary">Service Log Summary</h3>
            <table>
                <thead>
                    <tr>
                        <th>Service</th>
                        <th>Critical</th>
                        <th>Errors</th>
                        <th>Warnings</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for service in data.logs.services %}
                    {% if not service.error %}
                    <tr>
                        <td>{{ service.service }}</td>
                        <td>{{ service.critical_count }}</td>
                        <td>{{ service.error_count }}</td>
                        <td>{{ service.warning_count }}</td>
                        <td><span class="status {{ status_class(service.status) }}">{{ service.status }}</span></td>
                    </tr>
                    {% endif %}
                    {% endfor %}
                </tbody>
            </table>

            <h3 id="log-samples">Log Samples</h3>
            {% for service in data.logs.services %}
            {% if not service.error and (service.critical_count > 0 or service.error_count > 0 or service.warning_count > 0) %}
                {% if service.samples.CRITICAL %}
                <button class="collapsible">{{ service.service }} - Critical ({{ service.critical_count }} entries)</button>
                <div class="collapsible-content">
                    <div class="log-sample">
                        {% for sample in service.samples.CRITICAL[:10] %}
                        <div>{{ sample }}</div>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}

                {% if service.samples.ERROR %}
                <button class="collapsible">{{ service.service }} - Errors ({{ service.error_count }} entries)</button>
                <div class="collapsible-content">
                    <div class="log-sample">
                        {% for sample in service.samples.ERROR[:10] %}
                        <div>{{ sample }}</div>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}

                {% if service.samples.WARNING and not service.samples.CRITICAL and not service.samples.ERROR %}
                <button class="collapsible">{{ service.service }} - Warnings ({{ service.warning_count }} entries)</button>
                <div class="collapsible-content">
                    <div class="log-sample">
                        {% for sample in service.samples.WARNING[:10] %}
                        <div>{{ sample }}</div>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}
            {% endif %}
            {% endfor %}
            {% endif %}
        </div>
        {% endif %}

        {% if data.config %}
        <div class="section" id="configuration-review">
            <h2>Configuration Review</h2>
            <p><strong>Status:</strong> <span class="status {{ status_class(data.config.status) }}">{{ data.config.status }}</span></p>

            {% if data.config.alfresco %}
            <h3 id="alfresco-configuration">Alfresco Configuration</h3>
            <p><strong>Status:</strong> <span class="status {{ status_class(data.config.alfresco.status) }}">{{ data.config.alfresco.status }}</span></p>
            {% if data.config.alfresco.file_path %}
            <p><strong>File:</strong> <code>{{ data.config.alfresco.file_path }}</code></p>
            <p><strong>Total parameters:</strong> {{ data.config.alfresco.total_parameters }}</p>
            {% endif %}

            {% if data.config.alfresco.error %}
            <div class="issue">{{ data.config.alfresco.error }}</div>
            {% endif %}

            {% if data.config.alfresco.issues %}
            <h4>Issues:</h4>
            {% for issue in data.config.alfresco.issues %}
            <div class="issue">{{ issue }}</div>
            {% endfor %}
            {% endif %}

            {% if data.config.alfresco.warnings %}
            <h4>Warnings:</h4>
            {% for warning in data.config.alfresco.warnings %}
            <div class="warning">{{ warning }}</div>
            {% endfor %}
            {% endif %}

            {% if data.config.alfresco.key_parameters %}
            <h4>Key Parameters:</h4>
            <table>
                <thead>
                    <tr>
                        <th>Parameter</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    {% for key, value in data.config.alfresco.key_parameters.items() %}
                    <tr>
                        <td><code>{{ key }}</code></td>
                        <td>
                            {% if 'password' in key.lower() or 'secret' in key.lower() %}
                            ***MASKED***
                            {% else %}
                            {{ value }}
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}

            {% if data.config.alfresco.missing_parameters %}
            <h4>Missing Key Parameters ({{ data.config.alfresco.missing_parameters|length }}):</h4>
            <ul>
                {% for param in data.config.alfresco.missing_parameters[:10] %}
                <li><code>{{ param }}</code></li>
                {% endfor %}
                {% if data.config.alfresco.missing_parameters|length > 10 %}
                <li>... and {{ data.config.alfresco.missing_parameters|length - 10 }} more</li>
                {% endif %}
            </ul>
            {% endif %}
            {% endif %}

            {% if data.config.pristy_apps %}
            <h3 id="pristy-apps-configuration">Pristy Applications Configuration</h3>
            {% for app_name, app_config in data.config.pristy_apps.items() %}
            <h4>{{ app_name }}</h4>
            <p><strong>Status:</strong> <span class="status {{ status_class(app_config.status) }}">{{ app_config.status }}</span></p>
            {% if app_config.file_path %}
            <p><strong>File:</strong> <code>{{ app_config.file_path }}</code></p>
            <p><strong>Total parameters:</strong> {{ app_config.total_parameters }}</p>
            {% endif %}

            {% if app_config.error %}
            <div class="issue">{{ app_config.error }}</div>
            {% endif %}

            {% if app_config.key_parameters %}
            <h5>Key Parameters:</h5>
            <table>
                <thead>
                    <tr>
                        <th>Parameter</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    {% for key, value in app_config.key_parameters.items() %}
                    <tr>
                        <td><code>{{ key }}</code></td>
                        <td>
                            {% if 'password' in key.lower() or 'secret' in key.lower() %}
                            ***MASKED***
                            {% else %}
                            {{ value }}
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}

            {% if app_config.missing_parameters %}
            <h5>Missing Key Parameters ({{ app_config.missing_parameters|length }}):</h5>
            <ul>
                {% for param in app_config.missing_parameters %}
                <li><code>{{ param }}</code></li>
                {% endfor %}
            </ul>
            {% endif %}

            {% if app_config.warnings %}
            <h5>Warnings:</h5>
            <div style="margin-left: 20px;">
            {% for warning in app_config.warnings %}
            <div class="warning">{{ warning }}</div>
            {% endfor %}
            </div>
            {% endif %}
            {% endfor %}
            {% endif %}
        </div>
        {% endif %}
    </div>

    <script>
        // Add click event listeners to all collapsible buttons
        document.addEventListener('DOMContentLoaded', function() {
            var coll = document.getElementsByClassName('collapsible');
            for (var i = 0; i < coll.length; i++) {
                coll[i].addEventListener('click', function() {
                    this.classList.toggle('active');
                    var content = this.nextElementSibling;
                    content.classList.toggle('active');
                });
            }
        });
    </script>
</body>
</html>
"""
