### Upiti - Menadzer prodaje

### Upit 1: Prodavnice rangirane po prosečnoj vrednosti fakture, sa poređenjem sa globalnim prosekom. Koje prodavnice su iznad/ispod globalnog proseka prosečne fakture, i za koliko?

```javascript
db.getCollection("invoices").aggregate([
  {
    $group: {
      _id: "$store_id",
      avg_invoice: { $avg: "$invoice_total" }
    }
  },
  {
    $sort: { avg_invoice: -1 }
  },
  {
    $group: {
      _id: null,
      stores: { $push: { store_id: "$_id", avg_invoice: "$avg_invoice" } },
      global_avg: { $avg: "$avg_invoice" }
    }
  },
  {
    $unwind: "$stores"
  },
  {
    $project: {
      _id: 0,
      store_id: "$stores.store_id",
      avg_invoice: "$stores.avg_invoice",
      global_avg: 1,
      difference: { $subtract: ["$stores.avg_invoice", "$global_avg"] },
      status: {
        $cond: {
          if: { $gte: ["$stores.avg_invoice", "$global_avg"] },
          then: "above average",
          else: "below average"
        }
      }
    }
  },
  {
    $lookup: {
      from: "stores",
      localField: "store_id",
      foreignField: "_id",
      as: "store_info"
    }
  },
  {
    $project: {
      store_id: 1,
      store_name: { $arrayElemAt: ["$store_info.store_name", 0] },
      city: { $arrayElemAt: ["$store_info.city", 0] },
      country: { $arrayElemAt: ["$store_info.country", 0] },
      avg_invoice: 1,
      global_avg: 1,
      difference: 1,
      status: 1
    }
  },
  {
    $sort: { avg_invoice: -1 }
  }
])
```

**Rezultat upita:**
![Rezultat upita1](1.query.png)

*Prosecno vreme izvrsavanja: 4.29s*  


### Upit 2: Top 10% kupaca po potrošnji sa dominantnim načinom plaćanja. Identifikovati top 10% kupaca koji najviše troše i utvrditi koji način plaćanja dominira kod njih.

```javascript
db.getCollection("invoices").aggregate([
  {
    $group: {
      _id: {
        customer_id: "$customer.customer_id",
        payment_method: "$payment_method"
      },
      total_spent: { $sum: "$invoice_total" },
      customer_name: { $first: "$customer.name" },
      customer_city: { $first: "$customer.city" },
      customer_country: { $first: "$customer.country" }
    }
  },
  {
    $sort: { total_spent: -1 }
  },
  {
    $group: {
      _id: "$_id.customer_id",
      customer_name: { $first: "$customer_name" },
      customer_city: { $first: "$customer_city" },
      customer_country: { $first: "$customer_country" },
      dominant_payment: { $first: "$_id.payment_method" },
      total_spent: { $sum: "$total_spent" }
    }
  },
  {
    $sort: { total_spent: -1 }
  },
  {
    $limit: 128370
  },
  {
    $project: {
      _id: 0,
      customer_id: "$_id",
      customer_name: 1,
      customer_city: 1,
      customer_country: 1,
      dominant_payment: 1,
      total_spent: { $round: ["$total_spent", 2] }
    }
  }
])
```

**Rezultat upita:**
![Rezultat upita2](2.query.png)

*Prosecno vreme izvrsavanja: 62.33s*  

### Upit 3: Identifikovati koje prodavnice imaju najviše problema sa vraćanjem robe i koja kategorija dominira u povraćajima.

```javascript
db.getCollection("invoices").aggregate([
  {
    $match: {
      transaction_type: "Return"
    }
  },
  {
    $unwind: "$lines"
  },
  {
    $group: {
      _id: {
        store_id: "$store_id",
        category: "$lines.category"
      },
      total_returns: { $sum: "$lines.quantity" },
      total_return_value: { $sum: "$lines.line_total" }
    }
  },
  {
    $sort: {
      "_id.store_id": 1,
      total_returns: -1
    }
  },
  {
    $group: {
      _id: "$_id.store_id",
      top_category: { $first: "$_id.category" },
      top_category_returns: { $first: "$total_returns" },
      top_category_value: { $first: "$total_return_value" }
    }
  },
  {
    $lookup: {
      from: "stores",
      localField: "_id",
      foreignField: "_id",
      as: "store_info"
    }
  },
  {
    $project: {
      _id: 0,
      store_id: "$_id",
      store_name: { $arrayElemAt: ["$store_info.store_name", 0] },
      city: { $arrayElemAt: ["$store_info.city", 0] },
      country: { $arrayElemAt: ["$store_info.country", 0] },
      top_category: 1,
      top_category_returns: 1,
      top_category_value: { $round: ["$top_category_value", 2] }
    }
  },
  {
    $sort: { top_category_returns: -1 }
  }
])
```

**Rezultat upita:**
![Rezultat upita3](3.query.png) 

*Prosecno vreme izvrsavanja: 4.36s*  
