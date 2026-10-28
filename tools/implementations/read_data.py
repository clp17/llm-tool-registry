def read_data(percorso_file):
    """
    Legge un file CSV semplice e restituisce i dati come lista di dizionari.

    Il CSV deve avere:
    - una prima riga con i nomi delle colonne;
    - campi separati da virgole;
    - nessuna virgola all'interno dei valori.

    Parametri:
        percorso_file (str): percorso del file CSV da leggere.

    Restituisce:
        list[dict]: una lista di dizionari. Ogni dizionario rappresenta una riga:
        i nomi delle colonne sono le chiavi e i valori della riga sono i valori.
        Se il file è vuoto, restituisce una lista vuota.

    Esempio:
        Se il file contiene:

            nome,età
            Anna,30

        la funzione restituisce:

            [{"nome": "Anna", "età": "30"}]
    """
    with open(percorso_file, "r", encoding="utf-8") as file:
        righe = [riga.strip() for riga in file if riga.strip()]

    if not righe:
        return []

    intestazioni = righe[0].split(",")
    risultati = []

    for riga in righe[1:]:
        valori = riga.split(",")
        risultati.append(dict(zip(intestazioni, valori)))

    return risultati
