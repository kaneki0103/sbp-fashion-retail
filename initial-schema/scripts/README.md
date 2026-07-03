# Uputstvo za Pokretanje Projekta

## 1. Preduslovi

Pre pokretanja skripti, potrebno je obezbediti podatke i instalirati potrebne Python biblioteke.

### Podaci

Potrebne CSV datoteke možete preuzeti sa sledećeg linka: [Global Fashion Retail Stores Dataset na Kaggle-u](https://www.kaggle.com/datasets/ricgomes/global-fashion-retail-stores-dataset?select=products.csv)

Sve preuzete `.csv` datoteke smestite u folder `data` unutar foldera `scripts` (isti direktorijum u kojem se nalaze ovaj `README.md` i `import_data.py`). Ukoliko folder `data` ne postoji (npr. jer je prazan pa nije komitovan na Git-u), potrebno je da ga sami napravite:

```
mkdir data
```

i tek onda u njega smestite preuzete `.csv` fajlove.

### Potrebne biblioteke

**Pandas**
```
pip install pandas
```

**PyMongo**
```
pip install pymongo
```

**Os**

Ova biblioteka je deo standardne Python instalacije i nije je potrebno dodatno instalirati.

## 2. Struktura Direktorijuma

Primer preporučene strukture direktorijuma (folder `scripts`):

```
scripts/
├── README.md
├── import_data.py
└── data/
    ├── customers.csv
    ├── discounts.csv
    ├── employees.csv
    ├── inventory.csv
    ├── products.csv
    ├── sales.csv
    ├── stores.csv
    └── transactions.csv
```

> Napomena: nazivi CSV fajlova zavise od onih koje preuzmete sa Kaggle-a — smestite ih sve u `data` folder unutar `scripts`.

## 3. Koraci za Pokretanje

Pratite sledeće korake po navedenom redosledu:

1. Pozicionirajte se u folder `scripts`:

```
cd scripts
```

2. Ukoliko folder `data` ne postoji, napravite ga:

```
mkdir data
```

3. Uverite se da su preuzeti `.csv` fajlovi smešteni u folder `data`.

4. Pokrenite glavnu skriptu koja će učitati i obraditi podatke i popuniti bazu podataka.

```
python import_data.py
```
