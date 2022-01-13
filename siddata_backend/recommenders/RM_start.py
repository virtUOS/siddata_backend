from backend import models
from recommenders import recommender_functions
from recommenders.RM_BASE import RM_BASE


class RM_start(RM_BASE):
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
        self.NAME = "Startseite"
        # The description text summarizes the functionality. It is shown in teaser activity and tile view,
        self.DESCRIPTION = "Lorem ipsum the beginning is the end is the beginning."
        # This text is displayed in Teaser Activities
        self.TEASER_TEXT = "Lorem ipsum the beginning is the end is the beginning."
        # If set to False, the recommender will not appear in the GUI or the DB
        self.ACTIVE = True
        # "Order has to be a unique integer not used by other recommenders.
        self.ORDER = 0
        # Image is shown in teaser activity
        self.IMAGE = "professions.png"
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

    def initialize_templates(self):
        """
        Creates and updates all templates of this recommender
        Is executed at server startup
        """
        super().initialize_templates()

        welcome_text = "Siddata (www.siddata.de) unterstützt dich bei deinem persönlichen " \
                       "Weg durchs Studium und hilft dir, deine selbst gesteckten Bildungsziele auch über den " \
                       "Studienplan hinaus zu verfolgen." \
                       "<br>" \
                       "Siddata kann freiwillig genutzt werden. Welche Faktoren und Datenquellen dabei berücksichtigt " \
                       "werden, bestimmst du selbst.<br>Mit Siddata kannst du dich zum Beispiel mit anderen " \
                       "Studierenden vernetzen, mehr über dein Lernverhalten erfahren und Veranstaltungen an anderen " \
                       "Universitäten besuchen. Dazu kannst du verschiedene Funktionen aktivieren."

        order = 1000000001

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("welcome"),
            defaults={
                "title": "Was ist Siddata?",
                "type": "todo",
                "description": welcome_text,
                "status": "template",
                "image": "sid.png",
                "feedback_size": 0,
                "order": order,
            }
        )

        order += 1

        settings_text = "Als Stud.IP-Plugin kann Siddata mit deiner Zustimmung auf die Daten deines Stud.IP-Profils, " \
                        "deines Studiengangs und deiner belegten Kurse zugreifen. Dies legst du in den Einstellungen " \
                        "fest. "

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("settings"),
            defaults={
                "title": "Welche deiner Daten nutzt Siddata?",
                "type": "todo",
                "description": settings_text,
                "status": "template",
                "image": "sid.png",
                "feedback_size": 0,
                "order": order,
            }
        )

        order += 1

        instruction_text_1 = "Informationen und Empfehlungen werden dir in Siddata in Boxen wie dieser dargestellt.<br>" \
                             "Du kannst diese entweder abschließen, pausieren oder verwerfen.<br>" \
                             "Über die entsprechenden Ansichten (links unter der Navigation) kannst du die Boxen " \
                             "bei Bedarf wieder aufnehmen.<br>" \
                             "So lange eine Box nicht von dir bearbeitet wurde, ist sie offen.<br>" \
                             "Über die Buttons unten in jeder Box kannst du diese als abgeschlossen markieren.<br>" \
                             'Möchtest du eine Box später bearbeiten, kannst du sie über das Icon "Pausieren" zurückstellen.<br>' \
                             "Wenn du den Inhalt einer Box nicht sinnvoll findest, kannst du sie über das Icon Verwerfen aussortieren."

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("instructions_1"),
            defaults={
                "title": "Wie bedienst du Siddata?",
                "type": "todo",
                "description": instruction_text_1,
                "status": "template",
                "image": "stati.png",
                "feedback_size": 0,
                "order": order,
            }
        )

        order += 1

        instruction_text_2 = "Mit Siddata kannst du dich zum Beispiel mit anderen Studierenden vernetzen, mehr über " \
                             "dein Lernverhalten erfahren und Veranstaltungen an anderen Universitäten besuchen. " \
                             "Dazu kannst du verschiedene Funktionen/Tools aktivieren.<br><br>Im Folgenden werden " \
                             "dir alle Funktionen kurz beschrieben. Bitte entscheide dich zunächst, welche " \
                             "Funktionen du ausprobieren möchtest. Wenn du deine Meinung änderst, kannst du in " \
                             "den Einstellungen jederzeit Funktionen aktivieren oder deaktivieren."

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("instructions_2"),
            defaults={
                "title": "Was kann Siddata für dich tun?",
                "type": "todo",
                "description": instruction_text_2,
                "status": "template",
                "image": "sid.png",
                "feedback_size": 0,
                "order": order,
            }
        )

        order += 1

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("reset"),
            defaults={
                "title": "RESET",
                "description": "NUR IM POTOTYPBETRIEB VERFÜGBAR. " \
                               "Mit \"OK\" lösche ich meine Daten und kann somit als neuer User weiter testen. " \
                               "Damit die Löschung aktiv wird, logge ich mich bei Stud.IP aus und wieder ein.",
                "type": "todo",
                "status": "template",
                "image": "nuke.png",
                "feedback_size": 0,
                "order": 1900000000,
            }
        )

        return True

    def create_teaser_activity(self, goal):
        """
        This method is overridden without content. Reason: The Startpage is active by default.
        :param goal:
        :return:
        """
        return True

    def initialize(self, user):
        """
        When a user logs in for the first time, initial activities are generated.
        :param user: SiddataUser object
        :return: True if successful
        """
        # Relate recommender to user and magically create a goal that may be filled with activities
        goal = self.activate_recommender_for_user_and_create_first_goal(user)

        models.Activity.create_activity_from_template(
            template_id=self.get_template_id("welcome"),
            goal=goal,
        )

        models.Activity.create_activity_from_template(
            template_id=self.get_template_id("settings"),
            goal=goal,
        )

        models.Activity.create_activity_from_template(
            template_id=self.get_template_id("instructions_1"),
            goal=goal,
        )

        models.Activity.create_activity_from_template(
            template_id=self.get_template_id("instructions_2"),
            goal=goal,
        )

        models.Activity.create_activity_from_template(
            template_id=self.get_template_id("reset"),
            goal=goal,
            status="snoozed",
            color_theme="red",
        )

        return True

    def get_default_goal(self, user):
        """
        Returns the default goal to fill it with initial activities
        :return: default goal
        """
        userrecommender = models.SiddataUserRecommender.objects.get(
            user=user,
            recommender=self.recommender,
        )

        goal_start = models.Goal.objects.get(
            title=self.get_name(),
            userrecommender=userrecommender,
        )
        return goal_start

    def process_activity(self, activity):
        """
        :param activity:  models.Activity instance modified by Stud.IP plugin
        :return: True if successful
        """
        # activates other recommender if that is what the user intended
        if recommender_functions.check_for_teaser_activity(activity):
            return "Funktion wurde aktiviert. Du findest sie nun in der Navigation auf der linken Seite."

        # Delete user if reset activity was answered
        if activity.has_template(self.get_template_id("reset")):
            user = activity.goal.userrecommender.user
            user.delete()
            return "Deine Daten wurden gelöscht. Userdaten resettet."

        return True

    def get_or_create_announcements(self, user):
        """
        In this function announcements can be fed into the start recommender.
        :return:
        """
        goal = self.get_default_goal(user)
        evaluation_activity, created = models.Activity.objects.get_or_create(
            goal=goal,
            title="Evaluation-Workshop: Du bist herzlich eingeladen!",
            description="Aktuell sucht das Siddata-Team Teilnehmende für einen virtuellen Evaluations-Workshop. Dort lernst du am Beispiel von Siddata verschiedene Evaluationsperspektiven und Methoden kennen, probierst diese selber aus und hilfst, mit deinen Ideen Siddata weiterzuentwickeln und zu verbessern. Melde dich bei Interesse bitte bei Funda Seyfeli (seyfeli@his-he.de) für unsere Evaluationsreihe an, lerne andere Studierende auch von anderen Hochschulen kennen und erlebe einen dreistündigen, anregenden und abwechslungsreichen Online-Workshop im Januar 2022 (KW 02-04).",
            color_theme="green",
            type="todo",
            image="sid.png",
            feedback_size=0,
        )
        evaluation_activity.order = goal.get_max_order() + 1
        evaluation_activity.save()
