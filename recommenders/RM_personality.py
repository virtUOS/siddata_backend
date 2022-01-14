"""
Implementation of Questionnaires for different purposes.
"""
import json
import logging

from backend import models
from recommenders.RM_BASE import RM_BASE


class RM_personality(RM_BASE):
    """
        Generates different questionnaires.
    """

    def __init__(self):
        # this magic line of code lets our recommender inherit all attributes and methods from the baseclass.
        super().__init__()
        # This name should be unique and appears in the Stud.IP GUI.
        self.NAME = "Gedächtnis und Aufmerksamkeit"
        # The description text summarizes the functionality. It is shown in teaser activity and tile view,
        self.DESCRIPTION = "Lerne mehr über deine Persönlichkeit und dein Lernverhalten"
        # This text is displayed in Teaser Activities
        self.TEASER_TEXT = "Lerne mehr über die Fähigkeiten deines Gedächtnisses kennen. Dazu kannst du " \
                           "verschiedene Tests durchführen und bekommst persönlich angepasste Empfehlungen."

        # If set to False, the recommender will not appear in the GUI or the DB
        self.ACTIVE = True
        # Image is shown in teaser activity
        self.IMAGE = "personality.png"
        # determines arrangement in Frontend
        self.ORDER = 6
        # This string tells the user which data is required for this recommender
        self.DATA_INFO = "Diese Funktion speichert diejenigen Daten, die du aktiv eingibst."
        # Reference to the database object, can be used as value vor recommender attribute in goals.
        self.recommender = models.Recommender.objects.get_or_create(
            name=self.get_name(),
            description=self.DESCRIPTION,
            classname=self.__class__.__name__,
            image=self.IMAGE,
            order=self.ORDER,
            data_info=self.DATA_INFO,
        )[0]
        self.questions_personality = ["Ich bin sehr gut in Spielen, wie beispielsweise Memory",
                                      "Wenn mir jemand eine Telefonnummer sagt, habe ich sie bereits nach ein paar Sekunden wieder vergessen.",
                                      "Mir fällt es leicht Fakten für Prüfungen auswendig zu lernen.",
                                      "Ich muss meine Einkaufslisten aufschreiben, damit ich nichts vergesse.",
                                      "Ich denke, ich bin sehr gut im Multitasking.",
                                      "Um eine Tätigkeit erfolgreich abzuschließen, konzentriere ich mich auf nur eine Sache auf einmal.",
                                      ]

    def initialize_templates(self):
        """
        Creates and updates all templates of this recommender
        Is executed at server startup
        """
        super().initialize_templates()

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("lng_overview"),
            defaults={
                "title": "Lernen und Gedächtnis",
                "description": "Mit diesem Modul werden relevante Aspekte für den Lern- und Studienerfolg getestet. "
                               "Basierend auf den Ergebnissen der Tests generiert SIDDATA Ratschläge zum erfolgreichen"
                               " Lernen.<br><br>" \
                               "Insgesamt gibt es zwei unterschiedliche Tests, die das Gleiche messen. Um Feedback "
                               "zu erhalten können beide oder auch nur einer der Tests durchgeführt werden.<br><br>"
                               "Absolvierst du beide Tests, bekommst du Rückmeldungen zur Übereinstimmung.",
                "type": "todo",
                "status": "template",
                "image": self.IMAGE,
                "feedback_size": 0,
                "order": 1000001001,
                "button_text": "~static",
            }
        )

        choice1_question = models.Question.objects.get_or_create(
            question_text="Wie schätzt du relevanten Aspekte für deinen Lern- und Studienerfolg selbst ein? Mit dem " \
                          "folgenden Fragebogen kannst du dich dazu selbst bewerten.<br><br>" \
                          "Möchtest du den Fragebogen zur <strong>Selbsteinschätzung</strong> ausfüllen?",
            answer_type="selection",
            selection_answers=["Ja", "Nein"]
        )[0]

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("choice_self_assessement"),
            defaults={
                "title": "Fragebogen",
                "description": "choice 1",
                "type": "question",
                "status": "template",
                "image": self.IMAGE,
                "question": choice1_question,
                "feedback_size": 0,
                "order": 1000001002,
            }
        )

        choice2_question = models.Question.objects.get_or_create(
            question_text="Willst du relevanten Aspekte für deinen Lern- und Studienerfolg experimentell testen? " \
                          "Mit dem Experiment (in englisch) werden diese Aspekte objektiv getestet und darauf "
                          "basierend genaues Feedback gegeben.<br><br>"
                          "Möchtest du das Experiment zur <strong>technischen Einschätzung</strong> durchführen? ",
            answer_type="selection",
            selection_answers=["Ja", "Nein"]
        )[0]

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("choice_labvanced"),
            defaults={
                "title": "Technische Einschätzung",
                "description": "choice 1",
                "type": "question",
                "status": "template",
                "image": self.IMAGE,
                "question": choice2_question,
                "feedback_size": 0,
                "order": 1000002001,
            }
        )

        resource = models.WebResource.objects.create(
            title="LabVanced Experiment",
            description="Ein Experiment (in Englisch) zum Testen einzelner wichtiger Komponenten für den "
                        "Lernerfolg kann mit diesem Link abgerufen werden:",
            source="https://www.labvanced.com/player.html?id=27052",
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("lng_labvanced_url"),
            defaults={
                "title": "LabVanced",
                "description": "",
                "type": "resource",
                "resource": resource,
                "status": "template",
                "image": self.IMAGE,
                "order": 1000001002,
                "feedback_size": 0,
                "form": 1,
            }
        )

        lng_question = models.Question.objects.get_or_create(
            question_text="Hier kann das Ergebnis des Experiments einfügt werden:",
            answer_type="text",
        )[0]

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("lng_labvanced_input"),
            defaults={
                "title": "LabVanced",
                "description": "LabVanced Ergebnis",
                "type": "question",
                "status": "template",
                "image": self.IMAGE,
                "question": lng_question,
                "feedback_size": 0,
                "order": 1000001003,
                "form": 1,
            }
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("lng_testintro"),
            defaults={
                "title": "Lernen und Gedächtnis",
                "description": "Der folgende Test dient zu deiner Selbsteinschätzung der wichtigen Komponenten für den Lernerfolg:",
                "type": "todo",
                "status": "template",
                "image": self.IMAGE,
                "feedback_size": 0,
                "order": 1000001004,
            }
        )

        likert_scale = self.get_likert_scale(5)
        n_item = 1
        for element in self.questions_personality:
            q = models.Question.objects.get_or_create(
                question_text=element,
                answer_type="likert",
                selection_answers=likert_scale
            )[0]
            q.save()

            t = models.ActivityTemplate.objects.update_or_create(
                template_id=self.get_template_id("Item_{}".format(n_item)),
                defaults={
                    "title": "Fragebogen zur Selbsteinschätzung",
                    "description": n_item,
                    "type": "question",
                    "status": "template",
                    "question": q,
                    "order": 1000000000 + n_item,
                    "feedback_size": 0,
                    "form": 2,
                }
            )[0]
            t.save()
            n_item += 1

        description = "Du hast das Langzeitgedächtnis, das Kurzzeitgedächtnis und deine Fähigkeit zwischen Aufgaben " \
                      "zu wechseln, getestet.<br><br>Das Langzeitgedächtnis (LZG) speichert Informationen für eine lange " \
                      "Zeit im Gehirn ab und wird beispielsweise beansprucht wenn wir Fakten lernen.<br><br>Das " \
                      "Kurzzeitgedächtnis (KZG) hilft uns Informationen für eine kurze Zeit (kürzer als 1 Minute) im " \
                      "Gedächtnis zu behalten und ist zum Beispiel gefragt wenn wir Spiele wie Memory spielst, bei " \
                      "denen wir uns verschiedene Karten über einen kurzen Zeitraum merken müssen.<br><br>Die Fähigkeit " \
                      "zwischen Aufgaben zu wechseln / “Task-Switching” (TS) ist zum Beispiel gefragt wenn man an " \
                      "mehreren Aufgaben kurzfristig hintereinander arbeitet.<br><br>Anhand deiner Werte von LZG, KZG " \
                      "und TS haben wir folgende Ratschläge für dich gemacht. Passende Lernstrategien können dir " \
                      "dabei helfen, effektiv zu lernen und mehr Freunde beim Lernen zu haben."

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("feedback"),
            defaults={
                "title": "Persönlichkeits-Fragebogen - Feedback",
                "type": "todo",
                "status": "template",
                "description": description,
                "image": self.IMAGE,
                "order": 1000000000,
                "feedback_size": 2,
            }
        )

        # show suggestions (before official learning)
        description = "1. Ich formuliere fachliche Fragen zu dem Thema und suche aktiv nach Antworten. " + \
                      "<br><br>2. Ich überlege mir, was ich schon über das Thema weiß und schreibe " \
                                        "dies in Stichworten auf oder mache mir dazu eine Skizze." + "<br>" + \
                      "<br>" + "3. Ich frage mich, was mich " \
                               "persönlich an dem Thema interessiert oder interessieren könnte. "

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("strategies_before_learning_1"),
            defaults={
                "title": "Empfehlungen zu Lernstrategien VOR dem Lernen",
                "type": "todo",
                "status": "template",
                "description": description,
                "order": 1000000100,
                "image": self.IMAGE,
                "feedback_size": 2,
            }
        )

        description = "1. Ich formuliere fachliche Fragen zu dem Thema und suche aktiv nach Antworten. "

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("strategies_before_learning_2"),
            defaults={
                "title": "Empfehlungen zu Lernstrategien VOR dem Lernen",
                "type": "todo",
                "status": "template",
                "description": description,
                "order": 1000000100,
                "image": self.IMAGE,
                "feedback_size": 2,
            }
        )

        description = "1. Ich überlege mir, was ich schon über das Thema weiß und schreibe dies in " \
                      "Stichworten auf oder mache mir dazu eine Skizze. " + "<br>" + "<br>" + \
                      "2. Ich frage mich, was mich persönlich an dem Thema interessiert oder " \
                      "interessieren könnte. "

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("strategies_before_learning_3"),
            defaults={
                "title": "Empfehlungen zu Lernstrategien VOR dem Lernen",
                "type": "todo",
                "status": "template",
                "description": description,
                "order": 1000000100,
                "image": self.IMAGE,
                "feedback_size": 2,
            }
        )

        # show suggestions (during official learning)
        description = "1. Ich suche nach dem roten Faden: Was sind die Verbindungen zwischen den " \
                      "wichtigen Gedanken und Fakten?" + "<br>" + "<br>" + \
                      "2. Ich denke intensiv über den Stoff nach und prüfe, " \
                      "ob ich alles gut verstanden habe. Ich verschaffe mir einen Überblick, um von " \
                      "einem allgemeinen Verständnis aus die Details besser zu verstehen." + "<br>" + \
                      "<br>" + "3. Ich schreibe den Stoff in meinen eigenen Worten auf (Paraphrasieren). "

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("strategies_during_learning_1"),
            defaults={
                "title": "Empfehlungen zu Lernstrategien WÄHREND des Lernen",
                "type": "todo",
                "status": "template",
                "description": description,
                "order": 1000000200,
                "image": self.IMAGE,
                "feedback_size": 2,
            }
        )

        description = "1. Ich suche nach dem roten Faden: Was sind die Verbindungen zwischen den " \
                      "wichtigen " \
                      "Gedanken und Fakten?" + "<br>" + "<br>" + \
                      "2. Ich denke intensiv über den Stoff nach und prüfe, ob ich " \
                      "alles gut verstanden habe. "

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("strategies_during_learning_2"),
            defaults={
                "title": "Empfehlungen zu Lernstrategien WÄHREND des Lernen",
                "type": "todo",
                "status": "template",
                "description": description,
                "order": 1000000200,
                "image": self.IMAGE,
                "feedback_size": 2,
            }
        )

        description = "1. Ich suche nach dem roten Faden: Was sind die Verbindungen zwischen den " \
                      "wichtigen Gedanken und Fakten?" + "<br>" + "<br>" + \
                      "2. Ich denke intensiv über den Stoff nach und prüfe, " \
                      "ob ich alles gut verstanden habe." + "<br>" + "<br>" + \
                      "3. Ich gliedere den Stoff anhand vorhandener Strukturen." + "<br>" + "<br>" + \
                      "4. Ich achte darauf, sowohl Details zu verstehen als auch einen " \
                      "Überblick zu erlangen."

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("strategies_during_learning_3"),
            defaults={
                "title": "Empfehlungen zu Lernstrategien WÄHREND des Lernen",
                "type": "todo",
                "status": "template",
                "description": description,
                "order": 1000000200,
                "image": self.IMAGE,
                "feedback_size": 2,
            }
        )

        description = "1. Ich stelle den Lernstoff regelmäßig in Bezug mit meinem Vorwissen." + "<br>" + \
                      "<br>" + "2. Ich suche nach dem roten Faden: Was sind die Verbindungen zwischen " \
                               "den wichtigen " \
                               "Gedanken und Fakten?" + "<br>" + "<br>" + \
                      "3. Ich suche nach konkreten Beispielen und Anwendungen" + "<br>" + "<br>" + \
                      "4. Ich schreibe den Stoff in meinen eigenen Worten auf (Paraphrasieren)."

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("strategies_during_learning_4"),
            defaults={
                "title": "Empfehlungen zu Lernstrategien WÄHREND des Lernen",
                "type": "todo",
                "status": "template",
                "description": description,
                "order": 1000000200,
                "image": self.IMAGE,
                "feedback_size": 2,
            }
        )

        description = "1. Ich stelle den Lernstoff regelmäßig in Bezug mit meinem Vorwissen." + "<br>" + \
                      "<br>" + "2. Ich suche nach dem roten Faden: Was sind die Verbindungen " \
                               "zwischen den wichtigen " \
                               "Gedanken und Fakten?" + "<br>" + "<br>" + \
                      "3. Ich verschaffe mir einen Überblick, um von einem allgemeinen Verständnis aus die " \
                      "Details besser zu verstehen." + "<br>" + "<br>" + \
                      "4. Ich schreibe den Stoff in meinen eigenen Worten auf (Paraphrasieren)."

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("strategies_during_learning_5"),
            defaults={
                "title": "Empfehlungen zu Lernstrategien WÄHREND des Lernen",
                "type": "todo",
                "status": "template",
                "description": description,
                "order": 1000000200,
                "image": self.IMAGE,
                "feedback_size": 2,
            }
        )

        description = "1. Ich stelle den Lernstoff regelmäßig in Bezug mit meinem Vorwissen." + "<br>" + \
                      "<br>" + \
                      "2. Ich suche nach dem roten Faden: Was sind die Verbindungen zwischen " \
                      "den wichtigen " \
                      "Gedanken und Fakten?" + "<br>" + "<br>" + \
                      "3. Ich gliedere den Stoff anhand vorhandener Strukturen." + "<br>" + "<br>" + \
                      "4. Ich achte darauf, sowohl Details zu verstehen als auch einen " \
                      "Überblick zu erlangen."

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("strategies_during_learning_6"),
            defaults={
                "title": "Empfehlungen zu Lernstrategien WÄHREND des Lernen",
                "type": "todo",
                "status": "template",
                "description": description,
                "order": 1000000200,
                "image": self.IMAGE,
                "feedback_size": 2,
            }
        )

        description = "1. Ich frage mich, was mich persönlich an dem Thema interessiert oder " \
                      "interessieren könnte. " + "<br>" + "<br>" + \
                      "2. Ich schreibe den Stoff in meinen eigenen Worten auf (Paraphrasieren)."

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("strategies_during_learning_7"),
            defaults={
                "title": "Empfehlungen zu Lernstrategien WÄHREND des Lernen",
                "type": "todo",
                "status": "template",
                "description": description,
                "order": 1000000200,
                "image": self.IMAGE,
                "feedback_size": 2,
            }
        )

        description = "1. Ich verschaffe mir einen Überblick, um von einem allgemeinen Verständnis " \
                      "aus die Details besser zu verstehen." + "<br>" + "<br>" + \
                      "2. Ich schreibe den Stoff in meinen eigenen Worten auf (Paraphrasieren)."

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("strategies_during_learning_8"),
            defaults={
                "title": "Empfehlungen zu Lernstrategien WÄHREND des Lernen",
                "type": "todo",
                "status": "template",
                "description": description,
                "order": 1000000200,
                "image": self.IMAGE,
                "feedback_size": 2,
            }
        )

        description = "1. Ich gliedere den Stoff anhand vorhandener Strukturen." + "<br>" + "<br>" + \
                      "2. Ich achte darauf, sowohl Details zu verstehen als auch einen " \
                      "Überblick zu erlangen."

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("strategies_during_learning_9"),
            defaults={
                "title": "Empfehlungen zu Lernstrategien WÄHREND des Lernen",
                "type": "todo",
                "status": "template",
                "description": description,
                "order": 1000000200,
                "image": self.IMAGE,
                "feedback_size": 2,
            }
        )

        # show suggestions (after official learning)
        description = "1. Ich schreibe mir in meinen eigenen Worten eine kurze Zusammenfassung der " \
                      "wichtigsten Inhalte, ohne dabei in meine Aufzeichnungen oder in Bücher zu schauen." \
                      + "<br>" + "<br>" + "2. Ich erkläre Kommiliton*innen den Stoff. " + "<br>" + "<br>" \
                      + "3. Während ich den Stoff einer anderen " \
                        "Person erkläre, identifiziere ich Verständnis- und Erinnerungslücken und " \
                        "arbeite diese auf." + "<br>" + "<br>" + "4. Ich stelle mir vor, wie ich einem " \
                                                                 "Freund oder einer Freundin den Stoff erklären würde. "

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("strategies_after_learning_1"),
            defaults={
                "title": "Empfehlungen zu Lernstrategien NACH dem Lernen",
                "type": "todo",
                "status": "template",
                "description": description,
                "image": self.IMAGE,
                "order": 1000000300,
                "feedback_size": 2,
            }
        )

        description = "1. Ich schreibe mir in meinen eigenen Worten eine kurze Zusammenfassung der " \
                      "wichtigsten Inhalte, ohne dabei in meine Aufzeichnungen oder in Bücher zu schauen." \
                      + "<br>" + "<br>" + "2. Ich erkläre Kommiliton*innen den Stoff." + "<br>" + "<br>" + \
                      "3. Während ich den Stoff einer anderen Person erkläre, identifiziere ich " \
                      "Verständnis- und Erinnerungslücken und arbeite diese auf."

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("strategies_after_learning_2"),
            defaults={
                "title": "Empfehlungen zu Lernstrategien NACH dem Lernen",
                "type": "todo",
                "status": "template",
                "description": description,
                "image": self.IMAGE,
                "order": 1000000300,
                "feedback_size": 2,
            }
        )

        description = "1. Ich formuliere wichtige Gedanken in Merksätzen und rufe mir diese regelmäßig " \
                      "in Erinnerung - ohne dabei in meine Unterlagen zu schauen." \
                      + "<br>" + "<br>" + "2. Ich erkläre Kommiliton*innen den Stoff." + "<br>" + "<br>" + \
                      "3. Während ich den Stoff einer anderen Person erkläre, identifiziere ich " \
                      "Verständnis- und Erinnerungslücken und arbeite diese auf." + "<br>" + "<br>" + \
                      "4. Ich stelle mir vor, wie ich einem Freund oder einer Freundin den " \
                      "Stoff erklären würde."

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("strategies_after_learning_3"),
            defaults={
                "title": "Empfehlungen zu Lernstrategien NACH dem Lernen",
                "type": "todo",
                "status": "template",
                "description": description,
                "image": self.IMAGE,
                "order": 1000000300,
                "feedback_size": 2,
            }
        )

        description = "1. Ich formuliere wichtige Gedanken in Merksätzen und rufe mir diese regelmäßig " \
                      "in Erinnerung - ohne dabei in meine Unterlagen zu schauen." \
                      + "<br>" + "<br>" + "2. Ich erkläre Kommiliton*innen den Stoff." + "<br>" + "<br>" + \
                      "3. Während ich den Stoff einer anderen Person erkläre, identifiziere ich " \
                      "Verständnis- und Erinnerungslücken und arbeite diese auf."

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("strategies_after_learning_4"),
            defaults={
                "title": "Empfehlungen zu Lernstrategien NACH dem Lernen",
                "type": "todo",
                "status": "template",
                "description": description,
                "image": self.IMAGE,
                "order": 1000000300,
                "feedback_size": 2,
            }
        )

        description = "1. Ich versuche nachzuvollziehen, auf welchem Wege das Wissen zustande gekommen " \
                      "ist (beispielsweise durch mathematische Beweise, philosophische Argumentationen " \
                      "oder durch naturwissenschaftliche Experimente)." + "<br>" + "<br>" + \
                      "2. Ich denke mir Prüfungsfragen zum Stoff aus und versuche diese zu beantworten." + \
                      "<br>" + "<br>" + "3. Ich stelle mir vor, wie ich einem Freund oder " \
                                        "einer Freundin den Stoff erklären würde."

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("strategies_after_learning_5"),
            defaults={
                "title": "Empfehlungen zu Lernstrategien NACH dem Lernen",
                "type": "todo",
                "status": "template",
                "description": description,
                "image": self.IMAGE,
                "order": 1000000300,
                "feedback_size": 2,
            }
        )

        description = "1. Ich versuche nachzuvollziehen, auf welchem Wege das Wissen zustande gekommen " \
                      "ist (beispielsweise durch mathematische Beweise, philosophische Argumentationen " \
                      "oder durch naturwissenschaftliche Experimente)." + "<br>" + "<br>" \
                      + "2. Ich denke mir Prüfungsfragen zum Stoff aus und versuche diese zu beantworten."

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("strategies_after_learning_6"),
            defaults={
                "title": "Empfehlungen zu Lernstrategien NACH dem Lernen",
                "type": "todo",
                "status": "template",
                "description": description,
                "image": self.IMAGE,
                "order": 1000000300,
                "feedback_size": 2,
            }
        )

        description = "Mind Maps sind eine hilfreiche Weise Lernstoff besser zu verstehen und zu " \
                      "organisieren. Mit Miro kann man sowohl alleine als auch in Gruppen sehr einfach " \
                      "übersichtliche Mind Maps erstellen. "

        learning_resource = models.WebResource.objects.get_or_create(
            title="Mind Maps erstellen",
            description=description,
            source="https://miro.com/",
        )[0]

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("mind_maps"),
            defaults={
                "title": "Mind Maps erstellen",
                "type": "resource",
                "status": "template",
                "description": description,
                "resource": learning_resource,
                "image": self.IMAGE,
                "order": 1000000400,
                "feedback_size": 2,
            }
        )

        # insert external resource
        description1 = "Erfolgreiches Lernen beinhaltet verschiedene Strategien, beispielsweise " \
                       "das Schreiben von Karteikarten mit den wichtigsten Punkten oder das Erstellen " \
                       "und Lösen eigener Quizze. Hierbei kann das Online-Tool GoConqr Hilfestellung " \
                       "geben, indem es verschiedene Lernstrategien unterstützt. Einziger Nachteil " \
                       "Einziger Nachteil bei der kostenlosen Nutzung ist die angezeigte Werbung. "

        learning_resource1 = models.WebResource.objects.get_or_create(
            title="Online Notizen, Quizze, Karteikarten",
            description=description1,
            source="https://www.goconqr.com/",
        )[0]

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("goconqr"),
            defaults={
                "title": "Online Notizen, Quizze, Karteikarten",
                "type": "resource",
                "status": "template",
                "description": description1,
                "resource": learning_resource1,
                "image": self.IMAGE,
                "order": 1000000500,
                "feedback_size": 2,
            }
        )

        ### Comparison ###

        ### KZG ###
        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("KZG_self_greater_test"),
            defaults={
                "title": "Spezielles Feedback zu KZG",
                "type": "todo",
                "status": "template",
                "description": "Dein KZG hast du selbst besser eingeschätzt als es der objektive Test gezeigt hat.",
                "image": self.IMAGE,
                "order": 1000000301,
                "feedback_size": 2,
            }
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("KZG_self_equals_test"),
            defaults={
                "title": "Spezielles Feedback zu KZG",
                "type": "todo",
                "status": "template",
                "description": "Die Ergebnisse deiner Selbsteinschätzung und deinem objektiven Test für das KZG stimmen "
                               "miteinander überein.",
                "image": self.IMAGE,
                "order": 1000000301,
                "feedback_size": 2,
            }
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("KZG_self_smaller_test"),
            defaults={
                "title": "Spezielles Feedback zu KZG",
                "type": "todo",
                "status": "template",
                "description": "Das Ergebnis zu deinem KZG war besser in dem objektiven Test als deiner "
                               "Selbsteinschätzung.",
                "image": self.IMAGE,
                "order": 1000000301,
                "feedback_size": 2,
            }
        )

        ### LZG ###
        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("LZG_self_greater_test"),
            defaults={
                "title": "Spezielles Feedback zu LZG",
                "type": "todo",
                "status": "template",
                "description": "Dein LZG hast du selbst besser eingeschätzt als es der objektive Test gezeigt hat.",
                "image": self.IMAGE,
                "order": 1000000302,
                "feedback_size": 2,
            }
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("LZG_self_equals_test"),
            defaults={
                "title": "Spezielles Feedback zu LZG",
                "type": "todo",
                "status": "template",
                "description": "Die Ergebnisse deiner Selbsteinschätzung und deinem objektiven Test für das LZG stimmen "
                               "miteinander überein.",
                "image": self.IMAGE,
                "order": 1000000302,
                "feedback_size": 2,
            }
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("LZG_self_smaller_test"),
            defaults={
                "title": "Spezielles Feedback zu LZG",
                "type": "todo",
                "status": "template",
                "description": "Das Ergebnis zu deinem LZG war besser in dem objektiven Test als deiner "
                               "Selbsteinschätzung.",
                "image": self.IMAGE,
                "order": 1000000302,
                "feedback_size": 2,
            }
        )

        ### TS ###
        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("TS_self_greater_test"),
            defaults={
                "title": "Spezielles Feedback zu TS",
                "type": "todo",
                "status": "template",
                "description": "Deine Fähigkeit Aufgaben zu wechseln (TS) hast du selbst besser eingeschätzt als es der objektive Test gezeigt hat.",
                "image": self.IMAGE,
                "order": 1000000303,
                "feedback_size": 2,
            }
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("TS_self_equals_test"),
            defaults={
                "title": "Spezielles Feedback zu TS",
                "type": "todo",
                "status": "template",
                "description": "Das Ergebnis zu deiner Fähigkeit zwischen Aufgaben zu wechseln (TS) war besser in dem "
                               "objektiven Test als deiner Selbsteinschätzung.",
                "image": self.IMAGE,
                "order": 1000000303,
                "feedback_size": 2,
            }
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("TS_self_smaller_test"),
            defaults={
                "title": "Spezielles Feedback zu TS",
                "type": "todo",
                "status": "template",
                "description": "Die Ergebnisse deiner Selbsteinschätzung und deinem objektiven Test für die Fähigkeit "
                               "zwischen Aufgaben zu wechseln (TS) stimmen miteinander überein.",
                "image": self.IMAGE,
                "order": 1000000303,
                "feedback_size": 2,
            }
        )




    def initialize(self, user):
        """
        When a user logs in for the first time, initial activities are generated.
        :param user: SiddataUser object
        :return: True if successful
        """
        goal = self.activate_recommender_for_user_and_create_first_goal(user)
        goal.order = 1
        goal.save()

        models.Activity.create_activity_from_template(
            template_id=self.get_template_id("lng_overview"),
            goal=goal,
        )

        self_assessment_goal = models.Goal.objects.get_or_create(
            title="Selbsteinschätzung",
            description="Hier kannst Du durch die Beantwortung einer Reihe von Fragen dein Langzeitgedächtnis, "
                        "dein Kurzzeitgedächnis und deine Multitaskingfähigkeit einschätzen.",
            userrecommender=goal.userrecommender,
            order=2,
        )[0]
        self_assessment_goal.save()

        models.Activity.create_activity_from_template(
            template_id=self.get_template_id("choice_self_assessement"),
            goal=self_assessment_goal,
        )

        labvanced_goal = models.Goal.objects.get_or_create(
            title="Technische Messung",
            description="Hier kannst Du über die Teilnahme an eine Online-Experiment dein Langzeitgedächtnis, "
                        "dein Kurzzeitgedächnis und deine Multitaskingfähigkeit einschätzen.",
            userrecommender=goal.userrecommender,
            order=3,
        )[0]
        labvanced_goal.save()

        models.Activity.create_activity_from_template(
            template_id=self.get_template_id("choice_labvanced"),
            goal=labvanced_goal,
        )

    def initialize_questionnaire(self, goal):

        n_item = 1
        for element in self.questions_personality:

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("Item_{}".format(n_item)),
                goal=goal,
            )
            n_item += 1

        return True

    def get_scale_value(self, items):
        """
        transfer the value of likert scale from words into numbers
        """
        if items == 4:
            scale_value_dic_4 = {
                "trifft nicht zu": 1,
                "trifft eher nicht zu": 2,
                "trifft eher zu": 3,
                "trifft zu": 4}
            return scale_value_dic_4

        elif items == 5:
            scale_value_dic_5 = {
                "trifft nicht zu": 1,
                "trifft eher nicht zu": 2,
                "teils - teils": 3,
                "trifft eher zu": 4,
                "trifft zu": 5}
            return scale_value_dic_5

        elif items == 7:
            scale_value_dic_7 = {
                "trifft überhaupt nicht zu": 1,
                "trifft wenig zu": 2,
                "trifft eher nicht zu": 3,
                "teils teils": 4,
                "trifft eher zu": 5,
                "trifft viel zu": 6,
                "trifft vollständig zu": 7}
            return scale_value_dic_7

        else:
            return "no scale for {}".format(items)

    def get_likert_scale(self, items):

        if items == 4:
            likert_scale_answers_4 = [
                "trifft nicht zu",
                "trifft eher nicht zu",
                "trifft eher zu",
                "trifft zu"]
            return likert_scale_answers_4

        elif items == 5:
            likert_scale_answers_5 = [
                "trifft nicht zu",
                "trifft eher nicht zu",
                "teils - teils",
                "trifft eher zu",
                "trifft zu"]
            return likert_scale_answers_5

        elif items == 7:
            likert_scale_answers_7 = [
                "trifft überhaupt nicht zu",
                "trifft wenig zu",
                "trifft eher nicht zu",
                "teils teils",
                "trifft eher zu",
                "trifft viel zu",
                "trifft vollständig zu"]
            return likert_scale_answers_7

        else:
            return "no scale for {}".format(items)

    def process_activity(self, activity):
        """
        :param activity:  activity
        :return: True if successful
        """

        # User wants to do self-assessment
        if activity.has_template(self.get_template_id("choice_self_assessement")):
            if "Ja" in activity.answers:
                self.initialize_questionnaire(activity.goal)

        # User wants to do labvanced measurement
        if activity.has_template(self.get_template_id("choice_labvanced")):
            if "Ja" in activity.answers:


                initial_activities = ["lng_labvanced_url", "lng_labvanced_input"]

                for act in initial_activities:
                    models.Activity.create_activity_from_template(
                        template_id=self.get_template_id(act),
                        goal=activity.goal,
                    )

        # User has inserted result of external measurement, provide recommendations
        # Format of input: {"task_switching":0,"long-term-memory":1,"short-term-memory":2}
        if activity.has_template(self.get_template_id("lng_labvanced_input")):
            try:
                results = json.loads(activity.answers[0])

                results_personality = {}
                if results["task_switching"] == 0:
                    results_personality["TS"] = "not good"
                elif results["task_switching"] == 1:
                    results_personality["TS"] = "very good"
                else:
                    logging.error("Task switching value not allowed: {}".format(results["task-switching"]))

                if results["long-term-memory"] == 0:
                    results_personality["LZG"] = "not good"
                elif results["long-term-memory"] == 1:
                    results_personality["LZG"] = "good"
                elif results["long-term-memory"] == 2:
                    results_personality["LZG"] = "very good"
                else:
                    logging.error("Long term memory value not allowed: {}".format(results["LZG"]))

                if results["short-term-memory"] == 0:
                    results_personality["KZG"] = "not good"
                elif results["short-term-memory"] == 1:
                    results_personality["KZG"] = "good"
                elif results["short-term-memory"] == 2:
                    results_personality["KZG"] = "very good"
                else:
                    logging.error("Short term memory value not allowed: {}".format(results["KZG"]))

            except Exception:
                logging.exception("Error in RM_professions.process_activity()")
                return False

            activity.goal.set_property(
                key="results_personality",
                value=json.dumps(results_personality)
            )

            self.generate_recommendations(results_personality, activity.goal)


        # process personality questionnaire
        if activity.title == "Fragebogen zur Selbsteinschätzung":


            results_personality = activity.goal.get_property(
                    key="results_personality"
            )

            if results_personality == None:
                results_personality = {"LZG": [],
                                       "KZG": [],
                                       "TS": [],
                                       # number of evaluated items
                                       "count": 0}
            else:
                results_personality = json.loads(results_personality)

            # remember that one more item has been processed
            results_personality["count"] += 1

            likert_scale_5_dic = self.get_scale_value(5)

            # negative polarized items
            negative_item = [2, 4, 6]

            # categorize items into corresponding attributes
            shortTermMemory = [1, 2]
            longTermMemory = [3, 4]
            multitasking = [5, 6]

            n_item = int(activity.description)

            # reverse negatively polarized Items
            if n_item in negative_item:
                n_item_val = 6 - likert_scale_5_dic[activity.answers[0]]
            else:
                n_item_val = likert_scale_5_dic[activity.answers[0]]

            if n_item in longTermMemory:
                # if there is no entry yet, the answered activity is the first for this variable
                if results_personality["LZG"] == []:
                    results_personality["LZG"] = [n_item_val]
                else:
                    summed_results = results_personality["LZG"][0] + n_item_val
                    # categorize the cognitive performance into three levels and save their levels into the table
                    if summed_results < 6:
                        results_personality["LZG"] = "not good"
                    elif summed_results > 8:
                        results_personality["LZG"] = "very good"
                    else:
                        results_personality["LZG"] = "good"
            elif n_item in shortTermMemory:
                if results_personality["KZG"] == []:
                    results_personality["KZG"] = [n_item_val]
                else:
                    summed_results = results_personality["KZG"][0] + n_item_val
                    # categorize the cognitive performance into three levels and save their levels into the table
                    if summed_results < 6:
                        results_personality["KZG"] = "not good"
                    elif summed_results > 8:
                        results_personality["KZG"] = "very good"
                    else:
                        results_personality["KZG"] = "good"
            elif n_item in multitasking:
                if results_personality["TS"] == []:
                    results_personality["TS"] = [n_item_val]
                else:
                    summed_results = results_personality["TS"][0] + n_item_val
                    # categorize the cognitive performance into three levels and save their levels into the table
                    if summed_results < 6:
                        results_personality["TS"] = "not good"
                    elif summed_results > 8:
                        results_personality["TS"] = "very good"
                    else:
                        results_personality["TS"] = "good"

            activity.goal.set_property(
                key="results_personality",
                value=json.dumps(results_personality)
            )

            if results_personality["count"] == 6:
                self.generate_recommendations(results_personality, activity.goal)

    def generate_recommendations(self, results_personality, goal):
        """
        show feedback which explains the meaning of measurements
        :param results_personality: Dictionary with values for all measured latent variables.
        :param goal: Goal object wo which the feedback Activities will be added.
        :return:
        """

        models.Activity.create_activity_from_template(
            template_id=self.get_template_id("feedback"),
            goal=goal,
        )

        # show suggestions according to values of both LTM and STM
        if results_personality["LZG"] == "not good" \
                and results_personality["KZG"] == "good":
            # show suggestions (before official learning)
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_before_learning_1"),
                goal=goal,
            )

            # show suggestions (during official learning)
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_during_learning_1"),
                goal=goal,
            )

            # show suggestions (after official learning)
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_after_learning_1"),
                goal=goal,
            )

            # insert extermal resource
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("mind_maps"),
                goal=goal,
            )

            # insert extermal resource
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("goconqr"),
                goal=goal,
            )

        if results_personality["KZG"] == "not good" \
                and results_personality["LZG"] == "not good":
            # show suggestions (before official learning)
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_before_learning_1"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_during_learning_2"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_after_learning_1"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("mind_maps"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("goconqr"),
                goal=goal,
            )

        if results_personality["LZG"] == "not good" \
                and results_personality["KZG"] == "very good":
            # show suggestions (before official learning)
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_before_learning_2"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_during_learning_3"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_after_learning_2"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("mind_maps"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("goconqr"),
                goal=goal,
            )

        if results_personality["LZG"] == "good" \
                and results_personality["KZG"] == "not good":
            # show suggestions (before official learning)
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_before_learning_1"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_during_learning_4"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_after_learning_3"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("mind_maps"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("goconqr"),
                goal=goal,
            )

        if results_personality["LZG"] == "good" \
                and results_personality["KZG"] == "good":
            # show suggestions (before official learning)
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_before_learning_1"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_during_learning_5"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_after_learning_3"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("mind_maps"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("goconqr"),
                goal=goal,
            )

        if results_personality["LZG"] == "good" \
                and results_personality["KZG"] == "very good":
            # show suggestions (before official learning)
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_before_learning_2"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_during_learning_6"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_after_learning_4"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("mind_maps"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("goconqr"),
                goal=goal,
            )

        if results_personality["LZG"] == "very good" \
                and results_personality["KZG"] == "not good":
            # show suggestions (before official learning)
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_before_learning_3"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_during_learning_7"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_after_learning_5"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("goconqr"),
                goal=goal,
            )

        if results_personality["LZG"] == "very good" \
                and results_personality["KZG"] == "good":
            # show suggestions (during learning)
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_during_learning_8"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_after_learning_5"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("goconqr"),
                goal=goal,
            )

        if results_personality["LZG"] == "very good" \
                and results_personality["KZG"] == "very good":
            # show suggestions (before official learning)
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_before_learning_3"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_during_learning_9"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("strategies_after_learning_6"),
                goal=goal,
            )

            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("goconqr"),
                goal=goal,
            )

        self.compare_test_results(goal)

    def compare_test_results(self, goal):
        """
        Tests if both measurements have been completed and provides feedback on coherence.
        :param goal:
        :return:
        """

        questionnaire_goal = models.Goal.objects.get(
            title="Selbsteinschätzung",
            description="Hier kannst Du durch die Beantwortung einer Reihe von Fragen dein Langzeitgedächtnis, "
                        "dein Kurzzeitgedächnis und deine Multitaskingfähigkeit einschätzen.",
            userrecommender=goal.userrecommender,
        )

        results_questionnaire = questionnaire_goal.get_property(
            key="results_personality"
        )
        # questionnaire not answered yet
        if results_questionnaire==None:
            return
        else:
            results_questionnaire = json.loads(results_questionnaire)
        # questionnaire not fully answered yet
        if results_questionnaire["count"] != 6:
            return

        labvanced_goal = models.Goal.objects.get(
            title="Technische Messung",
            description="Hier kannst Du über die Teilnahme an eine Online-Experiment dein Langzeitgedächtnis, "
                        "dein Kurzzeitgedächnis und deine Multitaskingfähigkeit einschätzen.",
            userrecommender=goal.userrecommender,
            order=3,
        )

        results_labvanced = labvanced_goal.get_property(
            key="results_personality"
        )
        # questionnaire not answered yet
        if results_labvanced==None:
            return
        else:
            results_labvanced = json.loads(results_labvanced)

        comparison_goal = models.Goal.objects.get_or_create(
            title="Vergleich der Messungen",
            description="Hier bekommst du Rückmeldungen dazu, inwiefern die Ergebnisse des Fragebogens und des "
                        "Online-Experiment übereinstimmen.",
            userrecommender=goal.userrecommender,
            order=4,
        )[0]
        comparison_goal.save()

        ### EQUAL ###

        if results_labvanced["LZG"] == results_questionnaire["LZG"]:
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("LZG_self_equals_test"),
                goal=comparison_goal,
            )
        if results_labvanced["KZG"] == results_questionnaire["KZG"]:
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("KZG_self_equals_test"),
                goal=comparison_goal,
            )
        if results_labvanced["TS"] == results_questionnaire["TS"]:
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("TS_self_equals_test"),
                goal=comparison_goal,
            )

        ### TS ###

        ### smaller ###
        if results_questionnaire["TS"]=="good" and results_labvanced["TS"] == "very good":
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("TS_self_smaller_test"),
                goal=comparison_goal,
            )

        if results_questionnaire["TS"]=="not good" and results_labvanced["TS"] == "very good":
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("TS_self_smaller_test"),
                goal=comparison_goal,
            )

        if results_questionnaire["TS"]=="not good" and results_labvanced["TS"] == "good":
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("TS_self_smaller_test"),
                goal=comparison_goal,
            )

        ### greater ###
        if results_questionnaire["TS"] == "very good" and results_labvanced["TS"] == "not good":
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("TS_self_smaller_test"),
                goal=comparison_goal,
            )

        if results_questionnaire["TS"] == "good" and results_labvanced["TS"] == "not good":
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("TS_self_smaller_test"),
                goal=comparison_goal,
            )

        ### LZG ###

        ### smaller ###
        if results_questionnaire["LZG"] == "not good" and results_labvanced["LZG"] == "good":
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("TS_self_smaller_test"),
                goal=comparison_goal,
            )

        if results_questionnaire["LZG"] == "not good" and results_labvanced["LZG"] == "very good":
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("TS_self_smaller_test"),
                goal=comparison_goal,
            )

        if results_questionnaire["LZG"] == "good" and results_labvanced["LZG"] == "very good":
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("TS_self_smaller_test"),
                goal=comparison_goal,
            )

        ### greater ###

        if results_questionnaire["LZG"] == "good" and results_labvanced["LZG"] == "not good":
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("TS_self_greater_test"),
                goal=comparison_goal,
            )

        if results_questionnaire["LZG"] == "very good" and results_labvanced["LZG"] == "not good":
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("TS_self_greater_test"),
                goal=comparison_goal,
            )

        if results_questionnaire["LZG"] == "very good" and results_labvanced["LZG"] == "good":
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("TS_self_greater_test"),
                goal=comparison_goal,
            )

        ### KZG ###

        ### smaller ###
        if results_questionnaire["KZG"] == "not good" and results_labvanced["KZG"] == "good":
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("TS_self_smaller_test"),
                goal=comparison_goal,
            )

        if results_questionnaire["KZG"] == "not good" and results_labvanced["KZG"] == "very good":
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("TS_self_smaller_test"),
                goal=comparison_goal,
            )

        if results_questionnaire["KZG"] == "good" and results_labvanced["KZG"] == "very good":
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("TS_self_smaller_test"),
                goal=comparison_goal,
            )

        ### greater ###

        if results_questionnaire["KZG"] == "good" and results_labvanced["KZG"] == "not good":
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("TS_self_greater_test"),
                goal=comparison_goal,
            )

        if results_questionnaire["KZG"] == "very good" and results_labvanced["KZG"] == "not good":
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("TS_self_greater_test"),
                goal=comparison_goal,
            )

        if results_questionnaire["KZG"] == "very good" and results_labvanced["KZG"] == "good":
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("TS_self_greater_test"),
                goal=comparison_goal,
            )







