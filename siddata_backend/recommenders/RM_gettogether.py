"""
Matching users based on self-selected criteria.

author: Jo Sandor, Felix Weber

"""
import datetime
import json
import random
import re
import string
import copy

from recommenders import recommender_functions
from backend import models
from recommenders.RM_BASE import RM_BASE
from bert_app.recommender_backbone import ProfessionsRecommenderBackbone as SidBERT
from siddata_backend import settings
from django.http import HttpResponse

import logging
import recommenders.RM_abroad as RM_abroad

FORM_TITLE = "Meine Visitenkarte"
ALL_CONTACTS_TITLE = "Öffentliche Visitenkarten"
MY_CONTACTS_TITLE = "Persönliche Kontaktvorschläge des Matching Algorithmus"
FORM_SUBMIT_BUTTON_TEXT = "Profil und Kontaktvorschläge aktualisieren"
ABROAD_QUESTION_TEXT = "Empfehlungen auf Basis der Funktion \"Auslandsaufenthalt\""
ABROAD_OPTIONS = ["Ich möchte Kontaktvorschläge zu anderen Studis, die sich in der gleichen Bewerbungsphase befinden.",
                  "Ich möchte Kontaktvorschläge zu anderen Studis, die sich bereits erfolgreich beworben haben.",
                  ]
VISIBILITY_TEXT = "Ich möchte, dass meine Visitenkarte auch für Studis ohne konkrete Übereinstimmungen sichtbar ist."
NOTIFICATION_TEXT = "Ich möchte per E-Mail benachrichtigt werden Siddata neue Kontaktvorschläge für mich gefunden hat."
FEEDBACK_TEXT = "Kontaktvorschläge wurden aktualisiert."
SUBMIT_TEXT = "Ein Klick auf den Button löst eine Aktualisierung anhand der aktuellen Daten aus. Dies " \
                          "aktualisiert sowohl die Empfehlungen als auf das Formular selbst, beispielweise wenn du neue " \
                          "Funktionen genutzt oder neue Eingaben vorgenommen hast."


SEMESTER_START = datetime.datetime(year=2021, month=10, day=1)
SEMESTER_END = datetime.datetime(year=2022, month=3, day=31)


class RM_gettogether(RM_BASE):
    """
        RM for social recommendations, such as communities, matches, etc.
    """

    def __init__(self):
        # this magic line of code lets our recommender inherit all attributes and methods from the baseclass.
        super().__init__()
        # This name should be unique and appears in the Stud.IP GUI.
        self.NAME = "Get Together"
        # If set to False, the recommender will not appear in the GUI or the DB
        # The description text summarizes the functionality. It is shown in teaser activity and tile view,
        self.DESCRIPTION = "Verbinde dich mit anderen Studierenden aus Bremen, Hannover und Osnabrück."
        # This text is displayed in Teaser Activities
        self.TEASER_TEXT = "Siddata bietet dir die Möglichkeit, dich mit Studierenden aus Bremen, Hannover und Osnabrück zu vernetzen. Du kannst beispielsweise Lernpartner finden, Erfahrungen\
         zum Auslandssemester austauschen und Kommilitonen mit gleichen Interessen kennenlernen. Möchtest du die Funktion Get Together nutzen?"
        # If set to False, the recommender will not appear in the GUI or the DB
        self.ACTIVE = True
        # Image is shown in teaser activity
        self.IMAGE = "gettogether.png"
        # determines arrangement in Frontend
        self.ORDER = 4
        # This string tells the user which data is required for this recommender
        self.DATA_INFO = "Diese Funktion kann Daten zu deinem Studiengang, einem geplanten Auslandssemester, sowie deine Uni und belegte Kurse nutzen. Im Recommender " \
                         "selbst entscheidest du welche Daten genutzt werden."
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
        try:
            super().initialize_templates()

            models.ActivityTemplate.objects.update_or_create(
                template_id=self.get_template_id("no_matches"),
                defaults={
                    "description": "Hier tauchen Kontaktvorschläge auf wenn Siddata Übereinstimmungen findet.",
                    "title": "Aktuell keine Treffer",
                    "type": "todo",
                    "status": "template",
                    "image": self.IMAGE,
                    "order": 0,
                    "button_text": "~static",
                }
            )
        except Exception:
            logging.exception("Error in initialize_templates()")

    def generate_example_data(self):
        """
        For testing purposes: Generates some other users who wish to get in contact.
        :return: True if everything goes right
        """

        try:
            origin = models.Origin.objects.all()[0]

            names = ["c83zn9jBCKCZiWSn1+742Ukxq4aankBbhTaoFGXEQ9U=",
                     "pR7ANUr/2lehLe2Igj0XvyB4cw9DvPiHJuCV0R5LbLs=",
                     "gtMlA9o0xRbEb55N+QewJ1BffcxX69NxQ7iRerNeDWU=",
                     "UB1gvZSHl3ndyyCrLye1AVBhF/A0GOm5ReHE2VtKRNE=",
                     ]

            surnames = ["vUvYBj/f8mN2R0WLUKh2scIb2i8w61vfRSvXlDT4pC8=",
                        "Lcoyx1pt+aUnz4hM8YzulQwBJer+AO4nNIrdiRp8JOE=",
                        "N35HB2gnPZvplhQJxSfRMj6fAij92lSL+lWF6LQgER7YXo3eaYzb9FcYegNXCHsp",
                        "JgS3H16LdCyOPJGyp+MESgXfjnj0K40odP29ihv4VUI=",
                        ]

            emails = ["NrsH38BHZXcrnxh4JOWSRkmSTb+VhowK4yk26du/FaI=",
                      "yWnk4AHUGJONbD26Nf21/tPMjHz0sTG+b+Eoi3CY8tc=",
                      "2IUj9hzJogpu6oZ25gM1svzzW0ybOFUz+jm35liJ1cA=",
                      "w5PC9zrZYVTKXOsfkgRQNcoVPm2lyAG3D7OTcTeM2YRpqGIMZSOUtDXgXc1lKqqa",
                      ]

            images = ["7a92c8c3d92174796be571e8edd01cd502209e8de1798d83d067c2ddc4e954d4.png",
                      "30d48c36840a0e6beaf8354a3e235105f734f8910631de0f9b6eeb8319b85751.png",
                      "5906210ab6bf92a32c304fa28e26895a2ae6298924c18489a937e9bb7bec4e6a_TeelhKT.png",
                      "a7262115bc94bc0c979cd1813bdfdb08d5b61d8913dbf06ef1d610dbe23ffbec.png",
                      ]

            subjects = ["Ägyptologie",
                        "Kognitionswissenschaften",
                        "Wirtschaftswissenschaften"]

            descriptions = ["Ich denke also bin ich",
                            "A universe of atoms - an atom in the universe.",
                            "Ich teile heimlich durch null."]

            degrees = ["Bachelor of Science",
                       "Master of Desaster",
                       "Doppeldiplom"]

            courses = ["Einführung in die Meta-Häkelei",
                       "Frühstücken für Sozialwissenschaftler",
                       "Einführung in die frühe Geschichte des späten Mittelalters",
                       "Der Gouda und seine Auswirkungen auf Raclett mit und ohne Kirschwasser", ]

            semesters = list(range(1, 15))

            interests = ["Kochen und Backen",
                         "Deep Learning",
                         "Papierchromatografie mit Cellophan und selbst gebastelten Pigmenten"]

            abroad_phases = RM_abroad.STAGES

            for i in range(1, 10):
                user = models.SiddataUser.objects.create(
                    origin=origin,
                    user_origin_id=''.join(random.choices(string.ascii_letters + string.digits, k=15)),
                    gender_brain=True,
                    gender_social=True,
                    data_donation=True,
                )
                user.save()

                recommender_functions.create_initial_data_for_user(user)

                recommenders = recommender_functions.get_active_recommenders()

                for rm in recommenders:
                    if rm.NAME == self.get_name():
                        rm.initialize(user)

                userrecommender = models.SiddataUserRecommender.objects.get(user=user,
                                                                            recommender__name=self.get_name())

                form_goal = models.Goal.objects.get_or_create(userrecommender=userrecommender,
                                                              title=self.get_name())[0]

                form = form_goal.get_max_form() + 1
                order = form_goal.get_max_order() + 1

                name = random.choice(names)
                surname = random.choice(surnames)
                email = random.choice(emails)
                image = random.choice(images)
                role_description = random.choice(descriptions)

                form_name = "{} {}".format(name, surname)

                person = models.Person.objects.create(
                    image="images/{}".format(image),
                    editable=True,
                    first_name=name,
                    surname=surname,
                    email=email,
                    user=user,
                    role_description=role_description,
                )
                person.save()

                person_activity = models.Activity.objects.create(
                    title=form_name,
                    description="person",
                    image="sid.png",
                    type="person",
                    status="immortal",
                    person=person,
                    feedback_size=0,
                    order=order,
                    form=form,
                    goal=form_goal,
                )
                person_activity.save()

                order += 1

                subject = random.choice(subjects)
                degree = random.choice(degrees)
                semester = random.choice(semesters)

                sus_attributes = ["Fach: {}".format(subject),
                                  "Abschluss: {}".format(degree),
                                  "Semester: {}".format(semester), ]

                studies_question = models.Question.objects.get_or_create(
                    question_text='Welche Daten zu deinem Studium sollen für Kontaktvorschläge berücksichtigt werden?',
                    answer_type='checkbox',
                    selection_answers=sus_attributes,
                )[0]

                sus_answers = [sus for sus in sus_attributes if random.choice([True, False])]

                studies_activity = models.Activity.objects.create(
                    title=form_name,
                    description="sus",
                    goal=form_goal,
                    form=form,
                    type="question",
                    status="immortal",
                    question=studies_question,
                    feedback_size=0,
                    order=order,
                    answers=sus_answers,
                )
                studies_activity.save()

                order += 1

                ###  COURSES  ###

                my_courses = []
                for c in courses:
                    if random.choice([True, False]):
                        my_courses.append((c))
                if len(my_courses) == 0:
                    question_text = "Zu welchen Kursen würdest du dich gerne austauschen? (Keine Freigabeeinstellung)"
                else:
                    question_text = "Zu welchen Kursen würdest du dich gerne austauschen?"

                courses_question = models.Question.objects.create(
                    answer_type='checkbox',
                    question_text=question_text,
                    selection_answers=courses,
                )
                courses_question.save()

                courses_activity = models.Activity.objects.create(
                    title=FORM_TITLE,
                    description="courses",
                    type="question",
                    status="immortal",
                    feedback_size=0,
                    form=form,
                    order=order,
                    goal=form_goal,
                    question=courses_question,
                )
                courses_activity.save()

                order += 1

                question_text = "Empfehlungen auf Basis deiner fachlichen Interessen."

                professions_question = models.Question.objects.get_or_create(
                    question_text=question_text,
                    answer_type='checkbox',
                    selection_answers=interests,
                )[0]

                professions_question.save()

                interests_answers = [interest for interest in interests if random.choice([True, False])]

                professions_activity = models.Activity.objects.create(
                    title=form_name,
                    description="professions",
                    type="question",
                    status="immortal",
                    feedback_size=0,
                    form=form,
                    question=professions_question,
                    order=order,
                    goal=form_goal,
                    answers=interests_answers,
                )
                professions_activity.save()

                order += 1

                if random.choice([True, False]):
                    for rm in recommenders:
                        # initialize abroad recommender and induce random stage
                        if rm.NAME == "Auslandsaufenthalt":
                            rm.initialize(user)

                            selection_answers = RM_abroad.STAGE_DESCRIPTIONS

                            initial_activity = models.Activity.objects.get(
                                title="In welcher Phase befindest du dich?",
                                description="Initiale Fragen",
                                type="question",
                                goal__userrecommender__user=user,
                            )

                            initial_activity.answers = [random.choice(selection_answers)]

                            initial_activity.save()
                            rm.process_activity(initial_activity)

                if recommender_functions.recommender_activated(user, "RM_abroad") == False:
                    question_text = "{} (Aktuell nutzt du diese Funktion nicht.)".format(ABROAD_QUESTION_TEXT)
                    abroad_categories = []
                else:
                    question_text = ABROAD_QUESTION_TEXT
                    abroad_categories = [
                        "Ich möchte Kontaktvorschläge zu anderen Studis, die sich in der gleichen Bewerbungsphase befinden.",
                        "Ich möchte Kontaktvorschläge zu anderen Studis, die sich bereits erfolgreich beworben haben.",
                    ]

                abroad_question = models.Question.objects.create(
                    question_text=question_text,
                    answer_type="checkbox",
                    selection_answers=abroad_categories,
                )
                abroad_question.save()

                if len(abroad_categories) == 0:
                    answers = []
                else:
                    answers = [random.choice(abroad_categories)]

                abroad_activity = models.Activity.objects.create(
                    title=form_name,
                    description="abroad",
                    type="question",
                    status="immortal",
                    feedback_size=0,
                    form=form,
                    question=abroad_question,
                    order=order,
                    goal=form_goal,
                    answers=answers,
                )
                abroad_activity.save()

                order += 1

                visibility_question = models.Question.objects.get_or_create(
                    question_text='Sichtbarkeit',
                    answer_type='checkbox',
                    selection_answers=[
                        "Ich möchte, dass meine Visitenkarte auch für Studis ohne konkrete Übereinstimmungen "
                        "sichtbar ist."],
                )[0]

                visibility_activity = models.Activity.objects.create(
                    title=form_name,
                    description="visible",
                    type="question",
                    status="immortal",
                    feedback_size=0,
                    form=form,
                    question=visibility_question,
                    order=order,
                    goal=form_goal,
                    answers=random.choice([[], [
                        "Ich möchte, dass meine Visitenkarte auch für Studis ohne konkrete Übereinstimmungen "
                        "sichtbar ist."]])
                )
                visibility_activity.save()

                order += 1

                notification_question = models.Question.objects.get(
                    question_text='Benachrichtigungen',
                    answer_type='checkbox',
                    selection_answers=[NOTIFICATION_TEXT],
                )

                notification_activity = models.Activity.objects.create(
                    title=form_name,
                    description="notification",
                    type="question",
                    status="immortal",
                    feedback_size=0,
                    form=form,
                    question=notification_question,
                    order=order,
                    button_text=FORM_SUBMIT_BUTTON_TEXT,
                    goal=form_goal,
                    answers=random.choice([
                        [],
                        [
                            "Ich möchte per E-Mail benachrichtigt werden Siddata neue Kontaktvorschläge für mich gefunden hat."]
                    ]),
                )
                notification_activity.save()

                order += 1
        except Exception:
            logging.exception("Error in generate_example_data()")

        return True

    def initialize(self, user):
        """
        When a user logs in for the first time, initial activities are generated.
        :param user: SiddataUser object
        :return: True if successful
        """
        try:
            goal = self.activate_recommender_for_user_and_create_first_goal(user)
            goal.visible = False
            goal.save()

            personal_matches_goal = models.Goal.objects.create(
                title=MY_CONTACTS_TITLE,
                type="carousel",
                userrecommender=goal.userrecommender,
                order=2,
            )
            personal_matches_goal.save()

            available_contacts_goal = models.Goal.objects.create(
                title=ALL_CONTACTS_TITLE,
                type="carousel",
                userrecommender=goal.userrecommender,
                order=3,
            )
            available_contacts_goal.save()

            # todo: remove before release
            if settings.DEBUG:
                testdata_activity = models.Activity.objects.create(
                    title="Testdaten generieren",
                    description="Generiert im Testbetrieb 50 Nutzende.",
                    type="todo",
                    status="immortal",
                    feedback_size=0,
                    order=99,
                    button_text="Abracadabra!",
                    goal=goal,
                )
                testdata_activity.save()

            self.update_profile_form(goal)

            return True
        except Exception:
            logging.exception("Error in initialize()")


    def process_activity(self, activity):
        """
        This function processes the incoming activities which were processed by the user.
        :param activity: activity
        :return: True if successful
        """
        try:
            goal = activity.goal

            if goal.title == self.get_name():
                if activity.description == SUBMIT_TEXT:

                    all_form_goals = models.Goal.objects.filter(title=self.get_name()).exclude(
                        userrecommender=goal.userrecommender)

                    print(len(all_form_goals))
                    all_contacts_goal = models.Goal.objects.get(userrecommender=goal.userrecommender,
                                                                title=ALL_CONTACTS_TITLE)

                    personal_matches_goal = models.Goal.objects.get(userrecommender=goal.userrecommender,
                                                                    title=MY_CONTACTS_TITLE)

                    i = 1
                    for form_goal in all_form_goals:
                        my_data = self.extract_data_from_form(activity.goal)
                        your_data = self.extract_data_from_form(form_goal)
                        self.update_contactcard(data=your_data, target_goal=all_contacts_goal, public_only=True)
                        match, my_highlighted_data, your_highlighted_data = self.match_and_highlight(my_data=my_data,
                                                                                  your_data=your_data)
                        if match:
                            self.update_contactcard(data=your_highlighted_data, target_goal=personal_matches_goal, public_only=False)
                            i += 1
                    self.update_profile_form(goal)

                    return HttpResponse(FEEDBACK_TEXT)

                elif activity.title == "Testdaten generieren":
                    self.generate_example_data()

        except Exception:
            logging.exception("Error in process_activity()")

    def is_email(self, some_string):
        """
        Checks if a string is a valid email address.
        :param some_string:
        :return: Boolean
        """
        try:
            regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

            return re.fullmatch(regex, some_string)

        except Exception:
            logging.exception("Error in is_email()")


    def update_profile_form(self, goal):
        """
        Builds or renews the form that allows to insert contact request data.
        :param goal: goal containing the form
        :return: True if successful
        """
        try:
            user = goal.userrecommender.user

            order = 1
            form = 1

            person, created = models.Person.objects.get_or_create(
                editable=True,
                user=user,
            )
            person.save()

            person_activity, created = models.Activity.objects.get_or_create(
                title=FORM_TITLE,
                description="person",
                type="person",
                status="immortal",
                person=person,
                feedback_size=0,
                order=order,
                form=form,
                goal=goal,
                button_text=FORM_SUBMIT_BUTTON_TEXT,
            )
            person_activity.save()

            order += 1

            ### STUDIES  ###

            question_text = "Welche Daten zu deinem Studium sollen für Kontaktvorschläge berücksichtigt werden?"

            my_siddatauserstudies = models.SiddataUserStudy.objects.filter(user=user)

            sus_attributes = []
            for sus in my_siddatauserstudies:
                if sus == None:
                    continue
                try:
                    sus_attributes.append("Fach: {}".format(sus.subject.name))
                except:
                    logging.warning("Missing subject")
                try:
                    sus_attributes.append("Abschluss: {}".format(sus.degree.name))
                except:
                    logging.warning("Missing degree")
                try:
                    sus_attributes.append("Semester: {}".format(sus.semester))
                except:
                    logging.warning("Missing semester")

            studies_activity, created = models.Activity.objects.get_or_create(
                title=FORM_TITLE,
                description="sus",
                goal=goal,
                form=form,
                type="question",
                status="immortal",
                feedback_size=0,
                order=order,
                button_text=FORM_SUBMIT_BUTTON_TEXT,
            )

            if created:
                studies_question = models.Question.objects.create(
                    answer_type='checkbox',
                )
                studies_activity.question = studies_question
                studies_activity.save()
            else:
                studies_question = studies_activity.question
            studies_question.question_text = question_text
            studies_question.selection_answers = sus_attributes
            studies_question.save()

            order += 1

            ### COURSES ###

            my_courses_memberships = models.CourseMembership.objects.filter(
                user=user,
                share_brain=True,
                share_social=True,
            )

            question_text = "Zu welchen Kursen würdest du dich gerne austauschen?"
            courses = []
            if len(my_courses_memberships) == 0:
                question_text = "Zu welchen Kursen würdest du dich gerne austauschen? (Keine Freigabeeinstellung)"
            else:
                for cm in my_courses_memberships:
                    courses.append(cm.course.title)

            courses_activity, created = models.Activity.objects.get_or_create(
                title=FORM_TITLE,
                description="courses",
                type="question",
                status="immortal",
                feedback_size=0,
                form=form,
                order=order,
                goal=goal,
                button_text=FORM_SUBMIT_BUTTON_TEXT,
            )

            if created:
                courses_question = models.Question.objects.create(
                    answer_type='checkbox',
                )
                courses_activity.question = courses_question
                courses_activity.save()
            else:
                courses_question = courses_activity.question
            courses_question.question_text = question_text
            courses_question.selection_answers = courses
            courses_question.save()

            order += 1

            #### PROFESSIONS ###

            profession_goals = models.Goal.objects.filter(
                userrecommender__recommender__classname="RM_professions",
                userrecommender__user=user,
            ).exclude(title='interest_associated_goal')

            if recommender_functions.recommender_activated(user, "RM_professions") == False:
                question_text = "Empfehlungen auf Basis deiner fachliche Interessen (Aktuell nutzt du diese Funktion nicht.)"
                selection_answers = []
            else:
                question_text = "Empfehlungen auf Basis deiner fachlichen Interessen."
                if len(profession_goals) == 0:
                    selection_answers = []
                    question_text = "Empfehlungen auf Basis deiner fachlichen Interessen. (Du hast noch keine definiert.)"
                else:
                    selection_answers = [x.title for x in profession_goals]

            professions_activity, created = models.Activity.objects.get_or_create(
                title=FORM_TITLE,
                description="professions",
                type="question",
                status="immortal",
                feedback_size=0,
                form=form,
                order=order,
                goal=goal,
                button_text=FORM_SUBMIT_BUTTON_TEXT,
            )

            if created:
                professions_question = models.Question.objects.create(
                    answer_type='checkbox',
                )
                professions_activity.question = professions_question
                professions_activity.save()
            else:
                professions_question = professions_activity.question

            professions_question.question_text = question_text
            professions_question.selection_answers = selection_answers
            professions_question.save()

            order += 1

            ### ABROAD ###

            if recommender_functions.recommender_activated(user, "RM_abroad") == False:
                question_text = "{} (Aktuell nutzt du diese Funktion nicht.)".format(ABROAD_QUESTION_TEXT)
                abroad_categories = []
            else:
                question_text = ABROAD_QUESTION_TEXT
                abroad_categories = ABROAD_OPTIONS

            abroad_activity, created = models.Activity.objects.get_or_create(
                title=FORM_TITLE,
                description="abroad",
                type="question",
                status="immortal",
                feedback_size=0,
                form=form,
                order=order,
                goal=goal,
                button_text=FORM_SUBMIT_BUTTON_TEXT,
            )

            if created:
                abroad_question = models.Question.objects.create(
                    answer_type="checkbox",
                )
                abroad_activity.question = abroad_question
                abroad_activity.save()
            else:
                abroad_question = abroad_activity.question

            abroad_question.question_text = question_text
            abroad_question.selection_answers = abroad_categories
            abroad_question.save()

            order += 1

            ### VISIBILITY ###

            visibility_question, created = models.Question.objects.get_or_create(
                question_text='Sichtbarkeit',
                answer_type='checkbox',
                selection_answers=[VISIBILITY_TEXT],
            )

            visibility_activity, created = models.Activity.objects.get_or_create(
                title=FORM_TITLE,
                description="visible",
                type="question",
                status="immortal",
                feedback_size=0,
                form=form,
                question=visibility_question,
                order=order,
                goal=goal,
                button_text=FORM_SUBMIT_BUTTON_TEXT,
            )

            order += 1

            notification_question = models.Question.objects.get_or_create(
                question_text='Benachrichtigungen',
                answer_type='checkbox',
                selection_answers=[NOTIFICATION_TEXT],
            )[0]

            notification_activity = models.Activity.objects.get_or_create(
                title=FORM_TITLE,
                description="notification",
                type="question",
                status="immortal",
                feedback_size=0,
                form=form,
                question=notification_question,
                order=order,
                button_text=FORM_SUBMIT_BUTTON_TEXT,
                goal=goal,
            )[0]

            order += 1

            description = SUBMIT_TEXT

            info_activity, created = models.Activity.objects.get_or_create(
                title=FORM_TITLE,
                description=description,
                type="todo",
                status="immortal",
                feedback_size=0,
                form=form,
                order=order,
                goal=goal,
                button_text=FORM_SUBMIT_BUTTON_TEXT,
            )


        except Exception:
            logging.exception("Error in update_profile_form()")

    def send_email(self, goal):
        """"
        Is called to send an email notification when the cronjob finds new matches.
        """
        try:
            data = json.loads(goal.get_property(key="data"))
            try:
                address = data["email"]
            except Exception:
                return

            name = data["name"]

            url = goal.userrecommender.user.origin.api_endpoint

            title = "Neuer Kontaktvorschlag im SIDDATA Studienassistenten"
            content = "Guten Tag {},<br>" \
                      "der Siddata Studienassistent hat einen neuen Kontaktvorschlag mit Übereinstimmungen für dich gefunden!<br>" \
                      "Besuche das Recommender Modul 'Get Together' im Stud.IP SIDDATA" \
                      " Studierendenassistenten um diese Kontaktvorschläge anzusehen.{}".format(name, url)

            self.send_push_email(address, title, content)
        except Exception:
            logging.exception("Error in Gettogether.send_email()")

    def extract_data_from_form(self, goal):
        """Iterates over form activities and aggregates contained data."""
        try:
            form_activities = models.Activity.objects.filter(goal=goal)

            checksum = 0
            for act in form_activities:
                if act.description == "person":
                    person_activity = act
                    checksum += 1
                elif act.description == "sus":
                    sus_activity = act
                    checksum += 1
                elif act.description == "courses":
                    courses_activity = act
                    checksum += 1
                elif act.description == "professions":
                    professions_activity = act
                    checksum += 1
                elif act.description == "abroad":
                    abroad_activity = act
                    checksum += 1
                elif act.description == "visible":
                    visible_activity = act
                    checksum += 1
                elif act.description == "notification":
                    notification_activity = act
                    checksum += 1
                elif act.title == "Testdaten generieren":
                    pass

            if checksum < 7:
                return

            abroad_stages = []
            if ABROAD_OPTIONS[0] in abroad_activity.answers:
                abroad_stages.append(RM_abroad.RM_abroad.get_stage_for_user(goal.userrecommender.user))
            if ABROAD_OPTIONS[0] in abroad_activity.answers:
                if RM_abroad.STAGES[2] not in abroad_stages:
                    abroad_stages.append(RM_abroad.STAGES[2])
            if not abroad_stages:
                abroad_stages.append("Planungsphase noch offen")

            data = {"user_id": person_activity.person.user.id,
                    "email": person_activity.person.email,
                    "first_name": person_activity.person.first_name,
                    "surname": person_activity.person.surname,
                    "role_description": person_activity.person.role_description,
                    "image": person_activity.person.image,
                    "location": goal.userrecommender.user.origin.location,
                    "sus": sus_activity.answers,
                    "courses": courses_activity.answers,
                    "professions": professions_activity.answers,
                    "abroad": abroad_stages,
                    "visible": True if VISIBILITY_TEXT in visible_activity.answers else False,
                    "notification": True if NOTIFICATION_TEXT in visible_activity.answers else False,
                    }
            return data

        except Exception:
            logging.exception("Error in Gettogether.extract_data_from_form()")

    def match_and_highlight(self, my_data, your_data):
        """
        Calculates if two users match based on their data. If so, contact cards activities are
        generated and notifications sent.
        :param my_goal: Goal of the user initializing the matching process by new input.
        :param your_goal: Goal of other user to be compared (User gets email notification in case of match.)
        :return: my_data, your_data, True if match else False
        """
        try:

            match = False

            criteria = ["sus", "courses", "abroad"]

            for c in criteria:
                for me in range(len(my_data[c])):
                    for you in range(len(your_data[c])):
                        if my_data[c][me] == your_data[c][you]:
                            my_data[c][me] = "<strong>{}</strong>".format(my_data[c][me])
                            your_data[c][you] = "<strong>{}</strong>".format(your_data[c][you])
                            match = True

            for me in range(len(my_data["professions"])):
                for you in range(len(your_data["professions"])):
                    if SidBERT().compare_strings_by_ddc(my_data["professions"][me], your_data["professions"][you],
                                                        is_same=True):
                        my_data["professions"][me] = "<strong>{}</strong>".format(my_data["professions"][me])
                        your_data["professions"][you] = "<strong>{}</strong>".format(your_data["professions"][you])
                        match = True

            return match, my_data, your_data

        except Exception:
            logging.exception("Error in match()")

    def get_users_courses(self, user):
        """Retrieves all courses within the current semester, for which a user is enrolled."""
        coursememberships = models.CourseMembership.filter(
            user=user,
            share_brain=True,
            share_social=True,
            course__starttime__gte=SEMESTER_START,
            course__endtime__lte=SEMESTER_END,
        )
        return [c.course for c in coursememberships]


    def update_contactcard(self, data, target_goal, public_only=True):
        """Displays user data in a goal.
        :param data : Data to be displayed in dictionary form
        :param target_goal: Goal object
        :param public : Boolean which determines check for visibility consent
        :return: True if successful else False"""
        try:

            status = "immortal"

            # no user consent for visibility
            if public_only and (data["visible"]==False):
                return False


            user = models.SiddataUser.objects.get(id=data["user_id"])
            person, created = models.Person.objects.get_or_create(user=user,
                                                                  editable=False, )

            person.first_name = data["first_name"]
            person.surname = data["surname"]
            person.email = data["email"]
            person.image = data["image"]
            person.role_description = data["role_description"]
            person.save()

            person_activity, created = models.Activity.objects.get_or_create(person=person,
                                                                             goal=target_goal)

            if created:
                form = target_goal.get_max_form() + 1
                order = target_goal.get_max_order() + 1
                title = "Kontaktvorschlag {}".format(form)
                person_activity.form = form
                person_activity.order = order
                person_activity.title = title
                person_activity.type = "person"
                person_activity.feedback_size = 0
                person_activity.status = status
                person_activity.button_text = "~static"
                person_activity.save()

            form = person_activity.form
            title = person_activity.title
            order = person_activity.order

            order += 1


            location_activity, created = models.Activity.objects.get_or_create(
                title=title,
                description="Standort: {}".format(data["location"]),
                type="todo",
                status=status,
                feedback_size=0,
                order=order,
                form=form,
                goal=target_goal,
                button_text="~static",
            )
            location_activity.save()

            order += 1

            ### SUS ###

            description = "<strong>"
            description += "Studiengangsinformationen"
            description += "</strong>"
            description += "<br>"

            if data["sus"] != []:
                for sus in data["sus"]:
                    description += sus
                    description += "<br>"
            else:
                description += "Keine Studiengangsinformationen verfügbar"
                description += "<br>"

            out_sus_activity, created = models.Activity.objects.get_or_create(
                title=title,
                type="todo",
                goal=target_goal,
                order=order,
                status=status,
                feedback_size=0,
                form=form,
                button_text="~static",
            )

            out_sus_activity.description = description
            out_sus_activity.save()

            order += 1

            ### COURSES  ###

            description = "<strong>"
            description += "Belegte Kurse:"
            description += "</strong>"
            description += "<br>"
            if data["courses"] != []:
                for course in data["courses"]:
                    description += course
                    description += "<br>"
            else:
                description += "Keine Kursinformationen verfügbar"
                description += "</br>"

            out_courses_activity, created = models.Activity.objects.get_or_create(
                title=title,
                type="todo",
                status=status,
                feedback_size=0,
                order=order,
                form=form,
                goal=target_goal,
                button_text="~static",
            )
            out_courses_activity.description = description
            out_courses_activity.save()

            order += 1

            ### PROFESSIONS  ###

            description = "<strong>"
            description += "Interessen:"
            description += "</strong>"
            description += "<br>"
            if data["professions"] != []:
                for interest in data["professions"]:
                    description += interest
                    description += "<br>"
            else:
                description += "Keine Informationen über Interessen verfügbar"
                description += "<br>"

            out_professions_activity, created = models.Activity.objects.get_or_create(
                title=title,
                type="todo",
                status=status,
                feedback_size=0,
                order=order,
                form=form,
                goal=target_goal,
                button_text="~static",
            )
            out_professions_activity.description = description
            out_professions_activity.save()

            order += 1

            ### ABROAD  ###

            if data["abroad"] != []:
                description = "<strong>"
                description += "Auslangssemester Planungsphase:"
                description += "</strong>"
                description += "<br>"
                stages = []
                for stage in data["abroad"]:
                    if stage:
                        description += stage
                        description += "<br>"

                out_abroad_activity, created = models.Activity.objects.get_or_create(
                    title=title,
                    type="todo",
                    status=status,
                    feedback_size=0,
                    order=order,
                    form=form,
                    goal=target_goal,
                    button_text="~static",
                )
                out_abroad_activity.description = description
                out_abroad_activity.save()

            return True
        except Exception:
            logging.exception("Error in create_public_contact_card()")

    def get_users_courses(self, user):
        """Retrieves all courses within the current semester, for which a user is enrolled."""
        coursememberships = models.CourseMembership.filter(
            user=user,
            share_brain=True,
            share_social=True,
            course__starttime__gte=SEMESTER_START,
            course__endtime__lte=SEMESTER_END,
        )
        return [c.course for c in coursememberships]
