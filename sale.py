import struct
import os
from datetime import date
from prettytable import PrettyTable

SALE_STRUCT = '10s10s10sffi'
RECORD_SIZE = struct.calcsize(SALE_STRUCT)

def get_last_sale_id():
    try:
        if not os.path.exists('sale.dat'):
            return 0

        filesize = os.path.getsize('sale.dat')
        if filesize == 0:
            return 0

        with open('sale.dat', 'rb') as f:
            f.seek(filesize - RECORD_SIZE)
            data = f.read(RECORD_SIZE)
            record = struct.unpack(SALE_STRUCT, data)
            sale_id_raw = record[0].decode(errors='ignore').strip('\x00')
            if sale_id_raw.startswith('s'):
                return int(sale_id_raw[1:])
            return 0
    except Exception as e:
        print(f"Error : {e}")

def check_cust(cust_name):
    c_name = cust_name
    try:
        with open('customer.dat','rb') as file:
            while True:
                data = file.read(struct.calcsize('10s50s10si'))
                if not data:
                    break
                cust = struct.unpack('10s50s10si',data)
                id = (cust[0].decode().strip('\x00'))
                name = (cust[1].decode().strip('\x00'))
                if name == c_name:
                    return id
    except FileNotFoundError:
        print("Error: customer.dat not found.")
    except struct.error as e:
        print("Struct unpack error in customer.dat:", e)
    except Exception as e:
        print("Unexpected error in check_cust:", e)
    return False

        
s_id = 0
def sale():
    try:
        while True:
            cust_name = input('Enter Customer name : ').lower()
            cust_id = check_cust(cust_name)
            if cust_id:
                break
            else:
                print("Customer not found, please try again.")

        last_id = get_last_sale_id()
        new_id = last_id + 1
        sale_id = 's'+str(new_id).zfill(3)
        cust = cust_id
        sale_date = str(date.today())
        total_price = 0.0
        total_discount = 0.0
        status = 0

        while True:
            # --- ตรวจสอบ product id ---
            while True:
                pro_id = input('Enter Product Id : ').upper()
                if pro_id.strip() == "":
                    print("Product ID cannot be empty.")
                    continue
                sale_price, discount = sale_detail(pro_id, None, sale_id, check_only=True)
                if sale_price is not None:  
                    break
                else:
                    print("Product not found, try again.")

            # --- ตรวจสอบ amount ---
            while True:
                try:
                    amount = int(input('Enter amount of product : '))
                    if amount > 0:
                        break
                    else:
                        print("Amount must be greater than 0.")
                except ValueError:
                    print("Invalid input! Amount must be a number.")

            # เรียก sale_detail จริง
            sale_price, discount = sale_detail(pro_id, amount, sale_id)
            total_price += sale_price
            total_discount += discount
            net_price = total_price - total_discount

            more = input("Do you want to add another product? (y/n): ").lower()
            if more != 'y':
                break

        try:
            with open('sale.dat','ab') as sale_file :
                data = struct.pack('10s10s10sffi',
                                   sale_id.encode(),
                                   cust.encode(),
                                   sale_date.encode(),
                                   net_price,
                                   total_discount,
                                   status)
                sale_file.write(data)
        except Exception as e:
            print("Error writing to sale.dat:", e)

    except Exception as e:
        print("Unexpected error in sale():", e)


def sale_detail(pro_id, amount, sale_id, check_only=False):
    try:
        record_size = struct.calcsize('13s20sffi12si')
        products = []
        found = False

        # อ่าน product ทั้งหมด
        with open('product.dat', 'rb') as file:
            while True:
                data = file.read(record_size)
                if not data:
                    break
                record = list(struct.unpack('13s20sffi12si', data))
                products.append(record)

        # หา product ที่ต้องการ
        for record in products:
            id = record[0].decode().strip('\x00')
            if id == pro_id:
                if check_only:
                    return 0.0, 0.0  

                price = record[3]
                pro_amount = record[4]

                if amount > pro_amount:
                    print(f"Stock not enough! Available: {pro_amount}")
                    return 0.0, 0.0

                sale_price = price * float(amount)
                print('Sale Price of Product : ', sale_price)

                # --- ตรวจสอบ discount ---
                while True:
                    try:
                        discount = float(input('Enter discount : '))
                        if 0 <= discount <= sale_price:
                            break
                        else:
                            print("Discount must be between 0 and sale price.")
                    except ValueError:
                        print("Invalid discount, please enter a number.")

                # บันทึกลง sale_detail.dat
                with open('sale_detail.dat','ab') as file2:
                    data = struct.pack('10s13siff',sale_id.encode(),pro_id.encode(),amount,sale_price,discount)
                    file2.write(data)

                # อัปเดต stock
                record[4] = pro_amount - amount

                if record[4] == 0:
                    record[6] = 2

                found = True
                break

        # เขียนไฟล์ product.dat ใหม่ถ้าเจอ
        if found:
            with open('product.dat','wb') as file:
                for record in products:
                    data = struct.pack('13s20sffi12si',record[0],record[1],record[2],record[3],record[4],record[5],record[6])
                    file.write(data)
            return sale_price, discount
        else:
            if not check_only:
                print(f"Product ID {pro_id} not found.")
            return None, None if check_only else (0.0, 0.0)

    except FileNotFoundError:
        print("product.dat not found.")
        return None, None if check_only else (0.0, 0.0)
    except struct.error as e:
        print("Struct packing/unpacking error:", e)
        return None, None if check_only else (0.0, 0.0)
    except Exception as e:
        print("Unexpected error:", e)
        return None, None if check_only else (0.0, 0.0)



# ========================delete sale=========================

# กำหนดไฟล์และ struct format
SALE_FILE = "sale.dat"
SALE_DETAIL_FILE = "sale_detail.dat"
PRODUCT_FILE = "product.dat"

sale_format = "10s10s10sffi"       
sale_size = struct.calcsize(sale_format)

sale_detail_format = "10s13siff" 
sale_detail_size = struct.calcsize(sale_detail_format)

product_format = "13s20sffi12si"   
product_size = struct.calcsize(product_format)


# --- ฟังก์ชันช่วยอ่าน/เขียน sale และ sale_detail ---
def unpack_sale(data):
    r = struct.unpack(sale_format, data)
    return {
        "sale_id": r[0].decode().strip("\x00"),
        "cust_id": r[1].decode().strip("\x00"),
        "sale_date": r[2].decode().strip("\x00"),
        "net_price": r[3],
        "total_discount": r[4],
        "status": r[5]
    }

def unpack_sale_detail(data):
    r = struct.unpack(sale_detail_format, data)
    return {
        "sale_id": r[0].decode().strip("\x00"),
        "pro_id": r[1].decode().strip("\x00"),
        "amount": r[2],
        "sale_price": r[3],
        "discount": r[4]
    }

def load_products():
    products = {}
    try:
        with open(PRODUCT_FILE, "rb") as f:
            while True:
                data = f.read(product_size)
                if not data:
                    break
                r = struct.unpack(product_format, data)
                products[r[0].decode().strip("\x00")] = {
                    "Pro_id": r[0],
                    "Pro_name": r[1],
                    "Pro_cost": r[2],
                    "Pro_salePrice": r[3],
                    "Pro_amount": r[4],
                    "Category": r[5],
                    "Pro_status": r[6]
                }
    except FileNotFoundError:
        pass
    return products

def save_all_products(products):
    with open(PRODUCT_FILE, "wb") as f:
        for p in products.values():
            f.write(struct.pack(product_format,
                                p["Pro_id"],
                                p["Pro_name"],
                                p["Pro_cost"],
                                p["Pro_salePrice"],
                                p["Pro_amount"],
                                p["Category"],
                                p["Pro_status"]))


# --- delete_sale() ---
def delete_sale():
    try:
          # -------------------- โหลดข้อมูลลูกค้า --------------------
        customers = {}
        if os.path.exists("customer.dat"):
            CUSTOMER_STRUCT_FMT = '10s50s10sI'
            CUSTOMER_RECORD_SIZE = struct.calcsize(CUSTOMER_STRUCT_FMT)
            with open("customer.dat", "rb") as cf:
                while True:
                    data = cf.read(CUSTOMER_RECORD_SIZE)
                    if not data: break
                    if len(data) != CUSTOMER_RECORD_SIZE: continue
                    r = struct.unpack(CUSTOMER_STRUCT_FMT, data)
                    cust_id = r[0].decode(errors="ignore").strip("\x00").strip()
                    cust_name = r[1].decode(errors="ignore").strip("\x00").strip()
                    customers[cust_id] = cust_name

        # -------------------- โหลดข้อมูลสินค้า --------------------
        products = {}
        if os.path.exists("product.dat"):
            PRODUCT_STRUCT_FMT = "13s20sffi12si"
            PRODUCT_RECORD_SIZE = struct.calcsize(PRODUCT_STRUCT_FMT)
            with open("product.dat", "rb") as pf:
                while True:
                    data = pf.read(PRODUCT_RECORD_SIZE)
                    if not data: break
                    if len(data) != PRODUCT_RECORD_SIZE: continue
                    r = struct.unpack(PRODUCT_STRUCT_FMT, data)
                    pro_id = r[0].decode(errors="ignore").strip("\x00").strip()
                    pro_name = r[1].decode(errors="ignore").strip("\x00").strip()
                    products[pro_id] = pro_name

        # เลือกวันที่
        date_input = input("Enter sale date to display (YYYY-MM-DD): ").strip()

        # โหลด sale ทั้งหมด
        sales = []
        with open(SALE_FILE, "rb") as f:
            while True:
                data = f.read(sale_size)
                if not data:
                    break
                s = unpack_sale(data)
                if s["sale_date"] == date_input:
                    sales.append(s)

        if not sales:
            print(f"No sales found on {date_input}")
            return

        # แสดง sale table
        table_sale = PrettyTable()
        table_sale.field_names = ["Sale ID", "Customer name", "Date", "Net Price", "Total Discount", "Status"]
        for s in sales:
            table_sale.add_row([s["sale_id"], cust_name, s["sale_date"], s["net_price"], s["total_discount"], s["status"]])
        print("\n=== Sales ===")
        print(table_sale)

        # เลือก sale_id
        while True:
            sale_id = input("Enter Sale ID to delete: ").strip()
            if any(s["sale_id"] == sale_id for s in sales):
                break
            print("Sale ID not found. Try again.")

        # เลือกว่าจะลบทั้ง sale หรือสินค้าเฉพาะ
        while True:
            choice = input("Delete entire sale (1) or delete product from sale_detail (2)? : ").strip()
            if choice in ["1","2"]:
                break
            print("Invalid choice, enter 1 or 2.")

        if choice == "1":
            # ลบทั้ง sale + sale_detail
            # sale_detail
            new_details = []
            with open(SALE_DETAIL_FILE, "rb") as f:
                while True:
                    data = f.read(sale_detail_size)
                    if not data:
                        break
                    d = unpack_sale_detail(data)
                    if d["sale_id"] != sale_id:
                        new_details.append(data)
                    else:
                        # คืนสินค้าเข้า stock
                        products = load_products()
                        if d["pro_id"] in products:
                            products[d["pro_id"]]["Pro_amount"] += d["amount"]
                        save_all_products(products)
            with open(SALE_DETAIL_FILE, "wb") as f:
                for d in new_details:
                    f.write(d)

            # ลบ sale
            new_sales = []
            with open(SALE_FILE, "rb") as f:
                while True:
                    data = f.read(sale_size)
                    if not data:
                        break
                    s = unpack_sale(data)
                    if s["sale_id"] != sale_id:
                        new_sales.append(data)
            with open(SALE_FILE, "wb") as f:
                for d in new_sales:
                    f.write(d)

            print(f"Deleted entire sale {sale_id} and returned products to stock.")

        elif choice == "2":
            # delete product from sale_detail
            while True:
                # แสดง sale_detail ของ sale_id
                details = []
                with open(SALE_DETAIL_FILE, "rb") as f:
                    while True:
                        data = f.read(sale_detail_size)
                        if not data:
                            break
                        d = unpack_sale_detail(data)
                        if d["sale_id"] == sale_id:
                            details.append(d)
                if not details:
                    print("No sale_detail found for this sale_id.")
                    continue  # กลับไปเลือก choice ใหม่

                table_detail = PrettyTable()
                table_detail.field_names = ["Product ID","Product Name", "Amount", "Sale Price", "Discount"]
                for d in details:
                    pro_name = products.get(d["pro_id"],"-")
                    table_detail.add_row([d["pro_id"],pro_name, d["amount"], d["sale_price"], d["discount"]])
                print("\n=== Sale Details ===")
                print(table_detail)

                # เลือก product_id
                while True:
                    pro_id = input("Enter Product ID to delete from sale_detail: ").strip()
                    target_detail = next((d for d in details if d["pro_id"] == pro_id), None)
                    if target_detail:
                        break
                    print(f"Product ID {pro_id} not found in sale_detail. Try again.")

                # กรอกจำนวนที่จะลบ
                while True:
                    try:
                        del_amount = int(input(f"Enter amount to delete (max {target_detail['amount']}): "))
                        if 0 < del_amount <= target_detail["amount"]:
                            break
                        else:
                            print("Invalid amount, try again.")
                    except ValueError:
                        print("Please enter a valid number.")

                # ปรับ sale_detail และคืนสินค้าเข้า product
                products = load_products()
                new_details_data = []
                updated_details = []

                with open(SALE_DETAIL_FILE, "rb") as f:
                    while True:
                        data = f.read(sale_detail_size)
                        if not data:
                            break
                        d = unpack_sale_detail(data)
                        if d["sale_id"] == sale_id and d["pro_id"] == pro_id:
                            # คืน stock
                            if d["pro_id"] in products:
                                products[d["pro_id"]]["Pro_amount"] += del_amount
                            save_all_products(products)

                            if del_amount < d["amount"]:
                                ratio = (d["amount"] - del_amount)/d["amount"]
                                d["amount"] -= del_amount
                                d["sale_price"] *= ratio
                                d["discount"] *= ratio
                                updated_details.append(d)
                                data = struct.pack(sale_detail_format, d["sale_id"].encode(),
                                                   d["pro_id"].encode(), d["amount"], d["sale_price"], d["discount"])
                                new_details_data.append(data)
                            # ถ้าลบทั้งหมด ไม่เขียนกลับ
                        else:
                            new_details_data.append(data)
                            updated_details.append(d)

                # เขียน sale_detail ใหม่
                with open(SALE_DETAIL_FILE, "wb") as f:
                    for d in new_details_data:
                        f.write(d)

                # ปรับ net_price และ total_discount ของ sale
                total_net = sum(d["sale_price"] for d in updated_details if d["sale_id"] == sale_id)
                total_disc = sum(d["discount"] for d in updated_details if d["sale_id"] == sale_id)

                sales_data_all = []
                with open(SALE_FILE, "rb") as f:
                    while True:
                        data = f.read(sale_size)
                        if not data:
                            break
                        s = unpack_sale(data)
                        if s["sale_id"] == sale_id:
                            s["net_price"] = total_net
                            s["total_discount"] = total_disc
                            data = struct.pack(
                                sale_format,
                                s["sale_id"].encode(),
                                s["cust_id"].encode(),
                                s["sale_date"].encode(),
                                s["net_price"],
                                s["total_discount"],
                                s["status"]
                            )
                        sales_data_all.append(data)

                with open(SALE_FILE, "wb") as f:
                    for d in sales_data_all:
                        f.write(d)

                print(f"Updated Sale {sale_id} after removing {del_amount} of {pro_id} and returned to stock.")
                break

    except Exception as e:
        print("Unexpected error in delete_sale():", e)





