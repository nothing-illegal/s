#!/usr/bin/env python3
"""
Motion-triggered restart via webhook, for use with a cheap commercial motion
sensor (Wyze, SwitchBot, Aqara, Govee, etc.) through IFTTT or Home Assistant.

How the pieces fit together:
    [cheap motion sensor] -> [its app's automation: IFTTT or Home Assistant]
        -> HTTP POST to this script, running on your Mac -> restarts the Mac

Setup:
    pip install flask

    # Passwordless restart (required, since this runs unattended):
    #   sudo visudo
    #   add this line (replace "yourname" with `whoami`):
    #   yourname ALL=(root) NOPASSWD: /sbin/shutdown

Usage:
    python motion_webhook.py --token mySecretToken123
    python motion_webhook.py --token mySecretToken123 --port 8765 --cooldown 120
    python motion_webhook.py --token mySecretToken123 --dry-run   # test without restarting

Trigger it manually to test:
    curl -X POST http://localhost:8765/motion -H "X-Auth-Token: mySecretToken123"
"""
import argparse
import datetime
import subprocess
import time

from flask import Flask, request, jsonify

app = Flask(__name__)
state = {"last_trigger": 0.0, "token": "", "cooldown": 60, "dry_run": False}


def log(msg):
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


@app.route("/motion", methods=["POST"])
def motion():
    token = request.headers.get("X-Auth-Token") or request.args.get("token")
    if token != state["token"]:
        log("Rejected request: bad/missing token")
        return jsonify({"status": "unauthorized"}), 401

    since_last = time.time() - state["last_trigger"]
    if since_last < state["cooldown"]:
        log(f"In cooldown ({int(state['cooldown'] - since_last)}s left), ignoring")
        return jsonify({"status": "cooldown"}), 200

    state["last_trigger"] = time.time()
    if state["dry_run"]:
        log("DRY RUN: motion trigger received, would restart now")
    else:
        log("Motion trigger received — restarting macOS now")
        subprocess.run(["sudo", "shutdown", "-r", "now"], check=False)
    return jsonify({"status": "ok"}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "listening"}), 200


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", required=True, help="shared secret the sensor automation must send")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--cooldown", type=int, default=60, help="seconds between accepted triggers")
    ap.add_argument("--dry-run", action="store_true", help="log triggers but never restart")
    args = ap.parse_args()

    state["token"] = args.token
    state["cooldown"] = args.cooldown
    state["dry_run"] = args.dry_run

    log(f"Listening on 0.0.0.0:{args.port} (dry_run={args.dry_run}, cooldown={args.cooldown}s)")
    log("Point your sensor automation at POST http://<this-mac-ip>:%d/motion" % args.port)
    app.run(host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
