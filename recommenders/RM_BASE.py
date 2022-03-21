from backend import models
from django.core.mail import send_mail


class RM_BASE():
    """
    Recommender base class.
    Methods and attributes can be inherited from here.
    """

    def __init__(self):
        self.NAME = "RM_BASE"
        self.ACTIVE = False
        self.DESCRIPTION = "This text describes a recommender. Max 180 chars."
        self.TEASER_TEXT = "This text describes a recommender. It is displayed in teaser activities" \
                           "and also in the tiles view."
        self.IMAGE = "logo.png"
        self.ORDER = "Order has to be a unique integer not used by other recommenders."
        self.recommender = None
        self.DATA_INFO = "Die bei der Nutzung entstehenden Daten werden auf dem  Siddata Server gespeichert."

    def get_name(self):
        return self.NAME

    def activated(self):
        return self.ACTIVE

    def get_class_name(self):
        return self.__class__.__name__

    def get_template_id(self, template_name, origin=None):
        """
        Returns a template id which is built from recommender name, template_name and origin name (if passed).
        In a recommender each template must have a unique template name or a unique pair of template name and origin.
        Otherwise, a template couldn't clearly be identified in the activity_create_from_template method.
        """
        template_id = self.get_class_name() + "_AC_" + template_name
        if origin:
            template_id += "_OG_" + origin.api_endpoint
        return template_id

    def initialize_templates(self):
        """
        Initializes and updates teaser templates.
        """
        teaser_question = models.Question.objects.get_or_create(
            question_text="{} <br><br><p>Möchtest du die Funktion <strong>{}</strong> nutzen?</p>".format(
                self.TEASER_TEXT,
                self.get_name()),
            answer_type="selection",
            selection_answers=["Ja", "Nein"]
        )[0]

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_class_name() + "_AC_teaser",
            defaults={
                "title": self.get_name(),
                "description": "Teaser_{}".format(self.get_name()),
                "type": "question",
                "question": teaser_question,
                "status": "template",
                "image": self.IMAGE,
                "feedback_size": 0,
                # Tutorial starts from 1000001000
                # Teasers follow  from 1000002000
                "order": (1000002001 + self.ORDER),
            }
        )

    def create_teaser_activity(self, goal):
        """
        Creates an activity instance, related to the given goal (indirect user association),
        that teases the user about the recommender.
        :param goal: Goal instance.
        :return: True
        """
        models.Activity.create_activity_from_template(
            template_id=self.get_class_name() + "_AC_teaser",
            goal=goal,
        )
        return True

    def get_teaser_activity(self, goal):
        """
        Get the teaser activity for the given goal.
        :param goal: Goal instance.
        :return: Activity instance.
        """
        return models.Activity.objects.get(
            template_ref_id=self.get_class_name() + "_AC_teaser",
            goal=goal,
        )

    def activate_recommender_for_user_and_create_first_goal(self, user):
        """
        Sets the recommender active for the given user and creates a first goal for the user.
        :param user: SiddataUser instance.
        :return: Created Goal instance.
        """
        # Relate recommender to user
        userrecommender = models.SiddataUserRecommender.objects.get_or_create(
            recommender=self.recommender,
            user=user,
        )[0]
        userrecommender.enabled=True
        userrecommender.save()

        # Create default goal
        goal, created = models.Goal.objects.get_or_create(
            title=self.get_name(),
            userrecommender=userrecommender,
            userrecommender__user=user,
        )
        goal.save()

        return goal

    def get_next_goal_order(self, userrecommender):
        """
        Calculates next goal order number for dynamically creating goals within the recommender.
        :param userrecommender: UserRecommender instance.
        :return: Next goal order number.
        """
        new_goal_order = models.Goal.objects.filter(userrecommender=userrecommender).order_by('-order')[0].order
        if new_goal_order is None:
            new_goal_order = 1
        else:
            new_goal_order += 1
        return new_goal_order

    def get_next_activity_order(self, goal):
        """
        Calculates next activity order number for dynamically creating activities within a goal.
        :param goal: Goal instance.
        :return: Next activity order number.
        """
        new_activity_order = models.Activity.objects.filter(goal=goal).order_by('-order')[0].order
        if new_activity_order is None:
            new_activity_order = 1
        else:
            new_activity_order += 1
        return new_activity_order

    def execute_cron_functions(self):
        """
        This function provides an access point for interval-based executions triggered by a cron job function.
        """
        pass

    def send_push_email(self, address, title, content):
        """
        Send mails to defined recipients. This function basically encapsulates django.core.mail.send_mail.
        :param address: mail address of the recipient
        :param title: subject of the mail
        :param content: message content
        :return: return of send_mail
        """
        return send_mail(f"{self.get_name()}: {title}", content, None, [address])

    def refresh(self):
        """
        Allows recommenders to adapt to changes caused in other contexts.
        Is called on all recommenders when changes occur.
        :return: True
        """
        return True
