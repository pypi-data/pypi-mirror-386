# Quick Start

Get up and running with moneyflow in 5 minutes.

---

## Demo Mode (No Account Required)

Try moneyflow instantly without connecting any accounts:

```bash
moneyflow --demo
```

This loads synthetic spending data so you can explore all features risk-free.

**What you'll see:**
- 1,000+ transactions
- Realistic spending patterns
- Multiple accounts
- All features enabled

Press ++g++ to cycle through views, ++slash++ to search, ++q++ to quit.

---

## With Your Monarch Money Account

### Step 1: Get Your 2FA Secret

!!! warning "Important: Do this BEFORE running moneyflow"
    You'll need your 2FA/TOTP secret key. Here's how to get it:

    1. Log into [Monarch Money](https://app.monarchmoney.com/) on the web
    2. Go to **Settings** → **Security**
    3. **Disable** 2FA, then **re-enable** it
    4. When shown the QR code, click **"Can't scan?"** or **"Manual entry"**
    5. Copy the secret key (looks like: `JBSWY3DPEHPK3PXP`)

### Step 2: Launch moneyflow

```bash
moneyflow
```

On first run, you'll be prompted for:

1. **Monarch Money email** - Your login email
2. **Monarch Money password** - Your account password
3. **2FA Secret** - The secret key from Step 1
4. **Encryption password** - Create a NEW password to encrypt your stored credentials

!!! tip "Encryption Password"
    This is a **new password** just for moneyflow, not your Monarch password.

    Choose something you'll remember - you'll need it each time you launch moneyflow.

### Step 3: Wait for Initial Data Load

First run downloads all your transactions:

- **Small accounts** (<1k transactions): ~10 seconds
- **Medium accounts** (1k-10k): ~30 seconds
- **Large accounts** (10k+): ~1-2 minutes

!!! success "One-Time Download"
    After the first load, all operations are instant! moneyflow works offline with your data cached locally.

### Step 4: Explore

You're in! Here's what to try:

- Press ++g++ to cycle through Merchants → Categories → Groups
- Press ++enter++ on any row to drill down
- Press ++escape++ to go back
- Press ++question++ for help

---

## Common First Commands

```bash
# Load only current year (faster for large accounts)
moneyflow --year 2025

# Enable caching for even faster startup next time
moneyflow --cache
```

---

## Quick Edit Example

Let's rename a merchant:

1. Launch: `moneyflow`
2. Press ++g++ until you see "Merchants" view
3. Use arrow keys to find a merchant
4. Press ++m++ to edit merchant name
5. Type the new name, press ++enter++
6. Press ++w++ to review changes
7. Press ++enter++ to commit to Monarch Money

Done! The change is now saved.

---

## Next Steps

- [Keyboard Shortcuts](../guide/keyboard-shortcuts.md) - Learn all the keybindings
- [Navigation & Search](../guide/navigation.md) - Understand the different views
- [Editing Transactions](../guide/editing.md) - Master bulk operations

---

## Need Help?

- [FAQ](../reference/faq.md) - Common questions
- [Troubleshooting](../reference/troubleshooting.md) - Fix common issues
- [GitHub Issues](https://github.com/wesm/moneyflow/issues) - Report bugs
