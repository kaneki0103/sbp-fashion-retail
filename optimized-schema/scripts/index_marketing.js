db.invoice_lines_denorm.createIndex({ customer_id: 1 })
 
db.invoice_lines_denorm.createIndex({ store_country: 1, subcategory: 1 })