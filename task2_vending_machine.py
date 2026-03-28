def vending_machine():
    """Simuliert einen einfachen Getränkeautomaten."""

    drinks = {
        "1": "Wasser",
        "2": "Cola",
        "3": "Saft"
    }

    drink_price_in_cents = 100

    print("Willkommen beim Getränkeautomaten.")
    print("Bitte wähle ein Getränk:")
    print("1 - Wasser")
    print("2 - Cola")
    print("3 - Saft")

    choice = input("Deine Auswahl: ")

    if choice not in drinks:
        print("Ungültige Auswahl.")
        return

    selected_drink = drinks[choice]
    print(f"Du hast {selected_drink} gewählt.")
    print(f"Der Preis beträgt {drink_price_in_cents} Cent.")

    inserted_amount_in_cents = 0

    while inserted_amount_in_cents < drink_price_in_cents:
        coin = input("Bitte 50 oder 100 Cent einwerfen: ")

        if coin not in ["50", "100"]:
            print("Ungültige Münze. Erlaubt sind nur 50 oder 100 Cent.")
            continue

        inserted_amount_in_cents += int(coin)
        print(f"Aktueller Betrag: {inserted_amount_in_cents} Cent")

    print(f"{selected_drink} wird ausgegeben.")

    if inserted_amount_in_cents > drink_price_in_cents:
        change = inserted_amount_in_cents - drink_price_in_cents
        print(f"Rückgeld: {change} Cent")

    print("Vielen Dank für deinen Einkauf.")


vending_machine()