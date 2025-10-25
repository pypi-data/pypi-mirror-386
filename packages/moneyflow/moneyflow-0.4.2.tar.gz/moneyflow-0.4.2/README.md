# moneyflow

**Track your moneyflow from the terminal.**

A keyboard-driven terminal UI for managing personal finance transactions. Built for users who prefer efficiency and direct control over their financial data.

![moneyflow main screen](https://raw.githubusercontent.com/wesm/moneyflow-assets/main/home-screen.png)

**Supported Platforms:**
- ✅ **Monarch Money** - Full integration with editing and sync
- ✅ **Amazon Purchases** - Import and analyze purchase history
- ✅ **Demo Mode** - Try it without an account

**Documentation:** [moneyflow.dev](https://moneyflow.dev)

---

## Installation

```bash
# Install with pip
pip install moneyflow

# Or run without installing (recommended)
uvx moneyflow

# Or use pipx
pipx install moneyflow
```

---

## Quick Start

```bash
# Try demo mode first (no account needed)
moneyflow --demo

# Connect to Monarch Money
moneyflow

# Analyze Amazon purchase history
moneyflow amazon import ~/Downloads/"Your Orders"
moneyflow amazon

# Load only recent data (Monarch)
moneyflow --year 2025
```

**First-time Monarch Money setup:** You'll need your 2FA secret key. See the [Monarch Money setup guide](https://moneyflow.dev/guide/monarch).

---

## Key Features

- **Keyboard-driven** - Navigate with `g` to cycle views, `Enter` to drill down, `Escape` to go back
- **Multi-select bulk editing** - Select with `Space`, edit with `m`/`c`/`h`, commit with `w`
- **Drill-down and sub-grouping** - Analyze spending from multiple angles
- **Type-to-search** - Filter transactions as you type with `/`
- **Time navigation** - Switch periods with `t`/`y`/`a` and `←`/`→` arrows
- **Review before commit** - Preview all changes before syncing to backend
- **Encrypted credentials** - AES-128 with PBKDF2 (100,000 iterations)

Full keyboard shortcuts and tutorials: [moneyflow.dev](https://moneyflow.dev)

---

## Common Workflows

**Clean up merchant names:**
1. Press `g` until Merchant view
2. Press `m` on a merchant to rename all transactions
3. Press `w` to review and commit

**Recategorize transactions:**
1. Press `d` for detail view
2. Press `Space` to multi-select transactions
3. Press `c` to change category
4. Press `w` to review and commit

**Analyze spending:**
1. Press `g` to cycle to Category view
2. Press `Enter` on a category to drill down
3. Press `g` to sub-group by merchant or account
4. Press `t` for this month, `←`/`→` to navigate periods

Learn more: [Navigation & Search Guide](https://moneyflow.dev/guide/navigation)

---

## Amazon Mode

Import and analyze your Amazon purchase history:

1. Request "Your Orders" export from Amazon (Account Settings → Privacy)
2. Download and unzip "Your Orders.zip"
3. Import: `moneyflow amazon import ~/Downloads/"Your Orders"`
4. Launch: `moneyflow amazon`

See [Amazon Mode Guide](https://moneyflow.dev/guide/amazon-mode) for details.

---

## Troubleshooting

**Login fails with "Incorrect password"**
→ Enter your **encryption password** (for moneyflow), not your Monarch password
→ If forgotten: Click "Reset Credentials" or delete `~/.moneyflow/`

**2FA not working**
→ Copy the BASE32 secret (long string), not the QR code
→ Get fresh secret: Disable and re-enable 2FA in Monarch Money

**Terminal displays weird characters**
→ Use a modern terminal with Unicode support (iTerm2, GNOME Terminal, Windows Terminal)

**Complete reset**
```bash
rm -rf ~/.moneyflow/
pip install --upgrade --force-reinstall moneyflow
moneyflow
```

More help: [Troubleshooting Guide](https://moneyflow.dev/reference/troubleshooting)

---

## Documentation

**Full documentation available at [moneyflow.dev](https://moneyflow.dev)**

- [Installation](https://moneyflow.dev/getting-started/installation)
- [Quick Start Tutorial](https://moneyflow.dev/getting-started/quickstart)
- [Navigation & Search](https://moneyflow.dev/guide/navigation)
- [Editing Transactions](https://moneyflow.dev/guide/editing)
- [Keyboard Shortcuts](https://moneyflow.dev/guide/keyboard-shortcuts)
- [Monarch Money Setup](https://moneyflow.dev/guide/monarch)
- [Amazon Mode](https://moneyflow.dev/guide/amazon-mode)

---

## Security

- Credentials encrypted with AES-128 using PBKDF2 key derivation (100,000 iterations)
- Encryption password never leaves your machine
- Stored in `~/.moneyflow/credentials.enc` with 600 permissions
- See [SECURITY.md](SECURITY.md) for full details

---

## Contributing

Contributions welcome! See [Contributing Guide](https://moneyflow.dev/development/contributing).

**Development setup:**
```bash
git clone https://github.com/wesm/moneyflow.git
cd moneyflow
uv sync
uv run pytest -v
```

**Code quality checks:**
```bash
uv run pytest -v                          # Tests
uv run pyright moneyflow/                 # Type checking
uv run ruff format moneyflow/ tests/      # Formatting
uv run ruff check moneyflow/ tests/       # Linting
```

See [Developing moneyflow](https://moneyflow.dev/development/developing) for details.

---

## Acknowledgments

### Monarch Money Integration
This project's Monarch Money backend uses code derived from the [monarchmoney](https://github.com/hammem/monarchmoney) Python client library by hammem, used under the MIT License. See [licenses/monarchmoney-LICENSE](licenses/monarchmoney-LICENSE) for details.

Monarch Money® is a trademark of Monarch Money, Inc. This project is independent and not affiliated with, endorsed by, or officially connected to Monarch Money, Inc.

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

**Disclaimer:** Independent open-source project. Not affiliated with or endorsed by Monarch Money, Inc.
