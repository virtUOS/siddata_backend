"""
Implementation of Questionnaires for different purposes.
"""
from recommenders.RM_BASE import RM_BASE
from backend import models


class RM_evaluation(RM_BASE):
    """
        Generates different questionnaires.
    """

    def __init__(self):
        # this magic line of code lets our recommender inherit all attributes and methods from the baseclass.
        super().__init__()
        # This name should be unique and appears in the Stud.IP GUI.
        self.NAME = "Evaluation"
        # The description text summarizes the functionality. It is shown in teaser activity and tile view,
        self.DESCRIPTION = "Evaluation - hier kannst du Feedback zum Siddata-Prototypen geben."
        # This text is displayed in Teaser Activities
        self.TEASER_TEXT = "Danke, dass du dir die Zeit nimmst, den Siddata-Prototypen vorab zu testen. Bitte teile "\
                            "deine Eindrücke und Erfahrungen mit uns.<br>Möchtest du den <b>Fragebogen</b> beantworten?"
        # If set to False, the recommender will not appear in the GUI or the DB
        self.ACTIVE = True
        # Image is shown in teaser activity
        self.IMAGE = "evaluation.png"
        # determines arrangement in Frontend
        self.ORDER = 10
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
        self.questions_ux = ['Die Benutzung des Studienassistenten macht mir Spaß.',
                             'Die Texte und Inhalte des Assistenten sind für mich verständlich formuliert.',
                             'Ich empfinde die Gestaltung und Ausführung des Studienassistenten als langweilig.',
                             'Der Mehrwert des Studienassistenten durch die angebotenen Funktionen ist für mich ' +
                             'nicht ersichtlich.',
                             'Ich kann mir vorstellen den Studienassistenten regelmäßig zu nutzen.',
                             'Durch die Nutzung des Studienassistenten denke ich mehr über meine Studienziele nach.',
                             'Ich empfinde den Studienassistenten als einfach und intuitiv zu nutzen.',
                             'Das Design des Studienassistenten gefällt mir und spricht mich an.',
                             'Der Studienassistent bietet mir keine neuen und nützlichen Funktionen an.',
                             'Der Studienassistent gibt mir ein sicheres Gefühl im Umgang mit meinen Daten.',
                             'Der Studienassistent kann mir dabei helfen, schneller an notwendige Informationen zu ' +
                             'gelangen.',
                             'Die Handhabung und Navigation des Studienassistenten ist verwirrend. ',
                             'Ich werde den Studienassistenten weiterempfehlen.',
                             'Mit der Nutzung des Studienassistenten fühle ich mich wohl.',
                             ]

    def initialize_templates(self):
        """
        Creates and updates all templates of this recommender
        Is executed at server startup
        """
        super().initialize_templates()

        likert_scale = self.get_likert_scale(4)
        n_item = 1
        for element in self.questions_ux:
            q = models.Question.objects.get_or_create(
                question_text=element,
                answer_type="likert",
                selection_answers=likert_scale
            )[0]

            models.ActivityTemplate.objects.update_or_create(
                template_id=self.get_template_id("item_{}".format(n_item)),
                defaults={
                    "title": "Item {}".format(n_item),
                    "type": "question",
                    "status": "template",
                    "question": q,
                    "order": 1000000000 + n_item,
                }
            )
            n_item += 1


        q_uxo = models.Question.objects.get_or_create(
            question_text='Deine Meinung ist gefragt! Bitte  äußere Lob, Kritik oder auch Verbesserungsvorschläge '
                          'für den Studienassistenten.',
            answer_type="text"
        )[0]

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("item_{}".format(n_item)),
            defaults={
                "title": 'Item {}'.format(n_item),
                "description": "",
                "type": "question",
                "status": "template",
                "question": q_uxo,
                "order": 1000000000 + n_item,
            }
        )

    ### Start Survey activity

        instruction_text_3 = ' Im Zuge einer wissenschaftlichen Arbeit wird gerade eine Begleitumfrage zu SIDDATA durchgeführt.' \
                             ' Dort wollen wir untersuchen, wie deine Wahrnehmung der Nutzung von SIDDATA ist.' \
                             ' Um an der Studie teilzunehmen klicke bitte hier: ' \
                             '<a href="https://www.survey.uni-osnabrueck.de/limesurvey/index.php/286649?lang=de">Zur Studie</a>'

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("instructions_3"),
            defaults={
                "title": "Begleitforschung",
                "type": "todo",
                "description": instruction_text_3,
                "status": "template",
                "image": "sid.png",
                "feedback_size": 0,
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
        goal.type = "form"
        goal.save()

        order = goal.userrecommender.get_max_order()

        order += 1

        info_goal = models.Goal.objects.get_or_create(
            title='Zusatzumfrage',
            userrecommender=goal.userrecommender,
            order=order,
        )[0]

        survey = models.Activity.create_activity_from_template(
            template_id=self.get_template_id('instructions_3'),
            goal=info_goal,
            order=1,
        )
        survey.color_theme = 'green'
        survey.save()

        likert_scale = self.get_likert_scale(4)
        n_item = 1
        for element in self.questions_ux:
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("item_{}".format(n_item)),
                goal=goal,
            )
            n_item += 1

        models.Activity.create_activity_from_template(
            template_id=self.get_template_id("item_{}".format(n_item)),
            goal=goal,
        )

        return True


    def get_likert_scale(self,items):

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
            return  likert_scale_answers_7

        else:
            return "no scale for {}".format(items)

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


    def process_activity(self, activity):
        """
        :param activity:  activity
        :return: True if successful
        """
        if activity.has_template(self.get_template_id('instructions_3')):
            return True

        result_ux = activity.goal.get_property(key="Result_UX")
        if result_ux == None:
            result_ux = {}

        # transfer answers into numbers
        likert_scale_4_dic = self.get_scale_value(4)
        # negative polarized items
        negative_item = [4, 6, 10]
        m, n = activity.title.split()
        n_item = int(n)

        if n_item in negative_item:
            n_item_val = 5 - likert_scale_4_dic[activity.answers[0]]
        else:
            if n_item == 15:
                n_item_val = activity.answers[0]
            else:
                n_item_val = likert_scale_4_dic[activity.answers[0]]


        result_ux[activity.title] = n_item_val
        activity.goal.set_property(key="Result_UX", value=result_ux)

        return True
