print("Getraenkeautomat")
print("1 - Wasser")
print("2 - Cola")
print("3 - Saft")

selection = input("Bitte waehle ein Getraenk: ")

if selection == "1":
    drink = "Wasser"
elif selection == "2":
    drink = "Cola"
elif selection == "3":
    drink = "Saft"
else:
    print("Fehler: Diese Auswahl gibt es nicht.")
    drink = None

if drink is not None:
    money = input("Bitte 50 oder 100 Cent einwerfen: ")

    if money == "100":
        print(f"{drink} wird ausgegeben.")
    elif money == "50":
        second_money = input("Es fehlen noch 50 Cent. Bitte erneut einwerfen: ")
        if second_money == "50":
            print(f"{drink} wird ausgegeben.")
        elif second_money == "100":
            print(f"{drink} wird ausgegeben.")
            print("Rueckgeld: 50 Cent")
        else:
            print("Fehler: Unerlaubte Muenze.")
    else:
        print("Fehler: Nur 50 oder 100 Cent sind erlaubt.")
