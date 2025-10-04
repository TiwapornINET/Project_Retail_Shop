import struct
from datetime import datetime
from tabulate import tabulate
import os
# Customer format (main data file)
Customer_format = '10s50s10si'  
Customer_size = struct.calcsize(Customer_format)

log_format = "19sI10s50s10sI20s"
log_size = struct.calcsize(log_format)


# Constants for better maintainability
OPERATIONS = {1: "ADD", 2: "UPDATE", 3: "DELETE", 4: "VIEW"}
STATUS_NAMES = {0: "Cancel This Customer", 1: "Available To Buy"}
STATUS_REVERSE = { "Cancel This Customer": 0 ,  "Available To Buy": 1}

def log_change_binary(op_code, Customer_data, user):
    """
    Log changes with proper binary record formatting
    Ensures each record is exactly the right size for proper separation
    """
    try:
        # Create timestamp - pad to exactly 19 bytes
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 19 characters exactly
        timestamp_bytes = ts.encode('utf-8').ljust(19, b'\x00')[:19]
        
        # Prepare Customer data - ensure exact byte lengths
        cust_id = str(Customer_data[0]).encode('utf-8').ljust(10, b'\x00')[:10]
        custname = str(Customer_data[1]).encode('utf-8').ljust(50, b'\x00')[:50]
        cust_tel = str(Customer_data[2]).encode('utf-8').ljust(10, b'\x00')[:10]
        cus_status  = int(Customer_data[3])
        user_bytes = str(user).encode('utf-8').ljust(20, b'\x00')[:20]
        
        # Pack the complete record
        record = struct.pack(log_format, 
                           timestamp_bytes,    # 19 bytes
                           op_code,           # 4 bytes (i)
                           cust_id,            # 10 bytes
                           custname,        # 50 bytes
                           cust_tel,        # 10 bytes 
                           cus_status,        # 4 bytes 
                           user_bytes)        # 20 bytes
        
        # Verify the record size is correct
        expected_size = struct.calcsize(log_format)
        if len(record) != expected_size:
            print(f"⚠️ Warning: Record size mismatch! Expected {expected_size}, got {len(record)}")
            return False
        
        # Write the complete record as one atomic operation
        with open("customer_change.bin", "ab") as f:
            f.write(record)
            f.flush()  # Ensure data is written immediately
        
        print(f"📝 Logged: {OPERATIONS.get(op_code, 'UNKNOWN')} Customer {Customer_data[0]} by {user} ({len(record)} bytes)")
        return True
        
    except (ValueError, IndexError) as e:
        print(f"❌ Error logging change: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error in logging: {e}")
        return False

def read_all_Customers():
    """Helper function to read all Customers from binary file"""
    data = []
    try:
        with open("Customer.dat", "rb") as f:
            while True:
                chunk = f.read(Customer_size)
                if not chunk:
                    break
                if len(chunk) < Customer_size:
                    continue
                record = struct.unpack(Customer_format, chunk)
                data.append(record)
        return data
    except FileNotFoundError:
        print("❌ Customer file not found!")
        return []

def write_all_Customers(data):
    """Helper function to write all Customers to binary file"""
    try:
        with open('Customer.dat', 'wb') as f:
            for record in data:
                binary_record = struct.pack(Customer_format, *record)
                f.write(binary_record)
        return True
    except Exception as e:
        print(f"❌ Error writing to file: {e}")
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
                print("❌ This field is required!")
                continue
            elif not user_input:
                return None
        
        try:
            if data_type == float:
                value = float(user_input)
                if value < 0:
                    print("❌ Value cannot be negative!")
                    continue
                return value
            elif data_type == int:
                value = int(user_input)
                if value < 0:
                    print("❌ Value cannot be negative!")
                    continue
                return value
            else:
                return user_input
        except ValueError:
            print(f"❌ Invalid {data_type.__name__} value!")

def update_Customer():
    """Update Customer in binary file with improved validation"""
    data = read_all_Customers()
    if not data:
        return
    
    user = get_user_input("User", required=True)
    cust_id = get_user_input("Enter Customer ID to update", required=True)
    
    # Find and update record
    for i, record in enumerate(data):
        current_id = record[0].decode().strip("\x00")
        if current_id == cust_id:
            # Get current values
            current_name = record[1].decode().strip("\x00")
            current_tel = record[2].decode().strip("\x00")
            current_status = record[3]
            
            
            print(f"✅ Found Customer: {current_id} - {current_name}")
            print(f"Current status: {STATUS_NAMES.get(current_status, current_status)}")
            
            # Input new values with validation
            name = get_user_input("New Name", current_name)
            tel = get_user_input("New tel", current_tel,)
            
            
            # Status input with validation
            print("\nStatus options: 0 = Cancel This Customer , 1 = Available To Buy")
            status = get_user_input("New Status", current_status, int)
            if status not in STATUS_NAMES:
                print("❌ Invalid status! Using current value.")
                status = current_status
            
            # Create updated binary record
            cust_id_bytes = cust_id.encode().ljust(13, b'\x00')
            name_bytes = name.encode().ljust(20, b'\x00')
            tel_bytes = tel.encode().ljust(12, b'\x00')
            
            updated_record = struct.pack(Customer_format,
                                       cust_id_bytes, name_bytes, tel_bytes, status)
            
            # Replace the record in data list
            data[i] = struct.unpack(Customer_format, updated_record)
            
            # Write back to file
            if write_all_Customers(data):
                # Log the update
                Customer_data = [cust_id, name, tel, status]
                log_change_binary(2, Customer_data, user)
                print("✅ Customer updated successfully!")
            else:
                print("❌ Failed to save changes!")
            return
    
    print("❌ Customer ID not found.")

def format_Customer_record(record):
    """Helper function to format Customer record for display"""
    decoded_record = (
        record[0].decode().strip("\x00"),
        record[1].decode().strip("\x00"),
        record[2].decode().strip("\x00"),
        record[3]
    )
    
    status_text = STATUS_NAMES.get(decoded_record[3], f"Status {decoded_record[3]}")
    
    return [
        decoded_record[0],   # Cust_id
        decoded_record[1],   # Cust_name
        decoded_record[2],   # Category
        status_text  # Cust_status
    ]

def view_Customers_with_tabulate():
    """View Customers with improved search and automatic logging"""
    print("\nSearch option:")
    print("1. Specific Customer")
    print("2. All Customers")
    
    
    try:
        view_choice = int(input("Choose option: "))
    except ValueError:
        print("Invalid choice!")
        return

    # Get user name for logging
    user = get_user_input("User", required=True)

    data = read_all_Customers()
    if not data:
        return

    formatted_data = [format_Customer_record(record) for record in data]
    headers = ["Cust_id", "Cust_name", "Cust_tel","Cust_status"]

    if view_choice == 1:
        Customer_id = get_user_input("Enter Customer ID", required=True)
        filtered_data = [row for row in formatted_data if row[0] == Customer_id]
        
        if filtered_data:
            print(f"\n=== Search Result for {Customer_id} ===")
            print(tabulate(filtered_data, headers=headers, tablefmt="grid"))
            
            # Log the VIEW operation for the specific Customer
            original_record = next((row for row in formatted_data if row[0] == Customer_id), None)
            if original_record:
                Customer_data = [
                    original_record[0],
                    original_record[1],
                    original_record[2],
                    STATUS_REVERSE.get(original_record[3], 1)
                ]
                log_change_binary(4, Customer_data, user)  # op_code 4 = VIEW
        else:
            print(f"Customer ID {Customer_id} not found!")
            
    elif view_choice == 2:
        print(f"\n=== Customer List ({len(formatted_data)} Customers) ===")
        print(tabulate(formatted_data, headers=headers, tablefmt="grid"))
        
        # Log VIEW operation for all Customers view - use first Customer as representative
        if formatted_data:
            first_Customer = formatted_data[0]
            Customer_data = [
                first_Customer[0],
                first_Customer[1],
                first_Customer[2],
                STATUS_REVERSE.get(first_Customer[3], 1)
            ]
            log_change_binary(4, Customer_data, user)  # Log as VIEW ALL operation
        
    

def view_change_log():
    """View change log with user field support"""
    
    if not os.path.exists("customer_change.bin"):
        print("📄 No change log found!")
        return
    
    # Check file format 
    file_size = os.path.getsize("customer_change.bin")
    if file_size % log_size != 0:
        print("⚠️  Warning: Log file might be corrupted!")
        print(f"File size: {file_size} bytes, Expected record size: {log_size} bytes")
        print("❌ Cannot modify existing log file. Continuing with current data...")
    
    changes = []
    
    try:
        with open("customer_change.bin", "rb") as f:
            record_num = 1
            while True:
                chunk = f.read(log_size)
                if not chunk:
                    break
                    
                if len(chunk) < log_size:
                    print(f"⚠️ Incomplete record #{record_num}, skipping...")
                    continue
                
                try:
                    # Unpack log record with user field
                    record = struct.unpack(log_format, chunk)
                    
                    # Decode strings properly
                    timestamp = record[0].decode('utf-8', errors='ignore').strip('\x00')
                    op_code = record[1]
                    Cust_id = record[2].decode('utf-8', errors='ignore').strip('\x00')
                    name_after = record[3].decode('utf-8', errors='ignore').strip('\x00')
                    tel_after = record[4].decode('utf-8', errors='ignore').strip('\x00')
                    status_after = record[5]
                    user = record[6].decode('utf-8', errors='ignore').strip('\x00')
                    
                    changes.append([
                        record_num,
                        OPERATIONS.get(op_code, f"OP_{op_code}"),
                        timestamp,
                        Cust_id,
                        name_after,
                        tel_after,
                        STATUS_NAMES.get(status_after, f"Status_{status_after}"),
                        user
                    ])
                    
                except (struct.error, UnicodeDecodeError) as e:
                    print(f"⚠️ Error reading record #{record_num}: {e}")
                    continue
                
                record_num += 1
                
    except Exception as e:
        print(f"❌ Error reading log file: {e}")
        return
    
    if changes:
        # Headers with User column
        headers = ["#", "Action", "Timestamp", "Customer_ID", "Name", "Tel", "Status", "User"]
        print(f"\n=== Change Log ({len(changes)} records) ===")
        print(tabulate(changes, headers=headers, tablefmt="grid"))
        
        # Enhanced summary
        summary = {}
        for change in changes:
            action = change[1]
            summary[action] = summary.get(action, 0) + 1
        
        print(f"\n📊 Summary:")
        for action, count in summary.items():
            emoji = {"ADD": "➕", "UPDATE": "✏️", "DELETE": "🗑️", "VIEW": "👁️"}.get(action, "❓")
            print(f"   {emoji} {action}: {count}")
        
        if changes:
            print(f"   📅 Time range: {changes[0][2]} to {changes[-1][2]}")
    else:
        print("📄 No change records found")


