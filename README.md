Event Monitor Pro is a full-featured desktop application built with Flet, Python, OpenAI, and Windows APIs.
It combines real-time system monitoring, intelligent event log analysis, and a GPT-powered assistant specialized in Windows diagnostics.

Designed for developers, system administrators, and power users who want deep visibility into Windows internals with an intuitive UI.


1. AI Event Log Explanation (Windows Expert Mode)
Reads System, Application, and Security logs using win32evtlog
Sends event details to GPT-4o-mini for:

Summary
Technical explanation
Root cause
System impact
Prevention steps
Returns clean & structured output with icons and severity levels

2. Real-time Task Manager View
CPU %, RAM usage, Disk usage
Top 10 CPU-heavy processes
Auto-refreshing performance dashboard

3. Uptime Analyzer
Shows:
Last system boot time
Total uptime
Days / hours breakdown

4. Smart NLU-Based Search Engine
User can ask questions like:
“When did Chrome last crash?”
“What happened last night?”
“PC is slow, check performance”
“Show last restart”
“Applicat on hang for VS Code”
The AI automatically chooses whether to:
Search logs
Run hybrid analysis
Check real-time performance
Do uptime check
Or just answer conversationally

5. Port Analyzer (Network Port Intelligence)

Supports:
“which app is using port 8080”
“on which port is mysql running”
“list all ports”
“visual studio code running on which port”
Using:
psutil.net_connections()
GPT-based process name extraction

Intelligent mapping to PID, status, and process_name
