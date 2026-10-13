"""Generates synthetic financial data (CSV) for the Power BI project.
Run from repo root:  python scripts/generate_data.py
"""
import csv, random, datetime as dt
random.seed(42)
OUT = "data/"
start, end = dt.date(2023, 1, 1), dt.date(2024, 12, 31)

def writer(f):
    return csv.writer(f, lineterminator="\n")

# dim_date
with open(OUT + "dim_date.csv", "w", newline="") as f:
    w = writer(f)
    w.writerow(["date_key","full_date","year","quarter","month_num","month_name","period","day_name","is_weekend"])
    d = start
    while d <= end:
        w.writerow([int(d.strftime("%Y%m%d")), d, d.year, (d.month-1)//3+1, d.month,
                    d.strftime("%B"), d.strftime("%Y-%m"), d.strftime("%A"), int(d.weekday() >= 5)])
        d += dt.timedelta(days=1)

# dim_category
cats = [(1,"Product Sales","Revenue"),(2,"Service Fees","Revenue"),(3,"Subscriptions","Revenue"),
        (4,"Interest Income","Revenue"),(5,"Salaries","Expense"),(6,"Marketing","Expense"),
        (7,"Operations","Expense"),(8,"Rent","Expense"),(9,"Software","Expense"),(10,"Travel","Expense")]
with open(OUT + "dim_category.csv", "w", newline="") as f:
    w = writer(f); w.writerow(["category_id","category_name","category_type"]); w.writerows(cats)

# dim_customer
first = ["Aarav","Vivaan","Aditya","Ishaan","Kabir","Riya","Anaya","Diya","Meera","Saanvi","Rohan","Arjun","Kavya","Neha","Tanvi"]
last = ["Sharma","Verma","Thakur","Negi","Kapoor","Mehta","Reddy","Nair","Singh","Gupta","Chauhan","Bisht"]
segs = ["Retail","SME","Corporate"]; regs = ["North","South","East","West"]
cust = []
with open(OUT + "dim_customer.csv", "w", newline="") as f:
    w = writer(f); w.writerow(["customer_id","customer_name","segment","region","join_date"])
    for i in range(1, 201):
        row = [i, f"{random.choice(first)} {random.choice(last)}", random.choices(segs,[5,3,2])[0],
               random.choice(regs), start + dt.timedelta(days=random.randint(-400, 300))]
        cust.append(row); w.writerow(row)

# fact_transactions
modes = ["UPI","Card","Net Banking","Bank Transfer","Cash"]
rev_rng = {1:(800,9000),2:(300,4000),3:(200,1500),4:(100,2500)}
exp_rng = {5:(20000,45000),6:(1500,9000),7:(1000,7000),8:(20000,35000),9:(800,4500),10:(500,3500)}
NULL = r"\N"
with open(OUT + "fact_transactions.csv", "w", newline="") as f:
    w = writer(f)
    w.writerow(["transaction_id","date_key","customer_id","category_id","region","amount","payment_mode","status"])
    tid = 1; d = start
    while d <= end:
        months = (d.year-2023)*12 + d.month - 1
        growth = 1 + 0.015*months
        egrowth = 1 + 0.008*months
        season = 1.25 if d.month in (10,11,12,3) else 1.0
        key = d.strftime("%Y%m%d")
        # revenue transactions
        for _ in range(max(1, int(random.gauss(7, 2) * season))):
            c = random.choices([1,2,3,4], [45,30,18,7])[0]
            lo, hi = rev_rng[c]
            cu = random.choice(cust)
            status = random.choices(["Completed","Pending","Failed"], [92,4,4])[0]
            w.writerow([tid, key, cu[0], c, cu[3], round(random.uniform(lo,hi)*growth,2),
                        random.choice(modes), status]); tid += 1
        # monthly fixed costs: payroll + rent
        if d.day == 1:
            for c, n in ((5, 5), (8, 2)):
                for _ in range(n):
                    lo, hi = exp_rng[c]
                    w.writerow([tid, key, NULL, c, random.choice(regs), round(random.uniform(lo,hi)*egrowth,2),
                                "Bank Transfer", "Completed"]); tid += 1
        # daily variable costs
        for _ in range(random.choice([1,2,2,3])):
            c = random.choices([6,7,9,10],[30,30,25,15])[0]
            lo, hi = exp_rng[c]
            w.writerow([tid, key, NULL, c, random.choice(regs), round(random.uniform(lo,hi)*egrowth,2),
                        random.choice(["Bank Transfer","Card","Net Banking"]), "Completed"]); tid += 1
        d += dt.timedelta(days=1)
print("Done. Rows in fact_transactions:", tid-1)
