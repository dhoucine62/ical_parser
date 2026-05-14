# ICalendar Scraper - ADE

Scraper Python pour exporter les calendriers depuis l'interface ADE de l'Université d'Artois.

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

```bash
python ical_scraper.py [OPTIONS]
```

Saisis tes identifiants quand le script te le demande, puis laisse-le tourner.

### Arguments de commande

- `--url, -u` (chaîne): URL de base d'ADE. Défaut: `https://ade-consult.univ-artois.fr/jsp/standard/gui/interface.jsp`
  
- `--output, -o` (chaîne): Chemin du fichier JSON de sortie. Défaut: `ade_exports.json`

- `--headless`: Exécuter en mode headless (sans fenêtre navigateur). Défaut: mode interactif avec fenêtre

- `--no-interactive-login`: Ne pas faire de pause pour connexion CAS manuelle. Requiert `--cas-username` et `--cas-password` ou mode headless

- `--cas-username` (chaîne): Nom d'utilisateur CAS pour connexion automatique (optionnel)

- `--cas-password` (chaîne): Mot de passe CAS pour connexion automatique (optionnel, à utiliser avec prudence)

- `--timeout` (entier): Délai d'attente des sélecteurs en millisecondes. Défaut: `15000`

- `--max-steps` (entier): Nombre maximum de clics d'ouverture de branches. Défaut: `1000`

- `--click-delay-ms` (entier): Délai entre les clics de branches en millisecondes. Défaut: `800`

### Exemples de commandes

```bash
# Mode interactif (par défaut) avec fenêtre navigateur
python ical_scraper.py

# Mode headless avec connexion automatique
python ical_scraper.py --headless --cas-username john.doe --cas-password secretpass


# Mode headless avec clics plus lents (utile pour connexions lentes)
python ical_scraper.py --headless --click-delay-ms 1500 --cas-username john.doe --cas-password secretpass
```

## Output

- **ade_exports.json**: Fichier JSON contenant les calendriers avec `resourceId`, texte et information de chemin

### Format de sortie

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

## Lien iCal

Une fois `ade_exports.json` généré, utilise la valeur `resourceId` de chaque entrée pour construire un lien iCal de cette forme :

```text
https://ade-consult.univ-artois.fr/jsp/custom/modules/plannings/anonymous_cal.jsp?resources=7694&projectId=3&calType=ical
```

Dans cet exemple, `resources=7694` correspond au `resourceId` récupéré directement dans `ade_exports.json`.

## License

MIT License
