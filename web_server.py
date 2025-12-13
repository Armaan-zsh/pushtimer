#!/usr/bin/env python3
"""
Web server for phone sync via hotspot
"""

from flask import Flask, request, jsonify, render_template_string
import sqlite3
import datetime
import threading
import socket
import netifaces
import qrcode
from io import BytesIO
import base64
import logging

# Configure Flask logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class PushupWebServer:
    def __init__(self, db_path, port=8080):
        self.db_path = db_path
        self.port = port
        self.app = Flask(__name__)
        self.setup_routes()
        
    def get_local_ip(self):
        """Get best guess for local IP address"""
        try:
            # Method 1: Connect to an external server (most reliable if internet exists)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            # Method 2: Iterate interfaces
            try:
                interfaces = netifaces.interfaces()
                for interface in interfaces:
                    # Filter for likely candidates (wireless, ethernet)
                    if interface.startswith(('wlan', 'wl', 'en', 'eth')):
                        addrs = netifaces.ifaddresses(interface)
                        if netifaces.AF_INET in addrs:
                            for addr in addrs[netifaces.AF_INET]:
                                ip = addr.get('addr')
                                # Prefer standard private ranges
                                if ip and (ip.startswith('192.168.') or ip.startswith('10.')):
                                    return ip
            except:
                pass
            return "127.0.0.1"
    
    def get_today_total(self):
        """Get today's pushup total from database"""
        today = datetime.date.today().isoformat()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(count) FROM pushups WHERE date = ?", (today,))
        result = cursor.fetchone()[0]
        conn.close()
        return result or 0
    
    def log_pushups(self, count):
        """Log pushups to database (append mode)"""
        today = datetime.date.today().isoformat()
        now = datetime.datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pushups (date, count, timestamp) VALUES (?, ?, ?)",
            (today, count, now)
        )
        conn.commit()
        conn.close()

    def update_pushups_for_date(self, date_str, count):
        """Update/Overwrite pushups for a specific date"""
        # Note: This simplifies the data model by deleting all entries for that date
        # and inserting a single 'manual edit' entry.
        # This is destructive to strict timestamp logging but matches "Edit" intent best.
        
        now = datetime.datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Remove existing entries for this date
        cursor.execute("DELETE FROM pushups WHERE date = ?", (date_str,))
        
        # Insert new single entry
        cursor.execute(
            "INSERT INTO pushups (date, count, timestamp) VALUES (?, ?, ?)",
            (date_str, count, now)
        )
        conn.commit()
        conn.close()

    def get_history(self):
        """Get daily totals for history view"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT date, SUM(count) FROM pushups GROUP BY date ORDER BY date DESC LIMIT 30")
        data = [{'date': row[0], 'count': row[1] or 0} for row in cursor.fetchall()]
        conn.close()
        return data

    def setup_routes(self):
        """Setup Flask routes"""
        
        HTML_TEMPLATE = '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <title>Pushup Timer</title>
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
            <style>
                :root {
                    --bg: #0f1115;
                    --card-bg: #1a1d24;
                    --primary: #00ff88;
                    --primary-dim: rgba(0, 255, 136, 0.1);
                    --text: #ffffff;
                    --text-secondary: #8b9bb4;
                    --accent: #7000ff;
                }
                
                * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
                
                body {
                    background-color: var(--bg);
                    color: var(--text);
                    font-family: 'Outfit', sans-serif;
                    margin: 0;
                    padding: 0;
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                }

                .app-header {
                    padding: 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    background: rgba(15, 17, 21, 0.95);
                    backdrop-filter: blur(10px);
                    position: sticky;
                    top: 0;
                    z-index: 100;
                    border-bottom: 1px solid rgba(255,255,255,0.05);
                }

                .logo { font-weight: 800; font-size: 1.2rem; letter-spacing: -0.5px; }
                .logo span { color: var(--primary); }

                .nav-btn {
                    background: transparent;
                    border: none;
                    color: var(--text-secondary);
                    font-weight: 600;
                    font-size: 0.9rem;
                    cursor: pointer;
                    padding: 8px 12px;
                    border-radius: 8px;
                    transition: all 0.2s;
                }
                .nav-btn.active { background: var(--card-bg); color: var(--text); }

                main {
                    flex: 1;
                    padding: 20px;
                    max-width: 600px;
                    margin: 0 auto;
                    width: 100%;
                }

                /* Views */
                .view { display: none; animation: fadeIn 0.3s ease; }
                .view.active { display: block; }
                
                @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

                /* Dashboard */
                .stats-circle {
                    width: 260px;
                    height: 260px;
                    border-radius: 50%;
                    background: conic-gradient(var(--primary) var(--progress, 0%), var(--card-bg) 0);
                    margin: 40px auto;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    position: relative;
                    box-shadow: 0 0 30px rgba(0, 255, 136, 0.15);
                    transition: --progress 1s ease;
                }
                
                .stats-inner {
                    width: 240px;
                    height: 240px;
                    background: var(--bg);
                    border-radius: 50%;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                }

                .count-big { font-size: 4.5rem; font-weight: 800; line-height: 1; margin-bottom: 5px; }
                .label-dim { color: var(--text-secondary); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; }

                .controls {
                    display: grid;
                    grid-template-columns: 1fr 1.5fr 1fr;
                    gap: 15px;
                    align-items: center;
                    margin-top: 40px;
                }

                .btn-icon {
                    background: var(--card-bg);
                    border: none;
                    color: var(--text);
                    height: 60px;
                    border-radius: 16px;
                    font-size: 1.5rem;
                    cursor: pointer;
                    transition: transform 0.1s;
                }
                .btn-icon:active { transform: scale(0.95); }
                
                .btn-primary {
                    background: var(--primary);
                    color: #000;
                    height: 70px;
                    border-radius: 20px;
                    border: none;
                    font-weight: 800;
                    font-size: 1.1rem;
                    text-transform: uppercase;
                    box-shadow: 0 10px 20px rgba(0, 255, 136, 0.2);
                    cursor: pointer;
                }
                .btn-primary:active { transform: scale(0.98); }

                /* History List */
                .history-list { display: flex; flex-direction: column; gap: 12px; }
                
                .history-item {
                    background: var(--card-bg);
                    padding: 16px 20px;
                    border-radius: 16px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .date-col { display: flex; flex-direction: column; }
                .h-date { font-weight: 600; font-size: 1.1rem; }
                .h-ago { font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px; }
                
                .count-col { display: flex; align-items: center; gap: 15px; }
                .h-count { font-weight: 800; font-size: 1.3rem; color: var(--primary); }
                
                .edit-btn {
                    background: rgba(255,255,255,0.05);
                    border: none;
                    width: 36px;
                    height: 36px;
                    border-radius: 10px;
                    color: var(--text-secondary);
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                /* Modal */
                .modal-overlay {
                    position: fixed; inset: 0; background: rgba(0,0,0,0.8);
                    display: flex; align-items: center; justify-content: center;
                    opacity: 0; pointer-events: none; transition: opacity 0.2s;
                    z-index: 200;
                }
                .modal-overlay.open { opacity: 1; pointer-events: auto; }
                
                .modal {
                    background: var(--card-bg);
                    width: 90%; max-width: 320px;
                    padding: 25px; border-radius: 24px;
                    text-align: center;
                }
                
                .modal h3 { margin: 0 0 20px 0; }
                
                .input-group { margin-bottom: 20px; }
                input[type="number"], input[type="date"] {
                    width: 100%;
                    background: var(--bg);
                    border: 1px solid rgba(255,255,255,0.1);
                    padding: 15px;
                    border-radius: 12px;
                    color: white;
                    font-size: 1.2rem;
                    font-family: inherit;
                    text-align: center;
                    margin-bottom: 10px;
                }
                
                .modal-actions { display: flex; gap: 10px; }
                .modal-actions button { flex: 1; padding: 15px; border-radius: 12px; border: none; font-weight: 600; cursor: pointer; }
                .btn-cancel { background: rgba(255,255,255,0.1); color: white; }
                .btn-save { background: var(--primary); color: black; }

                /* Status Toast */
                .toast {
                    position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%) translateY(100px);
                    background: #fff; color: #000; padding: 12px 24px; border-radius: 50px;
                    font-weight: 600; opacity: 0; transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                }
                .toast.show { transform: translateX(-50%) translateY(0); opacity: 1; }
                .toast.error { background: #ff4757; color: white; }
            </style>
        </head>
        <body>
            <header class="app-header">
                <div class="logo">PUSH<span>TIMER</span></div>
                <nav>
                    <button class="nav-btn active" onclick="switchView('dashboard')">Timer</button>
                    <button class="nav-btn" onclick="switchView('history')">History</button>
                </nav>
            </header>

            <!-- Dashboard View -->
            <main id="dashboard" class="view active">
                <div class="stats-circle" id="progressRing">
                    <div class="stats-inner">
                        <div class="count-big" id="todayTotal">--</div>
                        <div class="label-dim">Today's Pushups</div>
                    </div>
                </div>

                <div class="controls">
                    <button class="btn-icon" onclick="adjustBuffer(-1)">-</button>
                    <button class="btn-primary" onclick="logBuffer()">
                        LOG <span id="bufferDisplay">10</span>
                    </button>
                    <button class="btn-icon" onclick="adjustBuffer(1)">+</button>
                </div>
            </main>

            <!-- History View -->
            <main id="history" class="view">
                <button class="log-btn" style="width:100%; margin-bottom:20px; background:var(--card-bg); border:1px dashed var(--text-secondary); color: var(--text-secondary); padding: 15px; border-radius: 12px; cursor: pointer;" onclick="openEditModal()">
                    + Add Missing Entry
                </button>
                <div class="history-list" id="historyList">
                    <!-- Items injected here -->
                </div>
            </main>

            <!-- Edit Modal -->
            <div class="modal-overlay" id="editModal">
                <div class="modal">
                    <h3 id="modalTitle">Edit Entry</h3>
                    <div class="input-group">
                        <input type="date" id="editDate" required>
                        <input type="number" id="editCount" placeholder="0" min="0">
                    </div>
                    <div class="modal-actions">
                        <button class="btn-cancel" onclick="closeEditModal()">Cancel</button>
                        <button class="btn-save" onclick="saveEdit()">Save</button>
                    </div>
                </div>
            </div>

            <div class="toast" id="toast">Saved!</div>

            <script>
                // State
                let buffer = 10;
                let todayTotal = 0;
                let currentView = 'dashboard';

                // Icons
                const icons = {
                    edit: '<svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z"/></svg>'
                };

                // Init
                document.addEventListener('DOMContentLoaded', () => {
                    refreshData();
                    // Set default date in modal to today
                    document.getElementById('editDate').valueAsDate = new Date();
                });

                // Navigation
                function switchView(viewName) {
                    document.querySelectorAll('.view').forEach(el => el.classList.remove('active'));
                    document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
                    
                    document.getElementById(viewName).classList.add('active');
                    // Find the button that triggered this or select by index
                    const btns = document.querySelectorAll('.nav-btn');
                    if(viewName === 'dashboard') btns[0].classList.add('active');
                    else btns[1].classList.add('active');
                    
                    if(viewName === 'history') loadHistory();
                }

                // Buffer Logic
                function adjustBuffer(delta) {
                    buffer += delta;
                    if(buffer < 1) buffer = 1;
                    document.getElementById('bufferDisplay').textContent = buffer;
                }

                async function logBuffer() {
                    try {
                        const res = await fetch('/api/log', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({count: buffer})
                        });
                        const data = await res.json();
                        if(data.success) {
                            showToast('Logged ' + buffer + ' pushups!');
                            refreshData();
                            buffer = 10; // Reset
                            document.getElementById('bufferDisplay').textContent = buffer;
                        }
                    } catch(e) {
                        showToast('Connection Failed', true);
                    }
                }

                // Data Fetching
                async function refreshData() {
                    const res = await fetch('/api/today');
                    const data = await res.json();
                    todayTotal = data.total;
                    document.getElementById('todayTotal').innerText = todayTotal;
                    
                    // Update ring (assuming goal of 100 for visual)
                    const percent = Math.min((todayTotal / 100) * 100, 100);
                    document.getElementById('progressRing').style.setProperty('--progress', percent + '%');
                }

                async function loadHistory() {
                    const res = await fetch('/api/history');
                    const data = await res.json();
                    const list = document.getElementById('historyList');
                    list.innerHTML = '';
                    
                    if(data.history.length === 0) {
                        list.innerHTML = '<div style="text-align:center; color:var(--text-secondary); padding:20px;">No logs yet</div>';
                        return;
                    }
                    
                    data.history.forEach(item => {
                        const el = document.createElement('div');
                        el.className = 'history-item';
                        // Format date nicely
                        const dateObj = new Date(item.date);
                        const dateStr = dateObj.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
                        
                        el.innerHTML = `
                            <div class="date-col">
                                <span class="h-date">${dateStr}</span>
                                <span class="h-ago">${item.date}</span>
                            </div>
                            <div class="count-col">
                                <span class="h-count">${item.count}</span>
                                <button class="edit-btn" onclick="openEditModal('${item.date}', ${item.count})">${icons.edit}</button>
                            </div>
                        `;
                        list.appendChild(el);
                    });
                }

                // Edit Modal
                function openEditModal(date = null, count = 0) {
                    const modal = document.getElementById('editModal');
                    const dateInput = document.getElementById('editDate');
                    const countInput = document.getElementById('editCount');
                    const title = document.getElementById('modalTitle');
                    
                    if(date) {
                        title.innerText = "Edit Entry";
                        dateInput.value = date;
                        countInput.value = count;
                    } else {
                        title.innerText = "Add Past Entry";
                        dateInput.valueAsDate = new Date();
                        countInput.value = "";
                    }
                    
                    modal.classList.add('open');
                }

                function closeEditModal() {
                    document.getElementById('editModal').classList.remove('open');
                }

                async function saveEdit() {
                    const date = document.getElementById('editDate').value;
                    const count = document.getElementById('editCount').value;
                    
                    if(!date || count === '') return;
                    
                    try {
                        const res = await fetch('/api/edit', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({date, count: parseInt(count)})
                        });
                        const data = await res.json();
                        
                        if(data.success) {
                            showToast('Record Updated');
                            closeEditModal();
                            loadHistory();
                            refreshData(); // Refresh today if we edited today
                        }
                    } catch(e) {
                        showToast('Error saving', true);
                    }
                }

                function showToast(msg, isError = false) {
                    const t = document.getElementById('toast');
                    t.innerText = msg;
                    t.className = isError ? 'toast show error' : 'toast show';
                    setTimeout(() => t.classList.remove('show'), 3000);
                }
            </script>
        </body>
        </html>
        '''
        
        @self.app.route('/')
        def index():
            return render_template_string(HTML_TEMPLATE)
        
        @self.app.route('/api/today')
        def api_today():
            total = self.get_today_total()
            return jsonify({'total': total})
        
        @self.app.route('/api/history')
        def api_history():
            history = self.get_history()
            return jsonify({'history': history})
        
        @self.app.route('/api/log', methods=['POST'])
        def api_log():
            try:
                data = request.get_json()
                count = int(data.get('count', 0))
                
                self.log_pushups(count)
                return jsonify({'success': True, 'count': count})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @self.app.route('/api/edit', methods=['POST'])
        def api_edit():
            try:
                data = request.get_json()
                date_str = data.get('date')
                try:
                    count = int(data.get('count', 0))
                except:
                    count = 0
                
                if not date_str or count < 0:
                    return jsonify({'success': False, 'error': 'Invalid data'})
                    
                self.update_pushups_for_date(date_str, count)
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
    
    def run(self):
        """Run the Flask server"""
        ip = self.get_local_ip()
        print(f"WEB_SERVER_STARTED_AT:http://{ip}:{self.port}")
        # Host=0.0.0.0 is CRITICAL for hotspot accessibility
        self.app.run(host='0.0.0.0', port=self.port, debug=False, threaded=True)
    
    def start_in_thread(self):
        """Start server in a background thread"""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        return thread

if __name__ == "__main__":
    # Standalone testing
    db_path = "test.db"
    server = PushupWebServer(db_path)
    server.run()
