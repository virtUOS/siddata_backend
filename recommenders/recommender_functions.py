import datetime
import importlib
import random
import logging

from os import listdir
from os.path import isfile, join

import pandas as pd

from backend import models
import settings
from recommenders.RM_start import RM_start


RMMODULE = "recommenders"

RANDOMIMAGES = ["brainbulb.png", "idea.png", "formulas.png"]


def check_for_RM_existence(rm_classname):
    """
    Function to check if an RM module already exists in the Database. Workaround to avoid multiple RM modules being
    instantiated.
    :para m rm_classname: class name of the recommender
    """
    try:
        return models.Recommender.objects.filter(classname=rm_classname).exists()
    except Exception:
        logging.exception("Error in recommender_functions.check_for_RM_existence()")


def create_initial_data_for_user(user):
    """
    Initializes categories, goals and activities for a user when he first shows up.
    :param user: SiddataUser instance
    :return: True if successful
    """

    try:
        start = RM_start()
        start.initialize(user)
        generate_p2_user_info(user)
        goal = start.get_default_goal(user)
        active_rms = get_active_recommenders()
        for rm in active_rms:
            try:
                rm.create_teaser_activity(goal)
                if rm.get_name() != "Startseite":
                    r = models.SiddataUserRecommender.objects.get_or_create(
                        user=user,
                        recommender=models.Recommender.objects.get_or_create(
                            name=rm.get_name(),
                            classname=rm.get_class_name(),
                            description=rm.DESCRIPTION,
                        )[0],
                        enabled=False,
                    )[0]
                    r.save()
            except Exception as e:
                logging.error("Error in recommender_functions.create_initial_data_for_user: {}".format(e))
                logging.error("RM is {}".format(rm.get_name()))

        return True

    except Exception as e:
        logging.error("Error in recommender_functions.create_initial_data_for_user: {}".format(e))
        return False


def create_recommender_by_classname(rm):
    """
    Create a class instance by constructor call in a string.
    :param rm: module class name, class name plus arguments in ()
    :return: an instance of the class specified.
    """
    try:
        rm_call = "{}.{}.{}()".format(RMMODULE, rm, rm)
        if "(" in rm_call:
            full_class_name, args = class_name = rm_call.rsplit('(', 1)
            args = '(' + args
        else:
            full_class_name = rm_call
            args = ()
        # Get the class object
        module_path, _, class_name = full_class_name.rpartition('.')
        mod = importlib.import_module(module_path)
        klazz = getattr(mod, class_name)
        alias = class_name + "Alias"
        instance = eval(alias + args, {alias: klazz})
        return instance

    except Exception:
        logging.exception("Error in recommender_functions.create_recommender_by_classname()")
        return False


def get_active_recommenders():
    """
    Returns a list of recommender instances which are activated.
    Searches the recommender directory for files and classes.
    :return: list with recommender class instances
    """
    try:
        # path with recommender modules
        RM_path = settings.BASE_DIR + "/recommenders"

        # only files
        files = [f for f in listdir(RM_path) if isfile(join(RM_path, f))]
        # only files starting with RM

        files = [f for f in files if f[:3] == "RM_"]

        active = []
        for file in files:
            try:
                # remove .py ending
                name = file[:-3]

                rm = create_recommender_by_classname(name)
                if rm.activated():
                    active.append(rm)

            except Exception as e:
                logging.error("class instantiation failed for {}".format(name))
                logging.error("Error in recommender_functions.get_active_recommenders() {}".format(e))
        return active
    except Exception:
        logging.exception("Error in recommender_functions.get_active_recommenders()")


def get_active_recommender_names():
    """
    Instantiates all active recommenders and returns their names.
    :return: list of class names
    """
    try:
        rms = get_active_recommenders()
        return [rm.get_name() for rm in rms]
    except Exception:
        logging.exception("Error in recommender_functions.get_active_recommender_names()")


def get_active_recommender_class_names():
    """
    Instantiates all active recommenders and returns their class names.
    :return: list of class names
    """
    try:
        rms = get_active_recommenders()
        return [rm.get_class_name() for rm in rms]
    except Exception:
        logging.exception("Error in recommender_functions.get_active_recommender_names()")


def get_random_image():
    return random.choice(RANDOMIMAGES)


def check_for_teaser_activity(activity):
    """
    Checks if an activity is a teaser-activity. If so and if answer is positive,
    activates recommender.
    :param activity: activity object to evaluate
    :return:
    """
    try:
        # Check if marker string for teaser activities is present
        if activity.description is None or "Teaser" not in activity.description:
            return False
        # if answer was not positive, return
        if not "Ja" in activity.answers:
            return False

        # remove marker string
        name = activity.description.replace("Teaser_", "")
        return initialize_recommender_for_user(activity.goal.userrecommender.user, name)
    except Exception:
        logging.exception("Error in recommender_functions.check_for_teaser_activity()")


def initialize_recommender_for_user(user, rm_name):
    """
    Finds a recommender by its name and instantiates it for a user.
    :param user: SiddataUser object
    :param rm_name: String with correct name
    :return: True if successful, else False
    """
    try:
        recommenders = get_active_recommenders()
        for rm in recommenders:
            # if correct recommender is found:
            if rm.get_name() == rm_name:
                rm.initialize(user)
                return True
        return False
    except Exception:
        logging.exception("Error in recommender_functions.initialize_recommender_for_user()")


def generate_comprehensive_recommender(user, include=True):
    """
    todo: complete or remove
    Returns a recommender that is dynamically filled with all activities of a user to develop prioritization
    functions.
    :return: Recommender object
    """
    try:
        rm_name = "Testgebiet Priorisierung"
        #################### Goal ##############

        included = []

        included_activities = []

        activity_dicts = []
        activityset = models.Activity.objects.filter(goal__userrecommender__user=user).order_by("order")

        for activity in activityset:
            activity_dicts.append({"id": activity.id, "type": "Activity"})
            if include:
                a_ser = activity.serialize()
                for entry in a_ser["data"] + a_ser["included"]:
                    if entry not in included_activities:
                        included_activities.append(entry)

        goal_json = {
            "data": [{
                "type": "Goal",
                "id": 42,
                "attributes": {
                    "title": "Alle Activities",
                    "description": "In diesem Goal sind alle Activities des Users enthalten.",
                    "makedate": datetime.datetime.now(),
                    "user": user.pk,
                    "recommender": rm_name,
                    "order": 1001,
                    "type": None,
                    "visible": False,

                },
                "relationships": {
                    "activities": {
                        "data": activity_dicts
                    },
                    "goalproperties": {
                        "data": {}
                    },
                    "students": {
                        "data": [{
                            "id": user.id,
                            "type": "SiddataUser"
                        }]
                    }
                }
            }],
        }

    ############################################ recommender ############
        goal_dicts = []
        included_goal = []

        goal_dicts.append({"id": 42, "type": "Goal"})
        if include:
            for entry in goal_json["data"] + goal_json["included"]:
                if entry not in included_goal:
                    included_goal.append(entry)

        response_data = {
            "data": [{
                "type": "Recommender",
                "id": 42,
                "attributes": {
                    "name": rm_name,
                    "classname": rm_name,
                    "description": "Hier werden Algorithmen entwickeln um einen Feed mit allen Activities in eine "
                                   "sinnvolle Reihenfolge zu bringen.",
                    "image": "{}{}".format(settings.IMAGE_URL, "professions.png"),
                    "order": 1001,
                    "enabled": True,
                    "data_info": "Keine Daten benötigt",
                },
                "relationships": {
                    "goals": {
                        "data": goal_dicts
                    },
                    "activities": {
                        "data": []
                    },
                    "students": {
                        "data": [{
                            "type": "SiddataUser",
                            "id": user.id
                        }]
                    }
                }
            }],
        }

        if include:
            u_ser = user.serialize(include=[])["data"][0]
            if u_ser not in included:
                included.append(u_ser)
            response_data['included'] = included

        return response_data
    except Exception:
        logging.exception("Error in recommender_functions.generate_comprehensive_recommender()")


def refresh_all_recommenders():
    """
    Recommenders may need to adapt to changes made by other recommenders.
    This function calls refresh() on each recommender to trigger such changes.
    :return:
    """
    try:
        rms = get_active_recommenders()
        for rm in get_active_recommenders():
            rm.refresh()
        return True

    except Exception:
        logging.exception("Error in recommender_functions.refresh_all_recommender()")


def active_recommenders_for_user(user):
    """
    returns a list of SiddataUserRecommender objects which are already initialized for a given user
    :param user: SiddataUser object
    :return: django queryset of SiddataUserRecommender objects
    """
    try:
        return models.SiddataUserRecommender.objects.filter(user=user)
    except Exception:
        logging.exception("Error in recommender_functions.get_active_recommenders_for_user()")


def active_recommender_classnames_for_user(user):
    """
    returns a list of recommender classnames which are active for a user
    :param user:
    :return: list of recommender classnames
    """
    try:
        lst_return = []
        for rm in active_recommenders_for_user(user):
            lst_return.append(rm.recommender.classname)
        return lst_return
    except Exception:
        logging.exception("Error in recommender_functions.active_recommender_classnames_for_user()")


def recommender_activated(user, rm_classname):
    """
    Check if a recommender is active for user
    :param user: SiddataUser object
    :param rm_classname: name of the recommender
    :return: bool
    """
    try:
        rm = models.SiddataUserRecommender.objects.get(
            user=user,
            recommender__classname=rm_classname,
        )
        exists = models.Goal.objects.filter(userrecommender=rm).exists()
        if exists:
            return True
    except models.SiddataUserRecommender.DoesNotExist as e:
        pass
    except Exception:
        logging.exception("Error in recommender_activated()")

    return False


def generate_p2_user_info(user):
    """
    Checks if a user's origin_id is known from prior p2 usage and generates an info activity if so.
    :param user: user to be checked
    :return: True, if user is known and activity was generated, False otherwise.
    """
    try:
        p2_users = pd.read_csv(filepath_or_buffer="{}/p2_data/p2_origin_ids.csv".format(settings.BASE_DIR),
                               sep=";",
                               )
        if str(user.user_origin_id) in set(p2_users["user_origin_id"]):
            rm_start = RM_start()
            goal = rm_start.get_default_goal(user)

            activity_data_info = models.Activity.objects.get_or_create(
                type="todo",
                title="Neue Version, neuer Start!",
                description="Siddata wurde grundlegend erneuert. Daher wurden alle Einstellungen und Daten alter "
                            "Versionen archiviert. Du kannst deine Rohdaten bei Bedarf bei uns anfragen und in "
                            "maschinenlesbarer Form erhalten. <br><br>Viel Spaß beim Erkunden der neuen Funktionen!",
                goal=goal,
                order=1,
                status="new",
                feedback_size=0,
                image="sid.png",
            )[0]
            return True
        else:
            return False
    except Exception:
        logging.exception("Error in recommender_functions.generate_p2_user_info()")

