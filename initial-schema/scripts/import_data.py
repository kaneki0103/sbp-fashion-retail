from importlib.resources import path

import pandas as pd
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os

# ─────────────────────────────────────────────
# KONFIGURACIJA
# ─────────────────────────────────────────────
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "fashion_retail_db"
DATA_PATH = os.path.join(os.path.dirname(__file__), "data")

CHUNK_SIZE = 100_000  # broj redova po chunk-u 


# ─────────────────────────────────────────────
# KONEKCIJA
# ─────────────────────────────────────────────
def connect_to_mongo(uri):
    print("Povezivanje na MongoDB...")
    try:
        client = MongoClient(uri)
        client.admin.command("ping")
        print("MongoDB konekcija uspesna.\n")
        return client
    except ConnectionFailure as e:
        print(f"Greska pri povezivanju: {e}")
        return None


# ─────────────────────────────────────────────
# UcITAVANJE LOOKUP TABELA U MEMORIJU
# ─────────────────────────────────────────────
def load_lookup_data(path):
    print("Ucitavanje lookup tabela (customers, products, stores, employees, discounts)...")

    # NOVO:
    customers_df = pd.read_csv(os.path.join(path, "customers.csv"), dtype={"Telephone": str})
    products_df  = pd.read_csv(os.path.join(path, "products.csv"))
    stores_df    = pd.read_csv(os.path.join(path, "stores.csv"))
    employees_df = pd.read_csv(os.path.join(path, "employees.csv"))

    # customer_id -> dict sa podacima o kupcu
    customers_map = {
        row["Customer ID"]: {
            "customer_id":  row["Customer ID"],
            "name":         row["Name"],
            "email":        row["Email"],
            "telephone":    row["Telephone"],
            "city":         row["City"],
            "country":      row["Country"],
            "gender":       row["Gender"],
            "date_of_birth": str(row["Date Of Birth"]),
            "job_title":    row["Job Title"]
        }
        for _, row in customers_df.iterrows()
    }

    # product_id -> dict sa podacima o proizvodu
    products_map = {
        row["Product ID"]: {
            "product_id":       row["Product ID"],
            "category":         row["Category"],
            "subcategory":      row["Sub Category"],
            "description_en":   row.get("Description EN", ""),
            "color":            row["Color"],
            "sizes":            row["Sizes"],
            "production_cost":  row["Production Cost"]
        }
        for _, row in products_df.iterrows()
    }

    # store_id -> dict sa podacima o prodavnici
    stores_map = {
        row["Store ID"]: {
            "store_id":           row["Store ID"],
            "store_name":         row["Store Name"],
            "country":            row["Country"],
            "city":               row["City"],
            "zip_code":           row["ZIP Code"],
            "latitude":           row["Latitude"],
            "longitude":          row["Longitude"],
            "number_of_employees": row["Number of Employees"]
        }
        for _, row in stores_df.iterrows()
    }

    # employee_id -> {name, position, store_id}
    employees_map = {
        row["Employee ID"]: {
            "employee_id": row["Employee ID"],
            "name":        row["Name"],
            "position":    row["Position"],
            "store_id":    row["Store ID"]
        }
        for _, row in employees_df.iterrows()
    }

    print("Lookup tabele uspesno ucitane.\n")
    return customers_map, products_map, stores_map, employees_map


# ─────────────────────────────────────────────
# IMPORT STORES KOLEKCIJE (sa ugnjezdenim zaposlenima)
# ─────────────────────────────────────────────
def import_stores(db, stores_map, employees_map):
    print("--- Obrada kolekcije: stores ---")

    db["stores"].delete_many({})

    # Grupisanje zaposlenih po store_id
    employees_by_store = {}
    for emp in employees_map.values():
        sid = emp["store_id"]
        if sid not in employees_by_store:
            employees_by_store[sid] = []
        employees_by_store[sid].append({
            "employee_id": emp["employee_id"],
            "name":        emp["name"],
            "position":    emp["position"]
        })

    documents = []
    for store_id, store in stores_map.items():
        doc = {
            "_id":                store["store_id"],
            "store_name":         store["store_name"],
            "country":            store["country"],
            "city":               store["city"],
            "zip_code":           store["zip_code"],
            "latitude":           store["latitude"],
            "longitude":          store["longitude"],
            "number_of_employees": store["number_of_employees"],
            "employees":          employees_by_store.get(store_id, [])
        }
        documents.append(doc)

    db["stores"].insert_many(documents)
    print(f"Ubaceno {len(documents)} prodavnica u kolekciju 'stores'.\n")


# ─────────────────────────────────────────────
# IMPORT INVOICES KOLEKCIJE (transactions -> Invoice dokumenti)
# ─────────────────────────────────────────────
def import_invoices(db, path, customers_map, products_map):
    print("--- Obrada kolekcije: invoices ---")
    print("(transactions.csv je velik, citamo ga u chunkovima...)\n")

    db["invoices"].delete_many({})

    # NOVO:
    transactions_path = os.path.join(path, "transactions.csv")
    total_invoices = 0
    chunk_num = 0

    for chunk in pd.read_csv(transactions_path, chunksize=CHUNK_SIZE):
        chunk_num += 1
        print(f"  Obradjujem chunk #{chunk_num} ({len(chunk)} redova)...")

        # Grupisanje redova po Invoice ID -> jedan dokument po fakturi
        invoice_groups = {}

        for _, row in chunk.iterrows():
            inv_id = row["Invoice ID"]

            if inv_id not in invoice_groups:
                # Kreiranje novog Invoice dokumenta
                customer = customers_map.get(row["Customer ID"], {})
                invoice_groups[inv_id] = {
                    "_id":              inv_id,
                    "date":             str(row["Date"]),
                    "payment_method":   row["Payment Method"],
                    "transaction_type": row["Transaction Type"],
                    "invoice_total":    row["Invoice Total"],
                    "currency":         row["Currency"],
                    "store_id":         row["Store ID"],
                    "employee_id":      row["Employee ID"],
                    "customer": {
                        "customer_id":  customer.get("customer_id"),
                        "name":         customer.get("name"),
                        "email":        customer.get("email"),
                        "telephone":    customer.get("telephone"),
                        "city":         customer.get("city"),
                        "country":      customer.get("country"),
                        "gender":       customer.get("gender"),
                        "date_of_birth": customer.get("date_of_birth"),
                        "job_title":    customer.get("job_title")
                    },
                    "lines": []
                }

            # Dodavanje linije proizvoda u fakturu
            product = products_map.get(row["Product ID"], {})
            line = {
                "line":        row["Line"],
                "product_id":  row["Product ID"],
                "category":    product.get("category"),
                "subcategory": product.get("subcategory"),
                "size":        row["Size"],
                "color":       row["Color"],
                "unit_price":  row["Unit Price"],
                "quantity":    row["Quantity"],
                "discount":    row["Discount"],
                "line_total":  row["Line Total"]
            }
            invoice_groups[inv_id]["lines"].append(line)

        # Ubacivanje obradjenog chunk-a u MongoDB
        # Koristimo upsert jer ista faktura moze biti rasporedjena u vise chunkova
        if invoice_groups:
            from pymongo import UpdateOne
            operations = []
            for inv_id, doc in invoice_groups.items():
                lines = doc.pop("lines")
                operations.append(
                    UpdateOne(
                        {"_id": inv_id},
                        {
                            "$setOnInsert": doc,
                            "$push": {"lines": {"$each": lines}}
                        },
                        upsert=True
                    )
                )
            db["invoices"].bulk_write(operations, ordered=False)
            total_invoices += len(invoice_groups)
            print(f"  Obradjeno {len(invoice_groups)} faktura. Ukupno do sad: {total_invoices}\n")

    print(f"Kolekcija 'invoices' zavrsena. Ukupno faktura: {total_invoices}\n")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    client = connect_to_mongo(MONGO_URI)
    if not client:
        return

    db = client[DB_NAME]

    customers_map, products_map, stores_map, employees_map = load_lookup_data(DATA_PATH)

    import_stores(db, stores_map, employees_map)
    import_invoices(db, DATA_PATH, customers_map, products_map)

    print("=" * 50)
    print("Svi podaci su uspesno importovani u MongoDB!")
    print(f"Baza: {DB_NAME}")
    print(f"Kolekcije: invoices, stores")
    print("=" * 50)

    client.close()


if __name__ == "__main__":
    main()