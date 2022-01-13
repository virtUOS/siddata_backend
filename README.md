# siddata_backend
Dokumentation zum Aufsetzen einer Entwicklungsumgebung unter Windows oder Ubuntu Linux findet sich im Repository "documentation".
https://git.siddata.de/siddata/documentation

Das Backend nimmt ueber eine REST-Schnittstelle Daten entgegen und erlaubt 
grafische Darstellungen der Daten.

1. Python Environment aufsetzen mit Python 3.7.
2. Django installieren.
3. python manage.py migrate
4. python manage.py createsuperuser
5. python manage.py runserver

Regeln zur Nutzung:
- Aussagekraeftige Kommentare
- Alle Commits werden Issues zugeordnet (#issue) mit folgenden Keywords:
  - close ,closes, closed (schließt Issue)
  - fix, fixes, fixed (schließt Issue)
  - resolve, resolves, resolved (schließt Issue)
  - refs (schließt Issue nicht)
 -Bei jedem Pull-Request auf den Server wird ein Tag (z.B. UOS_Server-Installation_2019_04_01) vergeben.
