from pathlib import Path

from src.io.load_wifi_csv import load_wifi_csv, print_column_names


def main() -> None:
    csv_path = Path("data/raw/wifi_measurements.csv")

    if not csv_path.exists():
        print(f"Keine CSV-Datei gefunden: {csv_path}")
        print("Lege eine Messdatei in data/raw/ ab und starte das Skript erneut.")
        return

    dataframe = load_wifi_csv(csv_path, skip_first_row=False)
    print(f"Anzahl Zeilen: {len(dataframe)}")
    print_column_names(dataframe)


if __name__ == "__main__":
    main()
