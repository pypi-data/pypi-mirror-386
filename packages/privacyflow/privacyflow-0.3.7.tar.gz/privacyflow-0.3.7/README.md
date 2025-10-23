# PrivacyFlow – Mappatura intelligente dei flussi di dati personali

## Installazione

Richiede **Python 3.10 o superiore**.

Da PyPI ufficiale:


pip install privacyflow
 
privacy-flow --help

Output:

usage: privacy-flow {init,scan,compose,render,license} ...

Comandi disponibili:
  init       Crea un file privacy.yaml di esempio
  scan       Analizza un dominio o sito web e individua terze parti
  compose    Unisce i risultati di più fonti in una mappa dei flussi
  render     Genera un report HTML / Markdown / JSON
  license    Gestisce l’attivazione e verifica della licenza
 
Licenze e modalità d’uso

Community	Gratuita per uso interno e demo	Sì	Integrata
Enterprise	Funzionalità estese (report avanzati, API, branding)	No	Chiave RSA firmata

Attivazione licenza
privacy-flow license activate license.json
In assenza di licenza, PrivacyFlow opera automaticamente in modalità Community Edition con watermark visibile nei report.

Documentazione ufficiale
Documentazione completa, esempi e modelli YAML:
https://www.privacyflow.it/docs

Approfondimenti:

Ruoli GDPR nel modello PrivacyFlow

Personalizzazione dei report HTML

Integrazione nei processi CI/CD

Autori e crediti
PrivacyFlow Labs
https://www.privacyflow.it

Maintainer: Fabio Marano

Licenza
Proprietaria – © 2025 PrivacyFlow Labs
Distribuita esclusivamente per uso interno, audit e ricerca.
È vietata la redistribuzione, modifica o rivendita senza autorizzazione scritta.