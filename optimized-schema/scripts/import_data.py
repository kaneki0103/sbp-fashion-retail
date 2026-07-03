from pymongo import MongoClient, InsertOne
from pymongo.errors import ConnectionFailure
 
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "fashion_retail_db"
BATCH_SIZE = 5000
 
 
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
 
 
def build_denormalized_collection(db):
    print("--- Kreiranje kolekcije: invoice_lines_denorm ---")
 
    db["invoice_lines_denorm"].drop()
    print("Stara verzija kolekcije (ako je postojala) obrisana.\n")
 
    print("Ucitavanje 'stores' u memoriju radi spajanja...")
    stores_map = {s["_id"]: s for s in db["stores"].find()}
    print(f"Ucitano {len(stores_map)} prodavnica.\n")
 
    print("Obrada kolekcije 'invoices' (samo transakcije tipa 'Sale')...")
    cursor = db["invoices"].find({"transaction_type": "Sale"})
 
    batch = []
    total_lines = 0
    total_invoices = 0
 
    for inv in cursor:
        total_invoices += 1
        store = stores_map.get(inv.get("store_id"), {})
        customer = inv.get("customer", {})
 
        for line in inv.get("lines", []):
            doc = {
                "invoice_id": inv["_id"],
                "date": inv.get("date"),
                "transaction_type": inv.get("transaction_type"),
 
                "store_id": inv.get("store_id"),
                "store_country": store.get("country"),
                "store_city": store.get("city"),
 
                "customer_id": customer.get("customer_id"),
                "customer_name": customer.get("name"),
                "customer_gender": customer.get("gender"),
                "customer_country": customer.get("country"),
                "customer_dob": customer.get("date_of_birth"),
 
                "product_id": line.get("product_id"),
                "category": line.get("category"),
                "subcategory": line.get("subcategory"),
                "size": line.get("size"),
                "color": line.get("color"),
                "quantity": line.get("quantity"),
                "unit_price": line.get("unit_price"),
                "line_total": line.get("line_total"),
 
                "invoice_total": inv.get("invoice_total"),
            }
            batch.append(InsertOne(doc))
            total_lines += 1
 
            if len(batch) >= BATCH_SIZE:
                db["invoice_lines_denorm"].bulk_write(batch, ordered=False)
                batch = []
                print(f"  Ubaceno do sad: {total_lines} linija "
                      f"(iz {total_invoices} faktura)...")
 
    if batch:
        db["invoice_lines_denorm"].bulk_write(batch, ordered=False)
 
    print(f"\nZavrseno. Ukupno faktura obradjeno: {total_invoices}")
    print(f"Ukupno linija ubaceno u 'invoice_lines_denorm': {total_lines}\n")
 
 
def main():
    client = connect_to_mongo(MONGO_URI)
    if not client:
        return
 
    db = client[DB_NAME]
 
    build_denormalized_collection(db)
 
    print("=" * 50)
    print("Denormalizovana kolekcija uspesno kreirana!")
    print(f"Baza: {DB_NAME}")
    print("Nova kolekcija: invoice_lines_denorm")
    print("Stare kolekcije (invoices, stores) su netaknute.")
    print("=" * 50)
 
    client.close()
 
 
if __name__ == "__main__":
    main()
