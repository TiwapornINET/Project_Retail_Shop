from datetime import datetime
from prettytable import PrettyTable
import struct
import os

# -------------------- Config --------------------
LOG_FILE = "product_change.bin"
CUSTOMER_LOG_FILE = "customer_change.bin"
LOG_STRUCT_FMT = "19si13s20sffi12si20s"
LOG_RECORD_SIZE = struct.calcsize(LOG_STRUCT_FMT)
CUSTOMER_LOG_STRUCT_FMT = "19si10s50s10sI20s"
CUSTOMER_LOG_RECORD_SIZE = struct.calcsize(CUSTOMER_LOG_STRUCT_FMT)

SALE_STRUCT_FMT = "10s10s10sffi"
SALE_RECORD_SIZE = struct.calcsize(SALE_STRUCT_FMT)

SALE_DETAIL_STRUCT_FMT = "10s13siff"
SALE_DETAIL_RECORD_SIZE = struct.calcsize(SALE_DETAIL_STRUCT_FMT)

CUSTOMER_STRUCT_FMT = "10s50s10sI"
CUSTOMER_RECORD_SIZE = struct.calcsize(CUSTOMER_STRUCT_FMT)

# -------------------- ฟังก์ชันช่วย --------------------
def unpack_log(data: bytes):
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
    except:
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

def unpack_customer_log(data: bytes):
    try:
        r = struct.unpack(CUSTOMER_LOG_STRUCT_FMT, data)
    except struct.error:
        return None
    ts_raw = r[0].decode().strip("\x00")
    op_code = r[1]
    cust_id = r[2].decode().strip("\x00")
    cust_name = r[3].decode().strip("\x00")
    cust_tel = r[4].decode().strip("\x00")
    cust_status = r[5]
    user = r[6].decode().strip("\x00")

    ts_dt = None
    try:
        ts_dt = datetime.strptime(ts_raw.replace("_", " "), "%Y-%m-%d %H:%M:%S")
    except:
        ts_dt = None

    return {
        "ts_dt": ts_dt,
        "op_code": op_code,
        "cust_id": cust_id,
        "cust_name": cust_name,
        "cust_tel": cust_tel,
        "cust_status": cust_status,
        "User": user
    }

# -------------------- ฟังก์ชันสร้างรายงาน --------------------
def generate_report():
    try:
        # -------------------- อ่าน product.dat --------------------
        products = {}
        table = PrettyTable()
        table.field_names = ["ID", "Name", "Cost", "Sale Price", "Amount", "Category", "Status"]

        status_counter = {1: 0, 2: 0, 3: 0}
        category_counter = {}
        sold_out_products = []

        if not os.path.exists("product.dat"):
            print("❌ ไม่พบไฟล์ product.dat")
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
                products[pro_id] = pro_name

                if status in status_counter:
                    status_counter[status] += 1
                category_counter[category] = category_counter.get(category, 0) + amount
                if status == 2:
                    sold_out_products.append(pro_name)
            # print(table)

        # -------------------- อ่าน customer.dat --------------------
        customers = {}
        if os.path.exists("customer.dat"):
            with open("customer.dat", "rb") as cf:
                while True:
                    data = cf.read(CUSTOMER_RECORD_SIZE)
                    if not data:
                        break
                    r = struct.unpack(CUSTOMER_STRUCT_FMT, data)
                    cust_id = r[0].decode().strip("\x00")
                    cust_name = r[1].decode().strip("\x00")
                    customers[cust_id] = cust_name

        # -------------------- อ่าน sale_detail.dat --------------------
        sale_details = {}
        if os.path.exists("sale_detail.dat"):
            with open("sale_detail.dat", "rb") as df:
                while True:
                    data = df.read(SALE_DETAIL_RECORD_SIZE)
                    if not data: break
                    if len(data) != SALE_DETAIL_RECORD_SIZE: continue
                    r = struct.unpack(SALE_DETAIL_STRUCT_FMT, data)
                    sale_id = r[0].decode(errors="ignore").strip("\x00").strip()
                    pro_id = r[1].decode(errors="ignore").strip("\x00").strip()
                    amount = r[2]
                    price = r[3]
                    discount = r[4]
                    if sale_id not in sale_details:
                        sale_details[sale_id] = []
                    sale_details[sale_id].append({
                        "pro_id": pro_id,
                        "amount": amount,
                        "price": price,
                        "discount": discount
                    })

        # -------------------- อ่าน sale.dat (เฉพาะวันนี้) --------------------
        today_sales = []
        if os.path.exists("sale.dat"):
            with open("sale.dat", "rb") as sf:
                while True:
                    data = sf.read(SALE_RECORD_SIZE)
                    if not data: break
                    if len(data) != SALE_RECORD_SIZE: continue
                    r = struct.unpack(SALE_STRUCT_FMT, data)
                    sale_id = r[0].decode(errors="ignore").strip("\x00").strip()
                    cust_id = r[1].decode(errors="ignore").strip("\x00").strip()
                    sale_date_str = r[2].decode(errors="ignore").strip("\x00").strip()
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
                            "net_discount": net_discount,
                            "sale_dt": sale_dt.date()
                        })

        # -------------------- รวมบิล + รายละเอียดสินค้าในตารางเดียว --------------------
        table_sale = PrettyTable()
        table_sale.field_names = [
            "Sale ID", "Customer", "Date",
            "Product", "Amount", "Price", "Item Discount",
            "Net Price", "Bill Discount"
        ]

        for s in today_sales:
            cust_name = customers.get(s['cust_id'], s['cust_id'])
            sale_dt = s['sale_dt'].strftime("%d-%m-%Y")

            if s['sale_id'] in sale_details:
                details = sale_details[s['sale_id']]
                last_index = len(details) - 1  # บรรทัดสุดท้ายของบิลนี้

                for i, d in enumerate(details):
                    pro_name = products.get(d['pro_id'], d['pro_id'])

                    table_sale.add_row([
                        s['sale_id'] if i == 0 else "",   # แสดง Sale ID แค่ครั้งแรก
                        cust_name if i == 0 else "",
                        sale_dt if i == 0 else "",
                        pro_name, d['amount'], f"{d['price']:.2f}", f"{d['discount']:.2f}",
                        f"{s['net_price']:.2f}" if i == last_index else "",   # แสดง Net/Bill เฉพาะแถวสุดท้าย
                        f"{s['net_discount']:.2f}" if i == last_index else ""
                    ])
            else:
                # กรณีไม่มี detail
                table_sale.add_row([
                    s['sale_id'], cust_name, sale_dt,
                    "-", "-", "-", "-",
                    f"{s['net_price']:.2f}", f"{s['net_discount']:.2f}"
                ])



        # -------------------- คำนวณสรุปยอดขาย --------------------
        total_sales = sum(s['net_price'] for s in today_sales) if today_sales else 0
        max_sale = max(today_sales, key=lambda x: x['net_price']) if today_sales else None
        min_sale = min(today_sales, key=lambda x: x['net_price']) if today_sales else None
        avg_sale = (total_sales / len(today_sales)) if today_sales else 0

        # -------------------- แสดงผลทางหน้าจอ --------------------
        print("\n📋 รายการขายวันนี้ + รายละเอียดสินค้า")
        print(table_sale)

        print("\n📊 สรุป Status สินค้า")
        for k, v in status_counter.items():
            meaning = {1: "มีสินค้า", 2: "สินค้าหมด", 3: "ยกเลิกการขาย"}.get(k, "Unknown")
            print(f"- {meaning}: {v}")

        print("\n📋 สรุปประเภทสินค้า")
        for k, v in category_counter.items():
            print(f"- {k}: {v}")

        print("\n⚠️ สินค้าหมด")
        if sold_out_products:
            for name in sold_out_products:
                print("-", name)
        else:
            print("ไม่มีสินค้าไหนหมด")

        print("\n💰 รายงานยอดขายวันนี้")
        print(f"- รวมยอดขายสุทธิวันนี้: {total_sales:.2f}")
        if max_sale:
            cust_name = customers.get(max_sale['cust_id'], max_sale['cust_id'])
            print(f"- บิลแพงสุด: {max_sale['sale_id']} ({cust_name}) : {max_sale['net_price']:.2f}")
        if min_sale:
            cust_name = customers.get(min_sale['cust_id'], min_sale['cust_id'])
            print(f"- บิลถูกสุด: {min_sale['sale_id']} ({cust_name}) : {min_sale['net_price']:.2f}")
        print(f"- ค่าเฉลี่ยต่อบิล: {avg_sale:.2f}")
       # -------------------- อ่านและสรุป Product Log --------------------
        product_logs = []
        product_action_counter = {}
        product_user_counter = {}
        action_meaning = {1:"ADD", 2:"UPDATE", 3:"DELETE", 4:"VIEW", 5:"OTHER"}

        if os.path.exists(LOG_FILE):
            with open(LOG_FILE,"rb") as pf:
                while True:
                    data = pf.read(LOG_RECORD_SIZE)
                    if not data: 
                        break
                    log = unpack_log(data)
                    if log and log["ts_dt"] and log["ts_dt"].date() == datetime.now().date():
                        product_logs.append(log)
                        # นับ action
                        product_action_counter[log["op_code"]] = product_action_counter.get(log["op_code"],0)+1
                        # นับ user
                        product_user_counter[log["User"]] = product_user_counter.get(log["User"],0)+1

        print("\n=== Product Change History ===")
        if product_logs:
            product_log_table = PrettyTable(["Time","Action","Product ID","Product Name","User"])
            for log in product_logs:
                ts = log["ts_dt"].strftime("%Y-%m-%d %H:%M:%S")
                action = action_meaning.get(log["op_code"], "Unknown")
                product_log_table.add_row([ts, action, log['Pro_id'], log['Pro_name'], log['User']])
            # print(product_log_table)
        else:
            print("ไม่มีการเปลี่ยนแปลงสินค้าในวันนี้")

        # สรุปจำนวน
        print("\n📊 Product Action Summary")
        for code, count in product_action_counter.items():
            print(f"- {action_meaning.get(code,'Unknown')}: {count} ครั้ง")

        print("\n👤 Product User Summary")
        for user, count in product_user_counter.items():
            print(f"- {user}: {count} ครั้ง")


        # -------------------- อ่านและสรุป Customer Log --------------------
        customer_logs = []
        customer_action_counter = {}
        customer_user_counter = {}
        if os.path.exists(CUSTOMER_LOG_FILE):
            with open(CUSTOMER_LOG_FILE,"rb") as cf:
                while True:
                    data = cf.read(CUSTOMER_LOG_RECORD_SIZE)
                    if not data: break
                    log = unpack_customer_log(data)
                    if log and log["ts_dt"] and log["ts_dt"].date()==datetime.now().date():
                        customer_logs.append(log)
                        customer_action_counter[log["op_code"]] = customer_action_counter.get(log["op_code"],0)+1
                        customer_user_counter[log["User"]] = customer_user_counter.get(log["User"],0)+1

        print("\n=== Customer Change History ===")
        if customer_logs:
            customer_log_table = PrettyTable(["Time","Action","Customer ID","Customer Name","User"])
            for log in customer_logs:
                ts = log["ts_dt"].strftime("%Y-%m-%d %H:%M:%S")
                action = action_meaning.get(log["op_code"], "Unknown")
                customer_log_table.add_row([ts, action, log['cust_id'], log['cust_name'], log['User']])
            # print(customer_log_table)
        else:
            print("ไม่มีการเปลี่ยนแปลงลูกค้าในวันนี้")

        print("\n📊 Customer Action Summary")
        for code, count in customer_action_counter.items():
            print(f"- {action_meaning.get(code,'Unknown')}: {count} ครั้ง")

        print("\n👤 Customer User Summary")
        for user, count in customer_user_counter.items():
            print(f"- {user}: {count} ครั้ง")

        # -------------------- เขียนรายงานลงไฟล์ --------------------
        with open("Generate_report.txt","w", encoding="utf-8") as report_file:
                report_file.write("\n\nRetail Shop System\n")
                report_file.write(f"\nGenerate At : {datetime.now()}\n")
                report_file.write("\n📋 รายการขายวันนี้ + รายละเอียดสินค้า\n")
                report_file.write(str(table_sale))

                report_file.write("\n\n💰 รายงานยอดขายวันนี้\n")
                report_file.write(f"- รวมยอดขายสุทธิวันนี้: {total_sales:.2f}\n")
                if max_sale:
                    cust_name = customers.get(max_sale['cust_id'], max_sale['cust_id'])
                    report_file.write(f"- บิลแพงสุด: {max_sale['sale_id']} ({cust_name}) : {max_sale['net_price']:.2f}\n")
                if min_sale:
                    cust_name = customers.get(min_sale['cust_id'], min_sale['cust_id'])
                    report_file.write(f"- บิลถูกสุด: {min_sale['sale_id']} ({cust_name}) : {min_sale['net_price']:.2f}\n")
                report_file.write(f"- ค่าเฉลี่ยต่อบิล: {avg_sale:.2f}\n")
                # report_file.write(f"\n\n📋 รายการสินค้า\n")
                # report_file.write(str(table))
                report_file.write("\n\n📊 สรุป Status สินค้า\n")
                for k, v in status_counter.items():
                    meaning = {1: "มีสินค้า", 2: "สินค้าหมด", 3: "ยกเลิกการขาย"}.get(k, "Unknown")
                    report_file.write(f"- {meaning}: {v}\n")

                report_file.write("\n\n📋 สรุปประเภทสินค้า\n")
                for k, v in category_counter.items():
                    report_file.write(f"- {k}: {v}\n")

                report_file.write("\n\n⚠️ สินค้าหมด\n")
                if sold_out_products:
                    for name in sold_out_products:
                        report_file.write(f"- {name}\n")
                else:
                    report_file.write("ไม่มีสินค้าไหนหมด\n")

              

               # Product Log 
                report_file.write("\n\n=== Product Change History ===\n") 
                if product_logs:
                    product_log_table = PrettyTable(["Time","Action","Product ID","Product Name","User"])
                    for log in product_logs:
                        ts = log["ts_dt"].strftime("%Y-%m-%d %H:%M:%S")
                        action = action_meaning.get(log["op_code"], "Unknown")
                        product_log_table.add_row([ts, action, log['Pro_id'], log['Pro_name'], log['User']])
                    # report_file.write(str(product_log_table) + "\n")
                else:
                    report_file.write("ไม่มีการเปลี่ยนแปลงสินค้าในวันนี้\n")

                report_file.write("\n📊 Product Action Summary\n")
                for code, count in product_action_counter.items():
                    report_file.write(f"- {action_meaning.get(code,'Unknown')}: {count} ครั้ง\n")

                report_file.write("\n👤 Product User Summary\n")
                for user, count in product_user_counter.items():
                    report_file.write(f"- {user}: {count} ครั้ง\n")

                # Customer Log 
                report_file.write("\n\n=== Customer Change History ===\n") 
                if customer_logs:
                    customer_log_table = PrettyTable(["Time","Action","Customer ID","Customer Name","User"])
                    for log in customer_logs:
                        ts = log["ts_dt"].strftime("%Y-%m-%d %H:%M:%S")
                        action = action_meaning.get(log["op_code"], "Unknown")
                        customer_log_table.add_row([ts, action, log['cust_id'], log['cust_name'], log['User']])
                    # report_file.write(str(customer_log_table) + "\n")
                else:
                    report_file.write("ไม่มีการเปลี่ยนแปลงลูกค้าในวันนี้\n")

                report_file.write("\n📊 Customer Action Summary\n")
                for code, count in customer_action_counter.items():
                    report_file.write(f"- {action_meaning.get(code,'Unknown')}: {count} ครั้ง\n")

                report_file.write("\n👤 Customer User Summary\n")
                for user, count in customer_user_counter.items():
                    report_file.write(f"- {user}: {count} ครั้ง\n")

        print("\n✅ บันทึกรายงานลง Generate_report.txt เรียบร้อยแล้ว")


    except Exception as e:
        print(f"Error : ❌ {e}")


# def Sale_Report():
#     import struct
#     from datetime import datetime
#     from prettytable import PrettyTable
#     import os

#     SALE_STRUCT_FMT = '10s10s10sffi'
#     SALE_RECORD_SIZE = struct.calcsize(SALE_STRUCT_FMT)

#     # ฟังก์ชันช่วยแปลง string วันในไฟล์เป็น date object (รองรับหลายรูปแบบ)
#     def parse_sale_date(s: str):
#         try:
#             s = s.strip().strip("\x00").strip()
#             if not s:
#                 return None
#             # ลองรูปแบบที่เป็นไปได้
#             fmts = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%d%m%Y"]
#             for fmt in fmts:
#                 try:
#                     dt = datetime.strptime(s, fmt)
#                     # แปลงพ.ศ. ถ้าจับได้ว่าปี > 2500
#                     if dt.year > 2500:
#                         dt = dt.replace(year=dt.year - 543)
#                     return dt.date()
#                 except Exception:
#                     continue
#             # ถ้าเป็นแบบไม่มีตัวคั่น (8 หลัก) พยายามแยก DDMMYYYY
#             s2 = ''.join(ch for ch in s if ch.isdigit())
#             if len(s2) == 8:
#                 try:
#                     day = int(s2[:2]); month = int(s2[2:4]); year = int(s2[4:])
#                     if year > 2500:
#                         year -= 543
#                     return datetime(year, month, day).date()
#                 except Exception:
#                     return None
#             return None
#         except Exception:
#             return None

#     while True:
#         try:
#             raw = input("Enter date to view (DDMMYYYY) or leave empty for today: ").strip()
#             # ถ้าไม่ใส่ ให้เป็นวันนี้ (default)
#             if raw == "":
#                 report_date = datetime.now().date()
#                 print(f"Using date: {report_date.strftime('%d-%m-%Y')} (today)")
#             else:
#                 s = raw.lower()
#                 if s in ("t", "today", "now"):
#                     report_date = datetime.now().date()
#                     print(f"Using date: {report_date.strftime('%d-%m-%Y')} (today)")
#                 else:
#                     parsed = None
#                     s_digits = ''.join(ch for ch in raw if ch.isdigit())
#                     if len(s_digits) == 8:
#                         try:
#                             day = int(s_digits[:2]); month = int(s_digits[2:4]); year = int(s_digits[4:])
#                             if year > 2500: year -= 543
#                             parsed = datetime(year, month, day).date()
#                         except Exception:
#                             parsed = None
#                     else:
#                         for fmt in ("%d%m%Y","%d-%m-%Y","%d/%m/%Y","%Y-%m-%d","%Y/%m/%d"):
#                             try:
#                                 dt = datetime.strptime(raw, fmt)
#                                 if dt.year > 2500:
#                                     dt = dt.replace(year=dt.year - 543)
#                                 parsed = dt.date()
#                                 break
#                             except:
#                                 continue

#                     if not parsed:
#                         print("❌ Invalid date format. Use DDMMYYYY or YYYY-MM-DD (blank = today).")
#                         continue
#                     report_date = parsed
#                     print(f"Using date: {report_date.strftime('%d-%m-%Y')}")
#         except Exception as e:
#             print(f"❌ Error parsing date: {e}")
#             continue

#         # ตรวจสอบไฟล์
#         if not os.path.exists("sale.dat"):
#             print("❌ ไม่พบไฟล์ sale.dat")
#             return

#         sales_today = []
#         cancelled_count = 0
#         discount_count = 0

#         try:
#             with open("sale.dat", "rb") as f:
#                 while True:
#                     data = f.read(SALE_RECORD_SIZE)
#                     if not data:
#                         break
#                     if len(data) != SALE_RECORD_SIZE:
#                         # record ขนาดไม่ตรง -> ข้าม
#                         continue
#                     try:
#                         r = struct.unpack(SALE_STRUCT_FMT, data)
#                     except struct.error:
#                         continue

#                     try:
#                         sale_id = r[0].decode(errors="ignore").strip("\x00").strip()
#                         cust_id = r[1].decode(errors="ignore").strip("\x00").strip()
#                         sale_date_str = r[2].decode(errors="ignore").strip("\x00").strip()
#                         net_price = float(r[3])
#                         net_discount = float(r[4])
#                         sale_status = int(r[5])
#                     except Exception:
#                         continue

#                     sale_dt = parse_sale_date(sale_date_str)
#                     if sale_dt is None:
#                         continue

#                     if sale_dt == report_date:
#                         sales_today.append({
#                             "sale_id": sale_id,
#                             "cust_id": cust_id,
#                             "net_price": net_price,
#                             "net_discount": net_discount,
#                             "sale_status": sale_status,
#                             "sale_dt": sale_dt
#                         })
#                         if sale_status == 1:
#                             cancelled_count += 1
#                         if net_discount > 0:
#                             discount_count += 1
#         except Exception as e:
#             print(f"❌ Error reading sale.dat: {e}")
#             continue

#         if not sales_today:
#             print("ไม่มีบิลขายในวันนั้น")
#         else:
#             # ตารางบิลขาย
#             try:
#                 table = PrettyTable()
#                 table.field_names = ["Sale ID", "Customer", "Date", "Net Price", "Discount", "Status"]
#                 for s in sales_today:
#                     status_str = "Cancelled" if s['sale_status'] == 1 else "Normal"
#                     table.add_row([
#                         s['sale_id'],
#                         s['cust_id'],
#                         s['sale_dt'].strftime("%d-%m-%Y"),
#                         f"{s['net_price']:.2f}",
#                         f"{s['net_discount']:.2f}",
#                         status_str
#                     ])

#                 print("\n📋 รายงานบิลขาย")
#                 print(table)

#                 # สรุปยอดขาย
#                 non_cancelled_count = sum(1 for s in sales_today if s['sale_status'] != 1)
#                 total_sales = sum(s['net_price'] for s in sales_today if s['sale_status'] != 1)
#                 max_sale = max(sales_today, key=lambda x: x['net_price'], default=None)
#                 min_sale = min(sales_today, key=lambda x: x['net_price'], default=None)
#                 avg_sale = total_sales / non_cancelled_count if non_cancelled_count > 0 else 0.0

#                 summary_table = PrettyTable()
#                 summary_table.field_names = ["Info", "Value"]
#                 summary_table.add_row(["Total Sales (Net)", f"{total_sales:.2f}"])
#                 if max_sale: summary_table.add_row(["Max Bill", f"{max_sale['sale_id']} : {max_sale['net_price']:.2f}"])
#                 if min_sale: summary_table.add_row(["Min Bill", f"{min_sale['sale_id']} : {min_sale['net_price']:.2f}"])
#                 summary_table.add_row(["Average per Bill", f"{avg_sale:.2f}"])
#                 summary_table.add_row(["Bills with Discount", discount_count])
#                 summary_table.add_row(["Cancelled Bills", cancelled_count])

#                 print("\n💰 สรุปยอดขาย")
#                 print(summary_table)
#             except Exception as e:
#                 print(f"❌ Error building report table: {e}")

#         # ถามว่าจะออกจากการดูรายงานหรือไม่
#         while True:
#             try:
#                 exit_input = input("\nDo you want to exit Sale Report? (Y/N): ").strip().upper()
#                 if exit_input in ("Y", "N"):
#                     break
#                 else:
#                     print("❌ Please enter only Y or N.")
#             except Exception as e:
#                 print(f"❌ Error reading input: {e}")
#                 continue

#         if exit_input == "Y":
#             break

from datetime import datetime
from prettytable import PrettyTable
import struct
import os

def Sale_Report():
    SALE_STRUCT_FMT = '10s10s10sffi'
    SALE_RECORD_SIZE = struct.calcsize(SALE_STRUCT_FMT)

    SALE_DETAIL_STRUCT_FMT = '10s13siff'
    SALE_DETAIL_RECORD_SIZE = struct.calcsize(SALE_DETAIL_STRUCT_FMT)

    CUSTOMER_STRUCT_FMT = '10s50s10sI'
    CUSTOMER_RECORD_SIZE = struct.calcsize(CUSTOMER_STRUCT_FMT)

    # -------------------- อ่านข้อมูลสินค้า --------------------
    products = {}
    if os.path.exists("product.dat"):
        with open("product.dat", "rb") as pf:
            record_size = struct.calcsize("13s20sffi12si")
            while True:
                data = pf.read(record_size)
                if not data: break
                if len(data) != record_size: continue
                r = struct.unpack("13s20sffi12si", data)
                pro_id = r[0].decode(errors="ignore").strip("\x00").strip()
                pro_name = r[1].decode(errors="ignore").strip("\x00").strip()
                products[pro_id] = pro_name

    # -------------------- อ่านข้อมูลลูกค้า --------------------
    customers = {}
    if os.path.exists("customer.dat"):
        with open("customer.dat", "rb") as cf:
            while True:
                data = cf.read(CUSTOMER_RECORD_SIZE)
                if not data: break
                if len(data) != CUSTOMER_RECORD_SIZE: continue
                r = struct.unpack(CUSTOMER_STRUCT_FMT, data)
                cust_id = r[0].decode(errors="ignore").strip("\x00").strip()
                cust_name = r[1].decode(errors="ignore").strip("\x00").strip()
                customers[cust_id] = cust_name

    # -------------------- อ่านรายละเอียดการขาย --------------------
    sale_details = {}
    if os.path.exists("sale_detail.dat"):
        with open("sale_detail.dat", "rb") as df:
            while True:
                data = df.read(SALE_DETAIL_RECORD_SIZE)
                if not data: break
                if len(data) != SALE_DETAIL_RECORD_SIZE: continue
                r = struct.unpack(SALE_DETAIL_STRUCT_FMT, data)
                sale_id = r[0].decode(errors="ignore").strip("\x00").strip()
                pro_id = r[1].decode(errors="ignore").strip("\x00").strip()
                amount = r[2]
                price = r[3]
                discount = r[4]

                if sale_id not in sale_details:
                    sale_details[sale_id] = []
                sale_details[sale_id].append({
                    "pro_id": pro_id,
                    "amount": amount,
                    "price": price,
                    "discount": discount
                })

    # -------------------- ฟังก์ชันช่วยแปลง string วันเป็น date object --------------------
    def parse_sale_date(s: str):
        try:
            s = s.strip().strip("\x00").strip()
            if not s:
                return None
            fmts = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%d%m%Y"]
            for fmt in fmts:
                try:
                    dt = datetime.strptime(s, fmt)
                    if dt.year > 2500:
                        dt = dt.replace(year=dt.year - 543)
                    return dt.date()
                except Exception:
                    continue
            # แบบไม่มีตัวคั่น DDMMYYYY
            s2 = ''.join(ch for ch in s if ch.isdigit())
            if len(s2) == 8:
                day = int(s2[:2]); month = int(s2[2:4]); year = int(s2[4:])
                if year > 2500: year -= 543
                return datetime(year, month, day).date()
            return None
        except Exception:
            return None

    # -------------------- เริ่ม loop รายงาน --------------------
    while True:
        try:
            raw = input("Enter date to view (DDMMYYYY) or leave empty for today: ").strip()
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
                        print("❌ Invalid date format. Use DDMMYYYY or YYYY-MM-DD (blank = today).")
                        continue
                    report_date = parsed
                    print(f"Using date: {report_date.strftime('%d-%m-%Y')}")
        except Exception as e:
            print(f"❌ Error parsing date: {e}")
            continue

        # -------------------- อ่าน sale.dat --------------------
        if not os.path.exists("sale.dat"):
            print("❌ ไม่พบไฟล์ sale.dat")
            return

        sales_today = []
        cancelled_count = 0
        discount_count = 0

        try:
            with open("sale.dat", "rb") as f:
                while True:
                    data = f.read(SALE_RECORD_SIZE)
                    if not data: break
                    if len(data) != SALE_RECORD_SIZE: continue
                    try:
                        r = struct.unpack(SALE_STRUCT_FMT, data)
                        sale_id = r[0].decode(errors="ignore").strip("\x00").strip()
                        cust_id = r[1].decode(errors="ignore").strip("\x00").strip()
                        sale_date_str = r[2].decode(errors="ignore").strip("\x00").strip()
                        net_price = float(r[3])
                        net_discount = float(r[4])
                        sale_status = int(r[5])
                    except Exception:
                        continue

                    sale_dt = parse_sale_date(sale_date_str)
                    if sale_dt is None: continue
                    if sale_dt == report_date:
                        sales_today.append({
                            "sale_id": sale_id,
                            "cust_id": cust_id,
                            "net_price": net_price,
                            "net_discount": net_discount,
                            "sale_status": sale_status,
                            "sale_dt": sale_dt
                        })
                        if sale_status == 1: cancelled_count += 1
                        if net_discount > 0: discount_count += 1
        except Exception as e:
            print(f"❌ Error reading sale.dat: {e}")
            continue

        if not sales_today:
            print("ไม่มีบิลขายในวันนั้น")
        else:
            # -------------------- ตารางบิลขาย + รายละเอียดสินค้า --------------------
            table = PrettyTable()
            table.field_names = [
                "Sale ID", "Customer", "Date",
                "Product", "Amount", "Price", "Item Discount",
                "Net Price", "Bill Discount", "Status"
            ]

            for s in sales_today:
                cust_name = customers.get(s['cust_id'], s['cust_id'])
                status_str = "Cancelled" if s['sale_status'] == 1 else "Normal"
                sale_dt = s['sale_dt'].strftime("%d-%m-%Y")

                if s['sale_id'] in sale_details:
                    details = sale_details[s['sale_id']]
                    last_index = len(details) - 1  # index ของบรรทัดสุดท้ายในบิลนี้

                    for i, d in enumerate(details):
                        pro_name = products.get(d['pro_id'], d['pro_id'])
                        table.add_row([
                            s['sale_id'] if i == 0 else "",
                            cust_name if i == 0 else "",
                            sale_dt if i == 0 else "",
                            pro_name,
                            d['amount'],
                            f"{d['price']:.2f}",
                            f"{d['discount']:.2f}",
                            f"{s['net_price']:.2f}" if i == last_index else "",
                            f"{s['net_discount']:.2f}" if i == last_index else "",
                            status_str if i == 0 else ""
                        ])
                else:
                    # กรณีไม่มี detail
                    table.add_row([
                        s['sale_id'],
                        cust_name,
                        sale_dt,
                        "-", "-", "-", "-",
                        f"{s['net_price']:.2f}",
                        f"{s['net_discount']:.2f}",
                        status_str
                    ])




            print("\n📋 รายงานบิลขาย + รายละเอียดสินค้า")
            print(table)

            # -------------------- สรุปยอดขาย (แบบข้อความ) --------------------
            non_cancelled_count = sum(1 for s in sales_today if s['sale_status'] != 1)
            total_sales = sum(s['net_price'] for s in sales_today if s['sale_status'] != 1)
            max_sale = max(sales_today, key=lambda x: x['net_price'], default=None)
            min_sale = min(sales_today, key=lambda x: x['net_price'], default=None)
            avg_sale = total_sales / non_cancelled_count if non_cancelled_count > 0 else 0.0

            print("\n💰 สรุปยอดขาย")
            print(f"- Total Sales (Net): {total_sales:.2f}")
            if max_sale: print(f"- Max Bill: {max_sale['sale_id']} : {max_sale['net_price']:.2f}")
            if min_sale: print(f"- Min Bill: {min_sale['sale_id']} : {min_sale['net_price']:.2f}")
            print(f"- Average per Bill: {avg_sale:.2f}")
            print(f"- Bills with Discount: {discount_count}")
            print(f"- Cancelled Bills: {cancelled_count}")

        # -------------------- ถามจะออกจาก Sale Report --------------------
        while True:
            try:
                exit_input = input("\nDo you want to exit Sale Report? (Y/N): ").strip().upper()
                if exit_input in ("Y", "N"): break
                print("❌ Please enter only Y or N.")
            except Exception as e:
                print(f"❌ Error reading input: {e}")
        if exit_input == "Y": break




def Product_report():
    from prettytable import PrettyTable
    import struct

    # สร้างตารางหลัก
    table = PrettyTable()
    table.field_names = ["ID", "Name", "Cost", "Sale Price", "Amount", "Category", "Status"]

    status_counter = {1: 0, 2: 0, 3: 0}
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

        # แสดงผลตารางสินค้า
        print("\n📋 รายการสินค้า")
        print(table)

        # แสดงสรุปสถานะสินค้า (เป็นข้อความแทนตาราง)
        print("\n📊 สรุปสถานะสินค้า")
        status_meaning = {1: "มีขาย", 2: "สินค้าหมด", 3: "ยกเลิก"}
        for key, count in status_counter.items():
            print(f"- {status_meaning.get(key, 'Unknown')}: {count} รายการ")

        # แสดงสรุปประเภทสินค้า (ข้อความแทนตาราง)
        print("\n📋 สรุปประเภทสินค้า")
        for cat, total in category_counter.items():
            print(f"- {cat}: {total} ชิ้น")

        # แสดงสินค้าหมด
        print("\n⚠️ สินค้าหมด")
        if sold_out_products:
            for name in sold_out_products:
                print("-", name)
        else:
            print("ไม่มีสินค้าไหนหมด")

    except FileNotFoundError:
        print("❌ ไม่พบไฟล์ product.dat")



