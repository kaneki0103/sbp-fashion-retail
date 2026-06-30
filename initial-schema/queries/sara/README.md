// UPIT 1 
// za svaku zemlju, izlistati subkategoriju proizvoda koja je donela najveci ukupni prihod
// i koliki je njen udeo u ukupnom prihodu te zemlje

```javascript
db.getCollection("invoices").aggregate(
    [
        {
            $match: { transaction_type: "Sale" }
        },
        {
            $lookup: {
                from: "stores",
                localField: "store_id",
                foreignField: "_id",
                as: "store"
            }
        },
        {
            $unwind: "$store"
        },
        {
            $unwind: "$lines"
        },
        {
            $group: {
                _id: {
                    region: "$store.country",
                    subcategory: "$lines.subcategory"
                },
                subcategory_revenue: { $sum: "$lines.line_total" }
            }
        },
        {
            $sort: {
                "_id.region": 1,
                subcategory_revenue: -1
            }
        },
        {
            $group: {
                _id: "$_id.region",
                top_subcategory: { $first: "$_id.subcategory" },
                top_subcategory_revenue: { $first: "$subcategory_revenue" },
                total_region_revenue: { $sum: "$subcategory_revenue" }
            }
        },
        {
            $project: {
                _id: 0,
                region: "$_id",
                top_subcategory: 1,
                top_subcategory_revenue: { $round: ["$top_subcategory_revenue", 2] },
                total_region_revenue: { $round: ["$total_region_revenue", 2] },
                revenue_share_pct: {
                    $round: [
                        {
                            $multiply: [
                                { $divide: ["$top_subcategory_revenue", "$total_region_revenue"] },
                                100
                            ]
                        },
                        2
                    ]
                }
            }
        },
        {
            $sort: { total_region_revenue: -1 }
        }
    ],
    { allowDiskUse: true }
)



// UPIT 2
// za svaku starosnu grupu (18-25, 26-35, 36-45, 46+) i pol,
// izracunati prosecnu potrosnju po transakciji i uporediti sa globalnim prosekom

db.getCollection("invoices").aggregate(
    [
        {
            $match: { transaction_type: "Sale" }
        },
        {
            $addFields: {
                age: {
                    $dateDiff: {
                        startDate: {
                            $dateFromString: {
                                dateString: "$customer.date_of_birth",
                                onError: null,
                                onNull: null
                            }
                        },
                        endDate: "$$NOW",
                        unit: "year"
                    }
                }
            }
        },
        {
            $match: { age: { $gte: 18, $lte: 100 } }
        },
        {
            $addFields: {
                age_group: {
                    $switch: {
                        branches: [
                            { case: { $lte: ["$age", 25] }, then: "18-25" },
                            { case: { $lte: ["$age", 35] }, then: "26-35" },
                            { case: { $lte: ["$age", 45] }, then: "36-45" }
                        ],
                        default: "46+"
                    }
                }
            }
        },
        {
            $group: {
                _id: {
                    age_group: "$age_group",
                    gender: "$customer.gender"
                },
                avg_spend: { $avg: "$invoice_total" },
                total_spend: { $sum: "$invoice_total" },
                num_transactions: { $sum: 1 }
            }
        },
        {
            $group: {
                _id: null,
                global_avg: { $avg: "$avg_spend" },
                segments: {
                    $push: {
                        age_group: "$_id.age_group",
                        gender: "$_id.gender",
                        avg_spend: "$avg_spend",
                        total_spend: "$total_spend",
                        num_transactions: "$num_transactions"
                    }
                }
            }
        },
        {
            $unwind: "$segments"
        },
        {
            $project: {
                _id: 0,
                age_group: "$segments.age_group",
                gender: "$segments.gender",
                avg_spend: { $round: ["$segments.avg_spend", 2] },
                total_spend: { $round: ["$segments.total_spend", 2] },
                num_transactions: "$segments.num_transactions",
                global_avg: { $round: ["$global_avg", 2] },
                difference_from_global: {
                    $round: [{ $subtract: ["$segments.avg_spend", "$global_avg"] }, 2]
                },
                pct_above_global: {
                    $round: [
                        {
                            $multiply: [
                                {
                                    $divide: [
                                        { $subtract: ["$segments.avg_spend", "$global_avg"] },
                                        "$global_avg"
                                    ]
                                },
                                100
                            ]
                        },
                        2
                    ]
                }
            }
        },
        {
            $sort: { avg_spend: -1 }
        }
    ],
    { allowDiskUse: true }
)



// UPIT 3
// pronaci top 10% kupaca po ukupnoj potrosnji i ispisati koliki procenat ukupnog prihoda cine
// kao i koja kategorija proizvoda dominira u njihovim kupovinama

db.getCollection("invoices").aggregate(
    [
        { $match: { transaction_type: "Sale" } },

        // grupisemo po kupcu
        {
            $group: {
                _id: "$customer.customer_id",
                customer_name: { $first: "$customer.name" },
                customer_country: { $first: "$customer.country" },
                total_spend: { $sum: "$invoice_total" },
                num_invoices: { $sum: 1 }
            }
        },
        { $sort: { total_spend: -1 } },

        // facet - paralelno racunamo ukupan prihod i rangiramo kupce
        {
            $facet: {
                stats: [
                    {
                        $group: {
                            _id: null,
                            grand_total: { $sum: "$total_spend" },
                            total_customers: { $sum: 1 }
                        }
                    }
                ],
                top_customers: [
                    { $limit: 128370 },
                    {
                        $group: {
                            _id: null,
                            top_revenue: { $sum: "$total_spend" },
                            top_count: { $sum: 1 },
                            top_ids: { $push: "$_id" }
                        }
                    }
                ]
            }
        },

        // spajamo stats i top_customers
        {
            $project: {
                grand_total: { $arrayElemAt: ["$stats.grand_total", 0] },
                total_customers: { $arrayElemAt: ["$stats.total_customers", 0] },
                top_revenue: { $arrayElemAt: ["$top_customers.top_revenue", 0] },
                top_count: { $arrayElemAt: ["$top_customers.top_count", 0] },
                top_ids: { $arrayElemAt: ["$top_customers.top_ids", 0] }
            }
        },

        // lookup - dominantna kategorija kod top kupaca
        {
            $lookup: {
                from: "invoices",
                let: { top_ids: "$top_ids" },
                pipeline: [
                    {
                        $match: {
                            $expr: {
                                $and: [
                                    { $in: ["$customer.customer_id", "$$top_ids"] },
                                    { $eq: ["$transaction_type", "Sale"] }
                                ]
                            }
                        }
                    },
                    { $unwind: "$lines" },
                    {
                        $group: {
                            _id: "$lines.category",
                            category_revenue: { $sum: "$lines.line_total" }
                        }
                    },
                    { $sort: { category_revenue: -1 } },
                    { $limit: 3 }
                ],
                as: "top_categories"
            }
        },

        {
            $project: {
                _id: 0,
                total_customers: 1,
                top_10_pct_count: "$top_count",
                grand_total: { $round: ["$grand_total", 2] },
                top_10_pct_revenue: { $round: ["$top_revenue", 2] },
                revenue_share_pct: {
                    $round: [
                        { $multiply: [{ $divide: ["$top_revenue", "$grand_total"] }, 100] },
                        2
                    ]
                },
                top_categories: 1
            }
        }
    ],
    { allowDiskUse: true }
)


// UPIT 4
// za svaki pol, pronaci top 3 velicine proizvoda
// po broju prodatih komada, sa procentualnim udelom u ukupnim kupovinama tog pola

db.getCollection("invoices").aggregate(
    [
        {
            $match: {
                transaction_type: "Sale",
                "customer.gender": { $in: ["M", "F"] }
            }
        },

        // $unwind - razvijamo linije proizvoda
        { $unwind: "$lines" },

        {
            $group: {
                _id: {
                    gender: "$customer.gender",
                    size: "$lines.size"
                },
                count: { $sum: "$lines.quantity" },
                total_revenue: { $sum: "$lines.line_total" }
            }
        },

        {
            $sort: {
                "_id.gender": 1,
                count: -1
            }
        },

        {
            $group: {
                _id: "$_id.gender",
                total_count: { $sum: "$count" },
                sizes: {
                    $push: {
                        size: "$_id.size",
                        count: "$count",
                        total_revenue: "$total_revenue"
                    }
                }
            }
        },

        {
            $project: {
                _id: 0,
                gender: "$_id",
                total_count: 1,
                top3: { $slice: ["$sizes", 3] }
            }
        },

        { $unwind: "$top3" },

        {
            $project: {
                gender: 1,
                size: "$top3.size",
                count: "$top3.count",
                total_revenue: { $round: ["$top3.total_revenue", 2] },
                pct_of_gender_purchases: {
                    $round: [
                        { $multiply: [{ $divide: ["$top3.count", "$total_count"] }, 100] },
                        2
                    ]
                }
            }
        },

        { $sort: { gender: 1, count: -1 } }
    ],
    { allowDiskUse: true }
)


// UPIT 5
// pronaci top 5 najprodavanijih proizvoda globalno po prihodu
// za svaki proizvod prikazati prihod po drzavi i da li se nalazi u top 5 u tom drzavi

db.getCollection("invoices").aggregate(
    [
        {
            $match: { transaction_type: "Sale" }
        },
        {
            $unwind: "$lines"
        },
        {
            $lookup: {
                from: "stores",
                localField: "store_id",
                foreignField: "_id",
                as: "store"
            }
        },
        {
            $unwind: "$store"
        },
        {
            $group: {
                _id: {
                    product_id: "$lines.product_id",
                    subcategory: "$lines.subcategory",
                    region: "$store.country"
                },
                revenue: { $sum: "$lines.line_total" },
                quantity: { $sum: "$lines.quantity" }
            }
        },
        {
            $group: {
                _id: {
                    product_id: "$_id.product_id",
                    subcategory: "$_id.subcategory"
                },
                global_revenue: { $sum: "$revenue" },
                global_quantity: { $sum: "$quantity" },
                by_region: {
                    $push: {
                        region: "$_id.region",
                        revenue: "$revenue",
                        quantity: "$quantity"
                    }
                }
            }
        },
        {
            $sort: { global_revenue: -1 }
        },
        {
            $limit: 5
        },
        {
            $project: {
                _id: 0,
                product_id: "$_id.product_id",
                subcategory: "$_id.subcategory",
                global_revenue: { $round: ["$global_revenue", 2] },
                global_quantity: 1,
                by_region: 1
            }
        }
    ],
    { allowDiskUse: true }
)