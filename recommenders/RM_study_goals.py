from backend import models
from recommenders.RM_BASE import RM_BASE


class RM_study_goals(RM_BASE):
    """
        Allows to define personal study goals.
    """

    def __init__(self):
        # this magic line of code lets our recommender inherit all attributes and methods from the baseclass.
        super().__init__()
        # This name should be unique and appears in the Stud.IP GUI.
        self.NAME = "Meine Studienziele"
        # The description text summarizes the functionality. It is shown in teaser activity and tile view,
        self.DESCRIPTION = "Hier kannst du eigene Studienziele definieren und diese in einer Baumstruktur deiner Wahl " \
                           "betrachten."
        # This text is displayed in Teaser Activities
        self.TEASER_TEXT = "Hast du dich schon einmal gefragt, wozu du studierst und was du bis zu deinem Abschluss alles " \
                           "schaffen möchtest? Hier kannst du Ziele visualisieren und planen, wie du sie erreichst."

        # If set to False, the recommender will not appear in the GUI or the DB
        self.ACTIVE = True
        # Image is shown in teaser activity
        self.IMAGE = "goals.png"
        # determines arrangement in Frontend
        self.ORDER = 5
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

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("study_goals"),
            defaults={
                "title": "Meine Studienziele",
                "type": "iframe",
                "resource": None,
                "status": "template",
                "image": None,
                "feedback_size": 2,
                "order": 1000000001,
            }
        )

    def initialize(self, user):
        """
        When a user logs in for the first time, initial activities are generated.
        :param user: SidataUser object
        :return: True if successful
        """
        goal = self.activate_recommender_for_user_and_create_first_goal(user)

        resource = models.WebResource.objects.get_or_create(
            title="Meine Studienziele",
            description=None,
            source="https://locke.siddata.de/study/siddata_study/{}".format(user.user_origin_id),
        )[0]

        models.Activity.create_activity_from_template(
            template_id=self.get_template_id("study_goals"),
            goal=goal,
            resource=resource,
        )

    def process_activity(self, activity):
        """
        :param activity:  activity
        :return: True if successful
        """
        # This is the activity that shows an iframe
        if activity.has_template(self.get_template_id("study_goals")):
            # it should always stay active, even if an interest has been entered
            activity.status = 'active'
            activity.save()
