#!/usr/bin/env python3
"""
Web server for phone sync via hotspot
"""

from flask import Flask, request, jsonify, render_template_string
import sqlite3
import datetime
from pathlib import Path
import threading
import socket
import netifaces
import qrcode
from io import BytesIO
import base64

class PushupWebServer:
    def __init__(self, db_path, port=8080):
        self.db_path = db_path
        self.port = port
        self.app = Flask(__name__)
        self.setup_routes()
        
    def get_local_ip(self):
        """Get laptop's IP address on hotspot"""
        try:
            # Try to find the hotspot interface (usually wlan0 or similar)
            interfaces = netifaces.interfaces()
            for interface in interfaces:
                if interface.startswith(('wlan', 'wl', 'en')):
                    addrs = netifaces.ifaddresses(interface)
                    if netifaces.AF_INET in addrs:
                        for addr in addrs[netifaces.AF_INET]:
                            ip = addr.get('addr')
                            if ip and ip.startswith('192.168.43.'):  # Typical hotspot subnet
                                return ip
            # Fallback: try socket method
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
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
        """Log pushups to database"""
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
        
    def generate_qr_code(self, url):
        """Generate QR code as base64 image"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        # HTML template for mobile web interface
        HTML_TEMPLATE = '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Pushup Logger</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                    max-width: 400px;
                    margin: 0 auto;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }
                .container {
                    background: white;
                    border-radius: 20px;
                    padding: 30px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    margin-top: 20px;
                }
                h1 {
                    color: #333;
                    text-align: center;
                    margin-bottom: 30px;
                }
                .total-display {
                    text-align: center;
                    font-size: 48px;
                    font-weight: bold;
                    color: #4CAF50;
                    margin: 20px 0;
                }
                .today-label {
                    text-align: center;
                    color: #666;
                    font-size: 18px;
                    margin-bottom: 30px;
                }
                .counter {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 20px;
                    margin: 30px 0;
                }
                .counter-btn {
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    border: none;
                    background: #4CAF50;
                    color: white;
                    font-size: 30px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .counter-btn:active {
                    transform: scale(0.95);
                }
                .counter-value {
                    font-size: 48px;
                    font-weight: bold;
                    min-width: 80px;
                    text-align: center;
                }
                .log-btn {
                    width: 100%;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    font-size: 20px;
                    font-weight: bold;
                    cursor: pointer;
                    margin-top: 20px;
                }
                .log-btn:active {
                    transform: scale(0.98);
                }
                .recent-logs {
                    margin-top: 30px;
                    border-top: 1px solid #eee;
                    padding-top: 20px;
                }
                .log-item {
                    display: flex;
                    justify-content: space-between;
                    padding: 10px 0;
                    border-bottom: 1px solid #f0f0f0;
                }
                .status {
                    text-align: center;
                    padding: 10px;
                    border-radius: 10px;
                    margin: 10px 0;
                    font-weight: bold;
                }
                .success { background: #d4edda; color: #155724; }
                .error { background: #f8d7da; color: #721c24; }
                .qrcode {
                    text-align: center;
                    margin: 20px 0;
                }
                .instructions {
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 10px;
                    margin: 20px 0;
                    font-size: 14px;
                    color: #666;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>💪 Pushup Logger</h1>
                
                <div class="today-label">Today's Total</div>
                <div class="total-display" id="todayTotal">0</div>
                
                <div class="counter">
                    <button class="counter-btn" onclick="changeCount(-1)">-</button>
                    <div class="counter-value" id="count">10</div>
                    <button class="counter-btn" onclick="changeCount(1)">+</button>
                </div>
                
                <button class="log-btn" onclick="logPushups()">LOG PUSHUPS</button>
                
                <div id="status"></div>
                
                <div class="recent-logs">
                    <h3>Recent Logs</h3>
                    <div id="recentLogs">Loading...</div>
                </div>
                
                <div class="instructions">
                    <strong>📱 How to use:</strong><br>
                    1. Keep this page open on your phone<br>
                    2. Log pushups anytime<br>
                    3. Data syncs to laptop automatically
                </div>
            </div>
            
            <script>
                let count = 10;
                let todayTotal = 0;
                
                function changeCount(change) {
                    count += change;
                    if (count < 0) count = 0;
                    if (count > 999) count = 999;
                    document.getElementById('count').textContent = count;
                }
                
                async function logPushups() {
                    try {
                        const response = await fetch('/api/log', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ count: count })
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            showStatus(`✅ Logged ${count} pushups!`, 'success');
                            updateTodayTotal();
                            updateRecentLogs();
                            // Reset to default value
                            count = 10;
                            document.getElementById('count').textContent = count;
                        } else {
                            showStatus('❌ Failed to log pushups', 'error');
                        }
                    } catch (error) {
                        showStatus('❌ Connection error', 'error');
                    }
                }
                
                async function updateTodayTotal() {
                    try {
                        const response = await fetch('/api/today');
                        const data = await response.json();
                        todayTotal = data.total;
                        document.getElementById('todayTotal').textContent = todayTotal;
                    } catch (error) {
                        console.error('Failed to update total:', error);
                    }
                }
                
                async function updateRecentLogs() {
                    try {
                        const response = await fetch('/api/recent');
                        const data = await response.json();
                        
                        let html = '';
                        data.logs.forEach(log => {
                            const time = new Date(log.timestamp).toLocaleTimeString([], { 
                                hour: '2-digit', 
                                minute: '2-digit' 
                            });
                            html += `
                                <div class="log-item">
                                    <span>${time}</span>
                                    <span><strong>${log.count}</strong> pushups</span>
                                </div>
                            `;
                        });
                        
                        document.getElementById('recentLogs').innerHTML = html || 'No logs yet';
                    } catch (error) {
                        console.error('Failed to update logs:', error);
                    }
                }
                
                function showStatus(message, type) {
                    const statusDiv = document.getElementById('status');
                    statusDiv.className = `status ${type}`;
                    statusDiv.textContent = message;
                    
                    setTimeout(() => {
                        statusDiv.textContent = '';
                        statusDiv.className = 'status';
                    }, 3000);
                }
                
                // Initial load
                updateTodayTotal();
                updateRecentLogs();
                
                // Auto-refresh every 30 seconds
                setInterval(updateTodayTotal, 30000);
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
        
        @self.app.route('/api/recent')
        def api_recent():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT count, timestamp FROM pushups WHERE date = date('now') ORDER BY timestamp DESC LIMIT 10"
            )
            logs = [{'count': row[0], 'timestamp': row[1]} for row in cursor.fetchall()]
            conn.close()
            return jsonify({'logs': logs})
        
        @self.app.route('/api/log', methods=['POST'])
        def api_log():
            try:
                data = request.get_json()
                count = int(data.get('count', 0))
                
                if count < 0 or count > 999:
                    return jsonify({'success': False, 'error': 'Invalid count'})
                
                self.log_pushups(count)
                return jsonify({'success': True, 'count': count})
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
    
    def run(self):
        """Run the Flask server"""
        ip = self.get_local_ip()
        print(f"🌐 Web server starting on http://{ip}:{self.port}")
        print(f"📱 Scan QR code from your phone to connect")
        self.app.run(host='0.0.0.0', port=self.port, debug=False, threaded=True)
    
    def start_in_thread(self):
        """Start server in a background thread"""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        return thread
