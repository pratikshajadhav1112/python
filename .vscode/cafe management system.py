# Cafe Management System

menu = {
    "Tea": 10,
    "Coffee": 20,
    "Burger": 80,
    "Pizza": 150,
    "Sandwich": 50
}

total_bill = 0

print("===== Welcome to Cafe =====")
print("\nMenu:")

for item, price in menu.items():
    print(f"{item} : ₹{price}")

while True:
    item = input("\nEnter item name: ")

    if item in menu:
        quantity = int(input("Enter quantity: "))

        item_total = menu[item] * quantity
        total_bill += item_total

        print(f"{item} x {quantity} = ₹{item_total}")

    else:
        print("Item not available!")

    another = input("Do you want to order another item? (yes/no): ")

    if another.lower() != "yes":
        break

print("\n===== BILL =====")
print(f"Total Amount = ₹{total_bill}")
print("   *** Thank You! Visit Again. *** ")