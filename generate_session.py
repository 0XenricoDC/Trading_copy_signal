"""Script per generare la Telegram Session String."""

from telethon.sync import TelegramClient
from telethon.sessions import StringSession

print("="*60)
print("GENERATORE SESSION STRING TELEGRAM")
print("="*60)
print()

API_ID = input("Inserisci TELEGRAM_API_ID: ").strip()
API_HASH = input("Inserisci TELEGRAM_API_HASH: ").strip()

print()
print("Connessione a Telegram...")
print("Ti verra' chiesto il numero di telefono (es: +393331234567)")
print("Poi riceverai un codice su Telegram da inserire qui.")
print()

with TelegramClient(StringSession(), int(API_ID), API_HASH) as client:
    session_string = client.session.save()
    print()
    print("="*60)
    print("SUCCESSO! Copia la stringa qui sotto nel file .env")
    print("="*60)
    print()
    print("TELEGRAM_SESSION_STRING=" + session_string)
    print()
    print("="*60)
    print("Incolla questa riga nel file:")
    print("docker\\.env")
    print("="*60)
