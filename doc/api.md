API

# Ziele eintragen

Endpoint: `api/goals`

Methode: `POST`

Datenstruktur:

    { "goal": "<Text des Ziels>",
        "origin": "<Identifier der Quelle, z.B. de.uos.studip>",
        "origin_id": "<ID der NutzerIn, eindeutig für Origin>",
        "age":<Alter der NutzerIn als Integer>,
        "study": [   # Liste von Studiengangsinformationen
        {"degree": <ID des Abschlusses gem. synchronisierter Abschlusstabelle>,
            "subject": <ID des Studienfachen gem. synchr. Abschlusstabelle>,
            "semester": <Nummer des Fachsemester >=0>
        }
    }
Return: 200 und Json: 
    
    {"goal_id":"<ID des Ziels>",}
    
# Ziel löschen

Endpoint: `api/goals/<id>`

Methode: `DELETE`

Return: 200 & Json: 

    {'ok': True} 

sonst Fehler


# Ziele für einen Nutzer abfragen

Endpoint: `api/goals/?origin=<de.uos.studip>&origin_id=<NutzerID>`

Methode: `GET`

Return: 200 und alle Ziele zum Nutzer in Json:

    [{"id": "<ID des Ziels>", "goal": "<Text zum Ziel>", "makedate": "<Timedate>", "user_id": <ID des Users>}]


sonst Fehler



