import csv
import logging
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import pdfplumber
import requests

# suppress pdfminer warnings (pdfplumber's underlying library)
# these appear when a PDF has malformed font metadata and are harmless
logging.getLogger("pdfminer").setLevel(logging.ERROR)


SHOPIFY_URL = "https://gardenlearningstore.com/products.json?limit=250"
CSV_COLUMNS = [
    "Internal Draft Order Id", "Note", "Email", "Tags",
    "Lineitem name", "Lineitem price", "Lineitem quantity", "Lineitem sku",
    "Customer First Name", "Customer Last Name", "Phone",
    "Billing First Name", "Billing Last Name", "Billing Address1",
    "Billing City", "Billing Zip", "Billing Country", "Billing Province",
    "Billing Company", "Billing Phone",
    "Shipping First Name", "Shipping Last Name", "Shipping Address1",
    "Shipping City", "Shipping Zip", "Shipping Country", "Shipping Province",
    "Shipping Company",
]

def has_isbn_table(pdf_path):
    """
    Returns True if the PDF appears to contain a table with ISBNs.
    Used to detect whether to use parse_isbn_table or parse_cart_pdf.
    """
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text and "isbn" in text.lower():
                return True
    return False

def get_raw_tables(pdf_path):
    """
    Open the PDF at pdf_path.
    Return a list of tables, where each table is a list of rows,
    and each row is a list of cell values.
    """
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables.extend(page.extract_tables())
    return tables

def parse_isbn_table(tables):
    """
    Takes the raw output of get_raw_tables().
    Returns a list of dicts, each with keys: name, sku, quantity, price.

    Assumes all tables belong to a single order (one company per PDF).
    """
    rows = []
    for table in tables:
        header = table[0]
        name_idx = header.index('Book Name')
        sku_idx = header.index('ISBN')
        quantity_idx = header.index('Quantity')
        price_idx = header.index('List Price')

        for row in table[1:]:
            if row[0] and row[0].strip():
                rows.append({
                    "name": row[name_idx],
                    "sku": re.sub(r"\D", "", row[sku_idx]),
                    "quantity": row[quantity_idx],
                    "price": row[price_idx].replace("$", "").replace(" ", "") if row[price_idx] else "",
                })
    return rows

def fetch_shopify_catalogue():
    """
    Fetch all products from gardenlearningstore.com.
    Returns a dict mapping variant_id -> {sku, title, variant_title, price}
    """
    all_products = []
    try:
        page = 1
        while True:
            response = requests.get(f"{SHOPIFY_URL}&page={page}", timeout=30)
            page_products = response.json().get("products", [])
            all_products.extend(page_products)
            if len(page_products) < 250:
                break
            page += 1

    except requests.exceptions.RequestException as e:
        print(f"WARNING: Could not reach {SHOPIFY_URL} (network error: {e}). ISBNs will be blank in output.")
        return {}
    except ValueError as e:
        print(f"WARNING: Response from {SHOPIFY_URL} was not valid JSON ({e}). ISBNs will be blank in output.")
        return {}

    variant_catalogue = {}
    for product in all_products:
        title = product.get("title")
        variants = product.get("variants", [])
        for variant in variants:
            sku = variant.get("sku")
            sku = sku.strip() if sku else None
            price = variant.get("price")
            variant_catalogue[variant.get("id")] = {
                "sku": sku,
                "title": title,
                "variant_title": variant.get("title"),
                "price": price,
            }
    return variant_catalogue

def parse_cart_pdf(pdf_path, variant_catalogue):
    """
    Parse a Shopify cart PDF by extracting variant IDs from hyperlinks.
    Returns a list of dicts with keys: name, sku, quantity, price.
    
    Assumes all items belong to a single order (one company per PDF).
    """
    rows = []
    seen = set()
    quantities = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # extract quantities from text
            text = page.extract_text() or ""
            page_quantities = re.findall(r'\$[\d.]+\s+(\d+)\s+\$[\d.]+', text)
            quantities.extend(page_quantities)

            # extract books from annotations
            for annot in page.annots:
                uri = annot.get("uri", "")
                # example URI: https://gardenlearningstore.com/products/look-touch-learn-garden?variant=44568341676290
                if "/products/" in uri and "variant=" in uri:
                    variant_id = uri.split("variant=")[1]
                    if variant_id not in seen:
                        seen.add(variant_id)
                        variant = variant_catalogue.get(int(variant_id))
                        if not variant:
                            slug = uri.split("/products/")[1].split("?")[0]
                            print(f"WARNING: '{slug}' (variant {variant_id}) not found in catalogue")
                            continue
                        rows.append({
                            "name": variant.get("title"),
                            "sku": variant.get("sku"),
                            "quantity": "CHECK QUANTITY",
                            "price": variant.get("price"),
                        })

    # match quantities to rows positionally
    if len(rows) != len(quantities):
        print(f"WARNING: found {len(rows)} books but {len(quantities)} quantities. Please manually input quantities.")
        return rows
    for i, row in enumerate(rows):
        row["quantity"] = quantities[i]

    return rows

def write_csv(rows, source_pdf_path=None):
    """
    Write a list of row dicts to a Shopify draft orders CSV.
    Output is saved to the output/ folder, named after the source PDF.
    Each row dict has keys: name, sku, quantity, price.
    """ 
    if source_pdf_path:
        filename = source_pdf_path.stem + ".csv"
    else:
        filename = f"draft_orders_{date.today()}.csv"

    output_path = Path(__file__).parent / "output" / filename
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "Lineitem name": row["name"],
                "Lineitem price": row["price"],
                "Lineitem quantity": row["quantity"],
                "Lineitem sku": row["sku"],
            })
    print(f"Done! Output saved to: {output_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python parse_orders.py /path/to/order.pdf")
        print("  python parse_orders.py /path/to/folder/")
        sys.exit(1)

    input_path = Path(sys.argv[1])

    # collect PDF files
    if input_path.is_dir():
        pdf_files = sorted(input_path.glob("*.pdf"))
    elif input_path.is_file() and input_path.suffix.lower() == ".pdf":
        pdf_files = [input_path]
    else:
        print(f"Error: {input_path} is not a PDF file or directory")
        sys.exit(1)
    
    if not pdf_files:
        print(f"No PDF files found in {input_path}")
        sys.exit(1)
    print(f"Found {len(pdf_files)} PDF(s) to process.")
    
    # fetch shopify catalogue
    variant_catalogue = fetch_shopify_catalogue()

    # process each PDF
    for pdf_path in pdf_files:
        print(f"\nProcessing: {pdf_path.name}")
        if has_isbn_table(pdf_path):
            tables = get_raw_tables(pdf_path)
            rows = parse_isbn_table(tables)
        else:
            rows = parse_cart_pdf(pdf_path, variant_catalogue)
        
        if not rows:
            print(f"No line items extracted from {pdf_path.name}")
            continue

        write_csv(rows, pdf_path)

        processed_dir = pdf_path.parent / "processed"
        processed_dir.mkdir(exist_ok=True)
        shutil.move(str(pdf_path), processed_dir / pdf_path.name) 
        print(f"Moved {pdf_path.name} to processed/")

if __name__ == "__main__":
    main()
