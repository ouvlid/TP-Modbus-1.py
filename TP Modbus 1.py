import serial
import struct
import time

# Fonction pour calculer le CRC Modbus
def calculate_crc(data):
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for _ in range(8):
            if (crc & 0x0001) != 0:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc

# Configurer le port série pour COM1 (envoi)
ser_com1 = serial.Serial(
    port='COM1',         # Utiliser COM1 pour envoyer la trame
    baudrate=9600,       # Baudrate : 9600 bauds
    bytesize=serial.EIGHTBITS,  # 8 bits de données
    parity=serial.PARITY_NONE,  # Pas de parité
    stopbits=serial.STOPBITS_ONE,  # 1 bit de stop
    timeout=1            # Timeout pour la lecture
)

# Configurer le port série pour COM2 (lecture)
ser_com2 = serial.Serial(
    port='COM2',         # Utiliser COM2 pour lire la trame
    baudrate=9600,       # Baudrate : 9600 bauds
    bytesize=serial.EIGHTBITS,  # 8 bits de données
    parity=serial.PARITY_NONE,  # Pas de parité
    stopbits=serial.STOPBITS_ONE,  # 1 bit de stop
    timeout=1            # Timeout pour la lecture
)

# Trame Modbus à envoyer (sans CRC pour le moment)
trame = [0x01, 0x01, 0x01, 0x0F, 0x00, 0x10]

# Calcul du CRC et ajout à la trame
crc = calculate_crc(trame)
crc_bytes = struct.pack('<H', crc)  # Conversion du CRC en 2 octets (little-endian)
trame.extend(crc_bytes)  # Ajouter le CRC à la trame

# Envoyer la trame via COM1
ser_com1.write(bytearray(trame))
print("Trame envoyée sur COM1:", ' '.join(format(x, '02X') for x in trame))

# Attendre un moment pour donner le temps à COM2 de recevoir les données
time.sleep(1)

# Lecture de la trame via COM2
response = ser_com2.read(8)  # Lire 8 octets (en fonction de la longueur de la réponse attendue)
if response:
    print("Trame reçue sur COM2 : ", ' '.join(format(x, '02X') for x in response))
    
    # Séparer les données et le CRC reçu
    received_data = response[:-2]  # Données sans les 2 derniers octets (CRC)
    received_crc = struct.unpack('<H', response[-2:])[0]  # CRC reçu (2 derniers octets)
    
    # Calculer le CRC des données reçues
    calculated_crc = calculate_crc(received_data)
    
    # Comparer le CRC calculé avec le CRC reçu
    if calculated_crc == received_crc:
        print(f"CRC valide : {hex(received_crc)}")
    else:
        print(f"Erreur CRC : CRC reçu = {hex(received_crc)}, CRC calculé = {hex(calculated_crc)}")
else:
    print("Aucune réponse reçue sur COM2.")

# Fermer les ports série après l'envoi et la lecture
ser_com1.close()
ser_com2.close()
