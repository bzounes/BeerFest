# 🍺 BeerFest

A self-hosted web app for running a home beer festival. Guests connect over local WiFi to register their beers, vote across categories, and watch the winners get revealed by the host.

---

## Features

- **Beer registration** — Enter a beer name, your name, and an optional photo
- **9 voting categories** — 3 votes per person per category, cast and removed with a single tap
- **Real-time voting UI** — No page reloads; selected beers highlight instantly
- **Locked results** — Winners stay hidden until the host flips the switch
- **Admin panel** — Password-protected; reveal/hide results, delete entries, reset all data
- **Offline-ready** — No CDN dependencies; works on a local network with no internet

---

## Voting Categories

| # | Category |
|---|----------|
| 1 | 🍺 Best IPA |
| 2 | 🖤 Best Dark Beer |
| 3 | 🍋 Best Sour / Fruit Beer |
| 4 | 🌾 Best Lager / Pilsner |
| 5 | 🍹 Best Non-Beer |
| 6 | ✨ Most Unique |
| 7 | 🎨 Best Label |
| 8 | 🏆 Best Overall |
| 9 | 💀 Worst Overall |

---

## Requirements

- Python 3.8+
- pip

Everything else (Flask, Pillow, SQLite) is installed automatically.

---

## Quick Start

```bash
git clone <repo-url>
cd BeerFest
./run.sh
```

The script creates a virtual environment, installs dependencies, and starts the server. Open the URL printed in the terminal from any device on the same WiFi network.

### Raspberry Pi

```bash
# Run on the default port (5000)
./run.sh

# Run on a different port
./run.sh 8080
```

Connect guests to `http://<pi-ip-address>:5000`. The startup banner prints the local IP automatically.

### Custom admin password

The default admin password is `beerfest`. Change it by setting an environment variable before starting:

```bash
ADMIN_PASSWORD=mysecret ./run.sh
```

You can also set a stable session secret key to persist login sessions across restarts:

```bash
SECRET_KEY=some-random-string ADMIN_PASSWORD=mysecret ./run.sh
```

---

## Usage

### For guests

1. Connect to the host's WiFi network
2. Open `http://<host-ip>:5000` in a browser
3. Tap **Add Beer** to register your entry — name, your name, and an optional photo
4. Tap **Vote** to browse the 9 categories and cast up to 3 votes per category
5. Tap a voted beer again to remove that vote
6. Check **Results** once the host announces the reveal

### For the host (admin)

1. Go to `http://<host-ip>:5000/admin` and log in with the admin password
2. Monitor vote tallies per category in real time
3. Delete any mistaken entries if needed
4. When voting is done, click **Reveal Results** — all guests instantly see the winners
5. Use **Reset All Data** to wipe everything for a fresh festival

---

## Project Structure

```
BeerFest/
├── app.py                  # Flask application & routes
├── requirements.txt        # Python dependencies
├── run.sh                  # Bootstrap & start script
├── static/
│   ├── css/style.css       # Dark amber theme, mobile-first
│   ├── js/app.js           # Vote toggling, image preview, dialogs
│   └── uploads/            # Uploaded beer photos (git-ignored)
└── templates/
    ├── base.html           # Shared layout & navigation
    ├── index.html          # Home page
    ├── register.html       # Beer registration form
    ├── beers.html          # Browse all beers
    ├── vote_home.html      # Category picker
    ├── vote.html           # Vote within a category
    ├── results.html        # Winner podium (when revealed)
    ├── results_hidden.html # Locked results placeholder
    ├── admin_login.html    # Admin login
    └── admin.html          # Admin panel
```

The SQLite database (`beerfest.db`) is created automatically on first run.

---

## Notes

- Voter identity is tracked by a browser session cookie. Clearing cookies allows re-voting — acceptable for a home party.
- Uploaded images are automatically resized to a maximum of 900×900 px to keep storage light on a Raspberry Pi.
- The app binds to `0.0.0.0` so it is reachable from other devices on the local network. Do not expose it to the public internet.
