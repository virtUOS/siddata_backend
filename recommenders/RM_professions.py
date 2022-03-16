import logging
import re

from backend import models
from recommenders.RM_BASE import RM_BASE
from bert_app.recommender_backbone import ProfessionsRecommenderBackbone

COURSE_MAX = 15 # maximum number of resources to be generated as recommendations

RESOURCE_TYPES = {
    'local_course': 'Stud.IP-Veranstaltungen meiner Universität',
    'external_course': 'Stud.IP-Veranstaltungen anderer Universitäten',
    'Event': 'Einzelnes Event in einer Veranstaltung',
    'MOOC': 'Massive Open Online Courses (MOOCs)',
    'OER': 'Open Educational Resources (OERs)',
}


class RM_professions(RM_BASE):
    """ This recommender generates matching educational resources based on an input string in natural langauge.
    It also provides functions to reflect upon one's own professional interests.
    """

    def __init__(self, functional_only = False):
        # this magic line of code lets our recommender inherit all attributes and methods from the baseclass.
        super().__init__()
        # This name should be unique and appears in the Stud.IP GUI.
        self.NAME = "Fachliche Interessen"
        # The description text summarizes the functionality. It is shown in teaser activity and tile view,
        self.DESCRIPTION = "Veranstaltungen und Angebote finden, die zu dir passen."
        # This text is displayed in Teaser Activities
        self.TEASER_TEXT = "Deinen Regelstudienplan kennst du. Darüber hinaus gibt es eine Menge an interessanten " \
                           "Veranstaltungen und Angeboten, von denen du vielleicht noch gar nichts weißt. Siddata kann " \
                           "diese für dich finden, wenn du etwas über deine Interessen - auch über dein Studium hinaus" \
                           " - eingibst."
        # If set to False, the recommender will not appear in the GUI or the DB
        self.ACTIVE = True
        # Image is shown in teaser activity
        self.IMAGE = "brain.png"
        # determines arrangement in Frontend
        self.ORDER = 3
        # This string tells the user which data is required for this recommender
        self.DATA_INFO = "Diese Funktion speichert deine von dir formulierten Interessen. Zudem speichert es, welche dir vorgeschlagenen Bildungsressourcen du aufrufst."
        # E-mail regex check
        self.mail_regex = re.compile("[^@]+@[^@]+\.[^@]+")
        # Reference to the database object, can be used as value vor recommender attribute in goals.
        try:
            if not functional_only:
                self.recommender = models.Recommender.objects.get_or_create(
                    name=self.get_name(),
                    description=self.DESCRIPTION,
                    classname=self.__class__.__name__,
                    image=self.IMAGE,
                    order=self.ORDER,
                    data_info=self.DATA_INFO,
                )[0]
            else:
                self.recommender = None
        except ChildProcessError:
            logging.info("instantiation of Recommender Object in RM_professions failed.")
        try:
            self.backbone = ProfessionsRecommenderBackbone(max_courses = COURSE_MAX)
        except (ModuleNotFoundError, AttributeError):
            logging.info("Error when loading RM_professions recommender backbone! "
                         "Bert App may not be loaded yet. Ignore this error when it occurs immediately at start")
            self.initialize_templates()

    def initialize_templates(self):
        """
        Creates and updates all templates of this recommender
        Is executed at server startup
        """
        super().initialize_templates()

        ### Generate and filter professional interests ###

        # This Question will be modified during the chat process.
        input_text_question = models.Question.objects.get_or_create(
            question_text='Hier kannst du eines deiner fachlichen Interessen eingeben (z.B. „Chemie“)',
            answer_type="text",
        )[0]

        input_type_question = models.Question.objects.get_or_create(
            question_text='Diese Arten an Bildungsressourcen interessieren mich:',
            answer_type='checkbox',
            selection_answers=list(RESOURCE_TYPES.values())
        )[0]

        # This activity is the container for the Question and will be continually modified.
        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("new_input_text"),
            defaults={
                "title": 'Neues Interesse',
                "type": "question",
                "status": "template",
                "image": self.IMAGE,
                "feedback_size": 0,
                'form': 1,
                "question": input_text_question,
                "order": 0,
            }
        )

        #Filter function
        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("resource_type_filter"),
            defaults={
                'title': 'Neues Interesse',
                'type':'question',
                'status':'template',
                'order': 1,
                'image': self.IMAGE,
                'form': 1,
                'question': input_type_question,
                'feedback_size': 0
            }
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("my_topic"),
            defaults={
                "type": "todo",
                "title": "Mein Thema",
                "status": "template",
                "feedback_size": 0,
                'form': 2,
            }
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id('my_topic_filter'),
            defaults={
                'type': 'question',
                'title': 'Mein Thema',
                'status': 'template',
                'feedback_size': 0,
                'form': 2,
                'question': input_type_question
            }
        )

        # e-mail request, modification and handling

        e_mail_request_text = 'Möchtest du E-mail Benachrichtigungen erhalten,' \
                              ' wenn ich neue Resourcen zu deinem Interesse gefunden habe? <br> ' \
                              'WARNUNG: Wenn du deine E-mail Adresse angibst,' \
                              ' bist du für Siddata nicht mehr annonym!<br>' \
                              'Du kannst deine E-mail Adresse jederzeit wieder löschen.'
        e_mail_request_question = models.Question.objects.get_or_create(
            question_text=e_mail_request_text,
            answer_type='text',
            selection_answers=list(RESOURCE_TYPES.values())
        )[0]

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("request_e_mail"),
            defaults={
                'title': 'Benachrichtigungen',
                'type': 'question',
                'status': 'template',
                'question': e_mail_request_question,
                'feedback_size': 0
            }
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("e_mail_saved"),
            defaults={
                'title': 'E-mail gespeichert!',
                'type': 'todo',
                'status': 'template',
                'feedback_size':0
            }
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("e_mail_wrong_format"),
            defaults={
                'title': 'Bitte gib eine korrekte E-mail Adresse ein.',
                'description': 'Leider ist die von dir eingegebene E-mail Adresse ungültig. '
                               'Bitte gib eine gültige E-mail Adresse (z.B. spock@mailserver.de) ein.',
                'type': 'todo',
                'status': 'template',
                'feedback_size':0,
            }
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("university_course_recommendation"),
            defaults={
                "type": "course",
                "status": "template",
                "feedback_size": 0,
            }
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("mooc_recommendation"),
            defaults={
                "type":"resource",
                "status":"template",
                "feedback_size":0
            }
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("resource_recommendation"),
            defaults={
                "type": "resource",
                "status": "template",
                "feedback_size": 0,
            }
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("no_recommendations"),
            defaults={
                "description": 'Zur Zeit gibt es leider keine Bildungsressourcen,'
                               ' die deinem Interesse entsprechen.'
                               ' Siddata wird dich an einem späteren Zeitpunkt noch einmal informieren,'
                               ' sobald neue Ressourcen für dich gefunden wurden.',
                "type": 'todo',
                "status": 'template',
            }
        )

        ### Questionaire for helping students to reflect upon their interests ###
        #initial question
        general_reflection_question = models.Question.objects.get_or_create(
            question_text='Möchtest du Hilfestellungen, um deine fachlichen Interessen möglichst präzise formulieren zu '
                          'können?',
            answer_type='checkbox',
            selection_answers=['Ich möchte den Unterschied zwischen fachlichen Interessen und nicht-fachlichen Interessen verstehen',
                               'Ich möchte die Formulierung von fachlichen Interessen ausprobieren']
        )[0]
        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("need_general_help"),
            defaults={
                "title": 'Hilfe bei der Formulierung meiner Interessen',
                "description": 'Hilfestellung',
                "type": 'question',
                "status": 'template',
                "feedback_size": 0,
                "image": None,
                "question": general_reflection_question
            }
        )

        # Information on why professional interests are usefull to know
        rm_professions_info_text = "<strong>Was ist der Unterschied zwischen meinem Studienfach und meinen" \
                                   " fachlichen Interessen? </strong> <br>" \
                                   "Deine fachlichen Interessen sollten im Idealfall der Grund sein, warum du das Fach," \
                                   " was du studierst, gewählt hast. Persönliche fachliche Interessen machen in der" \
                                   " Regel aber nur ein Teilgebiet deines Studienfaches aus und gehen im Idealfall" \
                                   " darüber hinaus. Siddata hilft dir Veranstaltungen zu finden, die stärker" \
                                   "deinen persönlichen fachlichen Interessen entsprechen. <br> <br>" \
                                   " <strong> Warum ist es wichtig, sich über seine fachlichen Interessen im Klaren " \
                                   "zu sein? </strong>" \
                                   "In vielen Kontexten, z.B. in Bewerbungsgesprächen, ist es hilfreich, wenn du " \
                                   "deine eigenen Interessen klar kommunizieren kannst. Auch bei der Wahl deines " \
                                   "Abschlussarbeitsthemas, eines Nebenfachs, einer Vertiefungsrichtung oder auch " \
                                   "bei der Suche nach geeigneten Praktika und Auslandsaufenthalten, kann es dir " \
                                   "helfen, deinen fachlichen Interessen bewusst zu sein. "

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id('help_info_text'),
            defaults={
                "title": 'Hilfe bei der Formulierung meiner Interessen',
                "description": rm_professions_info_text,
                "type": 'todo',
                "status": 'template',
                "feedback_size": 0,
                "image": None,
            }
        )

        # training activity to formulate professional interests
        rm_professions_train_text = "Wenn du Probleme hast, deine fachlichen Interessen zu formulieren," \
                                    " hilft dir eine kleine Übung. Hier kannst du dir folgende Fragen beantworten:<br>" \
                                    "<ul>" \
                                    " <li>Wenn du an die letzten Klausuren denkst," \
                                    " bei welchen Themen fiel dir das Lernen besonders leicht?</li>" \
                                    " <li>Wenn du an deine letzten Veranstaltungen denkst," \
                                    " welche Themen haben Dich besonders interessiert?</li>" \
                                    " <li>Welches Buch hast du Dir ausgeliehen ohne dass" \
                                    " es auf einer Leseliste stand?</li>" \
                                    " <li>Was hast du deinen" \
                                    " Freunden von Deinem Studium inhaltlich erzählt?</li>"  \
                                    " <li>Über welches Thema hast du noch nachgedacht," \
                                    " obwohl du schon längst etwas anderes gemacht hast?</li>" \
                                    "</ul>"

        train_text_question = models.Question.objects.get_or_create(
            question_text=rm_professions_train_text,
            answer_type="text",
        )[0]

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id('help_train_formulate'),
            defaults={
                "title": 'Übung zur Eingabe fachlicher Interessen',
                "description": '',
                "type": "question",
                "status": "template",
                "feedback_size": 0,
                "question": train_text_question
            }
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("my_train_topic"),
            defaults={
                "type": "todo",
                "title": "Mein Übungsthema",
                "status": "template",
                "feedback_size": 0,
            }
        )


    def build_resource_description(self, resource, type):
        """
        Creates resource description depending on resource type
        """
        if type == 'mooc':
            images = [re.split('image_', key)[1] for key in resource.creator[0].keys() if key.startswith('image_')]
            if len(images) == 0:
                image = None
            else:
                max_n = 0
                max_res = 0
                for n, element in enumerate(images):
                    split_element = [int(edge) for edge in images[0].split('x')]
                    resolution = split_element[0] * split_element[1]
                    if resolution > max_res:
                        max_n = n
                max_key = 'image_'+images[max_n]
                image = resource.creator[0][max_key]

            title = resource.title
            description = resource.description
            autor = resource.creator[0]['display_name']
            job = resource.creator[0]['job_title']

            activity_description = 'Massive Open Online Kurs Empfehlung: <br><ul>'
            if title:
                activity_description += '<li><b>Titel: </b>'+title+'</li>'
            if description:
                activity_description += '<li><b>Beschreibung: </b>'+description+'</li>'
            if autor:
                activity_description += '<li><b>Autor*in: </b>'+autor+'</li>'
            if job:
                activity_description += '<li><b>Position: </b>'+job+'</li>'
            activity_description += '</ul>'


        elif type == 'oer':
            image = None
            title = resource.title
            description = resource.description
            category = ''
            for element in resource.coverage:
                category += element + ' '
            category = category[:-1]
            subject = ''
            for element in resource.subject:
                subject += element + ' '
            subject = subject[:-1]
            lang = resource.language
            format = resource.format.capitalize()

            activity_description = 'Open Educational Resource Empfehlung: <br><ul>'
            if title:
                activity_description += '<li><b>Titel: </b>'+title+'</li>'
            if description:
                activity_description += '<li><b>Beschreibung: </b>'+description+'</li>'
            if format:
                activity_description += '<li><b>Format: </b>'+format+'</li>'
            if category:
                activity_description += '<li><b>Kategorie: </b>'+category+'</li>'
            if subject:
                activity_description += '<li><b>Thema: </b>'+subject+'</li>'
            if lang:
                activity_description += '<li><b>Sprache: </b>'+lang+'</li>'
            activity_description += '</ul>'

        else:
            activity_description = ''
            image = None

        return activity_description, image

    def initialize(self, user):
        """
        When a user logs in for the first time, initial activities are generated.
        :param user: SiddataUser object
        :return: True if successful
        """
        try:
            self.backbone
        except AttributeError:
            logging.error('RM_professions was initialized without a running SidBERT model from apps.BertAppConfig. '
                          'This occurs when model files are not present in their corresponding directory. '
                          'Please deactivate RM_professions or download model files.')

        ### Initalization for a searching for educational resources
        ur, _ = models.SiddataUserRecommender.objects.get_or_create(
            recommender=self.recommender,
            user=user,
        )
        search_goal = self.activate_recommender_for_user_and_create_first_goal(user)
        order = self.get_next_goal_order(ur)
        search_goal.order = order
        search_goal.title = 'interest_associated_goal'
        search_goal.visible = False
        search_goal.save()
        filter_pq, _ = models.GoalProperty.objects.get_or_create(
            goal=search_goal,
            key='type',
            value='questionnaire'
        )
        filter_pq.save()
        init_filter = models.Activity.create_activity_from_template(
            template_id=self.get_template_id("new_input_text"),
            goal=search_goal,
            status='immortal'
        )
        init_filter.answers = ['Hier kann eine Antwort eingetragen werden (Zum Beispiel: Chemie)']
        init_filter.save()
        models.Activity.create_activity_from_template(
            template_id=self.get_template_id('resource_type_filter'),
            goal=search_goal,
            status='immortal'
        )


        ### Initalization for reflection questions

        models.Activity.create_activity_from_template(
            template_id=self.get_template_id('need_general_help'),
            goal=search_goal,
            order = self.get_next_activity_order(search_goal)
        )

        return True

    def process_activity(self, activity):
        """
        Umbrella function that is called every time the recommender is queried via API.
        based on the type of incoming activity object, the function calls seperate sub-functions that handel
        different functionalities.
        """
        standard_answer = 'Hier kann eine Antwort eingetragen werden (Zum Beispiel: Chemie)'
        if activity.has_template(self.get_template_id("new_input_text")): # executes when new prof. interest is entered
            if activity.answers[0] == standard_answer or activity.answers[0] == '' or activity.answers[0].isspace():
                # if no interest is entered or the standard query is entered, no resources are generated
                return True
            else:
                activity.goal.set_property(key='input_text',value=activity.answers[0]) # store interest in goal property
            if activity.goal.get_property(key='filters') is not None:
                self.handle_type_filter(activity, re_filter=False, call_from_input_text=True)
            activity.answers = [standard_answer]
            activity.save()

        elif activity.has_template(self.get_template_id('resource_type_filter')):
            # activity to generate new recommendations, slaves input_text activities. Always stays active.
            get_input_text = activity.goal.get_property(key='input_text')
            if get_input_text is not None:
                # If input text was None either the User tried to delete the interest activity
                # or the plugin did not send an input_text yet and will do so with the next
                # activity sent to the recommender.
                if get_input_text == standard_answer or get_input_text == '':
                    # This case occurs if the user tries to delete an empty activity
                    return True
                else:
                    self.handle_type_filter(activity)
                    activity.goal.set_property(key='input_text', value=None) # reset value to receive new request
            elif activity.answers == []:
                return True
            else:
                activity.goal.set_property(key='filters',value=activity.answers) # store filter setting for next query
            activity.save()
        elif activity.has_template(self.get_template_id('my_topic_filter')):
            # activity to change filters for interests already submitted.
            new_goal = self.handle_type_filter(activity, re_filter=True)
            old_goal = activity.goal
            activity.goal = new_goal
            old_goal.delete()


        elif activity.has_template(self.get_template_id("request_e_mail")):
            self.handle_e_mail_request(activity)
            # handles e-mail notifications

        elif activity.has_template(self.get_template_id("e_mail_saved")):
            self.generate_e_mail_request(activity)
            activity.delete()

        elif activity.has_template(self.get_template_id('need_general_help')) or \
                activity.has_template(self.get_template_id('help_train_formulate')):
            # umbrella function for reflection questions.
            self.handle_reflexion_questions(activity)
            activity.answers = []
            activity.save()

    ### Filter and new interests preprocessing

    def handle_type_filter(self, activity, re_filter=False, call_from_input_text = False):
        if re_filter:
            input_text_activity = models.Activity.objects.get(template_ref_id=self.get_template_id('my_topic'),
                                                          goal=activity.goal)
            formulated_goal = input_text_activity.answers[0]
            input_text_activity.answers = ['Hier kann eine Antwort eingetragen werden (Zum Beispiel: Chemie)']
            input_text_activity.save()
            get_e_mail = models.Activity.objects.filter(goal=activity.goal, template_ref_id=self.get_template_id('e_mail_saved')).exclude(status='done')
            if get_e_mail:
                get_e_mail = get_e_mail[0]

        else:
            formulated_goal = activity.goal.get_property(key='input_text')
            if call_from_input_text:
                activity.answers = activity.goal.get_property(key='filters')
            get_e_mail = None

        new_goal_order = self.get_next_goal_order(userrecommender=activity.goal.userrecommender)
        new_goal = models.Goal.objects.create(
            title=formulated_goal,
            userrecommender=activity.goal.userrecommender,
            order=new_goal_order
        )
        new_goal.save()
        # generate a first activity inside of the goal that shows the interest string
        my_topic_activity = models.Activity.create_activity_from_template(
            template_id=self.get_template_id("my_topic"),
            goal=new_goal,
            description='Dein Interesse ' + str(formulated_goal) + ' wurde gespeichert. <br>'
                                                                   'Du kannst die Filtereinstellungen für dieses'
                                                                   ' Interesse jederzeit ändern.',
            answers=[formulated_goal],
            order=0,
        )

        my_topic_filter_activity = models.Activity.create_activity_from_template(
            template_id=self.get_template_id("my_topic_filter"),
            goal=new_goal,
            description='Dein Interesse ' + str(formulated_goal) + ' wurde gespeichert. <br>'
                                                                   'Du kannst die Filtereinstellungen für dieses'
                                                                   ' Interesse jederzeit ändern.',
            answers=activity.answers,
            order=1
        )
        my_topic_activity.save()
        my_topic_filter_activity.save()
        if get_e_mail:
            get_e_mail.order = self.get_next_activity_order(new_goal)
            get_e_mail.goal = new_goal
            get_e_mail.save()
        else:
            self.generate_e_mail_request(my_topic_activity)
        self.generate_new_recommendations(activity=my_topic_activity, filtered_tags=self.get_filter_tags(
            frontend_feedback=activity.answers))
        activity.goal.set_property(key='filters', value=None)
        activity.goal.set_property(key='input_text', value=None)
        return new_goal

    ### E-mail notification

    def handle_e_mail_request(self, activity):
        if self.mail_regex.match(activity.answers[0]):

            saved_e_mail = models.Activity.create_activity_from_template(
                template_id=self.get_template_id('e_mail_saved'),
                goal=activity.goal,
                order = self.get_next_activity_order(activity.goal)
            )
            saved_e_mail.description = 'Deine E-mail Adresse ' + str(
                activity.answers[0]) + ' wurde gespeichert. Klicke auf \"OK!\" um deine E-mail zu löschen.'
            saved_e_mail.answers = activity.answers
            saved_e_mail.save()
            activity.delete()
            wrong_format_activities = models.Activity.objects.filter(goal=activity.goal, template_ref_id=self.get_template_id("e_mail_wrong_format"))
            for item in wrong_format_activities:
                item.delete()
        else:
            # if e-mail format is not correct. A correct address format is 'something@something_else.xyz'
            wrong_format_activity = models.Activity.create_activity_from_template(
                template_id=self.get_template_id("e_mail_wrong_format"),
                goal=activity.goal,
                order=self.get_next_activity_order(activity.goal)
            )
            wrong_format_activity.color_theme = 'red'
            wrong_format_activity.save()
            self.generate_e_mail_request(activity=activity)
            activity.delete()
        return True

    def generate_e_mail_request(self, activity):
        models.ActivityTemplate.create_activity_from_template(
            template_id=self.get_template_id("request_e_mail"),
            goal=activity.goal,
            order=self.get_next_activity_order(activity.goal)
        )
        return True

    ### Reflection question handeling and tracking

    def handle_reflexion_questions(self, activity):
        if activity.has_template(self.get_template_id('need_general_help')):
            if 'Ich möchte den Unterschied zwischen fachlichen Interessen und nicht-fachlichen Interessen verstehen' in activity.answers:
                if not models.Activity.objects.filter(goal=activity.goal,
                                                      template_ref=self.get_template_id('help_info_text'),
                                                      ).exists():
                    models.Activity.create_activity_from_template(
                        template_id=self.get_template_id('help_info_text'),
                        goal=activity.goal,
                        order = self.get_next_activity_order(activity.goal)
                    )
            if 'Ich möchte die Formulierung von fachlichen Interessen ausprobieren' in activity.answers:
                if not models.Activity.objects.filter(goal=activity.goal,
                                                      template_ref=self.get_template_id('help_train_formulate'),
                                                      ).exists():
                    models.Activity.create_activity_from_template(
                        template_id=self.get_template_id('help_train_formulate'),
                        goal=activity.goal,
                        order=self.get_next_activity_order(activity.goal)
                        )

        elif activity.has_template(self.get_template_id('help_train_formulate')):
            activity.status = 'active'
            activity.save()
            models.Activity.create_activity_from_template(
                template_id=self.get_template_id("my_train_topic"),
                goal=activity.goal,
                description=activity.answers[0],
                answers=activity.answers,
                order= self.get_next_activity_order(activity.goal)
            )

    ### SidBERT interface and filter processing for resource recommendations.

    def get_filter_tags(self, frontend_feedback):
        filter_tags = []
        for key, value in RESOURCE_TYPES.items():
            if value in frontend_feedback:
                filter_tags.append(key)
        return filter_tags

    def generate_new_recommendations(self, activity, filtered_tags=None):
        """
        This function interfaces with the recommender backbone to generate and retreive new recommendations for courses
        :param new_check: Set true if the scheduled tasks function checks if new courses have been added to the database
        :param filtered_tags: List of tags to be used for filtering resources.
        that could potentially be relevant for this activity.
        :param activity: activity type object
        """

        user = activity.goal.userrecommender.user
        interest = activity.answers[0]
        if filtered_tags is None:
            filtered_tags = []
        sidbert_resources = self.backbone.fetch_resources_sidbert(interest, user.origin, filtered_tags)

        if len(sidbert_resources) == 0:
            self.generate_empty_feedback(activity=activity)
        else:
            for i, resource in enumerate(sidbert_resources):
                description = resource.description
                img = None
                title = 'Neue Empfehlung'
                if 'SIP' in resource.type:
                    description = resource.description
                    if resource.origin != user.origin:
                        title = f'Kursempfehlung an einer anderen Universität: {resource.title}'
                    else:
                        title = f'Kursempfehlung: {resource.title}'
                elif 'mooc' in resource.type:
                    description, img = self.build_resource_description(resource, type='mooc')
                    title = f'MOOC-Empfehlung: {resource.title}'
                elif 'oer' in resource.type:
                    description, img = self.build_resource_description(resource, type='oer')
                    title = f'OER-Empfehlung: {resource.title}'
                elif 'event' in resource.type:
                    if resource.title:
                        title = f'Einzeltermin-Empfehlung: {resource.title}'
                    else:
                        title = 'Einzeltermin-Empfehlung'
                    if resource.description:
                        description = resource.description
                    else:
                        description = 'Dieser Einzeltermin gehört zu einem Kurs, der zu deinen Interessen passt.'
                new_resource_order = self.get_next_activity_order(activity.goal)
                new_resource_recommendation = models.Activity.objects.create(
                    description=description,
                    type='resource',
                    resource=resource,
                    status='active',
                    goal=activity.goal,
                    title=title,
                    order=new_resource_order,
                    image=img
                )
                new_resource_recommendation.save()
        return True


    def generate_empty_feedback(self, activity):
        """
        This function generates a notification activity informing the user about resources in the requested knowledge
        domain not being available at the moment.
        """
        models.Activity.create_activity_from_template(
            template_id=self.get_template_id("no_recommendations"),
            title='Momentan sind keine Empfehlungen verfügbar für ' + activity.answers[0],
            answers=activity.answers,  # store the requested topic here for future reference.
            goal=activity.goal,
            order = self.get_next_activity_order(activity.goal)
        )
        return True



    ### Cron functions
    def check_for_new(self, activity):
        """
        This activity checks if there are new resources that match to requests that previously yielded no results.
        """
        successfully_generated = False
        if self.generate_new_recommendations(activity=activity):
            successfully_generated = True
            goal = activity.goal
            # Sends mail if users provided their address for this interest.
            if models.Activity.objects.filter(goal=goal, title__startswith='E-mail gespeichert!')\
                    .exclude(status='done').exists():
                # if the user has left an e-mail address, they are notified about new resources being available
                requested_interest = activity.answers[0]

                mail_text = 'Siddata hat neue Bildungsressourcen für dein Interesse '+str(requested_interest)+\
                            " gefunden!\n" \
                            " Besuche das Recommender Modul 'Fachliche Interessen' im Stud.IP Siddata" \
                            " Studierendenassistenten um diese Ressourcen anzusehen.\n" \
                            " Herzliche Grüße" \
                            " \n dein Siddata Studienassistent"

                mail_activity = models.Activity.objects.filter(goal=goal, title__startswith='E-mail gespeichert!')\
                    .exclude(status='done')
                mail_address = mail_activity.answers[0]
                self.send_push_email(address=mail_address,
                                     title='Neue Materialien für dein Interesse '+str(requested_interest),
                                     content=mail_text)
        return successfully_generated


    def execute_cron_functions(self):
        empty_professions_activities = models.Activity.objects.filter(type='todo',
                                                               title__startswith=
                                                               'Momentan sind keine Empfehlungen verfügbar')\
                                                                      .exclude(status='done')
        for activity in empty_professions_activities:
            self.check_for_new(activity=activity)

        goal_associated_interests = models.Goal.objects.filter(userrecommender__recommender=self.recommender)\
            .exclude(title='interest_associated_goal')
        for goal in goal_associated_interests:
            root_activity = models.Activity.objects.filter(goal=goal, template_ref_id=self.get_template_id('my_topic')).exclude(status='done')
            if not root_activity:
                root_activity = models.Activity.objects.filter(goal=goal,type='todo',title__startswith='Momentan sind keine Empfehlungen verfügbar').exclude(status='done')
            self.check_for_new(activity=root_activity)
