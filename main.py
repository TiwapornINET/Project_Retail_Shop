# import add_del
import update
import sale
import update_view_cust
import add_del_pd_cs
import edit_sale
import Report

while True:
    print("\n" + "="*50)
    print("RETAIL SHOP SYSTEM")
    print("="*50)
    print("1. Make a sale")
    print("2. Add")
    print("3. Update")
    print("4. Delete")
    print("5. View")
    print("6. View Change")
    print("7. Report Product")
    print("8. Report Sale")
    print("9. Generate Report")
    print("10. Exit")
    print("="*50)

    try:
        choice = input("Enter your choice (1-10): ").strip()
            
        if choice == "1":
            sale.sale()
                
        elif choice == "2":
            while True:
                try:
                    print('1. Add Product')
                    print('2. Add Customer')
                    choice_add = input('Enter menu add : ')
                    if choice_add == '1':
                        add_del_pd_cs.add_product()
                        break
                    elif choice_add == '2':
                        add_del_pd_cs.add_customer()
                        break
                    else:
                        print("Invalid choice, please select 1 or 2.")
                except Exception as e:
                    print("Unexpected error in add menu:", e)

            
                
        elif choice == "3":
            while True:
                try:
                    print('1. Update Product')
                    print('2. Update Customer')
                    print('3. Update Sale')
                    choice_add = input('Enter menu update : ')
                    if choice_add == "1" :
                        update.update_product()
                        break
                    elif choice_add == '2':
                        update_view_cust.update_Customer()
                        break
                    elif choice_add == '3':
                        edit_sale.update_sale()
                        break
                    else:
                        print("Invalid choice, please select 1 or 2.")
                except Exception as e:
                    print("Unexpected error in update menu:", e)
                
        elif choice == "4":
            while True:
                try:
                    print('1. Delete Product')
                    print('2. Delete Customer')
                    print('3. Delete Sale')
                    choice_add = input('Enter menu delete : ')
                    if choice_add == '1' :
                        add_del_pd_cs.delete_product()
                        break
                    elif choice_add == '2':
                        add_del_pd_cs.delete_customer()
                        break
                    elif choice_add == '3':
                        sale.delete_sale()
                        break
                    else:
                        print("Invalid choice, please select 1 or 2.")
                except Exception as e:
                    print("Unexpected error in delete menu:", e)
            
                
        elif choice == "5":
            while True:
                try:
                    print('1. View Product')
                    print('2. View Customer')
                    choice_add = input('Enter menu view : ')
                    if choice_add == '1' :
                        update.view_products_with_tabulate()
                        break
                    elif choice_add == '2':
                        update_view_cust.view_Customers_with_tabulate()
                        break
                    else:
                        print("Invalid choice, please select 1 or 2.")
                except Exception as e:
                    print("Unexpected error in view menu:", e)

            
                
        elif choice == "6":
            while True:
                try:
                    print('1 View Product Change')
                    print('2 View Customer Change')
                    choice_add = input('Enter menu view change : ')
                    if choice_add == '1' :
                        update.view_change_log()
                        break
                    elif choice_add == '2':
                        update_view_cust.view_change_log()
                        break
                    else:
                        print("Invalid choice, please select 1 or 2.")
                except Exception as e:
                    print("Unexpected error in view change menu:", e)
            
        elif choice == "7":
            Report.Product_report()
            
        elif choice == "8":
            Report.Sale_Report()

        elif choice == "9":
            Report.generate_report()
                    
        elif choice == "10":
            print("Exit Retail Shop System!")
            break
                
        else:
            print("Invalid choice! Please select 1-10.")
                
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        break
    except Exception as e:
        print(f"Unexpected error: {e}")