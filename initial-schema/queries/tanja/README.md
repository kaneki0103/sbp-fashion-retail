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
![Rezultat upita](1.query.png)
