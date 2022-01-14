from backend import models
from recommenders.RM_BASE import RM_BASE

class RM_data_ethics(RM_BASE):
    """
    Recommender with data ethics content.
    """

    def __init__(self):
        # this magic line of code lets our recommender inherit all attributes and methods from the baseclass.
        super().__init__()
        # This name should be unique and appears in the Stud.IP GUI.
        self.NAME = "Data Ethics"
        # The description text summarizes the functionality. It is shown in teaser activity and tile view,
        self.DESCRIPTION = "Multimedia content about Data Ethics from a Philosophical Perspective."
        # This text is displayed in Teaser Activities
        self.TEASER_TEXT = "Auch im Studium sind Apps und soziale Medien allgegenwärtig. Dabei teilst du auch " \
                           "deine Daten. Diese Funktion vermittelt dir anschaulich philosophische Hintergründe " \
                           "zu datenethischen Fragestellungen und unterstützt dich, informiert und bewusst mit " \
                           "deinen Daten umzugehen. (English)"
        # If set to False, the recommender will not appear in the GUI or the DB
        self.ACTIVE = True
        # Image is shown in teaser activity
        self.IMAGE = "data_ethics.png"
        self.ORDER = 9
        # This string tells the user which data is required for this recommender
        self.DATA_INFO = "Diese Funktion kann ohne eigene Daten genutzt werden."
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

        resource = models.WebResource.objects.create(
            title="Data Ethics Kurs",
            description="Das Studienprojekt Data Ethics am Institut für Kognitionswissenschaften der Universität "
                        "Osnabrück hat einen multimedialen Kurs über die philosophische Perspektive auf datenethische "
                        "Fragestellungen erstellt. Hier kommst du direkt zum Kurs.",
            # URLs already provided in resource description
            source="https://studip.uni-osnabrueck.de/dispatch.php/course/enrolment/apply/35c276fa0be1da48698a6c7bd7e56681?again=yes&cancel_login=1&sso=shib",
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("data_ethics_course"),
            defaults={
                "title": self.get_name(),
                "description": "data ethics",
                "type": "resource",
                "resource": resource,
                "status": "template",
                "image": self.IMAGE,
                "order": 1,
            }
        )


    def initialize(self, user):
        """
        When a user logs in for the first time, initial activities are generated.
        :param user: SiddataUser object
        :return: True if successful
        """
        goal = self.activate_recommender_for_user_and_create_first_goal(user)

        models.Activity.create_activity_from_template(
            template_id=self.get_template_id("data_ethics_course"),
            goal=goal,
        )

        return True


    def process_activity(self, activity):
        """
        :param activity:  models.Activity instance modified by Stud.IP plugin
        :return: True if successful
        """
        return True
