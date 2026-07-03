// Indeks 1 -  2, 4, 5 
db.invoice_lines_menadzer.createIndex({ transaction_type: 1, year: 1, month: 1 })

// Indeks 2 -  1, 3 
db.invoice_lines_menadzer.createIndex({ transaction_type: 1, store_id: 1 })