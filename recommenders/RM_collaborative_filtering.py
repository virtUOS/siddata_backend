from recommenders.RM_BASE import RM_BASE
from backend import models
import re
from collaborative_filtering_app import collaborative_filtering_interlink

import logging

class RM_collaborative_filtering(RM_BASE):
    def __init__(self):
        super().__init__()
        self.NAME = 'Kollaboratives Filtern'
        self.DESCRIPTION = 'Finde Veranstaltungen, die Nutzende, die ähnlich zu dir sind, belegen haben.'
        self.TEASER_TEXT = 'Im Studienalltag tauschst du dich bestimmt häufig mit deinen Mitstudierenden über Kurse aus, die du belegen könntest. ' \
                           'Hier haben wir einige Kurse für dich gesammelt, die Studierende, die ähnlich zu dir sind auch belegen.'
        self.ACTIVE = False
        self.IMAGE = "brain.png"
        self.ORDER = 8
        self.DATA_INFO = "Diese Funktion greift auf deine in der Vergangenheit belegten Kurse zu."
        self.recommender = models.Recommender.objects.get_or_create(
            name=self.get_name(),
            description=self.DESCRIPTION,
            classname=self.__class__.__name__,
            image=self.IMAGE,
            order=self.ORDER,
            data_info=self.DATA_INFO,
        )[0]

        self.mail_regex = re.compile("[^@]+@[^@]+\.[^@]+")
        try:
            self.backbone = collaborative_filtering_interlink.CollaborativeInterlink()
        except (ChildProcessError, AttributeError):
            logging.info("Error when loading RM_collaborative_filtering recommender backbone!")

    def initialize_templates(self):
        super().initialize_templates()

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id('request_generate_rm_collab'),
            defaults={
                'title': 'Möchtest du neue Empfehlungen erhalten?',
                'description': 'Basierend auf deinen bereits belegeten Kursen',
                'type': 'todo',
                'status': 'template',
                'feedback_size': 0,
                'order': 1111
            }
        )

        e_mail_request_text = 'Möchtest du E-mail Benachrichtigungen erhalten,' \
                              ' wenn ich neue Resourcen basierend auf deiner Belegungshistorie gefunden habe? <br> ' \
                              'WARNUNG: Wenn du deine E-mail Adresse angibst,' \
                              ' bist du für SIDDATA nicht mehr annonym!<br>' \
                              'Du kannst deine E-mail Adresse jederzeit wieder löschen.'

        e_mail_request_question = models.Question.objects.get_or_create(
            question_text=e_mail_request_text,
            answer_type='text',
        )[0]

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("request_e_mail_rm_collab"),
            defaults={
                'title': 'Benachrichtigungen',
                'type': 'question',
                'status': 'template',
                'order': 1111,
                'question': e_mail_request_question,
                'feedback_size': 0
            }
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("e_mail_saved_rm_collab"),
            defaults={
                'title': 'E-mail gespeichert!',
                'type': 'todo',
                'status': 'template',
                'order':1111,
                'feedback_size': 0,
            }
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("e_mail_wrong_format_rm_collab"),
            defaults={
                'title': 'Bitte gib eine korrekte E-mail Adresse ein.',
                'description': 'Leider ist die von dir eingegebene E-mail Adresse ungültig. '
                               'Bitte gib eine gültige E-mail Adresse (z.B. spock@mailserver.de) ein.',
                'type': 'todo',
                'status': 'template',
                'order': 1111,
                'feedback_size': 0,
            }
        )

        models.ActivityTemplate.objects.update_or_create(
            template_id=self.get_template_id("no_recommendations_rm_collab"),
            defaults={
                "description": 'Zur Zeit gibt es leider keine Kurse, die zu dir passen.',
                "type": 'todo',
                "status": 'template',
                "order": 1,
            }
        )

    def initialize(self, user):
        wrapper_goal = self.activate_recommender_for_user_and_create_first_goal(user)
        ur, _ = models.SiddataUserRecommender.objects.get_or_create(
            recommender=self.recommender,
            user=user,
        )
        wrapper_goal.order = 0
        wrapper_goal.title = 'Kurse belegt von Studierenden, die dir ähnlich sind'
        wrapper_goal.save()

        request_generate = models.Activity.create_activity_from_template(
            template_id=self.get_template_id('request_generate_rm_collab'),
            goal=wrapper_goal
        )
        request_generate.save()

        return True

    def process_activity(self, activity):
        if activity.has_template(self.get_template_id('request_generate_rm_collab')):
            self.generate_new_recommendations(activity)
            activity.status = 'active'
            activity.save()

        elif activity.has_template(self.get_template_id('request_e_mail_rm_collab')):
            self.handle_e_mail_request(activity)

        elif activity.has_template(self.get_template_id('e_mail_saved_rm_collab')):
            self.generate_e_mail_request(activity)
            activity.delete()

    def generate_new_recommendations(self,activity):
        goal_order = models.Goal.objects.filter(goal = activity.goal).order_by('order')[0].order + 1
        recommendations_goal = models.Goal.objects.create(
            title='Empfehlungen basierend auf Belegungen ähnlicher Nutzer*innen',
            userrecommender=activity.goal.userrecommender,
            order=goal_order
        )
        recommendations_goal.save()
        recresources = self.backbone.generate_similarity_resources(user=activity.goal.userrecommender.user, top_n=3)
        if len(recresources) == 0:
            self.generate_empty_feedback(activity=activity)
        else:
            local_order = models.Activity.objects.filter(goal=activity.goal).order_by('order')[0].order
            for resource in recresources:
                    local_order += 1
                    title = f'Kursempfehlung: {resource.title}'
                    new_resource_recommendation = models.Activity.objects.create(
                        description= resource.description,
                        type='resource',
                        resource=resource,
                        status='active',
                        goal=activity.goal,
                        title=title,
                        order=local_order
                    )
        return True

    def generate_empty_feedback(self, activity):
        models.Activity.create_activity_from_template(template_id=self.get_template_id('no_recommendations_rm_collab'),
                                                      title='Momentan sind keine Empfehlungen verfügbar',
                                                      goal=activity.goal)
        self.generate_e_mail_request(activity)
        return True

    def generate_e_mail_request(self, activity):
        models.ActivityTemplate.create_activity_from_template(
            template_id=self.get_template_id("request_e_mail_rm_collab"),
            goal=activity.goal,
        )
        return True

    def handle_e_mail_request(self, activity):
        if self.mail_regex.match(activity.answers[0]):
            local_order = models.Activity.objects.filter(goal=activity.goal).order_by('order')[0].order
            saved_e_mail = models.Activity.create_activity_from_template(
                template_id=self.get_template_id('e_mail_saved_rm_collab'),
                goal=activity.goal,
                order= local_order + 1
            )
            saved_e_mail.description = 'Deine E-mail Adresse ' + str(
                activity.answers[0]) + ' wurde gespeichert. Klicke auf \"OK\" um deine E-mail zu löschen.'
            saved_e_mail.answers = activity.answers
            saved_e_mail.save()
            activity.delete()
        else:
            local_order = models.Activity.objects.filter(goal=activity.goal).order_by('order')[0].order
            # if e-mail format is not correct. A correct address format is 'something@something_else.xyz'
            wrong_format_activity = models.Activity.create_activity_from_template(
                template_id=self.get_template_id("e_mail_wrong_format_rm_collab"),
                goal=activity.goal,
                order= local_order + 1
            )
            wrong_format_activity.color_theme = 'red'
            wrong_format_activity.save()
            self.generate_e_mail_request(activity=activity)
            activity.delete()
        return True

    def execute_cron_functions(self):
        address = ''
        title = ''
        content = ''
        self.send_push_email(address, title, content)
        return True
