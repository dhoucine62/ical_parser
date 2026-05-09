# ICalendar Scraper - ADE

A Python scraper to export calendars from the ADE interface of Université d'Artois.

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

```bash
python main.py
```

Enter your credentials when prompted and let the script work.

## Output

- **ade_exports.json**: Calendars with `resourceId`

## iCal Link

Once `ade_exports.json` is generated, use the `resourceId` value from each entry to build an iCal link like:

```text
https://ade-consult.univ-artois.fr/jsp/custom/modules/plannings/anonymous_cal.jsp?resources={resourceId}&projectId=3&calType=ical
```

In this example, `resources=7694` is the `resourceId` taken directly from `ade_exports.json`.

## Configuration

Edit `config.json` to change the ADE base URL.

## License

MIT License
