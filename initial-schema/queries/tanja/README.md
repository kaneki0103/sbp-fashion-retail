# Upiti - Menadzer prodaje

### Upit 1: Koje prodavnice su ostvarile najveći prihod u 2024. godini i koliko odstupaju od proseka prodavnica koje su te godine imale prodaju?

```javascript
db.invoices.aggregate([
  {
    $match: {
      transaction_type: "Sale",
      $expr: { $eq: [{ $year: { $dateFromString: { dateString: "$date" } } }, 2024] }
    }
  },
  { $unwind: "$lines" },

  {
    $addFields: {
      "lines.line_total_usd": {
        $multiply: [
          "$lines.line_total",
          {
            $switch: {
              branches: [
                { case: { $eq: ["$currency", "USD"] }, then: 1 },
                { case: { $eq: ["$currency", "EUR"] }, then: 1.08 },
                { case: { $eq: ["$currency", "GBP"] }, then: 1.27 },
                { case: { $eq: ["$currency", "CNY"] }, then: 0.14 }
              ],
              default: 1
            }
          }
        ]
      }
    }
  },

  {
    $group: {
      _id: "$store_id",
      total_revenue: { $sum: "$lines.line_total_usd" },
      avg_line_value: { $avg: "$lines.line_total_usd" },
      total_lines: { $sum: 1 }
    }
  },
  { $sort: { total_revenue: -1 } },
  {
    $group: {
      _id: null,
      stores: {
        $push: {
          store_id: "$_id",
          total_revenue: "$total_revenue",
          avg_line_value: "$avg_line_value",
          total_lines: "$total_lines"
        }
      },
      global_avg: { $avg: "$total_revenue" }
    }
  },
  { $unwind: "$stores" },
  {
    $lookup: {
      from: "stores",
      localField: "stores.store_id",
      foreignField: "_id",
      as: "store_info"
    }
  },
  {
    $project: {
      _id: 0,
      store_id: "$stores.store_id",
      store_name: { $arrayElemAt: ["$store_info.store_name", 0] },
      city: { $arrayElemAt: ["$store_info.city", 0] },
      country: { $arrayElemAt: ["$store_info.country", 0] },
      total_revenue: { $round: ["$stores.total_revenue", 2] },
      avg_line_value: { $round: ["$stores.avg_line_value", 2] },
      total_lines: "$stores.total_lines",
      difference_from_avg: {
        $round: [{ $subtract: ["$stores.total_revenue", "$global_avg"] }, 2]
      },
      status: {
        $cond: {
          if: { $gte: ["$stores.total_revenue", "$global_avg"] },
          then: "above average",
          else: "below average"
        }
      }
    }
  },
  { $sort: { total_revenue: -1 } }
])
```

**Rezultat upita:**
![Rezultat upita1](1.query.png)

*Prosecno vreme izvrsavanja: 14.10s*  

### Upit 2: Koji zaposleni su tokom 2024. godine ostvarili prihod iznad proseka zaposlenih u svojoj prodavnici, i za koliko?

```javascript
db.invoices.aggregate([
  {
    $match: {
      transaction_type: "Sale",
      $expr: { $eq: [{ $year: { $dateFromString: { dateString: "$date" } } }, 2024] }
    }
  },
  {
    $group: {
      _id: { store_id: "$store_id", employee_id: "$employee_id" },
      employee_revenue: { $sum: "$invoice_total" },
      total_invoices: { $sum: 1 }
    }
  },
  {
    $group: {
      _id: "$_id.store_id",
      store_avg_revenue: { $avg: "$employee_revenue" },
      employees: {
        $push: {
          employee_id: "$_id.employee_id",
          employee_revenue: "$employee_revenue",
          total_invoices: "$total_invoices"
        }
      }
    }
  },
  { $unwind: "$employees" },
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
      employee_id: "$employees.employee_id",
      employee_revenue: { $round: ["$employees.employee_revenue", 2] },
      total_invoices: "$employees.total_invoices",
      store_avg_revenue: { $round: ["$store_avg_revenue", 2] },
      above_avg_by: {
        $round: [{ $subtract: ["$employees.employee_revenue", "$store_avg_revenue"] }, 2]
      }
    }
  },
  { $match: { above_avg_by: { $gt: 0 } } },
  { $sort: { above_avg_by: -1 } }
])
```

**Rezultat upita:**
![Rezultat upita2](2.query.png)

*Prosecno vreme izvrsavanja: 7.13s*  

### Upit 3: Identifikovati koje prodavnice imaju najvise problema sa vracanjem robe i koja kategorija dominira u povracajima.

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

*Prosecno vreme izvrsavanja: 3.21s*  

### Upit 4: Prikazati koji gradovi pokazuju pad prihoda u Q4 (oktobar, novembar, decembar) u 2024. godini u odnosu na isti period 2023.

```javascript
db.getCollection("invoices").aggregate([
  {
    $match: {
      transaction_type: "Sale",
      $expr: {
        $in: [
          { $month: { $dateFromString: { dateString: "$date" } } },
          [10, 11, 12]
        ]
      }
    }
  },
  {
    $group: {
      _id: {
        city: "$customer.city",
        year: { $year: { $dateFromString: { dateString: "$date" } } },
        month: { $month: { $dateFromString: { dateString: "$date" } } }
      },
      monthly_revenue: { $sum: "$invoice_total" }
    }
  },
  {
    $group: {
      _id: {
        city: "$_id.city",
        month: "$_id.month"
      },
      yearly_data: {
        $push: {
          year: "$_id.year",
          revenue: "$monthly_revenue"
        }
      }
    }
  },
  {
    $project: {
      _id: 0,
      city: "$_id.city",
      month: "$_id.month",
      revenue_2023: {
        $sum: {
          $map: {
            input: { $filter: { input: "$yearly_data", as: "d", cond: { $eq: ["$$d.year", 2023] } } },
            as: "d",
            in: "$$d.revenue"
          }
        }
      },
      revenue_2024: {
        $sum: {
          $map: {
            input: { $filter: { input: "$yearly_data", as: "d", cond: { $eq: ["$$d.year", 2024] } } },
            as: "d",
            in: "$$d.revenue"
          }
        }
      }
    }
  },
  {
    $match: {
      revenue_2023: { $gt: 0 },
      revenue_2024: { $gt: 0 }
    }
  },
  {
    $project: {
      city: 1,
      month: 1,
      revenue_2023: { $round: ["$revenue_2023", 2] },
      revenue_2024: { $round: ["$revenue_2024", 2] },
      change_percent: {
        $round: [
          {
            $multiply: [
              { $divide: [{ $subtract: ["$revenue_2024", "$revenue_2023"] }, "$revenue_2023"] },
              100
            ]
          },
          2
        ]
      }
    }
  },
  {
    $match: {
      change_percent: { $lt: 0 }
    }
  },
  {
    $sort: { change_percent: 1 }
  }
])
```

**Rezultat upita:**
![Rezultat upita4](4.query.png) 

*Prosecno vreme izvrsavanja: 11.52s*  


### Upit 5: Koji su top 10 radnika po prihodu u decembru?

```javascript
db.getCollection("invoices").aggregate([
  {
    $match: {
      transaction_type: "Sale",
      $expr: {
        $eq: [
          { $month: { $dateFromString: { dateString: "$date" } } },
          12
        ]
      }
    }
  },
  {
    $group: {
      _id: "$employee_id",
      store_id: { $first: "$store_id" },
      total_revenue: { $sum: "$invoice_total" },
      total_invoices: { $sum: 1 }
    }
  },
  { $sort: { total_revenue: -1 } },
  { $limit: 10 },
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
      _id: 0,
      employee_id: "$_id",
      store_id: 1,
      store_name: { $arrayElemAt: ["$store_info.store_name", 0] },
      city: { $arrayElemAt: ["$store_info.city", 0] },
      country: { $arrayElemAt: ["$store_info.country", 0] },
      total_revenue: { $round: ["$total_revenue", 2] },
      total_invoices: 1
    }
  },
  { $sort: { total_revenue: -1 } }
])
```

**Rezultat upita:**
![Rezultat upita5](5.query.png) 

*Prosecno vreme izvrsavanja: 7.06s*  
