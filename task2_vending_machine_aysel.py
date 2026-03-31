drinks = ["Wasser", "Cola", "Saft"]

print("Willkommen.")
print("Unser Automat verkauft:")
for index, drink in enumerate(drinks, start=1):
    print(f"{index} - {drink}")

choice = input("Bitte waehle 1, 2 oder 3: ")

if not choice.isdigit():
    print("Fehler: Bitte eine Zahl eingeben.")
else:
    number = int(choice)

    if number < 1 or number > 3:
        print("Fehler: Auswahl ungueltig.")
    else:
        selected_drink = drinks[number - 1]
        amount = 0

        while amount < 100:
            coin = input("Muenze einwerfen (50 oder 100): ")

            if coin == "50":
                amount += 50
            elif coin == "100":
                amount += 100
            else:
                print("Diese Muenze wird nicht akzeptiert.")
                continue

        print(f"{selected_drink} wird ausgegeben.")

        if amount > 100:
            print(f"Rueckgeld: {amount - 100} Cent")
