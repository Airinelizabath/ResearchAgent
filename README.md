# Google News CLI

A premium Node.js command-line interface (CLI) application to fetch and read the latest news from Google News. Supports an interactive menu with selection controls, article summaries, direct web page opening, and flexible search/topic arguments.

## Features

- 📰 **Interactive Mode**: Select news categories, search terms, and articles interactively.
- 🌐 **Direct Browser Launching**: Open any article directly in your default browser from the CLI.
- 🔍 **Custom Search Query**: Retrieve search-specific news instantly.
- 🏷️ **Standard Categories**: Fast filtering by World, Nation, Business, Technology, Science, Sports, Health, or Entertainment.
- 🌍 **International Support**: Customize country and language settings (e.g., US/en, IN/en, ES/es, etc.).
- 🚀 **Script Friendly**: Command options allow pipe-friendly plain list outputs.

---

## Installation

1. Clone or navigate to the project directory:
   ```bash
   cd /home/archeron/ANTIGRAVITY_PROJ
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Link the package globally (optional, to run the `google-news` command anywhere):
   ```bash
   npm link
   ```

---

## Usage

### Interactive Mode

Simply run the application without any flags to enter interactive mode:
```bash
node index.js
```
*(Or run `google-news` if globally linked)*

Inside the interactive terminal:
- Use **Up/Down Arrow keys** to navigate options.
- Press **Enter** to select.
- Choose articles to inspect their details and select **Open in browser** or go back.

### CLI Direct Mode (Non-Interactive)

Get top news stories directly:
```bash
node index.js --top
```

Search Google News for articles about a specific subject:
```bash
node index.js --search "quantum computing"
```

Fetch news by a category topic:
```bash
node index.js --topic technology
```

#### Customization Options

| Option | Shorthand | Description | Default |
| :--- | :--- | :--- | :--- |
| `--limit <num>` | `-l` | Limit the number of articles | `10` |
| `--country <code>`| `-c` | Two-letter country code (US, GB, IN, etc.)| `US` |
| `--lang <code>` | `-g` | Two-letter language code (en, fr, es, etc.)| `en` |
| `--interactive` | `-i` | Force interactive mode | — |

**Examples:**
- Fetch 5 business news stories from India in English:
  ```bash
  node index.js --topic business --limit 5 --country IN --lang en
  ```
- Search for "space exploration" in French from France:
  ```bash
  node index.js --search "exploration spatiale" --country FR --lang fr --limit 3
  ```

---

## Technical Details

- **Language**: Node.js ES Modules (compatibility configured for Node `v12.22.0+`)
- **Main Dependencies**:
  - `rss-parser` for parsing Google News XML feeds.
  - `commander` for powerful option parsing.
  - `prompts` for the terminal list select menus.
  - `picocolors` for lightweight colored terminal prints.
  - `open` to trigger browser opens from terminal.
