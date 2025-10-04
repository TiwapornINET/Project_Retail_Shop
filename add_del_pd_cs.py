import os
import struct
from datetime import datetime

# ====== ไฟล์ ======
PRODUCT_FILE = "product.dat"
PRODUCT_LOG_FILE = "product_change.bin"
CUSTOMER_FILE = "customer.dat"
CUSTOMER_LOG_FILE = "customer_change.bin"

# ====== Product Struct ======
product_format = "13s20sffi12si"
product_size = struct.calcsize(product_format)
product_log_format = "19si13s20sffi12si20s"
product_log_size = struct.calcsize(product_log_format)
product_categories = ["Pistol", "Shotgun", "Rifle", "SMG"]
product_max_lengths = {"Pro_id": 13, "Pro_name": 20, "Category": 12, "User": 20}
product_max_digits_float = 5
product_max_digits_int = 5

# ====== Customer Struct ======
customer_format = "10s50s10si"
customer_size = struct.calcsize(customer_format)
customer_log_format = "19si10s50s10si20s"
customer_log_size = struct.calcsize(customer_log_format)
customer_max_lengths = {"Cust_id": 10, "Cust_name": 50, "Cust_tel": 10, "User": 20}

# ====== ฟังก์ชันช่วยเหลือ ======
def ts_now():
    """สร้าง timestamp ปัจจุบัน"""
    try:
        return datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    except Exception as e:
        print(f"⚠️ เกิดข้อผิดพลาดในการสร้างเวลา: {e}")
        return "0000-00-00_00:00:00"

def ensure_files():
    """ตรวจสอบและสร้างไฟล์ที่จำเป็น"""
    for f in [PRODUCT_FILE, PRODUCT_LOG_FILE, CUSTOMER_FILE, CUSTOMER_LOG_FILE]:
        try:
            if not os.path.exists(f):
                with open(f, "wb") as file:
                    pass
                print(f"✅ สร้างไฟล์ {f} สำเร็จ")
        except PermissionError:
            print(f"❌ ไม่มีสิทธิ์สร้างไฟล์ {f}")
            return False
        except Exception as e:
            print(f"❌ ไม่สามารถสร้างไฟล์ {f}: {e}")
            return False
    return True

def input_with_length(prompt, max_len, default=None, allow_empty=False):
    """รับข้อมูลพร้อมตรวจสอบความยาว"""
    while True:
        try:
            val = input(prompt).strip()
            
            # กรณีกด Ctrl+C หรือ Ctrl+D
            if val is None:
                if default is not None:
                    return default
                continue
            
            # ถ้าอนุญาตให้ว่างและผู้ใช้กด Enter
            if allow_empty and not val:
                return ""
            
            # ถ้ามี default และผู้ใช้ไม่กรอก
            if default is not None and not val:
                return default
            
            # ตรวจสอบว่าห้ามมีช่องว่าง
            if " " in val:
                print("❌ ห้ามมีช่องว่างในข้อมูล")
                continue
            
            # ตรวจสอบความยาว
            if val and len(val) <= max_len:
                return val
            
            print(f"❌ กรุณากรอกไม่เกิน {max_len} ตัวอักษร")
        except EOFError:
            print("\n⚠️ ตรวจพบการยกเลิก")
            if default is not None:
                return default
            return None
        except KeyboardInterrupt:
            print("\n⚠️ ถูกยกเลิกโดยผู้ใช้")
            return None
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {e}")
            if default is not None:
                return default

def input_float_with_size(prompt, max_digits):
    """รับตัวเลขทศนิยมพร้อมตรวจสอบขนาด"""
    while True:
        try:
            val = input(prompt).strip()
            
            if not val:
                print("❌ กรุณากรอกข้อมูล")
                continue
            
            f = float(val)
            
            # ตรวจสอบว่าเป็นค่าลบ
            if f < 0:
                print("❌ กรุณากรอกจำนวนที่มากกว่าหรือเท่ากับ 0")
                continue
            
            # ตรวจสอบขนาดหลัก
            if len(str(int(f))) > max_digits:
                print(f"❌ เกินขนาด {max_digits} หลัก, กรอกใหม่")
                continue
            
            return f
        except ValueError:
            print("❌ กรุณากรอกตัวเลขให้ถูกต้อง")
        except KeyboardInterrupt:
            print("\n⚠️ ถูกยกเลิกโดยผู้ใช้")
            return None
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {e}")

def input_int_with_size(prompt, max_digits):
    """รับจำนวนเต็มพร้อมตรวจสอบขนาด"""
    while True:
        try:
            val = input(prompt).strip()
            
            if not val:
                print("❌ กรุณากรอกข้อมูล")
                continue
            
            i = int(val)
            
            # ตรวจสอบว่าเป็นค่าลบ
            if i < 0:
                print("❌ กรุณากรอกจำนวนที่มากกว่าหรือเท่ากับ 0")
                continue
            
            if len(str(i)) > max_digits:
                print(f"❌ เกินขนาด {max_digits} หลัก, กรอกใหม่")
                continue
            
            return i
        except ValueError:
            print("❌ กรุณากรอกจำนวนเต็มให้ถูกต้อง")
        except KeyboardInterrupt:
            print("\n⚠️ ถูกยกเลิกโดยผู้ใช้")
            return None
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {e}")

# ====== Product Pack/Unpack ======
def pack_product(p):
    """แปลง dict เป็น binary สำหรับ Product"""
    try:
        return struct.pack(
            product_format,
            p["Pro_id"].encode('utf-8').ljust(product_max_lengths["Pro_id"], b"\x00"),
            p["Pro_name"].encode('utf-8').ljust(product_max_lengths["Pro_name"], b"\x00"),
            float(p["Pro_cost"]),
            float(p["Pro_salePrice"]),
            int(p["Pro_amount"]),
            p["Category"].encode('utf-8').ljust(product_max_lengths["Category"], b"\x00"),
            int(p["Pro_status"])
        )
    except struct.error as e:
        print(f"❌ ข้อผิดพลาดในการ pack ข้อมูล: {e}")
        return None
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")
        return None

def unpack_product(data):
    """แปลง binary เป็น dict สำหรับ Product"""
    try:
        r = struct.unpack(product_format, data)
        return {
            "Pro_id": r[0].decode('utf-8', errors='ignore').strip("\x00"),
            "Pro_name": r[1].decode('utf-8', errors='ignore').strip("\x00"),
            "Pro_cost": r[2],
            "Pro_salePrice": r[3],
            "Pro_amount": r[4],
            "Category": r[5].decode('utf-8', errors='ignore').strip("\x00"),
            "Pro_status": r[6]
        }
    except struct.error as e:
        print(f"❌ ข้อผิดพลาดในการ unpack ข้อมูล: {e}")
        return None
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")
        return None

def pack_product_log(p, op_code, user="Admin"):
    """แปลง dict เป็น binary สำหรับ Product Log"""
    try:
        return struct.pack(
            product_log_format,
            ts_now().encode('utf-8'),
            int(op_code),
            p["Pro_id"].encode('utf-8').ljust(product_max_lengths["Pro_id"], b"\x00"),
            p["Pro_name"].encode('utf-8').ljust(product_max_lengths["Pro_name"], b"\x00"),
            float(p["Pro_cost"]),
            float(p["Pro_salePrice"]),
            int(p["Pro_amount"]),
            p["Category"].encode('utf-8').ljust(product_max_lengths["Category"], b"\x00"),
            int(p["Pro_status"]),
            user.encode('utf-8').ljust(product_max_lengths["User"], b"\x00")
        )
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการสร้าง log: {e}")
        return None

def unpack_product_log(data):
    """แปลง binary เป็น dict สำหรับ Product Log"""
    try:
        r = struct.unpack(product_log_format, data)
        return {
            "ts": r[0].decode('utf-8', errors='ignore').strip("\x00"),
            "op_code": r[1],
            "Pro_id": r[2].decode('utf-8', errors='ignore').strip("\x00"),
            "Pro_name": r[3].decode('utf-8', errors='ignore').strip("\x00"),
            "Pro_cost": r[4],
            "Pro_salePrice": r[5],
            "Pro_amount": r[6],
            "Category": r[7].decode('utf-8', errors='ignore').strip("\x00"),
            "Pro_status": r[8],
            "User": r[9].decode('utf-8', errors='ignore').strip("\x00")
        }
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการอ่าน log: {e}")
        return None

# ====== Customer Pack/Unpack ======
def pack_customer(c):
    """แปลง dict เป็น binary สำหรับ Customer"""
    try:
        return struct.pack(
            customer_format,
            c["Cust_id"].encode('utf-8').ljust(customer_max_lengths["Cust_id"], b"\x00"),
            c["Cust_name"].encode('utf-8').ljust(customer_max_lengths["Cust_name"], b"\x00"),
            c["Cust_tel"].encode('utf-8').ljust(customer_max_lengths["Cust_tel"], b"\x00"),
            int(c["Cust_status"])
        )
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการ pack ข้อมูลลูกค้า: {e}")
        return None

def unpack_customer(data):
    """แปลง binary เป็น dict สำหรับ Customer"""
    try:
        r = struct.unpack(customer_format, data)
        return {
            "Cust_id": r[0].decode('utf-8', errors='ignore').strip("\x00"),
            "Cust_name": r[1].decode('utf-8', errors='ignore').strip("\x00"),
            "Cust_tel": r[2].decode('utf-8', errors='ignore').strip("\x00"),
            "Cust_status": r[3]
        }
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการอ่านข้อมูลลูกค้า: {e}")
        return None

def pack_customer_log(c, op_code, user="Admin"):
    """แปลง dict เป็น binary สำหรับ Customer Log"""
    try:
        return struct.pack(
            customer_log_format,
            ts_now().encode('utf-8'),
            int(op_code),
            c["Cust_id"].encode('utf-8').ljust(customer_max_lengths["Cust_id"], b"\x00"),
            c["Cust_name"].encode('utf-8').ljust(customer_max_lengths["Cust_name"], b"\x00"),
            c["Cust_tel"].encode('utf-8').ljust(customer_max_lengths["Cust_tel"], b"\x00"),
            int(c["Cust_status"]),
            user.encode('utf-8').ljust(customer_max_lengths["User"], b"\x00")
        )
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการสร้าง log ลูกค้า: {e}")
        return None

def unpack_customer_log(data):
    """แปลง binary เป็น dict สำหรับ Customer Log"""
    try:
        r = struct.unpack(customer_log_format, data)
        return {
            "ts": r[0].decode('utf-8', errors='ignore').strip("\x00"),
            "op_code": r[1],
            "Cust_id": r[2].decode('utf-8', errors='ignore').strip("\x00"),
            "cust_name_after": r[3].decode('utf-8', errors='ignore').strip("\x00"),
            "cust_tel_after": r[4].decode('utf-8', errors='ignore').strip("\x00"),
            "cust_status_after": r[5],
            "User": r[6].decode('utf-8', errors='ignore').strip("\x00")
        }
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการอ่าน log ลูกค้า: {e}")
        return None

# ====== Load/Save Product ======
def load_products():
    """โหลดข้อมูล Product จากไฟล์"""
    products = {}
    try:
        if not os.path.exists(PRODUCT_FILE):
            print("⚠️ ไม่พบไฟล์สินค้า")
            return products
        
        with open(PRODUCT_FILE, "rb") as f:
            while True:
                data = f.read(product_size)
                if not data:
                    break
                if len(data) != product_size:
                    print(f"⚠️ พบข้อมูลที่เสียหาย (ขนาดไม่ถูกต้อง: {len(data)} bytes)")
                    break
                p = unpack_product(data)
                if p:
                    products[p["Pro_id"]] = p
        return products
    except PermissionError:
        print(f"❌ ไม่มีสิทธิ์อ่านไฟล์ {PRODUCT_FILE}")
        return {}
    except FileNotFoundError:
        print(f"⚠️ ไม่พบไฟล์ {PRODUCT_FILE}")
        return {}
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการโหลดสินค้า: {e}")
        return {}

def save_products(products):
    """บันทึกข้อมูล Product ลงไฟล์"""
    try:
        with open(PRODUCT_FILE, "wb") as f:
            for p in products.values():
                packed = pack_product(p)
                if packed:
                    f.write(packed)
        return True
    except PermissionError:
        print(f"❌ ไม่มีสิทธิ์เขียนไฟล์ {PRODUCT_FILE}")
        return False
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการบันทึกสินค้า: {e}")
        return False

def log_product(op_code, product, user="Admin"):
    """บันทึก log สำหรับ Product"""
    try:
        with open(PRODUCT_LOG_FILE, "ab") as f:
            packed = pack_product_log(product, op_code, user)
            if packed:
                f.write(packed)
        return True
    except PermissionError:
        print(f"❌ ไม่มีสิทธิ์เขียนไฟล์ {PRODUCT_LOG_FILE}")
        return False
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการบันทึก log: {e}")
        return False

# ====== Load/Save Customer ======
def load_customers():
    """โหลดข้อมูล Customer จากไฟล์"""
    customers = {}
    try:
        if not os.path.exists(CUSTOMER_FILE):
            print("⚠️ ไม่พบไฟล์ลูกค้า")
            return customers
        
        with open(CUSTOMER_FILE, "rb") as f:
            while True:
                data = f.read(customer_size)
                if not data:
                    break
                if len(data) != customer_size:
                    print(f"⚠️ พบข้อมูลที่เสียหาย (ขนาดไม่ถูกต้อง: {len(data)} bytes)")
                    break
                c = unpack_customer(data)
                if c:
                    customers[c["Cust_id"]] = c
        return customers
    except PermissionError:
        print(f"❌ ไม่มีสิทธิ์อ่านไฟล์ {CUSTOMER_FILE}")
        return {}
    except FileNotFoundError:
        print(f"⚠️ ไม่พบไฟล์ {CUSTOMER_FILE}")
        return {}
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการโหลดลูกค้า: {e}")
        return {}

def save_customers(customers):
    """บันทึกข้อมูล Customer ลงไฟล์"""
    try:
        with open(CUSTOMER_FILE, "wb") as f:
            for c in customers.values():
                packed = pack_customer(c)
                if packed:
                    f.write(packed)
        return True
    except PermissionError:
        print(f"❌ ไม่มีสิทธิ์เขียนไฟล์ {CUSTOMER_FILE}")
        return False
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการบันทึกลูกค้า: {e}")
        return False

def log_customer(op_code, customer, user="Admin"):
    """บันทึก log สำหรับ Customer"""
    try:
        with open(CUSTOMER_LOG_FILE, "ab") as f:
            packed = pack_customer_log(customer, op_code, user)
            if packed:
                f.write(packed)
        return True
    except PermissionError:
        print(f"❌ ไม่มีสิทธิ์เขียนไฟล์ {CUSTOMER_LOG_FILE}")
        return False
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการบันทึก log ลูกค้า: {e}")
        return False

# ====== Product Functions ======
def add_product():
    """เพิ่มสินค้าใหม่"""
    try:
        products = load_products()
        
        # รับ Pro_id
        while True:
            pid = input_with_length(f"Pro_id (max {product_max_lengths['Pro_id']}): ", 
                                   product_max_lengths["Pro_id"])
            if pid is None:
                print("⚠️ ยกเลิกการเพิ่มสินค้า")
                return
            if pid in products:
                print("❌ Pro_id มีอยู่แล้ว")
                continue
            break
        
        # รับ Pro_name
        pname = input_with_length(f"Pro_name (max {product_max_lengths['Pro_name']}): ", 
                                 product_max_lengths["Pro_name"])
        if pname is None:
            print("⚠️ ยกเลิกการเพิ่มสินค้า")
            return
        
        # รับ Pro_cost
        cost = input_float_with_size("Pro_cost: ", product_max_digits_float)
        if cost is None:
            print("⚠️ ยกเลิกการเพิ่มสินค้า")
            return
        
        # รับ Pro_salePrice
        sale = input_float_with_size("Pro_salePrice: ", product_max_digits_float)
        if sale is None:
            print("⚠️ ยกเลิกการเพิ่มสินค้า")
            return
        
        # รับ Pro_amount
        amt = input_int_with_size("Pro_amount: ", product_max_digits_int)
        if amt is None:
            print("⚠️ ยกเลิกการเพิ่มสินค้า")
            return
        
        # รับ Category
        while True:
            cat_input = input(f"Category ({'/'.join(product_categories)}): ").strip()
            if cat_input.capitalize() in product_categories:
                category = cat_input.capitalize()
                break
            print("❌ Category ไม่ถูกต้อง")
        
        # รับ Pro_status
        status_input = input("Pro_status (1=ขายได้,2=ยกเลิก) [default=1]: ").strip()
        status = int(status_input) if status_input in ["1", "2"] else 1
        
        # รับ User
        user = input_with_length("User [default Admin]: ", product_max_lengths["User"], default="Admin")
        if user is None:
            user = "Admin"
        
        # สร้างสินค้าใหม่
        new_product = {
            "Pro_id": pid,
            "Pro_name": pname,
            "Pro_cost": cost,
            "Pro_salePrice": sale,
            "Pro_amount": amt,
            "Category": category,
            "Pro_status": status
        }
        
        products[pid] = new_product
        
        if save_products(products):
            log_product(1, new_product, user)
            print(f"✅ เพิ่มสินค้า {pid} สำเร็จ")
        else:
            print("❌ ไม่สามารถบันทึกสินค้าได้")
    except KeyboardInterrupt:
        print("\n⚠️ ยกเลิกการเพิ่มสินค้า")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")

def delete_product():
    """ลบสินค้า"""
    try:
        products = load_products()
        
        if not products:
            print("⚠️ ไม่มีสินค้าในระบบ")
            return
        
        pid = input("Pro_id ที่ต้องการลบ: ").strip()
        
        if not pid:
            print("❌ กรุณากรอก Pro_id")
            return
        
        if pid not in products:
            print("❌ ไม่พบ Pro_id นี้")
            return
        
        # ยืนยันการลบ
        confirm = input(f"ยืนยันการลบสินค้า {pid} - {products[pid]['Pro_name']} (y/n): ").strip().lower()
        if confirm != 'y':
            print("⚠️ ยกเลิกการลบ")
            return
        
        deleted = products.pop(pid)
        
        if save_products(products):
            deleted_log = deleted.copy()
            deleted_log["Pro_status"] = 3
            log_product(3, deleted_log)
            print(f"🗑️ ลบสินค้า {pid} เรียบร้อย")
        else:
            # คืนค่าถ้าบันทึกไม่สำเร็จ
            products[pid] = deleted
            print("❌ ไม่สามารถลบสินค้าได้")
    except KeyboardInterrupt:
        print("\n⚠️ ยกเลิกการลบสินค้า")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")

def show_products():
    """แสดงสินค้าทั้งหมด"""
    try:
        products = load_products()
        
        if not products:
            print("⚠️ ไม่มีสินค้า")
            return
        
        print("\n=== All Products ===")
        print(f"{'Pro_id':<13} | {'Pro_name':<20} | {'Cost':<8} | {'Sale':<8} | {'Amt':<5} | {'Category':<8} | Status")
        print("-" * 90)
        
        for p in products.values():
            print(f"{p['Pro_id']:<13} | {p['Pro_name']:<20} | {p['Pro_cost']:<8.2f} | "
                  f"{p['Pro_salePrice']:<8.2f} | {p['Pro_amount']:<5} | "
                  f"{p['Category']:<8} | {p['Pro_status']}")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการแสดงสินค้า: {e}")

def show_product_logs():
    """แสดง log ของ Product"""
    try:
        if not os.path.exists(PRODUCT_LOG_FILE):
            print("⚠️ ไม่มี log")
            return
        
        print("\n=== Product Logs ===")
        with open(PRODUCT_LOG_FILE, "rb") as f:
            count = 0
            while True:
                data = f.read(product_log_size)
                if not data:
                    break
                if len(data) != product_log_size:
                    print(f"⚠️ พบข้อมูล log ที่เสียหาย")
                    break
                log = unpack_product_log(data)
                if log:
                    print(f"{log['ts']} | Op:{log['op_code']} | {log['Pro_id']} | "
                          f"{log['Pro_name']} | Cost:{log['Pro_cost']:.2f} | "
                          f"Sale:{log['Pro_salePrice']:.2f} | Amt:{log['Pro_amount']} | "
                          f"Cat:{log['Category']} | Status:{log['Pro_status']} | User:{log['User']}")
                    count += 1
            
            if count == 0:
                print("⚠️ ไม่มี log")
    except PermissionError:
        print(f"❌ ไม่มีสิทธิ์อ่านไฟล์ {PRODUCT_LOG_FILE}")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการแสดง log: {e}")

# ====== Customer Functions ======
def add_customer():
    """เพิ่มลูกค้าใหม่"""
    try:
        customers = load_customers()
        
        # รับ Cust_id
        while True:
            cid = input_with_length(f"Cust_id (max {customer_max_lengths['Cust_id']}): ", 
                                   customer_max_lengths["Cust_id"])
            if cid is None:
                print("⚠️ ยกเลิกการเพิ่มลูกค้า")
                return
            if cid in customers:
                print("❌ Cust_id มีอยู่แล้ว")
                continue
            break
        
        # รับ Cust_name
        cname = input_with_length(f"Cust_name (max {customer_max_lengths['Cust_name']}): ", 
                                 customer_max_lengths["Cust_name"])
        if cname is None:
            print("⚠️ ยกเลิกการเพิ่มลูกค้า")
            return
        
        # รับ Cust_tel
        ctel = input_with_length(f"Cust_tel (max {customer_max_lengths['Cust_tel']}): ", 
                                customer_max_lengths["Cust_tel"])
        if ctel is None:
            print("⚠️ ยกเลิกการเพิ่มลูกค้า")
            return
        
        # รับ Cust_status
        status_input = input("Cust_status (1=ซื้อได้,0=ยกเลิก) [default=1]: ").strip()
        status = int(status_input) if status_input in ["0", "1"] else 1
        
        # รับ User
        user = input_with_length("User [default admin]: ", customer_max_lengths["User"], default="admin")
        if user is None:
            user = "admin"
        
        # สร้างลูกค้าใหม่
        new_customer = {
            "Cust_id": cid,
            "Cust_name": cname,
            "Cust_tel": ctel,
            "Cust_status": status
        }
        
        customers[cid] = new_customer
        
        if save_customers(customers):
            log_customer(1, new_customer, user)
            print(f"✅ เพิ่มลูกค้า {cid} สำเร็จ")
        else:
            print("❌ ไม่สามารถบันทึกลูกค้าได้")
    except KeyboardInterrupt:
        print("\n⚠️ ยกเลิกการเพิ่มลูกค้า")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")

def delete_customer():
    """ลบลูกค้า"""
    try:
        customers = load_customers()
        
        if not customers:
            print("⚠️ ไม่มีลูกค้าในระบบ")
            return
        
        cid = input("Cust_id ที่ต้องการลบ: ").strip()
        
        if not cid:
            print("❌ กรุณากรอก Cust_id")
            return
        
        if cid not in customers:
            print("❌ ไม่พบ Cust_id นี้")
            return
        
        # ยืนยันการลบ
        confirm = input(f"ยืนยันการลบลูกค้า {cid} - {customers[cid]['Cust_name']} (y/n): ").strip().lower()
        if confirm != 'y':
            print("⚠️ ยกเลิกการลบ")
            return
        
        deleted = customers.pop(cid)
        
        if save_customers(customers):
            deleted_log = deleted.copy()
            deleted_log["Cust_status"] = 2
            log_customer(3, deleted_log)
            print(f"🗑️ ลบลูกค้า {cid} เรียบร้อย")
        else:
            # คืนค่าถ้าบันทึกไม่สำเร็จ
            customers[cid] = deleted
            print("❌ ไม่สามารถลบลูกค้าได้")
    except KeyboardInterrupt:
        print("\n⚠️ ยกเลิกการลบลูกค้า")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")

def show_customers():
    """แสดงลูกค้าทั้งหมด"""
    try:
        customers = load_customers()
        
        if not customers:
            print("⚠️ ไม่มีลูกค้า")
            return
        
        print("\n=== All Customers ===")
        print(f"{'Cust_id':<10} | {'Cust_name':<50} | {'Tel':<10} | Status")
        print("-" * 80)
        
        for c in customers.values():
            print(f"{c['Cust_id']:<10} | {c['Cust_name']:<50} | {c['Cust_tel']:<10} | {c['Cust_status']}")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการแสดงลูกค้า: {e}")

def show_customer_logs():
    """แสดง log ของ Customer"""
    try:
        if not os.path.exists(CUSTOMER_LOG_FILE):
            print("⚠️ ไม่มี log")
            return
        
        print("\n=== Customer Logs ===")
        with open(CUSTOMER_LOG_FILE, "rb") as f:
            count = 0
            while True:
                data = f.read(customer_log_size)
                if not data:
                    break
                if len(data) != customer_log_size:
                    print(f"⚠️ พบข้อมูล log ที่เสียหาย")
                    break
                log = unpack_customer_log(data)
                if log:
                    print(f"{log['ts']} | Op:{log['op_code']} | {log['Cust_id']} | "
                          f"{log['cust_name_after']} | Tel:{log['cust_tel_after']} | "
                          f"Status:{log['cust_status_after']} | User:{log['User']}")
                    count += 1
            
            if count == 0:
                print("⚠️ ไม่มี log")
    except PermissionError:
        print(f"❌ ไม่มีสิทธิ์อ่านไฟล์ {CUSTOMER_LOG_FILE}")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการแสดง log: {e}")
