import struct
from datetime import datetime
from tabulate import tabulate
from prettytable import PrettyTable
import os

LOG_FILE = "product_change.bin"
# ฟอร์แมต struct ของ log
LOG_STRUCT_FMT = "19si13s20sffi12si20s"
LOG_RECORD_SIZE = struct.calcsize(LOG_STRUCT_FMT)

# ฟอร์แมต struct ของ sale.dat
SALE_STRUCT_FMT = "10s10s10sffi"
SALE_RECORD_SIZE = struct.calcsize(SALE_STRUCT_FMT)

def unpack_log(data: bytes):
    """แปลง binary log record -> dict"""
    try:
        r = struct.unpack(LOG_STRUCT_FMT, data)
    except struct.error:
        return None

    ts_raw = r[0].decode().strip("\x00")
    op_code = r[1]
    pro_id = r[2].decode().strip("\x00")
    pro_name = r[3].decode().strip("\x00")
    pro_cost = r[4]
    pro_sale = r[5]
    pro_amount = r[6]
    category = r[7].decode().strip("\x00")
    pro_status = r[8]
    user = r[9].decode().strip("\x00")

    ts_dt = None
    try:
        ts_dt = datetime.strptime(ts_raw.replace("_", " "), "%Y-%m-%d %H:%M:%S")
    except Exception:
        ts_dt = None

    return {
        "ts": ts_raw,
        "ts_dt": ts_dt,
        "op_code": op_code,
        "Pro_id": pro_id,
        "Pro_name": pro_name,
        "Pro_cost": pro_cost,
        "Pro_salePrice": pro_sale,
        "Pro_amount": pro_amount,
        "Category": category,
        "Pro_status": pro_status,
        "User": user
    }

def generate_report():
    try:
        # ------------------ อ่าน product.dat ------------------
        table = PrettyTable()
        table.field_names = ["ID", "Name", "Cost", "Sale Price", "Amount", "Category", "Status"]

        status_counter = {1: 0, 2: 0, 3: 0}
        category_counter = {}
        sold_out_products = []

        if not os.path.exists("product.dat"):
            print("not found product.dat")
            return

        with open("product.dat", "rb") as f:
            record_size = struct.calcsize('13s20sffi12si')
            while True:
                data = f.read(record_size)
                if not data:
                    break
                record = struct.unpack('13s20sffi12si', data)
                pro_id = record[0].decode().strip("\x00")
                pro_name = record[1].decode().strip("\x00")
                pro_cost = record[2]
                sale_price = record[3]
                amount = record[4]
                category = record[5].decode().strip("\x00")
                status = record[6]
                table.add_row([pro_id, pro_name, pro_cost, sale_price, amount, category, status])

                # สรุป Status
                if status in status_counter:
                    status_counter[status] += 1
                # สรุป Category
                category_counter[category] = category_counter.get(category, 0) + amount
                # สินค้าหมด
                if status == 2:
                    sold_out_products.append(pro_name)

        # ------------------ อ่าน product_change.bin ------------------
        logs_today = []
        action_counter = {1:0, 2:0, 3:0, 4:0}  # นับ Action

        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "rb") as lf:
                while True:
                    data = lf.read(LOG_RECORD_SIZE)
                    if not data:
                        break
                    log = unpack_log(data)
                    if log and log["ts_dt"] and log["ts_dt"].date() == datetime.now().date():
                        logs_today.append(log)
                        action_counter[log["op_code"]] = action_counter.get(log["op_code"], 0) + 1

        # ------------------ อ่าน sale.dat ------------------
        today_sales = []

        if os.path.exists("sale.dat"):
            with open("sale.dat", "rb") as sf:
                while True:
                    data = sf.read(SALE_RECORD_SIZE)
                    if not data:
                        break
                    r = struct.unpack(SALE_STRUCT_FMT, data)
                    sale_id = r[0].decode().strip("\x00")
                    cust_id = r[1].decode().strip("\x00")
                    sale_date_str = r[2].decode().strip("\x00")
                    net_price = r[3]
                    net_discount = r[4]
                    sale_status = r[5]

                    try:
                        sale_dt = datetime.strptime(sale_date_str, "%Y-%m-%d")
                    except:
                        continue

                    if sale_dt.date() == datetime.now().date() and sale_status != 1:
                        today_sales.append({
                            "sale_id": sale_id,
                            "cust_id": cust_id,
                            "net_price": net_price,
                            "net_discount": net_discount
                        })

        total_sales = sum(s['net_price'] for s in today_sales) if today_sales else 0
        max_sale = max(today_sales, key=lambda x: x['net_price']) if today_sales else None
        min_sale = min(today_sales, key=lambda x: x['net_price']) if today_sales else None

        # ------------------ สร้าง PrettyTable ------------------
        status_table = PrettyTable(["Status", "Meaning", "Count"])
        status_meaning = {1: "sale", 2: "sale out", 3: "cancle"}
        for k,v in status_counter.items():
            status_table.add_row([k, status_meaning.get(k,"Unknown"), v])

        category_table = PrettyTable(["Category", "Total Amount"])
        for k,v in category_counter.items():
            category_table.add_row([k,v])

        action_table = PrettyTable(["Action","Count"])
        action_meaning = {1:"ADD",2:"UPDATE",3:"DELETE",4:"VIEW"}
        for k,v in action_counter.items():
            action_table.add_row([action_meaning.get(k,"Unknown"), v])

        sale_table = PrettyTable(["Info","Value"])
        sale_table.add_row(["Total net sales today", total_sales])
        if max_sale:
            sale_table.add_row(["The most expensive bill", f"{max_sale['sale_id']} : {max_sale['net_price']}"])
        if min_sale:
            sale_table.add_row(["The cheapest bill", f"{min_sale['sale_id']} : {min_sale['net_price']}"])

        # ------------------ แสดงผล Terminal ------------------
        print("\n Product list")
        print(table)
        print("\n Product Status Summary")
        print(status_table)
        print("\n Product category summary")
        print(category_table)
        print("\n Out of stock")
        if sold_out_products:
            for name in sold_out_products:
                print("-", name)
        else:
            print("No products are out of stock.")
        print("\n=== Product Changes (Today) ===")
        print(action_table)
        print("\n Today's sales report")
        print(sale_table)

        # ------------------ เขียนลงไฟล์ ------------------
        with open("Generate_report.txt","w",encoding="utf-8") as report_file:
            report_file.write(f"\n\nRetail Shop System\n")
            report_file.write(f"\n\nGenerate At : {datetime.now()}\n")
            report_file.write(" Product list\n")
            report_file.write(str(table))
            report_file.write("\n\n Product Status Summary\n")
            report_file.write(str(status_table))
            report_file.write("\n\n Product category summary\n")
            report_file.write(str(category_table))
            report_file.write("\n\n Out of stock\n")
            if sold_out_products:
                for name in sold_out_products:
                    report_file.write(f"- {name}\n")
            else:
                report_file.write("No products are out of stock.\n")
            report_file.write("\n\n=== Product Changes (Today) ===\n")
            report_file.write(str(action_table))
            report_file.write("\n\n Today's sales report\n")
            report_file.write(str(sale_table))

        print("\n The report has been saved to Generate_report.txt.")

    except Exception as e:
        print(f" Error: {e}")

def Sale_Report():
    import struct
    from datetime import datetime
    from prettytable import PrettyTable
    import os

    SALE_STRUCT_FMT = '10s10s10sffi'
    SALE_RECORD_SIZE = struct.calcsize(SALE_STRUCT_FMT)

    # ฟังก์ชันช่วยแปลง string วันในไฟล์เป็น date object (รองรับหลายรูปแบบ)
    def parse_sale_date(s: str):
        try:
            s = s.strip().strip("\x00").strip()
            if not s:
                return None
            # ลองรูปแบบที่เป็นไปได้
            fmts = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%d%m%Y"]
            for fmt in fmts:
                try:
                    dt = datetime.strptime(s, fmt)
                    # แปลงพ.ศ. ถ้าจับได้ว่าปี > 2500
                    if dt.year > 2500:
                        dt = dt.replace(year=dt.year - 543)
                    return dt.date()
                except Exception:
                    continue
            # ถ้าเป็นแบบไม่มีตัวคั่น (8 หลัก) พยายามแยก DDMMYYYY
            s2 = ''.join(ch for ch in s if ch.isdigit())
            if len(s2) == 8:
                try:
                    day = int(s2[:2]); month = int(s2[2:4]); year = int(s2[4:])
                    if year > 2500:
                        year -= 543
                    return datetime(year, month, day).date()
                except Exception:
                    return None
            return None
        except Exception:
            return None

    while True:
        try:
            raw = input("Enter date to view (DDMMYYYY) or leave empty for today: ").strip()
            # ถ้าไม่ใส่ ให้เป็นวันนี้ (default)
            if raw == "":
                report_date = datetime.now().date()
                print(f"Using date: {report_date.strftime('%d-%m-%Y')} (today)")
            else:
                s = raw.lower()
                if s in ("t", "today", "now"):
                    report_date = datetime.now().date()
                    print(f"Using date: {report_date.strftime('%d-%m-%Y')} (today)")
                else:
                    parsed = None
                    s_digits = ''.join(ch for ch in raw if ch.isdigit())
                    if len(s_digits) == 8:
                        try:
                            day = int(s_digits[:2]); month = int(s_digits[2:4]); year = int(s_digits[4:])
                            if year > 2500: year -= 543
                            parsed = datetime(year, month, day).date()
                        except Exception:
                            parsed = None
                    else:
                        for fmt in ("%d%m%Y","%d-%m-%Y","%d/%m/%Y","%Y-%m-%d","%Y/%m/%d"):
                            try:
                                dt = datetime.strptime(raw, fmt)
                                if dt.year > 2500:
                                    dt = dt.replace(year=dt.year - 543)
                                parsed = dt.date()
                                break
                            except:
                                continue

                    if not parsed:
                        print(" Invalid date format. Use DDMMYYYY or YYYY-MM-DD (blank = today).")
                        continue
                    report_date = parsed
                    print(f"Using date: {report_date.strftime('%d-%m-%Y')}")
        except Exception as e:
            print(f" Error parsing date: {e}")
            continue

        # ตรวจสอบไฟล์
        if not os.path.exists("sale.dat"):
            print(" not found sale.dat")
            return

        sales_today = []
        cancelled_count = 0
        discount_count = 0

        try:
            with open("sale.dat", "rb") as f:
                while True:
                    data = f.read(SALE_RECORD_SIZE)
                    if not data:
                        break
                    if len(data) != SALE_RECORD_SIZE:
                        # record ขนาดไม่ตรง -> ข้าม
                        continue
                    try:
                        r = struct.unpack(SALE_STRUCT_FMT, data)
                    except struct.error:
                        continue

                    try:
                        sale_id = r[0].decode(errors="ignore").strip("\x00").strip()
                        cust_id = r[1].decode(errors="ignore").strip("\x00").strip()
                        sale_date_str = r[2].decode(errors="ignore").strip("\x00").strip()
                        net_price = float(r[3])
                        net_discount = float(r[4])
                        sale_status = int(r[5])
                    except Exception:
                        continue

                    sale_dt = parse_sale_date(sale_date_str)
                    if sale_dt is None:
                        continue

                    if sale_dt == report_date:
                        sales_today.append({
                            "sale_id": sale_id,
                            "cust_id": cust_id,
                            "net_price": net_price,
                            "net_discount": net_discount,
                            "sale_status": sale_status,
                            "sale_dt": sale_dt
                        })
                        if sale_status == 1:
                            cancelled_count += 1
                        if net_discount > 0:
                            discount_count += 1
        except Exception as e:
            print(f" Error reading sale.dat: {e}")
            continue

        if not sales_today:
            print("There was no sales bill that day.")
        else:
            # ตารางบิลขาย
            try:
                table = PrettyTable()
                table.field_names = ["Sale ID", "Customer", "Date", "Net Price", "Discount", "Status"]
                for s in sales_today:
                    status_str = "Cancelled" if s['sale_status'] == 1 else "Normal"
                    table.add_row([
                        s['sale_id'],
                        s['cust_id'],
                        s['sale_dt'].strftime("%d-%m-%Y"),
                        f"{s['net_price']:.2f}",
                        f"{s['net_discount']:.2f}",
                        status_str
                    ])

                print("\n Sales invoice report")
                print(table)

                # สรุปยอดขาย
                non_cancelled_count = sum(1 for s in sales_today if s['sale_status'] != 1)
                total_sales = sum(s['net_price'] for s in sales_today if s['sale_status'] != 1)
                max_sale = max(sales_today, key=lambda x: x['net_price'], default=None)
                min_sale = min(sales_today, key=lambda x: x['net_price'], default=None)
                avg_sale = total_sales / non_cancelled_count if non_cancelled_count > 0 else 0.0

                summary_table = PrettyTable()
                summary_table.field_names = ["Info", "Value"]
                summary_table.add_row(["Total Sales (Net)", f"{total_sales:.2f}"])
                if max_sale: summary_table.add_row(["Max Bill", f"{max_sale['sale_id']} : {max_sale['net_price']:.2f}"])
                if min_sale: summary_table.add_row(["Min Bill", f"{min_sale['sale_id']} : {min_sale['net_price']:.2f}"])
                summary_table.add_row(["Average per Bill", f"{avg_sale:.2f}"])
                summary_table.add_row(["Bills with Discount", discount_count])
                summary_table.add_row(["Cancelled Bills", cancelled_count])

                print("\n Sales summary")
                print(summary_table)
            except Exception as e:
                print(f" Error building report table: {e}")

        # ถามว่าจะออกจากการดูรายงานหรือไม่
        while True:
            try:
                exit_input = input("\nDo you want to exit Sale Report? (Y/N): ").strip().upper()
                if exit_input in ("Y", "N"):
                    break
                else:
                    print("Please enter only Y or N.")
            except Exception as e:
                print(f" Error reading input: {e}")
                continue

        if exit_input == "Y":
            break



def Product_report():
    from prettytable import PrettyTable
    import struct

    # สร้างตารางหลัก
    table = PrettyTable()
    table.field_names = ["ID", "Name", "Cost", "Sale Price", "Amount", "Category", "Status"]

    status_counter = {1:0, 2:0, 3:0}
    category_counter = {}
    sold_out_products = []

    # อ่านไฟล์ product.dat
    try:
        with open("product.dat", "rb") as f:
            record_fmt = "13s20sffi12si"
            record_size = struct.calcsize(record_fmt)

            while True:
                data = f.read(record_size)
                if not data:
                    break
                r = struct.unpack(record_fmt, data)
                pro_id = r[0].decode().strip("\x00")
                pro_name = r[1].decode().strip("\x00")
                pro_cost = r[2]
                pro_sale = r[3]
                pro_amount = r[4]
                category = r[5].decode().strip("\x00")
                status = r[6]

                table.add_row([pro_id, pro_name, pro_cost, pro_sale, pro_amount, category, status])

                # นับสรุป
                if status in status_counter:
                    status_counter[status] += 1
                if category in category_counter:
                    category_counter[category] += pro_amount
                else:
                    category_counter[category] = pro_amount
                if status == 2:
                    sold_out_products.append(pro_name)

        # แสดงผลตาราง
        print(table)

        # แสดงสรุปสถานะ
        status_table = PrettyTable()
        status_table.field_names = ["Status", "Meaning", "Count"]
        status_meaning = {1: "sale", 2: "sale out", 3: "cancle"}
        for key, count in status_counter.items():
            status_table.add_row([key, status_meaning.get(key, "Unknown"), count])
        print("\n Product Status Summary")
        print(status_table)

        # แสดงสรุปประเภทสินค้า
        category_table = PrettyTable()
        category_table.field_names = ["Category", "Total Amount"]
        for cat, total in category_counter.items():
            category_table.add_row([cat, total])
        print("\n Product category summary")
        print(category_table)

        # แสดงสินค้าหมด
        print("\n Out of stock")
        if sold_out_products:
            for name in sold_out_products:
                print("-", name)
        else:
            print("No products are out of stock.")

    except FileNotFoundError:
        print("not found product.dat")

#================================= Report ======================================



# Product format (main data file)
product_format = "13s20sffi12si"   # 7 fields
product_size = struct.calcsize(product_format)

# Log format based on Thai specification document
# ts(15s) + op_code(I) + Pro_id(13s) + Pro_name_after(20s) + Pro_cost_after(f) + Pro_salePrice_after(f) + Pro_amount_after(I) + Category_after(12s) + Pro_status_after(I)
log_format = "19sI13s20sffi12sI20s"
#"19sI13s20sffi12sI" 
  # Timestamp is 15 bytes, not 19
log_size = struct.calcsize(log_format)

# print(f"Product record size: {product_size} bytes")
# print(f"Log record size: {log_size} bytes")

# Constants for better maintainability
OPERATIONS = {1: "ADD", 2: "UPDATE", 3: "DELETE", 4: "VIEW"}
STATUS_NAMES = {1: "Active", 2: "Out of Stock", 3: "Discontinued"}
STATUS_REVERSE = {"Active": 1, "Out of Stock": 2, "Discontinued": 3}

def log_change_binary(op_code, product_data, user="SYSTEM"):
    """
    Log changes with proper binary record formatting
    Ensures each record is exactly the right size for proper separation
    """
    try:
        # Create timestamp - pad to exactly 19 bytes
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 19 characters exactly
        timestamp_bytes = ts.encode('utf-8').ljust(19, b'\x00')[:19]
        
        # Prepare product data - ensure exact byte lengths
        pro_id = str(product_data[0]).encode('utf-8').ljust(13, b'\x00')[:13]
        name_after = str(product_data[1]).encode('utf-8').ljust(20, b'\x00')[:20]
        cost_after = float(product_data[2])
        sale_after = float(product_data[3])
        amount_after = int(product_data[4])
        category_after = str(product_data[5]).encode('utf-8').ljust(12, b'\x00')[:12]
        status_after = int(product_data[6])
        user_bytes = str(user).encode('utf-8').ljust(20, b'\x00')[:20]
        
        # Pack the complete record
        record = struct.pack(log_format, 
                           timestamp_bytes,    # 19 bytes
                           op_code,           # 4 bytes (i)
                           pro_id,            # 13 bytes
                           name_after,        # 20 bytes
                           cost_after,        # 4 bytes (f)
                           sale_after,        # 4 bytes (f)
                           amount_after,      # 4 bytes (i)
                           category_after,    # 12 bytes
                           status_after,      # 4 bytes (i)
                           user_bytes)        # 20 bytes
        
        # Verify the record size is correct
        expected_size = struct.calcsize(log_format)
        if len(record) != expected_size:
            print(f"Warning: Record size mismatch! Expected {expected_size}, got {len(record)}")
            return False
        
        # Write the complete record as one atomic operation
        with open("product_change.bin", "ab") as f:
            f.write(record)
            f.flush()  # Ensure data is written immediately
        
        print(f"Logged: {OPERATIONS.get(op_code, 'UNKNOWN')} product {product_data[0]} by {user} ({len(record)} bytes)")
        return True
        
    except (ValueError, IndexError) as e:
        print(f"Error logging change: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error in logging: {e}")
        return False

def read_all_products():
    """Helper function to read all products from binary file"""
    data = []
    try:
        with open("product.dat", "rb") as f:
            while True:
                chunk = f.read(product_size)
                if not chunk:
                    break
                if len(chunk) < product_size:
                    continue
                record = struct.unpack(product_format, chunk)
                data.append(record)
        return data
    except FileNotFoundError:
        print("Product file not found!")
        return []

def write_all_products(data):
    """Helper function to write all products to binary file"""
    try:
        with open('product.dat', 'wb') as f:
            for record in data:
                binary_record = struct.pack(product_format, *record)
                f.write(binary_record)
        return True
    except Exception as e:
        print(f"Error writing to file: {e}")
        return False

def get_user_input(prompt, current_value=None, data_type=str, required=False):
    """Helper function for user input with validation"""
    while True:
        if current_value is not None:
            user_input = input(f"{prompt} [{current_value}]: ")
            if not user_input:
                return current_value
        else:
            user_input = input(f"{prompt}: ")
            if not user_input and required:
                print(" This field is required!")
                continue
            elif not user_input:
                return None
        
        try:
            if data_type == float:
                value = float(user_input)
                if value < 0:
                    print(" Value cannot be negative!")
                    continue
                return value
            elif data_type == int:
                value = int(user_input)
                if value < 0:
                    print(" Value cannot be negative!")
                    continue
                return value
            else:
                return user_input
        except ValueError:
            print(f" Invalid {data_type.__name__} value!")

def update_product():
    """Update product in binary file with improved validation"""
    data = read_all_products()
    if not data:
        return
    
    user = get_user_input("User", required=True)
    pro_id = get_user_input("Enter Product ID to update", required=True)
    
    # Find and update record
    for i, record in enumerate(data):
        current_id = record[0].decode().strip("\x00")
        if current_id == pro_id:
            # Get current values
            current_name = record[1].decode().strip("\x00")
            current_cost = record[2]
            current_sale = record[3]
            current_amount = record[4]
            current_category = record[5].decode().strip("\x00")
            current_status = record[6]
            
            print(f" Found product: {current_id} - {current_name}")
            print(f"Current status: {STATUS_NAMES.get(current_status, current_status)}")
            
            # Input new values with validation
            name = get_user_input("New Name", current_name)
            cost = get_user_input("New Cost", current_cost, float)
            sale = get_user_input("New Sale Price", current_sale, float)
            amount = get_user_input("New Amount", current_amount, int)
            category = get_user_input("New Category", current_category)
            
            # Status input with validation
            print("\nStatus options: 1=Active, 2=Out of Stock, 3=Discontinued")
            status = get_user_input("New Status", current_status, int)
            if status not in STATUS_NAMES:
                print(" Invalid status! Using current value.")
                status = current_status
            
            # Create updated binary record
            pro_id_bytes = pro_id.encode().ljust(13, b'\x00')
            name_bytes = name.encode().ljust(20, b'\x00')
            category_bytes = category.encode().ljust(12, b'\x00')
            
            updated_record = struct.pack(product_format,
                                       pro_id_bytes, name_bytes, cost, sale,
                                       amount, category_bytes, status)
            
            # Replace the record in data list
            data[i] = struct.unpack(product_format, updated_record)
            
            # Write back to file
            if write_all_products(data):
                # Log the update
                product_data = [pro_id, name, cost, sale, amount, category, status]
                log_change_binary(2, product_data, user)
                print(" Product updated successfully!")
            else:
                print(" Failed to save changes!")
            return
    
    print(" Product ID not found.")

def format_product_record(record):
    """Helper function to format product record for display"""
    decoded_record = (
        record[0].decode().strip("\x00"),
        record[1].decode().strip("\x00"),
        record[2],
        record[3],
        record[4],
        record[5].decode().strip("\x00"),
        record[6]
    )
    
    status_text = STATUS_NAMES.get(decoded_record[6], f"Status {decoded_record[6]}")
    
    return [
        decoded_record[0],   # Pro_id
        decoded_record[1],   # Pro_name
        f"{decoded_record[2]:,.2f}",   # Pro_cost
        f"{decoded_record[3]:,.2f}",   # Pro_salePrice
        f"{decoded_record[4]:,}",      # Pro_amount
        decoded_record[5],   # Category
        status_text  # Pro_status
    ]

def view_products_with_tabulate():
    """View products with improved search and automatic logging"""
    print("\nSearch option:")
    print("1. Specific Product")
    print("2. All Products")
    
    
    try:
        view_choice = int(input("Choose option: "))
    except ValueError:
        print("Invalid choice!")
        return

    # Get user name for logging
    user = get_user_input("User", required=True)

    data = read_all_products()
    if not data:
        return

    formatted_data = [format_product_record(record) for record in data]
    headers = ["Pro_id", "Pro_name", "Pro_cost", "Pro_salePrice", "Pro_amount", "Category", "Pro_status"]

    if view_choice == 1:
        product_id = get_user_input("Enter Product ID", required=True)
        filtered_data = [row for row in formatted_data if row[0] == product_id]
        
        if filtered_data:
            print(f"\n=== Search Result for {product_id} ===")
            print(tabulate(filtered_data, headers=headers, tablefmt="grid"))
            
            # Log the VIEW operation for the specific product
            original_record = next((row for row in formatted_data if row[0] == product_id), None)
            if original_record:
                product_data = [
                    original_record[0],
                    original_record[1],
                    float(original_record[2].replace(',', '')),
                    float(original_record[3].replace(',', '')),
                    int(original_record[4].replace(',', '')),
                    original_record[5],
                    STATUS_REVERSE.get(original_record[6], 1)
                ]
                log_change_binary(4, product_data, user)  # op_code 4 = VIEW
        else:
            print(f"Product ID {product_id} not found!")
            
    elif view_choice == 2:
        print(f"\n=== Product List ({len(formatted_data)} products) ===")
        print(tabulate(formatted_data, headers=headers, tablefmt="grid"))
        
        # Log VIEW operation for all products view - use first product as representative
        if formatted_data:
            first_product = formatted_data[0]
            product_data = [
                first_product[0],
                first_product[1],
                float(first_product[2].replace(',', '')),
                float(first_product[3].replace(',', '')),
                int(first_product[4].replace(',', '')),
                first_product[5],
                STATUS_REVERSE.get(first_product[6], 1)
            ]
            log_change_binary(4, product_data, user)  # Log as VIEW ALL operation
        
    

def view_change_log():
    """View change log with user field support"""
    
    if not os.path.exists("product_change.bin"):
        print(" No change log found!")
        return
    
    # Check file format 
    file_size = os.path.getsize("product_change.bin")
    if file_size % log_size != 0:
        print("  Warning: Log file might be corrupted!")
        print(f"File size: {file_size} bytes, Expected record size: {log_size} bytes")
        print(" Cannot modify existing log file. Continuing with current data...")
    
    changes = []
    
    try:
        with open("product_change.bin", "rb") as f:
            record_num = 1
            while True:
                chunk = f.read(log_size)
                if not chunk:
                    break
                    
                if len(chunk) < log_size:
                    print(f" Incomplete record #{record_num}, skipping...")
                    continue
                
                try:
                    # Unpack log record with user field
                    record = struct.unpack(log_format, chunk)
                    
                    # Decode strings properly
                    timestamp = record[0].decode('utf-8', errors='ignore').strip('\x00')
                    op_code = record[1]
                    pro_id = record[2].decode('utf-8', errors='ignore').strip('\x00')
                    name_after = record[3].decode('utf-8', errors='ignore').strip('\x00')
                    cost_after = record[4]
                    sale_after = record[5]
                    amount_after = record[6]
                    category_after = record[7].decode('utf-8', errors='ignore').strip('\x00')
                    status_after = record[8]
                    user = record[9].decode('utf-8', errors='ignore').strip('\x00')
                    
                    changes.append([
                        record_num,
                        OPERATIONS.get(op_code, f"OP_{op_code}"),
                        timestamp,
                        pro_id,
                        name_after,
                        f"{cost_after:,.2f}" if isinstance(cost_after, (int, float)) else str(cost_after),
                        f"{sale_after:,.2f}" if isinstance(sale_after, (int, float)) else str(sale_after),
                        f"{amount_after:,}" if isinstance(amount_after, int) else str(amount_after),
                        category_after,
                        STATUS_NAMES.get(status_after, f"Status_{status_after}"),
                        user
                    ])
                    
                except (struct.error, UnicodeDecodeError) as e:
                    print(f" Error reading record #{record_num}: {e}")
                    continue
                
                record_num += 1
                
    except Exception as e:
        print(f" Error reading log file: {e}")
        return
    
    if changes:
        # Headers with User column
        headers = ["#", "Action", "Timestamp", "Product_ID", "Name", "Cost", "Sale_Price", "Amount", "Category", "Status", "User"]
        print(f"\n=== Change Log ({len(changes)} records) ===")
        print(tabulate(changes, headers=headers, tablefmt="grid"))
        
        # Enhanced summary
        summary = {}
        for change in changes:
            action = change[1]
            summary[action] = summary.get(action, 0) + 1
        
        # print(f"\n📊 Summary:")
        # for action, count in summary.items():
        #     emoji = {"ADD": "➕", "UPDATE": "✏️", "DELETE": "🗑️", "VIEW": "👁️"}.get(action, "❓")
        #     print(f"   {emoji} {action}: {count}")
        
        if changes:
            print(f"Time range: {changes[0][2]} to {changes[-1][2]}")
    else:
        print("No change records found")

def debug_log_file():
    """Debug function to check log file structure"""
    if not os.path.exists("product_change.bin"):
        print("No log file found!")
        return
    
    file_size = os.path.getsize("product_change.bin")
    expected_record_size = struct.calcsize(log_format)
    
    # print(f"Log File Debug Info:")
    # print(f"   File size: {file_size} bytes")
    # print(f"   Expected record size: {expected_record_size} bytes")
    # print(f"   Calculated number of records: {file_size // expected_record_size}")
    # print(f"   Remainder bytes: {file_size % expected_record_size}")
    
    if file_size % expected_record_size == 0:
        print("File structure looks correct!")
    else:
        print("File structure mismatch - records may be corrupted")
    
    # Show first few bytes of each record
    try:
        with open("product_change.bin", "rb") as f:
            record_num = 1
            while True:
                record = f.read(expected_record_size)
                if not record:
                    break
                if len(record) < expected_record_size:
                    print(f"Record {record_num}: Only {len(record)} bytes (incomplete)")
                    break
                
                # Try to decode timestamp from first 15 bytes
                timestamp_bytes = record[:15]
                try:
                    timestamp = timestamp_bytes.decode('utf-8', errors='ignore').strip('\x00')
                    print(f"Record {record_num}: Timestamp '{timestamp}' ({len(record)} bytes total)")
                except:
                    print(f"Record {record_num}: Binary timestamp ({len(record)} bytes total)")
                
                record_num += 1
                if record_num > 5:  # Limit to first 5 records
                    print("   ... (showing first 5 records only)")
                    break
    except Exception as e:
        print(f"Error reading file: {e}")
