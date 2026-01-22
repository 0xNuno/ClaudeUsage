# Claude Usage Tracker

A lightweight macOS menu bar app that displays your Claude AI usage limits in real-time.

![Menu Bar Preview](docs/preview.png)

## Features

- **Session Limit**: 5-hour rolling window usage with countdown
- **Weekly Limit**: 7-day usage across all models
- **Sonnet Limit**: Sonnet-specific weekly usage
- **Auto-refresh**: Updates every 60 seconds
- **Secure Storage**: Credentials stored in macOS Keychain

## Installation

### Option 1: Run from Source (Development)

```bash
# Clone the repo
git clone https://github.com/yourusername/ClaudeUsage.git
cd ClaudeUsage

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python claude_usage.py
```

### Option 2: Build as macOS App

```bash
# Install py2app
pip install py2app

# Build the app
python setup.py py2app

# The app will be in dist/Claude Usage.app
# Move to Applications
mv "dist/Claude Usage.app" /Applications/
```

## Setup

1. Launch the app (it appears in your menu bar)
2. Click on the menu bar icon → "Settings..."
3. Follow the instructions to get your credentials:

### Getting Your Credentials

1. Open https://claude.ai/settings/usage in your browser
2. Open Developer Tools (Cmd+Option+I)
3. Go to the **Network** tab
4. Refresh the page and find the `usage` request
5. Click on it and look at the **Headers** tab
6. In the Cookie header, find `sessionKey=sk-ant-sid01-...` and copy the value
7. Your **Organization ID** is the UUID in the URL or in Settings → Account

## How It Works

The app polls Claude's usage API every 60 seconds:

```
GET https://claude.ai/api/organizations/{org-id}/usage
Cookie: sessionKey=sk-ant-sid01-...
```

Response includes:
- `five_hour.percent_used` - Session limit (0-100%)
- `five_hour.resets_at` - ISO timestamp when session resets
- `seven_day.percent_used` - Weekly limit
- `seven_day.resets_at` - Weekly reset timestamp
- `seven_day_sonnet.percent_used` - Sonnet-specific weekly limit

## Security

- Credentials are stored in **macOS Keychain** (encrypted)
- No data is sent anywhere except Claude's official API
- Session key is only transmitted to `claude.ai` over HTTPS
- Source code is fully open for inspection

## Troubleshooting

### "Claude: Setup" in menu bar
Click Settings and enter your credentials.

### "Claude: Error" in menu bar
- Session key may have expired (re-enter in Settings)
- Network connectivity issue
- Check Console.app for detailed errors

### Session key expires
Claude session keys expire periodically. When this happens:
1. Log into claude.ai in your browser
2. Get a fresh sessionKey from DevTools
3. Update in Settings

## License

MIT License - See LICENSE file

## Contributing

Pull requests welcome! Please open an issue first to discuss changes.
