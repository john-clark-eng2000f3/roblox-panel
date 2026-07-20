# roblox-panel

Terminal dashboard for checking on my Roblox games and tailing server logs without opening creator hub in a browser every five minutes.

Uses the Roblox Open Cloud API for metrics, datastores, and log streams. Can also do place restarts if you provide an API key with the restart permission.

## Install

```bash
git clone https://github.com/author/roblox-panel.git
cd roblox-panel
pip install -e .
```

## Setup

Save your Open Cloud API key and universe ID:

```bash
roblox-panel config set --key YOUR_OPEN_CLOUD_KEY
roblox-panel config add-universe --name "Main Game" --id 123456789
```

Keys are stored locally in `~/.config/roblox-panel/config.db` (sqlite).

## Usage

Open the live dashboard:

```bash
roblox-panel top
```

Tail Open Cloud engine logs for an experience:

```bash
roblox-panel logs tail --universe 123456789 --follow
```

List active server instances:

```bash
roblox-panel servers list --universe 123456789
```

Check datastore budget or read key:

```bash
roblox-panel datastore get --universe 123456789 --store PlayerData --key player_1049281
```

## License

MIT
