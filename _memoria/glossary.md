# Glossary

Shorthand, acronimi e termini interni.

## Fornitori / Siti
| Termine | Significato |
|---------|-------------|
| **Sacchi** / **sacchi.it** | Sacchi Elettroforniture — distributore materiale elettrico |
| **Elsist** | Elsist.biz — distributore automazione/PLC |
| **RS** | RS Online — distributore componenti elettronici |

## Strumenti CLI
| Termine | Significato |
|---------|-------------|
| **sacchi-cli** | `python sacchi_cli.py` — CLI per Sacchi.it |
| **search** | `sacchi_cli.py search <codice>` — cerca articolo |
| **cart-add** | `sacchi_cli.py cart-add <productId> <qty>` — aggiunge al carrello |
| **cart-remove** | `sacchi_cli.py cart-remove <productId>` — rimuove dal carrello |
| **cart-view** | `sacchi_cli.py cart-view` — mostra carrello |
| **price-research** | Skill Cowork per ricerca prezzi automatica da fornitori |

## Codici prodotto
| Termine | Significato |
|---------|-------------|
| **productId** | Codice interno Sacchi.it — 18 cifre (es. 000000000001406383) |
| **mfr code** | Codice produttore — quello stampato sul prodotto (es. 3RT20161BB41) |
| **GTIN** | Barcode EAN del prodotto |

## File importanti
| Termine | File |
|---------|------|
| **sacchi_cli** | `C:\Users\tecni\Claude\sacchi_cli.py` |
| **cookie sacchi** | `C:\Users\tecni\Claude\sacchi_cookies.json` |
| **prezzi db** | `C:\Users\tecni\Claude\prezzi_fornitori.db` |
| **prezzi json** | `C:\Users\tecni\Claude\prezzi_fornitori_completo.json` |
