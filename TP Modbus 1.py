import serial

def calculate_crc(data):
    """
    Calcul du CRC16 Modbus
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF

def validate_crc(data):
    """
    Valide le CRC d'une trame reçue
    """
    if len(data) < 3:
        return False
    received_crc = (data[-1] << 8) | data[-2]
    calculated_crc = calculate_crc(data[:-2])
    return received_crc == calculated_crc

def read_response(port):
    """
    Lit la réponse du port série et valide le CRC
    """
    try:
        response = port.read(256)  # Lire jusqu'à 256 octets
        if len(response) == 0:
            print("Aucune réponse reçue.")
            return

        response = list(response)  # Convertir en liste d'octets
        print("Réponse reçue :", ' '.join(f"{byte:02X}" for byte in response))

        if validate_crc(response):
            print("CRC valide. Réponse correcte.")
        else:
            print("CRC invalide. Réponse corrompue.")
    except Exception as e:
        print("Erreur lors de la lecture de la réponse :", e)

def build_trame_mission(robot_id, number_of_operations, operations):
    """
    Construit la trame Modbus pour écrire des missions
    """
    trame = [robot_id, 0x10, 0x00, 0x13, 0x00, 1 + len(operations), (1 + len(operations)) * 2]
    trame.extend([0x00, number_of_operations])  # Ajout de W20 (nombre d'opérations)
    for travail, station in operations:
        value = (travail << 8) | station  # Combine travail et station
        trame.extend([(value >> 8) & 0xFF, value & 0xFF])  # Ajoute les octets (poids fort et faible)

    crc = calculate_crc(trame)
    trame.extend([crc & 0xFF, (crc >> 8) & 0xFF])  # CRC
    return trame

def build_trame_launch(robot_id):
    """
    Construit la trame Modbus pour lancer une mission (écriture d’un bit, bit 272)
    """
    trame = [robot_id, 0x05, 0x01, 0x0F, 0xFF, 0x00]
    crc = calculate_crc(trame)
    trame.extend([crc & 0xFF, (crc >> 8) & 0xFF])  # CRC
    return trame

def build_trame_read_tor(robot_id):
    """
    Construit une trame standard pour lire les variables TOR de 271 à 287
    """
    # Adresse de départ = 271 (0x010F), Nombre de bits = 17 (0x11)
    trame = [robot_id, 0x02, 0x01, 0x0F, 0x00, 0x11]
    crc = calculate_crc(trame)
    trame.extend([crc & 0xFF, (crc >> 8) & 0xFF])  # CRC
    return trame

def main():
    # Configuration du port série
    port = serial.Serial(
        port='COM2',
        baudrate=9600,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_ODD,
        stopbits=serial.STOPBITS_ONE,
        timeout=1
    )

    while True:
        print("\n=== Menu Principal ===")
        print("1. Écrire des missions")
        print("2. Lancer une mission")
        print("3. Lire l'état des variables TOR (271 à 287)")
        print("X. Quitter")

        choice = input("Choisissez une option : ").strip().upper()

        if choice == '1':  # Écrire des missions
            while True:
                try:
                    robot_id = int(input("Numéro du robot (1-4) : "))
                    if 1 <= robot_id <= 4:
                        break
                    print("Veuillez entrer un numéro valide (entre 1 et 4).")
                except ValueError:
                    print("Veuillez entrer un nombre entier valide.")

            while True:
                try:
                    number_of_operations = int(input("Nombre de missions (1-3) : "))
                    if 1 <= number_of_operations <= 3:
                        break
                    print("Le nombre de missions doit être compris entre 1 et 3.")
                except ValueError:
                    print("Veuillez entrer un nombre entier valide.")

            operations = []
            for i in range(number_of_operations):
                while True:
                    try:
                        travail = int(input(f"Mission {i+1} - Travail (0=Rien, 1=Chargement, 2=Déchargement) : "))
                        if 0 <= travail <= 2:
                            break
                        print("Le travail doit être compris entre 0 et 2.")
                    except ValueError:
                        print("Veuillez entrer un nombre entier valide.")
                
                while True:
                    try:
                        station = int(input(f"Mission {i+1} - Station (1-255) : "))
                        if 1 <= station <= 255:
                            operations.append((travail, station))
                            break
                        print("La station doit être comprise entre 1 et 255.")
                    except ValueError:
                        print("Veuillez entrer un nombre entier valide.")

            trame_mission = build_trame_mission(robot_id, number_of_operations, operations)
            print("Trame mission générée :", ' '.join(f"{byte:02X}" for byte in trame_mission))

            while True:
                envoyer = input("Voulez-vous envoyer cette trame ? (oui/non/X pour revenir au menu) : ").strip().lower()
                if envoyer == 'oui':
                    port.write(bytearray(trame_mission))
                    print("Trame mission envoyée.")
                    read_response(port)
                    break
                elif envoyer == 'non':
                    print("En attente de confirmation pour l'envoi...")
                elif envoyer == 'x':
                    break
                else:
                    print("Réponse non valide.")

        elif choice == '2':  # Lancer une mission
            while True:
                try:
                    robot_id = int(input("Numéro du robot (1-4) : "))
                    if 1 <= robot_id <= 4:
                        break
                    print("Veuillez entrer un numéro valide (entre 1 et 4).")
                except ValueError:
                    print("Veuillez entrer un nombre entier valide.")

            trame_launch = build_trame_launch(robot_id)
            print("Trame lancement générée :", ' '.join(f"{byte:02X}" for byte in trame_launch))

            while True:
                envoyer = input("Voulez-vous envoyer cette trame ? (oui/non/X pour revenir au menu) : ").strip().lower()
                if envoyer == 'oui':
                    port.write(bytearray(trame_launch))
                    print("Mission lancée avec succès.")
                    read_response(port)
                    break
                elif envoyer == 'non':
                    print("En attente de confirmation pour lancer la mission...")
                elif envoyer == 'x':
                    break
                else:
                    print("Réponse non valide.")

        elif choice == '3':  # Lire l'état des variables TOR
            while True:
                try:
                    robot_id = int(input("Numéro du robot (1-4) : "))
                    if 1 <= robot_id <= 4:
                        break
                    print("Veuillez entrer un numéro valide (entre 1 et 4).")
                except ValueError:
                    print("Veuillez entrer un nombre entier valide.")

            trame_read = build_trame_read_tor(robot_id)
            print("Trame lecture générée :", ' '.join(f"{byte:02X}" for byte in trame_read))

            while True:
                envoyer = input("Voulez-vous envoyer cette trame ? (oui/non/X pour revenir au menu) : ").strip().lower()
                if envoyer == 'oui':
                    port.write(bytearray(trame_read))
                    print("Trame de lecture envoyée.")
                    read_response(port)
                    break
                elif envoyer == 'non':
                    print("En attente de confirmation pour envoyer la lecture...")
                elif envoyer == 'x':
                    break
                else:
                    print("Réponse non valide.")

        elif choice == 'X':  # Quitter
            print("Fin du programme.")
            break

        else:
            print("Choix invalide. Veuillez réessayer.")

    port.close()

if __name__ == "__main__":
    main()
