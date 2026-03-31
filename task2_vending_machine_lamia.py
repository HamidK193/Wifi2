def choose_drink():
    drinks = {
        "wasser": "Wasser",
        "cola": "Cola",
        "saft": "Saft",
    }

    print("Verfuegbare Getraenke: Wasser, Cola, Saft")
    choice = input("Bitte gib dein Getraenk ein: ").lower()

    if choice not in drinks:
        print("Dieses Getraenk gibt es nicht.")
        return None

    return drinks[choice]


drink = choose_drink()

if drink is not None:
    total = 0

    while total < 100:
        coin = input("Bitte 50 oder 100 Cent einwerfen: ")

        if coin == "50":
            total += 50
        elif coin == "100":
            total += 100
        else:
            print("Falsche Eingabe.")
            continue

        print(f"Bisher eingeworfen: {total} Cent")

    print(f"{drink} wird ausgegeben.")

    if total > 100:
        print(f"Rueckgeld: {total - 100} Cent")
