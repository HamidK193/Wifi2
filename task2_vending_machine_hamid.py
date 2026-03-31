def vending_machine():
    """Simuliert einen einfachen Getraenkeautomaten."""

    drinks = {
        "1": "Wasser",
        "2": "Cola",
        "3": "Saft"
    }

    drink_price_in_cents = 100

    print("Willkommen beim Getraenkeautomaten.")
    print("Bitte waehle ein Getraenk:")
    print("1 - Wasser")
    print("2 - Cola")
    print("3 - Saft")

    choice = input("Deine Auswahl: ")

    if choice not in drinks:
        print("Ungueltige Auswahl.")
        return

    selected_drink = drinks[choice]
    print(f"Du hast {selected_drink} gewaehlt.")
    print(f"Der Preis betraegt {drink_price_in_cents} Cent.")

    inserted_amount_in_cents = 0

    while inserted_amount_in_cents < drink_price_in_cents:
        coin = input("Bitte 50 oder 100 Cent einwerfen: ")

        if coin not in ["50", "100"]:
            print("Ungueltige Muenze. Erlaubt sind nur 50 oder 100 Cent.")
            continue

        inserted_amount_in_cents += int(coin)
        print(f"Aktueller Betrag: {inserted_amount_in_cents} Cent")

    print(f"{selected_drink} wird ausgegeben.")

    if inserted_amount_in_cents > drink_price_in_cents:
        change = inserted_amount_in_cents - drink_price_in_cents
        print(f"Rueckgeld: {change} Cent")

    print("Vielen Dank fuer deinen Einkauf.")


vending_machine()
