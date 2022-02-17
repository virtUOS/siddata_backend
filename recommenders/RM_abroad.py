import json
import datetime
import logging

from backend import models
from recommenders.RM_BASE import RM_BASE
from settings import DEBUG

STAGES = ["Vor der Bewerbung",
          "Während der Bewerbung",
          "Vor der Abreise"]

STAGE_DESCRIPTIONS = [
    "Ich interessiere mich für einen Auslandsaufenthalt und möchte hilfreiche Tipps zur "
    "Vorbereitung erhalten.",
    "Ich weiß, wo es hingehen soll und möchte mich bewerben.",
    "Ich habe eine Zusage meiner Gastuniversität erhalten und möchte meine Abreise "
    "vorbereiten.",
]
NAME = "Auslandsaufenthalt"

class RM_abroad(RM_BASE):
    """ Processes activities related to going abroad.
    """

    def __init__(self):
        # this magic line of code lets our recommender inherit all attributes and methods from the baseclass.
        super().__init__()
        # This name should be unique and appears in the Stud.IP GUI.
        self.NAME = NAME
        # The description text summarizes the functionality. It is shown in teaser activity and tile view,
        self.DESCRIPTION = "Hier bekommst du Unterstützung bei Planung und Durchführung eines Auslandsaufenthaltes."
        # This text is displayed in Teaser Activities
        self.TEASER_TEXT = "Hast du mal über einen Auslandsaufenthalt nachgedacht? Die Möglichkeiten sind fast " \
                           "grenzenlos, aber es gibt auch vieles zu beachten und zu organisieren. Damit du " \
                           "durchstarten kannst, unterstützt dich Siddata bei den notwendigen Schritten von der " \
                           "Bewerbung bis zur Abreise."
        # If set to False, the recommender will not appear in the GUI or the DB
        self.ACTIVE = True
        # Image is shown in teaser activity
        self.IMAGE = "world.png"
        # determines arrangement in Frontend
        self.ORDER = 2
        # This string tells the user which data is required for this recommender
        self.DATA_INFO = "Diese Funktion speichert diejenigen Daten, die du aktiv eingibst und nutzt Informationen über " \
                         "deinen Standort um Empfehlungen für deine Uni geben zu können."
        # Reference to the database object, can be used as value vor recommender attribute in goals.
        self.recommender = models.Recommender.objects.get_or_create(
            name=self.get_name(),
            description=self.DESCRIPTION,
            classname=self.__class__.__name__,
            image=self.IMAGE,
            order=self.ORDER,
            data_info=self.DATA_INFO,
        )[0]

        self.checklist = {
            "Bremen": {
                "Vor der Bewerbung": [
                    {
                        "type": "resource",
                        "description": "Überlege dir, wo du hin möchtest und informiere dich über Kooperationen.",
                        "source": "https://www.uni-bremen.de/studium/starten-studieren/studium-international/studieren-im-ausland/erasmus-studienaufenthalt",
                    },
                    {
                        "type": "resource",
                        "description": "Lies einige Erfahrungsberichte von Studierenden, die bereits im Ausland waren.",
                        "source": "https://www.uni-bremen.de/studium/starten-studieren/studium-international/studieren-im-ausland/erasmus-studienaufenthalt/erfahrungsberichte",
                    },
                    {
                        "type": "resource",
                        "description": "Besuche eine Informationsveranstaltung. Den nächsten Termin erfährst du im International Office.",
                        "source": "https://www.uni-bremen.de/studium/starten-studieren/studium-international",
                    },
                    {
                        "type": "resource",
                        "description": "Nimm Kontakt zur Erasmus-Initiative auf. Dort erfährst du aus erster Hand, wie du deinen Auslandsaufenthalt organisierst.",
                        "source": "https://www.erasmus-initiative.uni-bremen.de/#land",
                    },
                    {
                        "type": "resource",
                        "description": "Nimm am Study-Buddy Programm teil und hole dir Tipps von Studis, die ihren Auslandsaufenthalt schon hinter sich haben.",
                        "source": "https://www.uni-bremen.de/studium/starten-studieren/angebote-fuer-internationale-studierende/kompass/study-buddy",
                    },
                    {
                        "type": "resource",
                        "description": "Frische deine Sprachkenntnisse auf. Eine Anlaufstelle ist das Fremdsprachenzentrum.",
                        "source": "https://www.fremdsprachenzentrum-bremen.de/?L=0",
                    },
                ],
                "Während der Bewerbung": [
                    {
                        "type": "todo",
                        "description": "Nimm Kontakt zum Erasmus-Verantwortlichen deiner Fakultät auf."
                                        "<ul><li><a href='https://www.uni-bremen.de/fb1/studium/studieren-im-ausland' target='_blank'>FB1</a></li> "
                                        "<li><a href='https://www.uni-bremen.de/fb2/studium/auslandsaufenthalt' target='_blank'>FB2</a></li> "
                                        "<li><a href='https://www.uni-bremen.de/fb3/studium-lehre/international' target='_blank'>FB3</a></li> "
                                        "<li><a href='https://www.fb4.uni-bremen.de/studium_ausland.html' target='_blank'>FB4</a></li> "
                                        "<li><a href='https://www.geo.uni-bremen.de/page.php?pageid=850' target='_blank'>FB5</a></li> "
                                        "<li><a href='https://www.uni-bremen.de/jura/fachbereich-6-rechtswissenschaft/studium/studierende/staatsexamen/erasmus' target='_blank'>FB6</a></li> "
                                        "<li><a href='https://www.uni-bremen.de/wiwi/internationales/outgoing-bremer-studierende-im-ausland' target='_blank'>FB7</a></li> "
                                        "<li><a href='https://www.uni-bremen.de/fb8/international' target='_blank'>FB8</a></li> "
                                        "<li><a href='https://www.uni-bremen.de/fb9/internationalitaet' target='_blank'>FB9</a></li> "
                                        "<li><a href='https://www.uni-bremen.de/fb-10/internationales' target='_blank'>FB10</a></li> "
                                        "<li><a href='https://www.uni-bremen.de/fb11/internationales' target='_blank'>FB11</a></li> "
                                        "<li><a href='https://www.uni-bremen.de/fb12/studium-lehre/erasmus/erasmus-studierende/wichtige-hinweise-fuer-die-erasmus-bewerbung' target='_blank'>FB12</a>"
                                        "</li></ul>"
                    },
                    {
                        "type": "todo",
                        "description": "Schaue dir die Partneruniversitäten an und wähle zunächst 2-3 Angebote aus, die für Dich in Frage kommen würden.",
                    },
                    {
                        "type": "todo",
                        "description": "Vergleiche die Kursangebote der Gastuniversitäten und suche dir nun ein Favorit aus.",
                    },
                    {
                        "type": "resource",
                        "description": "Erstelle eine Liste der benötigten Unterlagen in Absprache mit der Erasmus-Koordination "
                                        "deiner Fakultät. (Du kannst dich an dieser Liste orientieren, beachte aber dass jede "
                                        "Fakultät unterschiedliche Kriterien hat)",
                        "source": "https://www.uni-bremen.de/fileadmin/user_upload/sites/international/"
                                         "ERASMUS_Dokumente/ERASMUSBewerbungHinweise18_19.pdf",
                    },
                    {
                        "type": "todo",
                        "description": "Bereite dein Motivationsschreiben vor.",
                    },
                    {
                        "type": "todo",
                        "description": "Übersetze deinen Lebenslauf in die Sprache des Reiselandes (ggf. ist ein CV auf Englisch ausreichend)",
                    },
                    {
                        "type": "todo",
                        "description": "Erstelle die Übersicht deiner Leistungen (Notenspiegel), drucke es aus und bewahre es gut in digitaler und physischer Form.",
                    },
                    {
                        "type": "resource",
                        "description": "Lass dir die Sprachkenntnisse nachweisen, bzw. besuche einen Kurs am Sprachenzentrum.",
                        "source": "https://www.fremdsprachenzentrum-bremen.de/?L=0",
                    },
                    {
                        "type": "todo",
                        "description": "Hast du die Nominierung deiner Heimuniversität erhalten?",
                                     },
                                     {
                                         "type": "todo",
                                         "description": "Bewerbe Dich online an deiner Gastuniversität, drucke die Unterlagen aus und bewahre sie sorgfältig auf.",
                                     },
                                     {
                                         "type": "todo",
                                         "description": "Hast du die Bestätigung der Gastuniversität erhalten?",
                                     },
                                 ],
                                 "Vor der Abreise": [
                                     {
                                         "type": "todo",
                                         "description": "Suche dir passende Kurse an der Gastuniversität. Fülle das Online Learning Agreement "
                                                        "aus und leite es an deine Erasmus-Koordination. Bei Mobilität im WiSe: Abgabe bis 30. "
                                                        "April. Bei Mobilität im SoSe: Abgabe bis 30. September.",
                                     },
                                     {
                                         "type": "todo",
                                         "description": "Grant Agreement (Erasmus-Stipendium) unterzeichnen.",
                                     },
                                     {
                                         "type": "todo",
                                         "description": "Informiere Dich, ob eine Beurlaubung an der Heimuniversität für Dich notwendig ist.",
                                     },
                                     {
                                         "type": "todo",
                                         "description": "Im April: Besuche die obligatorische Infoveranstaltung für alle Outgoings.",
                                     },
                                     {
                                         "type": "resource",
                                         "description": "Gleich nach der Zusage: Informiere dich, ob dir AuslandsBAföG zusteht.",
                                         "source": "https://www.uni-hannover.de/fileadmin/Internationales/pdf/Wege_ins_Ausland/"
                                                   "Finanzierung/Zustaendigkeiten-Auslands-BAfoeG.pdf",
                                     },
                                     {
                                         "type": "todo",
                                         "description": "Finde heraus, ob du ein Visum oder eine Aufenthaltsberechtigung für das Gastland brauchst.",
                                     },
                                     {
                                         "type": "todo",
                                         "description": "Überprüfe, ob du eine zusätzliche Auslandsversicherung brauchst – dafür ist deine "
                                                        "Krankenkasse der richtige Ansprechpartner.",
                                     },
                                     {
                                         "type": "todo",
                                         "description": "Manche Gastuniversitäten bieten kostenlose Sprachkurse bei Ankunft an. Diese sind "
                                                        "wertvoll, um direkt Kontakte zu anderen Erasmus-Teilnehmenden zu knüpfen. Dafür muss "
                                                        "allerdings von zu Hause aus ein Einstufungstest durchgeführt werden. Suche solch "
                                                        "einen Test auf der Webseite der Gastuniversität.",
                                     },
                                     {
                                         "type": "todo",
                                         "description": "Ggf. einen „Buddy“ an der Gastuniversität finden.",
                                     },
                                     {
                                         "type": "todo",
                                         "description": "Suche dir eine passende Unterkunft. Damit kann dir die Gastuniversität ggf. "
                                                        "weiterhelfen.",
                                     },
                                     {
                                         "type": "todo",
                                         "description": "Buche einen Flug und freu Dich auf die Reise. Wir wünschen dir ein unvergessliches "
                                                        "Abenteuer.",
                                     },
                                 ],
                             },
            "Hannover": {
                    "Vor der Bewerbung": [
                        {
                            "type": "resource",
                            "description": "Überlege dir, wo du hin möchtest und informiere dich über Kooperationen. Wähle zunächst 2-3 "
                                                        "Angebote aus, die für Dich in Frage kommen würden.",
                            "source": "https://www.uni-hannover.de/de/studium/im-studium/international/outgoing/auslandsprogramme/",
                        },
                        {
                            "type": "todo",
                            "description": "Vergleiche die Kursangebote der Gastuniversitäten und suche dir nun einen Favoriten aus.",
                        },
                         {
                             "type": "resource",
                             "description": "Lies einige Erfahrungsberichte von Studierenden, die bereits im Ausland waren.",
                             "source": "https://www.uni-hannover.de/de/studium/im-studium/international/outgoing/auslandsprogramme/europa/erfahrungsberichte/",
                         },
                         {
                             "type": "resource",
                             "description": "Besuche eine Informationsveranstaltung. Den nächsten Termin findest du im International Office.",
                             "source": "https://www.uni-hannover.de/de/universitaet/organisation/praesidialstab-und-stabsstellen/internationales/",
                         },
                         {
                             "type": "resource",
                             "description": "Frische deine Sprachkenntnisse auf. Eine Anlaufstelle ist das "
                                            "Sprachenzentrum.",
                             "source": "https://www.llc.uni-hannover.de/",
                         },
                         {
                             "type": "resource",
                             "description": "Nimm Kontakt zum Erasmus Student Network (ESN) auf, dort lernst du andere Erasmusbegeisterte kennen und erfährst aus erster Hand, wie ein Auslandsaufenthalt zu organisieren ist.",
                             "source": "https://hannover.esn-germany.de/",
                         },
                         {
                             "type": "resource",
                             "description": "Für einen Überblick über alle wichtigen Planungsschritte hat die Uni Hannover eine Seite mit eigener Checkliste erstellt, an der du dich orientieren kannst.",
                             "source": "https://www.uni-hannover.de/de/studium/im-studium/international/outgoing/auslandsprogramme/planung-semesteraufenthalte/",
                         },
                    ],
                    "Während der Bewerbung": [
                        {
                            "type": "todo",
                            "description": "Nimm Kontakt zum Erasmus-Verantwortlichen (Austausch-Koordination) deiner Fakultät auf."
                               "<ul> "
                               "<li><a href='https://www.archland.uni-hannover.de/de/personen/epv-details/epv/internationales-international-relations-fakultaet-fuer-architektur-und-landschaft-1/austausch-koordination/' target='_blank'>Fakultät für Architektur und Landschaft</a></li>"
                               "<li><a href='https://www.fbg.uni-hannover.de/de/fakultaet/internationales/erasmus-programm/' target='_blank'>Fakultät für Bauingenieurwesen und Geodäsie</a></li>"
                               "<li><a href='https://www.et-inf.uni-hannover.de/de/fakultaet/beauftragte/auslandsbeauftragte/' target='_blank'>Fakultät für Elektrotechnik und Informatik</a></li>"
                               "<li><a href='https://www.jura.uni-hannover.de/de/erasmus/' target='_blank'>Juristische Fakultät</a></li>"
                               "<li><a href='https://www.maschinenbau.uni-hannover.de/de/studium/internationales/kontakt/' target='_blank'>Fakultät für Maschinenbau</a></li>"
                               "<li><a href='https://www.maphy.uni-hannover.de/de/studium/auslandsaustausch/auslandsaustausch-mit-erasmus/' target='_blank'>Fakultät für Mathematik und Physik </a></li>"
                               "<li><a href='https://www.naturwissenschaften.uni-hannover.de/de/fakultaet/leitung-und-organisation/beauftragte/austauschkoordination/' target='_blank'>Naturwissenschaftliche Fakultät</a></li>"
                               "<li><a href='https://www.phil.uni-hannover.de/de/fakultaet/personenverzeichnis/epvps/Person/search/77/10614059/0////' target='_blank'>Philosophische Fakultät</a></li>"
                               "<li><a href='https://www.wiwi.uni-hannover.de/de/studium/im-studium/international/#c418' target='_blank'>Wirtschaftswissenschaftliche Fakultät</a></li>"
                               "</ul>",
                        },
                        {
                            "type": "resource",
                            "description": "Erstelle eine Liste der benötigten Unterlagen in Absprache mit der Erasmus-Koordination deiner Fakultät.",
                            "source": "https://www.uni-hannover.de/de/studium/im-studium/international/outgoing/auslandsprogramme/austauschprogramme-und-ansprechpartner/erasmus-plus/bewerbungsverfahren/",
                        },
                        {
                            "type": "todo",
                            "description": "Bereite dein Motivationsschreiben vor.",
                        },
                        {
                            "type": "todo",
                            "description": "Übersetze deinen Lebenslauf in die Sprache des Reiselandes (ggf. ist ein CV auf Englisch ausreichend)",
                        },
                        {
                            "type": "todo",
                            "description": "Erstelle die Übersicht deiner Leistungen (Notenspiegel), drucke es aus und bewahre es gut in digitaler und physischer Form.",
                        },
                        {
                            "type": "resource",
                            "description": "Lass dir die Sprachkenntnisse nachweisen, bzw. besuche einen Kurs am Sprachenzentrum.",
                            "source": "https://www.llc.uni-hannover.de/",
                        },
                        {
                            "type": "todo",
                            "description": "Hast du die Nominierung deiner Heimuniversität erhalten?",
                        },
                        {
                            "type": "todo",
                            "description": "Bewerbe Dich online an deiner Gastuniversität, drucke die Unterlagen aus und bewahre sie sorgfältig auf.",
                        },
                        {
                            "type": "todo",
                            "description": "Hast du die Bestätigung der Gastuniversität erhalten?",
                        },
                ],
                "Vor der Abreise": [
                        {
                            "type": "resource",
                            "description": "Besuche die obligatorische Infoveranstaltung für alle Outgoings.",
                            "source": "https://www.uni-hannover.de/de/studium/im-studium/international/auslandsaufenthalt-outgoing/",
                        },
                        {
                            "type": "resource",
                            "description": "Suche dir passende Kurse an der Gastuniversität aus. Fülle das Online Learning Agreement aus und leite es an dne/n Fachbereichs-Koordination mit der Bitte um Unterzeichnung. Dieses Dokument ist für die Anrechnung der im Ausland bestandenen Module notwendig.",
                            "source": "https://www.uni-hannover.de/de/studium/im-studium/international/outgoing/auslandsprogramme/austauschprogramme-und-ansprechpartner/erasmus-plus/bewerbungsverfahren/",
                        },
                        {
                            "type": "resource",
                            "description": "Grant Agreement (Erasmus-Stipendium) unterzeichnen.",
                            "source": "https://www.uni-hannover.de/de/studium/im-studium/international/outgoing/auslandsprogramme/austauschprogramme-und-ansprechpartner/erasmus-plus/bewerbungsverfahren/",
                        },
                        {
                            "type": "todo",
                            "description": "Informiere Dich, ob eine Beurlaubung an deiner Heimatuniversität für Dich in Frage kommt.",
                        },
                        {
                            "type": "resource",
                            "description": "Informiere Dich mindestens sechs Monate im Voraus, ob dir Auslands-BAföG zusteht.",
                            "source": "https://www.uni-hannover.de/de/studium/im-studium/international/outgoing/finanzierung-auslandsaufenthalt/auslands-bafoeg-bildungskredit/",
                        },
                        {
                            "type": "todo",
                            "description": "Finde heraus, ob du ein Visum oder eine Aufenthaltsberechtigung für das Gastland benötigst.",
                        },
                        {
                            "type": "todo",
                            "description": "Überprüfe, ob du eine zusätzliche Auslandsversicherung brauchst – dafür ist deine Krankenkasse der richtige Ansprechpartner.",
                        },
                        {
                            "type": "todo",
                            "description": "Manche Gastuniversitäten bieten kostenlose Sprachkurse bei Ankunft an. Diese sind wertvoll, um "
                                            "direkt Kontakte zu anderen Erasmus-Teilnehmenden zu knüpfen. Dafür muss allerdings von zu Hause "
                                            "aus ein Einstufungstest durchgeführt werden. Suche solch einen Test auf der Webseite der "
                                            "Gastuniversität."
                        },
                        {
                            "type": "todo",
                            "description": "*Ggf. einen „buddy“ an der Gastuniversität finden.",
                        },
                        {
                            "type": "todo",
                            "description": "Suche dir eine passende Unterkunft. Damit kanndir die Gastuniversität ggf. weiterhelfen."
                        },
                        {
                            "type": "todo",
                            "description": "Buche einen Flug und freu Dich auf die Reise. Wir wünschendir ein unvergessliches Abenteuer.",
                        },
                    ],
                },
            "Osnabrück": {
                "Vor der Bewerbung": [
                {
                    "type": "resource",
                    "description": "Überlege dir, wo du hin möchtest und informiere dich über Kooperationen. Wähle zunächst 2-3 "
                                   "Angebote aus, die für Dich in Frage kommen würden.",
                    "source": "https://www.uni-osnabrueck.de/studium/studium-und-praktikum-im-ausland/",
                },
                {
                    "type": "todo",
                    "description": "Vergleiche die Kursangebote der Gastuniversitäten und suchedir nun einen Favoriten aus.",
                },
                {
                    "type": "resource",
                    "description": "Lies einige Erfahrungsberichte von Studierenden, die bereits im Ausland waren. Deine Uni arbeitet "
                                   "noch an einer Sammlung von Erfahrungsberichten. Auf der Internetseite deines Fachbereichs findest "
                                   "du Erfahrungsberichte von anderen Studierenden. Eine gute Übersicht findest du auf der "
                                   "Internetseite unseres Verbundpartners, der Leibniz Universität Hannover.",
                    "source": "https://www.uni-hannover.de/de/studium/im-studium/international/outgoing/auslandsprogramme/europa/erfahrungsberichte/",
                },
                {
                    "type": "resource",
                    "description": "Besuche eine Informationsveranstaltung. Den nächsten Termin findest du im International Office.",
                    "source": "https://www.uni-osnabrueck.de/universitaet/organisation/studentisches/international-office/",
                },
                {
                    "type": "resource",
                    "description": "Frische deine Sprachkenntnisse auf. Eine Anlaufstelle ist das "
                                   "Sprachenzentrum.",
                    "source": "https://www.uni-osnabrueck.de/universitaet/organisation/zentrale-einrichtungen/sprachenzentrum/",
                },
                {
                    "type": "resource",
                    "description": "Nimm Kontakt zum Erasmus Student Network (ESN) auf, dort lernst du andere Erasmusbegeisterte "
                                   "kennen und erfährst aus erster Hand, wie ein Auslandsaufenthalt zu organisieren ist. ",
                    "source": "https://esn-germany.de/",
                },
            ],
            "Während der Bewerbung": [
                {
                    "type": "todo",
                    "description": "Nimm Kontakt zum Erasmus-Verantwortlichen deiner Fakultät auf."
                                   "<ul> <li><a href='https://www.fb1.uni-osnabrueck.de/service_beratung/auslandsbuero/"
                                   "kontaktpersonen.html' target='_blank'>FB1</a></li>"
                                   "<li><a href='https://www.fb3.uni-osnabrueck.de/studium/studienaufenthalte_im_ausland.html' "
                                   "target='_blank'>FB3</a></li>"
                                   "<li><a href='https://www.physik.uni-osnabrueck.de/fachbereich/internationale_"
                                   "kooperationen.html' target='_blank'>FB Physik</a></li>"
                                   "<li><a href='https://www.biologie.uni-osnabrueck.de/studium/erasmus.html' "
                                   "target='_blank'>FB Biologie</a></li>"
                                   "<li><a href='https://www.lili.uni-osnabrueck.de/fachbereich/studium_und_lehre/"
                                   "auslandsaufenthalte/erasmus_ansprechpersonen.html' target='_blank'>FB7</a></li>"
                                   "<li><a href='https://www.wiwi.uni-osnabrueck.de/studium/auslandssemester_outgoings.html' "
                                   "target='_blank'>FB Wiwi</a></li>"
                                   "<li><a href='https://www.jura.uni-osnabrueck.de/internationales/auslandsaufenthalte/"
                                   "kontakt.html'target='_blank'>FB Jura</a></li></ul>",
                },
                {
                    "type": "resource",
                    "description": "Erstelle eine Liste der benötigten Unterlagen in Absprache mit der Erasmus-Koordination deiner "
                                   "Fakultät.",
                    "source": "https://www.uni-osnabrueck.de/studium/studium_und_praktikum_im_ausland/downloads.html",
                },
                {
                    "type": "resource",
                    "description": "Behalte die Termine und Fristen für die Bewerbungsunterlagen im Auge.",
                    "source": "https://www.uni-osnabrueck.de/studium/studium-und-praktikum-im-ausland/austauschprogramme/erasmus/bewerbung/",
                },
                {
                    "type": "todo",
                    "description": "Bereite dein Motivationsschreiben vor.",
                },
                {
                    "type": "todo",
                    "description": "Übersetze deinen Lebenslauf in die Sprache des Reiselandes (ggf. ist ein CV auf Englisch "
                                   "ausreichend)",
                },
                {
                    "type": "todo",
                    "description": "Erstelle die Übersicht deiner Leistungen (Notenspiegel), drucke es aus und bewahre es gut in "
                                   "digitaler und physischer Form.",
                },
                {
                    "type": "resource",
                    "description": "Informiere dich darüber, ob du die Sprachkenntnisse des Gastlandes nachweisen musst. Für "
                                   "Prüfungen und Zertifikate kannst du ebenfalls das Sprachenzentrum kontaktieren.",
                    "source": "https://www.uni-osnabrueck.de/universitaet/organisation/zentrale-einrichtungen/sprachenzentrum/",
                },
                {
                    "type": "todo",
                    "description": "Hast du die Nominierung deiner Heimuniversität erhalten?",
                },
                {
                    "type": "todo",
                    "description": "Bewerbe Dich online an deiner Gastuniversität, drucke die Unterlagen aus und bewahre sie "
                                   "sorgfältig auf.",
                },
                {
                    "type": "todo",
                    "description": "Hast du die Zusage der Gastuniversität erhalten?",
                },
            ],
            "Vor der Abreise": [
                {
                    "type": "resource",
                    "description": "Suche dir passende Kurse an der Gastuniversität. Fülle das Online Learning Agreement aus und "
                                   "leite es an deine/n Fachbereichs-Koordination mit der Bitte um Unterzeichnung. Dieses Dokument "
                                   "ist für die Anrechnung der im Ausland bestandenen Module notwendig.",
                    "source": "https://www.uni-osnabrueck.de/studium/studium_und_praktikum_im_ausland/downloads.html",
                },
                {
                    "type": "resource",
                    "description": "Leite das vorläufige Learning Agreement an die Erasmus-Koordination deines International Office "
                                   "weiter, sobald dein vorläufiges Learning Agreement mit deiner/m Fachbereichs-Koordination "
                                   "abgestimmt ist. Änderungen kannst du noch zu Beginn deines Auslandsstudiums mit dem Learning "
                                   "Agreement - During the Mobility vornehmen.",
                    "source": "https://www.uni-osnabrueck.de/studium/studium_und_praktikum_im_ausland/downloads.html",
                },
                {
                    "type": "todo",
                    "description": "Informiere Dich, ob eine Beurlaubung an deiner Heimatuniversität für Dich in Frage kommt.",
                },
                {
                    "type": "resource",
                    "description": "Informiere Dich mindestens sechs Monate im Voraus, obdir Auslands-BAföG zusteht.",
                    "source": "https://www.uni-osnabrueck.de/studium/studium-und-praktikum-im-ausland/foerderungen/auslands-bafoeg/",
                },
                {
                    "type": "todo",
                    "description": "Finde heraus, ob du ein Visum oder eine Aufenthaltsberechtigung für das Gastland benötigst.",
                },
                {
                    "type": "todo",
                    "description": "Überprüfe, ob du eine zusätzliche Auslandsversicherung brauchst – dafür ist deine Krankenkasse der richtige Ansprechpartner.",
                },
                {
                    "type": "todo",
                    "description": "Manche Gastuniversitäten bieten kostenlose Sprachkurse bei Ankunft an. Diese sind wertvoll, "
                                   "um direkt Kontakte zu anderen Erasmus-Teilnehmenden zu knüpfen. Dafür muss vorher allerdings ein "
                                   "Einstufungstest durchgeführt werden. Suche solch einen Test auf der Webseite der Gastuniversität.",
                },
                {
                    "type": "todo",
                    "description": "Ggf. einen „buddy“ an der Gastuniversität finden.",
                },
                {
                    "type": "todo",
                    "description": "Suche dir eine passende Unterkunft. Damit kanndir die Gastuniversität ggf. weiterhelfen.",
                },
                {
                    "type": "todo",
                    "description": "Buche einen Flug und freu Dich auf die Reise. Wir wünschendir ein unvergessliches Abenteuer.",
                },
            ],
            }
            }

    def initialize_templates(self):
        """
        Creates and updates all templates of this recommender
        Is executed at server startup
        """
        super().initialize_templates()

        # Initial question for all locations - no api_endpoint query necessary
        abroad_question = models.Question.objects.create(
            question_text="Siddata möchte dich bei der Organisation deines Auslandsabenteuers unterstützen. Je nachdem,"
                          " in welcher Phase du dich befindest, führt dich Siddata durch eine Checkliste mit "
                          "hilfreichen Informationen. Wo stehst du gerade?",
            answer_type="selection",
            selection_answers=STAGE_DESCRIPTIONS,
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("initial_question"),
            defaults={
                "title": "In welcher Phase befindest du dich?",
                "description": "Initiale Fragen",
                "type": "question",
                "status": "template",
                "question": abroad_question,
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": 2,
            }
        )

        email_text = "Hier kannst du eine E-Mail-Adresse hinterlegen um einmal wöchentlich an die Planung deines " \
                     "Auslandsaufenthaltes erinnert zu werden."

        email_question = models.Question.objects.get_or_create(
            question_text=email_text,
            answer_type="text",
        )[0]

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("abroad_email"),
            defaults={
                'title': "E-Mail-Benachrichtigung",
                'type': 'question',
                'status': 'template',
                'order': 1,
                'question': email_question,
                'feedback_size': 0,
                'color_theme': 'green',
            }
        )

        # create all generic templates
        for location in self.checklist.keys():
            stage_number = 1
            for stage in self.checklist[location].keys():
                point_number = 1
                for point in self.checklist[location][stage]:

                    order = stage_number*1000+point_number

                    template_id = "{}_{}_{}".format(location, stage, point_number)
                    if point["type"] == "todo":
                        models.ActivityTemplate.objects.update_or_create(
                            template_id=self.get_template_id(template_id),
                            defaults={
                                "title": "{} - Schritt {}".format(stage, point_number),
                                "description": point["description"],
                                "type": "todo",
                                "status": "template",
                                "feedback_size": 0,
                                "image": self.IMAGE,
                                "button_text": "Erledigt.",
                                "order": order,
                            }
                        )
                    elif point["type"] == "resource":

                        resource = models.EducationalResource.objects.get_or_create(
                            title="{} - Schritt {}".format(stage, point_number),
                            description=point["description"],
                            source=point["source"],
                        )[0]

                        models.ActivityTemplate.objects.update_or_create(
                            template_id=self.get_template_id(template_id),
                            defaults={
                                "title": "{} - Schritt {}".format(stage, point_number),
                                "description": point["description"],
                                "type": "resource",
                                "status": "template",
                                "resource": resource,
                                "feedback_size": 0,
                                "image": self.IMAGE,
                                "button_text": "Erledigt.",
                                "order": order,
                            }
                        )

                    point_number += 1
                stage_number += 1

    def initialize(self, user):
        """
        When a user logs in for the first time, initial activities are generated.
        :param siddatauser_id: Id of the user who logged in for the first time.
        :return: True if successful
        """
        goal = self.activate_recommender_for_user_and_create_first_goal(user)

        models.Activity.create_activity_from_template(
            template_id=self.get_template_id("initial_question"),
            goal=goal,
        )

        activity = models.Activity.create_activity_from_template(
            template_id=self.get_template_id("abroad_email"),
            goal=goal,
        )
        activity.color_theme="green"
        activity.save()
        return True

    def process_activity(self, activity):
        """
        This function processes the incoming activities which were processed by the user.
        :param activity:  activity
        :return: True if successful
        """

        # check if answer value is None
        if activity.answers is None:
            activity.answers = []

        if activity.has_template(self.get_template_id("initial_question")):
            if STAGE_DESCRIPTIONS[0] in activity.answers:
                stage = STAGES[0]
            elif STAGE_DESCRIPTIONS[1] in activity.answers:
                stage = STAGES[1]
            elif STAGE_DESCRIPTIONS[2] in activity.answers:
                stage = STAGES[2]
            self.set_to_stage(activity.goal, stage)
            # color_theme is used as symbol for done and required later
            activity.color_theme = "green"
            activity.save()
            return True

        elif activity.has_template(template_id=self.get_template_id("abroad_email")):
            data = {"email": activity.answers[0]}
            activity.goal.set_property(key="email", value=json.dumps(data))
            activity.status = "active"
            activity.save()
            return True

        else:
            if activity.status == "done":
                activity.status = "new"
                activity.color_theme = "green"
                activity.button_text = "~static"
                activity.save()

                activities = models.Activity.objects.filter(goal=activity.goal)
                for activity in activities:
                    if activity.color_theme != "green":
                        return True



                # now we know all activies are green, hence done
                for act in activities:
                    if act.has_template(template_id=self.get_template_id("abroad_email")):
                        continue
                    act.status ="done"
                    act.save()

                old_stage = activity.goal.title
                if old_stage == STAGES[0]:
                    self.set_to_stage(activity.goal, STAGES[1])
                elif old_stage == STAGES[1]:
                    self.set_to_stage(activity.goal, STAGES[2])
                else:

                    return True

        return True

    def set_to_stage(self, goal, stage):

        goal.title = stage
        goal.save()

        location = goal.userrecommender.user.origin.location

        if DEBUG and (location not in ["Osnabrück", "Bremen", "Hannover"]):
            location = "Bremen"


        for point_number in range(1, len(self.checklist[location][stage]) + 1):
            template_id = "{}_{}_{}".format(location, stage, point_number)
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id(template_id),
                goal=goal,
            )

    def execute_cron_functions(self):
        """
        This function provides an access point for interval-based executions triggered by a cron job function.
        """

        if datetime.datetime.today().weekday() == 7:
            goals = models.Goal.objects.filter(userrecommender__recommender__name=self.NAME)
            for goal in goals:
                if self.open_todos(goal):
                    self.send_nudging_email(goal)


    def send_nudging_email(self, goal):
        """"
        Is called to send a nudging email once a week.
        """
        try:
            address = goal.get_property(key="email")["email"]
        except Exception as e:
            logging.ERROR(e)

        stage = goal.title

        title = "Siddata Studienassistent : Erinnerung an deinen Auslandsaufenthalt"
        content = "Guten Tag," \
                "du befindest dich in der Phase '{}'<br>".format(stage)
        content += "Die nächsten Schritte sind:<br>"
        activities = models.Activity.objects.filter(goal=goal)
        for activity in activities:
            if activity.color_theme != "green":
                content += "* {}<br>".format(activity.description)
        content += "<br>"
        content += "Eine große Reise beginnt mit kleinen Schritten. Just do it!"
        content += "Dein Siddata Studienassistent"

        self.send_push_email(address, title, content)


    def open_todos(self, goal):
        """
        Checks if there are non-green activities to tell if there are open todos.
        :param goal: goal to be checked
        :return: boolean
        """
        activities = models.Activity.objects.filter(goal=goal)
        for activity in activities:
            if activity.color_theme != "green":
                return True
        return False


    @staticmethod
    def get_stage_for_user(user):
        """
        Returns the current planning stage of a user as string.
        :param user: User in Question
        :return: String representing the phase
        """
        stage = models.Goal.objects.get(userrecommender__user=user,
                                        userrecommender__recommender__name=NAME).title
        return stage
