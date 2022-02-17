from backend import models
from recommenders.RM_BASE import RM_BASE
import pandas as pd
import os


class RM_start_of_studies(RM_BASE):
    """ Recommender that contains
        - initial activites (guided tour)
        - teaser activities that introduce all recommenders
        - salient or emergent activities
        In Addition the frontend adds a tile view of all recommenders available.
    """

    def __init__(self):
        # this magic line of code lets our recommender inherit all attributes and methods from the baseclass.
        super().__init__()
        # This name should be unique and appears in the Stud.IP GUI.
        self.NAME = "Orientierung zum Studienstart"
        # The description text summarizes the functionality. It is shown in teaser activity and tile view,
        self.DESCRIPTION = "Hilfe in der Studieneingangsphase."
        # This text is displayed in Teaser Activities
        self.TEASER_TEXT = "Unter Orientierung zum Studienstart kannst du dich über verschiedene Themen rund um " \
                           "den Studienstart informieren. Außerdem werden dir auf Basis deiner Themenwünsche " \
                           "konkrete Workshops und Trainings für den Studieneinstieg empfohlen."
        # If set to False, the recommender will not appear in the GUI or the DB
        self.ACTIVE = True
        # Image is shown in teaser activity
        self.IMAGE = "professions.png"
        # determines arrangement in Frontend
        self.ORDER = 1
        # This string tells the user which data is required for this recommender
        self.DATA_INFO = "Diese Funktion speichert diejenigen Daten, die du aktiv eingibst und nutze Daten zu deiner Uni um passgenaue Empfehlungen zu geben."
        # Reference to the database object, can be used as value vor recommender attribute in goals.
        self.recommender = models.Recommender.objects.get_or_create(
            name=self.get_name(),
            description=self.DESCRIPTION,
            classname=self.__class__.__name__,
            image=self.IMAGE,
            order=self.ORDER,
            data_info=self.DATA_INFO,
        )[0]

        self.dirname = os.path.dirname(__file__)

        self.filename = os.path.join(self.dirname, 'recommender_data/start_of_studies_data.csv')

        self.course_df = pd.read_csv(self.filename, delimiter=',')

    def initialize_templates(self):
        """
        Creates and updates all templates of this recommender
        Is executed at server startup
        """
        super().initialize_templates()

        order = 1

        # create template for general information question
        general_information_question = models.Question.objects.create(
            question_text="Der Studienstart ist mit verschiedenen Herausforderungen und Chancen verbunden. Hier "
                          "findest du passende Informationen und Unterstützungsangebote:",
            answer_type="checkbox",
            selection_answers=["Studienverlauf, Prüfungen, Rückmeldung",
                               "Literatur ausleihen",
                               "Raum für Gruppenarbeiten",
                               "Raum zum ruhigen Arbeiten",
                               "Studium und Familie",
                               "Sport treiben",
                               "Eine weitere Sprache lernen",
                               "Auslandssemester",
                               "Probleme im Studium",
                               "Technische Fragen und Probleme",
                               "Finanzierung meines Studiums",
                               "Wohnen",
                               "Was gibt es heute zum Mittag?",
                               ]
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("general_information_question"),
            defaults={
                "title": "Generelle Infos zum Studium",
                "description": "Orientierung zum Studienstart",
                "type": "question",
                "status": "template",
                "question": general_information_question,
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        # create template for general recommendations question
        general_recommendation_question = models.Question.objects.create(
            question_text="Wusstest du schon: deine Universität bietet neben den Vorlesungen deines Studiengangs auch Veranstaltungen an, die dich in deinem Studium "
                          "unterstützen sollen. Welche Themen interessieren dich? Wenn du deine Auswahl getroffen "
                          "hast, bekommst du konkrete Veranstaltungen vorgeschlagen.",
            answer_type="checkbox",
            selection_answers=["Wissenschaftliches Arbeiten",
                               "Lernen & Gedächtnis",
                               "Prüfungsvorbereitung",
                               "Präsentation & Kommunikation",
                               "Projektmanagement",
                               "Selbst- und Zeitmanagement",
                               "Gesund studieren",
                               "Sport & Bewegung",
                               "Literaturverwaltung",
                               "Schreibtraining",
                               ]
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("general_recommendation_question"),
            defaults={
                "title": "Persönliche Weiterentwicklung",
                "description": "Orientierung zum Studienstart",
                "type": "question",
                "status": "template",
                "question": general_recommendation_question,
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        # create course recommendation templates
        for index in self.course_df.index:

            models.ActivityTemplate.objects.update_or_create(
                template_id=self.get_template_id("course_recommendation_{}".format(index)),
                defaults={
                    "title": "Veranstaltung zum Thema '{}'".format(self.course_df["Categories"].iloc[index]),
                    "description": "<p><strong>Volltreffer! Wir haben eine Kursempfehlung für dich:</strong></p>"
                                   "<ul>"
                                   "<li>Veranstaltung: {}</li> "
                                   "<li>Beschreibung: {}</li> "
                                   "<li>Zeit: {}</li> "
                                   "<li>Ort: {}</li> "
                                   "<li>Link: <a href='{}' target='_blank'>Hier geht es zum Kurs.</a></li>"
                                   "</ul>".format(self.course_df["Course"].iloc[index],
                                                  self.course_df["Description"].iloc[index],
                                                  self.course_df["Date"].iloc[index],
                                                  self.course_df["Location"].iloc[index],
                                                  self.course_df["Registration"].iloc[index]),
                    "type": "todo",
                    "status": "template",
                    "feedback_size": 0,
                    "image": self.IMAGE,
                    # changed all order attributes to unique values in DataFrame
                    "order": self.course_df["Order"].iloc[index],
                }
            )
            # order count up not necessary anymore in for-loop
            # order += 1



        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("library_OS"),
            defaults={
                "title": "Universitätsbibliothek",
                "description": "Wenn du dir Literatur ausleihen möchtest, kann dir die Bibliothek deiner Universität"
                "helfen. <a href='https://www.ub.uni-osnabrueck.de/startseite.html' target='_blank'>Hier geht es zur " 
                "Website.</a>",
                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("library_UB"),
            defaults={
                "title": "Universitätsbibliothek",
                "description": "Wenn du dir Literatur ausleihen möchtest, kann dir die Bibliothek deiner Universität" 
                "helfen. <a href='https://www.suub.uni-bremen.de/' target='_blank'>Hier geht es zur "
                "Website.</a>",
                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1


        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("library_LUH"),
            defaults={
                "title": "Universitätsbibliothek",
                "description": "Wenn du dir Literatur ausleihen möchtest, kann dir die Bibliothek deiner Universität" 
                "helfen. <a href='https://www.tib.eu/de/' target='_blank'>Hier geht es zur "
                "Website.</a>",
                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("rooms_OS"),
            defaults={
                "title": "Lern- und Gruppenarbeitsräume",
                "description": "Wenn du einen ruhigen Platz zum Arbeiten suchst oder einen Ort für Gruppenarbeiten"
                " benötigst, kannst du dir hier einen Raum buchen. "
                "<a href='https://www.ub.uni-osnabrueck.de/startseite.html'"
                "target='_blank'>Hier geht es zur "    
                "Website.</a>",
                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("rooms_UB"),
            defaults={
                "title": "Lern- und Gruppenarbeitsräume",
                "description": "Wenn du einen ruhigen Platz zum Arbeiten suchst oder einen Ort für Gruppenarbeiten"
                               " benötigst,kannst du dir hier einen Raum buchen. "
                               "<a href='https://www.uni-bremen.de/universitaet/campus/lernraeume'"
                               "target='_blank'>Hier geht es zur "
                               "Website.</a>",
                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("rooms_LUH"),
            defaults={
                "title": "Lern- und Gruppenarbeitsräume",
                "description": "Wenn du einen ruhigen Platz zum Arbeiten suchst oder einen Ort für Gruppenarbeiten"
                               " benötigst,kannst du dir hier einen Raum buchen. "
                               "<a href='https://www.zqs.uni-hannover.de/de/qs/lernraum/'"
                               "target='_blank'>Hier geht es zur "
                               "Website.</a>",
                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("problems_OS"),
            defaults={
                "title": "Wenn es mal nicht so läuft...",
                "description": "Schwierige Phasen erlebt jeder einmal, im Studium und im Privaten."
                               " Nicht immer lassen sich diese Hindernisse schnell und aus eigener Kraft überwinden."
                               " Wenn du in einer solchen Phase bist, scheue dich nicht Hilfe anzunehmen. "
                               "<a href='https://www.studentenwerk-osnabrueck.de/de/beratung/"
                               "psychologische-beratung.html' "
                               "target='_blank'>Hier geht es zur Website.</a>",


                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("problems_UB"),
            defaults={
                "title": "Wenn es mal nicht so läuft...",
                "description": "Schwierige Phasen erlebt jeder einmal, im Studium und im Privaten."
                               " Nicht immer lassen sich diese Hindernisse schnell und aus eigener Kraft überwinden."
                               " Wenn du in einer solchen Phase bist, scheue dich nicht Hilfe anzunehmen. "
                               "<a href='https://www.stw-bremen.de/de/beratung/psychologische-beratung'"
                               "target='_blank'>Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("problems_LUH"),
            defaults={
                "title": "Wenn es mal nicht so läuft...",
                "description": "Schwierige Phasen erlebt jeder einmal, im Studium und im Privaten."
                               " Nicht immer lassen sich diese Hindernisse schnell und aus eigener Kraft überwinden."
                               " Wenn du in einer solchen Phase bist, scheue dich nicht Hilfe anzunehmen. "
                               "<a href='https://www.ptb.uni-hannover.de/'"
                               "target='_blank'>Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("language_OS"),
            defaults={
                "title": "Sprachen lernen",
                "description": "Möchtest du eine neue Fremdsprache lernen oder deine Kenntnisse auffrischen?"
                               " Das Fremdsprachenangebot an Grund-, Aufbau- und Vertiefungskursen findest du hier: "
                               "<a href='https://www.uni-osnabrueck.de/universitaet/organisation/"
                               "zentrale-einrichtungen/sprachenzentrum/'"
                "target='_blank'>Hier geht es zur Website.</a>",
                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("language_UB"),
            defaults={
                "title": "Sprachen lernen",
                "description": "Möchtest du eine neue Fremdsprache lernen oder deine Kenntnisse auffrischen?"
                               " Das Fremdsprachenangebot an Grund-, Aufbau- und Vertiefungskursen findest du hier: "
                               "<a href='https://www.fremdsprachenzentrum-bremen.de/'"
                               "target='_blank'>Hier geht es zur Website.</a>",
                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("language_LUH"),
            defaults={
                "title": "Sprachen lernen",
                "description": "Möchtest du eine neue Fremdsprache lernen oder deine Kenntnisse auffrischen?"
                               " Das Fremdsprachenangebot an Grund-, Aufbau- und Vertiefungskursen findest du hier: "
                               "<a href='https://www.llc.uni-hannover.de/'"
                               "target='_blank'>Hier geht es zur Website.</a>",
                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("sports_OS"),
            defaults={
                "title": "Sportangebote",
                "description": "Jedes Semester stehen dir zahlreiche Sportangebote im Rahmen des Hochschulsports zur "
                               "Verfügung. <a href='https://www.zfh.uni-osnabrueck.de/startseite.html'"
                               "target='_blank'>Hier geht es zur Website.</a>",
                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("sports_UB"),
            defaults={
                "title": "Sportangebote",
                "description": "Jedes Semester stehen dir zahlreiche Sportangebote im Rahmen des Hochschulsports zur "
                               "Verfügung. <a href='https://www.uni-bremen.de/hospo'"
                               "target='_blank'>Hier geht es zur Website.</a>",
                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("sports_LUH"),
            defaults={
                "title": "Sportangebote",
                "description": "Jedes Semester stehen dir zahlreiche Sportangebote im Rahmen des Hochschulsports zur "
                               "Verfügung. <a href='https://www.hochschulsport-hannover.de/'"
                               "target='_blank'>Hier geht es zur Website.</a>",
                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("international_office_OS"),
            defaults={
                "title": "International Office",
                "description": "Wenn du dich für einen Studienaufenthalt im Ausland interessiert, erhältst du hier "
                               "Informationen und Unterstützung bei der Planung. "
                               "<a href='https://www.uni-osnabrueck.de/universitaet/organisation/studentisches/"
                               "international-office/' target='_blank'>Hier geht es zur Website.</a>",
                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("international_office_UB"),
            defaults={
                "title": "International Office",
                "description": "Wenn du dich für einen Studienaufenthalt im Ausland interessiert, erhältst du hier "
                               "Informationen und Unterstützung bei der Planung. "
                               "<a href='https://www.uni-bremen.de/universitaet/profil/international/"
                               "international-office' target='_blank'>Hier geht es zur Website.</a>",
                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("international_office_LUH"),
            defaults={
                "title": "International Office",
                "description": "Wenn du dich für einen Studienaufenthalt im Ausland interessiert, erhältst du hier "
                               "Informationen und Unterstützung bei der Planung. "
                               "<a href='https://www.uni-hannover.de/de/universitaet/internationales/'"
                               "_blank'>Hier geht es zur Website.</a>",
                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("rechenzentrum_OS"),
            defaults={
                "title": "Rechenzentrum",
                "description": "Bei technischen Fragen (z.B. zu deinem Uni-Account, zum WLAN) findest du hier "
                               "Informationen und Hilfestellungen."
                               "<ul> <li><a href='https://www.rz.uni-osnabrueck.de/' target='_blank'>"
                               "Hier geht es zur Website des Rechenzentrums.</a></li>"
                               "<li><a href='https://www.rz.uni-osnabrueck.de/dienste/leitfaden/"
                               "leitfaden_studierende.html' target='_blank'>Hier geht es zu einem Leitfaden für "
                               "Erstsemester</a></li></ul>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("rechenzentrum_UB"),
            defaults={
                "title": "Rechenzentrum",
                "description": "Bei technischen Fragen (z.B. zu deinem Uni-Account, zum WLAN) findest du hier "
                               "Informationen und Hilfestellungen. "
                               "<a href='https://www.uni-bremen.de/zfn' target='_blank'>"
                               "Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("rechenzentrum_LUH"),
            defaults={
                "title": "Rechenzentrum",
                "description": "Bei technischen Fragen (z.B. zu deinem Uni-Account, zum WLAN) findest du hier "
                               "Informationen und Hilfestellungen. "
                               "<a href='https://www.luis.uni-hannover.de/' target='_blank'>"
                               "Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("sekretariat_OS"),
            defaults={
                "title": "Studierendensekretariat",
                "description": "Das Studierendensekretariat ist zuständig für die den Studierendenstatus betreffenden "
                               "administrativen Vorgänge während der gesamten Studienzeit z.B. der Rückmeldung, der "
                               "Campuscard oder der Beurlaubung."
                               "<ul> <li><a href='https://www.uni-osnabrueck.de/universitaet/organisation/"
                               "studentisches/studierenden-information-osnabrueck-studios/'"
                               " target='_blank'>Hier geht es zur Website der Studierenden Information Osnabrück."
                               "</a></li>"
                               "<li><a href='https://www.uni-osnabrueck.de/universitaet/organisation/"
                               "zentrale-verwaltung/studentische-angelegenheiten/studierendenservice/'"
                               " target='_blank'>Hier geht es zur Website vom Studierendenservice.</a></li></ul>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("sekretariat_UB"),
            defaults={
                "title": "Studierendensekretariat",
                "description": "Das Studierendensekretariat ist zuständig für die den Studierendenstatus betreffenden "
                               "administrativen Vorgänge während der gesamten Studienzeit z.B. der Rückmeldung, der "
                               "Campuscard oder der Beurlaubung. "
                               "<a href='https://www.uni-bremen.de/sfs' target='_blank'> Hier geht es zur Website.",
                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("sekretariat_LUH"),
            defaults={
                "title": "Studierendensekretariat",
                "description": "Das Studierendensekretariat ist zuständig für die den Studierendenstatus betreffenden "
                               "administrativen Vorgänge während der gesamten Studienzeit z.B. der Rückmeldung, der "
                               "Campuscard oder der Beurlaubung. "
                               "<a href='https://www.uni-hannover.de/de/studium/beratung-und-hilfe/servicecenter/'"
                               " target='_blank'> Hier geht es zur Website.",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("studienberatung_OS"),
            defaults={
                "title": "Studienberatung",
                "description": "Die Studienberatung ist Anlaufstelle bei Fragen und Anliegen,"
                               " die im Zusammenhang mit der Wahl oder Durchführung eines Studiums auftreten. "
                               "<a href='https://www.zsb-os.de/' target='_blank'>Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("studienberatung_UB"),
            defaults={
                "title": "Studienberatung",
                "description": "Die Studienberatung ist Anlaufstelle bei Fragen und Anliegen,"
                               " die im Zusammenhang mit der Wahl oder Durchführung eines Studiums auftreten. "
                               "<a href='https://www.uni-bremen.de/zsb' target='_blank'>Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("studienberatung_LUH"),
            defaults={
                "title": "Studienberatung",
                "description": "Die Studienberatung ist Anlaufstelle bei Fragen und Anliegen,"
                               " die im Zusammenhang mit der Wahl oder Durchführung eines Studiums auftreten. "
                               "<a href='https://www.uni-hannover.de/de/universitaet/organisation/"
                               "dezernate/dezernat-6/sg-63-zentrale-studienberatung/'"
                               "target='_blank'>Hier geht es zur Website.</a>",


                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("funding_OS"),
            defaults={
                "title": "Finanzierung und Förderung",
                "description": "Hier findest du Informationen rund um die Finanzierung deines Studiums z.B. "
                               "zum BAföG oder zu Stipendienprogrammen:"
                               "<ul><li><a href='https://www.studentenwerk-osnabrueck.de/de/finanzen/bafoeg.html' "
                               "target='_blank'>BAföG-Abteilung des Studentenwerks</a></li>"
                               "<li><a href='https://www.uni-osnabrueck.de/studieninteressierte/"
                               "stipendien-und-foerderung/'target='_blank'>Stipendien & Förderung</a></li></ul>",


                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("funding_UB"),
            defaults={
                "title": "Finanzierung und Förderung",
                "description": "Hier findest du Informationen rund um die Finanzierung deines Studiums z.B. "
                               "zum BAföG oder zu Stipendienprogrammen:"
                               "<a href='https://www.uni-bremen.de/studium/rund-ums-studium"
                               "studienfinanzierung-und-jobben' target='_blank'>Studienfinanzierung und Jobben</a>",


                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("funding_LUH"),
            defaults={
                "title": "Finanzierung und Förderung",
                "description": "Hier findest du Informationen rund um die Finanzierung deines Studiums z.B. "
                               "zum BAföG oder zu Stipendienprogrammen: "
                               "<a href='https://www.uni-hannover.de/de/studium/finanzierung-foerderung/'"
                               "target='_blank'>Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("digitization_OS"),
            defaults={
                "title": "Digitalisierung von Studium und Lehre",
                "description": "Bei Fragen rund um das Thema digitale Medien in Studium und Lehre (z.B. zu Stud.IP) "
                               "findest du hier Informationen und Hilfestellungen: "
                               "<a href='https://www.virtuos.uni-osnabrueck.de/zentrum_fuer_digitale_lehre_campus_"
                               "management_und_hochschuldidaktik.html' target='_blank'>Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("digitization_UB"),
            defaults={
                "title": "Digitalisierung von Studium und Lehre",
                "description": "Bei Fragen rund um das Thema digitale Medien in Studium und Lehre (z.B. zu Stud.IP) "
                               "findest du hier Informationen und Hilfestellungen: "
                               "<a href='https://www.uni-bremen.de/zmml' target='_blank'>Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("digitization_LUH"),
            defaults={
                "title": "Digitalisierung von Studium und Lehre",
                "description": "Bei Fragen rund um das Thema digitale Medien in Studium und Lehre (z.B. zu Stud.IP) "
                               "findest du hier Informationen und Hilfestellungen: "
                               "<a href='https://www.zqs.uni-hannover.de/de/elsa/'"
                               " target='_blank'>Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("family_OS"),
            defaults={
                "title": "Studieren mit Familie",
                "description": "Alle Informationen rund um das Thema Studieren mit Familie (z.B. Kinderbetreuung, "
                               "Pflege von Angehörigen) findest du hier: "
                               "<a href='https://www.uni-osnabrueck.de/universitaet/organisation/familien-service/'"
                               " target='_blank'>Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("family_UB"),
            defaults={
                "title": "Studieren mit Familie",
                "description": "Alle Informationen rund um das Thema Studieren mit Familie (z.B. Kinderbetreuung, "
                               "Pflege von Angehörigen) findest du hier: "
                               "<a href='https://www.uni-bremen.de/familie/studierende'"
                               " target='_blank'>Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("family_LUH"),
            defaults={
                "title": "Studieren mit Familie",
                "description": "Alle Informationen rund um das Thema Studieren mit Familie (z.B. Kinderbetreuung, "
                               "Pflege von Angehörigen) findest du hier: "
                               "<a href='https://www.chancenvielfalt.uni-hannover.de/"
                               "de/angebote/angebote-fuer-familien/'"
                               " target='_blank'>Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("asta_OS"),
            defaults={
                "title": "Allgemeiner Studierendenausschuss (AStA)",
                "description": "Allgemeiner Studierendenausschuss (AStA)"
                               " ist die universitätsweite Interessenvertretung der Studierenden und informiert euch"
                               " über Themen wie Bafög, Semesterticket etc. "
                               "<a href='https://www.asta.uni-osnabrueck.de/' "
                               "target='_blank'>Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("asta_UB"),
            defaults={
                "title": "Allgemeiner Studierendenausschuss (AStA)",
                "description": "Allgemeiner Studierendenausschuss (AStA)"
                               " ist die universitätsweite Interessenvertretung der Studierenden und informiert euch"
                               " über Themen wie Bafög, Semesterticket etc. "
                               "<a href='https://www.asta.uni-bremen.de/' "
                               "target='_blank'>Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("asta_LUH"),
            defaults={
                "title": "Allgemeiner Studierendenausschuss (AStA)",
                "description": "Allgemeiner Studierendenausschuss (AStA)"
                               " ist die universitätsweite Interessenvertretung der Studierenden und informiert euch"
                               " über Themen wie Bafög, Semesterticket etc. "
                               "<a href='https://www.asta-hannover.de/' "
                               "target='_blank'>Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("cantine_OS"),
            defaults={
                "title": "Mensa",
                "description": "Das Studentenwerk bietet dir in seinen Mensen ein vielfältiges Essensangebot. "
                               "<a href='https://www.studentenwerk-osnabrueck.de/de/essen/speiseplaene.html' "
                               "target='_blank'>Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("cantine_UB"),
            defaults={
                "title": "Mensa",
                "description": "Das Studentenwerk bietet dir in seinen Mensen ein vielfältiges Essensangebot. "
                               "<a href='https://www.stw-bremen.de/de/mensa/uni-mensa' "
                               "target='_blank'>Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("cantine_LUH"),
            defaults={
                "title": "Mensa",
                "description": "Das Studentenwerk bietet dir in seinen Mensen ein vielfältiges Essensangebot. "
                               "<a href='https://www.studentenwerk-hannover.de/essen/speiseplaene/alle-mensen-heute/' "
                               "target='_blank'>Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("dorms_OS"),
            defaults={
                "title": "Wohnungsangebote",
                "description": "Guten und preiswerten Wohnraum zu finden ist nicht immer leicht. Hier findest du "
                               "Informationen und Hilfestellungen: "
                               "<a href='https://www.studentenwerk-osnabrueck.de/de/wohnen.html' "
                               "target='_blank'>Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("dorms_UB"),
            defaults={
                "title": "Wohnungsangebote",
                "description": "Guten und preiswerten Wohnraum zu finden ist nicht immer leicht. Hier findest du "
                               "Informationen und Hilfestellungen: "
                               "<a href='https://www.uni-bremen.de/universitaet/campus/wohnen' "
                               "target='_blank'>Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("dorms_LUH"),
            defaults={
                "title": "Wohnungsangebote",
                "description": "Guten und preiswerten Wohnraum zu finden ist nicht immer leicht. Hier findest du "
                               "Informationen und Hilfestellungen: "
                               "<a href='https://www.uni-hannover.de/de/universitaet/campus-und-stadt/wohnen/' "
                               "target='_blank'>Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("prüfungsamt_LUH"),
            defaults={
                "title": "Zentrales Prüfungsamt",
                "description": "Das zentrale Prüfungsamt ist zuständig bei Fragen und Problemen rund um "
                               "Prüfungsangelegenheiten. "
                               "<a href='https://www.uni-hannover.de/de/universitaet/"
                               "organisation/dezernate/dezernat-6/pruefungsamt/'"
                               "target='_blank'>Hier geht es zur Website.</a>",


                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("prüfungsamt_OS"),
            defaults={
                "title": "Mehr-Fächer-Prüfungsamt PATMOS",
                "description": "Das Mehrfächer-Prüfungsamt ist zuständig für die Prüfungsadministration des "
                               "fachübergreifenden Bereichs (Kerncurriculum Lehrerbildung"
                               ", allgemeine Schlüsselkompetenzen) "
                               "und für die Erstellung von übergreifenden Bescheinigungen, Leistungsübersichten sowie "
                               "Abschlusszeugnissen in den Mehrfächer-Studiengängen. "
                               "<a href='https://www.uni-osnabrueck.de/universitaet/organisation/zentrale-verwaltung/"
                               "studentische-angelegenheiten/mehrfaecher-pruefungsamt-patmos/' "
                               "target='_blank'>Hier geht es zur Website.</a>",

                "type": "todo",
                "status": "template",
                "feedback_size": 0,
                "image": self.IMAGE,
                "order": order,
            }
        )

        return True

    def initialize(self, user):
        """
        When a user logs in for the first time, initial activities are generated.
        :param user: SiddataUser object
        :return: True if successful
        """
        goal = self.activate_recommender_for_user_and_create_first_goal(user)

        models.Activity.create_activity_from_template(
            template_id=self.get_template_id("general_information_question"),
            goal=goal,
        )

        models.Activity.create_activity_from_template(
            template_id=self.get_template_id("general_recommendation_question"),
            goal=goal,
        )

        return True


    def process_activity(self, activity):
        """
        :param activity:  models.Activity instance modified by Stud.IP plugin
        :return: True if successful
        """

        # get user api endpoint from incoming activity
        user_api_endpoint = activity.goal.userrecommender.user.origin.api_endpoint

        # check if answer value is None
        if activity.answers is None:
            activity.answers = []

        if "Studienverlauf, Prüfungen, Rückmeldung" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("international_office_OS"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("sekretariat_OS"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("studienberatung_OS"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("prüfungsamt_OS"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("international_office_UB"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("sekretariat_UB"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("studienberatung_UB"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("international_office_LUH"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("sekretariat_LUH"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("studienberatung_LUH"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("prüfungsamt_LUH"),
                    goal=activity.goal,
                )

        if "Literatur ausleihen" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("library_OS"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("library_UB"),
                    goal=activity.goal,
                )


            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("library_LUH"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("rooms_LUH"),
                    goal=activity.goal,
                )

        if "Raum für Gruppenarbeiten" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("library_OS"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("rooms_OS"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("library_UB"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("rooms_UB"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("rooms_LUH"),
                    goal=activity.goal,
                )

        if "Raum zum ruhigen Arbeiten" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("library_OS"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("library_UB"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("rooms_LUH"),
                    goal=activity.goal,
                )

        if "Studium und Familie" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("family_OS"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("family_UB"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("family_LUH"),
                    goal=activity.goal,
                )

        if "Sport treiben" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("sports_OS"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("sports_UB"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("sports_LUH"),
                    goal=activity.goal,
                )

        if "eine weitere Sprache lernen" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("language_OS"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("language_UB"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("language_LUH"),
                    goal=activity.goal,
                )

        if "Auslandssemester" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("language_OS"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("international_office_OS"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("language_UB"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("international_office_UB"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("language_LUH"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("international_office_LUH"),
                    goal=activity.goal,
                )

        if "Probleme im Studium" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("sekretariat_OS"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("studienberatung_OS"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("problems_OS"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("sekretariat_UB"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("studienberatung_UB"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("problems_UB"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("sekretariat_LUH"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("studienberatung_LUH"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("problems_LUH"),
                    goal=activity.goal,
                )

        if "Technische Fragen und Probleme" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("rechenzentrum_OS"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("digitization_OS"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("rechenzentrum_UB"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("digitization_UB"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("rechenzentrum_LUH"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("digitization_LUH"),
                    goal=activity.goal,
                )

        if "Finanzierung meines Studiums" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("funding_OS"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("asta_OS"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("funding_UB"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("asta_UB"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("funding_LUH"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("asta_LUH"),
                    goal=activity.goal,
                )

        if "Wohnen" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("dorms_OS"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("dorms_UB"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("dorms_LUH"),
                    goal=activity.goal,
                )

        if "Was gibt es heute zu Mittag?" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("cantine_OS"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("cantine_UB"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("cantine_LUH"),
                    goal=activity.goal,
                )

        ### ORANGE TREE ###

        if "Wissenschaftliches Arbeiten" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_0"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_1"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_2"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_3"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_4"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_22"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_23"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_27"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_0"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_1"),
                    goal=activity.goal,
                )

        if "Lernen & Gedächtnis" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_3"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_4"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_6"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):
                ...
            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_13"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_16"),
                    goal=activity.goal,
                )

        if "Prüfungsvorbereitung" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_6"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_24"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_25"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_26"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):
                ...

        if "Präsentation & Kommunikation" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_8"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):
                ...
            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_15"),
                    goal=activity.goal,
                )

        if "Projektmanagement" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):
                ...
            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):
                ...
            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):
                ...

        if "Selbst- und Zeitmanagement" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_5"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_6"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_7"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_9"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_10"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_11"),
                    goal=activity.goal,
                )
            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_18"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_19"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_20"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_21"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_12"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_14"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_17"),
                    goal=activity.goal,
                )

        if "Gesund studieren" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_5"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_6"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):
                ...
            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):
                ...

        if "Sport & Bewegung" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):
                ...
            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):
                ...
            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):
                ...

        if "Literaturverwaltung" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_1"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_2"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):
                ...
            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):
                ...

        if "Schreibtraining" in activity.answers:
            if any(endpoint in user_api_endpoint for endpoint in ["osnabrueck", "localhost"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_0"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["bremen"]):

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_22"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_23"),
                    goal=activity.goal,
                )

                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("course_recommendation_27"),
                    goal=activity.goal,
                )

            if any(endpoint in user_api_endpoint for endpoint in ["hannover"]):
                ...

        return True
