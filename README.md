# ICalendar Scraper - ADE

A Python scraper to export calendars from the ADE interface of Université d'Artois.

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

```bash
python ical_scraper.py [OPTIONS]
```

Enter your credentials when prompted and let the script work.

### Command-Line Arguments

- `--url, -u` (string): Base ADE URL. Default: `https://ade-consult.univ-artois.fr/jsp/standard/gui/interface.jsp`
  
- `--output, -o` (string): Output JSON file path. Default: `ade_exports.json`

- `--headless`: Run in headless mode (no browser window displayed). Default: interactive mode with browser window

- `--no-interactive-login`: Do not pause for manual CAS login. Requires `--cas-username` and `--cas-password` or headless mode prompting

- `--cas-username` (string): CAS username for automatic login (optional)

- `--cas-password` (string): CAS password for automatic login (optional, use with caution)

- `--timeout` (int): Selector wait timeout in milliseconds. Default: `15000`

- `--max-steps` (int): Maximum number of branch opening clicks. Default: `1000`

- `--click-delay-ms` (int): Delay between branch clicks in milliseconds. Default: `800`

### Example Commands

```bash
# Interactive mode (default) with browser window
python ical_scraper.py

# Headless mode with automatic login
python ical_scraper.py --headless --cas-username john.doe --cas-password secretpass

# Custom output file and increased timeout
python ical_scraper.py -o my_calendars.json --timeout 20000

# Headless mode with slower clicks (useful for slow connections)
python ical_scraper.py --headless --click-delay-ms 1500 --cas-username john.doe --cas-password secretpass
```

## Output

- **ade_exports.json**: JSON file containing calendars with `resourceId`, text, and path information

### Output Format

```json
[
  {
    "resourceId": "7694",
    "text": "L2 Info",
    "path": "Planning / Licences / L2 Info",
    "href": "javascript:check(7694, 'true')"
  }
]
```

## iCal Link

Once `ade_exports.json` is generated, use the `resourceId` value from each entry to build an iCal link like:

```text
https://ade-consult.univ-artois.fr/jsp/custom/modules/plannings/anonymous_cal.jsp?resources=7694&projectId=3&calType=ical
```

In this example, `resources=7694` is the `resourceId` taken directly from `ade_exports.json`.

## License

MIT License
