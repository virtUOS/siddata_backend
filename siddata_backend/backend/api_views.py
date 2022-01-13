"""
api_views.py

"""
import base64
import logging
import datetime
import json
import hashlib
import os
import io

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseServerError, HttpResponseNotFound, JsonResponse
from django.core.files.images import ImageFile
from django.views.decorators.csrf import csrf_exempt

from recommenders import recommender_functions
from recommenders.RM_start import RM_start
from . import models
from siddata_backend import settings


# Flag for debugging features, if true, origin will not be checked and siddata runs on localhost stud.ip versions

def preprocess(func):
    def function_wrapper(*args, **kwargs):
        # check for api_keys
        # log recommender usage if user consent is given
        # check if origin is allowed or has to be created in debug mode

        if settings.DEBUG:
            return func(*args, **kwargs)
        request_data = args[0].GET
        if request_data['api_key'] == '':
            return HttpResponse("Invalid origin, empty api_key is not allowed", status=401)
        try:
            _ = models.Origin.objects.get(api_endpoint=request_data['origin'], api_key=request_data['api_key'])
        except ObjectDoesNotExist:
            logging.info('no origin object found')
            return HttpResponse("Invalid origin, not allowed", status=401)
        return func(*args, **kwargs)

    return function_wrapper


@csrf_exempt
@preprocess
def student(request):
    """Route that returns all data related to a SiddataUser.
    """
    if request.method == 'GET':

        request_data = request.GET

        origin = models.Origin.objects.get_or_create(
            api_endpoint=request_data['origin'],
        )[0]

        # Get_or_create user, check if user is new
        user, created = models.SiddataUser.objects.get_or_create(
            user_origin_id=request.GET['user_origin_id'],
            origin=origin)

        # If user was created (hence this request is the first for this user) the db is initialized
        if created:
            recommender_functions.create_initial_data_for_user(user)

        include_params = request.GET['include'].split(",")
        data_response = user.serialize(include=include_params)

        return JsonResponse(data_response, safe=False)

    if request.method == 'DELETE':

        origin = models.Origin.objects.get_or_create(
            api_endpoint=request.GET['origin']
        )[0]

        try:
            user = models.SiddataUser.objects.get(
                user_origin_id=request.GET['user_origin_id'],
                origin=origin
            )
        except models.SiddataUser.DoesNotExist:
            return HttpResponse("Nutzer existiert nicht.")

        user.delete()
        return HttpResponse("Nutzer wurde gelöscht.")

    if request.method == 'PATCH':
        request_data_json = json.loads(request.body)
        studi_json = request_data_json["data"]

        request_data = request.GET
        origin = models.Origin.objects.get_or_create(
            api_endpoint=request_data['origin'],
        )[0]

        user = models.SiddataUser.objects.get(user_origin_id=studi_json["id"], origin=origin)
        for attribute in studi_json["attributes"]:
            if attribute == "data_donation":
                user.data_donation = studi_json["attributes"][attribute]
            elif attribute == "gender_brain":
                user.gender_brain = studi_json["attributes"][attribute]
            elif attribute == "gender_social":
                user.gender_social = studi_json["attributes"][attribute]
            elif attribute == "data_regulations":
                user.data_regulations = studi_json["attributes"][attribute]
            else:
                logging.log("Unknown attribute in student PATCH route: {}".format(attribute))
        user.save()

        for institute_json in studi_json["relationships"]["institutes_brain"]["data"]:
            institute = models.Institute.objects.get(institute_origin_id=institute_json["id"], origin=origin)
            institutemembership = models.InstituteMembership.objects.get_or_create(
                institute=institute,
                user=user,
            )[0]
            institutemembership.share_brain = True
            institutemembership.save()

        for institute_json in studi_json["relationships"]["institutes_social"]["data"]:
            institute = models.Institute.objects.get(institute_origin_id=institute_json["id"], origin=origin)
            institutemembership = models.InstituteMembership.objects.get_or_create(
                institute=institute,
                user=user,
            )[0]
            institutemembership.share_social = True
            institutemembership.save()

        # respect rejected permissions
        for im in models.InstituteMembership.objects.filter(user=user):
            if im.institute.institute_origin_id not in [
                institute_json.get('id') for institute_json in studi_json["relationships"]["institutes_brain"]["data"]
            ]:
                im.share_brain = False
                im.save()
            if im.institute.institute_origin_id not in [
                institute_json.get('id') for institute_json in studi_json["relationships"]["institutes_social"]["data"]
            ]:
                im.share_social = False
                im.save()
            if not any([im.share_brain, im.share_social]):
                # according to data privacy guidelines, if a membership is not shared at all, it should be deleted
                im.delete()

        for course_json in studi_json["relationships"]["courses_brain"]["data"]:
            course = models.StudipCourse.objects.get(course_origin_id=course_json["id"], origin=origin)
            coursemembership = models.CourseMembership.objects.get_or_create(
                course=course,
                user=user,
            )[0]
            coursemembership.share_brain = True
            coursemembership.save()

        for course_json in studi_json["relationships"]["courses_social"]["data"]:
            course = models.InheritingCourse.objects.get(course_origin_id=course_json["id"], origin=origin)
            coursemembership = models.CourseMembership.objects.get_or_create(
                course=course,
                user=user,
            )[0]
            coursemembership.share_social = True
            coursemembership.save()

        # respect rejected permissions
        for cm in models.CourseMembership.objects.filter(user=user):
            if cm.course.course_origin_id not in [
                course_json.get('id') for course_json in studi_json["relationships"]["courses_brain"]["data"]
            ]:
                cm.share_brain = False
                cm.save()
            if cm.course.course_origin_id not in [
                course_json.get('id') for course_json in studi_json["relationships"]["courses_social"]["data"]
            ]:
                cm.share_social = False
                cm.save()
            if not any([cm.share_brain, cm.share_social]):
                # according to data privacy guidelines, if a membership is not shared at all, it should be deleted
                cm.delete()

        return HttpResponse("Die Nutzendendaten wurden gespeichert.")


@csrf_exempt
@preprocess
def recommender(request, recommender_id=None):
    """Route that returns all data related to a SiddataUserRecommender.
    """

    if request.method == 'GET':
        request_data = request.GET

        origin = models.Origin.objects.get_or_create(
            api_endpoint=request_data['origin'],
        )[0]

        # Get_or_create user, check it user is new
        user, created = models.SiddataUser.objects.get_or_create(
            user_origin_id=request_data["user_origin_id"],
            origin=origin)

        # If user was created (hence this request is the first for this user) the db is initialized
        if created:
            recommender_functions.create_initial_data_for_user(user)

        data_response = {}
        if recommender_id:
            userrecommender = models.SiddataUserRecommender.objects.get(id=recommender_id)
            data_response = userrecommender.serialize()
        else:
            data_response['data'] = []
            data_response['included'] = []
            recommenders = models.SiddataUserRecommender.objects.filter(user=user,
                                                                        recommender__active=True,).order_by("recommender__order")
            for rec in recommenders:
                r_ser = rec.serialize()
                data_response['data'] += r_ser['data']
                for i in r_ser['included']:
                    if not i in data_response['included']:
                        data_response['included'].append(i)
        return JsonResponse(data_response, safe=False)

    if request.method == 'PATCH':

        request_data = json.loads(request.body)
        recommenders = request_data["data"]
        start_recommender = RM_start()
        for recommender in recommenders:
            if recommender["type"] != "Recommender":
                return HttpResponseServerError("Recommender Object expected. Instead: {}".format(recommender))
            SUR = models.SiddataUserRecommender.objects.get(id=recommender["id"])
            SUR.enabled = recommender["attributes"]["enabled"]
            SUR.save()

            # if recommender is disabled or has been used before, continue..
            if SUR.enabled == False or models.Goal.objects.filter(userrecommender=SUR).exists():
                continue
            else:
                recommender_class_object = recommender_functions.create_recommender_by_classname(
                    SUR.recommender.classname)
                recommender_class_object.initialize(SUR.user)
                # Set teaser activity as done
                teaser_activity = recommender_class_object.get_teaser_activity(
                    start_recommender.get_default_goal(SUR.user))
                teaser_activity.status = "done"
                teaser_activity.save()

        return HttpResponse("Recommender-Einstellungen gespeichert.")


@csrf_exempt
@preprocess
def goal(request, goal_id=None):
    """Route that returns all data related to a Goal.
    """
    logger = logging.getLogger("api_goal")

    if request.method == 'GET':
        request_data = request.GET

        origin = models.Origin.objects.get_or_create(
            api_endpoint=request_data['origin'],
        )[0]

        user = models.SiddataUser.objects.get(origin=origin, user_origin_id=request.GET["user_origin_id"])

        data_response = {}
        if goal_id:
            goal = models.Goal.objects.get(id=goal_id)
            data_response = goal.serialize()
        else:
            data_response['data'] = []
            data_response['included'] = []
            goals = models.Goal.objects.filter(user=user).order_by("order")
            for g in goals:
                g_ser = g.serialize()
                data_response['data'] += g_ser['data']
                data_response['included'] += g_ser['included']

        return JsonResponse(data_response, safe=False)

    elif request.method == 'PATCH':
        request_data = json.loads(request.body)
        request_goal = request_data["data"]
        if request_goal["type"] != "Goal":
            return HttpResponseServerError("Sent object is not of type Goal!")
        try:
            goal = models.Goal.objects.get(id=goal_id)
        except models.Goal.DoesNotExist:
            return HttpResponseServerError("Goal with this ID not known.")
        except Exception as e:
            logger.error(e)
            return HttpResponseServerError()

        for key in request_goal["attributes"]:
            if key == "title":
                goal.title = request_goal["attributes"]["title"]
                goal.save()
            elif key == "description":
                goal.description = request_goal["attributes"]["description"]
                goal.save()
            elif key == "order":
                goal.order = request_goal["attributes"]["order"]
                goal.save()
        return HttpResponse("Ziel wurde bearbeitet.")

    elif request.method == 'DELETE':
        try:
            goal = models.Goal.objects.get(id=goal_id)
        except models.Goal.DoesNotExist:
            return HttpResponseServerError("Goal with this ID not known.")
        except Exception as e:
            logger.error(e)
            return HttpResponseServerError()
        goal.delete()
        return HttpResponse("Ziel wurde gelöscht.")


@csrf_exempt
@preprocess
def activity(request, activity_id=None):
    """Route that returns an Activity..
    """
    logger = logging.getLogger("api_activity")

    if request.method == 'GET':
        request_data = request.GET

        origin_id = request_data['user_origin_id']

        origin = models.Origin.objects.get_or_create(
            api_endpoint=request_data['origin'],
        )[0]

        user = models.SiddataUser.objects.get(origin=origin, user_origin_id=origin_id)

        data_response = {}
        if activity_id:
            act_obj = models.Activity.objects.get(id=activity_id)
            data_response = act_obj.serialize()
        else:
            data_response['data'] = []
            data_response['included'] = []
            act_objs = models.Activity.objects.filter(goal__user=user)
            for act in act_objs:
                a_ser = act.serialize()
                data_response['data'] += a_ser['data']
                data_response['included'] += a_ser['included']

        return JsonResponse(data_response, safe=False)

    elif request.method == 'PATCH':
        request_data = json.loads(request.body)
        request_activity = request_data["data"]

        if request_activity["type"] != "Activity":
            return HttpResponseServerError("Sent object is not of type Activity!")

        try:
            activity = models.Activity.objects.get(id=activity_id)
            # activity = models.Activity.objects.get(id=request_activity['id'])
        except models.Activity.DoesNotExist:
            return HttpResponseServerError("Activity with this ID not known.")
        except Exception as e:
            logger.error(e)
            return HttpResponseServerError()

        # flags for special cases
        feedback = False
        status = False
        answer = False

        for key in request_activity["attributes"]:
            if key == "title":
                activity.title = request_activity["attributes"]["title"]
            elif key == "description":
                activity.description = request_activity["attributes"]["description"]
            elif key == "status":
                if activity.status == "immortal":
                    continue
                # If status has changed..
                elif activity.status != request_activity["attributes"]["status"]:

                    # ..set new status..
                    activity.status = request_activity["attributes"]["status"]
                    activity.save()
                    # If the reason for the request was a finalization:
                    if activity.status == "done":
                        status = True
                    elif activity.status == "discarded":
                        return HttpResponse("Activity verworfen.")
                    elif activity.status == "snoozed":
                        return HttpResponse("Activity pausiert.")
                    elif activity.status == "active":
                        return HttpResponse("Activity reaktiviert.")

            elif key == "answers":
                activity.answers = request_activity["attributes"]["answers"]
                if activity.status != "immortal":
                    activity.status = "done"
                activity.save()
                answer = True
            elif key == "feedback_value":
                activity.feedback_value = request_activity["attributes"]["feedback_value"]
                activity.save()
                feedback = True
            elif key == "feedback_text":
                activity.feedback_text = request_activity["attributes"]["feedback_text"]
                activity.save()
                feedback = True
            elif key == "feedback_chdate":
                Date = datetime.datetime.fromtimestamp(request_activity["attributes"]["feedback_chdate"],
                                                       datetime.timezone.utc)
                activity.feedback_chdate = Date
                activity.save()
            elif key == "notes":
                activity.notes = request_activity["attributes"]["notes"]
                activity.save()
            elif key == "duedate":
                Date = datetime.datetime.fromtimestamp(request_activity["attributes"]["duedate"], datetime.timezone.utc)
                activity.duedate = Date
                activity.save()
            elif key == "order":
                activity.order = request_activity["attributes"]["order"]
                activity.save()
            elif key == "chdate":
                Date = datetime.datetime.fromtimestamp(request_activity["attributes"]["chdate"], datetime.timezone.utc)
                activity.chdate = Date
                activity.save()
            elif key == "activation_time":
                Date = datetime.datetime.fromtimestamp(request_activity["attributes"]["activation_time"],
                                                       datetime.timezone.utc)
                activity.activation_time = Date
                activity.save()
            elif key == "deactivation_time":
                Date = datetime.datetime.fromtimestamp(request_activity["attributes"]["deactivation_time"],
                                                       datetime.timezone.utc)
                activity.deactivation_time = Date
                activity.save()
            elif key == "interactions":
                activity.interactions = request_activity["attributes"]["interactions"]
                activity.save()
            else:
                pass

        # If the changes only were a feedback change which does not finalize the activity...
        if feedback and (not status and not answer):
            # Send response to frontend and thereby end function call.
            return HttpResponse("Feedback wurde gespeichert.")

        rm_classname = activity.goal.userrecommender.recommender.classname
        rm = recommender_functions.create_recommender_by_classname(rm_classname)

        feedback = rm.process_activity(activity=activity)

        recommender_functions.refresh_all_recommenders()

        if feedback == None or feedback == True:
            feedback = activity.respond()

        return HttpResponse(feedback)

    elif request.method == 'DELETE':
        try:
            activity = models.Activity.objects.get(id=activity_id)
        except models.Activity.DoesNotExist:
            return HttpResponseServerError("Activity with this ID not known.")
        except Exception as e:
            logger.error(e)
            return HttpResponseServerError()
        activity.delete()
        return HttpResponse("Empfehlung wurde gelöscht.")


@csrf_exempt
@preprocess
def coursemembership(request):
    """

    :param request:
    :return:
    """

    return HttpResponse("Kursteilnahme wurde gespeichert.")


@csrf_exempt
@preprocess
def institutemembership(request):
    """

    :param request:
    :return:
    """

    return HttpResponse("Institutszugehörigkeit wurde gespeichert.")


@csrf_exempt
@preprocess
def studycourse(request):
    """

    :param request:
    :return:
    """
    if request.method == 'GET':
        request_data = request.GET

        user = models.SiddataUser.objects.get(user_origin_id=request_data["user_origin_id"])
        studycourses = models.SiddataUserStudy.objects.filter(
            user=user,
        )
        data_response = {"data": []}
        for studycourse in studycourses:
            data_response["data"] += studycourse.serialize()["data"]

        return JsonResponse(data_response, safe=False)

    elif request.method == 'POST':
        request_data_head = request.GET
        origin = models.Origin.objects.get_or_create(
            api_endpoint=request_data_head['origin'],
        )[0]

        request_data = json.loads(request.body)

        users_scs = models.SiddataUserStudy.objects.filter(
            user=models.SiddataUser.objects.get(user_origin_id=request.GET['user_origin_id'])
        )

        # handle empty requests
        if not request_data["data"]:
            # according to data privacy guidelines, if a studycourse is not shared at all, it should be deleted
            for sc in users_scs:
                sc.delete()
            return HttpResponse("Studieninformationen wurden gespeichert.")

        # now handle existing studycourses, which are missing in the submitted data
        submitted_ids = [entry.get('attributes')['studip_id'] for entry in request_data["data"]]
        for sc in users_scs:
            if sc.studycourse_origin_id not in submitted_ids:
                # according to data privacy guidelines, if a studycourse is not shared at all, it should be deleted
                sc.delete()

        for entry in request_data["data"]:

            if entry["attributes"]["share_semester_brain"] == True or entry["attributes"]["share_semester_social"]:
                semester = entry["attributes"]["semester"]
            else:
                semester = None

            if entry["attributes"]["share_degree_brain"] or entry["attributes"]["share_degree_social"]:
                degree = models.Degree.objects.get(degree_origin_id=entry["relationships"]["degree"]["data"][0]["id"],
                                                   origin=origin)
            else:
                degree = None

            if entry["attributes"]["share_subject_brain"] == True or entry["attributes"]["share_subject_social"]:
                subject = models.Subject.objects.get(
                    subject_origin_id=entry["relationships"]["subject"]["data"][0]["id"], origin=origin)
            else:
                subject = None

            user = models.SiddataUser.objects.get(user_origin_id=entry["relationships"]["user"]["data"][0]["id"],
                                                  origin=origin)

            # handle existing studycourses, which do occur in the submitted data
            existing_scs = models.SiddataUserStudy.objects.filter(
                studycourse_origin_id=entry["attributes"]["studip_id"])
            if existing_scs:
                for sc in existing_scs:
                    sc.share_subject_brain = entry["attributes"]["share_subject_brain"]
                    sc.share_subject_social = entry["attributes"]["share_subject_social"]
                    sc.share_degree_brain = entry["attributes"]["share_degree_brain"]
                    sc.share_degree_social = entry["attributes"]["share_degree_social"]
                    sc.share_semester_brain = entry["attributes"]["share_semester_brain"]
                    sc.share_semester_social = entry["attributes"]["share_semester_social"]
                    sc.save()

                    if not any([
                        sc.share_subject_brain,
                        sc.share_subject_social,
                        sc.share_degree_brain,
                        sc.share_degree_social,
                        sc.share_semester_brain,
                        sc.share_semester_social
                    ]):
                        # according to data privacy guidelines, if a studycourse is not shared at all, it should be deleted
                        sc.delete()
            else:
                # studycourse is new
                studycourse = models.SiddataUserStudy.objects.get_or_create(
                    user=user,
                    degree=degree,
                    subject=subject,
                    semester=semester,
                    studycourse_origin_id=entry["attributes"]["studip_id"],
                    share_subject_brain=entry["attributes"]["share_subject_brain"],
                    share_subject_social=entry["attributes"]["share_subject_social"],
                    share_degree_brain=entry["attributes"]["share_degree_brain"],
                    share_degree_social=entry["attributes"]["share_degree_social"],
                    share_semester_brain=entry["attributes"]["share_semester_brain"],
                    share_semester_social=entry["attributes"]["share_semester_social"],
                )[0]
                studycourse.save()

        return HttpResponse("Studieninformationen wurden gespeichert.")


@csrf_exempt
@preprocess
def subject(request):
    """
    Function is called by the Stud.IP plugin Cronjob via POST request to send subject data.
    :param request: Django request object
    :return: HttpResponse object or HttpResponseServerError object
    """
    logger = logging.getLogger('api_subject')
    try:
        origin = models.Origin.objects.get_or_create(
            api_endpoint=request.GET['origin'],
        )[0]
    except Exception as e:
        logger.error(e)
        return HttpResponseServerError(e)

    if request.method == "POST":
        try:
            request_data = json.loads(request.body)
            for entity in request_data["data"]:
                if entity["type"] == "Subject":
                    if models.Subject.is_valid_data(entity):
                        subject_object = models.Subject.objects.update_or_create(
                            name=entity["attributes"]["name"],
                            description=entity["attributes"]["description"],
                            keywords=entity["attributes"]["keywords"],
                            origin=origin,
                            subject_origin_id=entity["attributes"]["studip_id"],
                        )[0]
                        subject_object.save()
                    else:
                        logger.error("Subject JSON formatting error: {}".format(entity))

        except Exception as e:
            logger.error(e)
            return HttpResponseServerError(e)

        return HttpResponse("Studiengang wurde gespeichert.")


@csrf_exempt
@preprocess
def course(request, course_origin_id=None):
    """
    Function is called by the Stud.IP plugin Cronjob via POST request to send course data.
    :param request: Django request object
    :return: HttpResponse object or HttpResponseServerError object
    """
    logger = logging.getLogger('api_course')
    try:
        origin = models.Origin.objects.get_or_create(
            api_endpoint=request.GET['origin'],
        )[0]
    except Exception as e:
        logger.error(e)
        return HttpResponseServerError(e)

    if request.method == "POST":
        try:
            request_data = json.loads(request.body)
            for entity in request_data["data"]:
                if entity["type"] == "Course":
                    if not models.StudipCourse.is_valid_data(entity):
                        logger.error("Invalid Course JSON. {}".format(entity))
                    else:
                        date_str = datetime.datetime.fromtimestamp(
                            entity["attributes"]["start_time"],
                            datetime.timezone.utc
                        ).strftime("%a %d.%m%y")
                        if date_str is None:
                            date_str = ""

                        place_str = entity["attributes"]["place"] \
                            if "place" in entity["attributes"].keys() and entity["attributes"][
                            "place"] is not None else ""

                        rel_inst = None
                        if 'relationships' in entity.keys() \
                                and 'institute' in entity['relationships'].keys() \
                                and entity['relationships']['institute']['data'][0]['id']:
                            try: rel_inst = models.Institute.objects.get(
                                    institute_origin_id=entity['relationships']['institute']['data'][0]['id'],
                                    origin=origin
                                )
                            except models.Institute.DoesNotExist as e:
                                logger.error(e)

                        course_object, created = models.StudipCourse.objects.update_or_create(
                            identifier=hashlib.sha256(
                                (str(origin.id) + entity["attributes"]["studip_id"]).encode('utf-8')
                            ).hexdigest(),
                            origin=origin,
                            course_origin_id=entity["attributes"]["studip_id"],
                            defaults={
                                "contributor": [],
                                "coverage": date_str + " " + place_str,
                                "creator": {},
                                "date": datetime.datetime.fromtimestamp(entity["attributes"]["start_time"],
                                                                        datetime.timezone.utc),
                                "description": entity["attributes"]["description"],
                                "format": ['CRS'],
                                "language": "",
                                "place": entity["attributes"]["place"],
                                "publisher": origin.name,
                                "relation": None,
                                "rights": None,
                                "start_time": datetime.datetime.fromtimestamp(entity["attributes"]["start_time"],
                                                                              datetime.timezone.utc),
                                "end_time": datetime.datetime.fromtimestamp(entity["attributes"]["end_time"],
                                                                            datetime.timezone.utc),
                                "start_semester": entity["attributes"]["start_semester"],
                                "end_semester": entity["attributes"]["end_semester"],
                                "source": entity["attributes"]["url"],
                                "subject": [],  # TODO
                                "title": entity["attributes"]["name"],
                                "type": ['SIP'],
                                "institute": rel_inst
                            },
                        )

                        if 'relationships' in entity.keys() \
                                and 'lecturers' in entity['relationships'].keys() \
                                and entity['relationships']['lecturers']['data']:
                            for lecturer in entity['relationships']['lecturers']['data']:
                                try:
                                    lecturer_object = models.Lecturer.objects.get(origin=origin,
                                                                                  person_origin_id=lecturer['id'])
                                    cl, created = models.CourseLecturer.objects.update_or_create(
                                        course=course_object,
                                        lecturer=lecturer_object
                                    )
                                    cl.save()
                                except models.Lecturer.DoesNotExist:
                                    logger.error(
                                        f"Lecturer from origin {origin.name} with id {lecturer['id']} not found!")

        except Exception as e:
            logger.error(e)
            return HttpResponseServerError(e)

        return HttpResponse("Kurs wurde gespeichert")

    elif request.method == "GET":
        logger.debug("GET course")
        if course_origin_id:
            try:
                logger.debug("course by origin_id")
                courses = [models.StudipCourse.objects.get(course_origin_id=course_origin_id, origin=origin)]
            except Exception as e:
                logger.error(e)
                return HttpResponseNotFound(e)
        else:
            logger.debug("Only origin course query")
            courses = models.InheritingCourse.objects.filter(origin=origin)

        response_data = {"data": []}

        for c in courses:
            response_data["data"] += c.serialize()["data"]

        return JsonResponse(response_data, safe=False)


@csrf_exempt
@preprocess
def degree(request):
    """
    Function is called by the Stud.IP plugin Cronjob via POST request to send degree data.
    :param request: Django request object
    :return: HttpResponse object or HttpResponseServerError object
    """
    logger = logging.getLogger('api_degree')
    try:
        origin = models.Origin.objects.get_or_create(
            api_endpoint=request.GET['origin'],
        )[0]
    except Exception as e:
        logger.error(e)
        return HttpResponseServerError(e)

    if request.method == "POST":
        try:
            request_data = json.loads(request.body)
            for entity in request_data["data"]:
                if entity["type"] == "Degree":
                    if not models.Degree.is_valid_data(entity):
                        logger.error("Invalid Degree JSON. {}".format(entity))
                    else:
                        degree_object = models.Degree.objects.update_or_create(
                            name=entity["attributes"]["name"],
                            description="{}".format(entity["attributes"]["description"]),
                            origin=origin,
                            degree_origin_id=entity["attributes"]["studip_id"],
                        )[0]
                        degree_object.save()
        except Exception as e:
            logger.error(e)
            return HttpResponseServerError(e)

        return HttpResponse("Abschluss wurde gespeichert.")


@csrf_exempt
@preprocess
def event(request):
    logger = logging.getLogger('api_event')
    """
    Function is called by the Stud.IP plugin Cronjob via POST request to send event data.
    :param request: Django request object
    :return: HttpResponse object or HttpResponseServerError object
    """
    logger.debug('New event request received')
    logger.debug(str(request))
    try:
        origin = models.Origin.objects.get_or_create(
            api_endpoint=request.GET['origin'],
        )[0]
    except Exception as e:
        logger.debug("Establishing API Endpoint for Event failed.")
        return HttpResponseServerError(e)

    if request.method == "POST":
        logger.debug("New event POST request received")
        try:
            logger.debug("Attempting to load body")
            request_data = json.loads(request.body)
            for entity in request_data["data"]:
                if entity["type"] == "Event":
                    if not models.StudipEvent.is_valid_data(entity):
                        logger.error("Invalid Event JSON. {}".format(entity))
                    else:
                        try:
                            course_obj = models.StudipCourse.objects.get(
                                course_origin_id=entity["relationships"]["course"]["data"][0]["id"], origin=origin)
                        except models.StudipCourse.DoesNotExist:
                            logger.debug(
                                "Course not found for ID: " + "\n" + entity['relationships']['course']['data'][0][
                                    'id'] + " !")
                            continue

                        date_str = datetime.datetime.fromtimestamp(
                            entity["attributes"]["start_time"],
                            datetime.timezone.utc
                        ).strftime("%a %d.%m%y")
                        if date_str is None:
                            date_str = ""

                        attr_keys = entity["attributes"].keys()

                        place_str = entity["attributes"]["place"] \
                            if "place" in attr_keys and entity["attributes"][
                            "place"] is not None else ""

                        if "topic_title" in attr_keys and entity["attributes"]["topic_title"] is not None:
                            title = entity["attributes"]["topic_title"]
                            if title == 'Ohne Titel':
                                continue
                        else:
                            continue

                        event_object, created = models.StudipEvent.objects.update_or_create(
                            identifier=entity["attributes"]["studip_id"],
                            event_origin_id=entity["attributes"]["studip_id"],
                            origin=origin,
                            course=course_obj,
                            defaults={
                                "contributor": [],
                                "coverage": date_str + " " + place_str,
                                "creator": {},
                                "date": datetime.datetime.fromtimestamp(entity["attributes"]["start_time"],
                                                                        datetime.timezone.utc) if "start_time" in attr_keys else None,
                                "description": entity["attributes"][
                                    "topic_description"] if "topic_description" in attr_keys else None,
                                "format": ['CRS'],
                                "language": "",
                                "publisher": origin.name,
                                "relation": None,
                                "rights": None,
                                "start_time": datetime.datetime.fromtimestamp(entity["attributes"]["start_time"],
                                                                              datetime.timezone.utc),
                                "end_time": datetime.datetime.fromtimestamp(entity["attributes"]["end_time"],
                                                                            datetime.timezone.utc),
                                "source": entity["attributes"]["url"] if "url" in attr_keys else None,
                                "subject": [],  # TODO
                                "title": title,
                                "type": ['SIP']
                            }
                        )
                        event_object.save()
                else:
                    logger.error("Type error!")
                    raise TypeError("This data type is not supported: %s" % entity["type"])

        except Exception as e:
            logger.error(e)
            return HttpResponseServerError(e)

        return HttpResponse("Veranstaltung wurde gespeichert.")


@csrf_exempt
@preprocess
def institute(request):
    """
    Function is called by the Stud.IP plugin Cronjob via POST request to send institute data.
    :param request: Django request object
    :return: HttpResponse object or HttpResponseServerError object
    """
    logger = logging.getLogger('api_institute')
    try:
        origin = models.Origin.objects.get_or_create(
            api_endpoint=request.GET['origin'],
        )[0]
    except Exception as e:
        logger.error(e)
        return HttpResponseServerError(e)

    if request.method == "POST":
        try:
            request_data = json.loads(request.body)
            for entity in request_data["data"]:
                if entity["type"] == "Institute":
                    if not models.Institute.is_valid_data(entity):
                        logger.error("Invalid Institute JSON. {}".format(entity))
                    else:
                        institute_object = models.Institute.objects.update_or_create(
                            name=entity["attributes"]["name"],
                            url=entity["attributes"]["url"],
                            origin=origin,
                            institute_origin_id=entity["attributes"]["studip_id"],
                        )[0]
                        institute_object.save()
                else:
                    logger.error("Type error!")
                    raise TypeError("This data type is not supported: %s" % entity["type"])

            if len(request_data["data"]) == 0:
                return HttpResponse("Keine Einrichtung wurde gespeichert.")
        except Exception as e:
            logger.error(e)
            return HttpResponseServerError(e)

        return HttpResponse("Einrichtung wurde gespeichert.")


@csrf_exempt
@preprocess
def person(request):
    """
    Function is called by the Stud.IP plugin Cronjob via POST request to send staff data.
    :param request:
    :return:
    """
    logger = logging.getLogger('api_person')
    try:
        origin = models.Origin.objects.get_or_create(
            api_endpoint=request.GET['origin'],
        )[0]
    except Exception as e:
        logger.error(e)
        return HttpResponseServerError(e)

    if request.method == "POST":
        try:
            request_data = json.loads(request.body)
            activity = None
            if "relationships" in request_data.keys() and "activity" in request_data["relationships"].keys():
                activity_id = request_data["relationships"]["activity"]["data"][0]["id"]
                try:
                    activity = models.Activity.objects.get(id=activity_id)
                except models.Activity.DoesNotExist:
                    pass
            for entity in request_data["data"]:
                if entity['type'] == 'Person' or entity['type'] == 'Lecturer':
                    if not models.Person.is_valid_data(entity):
                        logger.error("Invalid Person JSON. {}".format(entity))
                    else:
                        attr_keys = entity['attributes'].keys()

                        user = None
                        if 'user_origin_id' in attr_keys:
                            try:
                                user = models.SiddataUser.objects.get(
                                    user_origin_id=entity['attributes']['user_origin_id'],
                                    origin=origin
                                )
                            except models.SiddataUser.DoesNotExist:
                                pass

                        defaults = {
                            'first_name': entity['attributes']['first_name'] if 'first_name' in attr_keys else None,
                            'surname': entity['attributes']['surname'] if 'surname' in attr_keys else None,
                            'title': entity['attributes']['title'] if 'title' in attr_keys else None,
                            'url': entity['attributes']['url'] if 'url' in attr_keys else None,
                            'role_description': entity['attributes']['description'] if 'description' in attr_keys else None,
                            'user': user
                        }

                        if 'image' in attr_keys:
                            person_image = None
                            if entity['attributes']['image'] is not None:
                                person_image = ImageFile(
                                    io.BytesIO(
                                        base64.decodebytes(
                                            bytes(
                                                entity['attributes']['image'],
                                                'utf-8'
                                            )
                                        )
                                    ),
                                    name=entity['attributes']['image_name'] if 'image_name' in attr_keys else None
                                )
                            defaults['image'] = person_image

                        person_object = None
                        if entity['type'] == 'Lecturer' and 'person_origin_id' in attr_keys and entity['attributes']['person_origin_id']:
                            defaults['email'] = entity['attributes']['email'] if 'email' in attr_keys else None
                            person_object, created = models.Lecturer.objects.update_or_create(
                                origin=origin,
                                person_origin_id=entity['attributes']['person_origin_id'],
                                defaults=defaults
                            )
                        elif entity['type'] == 'Person':
                            if activity is not None and activity.person is not None:
                                person_object = activity.person
                                defaults['email'] = entity['attributes']['email'] if 'email' in attr_keys else None
                                for attr, value in defaults.items():
                                    setattr(person_object, attr, value)
                            else:
                                person_object, created = models.Person.objects.update_or_create(
                                    email=entity['attributes']['email'],
                                    defaults=defaults
                                )
                        if person_object is not None:
                            person_object.save()

                            if 'relationships' in entity.keys() \
                                    and entity['type'] == 'Lecturer' \
                                    and 'institutes' in entity['relationships'].keys() \
                                    and entity['relationships']['institutes']['data']:
                                for institute in entity['relationships']['institutes']['data']:
                                    try:
                                        institute_object = models.Institute.objects.get(origin=origin,
                                                                                        institute_origin_id=institute['id'])
                                        li, created = models.LecturerInstitute.objects.update_or_create(
                                            institute=institute_object,
                                            lecturer=person_object
                                        )
                                        li.save()
                                    except models.Lecturer.DoesNotExist:
                                        logger.error(
                                            f"Institute from origin {origin.name} with id {institute['id']} not found!")

                else:
                    logger.error("Type error!")
                    raise TypeError("This data type is not supported: %s" % entity["type"])
            if len(request_data["data"]) == 0:
                return HttpResponse("Keine Einrichtung wurde gespeichert.")
        except Exception as e:
            logger.error(e)
            return HttpResponseServerError(e)

        return HttpResponse("Einrichtung wurde gespeichert.")


@preprocess
def extract_object_from_included(object_type, object_id, included):
    """ Helper function that retrieves a specific object.
    @:param type String that represents the object class.
    @:param id   String that represents the id of the object.
    @:param List of objects.
    @:return object in JSON or None
    """
    for object in included:
        if object["type"] == object_type and object["id"] == object_id:
            return object
    return None
