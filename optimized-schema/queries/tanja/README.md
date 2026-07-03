# Optimizovani upiti - Menadzer prodaje

### Upit 1: Koje prodavnice su ostvarile najveći prihod u 2024. godini i koliko odstupaju od proseka prodavnica koje su te godine imale prodaju?

```javascript
db.invoice_lines_menadzer.aggregate([
  { $match: { transaction_type: "Sale", year: 2024 } },

  {
    $group: {
      _id: "$store_id",
      store_name: { $first: "$store_name" },
      city: { $first: "$store_city" },
      country: { $first: "$store_country" },
      total_revenue: { $sum: "$line_total_usd" },
      avg_line_value: { $avg: "$line_total_usd" },
      total_lines: { $sum: 1 }
    }
  },

  { $sort: { total_revenue: -1 } },
  {
    $group: {
      _id: null,
      stores: { $push: "$$ROOT" },
      global_avg: { $avg: "$total_revenue" }
    }
  },
  { $unwind: "$stores" },
  {
    $project: {
      _id: 0,
      store_id: "$stores._id",
      store_name: "$stores.store_name",
      city: "$stores.city",
      country: "$stores.country",
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

*Prosecno vreme izvrsavanja: 4.66s*  

### Upit 2: KKoji zaposleni su tokom 2024. godine ostvarili prihod iznad proseka zaposlenih u svojoj prodavnici, i za koliko?

```javascript
db.invoice_lines_menadzer.aggregate([
  { $match: { transaction_type: "Sale", year: 2024 } },
  {
    $group: {
      _id: { store_id: "$store_id", employee_id: "$employee_id" },
      store_name: { $first: "$store_name" },
      employee_revenue: { $sum: "$line_total" },
      invoice_ids: { $addToSet: "$invoice_id" }
    }
  },
  {
    $group: {
      _id: "$_id.store_id",
      store_name: { $first: "$store_name" },
      store_avg_revenue: { $avg: "$employee_revenue" },
      employees: {
        $push: {
          employee_id: "$_id.employee_id",
          employee_revenue: "$employee_revenue",
          total_invoices: { $size: "$invoice_ids" }
        }
      }
    }
  },
  { $unwind: "$employees" },
  {
    $project: {
      _id: 0,
      store_id: "$_id",
      store_name: 1,
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

*Prosecno vreme izvrsavanja: 4.3s*  

### Upit 3: Identifikovati koje prodavnice imaju najvise problema sa vracanjem robe i koja kategorija dominira u povracajima.

```javascript
db.invoice_lines_menadzer.aggregate([
  { $match: { transaction_type: "Return" } },
  {
    $group: {
      _id: { store_id: "$store_id", category: "$category" },
      store_name: { $first: "$store_name" },
      city: { $first: "$store_city" },
      country: { $first: "$store_country" },
      total_returns: { $sum: "$quantity" },
      total_return_value: { $sum: "$line_total" }
    }
  },

  { $sort: { "_id.store_id": 1, total_returns: -1 } },

  {
    $group: {
      _id: "$_id.store_id",
      store_name: { $first: "$store_name" },
      city: { $first: "$city" },
      country: { $first: "$country" },
      top_category: { $first: "$_id.category" },
      top_category_returns: { $first: "$total_returns" },
      top_category_value: { $first: "$total_return_value" }
    }
  },
  {
    $project: {
      _id: 0,
      store_id: "$_id",
      store_name: 1,
      city: 1,
      country: 1,
      top_category: 1,
      top_category_returns: 1,
      top_category_value: { $round: ["$top_category_value", 2] }
    }
  },

  { $sort: { top_category_returns: -1 } }
])
```

**Rezultat upita:**
![Rezultat upita3](3.query.png) 

*Prosecno vreme izvrsavanja: 0.72s*  

### Upit 4: Prikazati koji gradovi pokazuju pad prihoda u Q4 (oktobar, novembar, decembar) u 2024. godini u odnosu na isti period 2023.

```javascript
db.invoice_lines_menadzer.aggregate([
  {
    $match: {
      transaction_type: "Sale",
      month: { $in: [10, 11, 12] },
      year: { $in: [2023, 2024] }
    }
  },
  {
    $group: {
      _id: {
        city: "$customer_city",
        year: "$year",
        month: "$month"
      },
      monthly_revenue: { $sum: "$line_total" }
    }
  },
  {
    $group: {
      _id: { city: "$_id.city", month: "$_id.month" },
      yearly_data: { $push: { year: "$_id.year", revenue: "$monthly_revenue" } }
    }
  },
  {
    $project: {
      _id: 0,
      city: "$_id.city",
      month: "$_id.month",
      revenue_2023: {
        $sum: { $map: { input: { $filter: { input: "$yearly_data", as: "d", cond: { $eq: ["$$d.year", 2023] } } }, as: "d", in: "$$d.revenue" } }
      },
      revenue_2024: {
        $sum: { $map: { input: { $filter: { input: "$yearly_data", as: "d", cond: { $eq: ["$$d.year", 2024] } } }, as: "d", in: "$$d.revenue" } }
      }
    }
  },
  { $match: { revenue_2023: { $gt: 0 }, revenue_2024: { $gt: 0 } } },
  {
    $project: {
      city: 1,
      month: 1,
      revenue_2023: { $round: ["$revenue_2023", 2] },
      revenue_2024: { $round: ["$revenue_2024", 2] },
      change_percent: {
        $round: [
          { $multiply: [{ $divide: [{ $subtract: ["$revenue_2024", "$revenue_2023"] }, "$revenue_2023"] }, 100] },
          2
        ]
      }
    }
  },
  { $match: { change_percent: { $lt: 0 } } },
  { $sort: { change_percent: 1 } }
])
```

**Rezultat upita:**
![Rezultat upita4](4.query.png) 

*Prosecno vreme izvrsavanja: 2.05s*  


### Upit 5: Koji su top 10 radnika po prihodu u decembru?

```javascript
db.invoice_lines_menadzer.aggregate([
  {
    $match: {
      transaction_type: "Sale",
      month: 12
    }
  },
  {
    $group: {
      _id: "$employee_id",
      store_id: { $first: "$store_id" },
      store_name: { $first: "$store_name" },
      city: { $first: "$store_city" },
      country: { $first: "$store_country" },
      total_revenue: { $sum: "$line_total" },
      invoice_ids: { $addToSet: "$invoice_id" }
    }
  },
  {
    $project: {
      _id: 0,
      employee_id: "$_id",
      store_id: 1,
      store_name: 1,
      city: 1,
      country: 1,
      total_revenue: { $round: ["$total_revenue", 2] },
      total_invoices: { $size: "$invoice_ids" }
    }
  },

  { $sort: { total_revenue: -1 } },
  { $limit: 10 }
])
```

**Rezultat upita:**
![Rezultat upita5](5.query.png) 

*Prosecno vreme izvrsavanja: 2.45s*  
