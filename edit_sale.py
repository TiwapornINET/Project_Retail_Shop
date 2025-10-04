import struct
from datetime import date
from prettytable import PrettyTable
import os

SALE_FILE = "sale.dat"
SALE_DETAIL_FILE = "sale_detail.dat"
PRODUCT_FILE = "product.dat"
CUSTOMER_FILE = "customer.dat"

# Struct format
SALE_STRUCT = "10s10s10sffi"  # sale_id, cust_id, sale_date, net_price, total_discount, sale_status
SALE_DETAIL_STRUCT = "10s13siff"  # sale_id, pro_id, amount, sale_price, discount
PRODUCT_STRUCT = "13s20sffi12si"
CUSTOMER_STRUCT = "10s50s10si"  # pro_id, pro_name, pro_cost, pro_salePrice, pro_amount, category, status

# Helper functions to pack/unpack
def pack_sale(record):
    return struct.pack(SALE_STRUCT, record["sale_id"].encode(), record["cust_id"].encode(),
                       record["sale_date"].encode(), record["net_price"], record["total_discount"], record["sale_status"])

def unpack_sale(data):
    r = struct.unpack(SALE_STRUCT, data)
    return {
        "sale_id": r[0].decode().strip('\x00'),
        "cust_id": r[1].decode().strip('\x00'),
        "sale_date": r[2].decode().strip('\x00'),
        "net_price": r[3],
        "total_discount": r[4],
        "sale_status": r[5]
    }

def pack_sale_detail(record):
    return struct.pack(SALE_DETAIL_STRUCT, record["sale_id"].encode(), record["pro_id"].encode(),
                       record["amount"], record["sale_price"], record["discount"])

def unpack_sale_detail(data):
    r = struct.unpack(SALE_DETAIL_STRUCT, data)
    return {
        "sale_id": r[0].decode().strip('\x00'),
        "pro_id": r[1].decode().strip('\x00'),
        "amount": r[2],
        "sale_price": r[3],
        "discount": r[4]
    }

def pack_product(record):
    return struct.pack(PRODUCT_STRUCT, record[0], record[1], record[2], record[3],
                       record[4], record[5], record[6])

def unpack_product(data):
    r = struct.unpack(PRODUCT_STRUCT, data)
    return {
        "pro_id": r[0].decode().strip('\x00'),
        "pro_name": r[1].decode().strip('\x00'),
        "pro_cost": r[2],
        "pro_salePrice": r[3],
        "pro_amount": r[4],
        "category": r[5].decode().strip('\x00'),
        "status": r[6]
    }

# Load all sale
def load_sales():
    sales = []
    if os.path.exists(SALE_FILE):
        with open(SALE_FILE,"rb") as f:
            while True:
                data = f.read(struct.calcsize(SALE_STRUCT))
                if not data: break
                sales.append(unpack_sale(data))
    return sales

# Load all sale_detail
def load_sale_details():
    details = []
    if os.path.exists(SALE_DETAIL_FILE):
        with open(SALE_DETAIL_FILE,"rb") as f:
            while True:
                data = f.read(struct.calcsize(SALE_DETAIL_STRUCT))
                if not data: break
                details.append(unpack_sale_detail(data))
    return details

# Load all products
def load_products():
    products = {}
    if os.path.exists(PRODUCT_FILE):
        with open(PRODUCT_FILE,"rb") as f:
            while True:
                data = f.read(struct.calcsize(PRODUCT_STRUCT))
                if not data: break
                prod = unpack_product(data)
                products[prod["pro_id"]] = prod
    return products

def load_customers():
    customers = {}
    if os.path.exists(CUSTOMER_FILE):
        record_size = struct.calcsize(CUSTOMER_STRUCT)
        with open(CUSTOMER_FILE, "rb") as f:
            while True:
                data = f.read(record_size)
                if not data:
                    break
                if len(data) != record_size:
                    continue
                r = struct.unpack(CUSTOMER_STRUCT, data)
                cust_id = r[0].decode().strip('\x00')
                cust_name = r[1].decode().strip('\x00')
                customers[cust_id] = cust_name
    return customers

# Save sale
def save_sales(sales):
    with open(SALE_FILE,"wb") as f:
        for s in sales:
            f.write(pack_sale(s))

# Save sale_detail
def save_sale_details(details):
    with open(SALE_DETAIL_FILE,"wb") as f:
        for d in details:
            f.write(pack_sale_detail(d))

# Save products
def save_products(products):
    with open(PRODUCT_FILE,"wb") as f:
        for p in products.values():
            f.write(pack_product((
                p["pro_id"].encode(), p["pro_name"].encode(), p["pro_cost"], p["pro_salePrice"],
                p["pro_amount"], p["category"].encode(), p["status"]
            )))

# Update sale function
def update_sale():
    sales = load_sales()
    details = load_sale_details()
    products = load_products()
    customers = load_customers()

    # --- เลือกวันที่จะแสดง sale ---
    while True:
        sale_date_input = input("Enter sale date to display (YYYY-MM-DD): ").strip()
        if sale_date_input:
            filtered_sales = [s for s in sales if s["sale_date"]==sale_date_input]
            if filtered_sales:
                break
            else:
                print("No sales found on this date.")
        else:
            print("Date cannot be empty.")

    # แสดงตาราง sale
    table = PrettyTable(["sale_id","customer_name","sale_date","net_price","total_discount","sale_status"])
    for s in filtered_sales:
        cust_name = customers.get(s["cust_id"],"-")
        table.add_row([s["sale_id"],cust_name,s["sale_date"],s["net_price"],s["total_discount"],s["sale_status"]])
    print("\n--- Sales ---")
    print(table)

    # เลือก sale_id
    while True:
        sale_id = input("Enter sale_id to update: ").strip()
        sale_record = next((s for s in sales if s["sale_id"]==sale_id), None)
        if sale_record:
            break
        else:
            print("sale_id not found.")

    # --- Update sale fields ---
    new_cust = input(f"Enter new cust_id (leave blank to keep {sale_record['cust_id']}): ").strip()
    if new_cust: sale_record['cust_id'] = new_cust

    new_date = input(f"Enter new sale_date (YYYY-MM-DD, leave blank to keep {sale_record['sale_date']}): ").strip()
    if new_date: sale_record['sale_date'] = new_date

    old_status = sale_record["sale_status"]  # เก็บสถานะเดิมไว้ก่อน
    while True:
        new_status = input(f"Enter sale_status (0=sold,1=canceled, leave blank to keep {sale_record['sale_status']}): ").strip()
        if not new_status:
            break
        if new_status in ("0", "1"):
            sale_record['sale_status'] = int(new_status)
            break
        print("Invalid input, enter 0 or 1.")

    # ✅ ถ้าสถานะเปลี่ยนเป็น 1 (Canceled) จากเดิมไม่ใช่ 1 -> คืนสินค้ากลับสต๊อก
    if sale_record["sale_status"] == 1 and old_status != 1:
        print(f"\nSale {sale_id} canceled — returning products to stock...")
        for d in details:
            if d["sale_id"] == sale_id:
                pro_id = d["pro_id"]
                amount = d["amount"]
                if pro_id in products:
                    old_amount = products[pro_id]["pro_amount"]  # จำนวนเดิมก่อนคืนของ
                    products[pro_id]["pro_amount"] += amount      # คืนของเข้าสต๊อก

                    # ✅ ถ้าก่อนคืนของ สินค้าหมดสต๊อก (old_amount == 0) → เปลี่ยนสถานะเป็น 1
                    if old_amount == 0:
                        products[pro_id]["status"] = 1

                    print(f"  - Returned {amount} of {pro_id} ({products[pro_id]['pro_name']}) to stock.")
        print("All products have been returned to stock.\n")


    # --- Update sale_detail ---
    sale_details = [d for d in details if d["sale_id"]==sale_id]

    while True:
        table_detail = PrettyTable(["product id","product name","amount","sale price","discount"])
        for d in sale_details:
            pro_info = products.get(d["pro_id"]) 
            pro_name = pro_info["pro_name"] if pro_info else "-"  
            table_detail.add_row([d["pro_id"], pro_name, d["amount"], d["sale_price"], d["discount"]])
        print("\n--- Sale Details ---")
        print(table_detail)

        choice = input("Modify existing product (1) or add new product (2) or finish (3): ").strip()
        if choice=="1":
            # เลือก pro_id
            while True:
                pro_id = input("Enter pro_id to modify: ").strip()
                detail = next((d for d in sale_details if d["pro_id"]==pro_id), None)
                if detail: break
                print("pro_id not found in this sale_detail.")

            # จำนวน
            while True:
                amt_input = input(f"Enter new amount (leave blank to keep {detail['amount']}): ").strip()
                if not amt_input: new_amount = detail["amount"]; break
                try:
                    new_amount = int(amt_input)
                    if new_amount>0: break
                    print("Amount must be >0.")
                except:
                    print("Invalid number.")

            # ปรับ stock ใน product
            prod = products[pro_id]
            diff = new_amount - detail["amount"]
            if prod["pro_amount"] - diff <0:
                print(f"Not enough stock to increase amount. Available: {prod['pro_amount']}")
                continue
            prod["pro_amount"] -= diff

            # ปรับ sale_price อัตโนมัติ
            detail["amount"] = new_amount
            detail["sale_price"] = prod["pro_salePrice"] * new_amount

            # discount
            while True:
                disc_input = input(f"Enter discount (leave blank to keep {detail['discount']}): ").strip()
                if not disc_input: break
                try:
                    detail["discount"] = float(disc_input)
                    break
                except:
                    print("Invalid discount")

        elif choice=="2":
            # เพิ่มสินค้าใหม่
            while True:
                new_pro_id = input("Enter new pro_id to add: ").strip()
                if new_pro_id in [d["pro_id"] for d in sale_details]:
                    print("Product already in sale_detail.")
                    continue
                if new_pro_id in products:
                    prod = products[new_pro_id]
                    break
                print("pro_id not found in products.")

            # จำนวน
            while True:
                try:
                    amt = int(input(f"Enter amount of {new_pro_id}: "))
                    if amt>0 and amt <= prod["pro_amount"]:
                        break
                    print(f"Amount must be 1-{prod['pro_amount']}")
                except:
                    print("Invalid number.")

            # discount
            while True:
                try:
                    disc = float(input("Enter discount: "))
                    break
                except:
                    print("Invalid discount.")

            # เพิ่มใน sale_detail
            sale_details.append({
                "sale_id": sale_id,
                "pro_id": new_pro_id,
                "amount": amt,
                "sale_price": prod["pro_salePrice"]*amt,
                "discount": disc
            })
            prod["pro_amount"] -= amt

        elif choice=="3":
            break
        else:
            print("Invalid choice, enter 1,2,3.")

    # ปรับ net_price และ total_discount
    sale_record["net_price"] = sum(d["sale_price"] for d in sale_details)
    sale_record["total_discount"] = sum(d["discount"] for d in sale_details)

    # บันทึก
    save_sales(sales)
    save_sale_details([d for d in details if d["sale_id"]!=sale_id]+sale_details)
    save_products(products)
    print("Sale updated successfully.")
