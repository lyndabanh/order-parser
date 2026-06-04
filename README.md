# Order Parser

A command-line tool that converts book order PDFs into Shopify-compatible draft order CSVs.

## The Problem

A small book distributor was manually re-entering order data from customer PDFs into Shopify, copying book titles, ISBNs, quantities, and prices one by one. The goal was to automate that process so they could drop PDFs into a folder, double-click a script, and get a ready-to-import CSV.

## How It Works

The tool handles two PDF formats:

**Quote PDFs** contain a formatted table with book titles, ISBNs, quantities, and prices. These are parsed directly using `pdfplumber`'s table extraction.

**Cart PDFs** are printed Shopify shopping carts with titles and prices but no ISBNs. These are parsed by extracting hyperlinks embedded in the PDF (every book image and title links to its product page, including the Shopify variant ID in the URL). The variant ID is then used to look up the ISBN from the store's public product catalogue.

```
PDF input
  ├── Quote format (has ISBN column)
  │     └── pdfplumber table extraction → parse rows → write CSV
  └── Cart format (no ISBNs)
        └── extract variant IDs from annotations
              └── look up ISBNs via Shopify /products.json API → write CSV
```

## Technical Details

**Two-mode detection:** the script inspects each PDF for the word "isbn" in its text. If found, it uses the table parser. If not, it uses the annotation-based cart parser. This runs automatically with no input from the user.

**Shopify API pagination:** the store uses the public Storefront `/products.json` endpoint, which uses older `?page=N` style pagination rather than the cursor-based pagination with `Link` headers available in the Admin API. The script fetches all pages and builds a complete variant catalogue in memory before processing any PDFs.

**Variant ID lookup:** Shopify cart PDFs embed hyperlinks on each product that include the variant ID in the URL (e.g. `?variant=44568377360642`). Each variant maps to a specific edition of a book (hardcover vs. paperback, English vs. bilingual) with its own ISBN. Looking up by variant ID is more precise than fuzzy title matching.

**Quantity extraction:** quantities in cart PDFs are extracted from the page text using a regex pattern that matches the `$price quantity $total` layout, then matched positionally to the annotation-derived book list.

## Stack

- Python 3
- `pdfplumber` — PDF text, table, and annotation extraction
- `requests` — Shopify Storefront API
- `csv`, `pathlib`, `re` — standard library

## Usage

```bash
# process a folder of PDFs
python parse_orders.py input/

# process a single PDF
python parse_orders.py order.pdf
```

Output CSVs are written to `output/` with the same name as the input PDF. Processed PDFs are moved to `input/processed/` automatically.

For non-technical users, a `run_me.command` shell script is included. Double-clicking it from Finder runs the tool without needing a terminal.

## Distribution

To share this tool with a non-technical user, send them a folder containing:

```
Order Parser/
├── input/          ← drop PDF files here
├── output/         ← converted CSVs appear here
├── parse_orders.py
├── requirements.txt
└── run_me.command
```

Do not include `venv/` — the script will create it automatically on first run.

The recipient needs Python 3 installed. On first run, `run_me.command` will install all dependencies automatically. If double-clicking gives a permissions error, run this once in Terminal:

```bash
chmod +x run_me.command
```

After that, double-clicking will work permanently.

## Setup

For development:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

`requirements.txt` contains only the direct dependencies (`pdfplumber` and `requests`) and is used by `run_me.command` when setting up on a user's machine. `requirements-dev.txt` contains fully pinned versions of all dependencies for a reproducible development environment.
