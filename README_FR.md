# ICalendar Scraper - ADE

Scraper Python pour exporter les calendriers depuis l'interface ADE de l'Université d'Artois.

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

```bash
python ical_parser.py
```

Saisis tes identifiants quand le script te le demande, puis laisse-le tourner.

## Output

- **ade_exports.json**: Calendrier avec le `resourceId`

## Lien iCal

Une fois `ade_exports.json` généré, utilise la valeur `resourceId` de chaque entrée pour construire un lien iCal de cette forme :

```text
https://ade-consult.univ-artois.fr/jsp/custom/modules/plannings/anonymous_cal.jsp?resources=7694&projectId=3&calType=ical
```

Dans cet exemple, `resources=7694` correspond au `resourceId` récupéré directement dans `ade_exports.json`.

## Configuration

Modifie `config.json` pour changer l'URL de base ADE.

## License

MIT License
