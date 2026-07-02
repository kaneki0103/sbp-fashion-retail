from datetime import datetime
from pymongo import MongoClient, InsertOne
from pymongo.errors import ConnectionFailure

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "fashion_retail_db"
BATCH_SIZE = 25000
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"  # "2023-01-01 15:42:00"
CURRENCY_TO_USD = {"USD": 1, "EUR": 1.08, "GBP": 1.27, "CNY": 0.14}


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


def build_menadzer_collection(db):

    print("--- Kreiranje kolekcije: invoice_lines_menadzer ---")

    db["invoice_lines_menadzer"].drop()
    print("Stara verzija kolekcije (ako je postojala) obrisana.\n")

    print("Ucitavanje 'stores' u memoriju radi spajanja...")
    stores_map = {s["_id"]: s for s in db["stores"].find()}
    print(f"Ucitano {len(stores_map)} prodavnica.\n")

    print("Obrada kolekcije 'invoices' (Sale + Return, sve transakcije)...")
    cursor = db["invoices"].find({}).batch_size(10000)

    batch = []
    total_lines = 0
    total_invoices = 0

    for inv in cursor:
        total_invoices += 1
        store = stores_map.get(inv.get("store_id"), {})
        customer = inv.get("customer", {})

        raw_date = inv.get("date")
        try:
            parsed_date = datetime.strptime(raw_date, DATE_FORMAT)
        except (ValueError, TypeError):
            parsed_date = None

        year = parsed_date.year if parsed_date else None
        month = parsed_date.month if parsed_date else None
        date_value = parsed_date  # cuvamo pravi datetime (BSON Date u Mongu)

        for line in inv.get("lines", []):
            doc = {
                "invoice_id": inv["_id"],
                "date": date_value,
                "year": year,        
                "month": month,         
                "transaction_type": inv.get("transaction_type"),
                "currency": inv.get("currency"),

                "store_id": inv.get("store_id"),         
                "employee_id": inv.get("employee_id"),   
                "store_name": store.get("store_name"),      
                "store_city": store.get("city"),             
                "store_country": store.get("country"),         

                "customer_id": customer.get("customer_id"),
                "customer_name": customer.get("name"),
                "customer_city": customer.get("city"),
                "customer_country": customer.get("country"),

                "category": line.get("category"),
                "quantity": line.get("quantity"),
                "line_total": line.get("line_total"),
                "line_total_usd": round(                                         
                            line.get("line_total", 0) * CURRENCY_TO_USD.get(inv.get("currency"), 1), 2),

                "invoice_total": inv.get("invoice_total"),
            }
            batch.append(InsertOne(doc))
            total_lines += 1

            if len(batch) >= BATCH_SIZE:
                db["invoice_lines_menadzer"].bulk_write(batch, ordered=False)
                batch = []
                print(f"  Ubaceno do sad: {total_lines} linija "
                      f"(iz {total_invoices} faktura)...")

    if batch:
        db["invoice_lines_menadzer"].bulk_write(batch, ordered=False)

    print(f"\nZavrseno. Ukupno faktura obradjeno: {total_invoices}")
    print(f"Ukupno linija ubaceno u 'invoice_lines_menadzer': {total_lines}\n")


def main():
    client = connect_to_mongo(MONGO_URI)
    if not client:
        return

    db = client[DB_NAME]

    build_menadzer_collection(db)

    print("=" * 50)
    print("Optimizovana kolekcija uspesno kreirana!")
    print(f"Baza: {DB_NAME}")
    print("Nova kolekcija: invoice_lines_menadzer")
    print("=" * 50)

    client.close()


if __name__ == "__main__":
    main()