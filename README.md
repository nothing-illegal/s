# motion-restart-mac

Restart a Mac automatically when a commercial motion sensor (Wyze,
SwitchBot, Aqara, Govee, etc.) detects motion at a doorway — e.g. restart
the moment you walk out the door.

The sensor doesn't talk to the Mac directly. Instead:

```
[motion sensor] --> [IFTTT or Home Assistant automation] --> POST /motion --> [this script] --> restarts the Mac
```

This repo contains a small local webhook listener (`motion_webhook.py`)
that triggers `shutdown -r now` when it receives an authenticated POST
request, plus a `launchd` job to keep it running in the background.

## Requirements

- macOS
- Python 3
- A motion sensor that supports **IFTTT** or **Home Assistant**
  (Wyze Sense, SwitchBot Motion Sensor, Aqara, Govee, etc. — typically $15–30)
- The Mac and the sensor's hub/app on the same Wi-Fi network while armed

## Install

```bash
git clone https://github.com/<you>/motion-restart-mac.git
cd motion-restart-mac
pip install -r requirements.txt
```

Allow passwordless restart, since this runs unattended with no one to type
a password:

```bash
sudo visudo
```

Add this line (replace `yourname` with the output of `whoami`):

```
yourname ALL=(root) NOPASSWD: /sbin/shutdown
```

## Test it (dry run — nothing actually restarts)

```bash
python motion_webhook.py --token mySecretToken123 --dry-run
```

In another terminal:

```bash
curl -X POST http://localhost:8765/motion -H "X-Auth-Token: mySecretToken123"
```

You should see a log line confirming the trigger was received. Once
confirmed, drop `--dry-run` and the same request will actually restart
the machine.

Find the Mac's local IP address (needed for the sensor automation):

```bash
ipconfig getifaddr en0
```

## Connect a sensor via IFTTT

1. Create an IFTTT account and link your sensor's service (Wyze, SwitchBot, etc.).
2. New Applet → **If** your sensor's "motion detected" trigger → **Then**
   Webhooks → "Make a web request":
   - URL: `http://<mac-ip>:8765/motion`
   - Method: `POST`
   - Content type: `application/json`
   - Header: `X-Auth-Token: mySecretToken123`

If your sensor doesn't support IFTTT, most cheap sensors integrate with
[Home Assistant](https://www.home-assistant.io/), which can call this same
webhook from an automation.

## Run automatically on login/boot

```bash
cp launchd/com.user.motionwebhook.plist ~/Library/LaunchAgents/
# edit that file first — see below
launchctl load ~/Library/LaunchAgents/com.user.motionwebhook.plist
```

Before copying it, edit `launchd/com.user.motionwebhook.plist`:

- Set the real path to `motion_webhook.py` on your machine
- Replace the placeholder token with your own long random string

Logs are written to `/tmp/motion_webhook.log` and `/tmp/motion_webhook.err`.

## Options

| Flag          | Default | Meaning                                      |
|---------------|---------|-----------------------------------------------|
| `--token`     | —       | required shared secret the automation must send |
| `--port`      | 8765    | port to listen on                              |
| `--cooldown`  | 60      | seconds to ignore repeat triggers              |
| `--dry-run`   | off     | log triggers but never actually restart        |

## Limitations

- Only works while the Mac is awake and on the network — it can't wake
  itself from sleep or power on from off.
- Anyone who can reach the port and knows the token can restart the Mac,
  so keep the token private and consider restricting the port to your LAN
  (e.g. via your router's firewall) rather than exposing it to the internet.

## License

MIT
