"""
Windows Event Monitor - AI Edition
FINAL PERFECT VERSION - v25 (Major Apps & History Specialist)
"""

import flet as ft
from flet import *
import win32evtlog
import win32evtlogutil
import win32con
import pywintypes
import psutil
import datetime
import json
import time
import threading
from collections import Counter
from openai import OpenAI

#
# ==============================================================================
# ⬇️ START OF "TASK MANAGER" & "UPTIME" TOOLS (v20) ⬇️
# ==============================================================================
#
def get_top_processes(sort_by='cpu', num_processes=10):
    """
    Gets a list of top processes sorted by CPU or memory.
    """
    processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            try:
                proc.info['cpu_percent'] = proc.cpu_percent(interval=0.1)
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        time.sleep(0.2)
        
        for proc_info in processes:
            try:
                p = psutil.Process(proc_info['pid'])
                proc_info['cpu_percent'] = p.cpu_percent(interval=None)
            except psutil.NoSuchProcess:
                proc_info['cpu_percent'] = 0.0

        if sort_by == 'cpu':
            top_processes = sorted(processes, key=lambda p: p['cpu_percent'], reverse=True)
        elif sort_by == 'memory':
            top_processes = sorted(processes, key=lambda p: p['memory_percent'], reverse=True)
        else:
            return []

        formatted_list = []
        for p in top_processes[:num_processes]:
            if p['cpu_percent'] > 0.1 or p['memory_percent'] > 0.1:
                formatted_list.append(
                    f"- {p['name']} (PID: {p['pid']}): CPU {p['cpu_percent']:.1f}%, RAM {p['memory_percent']:.1f}%"
                )
        return formatted_list

    except Exception as e:
        print(f"Error getting top processes: {e}")
        return [f"Error getting processes: {e}"]

def get_realtime_system_stats():
    """
    The "Task Manager" tool. Returns a string of current system stats.
    """
    print("🤖 (AI Tool): Running get_realtime_system_stats()...")
    try:
        cpu_overall = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        top_cpu = get_top_processes(sort_by='cpu', num_processes=10)
        
        report = f"""
**Real-time System Stats (Task Manager View):**
* **Overall CPU Load:** {cpu_overall:.1f}%
* **Overall RAM Usage:** {ram.percent}% ({ram.used / (1024**3):.1f} GB / {ram.total / (1024**3):.1f} GB)

**Top 10 CPU Processes:**
"""
        if top_cpu:
            report += "\n".join(top_cpu)
        else:
            report += "No significant CPU processes found."
        
        print("🤖 (AI Tool): Stats report generated.")
        return report

    except Exception as e:
        print(f"Error in get_realtime_system_stats: {e}")
        return f"Error: Could not retrieve system stats. {e}"

def get_system_boot_time():
    """
    v20 "Uptime" Tool:
    Gets the exact system boot time.
    """
    print("🤖 (AI Tool): Running get_system_boot_time()...")
    try:
        boot_timestamp = psutil.boot_time()
        boot_time = datetime.datetime.fromtimestamp(boot_timestamp)
        uptime = datetime.datetime.now() - boot_time
        
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        response = (
            f"**Your PC has been on since:**\n\n"
            f"📅 **Boot Time:** {boot_time.strftime('%A, %B %d, %Y at %I:%M %p')}\n\n"
            f"⏱️ **Total Uptime:** {days} days, {hours} hours, and {minutes} minutes."
        )
        print("🤖 (AI Tool): Uptime report generated.")
        return response
    except Exception as e:
        print(f"Error getting boot time: {e}")
        return f"Error: Could not retrieve boot time. {e}"


def get_port_process_mapping():
    """
    Returns a dictionary:
    {
        port_number: {
            "pid": PID,
            "process_name": "chrome.exe",
            "status": "LISTEN" / "ESTABLISHED"
        }
    }
    """
    try:
        connections = psutil.net_connections()
        port_map = {}

        for conn in connections:
            try:
                if conn.laddr and conn.laddr.port:
                    port = conn.laddr.port
                    pid = conn.pid
                    status = conn.status

                    if pid:
                        try:
                            pname = psutil.Process(pid).name()
                        except:
                            pname = "Unknown"

                        port_map[port] = {
                            "pid": pid,
                            "process_name": pname,
                            "status": status
                        }
            except:
                pass

        return port_map

    except Exception as e:
        return {"error": str(e)}


def find_processes_on_port(port):
    port = int(port)
    full_map = get_port_process_mapping()
    
    return full_map.get(port, None)


def find_ports_for_process(process_name):
    pname = process_name.lower()
    full_map = get_port_process_mapping()
    results = {}

    for port, info in full_map.items():
        if pname in info["process_name"].lower():
            results[port] = info

    return results

# ==============================================================================
# ⬆️ END OF "PORT ANALYSIS" TOOL (v26) ⬆️
# ==============================================================================

def get_specific_process_stats(process_name_query):
    """
    v23 "Specific Process" Tool:
    Gets the CPU and RAM usage for a specific process name query.
    """
    print(f"🤖 (AI Tool): Running get_specific_process_stats(process_name='{process_name_query}')...")
    
    query_lower = process_name_query.lower()
    found_processes = {} # To aggregate stats by full process name
    total_cpu = 0.0
    total_ram_percent = 0.0
    total_ram_mb = 0.0
    count = 0
    
    # Ensure a baseline CPU measurement is available for interval=None
    psutil.cpu_percent(interval=0.1) 
    time.sleep(0.1) # Give psutil a moment to collect data

    try:
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
            try:
                proc_name = proc.info['name']
                
                # Check if the query is part of the process name
                if query_lower in proc_name.lower():
                    # Get stats (interval=None is non-blocking)
                    cpu = proc.cpu_percent(interval=None) 
                    ram_percent = proc.info['memory_percent']
                    ram_mb = proc.info['memory_info'].rss / (1024 * 1024) # RSS in MB

                    # Aggregate totals
                    total_cpu += cpu
                    total_ram_percent += ram_percent
                    total_ram_mb += ram_mb
                    count += 1
                    
                    # Store individual process info
                    if proc_name not in found_processes:
                        found_processes[proc_name] = {'count': 0, 'cpu': 0.0, 'ram_mb': 0.0}
                    
                    found_processes[proc_name]['count'] += 1
                    found_processes[proc_name]['cpu'] += cpu
                    found_processes[proc_name]['ram_mb'] += ram_mb

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        if count == 0:
            return f"**No processes found matching '{process_name_query}'.**\n\nIt might not be running, or the name is incorrect. (I searched for `*{query_lower}*`)"

        # Format the report
        report = f"**Stats for processes matching '{process_name_query}' ({count} total instances):**\n\n"
        report += f"📊 **Total CPU Load:** {total_cpu:.1f}%\n"
        report += f"🧠 **Total RAM Usage:** {total_ram_mb:.1f} MB ({total_ram_percent:.1f}% of system total)\n"

        # Show breakdown only if there are multiple *different* process names found
        if len(found_processes) > 1:
            report += "\n**Breakdown by process name:**\n"
            # Sort by RAM usage, descending
            sorted_processes = sorted(found_processes.items(), key=lambda item: item[1]['ram_mb'], reverse=True)
            for name, data in sorted_processes:
                report += f"- **{name}** ({data['count']} instances): {data['cpu']:.1f}% CPU, {data['ram_mb']:.1f} MB RAM\n"
        
        print("🤖 (AI Tool): Specific process report generated.")
        return report

    except Exception as e:
        print(f"Error in get_specific_process_stats: {e}")
        return f"Error: Could not retrieve stats for '{process_name_query}'. {e}"

#
# ==============================================================================
# ⬆️ END OF "SPECIFIC PROCESS" TOOL (v23) ⬆️
# ==============================================================================
#

# ==============================================================================
# ⬇️ START OF "MAJOR APPS" TOOL (v25) ⬇️
# ==============================================================================
def get_major_apps_overview():
    """
    v25 "Major Apps" Tool:
    Scans for a predefined list of popular/heavy applications.
    """
    print("🤖 (AI Tool): Running get_major_apps_overview()...")
    
    # The "Watchlist" - Add more here if you want!
    WATCHLIST = {
        # Browsers
        'chrome': 'Google Chrome', 'msedge': 'Microsoft Edge', 'firefox': 'Firefox', 'brave': 'Brave Browser',
        # Dev Tools
        'code': 'VS Code', 'devenv': 'Visual Studio (IDE)', 'idea64': 'IntelliJ IDEA', 'pycharm64': 'PyCharm',
        'java': 'Java Runtime', 'javaw': 'Java Runtime (Windowed)', 'node': 'Node.js', 'python': 'Python',
        'postgres': 'PostgreSQL', 'mysqld': 'MySQL', 'docker': 'Docker Desktop', 'wsl': 'WSL (Linux)',
        # Communication & Media
        'teams': 'Microsoft Teams', 'discord': 'Discord', 'slack': 'Slack', 'spotify': 'Spotify',
        # Productivity
        'excel': 'Microsoft Excel', 'winword': 'Microsoft Word', 'powerpnt': 'PowerPoint'
    }

    found_apps = {}

    try:
        for proc in psutil.process_iter(['name', 'memory_info']):
            try:
                p_name = proc.info['name'].lower()
                # Check if process name key is a substring of the full process name
                for key in WATCHLIST.keys():
                    if key in p_name:
                        readable_name = WATCHLIST[key]
                        if readable_name not in found_apps:
                            found_apps[readable_name] = {'count': 0, 'ram_mb': 0.0}
                        found_apps[readable_name]['count'] += 1
                        found_apps[readable_name]['ram_mb'] += proc.info['memory_info'].rss / (1024 * 1024)
                        break # Found a match for this process, move to next process
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        if not found_apps:
            return "**No major applications from my watchlist are currently running.**\n\n(My watchlist includes common browsers, dev tools, and office apps.)"

        # Sort by RAM usage descending
        sorted_apps = sorted(found_apps.items(), key=lambda item: item[1]['ram_mb'], reverse=True)

        report = "**Major Applications Currently Running (from Watchlist):**\n\n"
        for app_name, data in sorted_apps:
            report += f"🔹 **{app_name}**: {data['count']} processes, using **{data['ram_mb']:.0f} MB** RAM\n"
        
        print("🤖 (AI Tool): Major apps report generated.")
        return report

    except Exception as e:
        print(f"Error in get_major_apps_overview: {e}")
        return f"Error scanning for major apps: {e}"
# ==============================================================================
# ⬆️ END OF "MAJOR APPS" TOOL (v25) ⬆️
# ==============================================================================
        
class AIExplainer:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
        self.cache = {}
    
    def explain_event(self, event_id, event_type, source, message):
        cache_key = f"{event_id}_{event_type}_{source}_{message[:50]}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            message_snippet = message[:800]
            
            prompt = f"""Generate a comprehensive, detailed explanation for this Windows event:
Event ID: {event_id}, Type: {event_type}, Source: {source}, Message: {message_snippet}
Provide response in this EXACT JSON format:
{{
    "title": "Brief title with emoji (e.g., 🔄 System Uptime Recorded)",
    "simple": "One clear sentence explaining what happened in plain English",
    "detail": "4-5 sentences providing comprehensive technical details, root cause analysis, potential impacts, and context. Be thorough and educational.",
    "severity": "info/warning/error",
    "action": "2-3 sentences with specific actionable steps the user should take, with emojis",
    "technical": "Detailed technical breakdown including: what triggered this event, system components involved, and any relevant configuration details",
    "impact": "What this event means for system performance, security, and stability",
    "prevention": "How to prevent similar events or warnings in the future",
    "icon": "Single emoji that represents this event"
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Windows system expert who provides detailed, comprehensive technical analysis in simple language. Always respond with valid JSON only. Be thorough and educational."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            result = json.loads(response.choices[0].message.content)
            self.cache[cache_key] = result
            return result
            
        except Exception as e:
            icon_map = {'Error': '❌', 'Warning': '⚠️', 'Information': 'ℹ️'}
            icon = icon_map.get(event_type, 'ℹ️')
            
            return {
                'title': f'{icon} {source} Event',
                'simple': f'{source} generated a {event_type.lower()} event',
                'detail': message[:300] if message else 'A system event occurred.',
                'severity': event_type.lower(),
                'action': '✅ Review the event details and monitor for recurring patterns.',
                'technical': f'Event triggered by {source} component.',
                'impact': 'Minimal impact on system performance.',
                'prevention': 'Keep your system updated and monitor regularly.',
                'icon': icon
            }

#
# ==============================================================================
# ⬇️ START OF AI ASSISTANT (v25 "Major Apps & History" SPECIALIST BRAIN) ⬇️
# ==============================================================================
#
class AIAssistant:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
    def extract_process_name(self, user_msg):
        """
    Uses GPT to extract the actual application or process name from a user's query.
    """
        prompt = f"""
Extract the REAL application or process name from this message:

"{user_msg}"

Reply with only the process name in lowercase (NO sentences).
Examples:
- "visual studio code" -> code
- "vs code" -> code
- "visual studio" -> devenv
- "google chrome" -> chrome
- "microsoft edge" -> msedge
- "mysql server" -> mysqld
- "postgres database" -> postgres
- "steam client" -> steam
- "docker desktop" -> docker
- "which app uses port 8080" -> none

If unsure, reply "none".
"""

        try:
            res = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=5
            )
            return res.choices[0].message.content.strip().lower()
        except:
            return "none"


    
    def get_ai_plan(self, chat_history): 
        """
        UPDATED: v25 - Added "Major Apps" tool (v25) and
        process history NLU (v24).
        """
        
        current_time_str = datetime.datetime.now().strftime('%Y-%m-%d %A, %I:%M %p')
        today_date_str = datetime.date.today().strftime('%Y-%m-%d')
        yesterday_date_str = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        
        history_string = ""
        for msg in chat_history:
            role = "user" if msg['role'] == "user" else "assistant"
            history_string += f"{role}: {msg['content']}\n"
        
        system_prompt = f"""
You are an "Event Log Agent", a conversational AI expert with real-time "Task Manager", "Uptime", and "Specific Process" tools.
Your job is to analyze the user's *intent* (in any language) in the context of the chat history and decide on a plan.
Today's date and time is: **{current_time_str}**.

You MUST respond in one of six valid JSON formats:

---
**FORMAT 1: CHAT (Follow-up question)**
If the user's latest message is a question *about the events you just presented* (e.g., "are these serious?", "what is 'volsnap'?", "do u think these can be issue or others", "yeh kya hai?").
**Your Plan:** Answer conversationally.
{{
    "action": "chat",
    "response": "Your conversational answer here. Be helpful, concise, and use markdown. Use the user's language."
}}

---
**FORMAT 2: GET BOOT TIME (Uptime query)**
If the user asks "pc kab se on hai?", "when did my pc last boot?", "system uptime".
**Your Plan:** Use the specialist "Uptime" tool.
{{
    "action": "get_boot_time"
}}

---
**FORMAT 3: SEARCH LOGS (Past-tense / "Last Event" query)**
If the user asks about a *past* event (e.g., "what happened *yesterday*?", "pc *crashed last night*") OR a specific "last" event ("*last* restart", "*last* shutdown", "*last* update", "*last crash for chrome*").
**Your Plan:** Search *only* the Event Logs.
{{
    "action": "search_logs",
    "params": {{ (search parameters) }}
}}

---
**FORMAT 4: HYBRID ANALYSIS (Present-tense issue)**
If the user asks about a *current* problem (e.g., "why *is* my PC slow?", "my pc *is* hanging", "what *is* using my CPU?", "PC abhi slow kyu hai?", "achaanak se ye ram usage kyu badh gai meri").
**Your Plan:** Check *both* "Task Manager" stats and *recent* Event Logs.
{{
    "action": "hybrid_analysis",
    "params": {{ (search parameters for the logs) }},
    "analysis_request": "A 1-sentence summary of the user's goal (e.g., 'User is checking for real-time performance issues.')"
}}

---
**FORMAT 5: GET PROCESS STATS (Specific Process query)**
If the user asks about the CPU or RAM of a *specific* running program (e.g., "chrome ram", "visual studio cpu", "code.exe usage", "visual studio code ki ram usage kitni hai").
**Your Plan:** Use the specialist "Specific Process" tool.
{{
    "action": "get_process_stats",
    "params": {{
        "process_name": "The name of the process (e.g., 'chrome', 'visual studio', 'code.exe')"
    }}
}}

---
**FORMAT 6: CHECK MAJOR APPS (General Overview query)**
If the user asks "what major apps are running?", "what heavy processes are on?", "kaunse bade apps chal rahe hain?", "overview of my apps".
**Your Plan:** Use the specialist "Major Apps" tool.
{{
    "action": "check_major_apps"
}}

---
FORMAT 7: PORT ANALYSIS (Port or Application Network Query)
If user asks:
- "which app is using port 8080?"
- "list all apps using ports"
- "on which port is mysql running?"
- "show ports being used"
Your Plan:
{{
    "action": "port_analysis",
    "params": {{
        "port": "...",          (optional)
        "process_name": "..."   (optional)
    }}
}}
---

**How to Create Search `params` (Use your NLU)**

* **Concept: System Uptime**
    * **User says:** "pc kab se on hai?", "when did it boot?", "system uptime".
    * **Your Plan:** Use `action: "get_boot_time"`.

* **Concept: Windows Update (NEW v22)**
    * **User says:** "when was pc last updated?", "last update", "windows update history", "pc kab update hua tha".
    * **Your Plan:** Use `action: "search_logs"`.
    * **Set:** `log_type: "System"`, `search_keywords: ["19"]` (Event ID 19 is "Installation Successful").
    * **Set:** `find_most_recent: true`.
    * **Set:** `analysis_request: "User is checking for the last successful Windows Update."`

* **Concept: Specific Process Stats (NEW v23)**
    * **User says:** "what is chrome's ram usage?", "how much cpu is 'devenv.exe' using?", "visual studio ki ram kitni hai?", "check 'explorer.exe'", "vs code ram", "visual studio code ki ram".
    * **Your Plan:** Use `action: "get_process_stats"`.
    * **NLU Rule:** Extract the *executable name* if you know it, or the common name if you don't.
    * **Examples:**
        * "chrome" -> `params: {{"process_name": "chrome"}}` (matches chrome.exe)
        * "visual studio" -> `params: {{"process_name": "devenv"}}` (matches devenv.exe)
        * "visual studio code" OR "vs code" -> `params: {{"process_name": "code"}}` (matches Code.exe)
        * "explorer" -> `params: {{"process_name": "explorer"}}` (matches explorer.exe)
        * "word" -> `params: {{"process_name": "winword"}}` (matches WINWORD.EXE)

* **Concept: Application Crash/Hang (NEW v24 - Reliable)**
    * **User says:** "when did chrome last crash?", "show me the last time visual studio hung", "explorer.exe last error"
    * **Your Plan:** Use `action: "search_logs"`.
    * **NLU Rule:** Get the process name (e.g., "chrome", "devenv", "explorer").
    * **Set:** `log_type: "Application"`.
    * **Set:** `search_keywords: ["1000", "1002", "process_name_here"]` (e.g., ["1000", "1002", "chrome"])
    * **Set:** `find_most_recent: true`.
    * **Set:** `analysis_request: "User is checking for the last Application Crash (1000) or Hang (1002) for 'process_name_here'."`

* **Concept: Application Start/Stop (NEW v24 - Advanced)**
    * **User says:** "when was 'chrome.exe' last *opened*?", "when did 'devenv.exe' *restart*?", "last *shutdown* for 'explorer.exe'"
    * **Your Plan:** Use `action: "search_logs"`.
    * **NLU Rule:** Get the *exact* executable name (e.g., "chrome.exe", "devenv.exe").
    * **Set:** `log_type: "Security"`.
    * **Set:** `search_keywords: ["4688", "4689", "executable_name_here"]` (e.g., ["4688", "4689", "chrome.exe"])
    * **Set:** `find_most_recent: true`.
    * **Set:** `analysis_request: "User is checking for the last Process Start (4688) or Stop (4689) event for 'executable_name_here'. Note: This requires process auditing to be enabled."`

* **Concept: Performance Issues (e.g., "slow", "hang", "lag")**
    * **If Present Tense ("is slow"):** Use `action: "hybrid_analysis"`. Set `log_type: "Application"`, `event_type_filter: ["Error", "Warning"]`, and dates to *today*.
    * **If Past Tense ("was slow", "kal hang kr rha tha"):** Use `action: "search_logs"`. Set `log_type: "Application"` and dates to the specified past time (e.g., "last night").

* **Concept: System Stability (e.g., "crash", "restart", "shutdown")**
    * **Your Plan:** Use `action: "search_logs"`.
    * **Set:** `log_type: "System"`.
    * **Keywords:** `["6008"]` (crash), `["1074"]` (restart/shutdown), `["6005", "6006"]` (start/stop).
    * **If "last restart" or "last shutdown":** Set `find_most_recent: true`.

* **Concept: Time (CRITICAL - v21 Precision Rules)**
    * **"Last" Event:** Use `action: "search_logs"`, set `find_most_recent: true`, and **do not** set any dates.
    * **Present Tense ("is slow", "achaanak se"):**
        * Use `action: "hybrid_analysis"`.
        * The search `params` for the *logs* should be for **today**: `start_date: "{today_date_str}", end_date: "{today_date_str}"`.
    * **Past Tense / Specific Date:**
        * Use `action: "search_logs"`.
        * **"between 3 am and 4 am of 6th november":** `start_date: "2025-11-06"`, `start_time: "03:00"`, `end_date: "2025-11-06"`, `end_time: "04:00"`.
        * **"last night":** `start_date: "{yesterday_date_str}", start_time: "20:00", end_date: "{today_date_str}", end_time: "06:00"`.
        * **"yesterday":** `start_date: "{yesterday_date_str}", end_date: "{yesterday_date_str}"`.
        * **"this morning":** `start_date: "{today_date_str}", end_date: "{today_date_str}", start_time: "06:00", end_time: "11:00"`.
    * **Default (No time mentioned):** Default to **today**: `start_date: "{today_date_str}", end_date: "{today_date_str}"`.

---
**CHAT HISTORY (Analyze This):**
{history_string}

---
**Your Decision:**
Based on the *latest* user message in the context of the history, what is your plan?
Respond with *only* the valid JSON for "chat", "get_boot_time", "search_logs", "hybrid_analysis", "get_process_stats", or "check_major_apps".
"""
        msg = chat_history[-1]['content'].lower()

        import re

        # Case 1: direct port query like "port 8080" / "which app uses port 5000"
        port_match = re.findall(r"\bport\s*(\d+)\b", msg)
        if port_match:
            return {
                "action": "port_analysis",
                "params": {"port": port_match[0]}
            }

        # Case 2: which port a process is using
        # "mysql port", "on which port is postgres running"
        if "port" in msg:
            process_guess = self.extract_process_name(msg)
            if process_guess != "none":
                return {
                    "action": "port_analysis",
                    "params": {"process_name": process_guess}
                }


        # Case 3: list all ports
        if any(k in msg for k in ["ports", "all ports", "show ports", "list ports"]):
            return {"action": "port_analysis", "params": {}}

        try:
            user_query = chat_history[-1]['content']
            
            # Simple check to add context
            if "today" not in user_query.lower() and "yesterday" not in user_query.lower() and "last" not in user_query.lower() and "november" not in user_query.lower():
                if "am" in user_query.lower() or "pm" in user_query.lower():
                    chat_history[-1]['content'] = f"{user_query} (assume this is for today, {today_date_str})"
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt}
                ],
                temperature=0.0,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            plan = json.loads(response.choices[0].message.content)
            
            # Post-processing safety net
            if plan.get("action") == "search_logs" or plan.get("action") == "hybrid_analysis":
                query = chat_history[-1]['content']
                hang_terms = ['hang', 'freeze', 'lag', 'stuck', 'unresponsive', 'not responding', 'slow', 'feels slow']
                if any(k in query.lower() for k in hang_terms):
                    if 'params' not in plan: plan['params'] = {}
                    plan['params']['log_type'] = 'Application'
            
            return plan
        except Exception as e:
            print(f"Error getting AI plan: {e}")
            return {"action": "chat", "response": f"I encountered an error planning my next step: {e}"}

    def analyze_hybrid_results(self, analysis_request, realtime_stats, events_data):
        """
        v19 PROMPT:
        Synthesizes "Task Manager" data and Event Log data.
        """
        
        try:
            events = events_data if isinstance(events_data, list) else []
            
            system_prompt = f"""You are a Senior Windows System Administrator.
A user is investigating a real-time issue. Their goal is: **"{analysis_request}"**
You have been given TWO sets of data:
1.  **Real-time Stats:** The *current* "Task Manager" view.
2.  **Recent Events:** A list of *recent* relevant logs.
Your job is to *correlate and synthesize* this data into a single, high-level, intelligent summary.

**Your Analysis MUST Include:**
1.  **Executive Summary:** A 2-3 sentence answer to the user's question, *linking* the real-time stats to the event logs.
2.  **Real-time Finding:** What did you learn from the "Task Manager" data? (High CPU? High RAM? A specific process?)
3.  **Historical Finding:** What did you learn from the *recent* logs? (Any hang events? Errors? Warnings?)
4.  **Hypothesized Root Cause (Correlation):** How do these two findings relate? (e.g., "The high CPU in `process.exe` *correlates* with the 'Application Hang' event I found for it...")
5.  **Next Steps:** What should the user check next?

**CRITICAL ANALYSIS INSTRUCTIONS:**
* If the "Task Manager" data shows a high-CPU process (e.g., `jdk.exe`), *look for that process name* in the event logs.
* If the event logs show a specific error (e.g., Event ID 1002 for `chrome.exe`), *check if that process* is in the "Task Manager" list.
* If no clear correlation is found, state that. (e.g., "I see high CPU, but the recent logs seem unrelated. The high CPU might be temporary.")
* If no events are found, just report on the real-time stats.
* Use markdown for formatting.
"""
            
            context = f"**User's Goal:** {analysis_request}\n\n"
            context += "--- (DATA 1) REAL-TIME STATS ---\n"
            context += realtime_stats
            context += "\n\n"
            context += "--- (DATA 2) RECENT EVENT LOGS ---\n"
            if events:
                for i, evt in enumerate(events[:10]):
                    message_snippet = evt.get('message', '')[:300].strip()
                    context += f"- [{evt.get('event_type')}] ID {evt.get('event_id')} | {evt.get('time_generated')} | {evt.get('source')} | Msg: {message_snippet}...\n"
            else:
                context += "No relevant events were found in the specified time range.\n"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"⚠️ AI Synthesis Error: {str(e)}"

    def analyze_results(self, analysis_request, events_data):
        """
        v21 - This analyzer is "precision-focused".
        It gives a direct answer for "last event" queries.
        """
        try:
            if isinstance(events_data, list):
                events = events_data
            else:
                events = []
            
            is_last_event_query = "last" in analysis_request.lower() or "most recent" in analysis_request.lower()

            system_prompt = f"""You are a Senior Windows System Administrator and expert Event Log Analyst.
A user is investigating an issue. Their goal is: **"{analysis_request}"**
You have been given {len(events)} events matching their query.
Your job is to analyze these events and provide a high-level, intelligent summary.

**CRITICAL ANSWER FORMATTING:**

* **IF the user asked for the "last" or "most recent" event (e.g., "last shutdown", "last update", "last crash"):**
    Your *entire response* MUST be a single, direct answer. Find the single most recent event (it will be the first one in the list) and state the time and a brief summary.
    *Example:* "The last unexpected shutdown (Event 6008) occurred on **November 5th, 2025 at 10:30 AM**."
    *Example:* "The last user-initiated restart (Event 1074) was on **November 4th, 2025 at 08:00 PM**."
    *Example:* "The last successful Windows Update (Event 19) was on **November 3rd, 2025 at 04:15 AM**."
    *Example:* "The last application crash (Event 1000) for `chrome.exe` was on **November 2nd, 2025 at 01:20 PM**."
    (DO NOT provide the "Timeline, Patterns, Root Cause" sections for these queries).

* **IF the user asked for a general investigation (e.g., "what happened last night"):**
    Provide a full, detailed analysis using the format below:
    1.  **Executive Summary:** A 2-3 sentence answer.
    2.  **Timeline of Key Events:** The 3-5 most important events.
    3.  **Pattern Identification:** Any recurring errors or warnings.
    4.  **Hypothesized Root Cause:** What do you think is the cause?
    5.  **Next Steps:** What should the user check next?

Use markdown for formatting.
"""
            
            context = f"**Total Events Found:** {len(events)}\n\n**Event Log Data:**\n"
            
            if events:
                context += "--- Event Details ---\n"
                for i, evt in enumerate(events):
                    message_snippet = evt.get('message', '')[:300].strip()
                    context += f"- [{evt.get('event_type')}] ID {evt.get('event_id')} | {evt.get('time_generated')} | {evt.get('source')} | Msg: {message_snippet}...\n"
            else:
                context += "No events were found that match the user's query.\n"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1200
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"⚠️ AI Error: {str(e)}"

#
# ==============================================================================
# ⬆️ END OF AI ASSISTANT FIX ⬆️
# ==============================================================================
#

class EventLogReader:
    def read_events(self, log_type='System', max_records=500, start_datetime=None, end_datetime=None, hide_common=False, keywords=None, event_type_filter=None):
        if keywords is None:
            keywords = []
            
        try:
            events = []
            hand = win32evtlog.OpenEventLog('localhost', log_type)
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            
            common_sources = ['BITS', 'gpsvc', 'Microsoft-Windows-GroupPolicy', 'Microsoft-Windows-Bits-Client', 
                            'DCOM', 'DistributedCOM', 'USER32', 'DeviceSetupManager', 'WinMgmt', 
                            'Microsoft-Windows-Time-Service', 'Service Control Manager',
                            'Kernel-Power', 'Kernel-General']
            
            count = 0
            total_read = 0
            max_scan_limit = 999999999
            
            print(f"\n{'='*80}")
            print(f"🔍 READING {log_type} LOG (BACKWARDS - UNLIMITED SCAN)")
            if start_datetime: print(f"    📅 START: {start_datetime}")
            if end_datetime: print(f"      📅 END: {end_datetime}")
            if keywords: print(f"      🔑 KEYWORDS: {keywords}")
            if event_type_filter: print(f"      🚦 TYPE FILTER: {event_type_filter}")
            print(f"      🙈 HIDE COMMON: {hide_common}")
            print(f"      📊 Scanning until we find {max_records} matching events...")
            print(f"{'='*80}\n")
            
            stop_scanning = False
            
            while count < max_records and total_read < max_scan_limit and not stop_scanning:
                event_records = win32evtlog.ReadEventLog(hand, flags, 0)
                if not event_records:
                    print(f"\n⚠️ Reached end of event log (scanned all {total_read} events)")
                    break
                
                for event in event_records:
                    total_read += 1
                    
                    if total_read % 1000 == 0:
                        print(f"     📊 Scanned {total_read} events... Found {count} matches so far...")
                    
                    if count >= max_records:
                        print(f"\nℹ️ Reached 'max_records' limit of {max_records}. Stopping scan.")
                        stop_scanning = True
                        break
                    
                    event_time = event.TimeGenerated
                    
                    if end_datetime and event_time > end_datetime:
                        continue
                    
                    if start_datetime and event_time < start_datetime:
                        if total_read > 500:
                            print(f"\nℹ️ Reached start of date range. Stopping scan at {event_time}.")
                            stop_scanning = True
                            break
                        continue 
                    
                    event_type = self._get_event_type(event.EventType)
                    
                    if event_type_filter:
                        if event_type not in event_type_filter:
                            continue

                    source = event.SourceName
                    
                    if hide_common and any(common.lower() in source.lower() for common in common_sources):
                        continue
                    
                    try:
                        message = win32evtlogutil.SafeFormatMessage(event, log_type)
                    except Exception:
                        message = ' '.join(str(s) for s in event.StringInserts) if event.StringInserts else 'No description available'

                    if keywords:
                        message_lower = message.lower()
                        event_id_str = str(event.EventID & 0xFFFF) 
                        
                        if not any(k.lower() in message_lower or k.lower() in source.lower() or k == event_id_str for k in keywords):
                            continue

                    event_data = {
                        'source': source,
                        'event_id': event.EventID & 0xFFFF,
                        'event_type': event_type,
                        'time_generated': event.TimeGenerated.Format(),
                        'computer': event.ComputerName,
                        'message': message.strip()
                    }
                    events.append(event_data)
                    count += 1
                    
                    if count <= 5 or count % 10 == 0:
                        print(f"✅ Found {count} matching events...")
            
            win32evtlog.CloseEventLog(hand)
            print(f"\n{'='*80}")
            print(f"✅ RETURNED {len(events)} events (scanned {total_read} total)")
            print(f"{'='*80}\n")
            return events
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            if "Access is denied" in str(e):
                raise Exception("Access Denied. Please run this application as an Administrator to read all event logs (especially 'Security').")
            raise Exception(f"Error reading event log: {str(e)}")
    
    def _get_event_type(self, event_type):
        types = {
            win32con.EVENTLOG_ERROR_TYPE: 'Error',
            win32con.EVENTLOG_WARNING_TYPE: 'Warning',
            win32con.EVENTLOG_INFORMATION_TYPE: 'Information',
            win32con.EVENTLOG_AUDIT_SUCCESS: 'Audit Success',
            win32con.EVENTLOG_AUDIT_FAILURE: 'Audit Failure'
        }
        return types.get(event_type, 'Unknown')


def parse_time_input(time_str):
    if not time_str or not time_str.strip():
        return None
    time_str = time_str.strip().lower().replace(' ', '')
    is_pm = 'pm' in time_str
    is_am = 'am' in time_str
    time_str = time_str.replace('am', '').replace('pm', '')
    try:
        if ':' in time_str:
            parts = time_str.split(':')
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
        else:
            if len(time_str) >= 3:
                hour = int(time_str[:-2])
                minute = int(time_str[-2:])
            else:
                hour = int(time_str)
                minute = 0
        if is_pm and hour != 12:
            hour += 12
        elif is_am and hour == 12:
            hour = 0
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return (hour, minute)
        return None
    except:
        return None


def main(page: Page):
    page.title = "Event Monitor Pro"
    page.padding = 0
    page.window_width = 1450
    page.window_height = 950
    page.window_resizable = True
    page.scroll = ScrollMode.HIDDEN
    
    is_dark_mode = [False]
    
    LIGHT_THEME = {
        'PRIMARY': "#4f46e5", 'SUCCESS': "#10b981", 'WARNING': "#f59e0b", 'ERROR': "#ef4444",
        'BG': "#f8fafc", 'CARD': "#ffffff", 'TEXT': "#0f172a", 'TEXT_LIGHT': "#64748b",
        'ACCENT': "#3b82f6", 'WHITE': "#ffffff", 'DIVIDER': "#e2e8f0", 'BORDER': "#cbd5e1"
    }
    
    DARK_THEME = {
        'PRIMARY': "#818cf8", 'SUCCESS': "#34d399", 'WARNING': "#fbbf24", 'ERROR': "#f87171",
        'BG': "#0f172a", 'CARD': "#1e293b", 'TEXT': "#f1f5f9", 'TEXT_LIGHT': "#94a3b8",
        'ACCENT': "#60a5fa", 'WHITE': "#ffffff", 'DIVIDER': "#334155", 'BORDER': "#475569"
    }
    
    theme = [LIGHT_THEME]
    def get_color(key):
        return theme[0][key]
    
    # ⚠️ PASTE YOUR API KEY HERE ⚠️
    OPENAI_API_KEY = ""
 # Please paste your actual key here
    
    if OPENAI_API_KEY == "YOUR_API_KEY_HERE":
        print("="*80)
        print("⚠️ WARNING: OPENAI_API_KEY is not set.")
        print("Please paste your API key into the `OPENAI_API_KEY` variable.")
        print("="*80)

    event_reader = EventLogReader()
    ai_explainer = AIExplainer(OPENAI_API_KEY)
    ai_assistant = AIAssistant(OPENAI_API_KEY)
    current_events = [] 
    
    chat_history = []
    
    filter_state = {'start_date': None, 'end_date': None}
    
    hide_common_checkbox = Checkbox(label="Hide common events", value=True, check_color=get_color('WHITE'), fill_color=get_color('PRIMARY'))

    def show_splash():
        splash_content = Container(
            content=Column([
                Icon(Icons.ANALYTICS_ROUNDED, size=90, color="#4f46e5"),
                Container(height=20),
                Text("Event Monitor Pro", size=42, weight=FontWeight.BOLD, color="#0f172a"),
                Container(height=5),
                Text("AI-Powered System Intelligence", size=15, color="#64748b"),
                Container(height=40),
                ProgressBar(width=350, color="#4f46e5", height=3),
                Container(height=15),
                Text("Initializing AI Engine...", size=13, color="#64748b"),
                Container(height=30),
                Row([
                    Container(content=Text("Realtime", size=11, color="#ffffff"), bgcolor="#10b981", padding=10, border_radius=20),
                    Container(content=Text("Auto-Loading", size=11, color="#ffffff"), bgcolor="#3b82f6", padding=10, border_radius=20),
                    Container(content=Text("GPT-4o-mini", size=11, color="#ffffff"), bgcolor="#8b5cf6", padding=10, border_radius=20),
                ], spacing=10, alignment=MainAxisAlignment.CENTER)
            ], horizontal_alignment=CrossAxisAlignment.CENTER, spacing=0),
            padding=60,
            bgcolor="#ffffff",
            border_radius=24
        )
        
        page.add(Container(content=splash_content, expand=True, bgcolor="#f8fafc", alignment=ft.alignment.center))
        page.update()
        time.sleep(2)
        page.clean()
    
    show_splash()
    
    stats_total = Text("0", size=36, weight=FontWeight.BOLD, color=get_color('TEXT'))
    stats_errors = Text("0", size=36, weight=FontWeight.BOLD, color=get_color('ERROR'))
    stats_warnings = Text("0", size=36, weight=FontWeight.BOLD, color=get_color('WARNING'))
    stats_info = Text("0", size=36, weight=FontWeight.BOLD, color=get_color('SUCCESS'))
    
    def create_stat_card(icon, label, value_text, color, description):
        return Container(
            content=Column([
                Row([
                    Container(content=Icon(icon, size=28, color=color), bgcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.1)", border_radius=10, padding=10),
                    Container(width=12),
                    Column([value_text, Text(label, size=13, weight=FontWeight.W_600, color=get_color('TEXT')), Text(description, size=11, color=get_color('TEXT_LIGHT'))], spacing=2)
                ], alignment=MainAxisAlignment.START, vertical_alignment=CrossAxisAlignment.CENTER)
            ]),
            bgcolor=get_color('CARD'),
            padding=20,
            border_radius=16,
            border=border.all(1, get_color('BORDER')),
            expand=True
        )
    
    theme_toggle = IconButton(icon=Icons.DARK_MODE_OUTLINED if not is_dark_mode[0] else Icons.LIGHT_MODE_OUTLINED, icon_color=get_color('TEXT_LIGHT'), tooltip="Toggle Theme", on_click=lambda e: toggle_theme())
    
    def toggle_theme():
        is_dark_mode[0] = not is_dark_mode[0]
        theme[0] = DARK_THEME if is_dark_mode[0] else LIGHT_THEME
        page.theme_mode = ThemeMode.DARK if is_dark_mode[0] else ThemeMode.LIGHT
        page.bgcolor = get_color('BG')
        theme_toggle.icon = Icons.LIGHT_MODE_OUTLINED if is_dark_mode[0] else Icons.DARK_MODE_OUTLINED
        page.clean()
        build_ui()
        page.update()
    
    def build_ui():
        nonlocal hide_common_checkbox 
        
        header = Container(
            content=Row([
                Row([
                    Icon(Icons.ANALYTICS_ROUNDED, size=32, color=get_color('PRIMARY')),
                    Container(width=12),
                    Column([Text("Event Monitor Pro", size=24, weight=FontWeight.BOLD, color=get_color('TEXT')), Text("AI-Powered System Intelligence", size=12, color=get_color('TEXT_LIGHT'))], spacing=2)
                ]),
                Row([
                    Container(content=Row([Container(content=Container(width=6, height=6, bgcolor="#10b981", border_radius=3)), Text("AI Active", size=12, color=get_color('TEXT'), weight=FontWeight.W_500)], spacing=8), bgcolor=f"rgba({int(get_color('SUCCESS')[1:3],16)},{int(get_color('SUCCESS')[3:5],16)},{int(get_color('SUCCESS')[5:7],16)},0.1)", padding=padding.symmetric(horizontal=14, vertical=8), border_radius=8),
                    Container(width=10),
                    theme_toggle
                ], spacing=10)
            ], alignment=MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=get_color('CARD'),
            padding=padding.symmetric(horizontal=40, vertical=20),
            border=border.only(bottom=border.BorderSide(1, get_color('BORDER')))
        )
        
        stats_row = Container(
            content=Row([
                create_stat_card(Icons.ANALYTICS_OUTLINED, "Total Events", stats_total, get_color('ACCENT'), "All events"),
                create_stat_card(Icons.ERROR_OUTLINE, "Errors", stats_errors, get_color('ERROR'), "Critical issues"),
                create_stat_card(Icons.WARNING_AMBER_OUTLINED, "Warnings", stats_warnings, get_color('WARNING'), "Potential issues"),
                create_stat_card(Icons.INFO_OUTLINE, "Information", stats_info, get_color('SUCCESS'), "Normal activity")
            ], spacing=16),
            padding=padding.symmetric(horizontal=40, vertical=24)
        )

        event_list = Column([], spacing=10, scroll=ScrollMode.AUTO, expand=True)
        
        start_date_field = TextField(label="Start Date", hint_text="Select", read_only=True, width=130, border_radius=8, filled=True, dense=True, bgcolor=get_color('BG'), suffix_icon=Icons.CALENDAR_TODAY_OUTLINED)
        start_time_field = TextField(label="Start Time", hint_text="9am", width=110, border_radius=8, filled=True, dense=True, bgcolor=get_color('BG'))
        end_date_field = TextField(label="End Date", hint_text="Select", read_only=True, width=130, border_radius=8, filled=True, dense=True, bgcolor=get_color('BG'), suffix_icon=Icons.CALENDAR_TODAY_OUTLINED)
        end_time_field = TextField(label="End Time", hint_text="5pm", width=110, border_radius=8, filled=True, dense=True, bgcolor=get_color('BG'))
        
        hide_common_checkbox.check_color = get_color('WHITE')
        hide_common_checkbox.fill_color = get_color('PRIMARY')
        
        def handle_start_date_change(e):
            if e.control.value:
                filter_state['start_date'] = e.control.value
                start_date_field.value = e.control.value.strftime("%d/%m/%Y")
                print(f"✅ Start date: {e.control.value}")
                page.update()
        
        def handle_end_date_change(e):
            if e.control.value:
                filter_state['end_date'] = e.control.value
                end_date_field.value = e.control.value.strftime("%d/%m/%Y")
                print(f"✅ End date: {e.control.value}")
                page.update()
        
        start_date_picker = ft.DatePicker(first_date=datetime.datetime(2000, 1, 1), last_date=datetime.datetime.now(), on_change=handle_start_date_change)
        end_date_picker = ft.DatePicker(first_date=datetime.datetime(2000, 1, 1), last_date=datetime.datetime.now(), on_change=handle_end_date_change)
        page.overlay.extend([start_date_picker, end_date_picker])
        start_date_field.on_click = lambda e: page.open(start_date_picker)
        end_date_field.on_click = lambda e: page.open(end_date_picker)
        
        def clear_filters(e):
            start_date_field.value = ""
            end_date_field.value = ""
            start_time_field.value = ""
            end_time_field.value = ""
            filter_state['start_date'] = None
            filter_state['end_date'] = None
            hide_common_checkbox.value = True
            page.update()
        
        clear_filter_btn = TextButton("Clear", icon=Icons.CLEAR, on_click=clear_filters)
        
        def create_event_card(event, explanation, idx):
            if explanation['severity'] == 'error':
                color = get_color('ERROR')
                bg = f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)"
            elif explanation['severity'] == 'warning':
                color = get_color('WARNING')
                bg = f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)"
            else:
                color = get_color('SUCCESS')
                bg = f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)"
            
            try:
                dt = datetime.datetime.strptime(event['time_generated'], '%m/%d/%y %H:%M:%S')
                time_str = dt.strftime('%I:%M %p')
                date_str = dt.strftime('%b %d, %Y')
            except:
                time_str = event['time_generated']
                date_str = ""
            
            is_expanded = [False]
            header_row = Row([
                Container(content=Text(explanation['icon'], size=24), width=50, height=50, bgcolor=bg, border_radius=10, alignment=ft.alignment.center),
                Container(width=12),
                Column([Text(explanation['title'], size=14, weight=FontWeight.W_600, color=get_color('TEXT')), Text(explanation['simple'], size=12, color=get_color('TEXT_LIGHT'), max_lines=1), Text(f"{time_str} • {date_str}", size=11, color=get_color('TEXT_LIGHT'))], spacing=3, expand=True),
                Icon(Icons.KEYBOARD_ARROW_DOWN_ROUNDED, size=20, color=get_color('TEXT_LIGHT'))
            ], alignment=MainAxisAlignment.START, vertical_alignment=CrossAxisAlignment.CENTER)
            
            details_section = Container(visible=False, content=Column([
                Divider(height=1, color=get_color('DIVIDER')), Container(height=12),
                Text("📌 Summary", size=13, weight=FontWeight.BOLD, color=get_color('TEXT')), Container(height=6),
                Container(content=Text(explanation['simple'], size=12, color=get_color('TEXT'), selectable=True), bgcolor=get_color('BG'), padding=12, border_radius=8), Container(height=12),
                Text("📖 Details", size=13, weight=FontWeight.BOLD, color=get_color('TEXT')), Container(height=6),
                Text(explanation['detail'], size=12, color=get_color('TEXT_LIGHT'), selectable=True), Container(height=12),
                Text("🔧 Technical", size=13, weight=FontWeight.BOLD, color=get_color('TEXT')), Container(height=6),
                Container(content=Text(explanation.get('technical', ''), size=12, color=get_color('TEXT'), selectable=True), bgcolor=get_color('BG'), padding=12, border_radius=8), Container(height=12),
                Text("✅ Actions", size=13, weight=FontWeight.BOLD, color=get_color('TEXT')), Container(height=6),
                Container(content=Text(explanation['action'], size=12, color=get_color('TEXT'), selectable=True), bgcolor=f"rgba({int(get_color('SUCCESS')[1:3],16)},{int(get_color('SUCCESS')[3:5],16)},{int(get_color('SUCCESS')[5:7],16)},0.1)", padding=12, border_radius=8),
                Container(height=12),
                Text("📋 Raw Message", size=13, weight=FontWeight.BOLD, color=get_color('TEXT')), Container(height=6),
                Container(content=Text(event['message'], size=12, color=get_color('TEXT_LIGHT'), selectable=True), bgcolor=get_color('BG'), padding=12, border_radius=8),
            ], spacing=0), padding=padding.only(top=12))
            
            card_column = Column([header_row, details_section], spacing=0)
            card_container = Container(content=card_column, bgcolor=get_color('CARD'), padding=16, border_radius=12, border=border.all(1, get_color('BORDER')))
            
            def toggle_expand(e):
                is_expanded[0] = not is_expanded[0]
                details_section.visible = is_expanded[0]
                header_row.controls[3] = Icon(Icons.KEYBOARD_ARROW_UP_ROUNDED if is_expanded[0] else Icons.KEYBOARD_ARROW_DOWN_ROUNDED, size=20, color=get_color('TEXT_LIGHT'))
                page.update()
            
            card_container.on_click = toggle_expand
            return card_container

        def update_stats():
            if not current_events:
                stats_total.value = stats_errors.value = stats_warnings.value = stats_info.value = "0"
            else:
                counts = Counter(e['event_type'] for e in current_events)
                stats_total.value = str(len(current_events))
                stats_errors.value = str(counts.get('Error', 0))
                stats_warnings.value = str(counts.get('Warning', 0))
                stats_info.value = str(counts.get('Information', 0))
            page.update()

        def load_events(e):
            dialog = AlertDialog(
                title=Row([ProgressRing(width=20, height=20, stroke_width=2, color=get_color('PRIMARY')), Text("Loading", weight=FontWeight.W_600)], spacing=12),
                content=Text("Fetching and analyzing events...", color=get_color('TEXT_LIGHT'), size=13),
                modal=True
            )
            page.dialog = dialog
            dialog.open = True
            page.update()
            
            def load_bg():
                try:
                    if OPENAI_API_KEY == "YOUR_API_KEY_HERE":
                        raise Exception("OpenAI API key is not set. Please add it to the code.")
                    
                    log_type = log_dropdown.value
                    max_records = int(records_field.value)
                    hide_common = hide_common_checkbox.value
                    
                    start_datetime = None
                    end_datetime = None
                    
                    if filter_state['start_date']:
                        start_time = parse_time_input(start_time_field.value)
                        start_hour, start_minute = start_time if start_time else (0, 0)
                        start_datetime = datetime.datetime.combine(filter_state['start_date'], datetime.time(start_hour, start_minute, 0))
                        print(f"\n📅 START FILTER: {start_datetime}")
                    
                    if filter_state['end_date']:
                        end_time = parse_time_input(end_time_field.value)
                        end_hour, end_minute = end_time if end_time else (23, 59)
                        end_datetime = datetime.datetime.combine(filter_state['end_date'], datetime.time(end_hour, end_minute, 59))
                        print(f"📅 END FILTER: {end_datetime}\n")
                    
                    events = event_reader.read_events(log_type, max_records, start_datetime, end_datetime, hide_common, keywords=None)
                    
                    current_events.clear()
                    current_events.extend(events)
                    
                    event_list.controls.clear()
                    
                    if not events:
                        event_list.controls.append(Container(content=Row([Icon(Icons.INFO_OUTLINE, color=get_color('TEXT_LIGHT')), Container(width=12), Text("No events found matching your criteria.", size=13, color=get_color('TEXT_LIGHT'))]), bgcolor=get_color('CARD'), padding=24, border_radius=12, border=border.all(1, get_color('BORDER'))))
                    else:
                        for idx, evt in enumerate(events):
                            placeholder = Container(content=Row([ProgressRing(width=24, height=24, stroke_width=2, color=get_color('PRIMARY')), Container(width=12), Text("AI analyzing...", size=12, color=get_color('TEXT_LIGHT'))]), bgcolor=get_color('CARD'), padding=16, border_radius=12, border=border.all(1, get_color('BORDER')))
                            event_list.controls.append(placeholder)
                        page.update()
                        
                        for idx, evt in enumerate(events):
                            explanation = ai_explainer.explain_event(evt['event_id'], evt['event_type'], evt['source'], evt['message'])
                            event_list.controls[idx] = create_event_card(evt, explanation, idx)
                            if idx % 5 == 0:
                                page.update()
                    
                    update_stats()
                    dialog.open = False
                    page.snack_bar = SnackBar(content=Row([Icon(Icons.CHECK_CIRCLE, color="#ffffff", size=20), Text(f"Loaded {len(events)} events", color="#ffffff")], spacing=8), bgcolor=get_color('SUCCESS'))
                    page.snack_bar.open = True
                    page.update()
                except Exception as ex:
                    import traceback
                    traceback.print_exc()
                    dialog.open = False
                    page.snack_bar = SnackBar(content=Row([Icon(Icons.ERROR, color="#ffffff", size=20), Text(f"Error: {str(ex)}", color="#ffffff")], spacing=8), bgcolor=get_color('ERROR'))
                    page.snack_bar.open = True
                    page.update()
            
            threading.Thread(target=load_bg, daemon=True).start()
        
        log_dropdown = Dropdown(label="Log Type", options=[dropdown.Option(t) for t in ["System", "Application", "Security"]], value="System", width=130, border_radius=8, filled=True, dense=True, bgcolor=get_color('BG'))
        records_field = TextField(label="Max Events", value="10", width=100, border_radius=8, filled=True, dense=True, bgcolor=get_color('BG'), keyboard_type=ft.KeyboardType.NUMBER)
        load_btn = ElevatedButton("Load & Analyze", icon=Icons.REFRESH_ROUNDED, on_click=load_events, bgcolor=get_color('PRIMARY'), color=get_color('WHITE'), height=40)
        
        events_tab = Container(
            content=Column([
                Container(content=Column([Text("Event Controls", size=16, weight=FontWeight.W_600, color=get_color('TEXT')), Container(height=16), Row([log_dropdown, records_field, start_date_field, start_time_field, end_date_field, end_time_field, clear_filter_btn, load_btn], spacing=10, wrap=True), Container(height=12), hide_common_checkbox]), bgcolor=get_color('CARD'), padding=24, border_radius=12, border=border.all(1, get_color('BORDER'))),
                Container(height=20),
                Container(content=Column([Row([Text("Recent Events", size=16, weight=FontWeight.W_600, color=get_color('TEXT'))]), Container(height=16), event_list]), bgcolor=get_color('CARD'), padding=24, border_radius=12, border=border.all(1, get_color('BORDER')), expand=True)
            ], expand=True),
            padding=padding.symmetric(horizontal=40, vertical=24)
        )
        
        #
        # ==============================================================================
        # ⬇️ START OF AI CHAT (v25 "SPECIALIST" AGENT ORCHESTRATOR) ⬇️
        # ==============================================================================
        #
        
        chat_list = Column([], spacing=12, scroll=ScrollMode.AUTO, expand=True)
        chat_input = TextField(hint_text="Ask an investigative query...", multiline=False, expand=True, border_radius=8, filled=True, dense=True, bgcolor=get_color('BG'))
        
        def create_chat_bubble(msg, is_user=True):
            if is_user:
                return Container(content=Text(msg, size=13, color=get_color('WHITE'), selectable=True), bgcolor=get_color('PRIMARY'), padding=12, border_radius=border_radius.only(12, 12, 2, 12), margin=margin.only(left=80))

            return Container(content=ft.Markdown(msg, selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB), bgcolor=get_color('BG'), padding=12, border_radius=border_radius.only(12, 12, 12, 2), margin=margin.only(right=80), border=border.all(1, get_color('BORDER')))
        
        def send_message(e):
            nonlocal chat_history
            msg = chat_input.value.strip()
            if not msg:
                return
            
            chat_list.controls.append(create_chat_bubble(msg, True))
            chat_history.append({"role": "user", "content": msg})
            chat_input.value = ""
            chat_input.disabled = True
            
            page.update()
            
            history_copy = list(chat_history[-10:])
            threading.Thread(target=get_smart_response, args=(history_copy,), daemon=True).start()
        
        def get_smart_response(history_copy):
            nonlocal chat_history
            
            status_text = Text(
                "⚙️ Thinking...", 
                size=13, 
                color=get_color('TEXT'), 
                italic=True
            )
            
            status_bubble = Container(
                content=Row(
                    [
                        ProgressRing(width=16, height=16, stroke_width=2, color=get_color('PRIMARY')), 
                        status_text
                    ], 
                    spacing=12
                ), 
                bgcolor=get_color('BG'), 
                padding=12, 
                border_radius=border_radius.only(12, 12, 12, 2), 
                margin=margin.only(right=80), 
                border=border.all(1, get_color('BORDER'))
            )
            
            try:
                chat_list.controls.append(status_bubble)
                page.update()
                
                if OPENAI_API_KEY == "YOUR_API_KEY_HERE":
                    raise Exception("OpenAI API key is not set.")

                # --- Step 1: Get the AI's plan (Chat, Search, Hybrid, or Uptime) ---
                plan = ai_assistant.get_ai_plan(history_copy)
                
                # --- Step 2: Execute the plan ---
                
                if plan.get("action") == "chat":
                    # --- ACTION: CHAT ---
                    status_text.value = "💬 Generating response..."
                    page.update()
                    response_text = plan.get("response", "I'm not sure how to respond to that.")
                    
                elif plan.get("action") == "get_boot_time":
                    # --- ACTION: GET BOOT TIME ---
                    status_text.value = "⏱️ Checking system boot time..."
                    page.update()
                    response_text = get_system_boot_time()
                

                elif plan.get("action") == "get_process_stats":
                    # --- ACTION: GET SPECIFIC PROCESS STATS (v23) ---
                    params = plan.get("params", {})
                    process_name = params.get("process_name")
                    
                    if not process_name:
                        response_text = "⚠️ AI Error: The AI plan wanted to check a process, but didn't specify which one. Please try rephrasing your query."
                    else:
                        status_text.value = f"🔎 Checking stats for processes matching '{process_name}'..."
                        page.update()
                        response_text = get_specific_process_stats(process_name)
                
                # ==========================================================
                # ⬇️ ADDED THIS NEW BLOCK (v25) ⬇️
                # ==========================================================
                elif plan.get("action") == "check_major_apps":
                    # --- ACTION: GET MAJOR APPS OVERVIEW (v25) ---
                    status_text.value = "📊 Scanning for major applications..."
                    page.update()
                    response_text = get_major_apps_overview()
                # ==========================================================
                # ⬆️ END OF NEW BLOCK (v25) ⬆️
                # ==========================================================
                # ✅ ACTION: PORT ANALYSIS (v26)
                elif plan.get("action") == "port_analysis":
                    params = plan.get("params", {})

                    port = params.get("port")
                    process = params.get("process_name")

                    status_text.value = "🌐 Analyzing network ports..."
                    page.update()

                    if port:
                        data = find_processes_on_port(port)
                        if not data:
                            response_text = f"No application is using port **{port}**."
                        else:
                            response_text = f"""
                **Port {port} Analysis**
                ✅ Process: **{data['process_name']}**
                ✅ PID: **{data['pid']}**
                ✅ Status: **{data['status']}**
                """
                    elif process:
                        data = find_ports_for_process(process)
                        if not data:
                            response_text = f"Process **{process}** is not using any ports."
                        else:
                            response_text = f"**{process} Port Usage:**\n"
                            for p, info in data.items():
                                response_text += f"- Port **{p}** → PID {info['pid']} ({info['status']})\n"
                    else:
                        full_map = get_port_process_mapping()
                        lines = []
                        for p, info in full_map.items():
                            lines.append(f"- Port **{p}** → {info['process_name']} (PID {info['pid']}, {info['status']})")
                        response_text = "**All Active Ports:**\n" + "\n".join(lines)

                elif plan.get("action") == "search_logs":
                    # --- ACTION: SEARCH LOGS (Past-tense) ---
                    params = plan.get("params", {})
                    status_text.value = f"🔍 Searching {params.get('log_type', 'System')} logs..."
                    page.update()
                    
                    log_type = params.get('log_type', 'System')
                    keywords = params.get('search_keywords', [])
                    analysis_request = params.get('analysis_request', "Analyze the user's query.")
                    event_type_filter = params.get('event_type_filter')

                    is_last_event_query = params.get("find_most_recent", False)
                    max_records_to_fetch = 5 if is_last_event_query else 500
                    
                    # --- v21 DATETIME FIX ---
                    start_datetime, end_datetime = None, None
                    try:
                        if params.get('start_date'):
                            start_date = datetime.datetime.strptime(params['start_date'], '%Y-%m-%d').date()
                            start_time = datetime.datetime.strptime(params.get('start_time', '00:00'), '%H:%M').time()
                            start_datetime = datetime.datetime.combine(start_date, start_time)
                        
                        if params.get('end_date'):
                            end_date = datetime.datetime.strptime(params['end_date'], '%Y-%m-%d').date()
                            end_time = datetime.datetime.strptime(params.get('end_time', '23:59'), '%H:%M').time()
                            end_datetime = datetime.datetime.combine(end_date, end_time)
                    except Exception as e:
                        print(f"Error parsing AI-generated dates: {e}")
                        start_datetime, end_datetime = None, None

                    events_to_analyze = event_reader.read_events(
                        log_type, max_records=max_records_to_fetch,
                        start_datetime=start_datetime, end_datetime=end_datetime,
                        hide_common=False, keywords=keywords, event_type_filter=event_type_filter
                    )
                    
                    current_events.clear()
                    current_events.extend(events_to_analyze)
                    update_stats()

                    status_text.value = f"🧠 Analyzing {len(events_to_analyze)} found events..."
                    page.update()
                    
                    if not events_to_analyze:
                        response_text = (
                            "I searched the logs based on your query but found **0 events** matching those criteria.\n\n"
                            "This could mean no relevant events were logged, or the time range is incorrect. You could try broadening your search."
                        )
                    else:
                        response_text = ai_assistant.analyze_results(analysis_request, events_to_analyze)

                elif plan.get("action") == "hybrid_analysis":
                    # --- ACTION: HYBRID ANALYSIS (Present-tense) ---
                    params = plan.get("params", {})
                    analysis_request = plan.get('analysis_request', "Analyze real-time system issues.")
                    
                    # Step 1: Get "Task Manager" stats
                    status_text.value = "🔬 Checking real-time stats (Task Manager)..."
                    page.update()
                    realtime_data = get_realtime_system_stats()
                    
                    # Step 2: Get recent logs
                    status_text.value = "🔍 Correlating with recent event logs..."
                    page.update()
                    
                    log_type = params.get('log_type', 'Application')
                    keywords = params.get('search_keywords', [])
                    event_type_filter = params.get('event_type_filter')
                    
                    # --- v21 DATETIME FIX ---
                    start_datetime, end_datetime = None, None
                    try:
                        if params.get('start_date'):
                            start_date = datetime.datetime.strptime(params['start_date'], '%Y-%m-%d').date()
                            start_time = datetime.datetime.strptime(params.get('start_time', '00:00'), '%H:%M').time()
                            start_datetime = datetime.datetime.combine(start_date, start_time)
                        
                        if params.get('end_date'):
                            end_date = datetime.datetime.strptime(params['end_date'], '%Y-%m-%d').date()
                            end_time = datetime.datetime.strptime(params.get('end_time', '23:59'), '%H:%M').time()
                            end_datetime = datetime.datetime.combine(end_date, end_time)
                    except Exception as e:
                        print(f"Error parsing AI-generated dates: {e}")
                        # Default to today for hybrid analysis if parsing fails
                        start_datetime = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
                        end_datetime = datetime.datetime.combine(datetime.date.today(), datetime.time.max)


                    events_to_analyze = event_reader.read_events(
                        log_type, max_records=100,
                        start_datetime=start_datetime, end_datetime=end_datetime,
                        hide_common=False, keywords=keywords, event_type_filter=event_type_filter
                    )
                    
                    current_events.clear()
                    current_events.extend(events_to_analyze)
                    update_stats()

                    # Step 3: Synthesize both
                    status_text.value = f"🧠 Synthesizing real-time and historical data..."
                    page.update()
                    
                    response_text = ai_assistant.analyze_hybrid_results(
                        analysis_request,
                        realtime_data,
                        events_to_analyze
                    )
                
                else:
                    raise Exception(f"Unknown AI action: {plan.get('action')}")

                # --- Final Step: Show response and update history ---
                chat_list.controls.remove(status_bubble)
                chat_list.controls.append(create_chat_bubble(response_text, False))
                chat_history.append({"role": "assistant", "content": response_text})
                chat_input.disabled = False
                page.update()

            except Exception as ex:
                import traceback
                traceback.print_exc()
                if 'status_bubble' in locals() and status_bubble in chat_list.controls:
                    chat_list.controls.remove(status_bubble)
                
                error_message = f"An error occurred: {str(ex)}"
                chat_list.controls.append(create_chat_bubble(error_message, False))
                chat_history.append({"role": "assistant", "content": error_message})
                chat_input.disabled = False
                page.update()
        
        chat_input.on_submit = send_message
        send_btn = IconButton(icon=Icons.SEND_ROUNDED, bgcolor=get_color('PRIMARY'), icon_color=get_color('WHITE'), on_click=send_message, width=40, height=40)
        
        # --- Enhanced Welcome Message (v25) ---
        chat_list.controls.clear() 
        chat_history.clear()
        
        
        
        ai_tab = Container(content=Column([Container(content=chat_list, bgcolor=get_color('CARD'), padding=20, border_radius=12, border=border.all(1, get_color('BORDER')) , expand=True), Container(height=16), Row([chat_input, send_btn], spacing=10)], expand=True), padding=padding.symmetric(horizontal=40, vertical=24))
        
        #
        # ==============================================================================
        # ⬆️ END OF AI CHAT FIX ⬆️
        # ==============================================================================
        #
        
        cpu_bar = ProgressBar(value=0, color=get_color('PRIMARY'), height=8, border_radius=4)
        ram_bar = ProgressBar(value=0, color=get_color('SUCCESS'), height=8, border_radius=4)
        disk_bar = ProgressBar(value=0, color=get_color('WARNING'), height=8, border_radius=4)
        cpu_txt = Text("0%", size=32, weight=FontWeight.BOLD, color=get_color('TEXT'))
        ram_txt = Text("0%", size=32, weight=FontWeight.BOLD, color=get_color('TEXT'))
        disk_txt = Text("0%", size=32, weight=FontWeight.BOLD, color=get_color('TEXT'))
        
        def update_monitor():
            while True:
                try:
                    cpu = psutil.cpu_percent(interval=1)
                    ram = psutil.virtual_memory().percent
                    disk = psutil.disk_usage('/').percent
                    cpu_bar.value = cpu / 100
                    ram_bar.value = ram / 100
                    disk_bar.value = disk / 100
                    cpu_txt.value = f"{cpu:.1f}%"
                    ram_txt.value = f"{ram:.1f}%"
                    disk_txt.value = f"{disk:.1f}%"
                    page.update()
                    time.sleep(2)
                except:
                    pass
        
        threading.Thread(target=update_monitor, daemon=True).start()
        
        def create_monitor_card(icon, color, title, value_txt, progress_bar):
            return Container(content=Column([Row([Icon(icon, size=32, color=color), Container(width=16), Column([Text(title, size=14, color=get_color('TEXT_LIGHT')), value_txt], spacing=4, expand=True)]), Container(height=16), progress_bar]), bgcolor=get_color('CARD'), padding=28, border_radius=12, border=border.all(1, get_color('BORDER')))
        
        monitor_tab = Container(content=Column([Text("System Performance", size=20, weight=FontWeight.BOLD, color=get_color('TEXT')), Container(height=24), create_monitor_card(Icons.MEMORY_OUTLINED, get_color('PRIMARY'), "CPU", cpu_txt, cpu_bar), Container(height=20), create_monitor_card(Icons.STORAGE_OUTLINED, get_color('SUCCESS'), "Memory", ram_txt, ram_bar), Container(height=20), create_monitor_card(Icons.SAVE_OUTLINED, get_color('WARNING'), "Disk", disk_txt, disk_bar)], scroll=ScrollMode.AUTO, expand=True), padding=padding.symmetric(horizontal=40, vertical=24))
        
        tabs = Tabs(selected_index=0, animation_duration=250, indicator_color=get_color('PRIMARY'), label_color=get_color('PRIMARY'), unselected_label_color=get_color('TEXT_LIGHT'), tabs=[Tab(text="Events", icon=Icons.LIST_ALT_OUTLINED, content=events_tab), Tab(text="AI Assistant", icon=Icons.SMART_TOY_OUTLINED, content=ai_tab), Tab(text="Monitor", icon=Icons.MONITOR_HEART_OUTLINED, content=monitor_tab)], expand=True)
        
        page.add(Column([header, stats_row, tabs], spacing=0, expand=True))
        page.bgcolor = get_color('BG')
    
    build_ui()

if __name__ == "__main__":
    ft.app(target=main)