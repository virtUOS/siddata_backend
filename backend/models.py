import datetime
import logging
import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.core.mail import send_mail
from django.db.models import JSONField
from languages.fields import LanguageField
from model_utils import Choices

import settings
import recommenders


class Origin(models.Model):
    """
    Represents a Stud.IP instance from which requests originate.
    """

    #: Unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #: Name.
    name = models.CharField(max_length=128, default="default")
    #: The physical location of the origin, e.g. "Osnabrück".
    location = models.CharField(max_length=32, default="planet earth")
    #: Type.
    type = models.CharField(max_length=32, default="tests")
    #: Functional identifier.
    api_endpoint = models.CharField(max_length=128)
    #: A secret API key used for authentication.
    api_key = models.CharField(max_length=128, default='')

    def __str__(self):
        """String representation of an Origin object."""
        return "Origin: {} {}".format(self.name, self.api_endpoint)


class Degree(models.Model):
    """Represents various degrees, such as Bachelor, Master, ..."""

    #: Unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #: Name.
    name = models.CharField(max_length=128)
    #: Textual description.
    description = models.CharField(max_length=256, null=True)
    #: The origin providing this degree.
    origin = models.ForeignKey(Origin, on_delete=models.CASCADE)
    #: The ID of the degree in the origin's database.
    degree_origin_id = models.CharField(max_length=256)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["degree_origin_id", "origin"], name="unique_origin_degree"),
        ]

    def __str__(self):
        """String representation of a Degree object."""
        return "Degree {} {}".format(self.name, self.origin.name)

    @staticmethod
    def is_valid_data(entity):
        """
        Checks if a json string is a valid Degree representation.
        :param entity: json data
        :return: Boolean
        """

        if entity["type"] == "Degree":
            if (entity["attributes"]["studip_id"] is None
                    or entity["attributes"]["name"] is None):
                return False
            else:
                return True
        else:
            return False

    def serialize(self):
        """
        Serializes a Degree object to a json string ready for JSON-API-conform submission.
        :param include: If true, related objects will be included.
        :return: json-ready dict
        """
        response_data = {
            "data": [{
                "type": "Degree",
                "id": self.id,
                "attributes": {
                    "name": self.name,
                    "description": self.description,
                    "origin": self.origin.name,
                    "origin_id": self.degree_origin_id,
                }
            }]
        }

        return response_data


class Subject(models.Model):
    """
    Represents a course of study (subject), like 'Informatik', 'Cognitive Science'.
   The name field uses the local name at student's origin institution.
   Subjects are linked via references to official ids from Destatis
   (https://www.destatis.de/DE/Methoden/Klassifikationen/BildungKultur/StudentenPruefungsstatistik.html).
   """

    #: Unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #: Name.
    name = models.CharField(max_length=128)
    #: Textual description.
    description = models.CharField(max_length=1024, null=True)
    #: Keywords for categorizing this subject.
    keywords = models.CharField(max_length=256, null=True)
    #: The origin providing this subject.
    origin = models.ForeignKey(Origin, on_delete=models.CASCADE)
    #: The ID of the subject in the origin's database.
    subject_origin_id = models.CharField(max_length=128)
    #: Subject ID from the German Federal Office of Statistics (Statistisches Bundesamt).
    destatis_subject_id = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["subject_origin_id", "origin"], name="unique_origin_subject"),
        ]

    @staticmethod
    def is_valid_data(entity):
        """
        Checks if a json string is a valid Subject representation.
        :param entity: json data
        :return: Boolean
        """

        if entity["type"] == "Subject":
            if (entity["attributes"]["studip_id"] is None
                    or entity["attributes"]["name"] is None):
                return False
            else:
                return True
        else:
            return False

    def __str__(self):
        """String representation of a Subject object."""
        return "Subject {} {}".format(self.name, self.origin.name)


class SiddataUser(models.Model):
    """
    A user of the Siddata Study Assistant (not a user for the django app frontend)
    """

    #: Unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #: The origin from which this user accesses Siddata.
    origin = models.ForeignKey(Origin, on_delete=models.CASCADE)
    #: The pseudonymized ID of the user in the origin's database.
    user_origin_id = models.CharField(max_length=128)
    #: The gender shared for analysis purposes.
    gender_brain = models.CharField(max_length=256, null=True)
    #: The gender shared with other users.
    gender_social = models.CharField(max_length=256, null=True)
    #: If true, the user agreed that usage data can be retrieved and used for analysis purposes.
    data_donation = models.BooleanField(default=False)
    #: Specific settings for data usage configured by the user.
    data_regulations = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user_origin_id", "origin"], name="unique_origin_user"),
        ]

    def __str__(self):
        """String representation of a SiddataUser object."""
        return "SiddataUser {} {}".format(self.id, self.origin.name)

    def serialize(self, include=[]):
        """
        Converts SiddataUser instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :param include: List of fields to include in the response.
        :return: data Dictionary with nested data.
        """

        recommenders = []
        included = []
        userrecommenders = SiddataUserRecommender.objects.filter(user=self,
                                                                 recommender__active=True).order_by("recommender__order")
        for userrecommender in userrecommenders:
            recommenders.append({"id": userrecommender.id, "type": "Recommender"})
            if 'recommenders' in include:
                r_ser = userrecommender.serialize()
                for entry in r_ser["data"] + r_ser["included"]:
                    if entry not in included:
                        included.append(entry)

        response_data = {
            "data": [{
                "type": "SiddataUser",
                "id": self.id,
                "attributes": {
                    "origin": self.origin.name,
                    "user_origin_id": self.user_origin_id,
                    "data_donation": self.data_donation,
                    "gender_brain": self.gender_brain,
                    "gender_social": self.gender_social,
                },
                "relationships": {
                    "recommenders": {
                        "data": recommenders
                    }
                }
            }],
        }

        courses_brain = 'courses_brain' in include
        courses_social = 'courses_social' in include
        if courses_brain or courses_social:
            cms = CourseMembership.objects.filter(user=self)
            if courses_brain:
                response_data['data'][0]['relationships']['courses_brain'] = {
                    "data": []
                }
            if courses_social:
                response_data['data'][0]['relationships']['courses_social'] = {
                    "data": []
                }

            for cm in cms:
                relationship = {
                    "type": "StudipCourse",
                    "id": cm.course.course_origin_id
                }
                if cm.share_brain and courses_brain:
                    response_data['data'][0]['relationships']['courses_brain']["data"].append(
                        relationship
                    )
                if cm.share_social and courses_social:
                    response_data['data'][0]['relationships']['courses_social']["data"].append(
                        relationship
                    )

        institutes_brain = 'institutes_brain' in include
        institutes_social = 'institutes_social' in include
        if institutes_brain or institutes_social:
            ims = InstituteMembership.objects.filter(user=self)
            if institutes_brain:
                response_data['data'][0]['relationships']['institutes_brain'] = {
                    "data": []
                }
            if institutes_social:
                response_data['data'][0]['relationships']['institutes_social'] = {
                    "data": []
                }

            for im in ims:
                relationship = {
                    "type": "StudipInstitute",
                    "id": im.institute.institute_origin_id
                }
                if im.share_brain and institutes_brain:
                    response_data['data'][0]['relationships']['institutes_brain']["data"].append(
                        relationship
                    )
                if im.share_social and institutes_social:
                    response_data['data'][0]['relationships']['institutes_social']["data"].append(
                        relationship
                    )

        if len(include) > 0:
            response_data["included"] = included

        return response_data

    def get_property(self, key):
        """
        Get a user's property identified by key.

        This encapsulates the user property handling with UserProperty objects.
        :return: The key's value is a string or None if key is not set."""
        UPs = UserProperty.objects.filter(user=self, key=key)
        if len(UPs) == 0:
            return None
        elif len(UPs) == 1:
            return UPs[0].value
        else:
            logging.warning("UserProperty not unique! User: {}, Key: {}".format(self.id, key))
            return None

    def set_property(self, key, value):
        """Sets or updates a goal  property."""
        (p, created) = UserProperty.objects.get_or_create(user=self, key=key)
        p.value = value
        p.save()


class UserProperty(models.Model):
    """
    A UserProperty specifies a User. For example: key=age, value=42
    Permissions to use data are also stored here.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(SiddataUser, on_delete=models.CASCADE, default=None)
    key = models.CharField(max_length=64)
    value = JSONField(null=True)

    def __str__(self):
        """String representation of a UserProperty object."""
        return "UserProperty {}".format(self.key)


class SiddataUserStudy(models.Model):
    """
    Represents one subject for one student:
    Student id, degree, subject and semester. One student can have many SiddataUserStudy entries.
    Examples:
        - Bachelor Informatik, 3. Semester
        - 2-Fächer-Bachelor Latein, 14. Semester
        - Juristisches Staatsexamen Jura, 1. Semester
    """

    #: Unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #: The ID of the study course in the origin system.
    studycourse_origin_id = models.CharField(max_length=512, null=True)
    #: The user which is applied to this study course.
    user = models.ForeignKey(SiddataUser, on_delete=models.CASCADE)  # references entry in SiddataUser table
    #: The degree the study course results in.
    degree = models.ForeignKey(Degree, on_delete=models.CASCADE, null=True)  # the prospective degree
    #: The major subject of this study course.
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True)  # the subject
    #: The current semester of the user in this study course.
    semester = models.IntegerField(null=True)  # the semester for this subject
    #: True, if the user agrees to share the subject for analysis purposes.
    share_subject_brain = models.BooleanField(default=False)
    #: True, if the user agrees to share the subject with other users.
    share_subject_social = models.BooleanField(default=False)
    #: True, if the user agrees to share the degree for analysis purposes.
    share_degree_brain = models.BooleanField(default=False)
    #: True, if the user agrees to share the degree with other users.
    share_degree_social = models.BooleanField(default=False)
    #: True, if the user agrees to share the semester for analysis purposes.
    share_semester_brain = models.BooleanField(default=False)
    #: True, if the user agrees to share the semester with other users.
    share_semester_social = models.BooleanField(default=False)

    def __str__(self):
        """String representation of a SiddataUserStudy object."""
        if self.subject is not None and self.degree is not None:
            return "SiddataUserStudy {} {} {} {}".format(self.user.id, self.degree.name, self.subject.name,
                                                         self.semester)
        else:
            return "SiddataUserStudy {} {}".format(self.user.id, self.semester)

    def serialize(self):
        """
        Serializes a Degree object to a json string ready for JSON-API-conform submission.
        :return: json-ready dict
        """
        response_data = {
            "data": [{
                "type": "SiddataUserStudy",
                "id": self.id,
                "attributes": {
                    "studip_id": self.studycourse_origin_id,
                    "semester": self.semester,
                    "share_subject_brain": self.share_subject_brain,
                    "share_subject_social": self.share_subject_social,
                    "share_degree_brain": self.share_degree_brain,
                    "share_degree_social": self.share_degree_social,
                    "share_semester_brain": self.share_semester_brain,
                    "share_semester_social": self.share_semester_social,
                },
                "relationships": {
                },
            }],
        }
        return response_data


class Recommender(models.Model):
    """
    Represents a recommender
    """
    #: Unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #: The name of the recommender.
    name = models.CharField(max_length=56)
    #: If true, the recommender is active system-wide and will be accessible for all users.
    active = models.BooleanField(default=True)
    #: The name of the class which defines the recommender's behavior.
    classname = models.CharField(max_length=56)
    #: Textual description of the recommender.
    description = models.CharField(max_length=2048, null=True)
    #: Path to the recommender's iconic image.
    image = models.CharField(max_length=128, null=True)
    #: Defines the order in which the recommender is displayed.
    order = models.IntegerField(null=True, unique=True)
    #: Information about how the user's data is used by the recommender.
    data_info = models.CharField(max_length=256, default="Die bei der Nutzung enstehenden Daten werden auf dem \
               Siddata Server gespeichert.")

    def __str__(self):
        """String representation of a Recommender object."""
        return "Recommender {}".format(self.name)


class SiddataUserRecommender(models.Model):
    """
    Represents the usage of a recommender by a user.
    """

    #: Unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #: The user who uses the recommender.
    user = models.ForeignKey(SiddataUser, on_delete=models.CASCADE)
    #: The recommender used by the user.
    recommender = models.ForeignKey(Recommender, on_delete=models.CASCADE)
    #: If true, the user has enabled the recommender and wants to use it.
    enabled = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "recommender"], name="unique_user_recommender"),
        ]

    def __str__(self):
        """String representation of a Category object."""
        return "User {} uses recommender {}".format(self.user.id, self.recommender.name)

    def get_max_order(self):
        """returns maximum order value og goals"""
        goals = Goal.objects.filter(userrecommender=self).order_by('-order')
        if len(goals) == 0:
            return 0
        else:
            return goals[0].order

    def serialize(self, include=True):
        """
        Converts a Recommender instance related to a certain user to nested structure that can be transformed to JSON.
        Follows REST API standards at
        https://jsonapi.org.
        :param include: If true, related objects are included in the response.
        :return: data Dictionary with nested data.
        """

        # Create announcements
        if self.recommender.name == "Startseite":
            rm_start = recommenders.RM_start.RM_start()
            rm_start.get_or_create_announcements(self.user)

        goal_dicts = []
        included = []
        goals = Goal.objects.filter(userrecommender=self).order_by("order")
        for goal in goals:
            goal_dicts.append({"id": goal.id, "type": "Goal"})
            if include:
                g_ser = goal.serialize(include=True)
                for entry in g_ser["data"] + g_ser["included"]:
                    if entry not in included:
                        included.append(entry)

        response_data = {
            "data": [{
                "type": "Recommender",
                "id": self.id,
                "attributes": {
                    "name": self.recommender.name,
                    "classname": self.recommender.classname,
                    "description": self.recommender.description,
                    "image": "{}{}".format(settings.IMAGE_URL, self.recommender.image),
                    "order": self.recommender.order,
                    "enabled": self.enabled,
                    "data_info": self.recommender.data_info,
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
                            "id": self.user.id
                        }]
                    }
                }
            }],
        }

        if include:
            u_ser = self.user.serialize(include=[])["data"][0]
            if u_ser not in included:
                included.append(u_ser)
            response_data['included'] = included

        return response_data


class Goal(models.Model):
    """
    Structure that represents some interest or work topic of a student. A goal holds a collection of activities.
    """

    #: Unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #: Title of the goal.
    title = models.CharField(max_length=1024, null=True)
    #: Textual description of the goal.
    description = models.TextField(null=True)
    #: Make date of the goal object.
    makedate = models.DateTimeField(auto_now_add=True)
    #: The associated user-recommender-usage-relation.
    userrecommender = models.ForeignKey(SiddataUserRecommender, on_delete=models.CASCADE)
    #: Display order of the goal.
    order = models.IntegerField(default=1)
    #: Type of the goal.
    type = models.CharField(max_length=128, null=True)
    #: If true, the goal will be displayed, else it will be hidden, and its activities will be displayed without a
    #: goal wrapped around them.
    visible = models.BooleanField(default=True)

    class Meta:
         constraints = [
             models.UniqueConstraint(fields=["userrecommender", "order"], name="unique_goal_in_recommender"),
         ]

    def __str__(self):
        """String representation of a Goal object."""
        return self.title

    def serialize(self, include=True):
        """
        Converts Goal instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :param include: If true, related objects are included in the response.
        :return: data Dictionary with nested data.
        """

        included = []

        activity_dicts = []
        activityset = Activity.objects.filter(goal=self,visible=True).order_by("order")

        for activity in activityset:
            activity_dicts.append({"id": activity.id, "type": "Activity"})
            if include:
                a_ser = activity.serialize()
                for entry in a_ser["data"] + a_ser["included"]:
                    if entry not in included:
                        included.append(entry)

        goalproperty_dicts = []
        goalpropertyset = GoalProperty.objects.filter(goal=self)
        for goalproperty in goalpropertyset:
            goalproperty_dicts.append({"id": goalproperty.id, "type": "GoalProperty"})
            gp_ser = goalproperty.serialize()
            if include:
                for entry in gp_ser["data"] + gp_ser["included"]:
                    if entry not in included:
                        included.append(entry)

        response_data = {
            "data": [{
                "type": "Goal",
                "id": self.id,
                "attributes": {
                    "title": self.title,
                    "description": self.description,
                    "makedate": self.makedate,
                    "user": self.userrecommender.user.pk,
                    "recommender": self.userrecommender.recommender.name,
                    "order": self.order,
                    "type": self.type,
                    "visible": self.visible,

                },
                "relationships": {
                    "activities": {
                        "data": activity_dicts
                    },
                    "goalproperties": {
                        "data": goalproperty_dicts
                    },
                    "students": {
                        "data": [{
                            "id": self.userrecommender.user.id,
                            "type": "SiddataUser"
                        }]
                    }
                }
            }],
        }

        if include:
            userrec_ser = self.userrecommender.serialize(include=False)["data"][0]
            if userrec_ser not in included:
                included.append(userrec_ser)
            response_data['included'] = included

        return response_data

    def get_property(self, key):
        """Get a goal's property identified by key.

        This encapsulates the goal property handling with GoalProperty objects.
        :return:The key's value as a string or None if key is not set."""
        GPs = GoalProperty.objects.filter(goal=self, key=key)
        if len(GPs) == 0:
            return None
        elif len(GPs) == 1:
            return GPs[0].value
        else:
            # must not happen: The key is not unique
            logging.warning("GoalProperty not unique! Goal: {} Key: {}".format(self.id, key))

    def get_max_form(self):
        """returns maximum form value of activities in the goal"""
        try:
            acts = Activity.objects.filter(goal=self, form__isnull=False).order_by('-form')
            if len(acts) == 0:
                return 0
            else:
                return acts[0].form
        except:
            logging.exception("Error in Goal.get_max_form()")

    def get_max_order(self):
        """returns maximum order value of activities in the goal"""
        acts = Activity.objects.filter(goal=self,
                                       order__isnull=False).order_by('-order')
        if len(acts) == 0:
            ret =  0
        else:
            ret = acts[0].order
        return ret

    def set_property(self, key, value):
        """Sets or updates a goal  property."""
        (p, created) = GoalProperty.objects.get_or_create(goal=self, key=key)
        p.value = value
        p.save()


class GoalProperty(models.Model):
    """A GoalProperty specifies a goal. For example: key=country, value=england"""
    #: Unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #: The goal this property belongs to.
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, default=None)
    #: The key string of the property.
    key = models.CharField(max_length=128)
    #: The value of the property.
    value = JSONField(null=True)

    def __str__(self):
        """String representation of a GoalProperty object."""
        return "GoalProperty {}".format(self.key)

    def serialize(self):
        """
        Converts GoalProperty instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """
        response_data = {
            "data": [{
                "type": "GoalProperty",
                "id": self.id,
                "attributes": {
                    "key": self.key,
                    "value": self.value,
                },
            }],
            "included": [],
        }
        return response_data


class Category(models.Model):
    """
    A category of goals, for instance DDC-codes but also the categories from our goal tagset.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1024)
    super_category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        """String representation of a Category object."""
        return "Category {}".format(self.name)


class GoalCategory(models.Model):
    """Represents one goal categorized by majority vote.
    One goal can have many categories and can only once be categorized by the majority vote.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    belongs_to = models.BooleanField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """String representation of a GoalCategory object."""
        return "GoalCategory {} {}".format(self.goal.title, self.category.name)


class EducationalResource(models.Model):
    """Represents an educational resource like books, courses, MOOCs etc."""
    FORMAT_CHOICES = [
        ('PDF', 'PDF'),
        ('VID', 'Video'),
        ('CRS', 'Course'),
        ('WEB', 'Web resource'),
        ('APP', 'Application'),
        ('TXT', 'Text resource'),
        ('AUD', 'Audio'),
        ('IMG', 'Image')
    ]
    TYPE_CHOICES = [
        ('SIP', 'Stud.IP Course'),
        ('MOOC', 'Massive Open Online Course'),
        ('OER', 'Open Educational Resource'),
        ('WEB', 'Website')
    ]

    #: Unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #: Dewey decimal classification number assigned by SidBERT.
    ddc_code = models.JSONField(null=True)
    #: The origin providing the resource.
    origin = models.ForeignKey(Origin, on_delete=models.CASCADE, related_name="educational_resource_origin", null=True)
    #: The resource's ID in its origin system.
    identifier = models.CharField(max_length=1024, unique=True, null=True)
    #: Contributor after dublin core scheme.
    contributor = models.JSONField(null=True)
    #: Time and place string, if present, after dublin core scheme.
    coverage = models.CharField(max_length=1024, null=True)
    #: lom creator or visible instructors after dublin core scheme.
    creator = models.JSONField(null=True)
    #: Date if the resource has a date of happening.
    date = models.DateTimeField(max_length=128, null=True)
    #: Textual description of the resource.
    description = models.TextField(null=True)
    #: pdf/video/mooc/etc.
    format = models.JSONField(max_length=1024, null=True, choices=FORMAT_CHOICES)
    #: The language of the resource.
    language = LanguageField(max_length=1024, null=True)
    #: Publisher of the resource.
    publisher = models.CharField(max_length=1024, null=True)  # keep it None for now, later maybe alias with origin
    #: Relation after dublin core scheme.
    relation = models.CharField(max_length=1024, null=True)
    #: Rights after dublin core scheme.
    rights = models.CharField(max_length=1024, null=True)
    #: URL to the original resource.
    source = models.TextField(null=True)
    #: List of content-related keywords.
    subject = models.JSONField(null=True)
    #: Title of the resource.
    title = models.CharField(max_length=1024)
    #: List of type-related keywords.
    type = models.JSONField(max_length=1024, null=True, choices=TYPE_CHOICES)

    def serialize(self):
        """
        Converts EducationalResource instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """

        if self.format is None:
            serialize_format = None
        else:
            serialize_format = self.get_format_translate()

        response_data = {
            "data": [{
                "type": "Resource",
                "id": self.id,
                "attributes": {
                    "title": self.title,
                    "description":  self.description,
                    "url": self.source if self.source else None,
                    "origin": [self.origin.name if self.origin else None],
                    "creator":self.creator,
                    "format": serialize_format
                },
            }],
            "included": [],
        }
        return response_data

    def get_format_translate(self):
        """
        Translates format abbreviations to full names.
        """
        format_translation_dict = {
        'IMG': 'Bilddatei',
        'CRS': 'Kurs',
        'WEB': 'Webseite',
        'APP': 'App / Anwendung',
        'TXT': 'Text',
        }

        if type(self.format) is list:
            local_format = self.format[0]
        elif '[\'' in self.format or '\']' in self.format:
            local_format = self.format.strip('[\'').strip(']\'')
        else:
            local_format = self.format
        if local_format in format_translation_dict:
            return format_translation_dict[local_format]
        else:
            for tuples in self.FORMAT_CHOICES:
                if local_format == tuples[0]:
                    return tuples[1]
        return None


class InheritingCourse(EducationalResource):
    """
    Course model inheriting from EducationalResource.
    """

    #: The course's ID in its origin system.
    course_origin_id = models.CharField(max_length=512, default=None)

    def __str__(self):
        """String representation of an Event object."""
        return f"{type(self).__name__} {self.title}"

    def serialize(self):
        """
        Converts Resource instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """
        response_data = {
            "data": [{
                "type": "Resource",
                "id": self.id,
                "description": self.description,
                "attributes": {
                    "title": self.title,
                    "description": self.description,
                    "url": self.source,
                    "origin": [self.origin.name if self.origin else None],
                },
            }],
            "included": [],
        }
        return response_data


class Institute(models.Model):
    """ Represents University Institutes. """

    #: Unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #: Name of the institute.
    name = models.CharField(max_length=512)
    #: URL to the institute's homepage.
    url = models.CharField(max_length=512, null=True)
    #: The origin where the institute is located.
    origin = models.ForeignKey(Origin, on_delete=models.CASCADE)
    #: ID of the institute in its origin system.
    institute_origin_id = models.CharField(max_length=512)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["institute_origin_id", "origin"], name="unique_origin_institute"),
        ]

    @staticmethod
    def is_valid_data(entity):
        """
        Checks if a json string is a valid Institute representation.
        :param entity: json data
        :return: Boolean
        """

        if entity["type"] == "Institute":
            if (entity["attributes"]["studip_id"] is None
                    or entity["attributes"]["name"] is None):
                return False
            else:
                return True
        else:
            return False


class StudipCourse(InheritingCourse):
    """
    Siddata's representation of Stud.IP courses.
    """

    #: The place where the course is held.
    place = models.CharField(max_length=1024, null=True)
    #: The course's start time.
    start_time = models.DateTimeField(null=True)
    #: The course's end time.
    end_time = models.DateTimeField(null=True)
    #: The semester in which the course is held first time.
    start_semester = models.CharField(max_length=128)
    #: The semester in which the course is held last time.
    end_semester = models.CharField(max_length=128)
    #: The institute providing the course.
    institute = models.ForeignKey(Institute, on_delete=models.DO_NOTHING, null=True, default=None)

    @staticmethod
    def is_valid_data(entity):
        """
        Checks if a json string is a valid Course representation.
        :param entity: json data
        :return: Boolean
        """

        if entity["type"] == "Course":
            if (entity["attributes"]["studip_id"] is None
                    or entity["attributes"]["name"] is None
                    or len(entity["attributes"]["name"]) < 2
                    or entity["attributes"]["start_semester"] is None
                    or entity["attributes"]["end_semester"] is None):
                return False
            else:
                return True
        else:
            return False

    def serialize(self):
        """
        Converts Course instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """
        response_data = {
            "data": [{
                "type": "Course",
                "id": self.id,
                "attributes": {
                    "title": self.title,
                    "description":  self.description,
                    "place": self.place,
                    "start_time": datetime.datetime.timestamp(self.start_time),
                    "end_time": datetime.datetime.timestamp(self.end_time),
                    "start_semester": self.start_semester,
                    "end_semester": self.end_semester,
                    "url": self.source,
                    "studip_id": self.course_origin_id
                }
            }],
            "included": []
        }
        return response_data


class InheritingEvent(EducationalResource):
    """
    Event model class inheriting from EducationalResource.
    """

    #: The course the event belongs to.
    course = models.ForeignKey(InheritingCourse, on_delete=models.CASCADE, null=True)
    #: The event's ID in its origin system.
    event_origin_id = models.CharField(max_length=128)

    def __str__(self):
        """String representation of an Event object."""
        return f"{type(self).__name__} {self.title}"

    def serialize(self):
        """
        Converts an Event instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """
        response_data = {
            "data": [{
                "type": "Event",
                "id": self.id,
                "attributes": {
                    "title": self.title,
                    "description":  self.description,
                    "origin_id": self.event_origin_id,
                    "type": self.type,
                    "self": (self.course.id if self.course else self.course),
                    "url": self.source,
                    "origin": self.origin.name,
                    "ddc_code": self.ddc_code
                },
            }],
            "included": [self.course],
        }

        return response_data


class StudipEvent(InheritingEvent):
    """
    Siddata's representation of events in Stud.IP systems.
    """

    #: The event's start time.
    start_time = models.DateTimeField(null=True)
    #: The event's end time.
    end_time = models.DateTimeField(null=True)
    #: The location where the event is happening.
    place = models.CharField(max_length=1024)

    @staticmethod
    def is_valid_data(entity):
        """
        Checks if a json string is a valid Event representation.
        :param entity: json data
        :return: Boolean
        """

        if "type" not in entity.keys() or "attributes" not in entity.keys():
            return False

        attr_keys = entity["attributes"].keys()

        if entity["type"] != "Event":
            return False

        if "studip_id" not in attr_keys or entity["attributes"]["studip_id"] is None:
            return False

        return True

    def serialize(self):
        """
        Converts an Event instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """
        response_data = {
            "data": [{
                "type": "Event",
                "id": self.id,
                "attributes": {
                    "title": self.title,
                    "description": self.description,
                    "studip_id": self.event_origin_id,
                    "start_time": datetime.datetime.timestamp(self.start_time),
                    "end_time": datetime.datetime.timestamp(self.end_time),
                    "type": self.type,
                    "self": (self.course.id if self.course else self.course),
                    "url": self.source,
                    "place": self.place,
                    "origin": self.origin.name,
                    "ddc_code": self.ddc_code
                },
            }],
            "included": [self.course],
        }

        return response_data


class WebResource(EducationalResource):
    """
    A web resource that can be recommended to users.
    """

    def __str__(self):
        """String representation of a Resource object."""
        return f"{type(self).__name__} {self.title}"

    def serialize(self):
        """
        Converts Resource instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """
        response_data = {
            "data": [{
                "type": "Resource",
                "id": self.id,
                "attributes": {
                    "title": self.title,
                    "description":  self.description,
                    "url": self.source,
                    "origin": [self.origin.name if self.origin else None],
                },
            }],
            "included": [],
        }
        return response_data


class Question(models.Model):
    """
    A question that can be asked to users wrapped in activities.
    """

    TYPE_CHOICES = [
        ('checkbox', 'Checkboxes'),
        ('text', 'Long answers in natural language'),
        ('shorttext', 'Short answers in natural language'),
        ('selection', 'Selection from `selection_answers`'),
        ('multitext', 'Users can add multiple shorttext answers'),
        ('auto_completion', 'Use for large selection'),
        ('date', 'Timestamps (frontend converts dates into timestamps)'),
        ('datetime', 'Timestamps (frontend converts dates into timestamps)')
    ]

    #: Unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #: The actual question.
    question_text = models.TextField()
    #: The typ of how the question is answered. Options are:
    #: checkbox = multiple choice
    #: text = free natural text
    #: likert = likert scale
    #: selection = single choice
    answer_type = models.CharField(max_length=1024, choices=TYPE_CHOICES)
    #: The answer options for the question.
    selection_answers = ArrayField(models.CharField(max_length=256), null=True)

    def __str__(self):
        """String representation of an Question object."""
        return "Question {}".format(self.question_text)

    def serialize(self):
        """
        Converts Question instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """
        response_data = {
            "data": [{
                "type": "Question",
                "id": self.id,
                "attributes": {
                    "question_text": self.question_text,
                    "answer_type": self.answer_type,
                    "selection_answers": self.selection_answers,
                }
            }],
            "included": []
        }
        return response_data


class Person(models.Model):
    """
    Represents a person. This can either be a lecturer which might not use Siddata by themselves, or a social business
    card created by a user mainly used by the Get Together recommender.
    """

    #: Unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #: The image the person wants to appear with.
    image = models.ImageField(upload_to='images/', default="images/default.png", null=True)
    #: The first name of the person.
    first_name = models.CharField(max_length=256, null=True)
    #: The last name of the person.
    surname = models.CharField(max_length=256, null=True)
    #: The academic title of the person.
    title = models.CharField(max_length=256, null=True)
    #: The email of the person.
    email = models.CharField(max_length=256, null=True)
    #: Description of the person's role or their interests.
    role_description = models.TextField(null=True)
    #: URL e.g. to the person's homepage.
    url = models.CharField(max_length=256, null=True)
    #: If true, this object will be used for data submission by users.
    editable = models.BooleanField(default=False)
    #: The user which created this person object.
    user = models.ForeignKey(SiddataUser, null=True, on_delete=models.CASCADE)

    def __str__(self):
        """String representation of an Question object."""
        return "Person {} {}".format(self.first_name, self.surname)

    def serialize(self):
        """
        Converts Question instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """
        try:
            image = self.image.url
        except Exception as e:
            logging.error(e)
            image = None

        response_data = {
            "data": [{
                "type": "Person",
                "id": self.id,
                "attributes": {
                    "first_name": self.first_name,
                    "surname": self.surname,
                    "title": self.title,
                    "email": self.email,
                    "role_description": self.role_description,
                    "url": self.url,
                    "image": "{}{}".format(settings.BASE_URL, image),
                    "editable": self.editable
                }
            }],
            "included": []
        }

        return response_data

    @staticmethod
    def is_valid_data(entity):
        """
        Checks if a json string is a valid Person representation.
        :param entity: json data
        :return: Boolean
        """
        return True


class Lecturer(Person):
    """
    Lecturer model class.
    """

    #: The origin where the lecturer works.
    origin = models.ForeignKey(Origin, on_delete=models.CASCADE)
    #: The ID of the lecturer their the origin system.
    person_origin_id = models.CharField(max_length=256)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["person_origin_id", "origin"], name="unique_origin_lecturer"),
        ]

    def serialize(self):
        """
        Converts Question instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """
        response_data = super().serialize()
        response_data['data'][0]['attributes']['origin_id'] = self.origin.id
        return response_data

    @staticmethod
    def is_valid_data(entity):
        """
        Checks if a json string is a valid Person representation.
        :param entity: json data
        :return: Boolean
        """

        if 'person_origin_id' in entity['attributes'].keys() and entity['attributes']['person_origin_id'] is not None:
            return True
        return False


class CourseLecturer(models.Model):
    """
    Relation between a lecturer and a course.
    """

    #: Unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #: The course.
    course = models.ForeignKey(InheritingCourse, null=False, on_delete=models.CASCADE)
    #: The lecturer.
    lecturer = models.ForeignKey(Person, null=False, on_delete=models.CASCADE)


class LecturerInstitute(models.Model):
    """
    Relation between a lecturer and an institute.
    """

    #: Unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #: The lecturer.
    lecturer = models.ForeignKey(Person, null=False, on_delete=models.CASCADE)
    #: The institute.
    institute = models.ForeignKey(Institute, null=False, on_delete=models.CASCADE)


class Activity(models.Model):
    """
    Represents an activity, the key interaction object in the system.
    """

    STATUSES = Choices("new", "active", "snoozed", "discarded", "done", "immortal")
    TYPES = Choices("resource",  "question", "person", "todo", "course", "event")

    #: If true, the activity can be re-activated by the user.
    rebirth = models.BooleanField(default=True, null=False)
    #: Unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #: Related goal object.
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, null=True)
    #: Title of the activity.
    title = models.CharField(max_length=256, null=True)
    #: Textual description of the activity.
    description = models.TextField(null=True)
    #: Type of the activity. Options are: resource, question, person, todo, course, event, iframe.
    type = models.CharField(max_length=64)
    #: Status of the activity. Options are: new, active, snoozed, discarded, done, immortal
    status = models.CharField(max_length=64, default="new")
    #: Related EducationalResource object.
    resource = models.ForeignKey(EducationalResource, on_delete=models.CASCADE, null=True)
    #: Related Question object.
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True)
    #: Related Person object.
    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True)
    #: Given answers, if this is a question activity.
    answers = ArrayField(models.CharField(max_length=256), null=True, default=list)
    #: Defines the size of the feedback scale for this activity.
    feedback_size = models.IntegerField(default=2)
    #: Numerical feedback given by the user.
    feedback_value = models.IntegerField(null=True)
    #: Textual feedback given by the user.
    feedback_text = models.CharField(max_length=1024, null=True)
    #: Date when the feedback was given.
    feedback_chdate = models.DateTimeField(null=True)
    #: User notes regarding this activity.
    notes = models.CharField(max_length=1024, null=True)
    #: Date when the activity should be resolved.
    duedate = models.DateTimeField(null=True)
    #: Display order of the activity.
    order = models.IntegerField(null=True)
    #: ID of the activity batch this activity belongs to.
    form = models.IntegerField(null=True)
    #: Change date of the activity.
    chdate = models.DateTimeField(null=True)
    #: Creation date of the activity.
    mkdate = models.DateTimeField(auto_now_add=True)
    #: Activation date of the activity.
    activation_time = models.DateTimeField(null=True)
    #: Deactivation date of the activity.
    deactivation_time = models.DateTimeField(null=True)
    #: Iconic image of the activity.
    image = models.CharField(max_length=256, null=True)
    #: Color theme of the activity.
    color_theme = models.CharField(max_length=64, null=True)
    #: Text displayed in the submit button of the activity. Note: "~static" hides the submit button.
    button_text = models.CharField(max_length=128, null=True)
    #: Number of the interactions the user made with this activity.
    interactions = models.IntegerField(null=True, default=0)
    #: ActivityTemplate this activity is based on.
    template_ref = models.ForeignKey("ActivityTemplate", on_delete=models.CASCADE, null=True)
    #: If true, the activity is displayed to the user.
    visible = models.BooleanField(default=True, null=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["goal", "order"], name="unique_order_in_goal"),
        ]

    def __str__(self):
        """String representation of an Activity object."""
        return "Activity {} {}".format(self.title, self.description)

    def respond(self):
        """
        Generates String that is displayed in Frontend when activity is finalized.
        :param activity:
        :return:
        """
        if self.type == "todo":
            return "To-do {} wurde erledigt.".format(self.title)
        elif self.type == "question":
            return "Antwort zu {} wurde gespeichert.".format(self.title)
        elif self.type == "resource":
            return "Empfehlung {} wurde bearbeitet.".format(self.title)
        elif self.type == "event":
            return "Veranstaltungsempfehlung {} wurde bearbeitet.".format(self.title)
        elif self.type == "course":
            return "Kursempfehlung {} wurde bearbeitet.".format(self.title)
        elif self.type == "person":
            return "Person {} wurde bearbeitet.".format(self.title)
        else:
            return "Eingabe {} wurde bearbeitet.".format(self.title)

    def get_dynamic_attributes(self):
        """
        Attributes which should get dynamically from template.
        Dynamic attributes always prioritize non empty Template attributes against Activity attributes.
        """
        return [
            "title",
            "description",
            "type",
            "resource",
            "question",
            "person",
            "feedback_size",
            "notes",
            "duedate",
            "order",
            "form",
            "image",
            "color_theme",
            "button_text",
        ]

    def __getattribute__(self, item):
        """
        Implements prioritize mechanism for ActivityTemplate attributes.
        Return Activity attribute if corresponding ActivityTemplate attribute is not set (empty|null).
        :param item: The attribute.
        """
        # Prioritize template attribute only if it is a dynamic attribute
        if item in object.__getattribute__(self, "get_dynamic_attributes")():
            # if template reference not exist
            if not object.__getattribute__(self, "template_ref_id"):
                # return Activity attribute
                return object.__getattribute__(self, item)

            template_item = getattr(object.__getattribute__(self, "template_ref"), item)
            # if template attribute is set
            if template_item:
                # return Template attribute
                return template_item
            else:
                return object.__getattribute__(self, item)
        # return Activity attribute
        return object.__getattribute__(self, item)

    @staticmethod
    def create_activity_from_template(template_id, goal, status="new", **kwargs):
        """
        Creates an activity instance from a specific template.
        :param template_id: The template id.
        :param goal: The related goal of the activity.
        :param status: The status the activity will be initialized with.
        :param kwargs: Additional attributes which will be set on the activity.
        """
        template = ActivityTemplate.objects.get(template_id=template_id)
        attributes = {}
        # copy all Template attributes which are specified as dynamic
        for attribute in template.get_dynamic_attributes():
            attributes[attribute] = getattr(template, attribute)
        attributes["goal"] = goal
        attributes["status"] = status
        attributes["template_ref"] = template

        # create activity
        activity = Activity.objects.get_or_create(**attributes)[0]

        # allow setting of values different from template
        for field, value in kwargs.items():
            setattr(activity, field, value)
        if settings.DEBUG and activity.form is not None:
            # ensure that there are no inconsistencies within the form activities
            form_activities = Activity.objects.filter(form=activity.form, goal=activity.goal)
            for fa in form_activities:
                assert fa.feedback_size == activity.feedback_size
                assert fa.button_text == activity.button_text
                assert fa.title == activity.title

        activity.save()

        return activity

    def has_template(self, template_id):
        """
        Returns true if the passed template_id matches the containing template reference.
        :param template_id: The template id to be tested.
        """
        return self.template_ref_id == template_id

    def serialize(self, include=True):
        """
        Converts an Activity instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :param include: If true, related objects will be included.
        :return: data Dictionary with nested data.
        """

        # Do not return Activity if it is not active yet or not active anymore
        now = datetime.datetime.now()
        start = datetime.datetime.timestamp(self.activation_time) if self.activation_time else None
        end = datetime.datetime.timestamp(self.deactivation_time) if self.deactivation_time else None
        if start and end and (now < start or now > end):
            return None

        response_data = {
            "data": [{
                "type": "Activity",
                "id": self.id,
                "attributes": {
                    "description": self.description,
                    "type": self.type,
                    "goal_id": self.goal.pk,
                    "title": self.title,
                    "status": self.status, #"active" if self.status == "immortal" else self.status,
                    "answers": self.answers,
                    "feedback_size": self.feedback_size,
                    "feedback_value": self.feedback_value,
                    "feedback_text": self.feedback_text,
                    "feedback_chdate": self.feedback_chdate,
                    "notes": self.notes,
                    "duedate": self.duedate,
                    "order": self.order,
                    "form": self.form,
                    "chdate": self.chdate,
                    "mkdate": self.mkdate,
                    "activation_time": self.activation_time,
                    "deactivation_time": self.deactivation_time,
                    "image": self.image if (self.image == None) else (self.image if (self.image[:4] == "http") else "{}{}".format(
                        settings.IMAGE_URL, self.image)),
                    "color_theme": self.color_theme,
                    "button_text": self.button_text,
                    "interactions": self.interactions,
                    "rebirth":self.rebirth,
                },
                "relationships": {
                    "course": {
                        "data": [{"id": self.resource.id, "type": "Course"}] if self.resource else []
                    },
                    "resource": {
                        "data": [{"id": self.resource.id, "type": "Resource"}] if self.resource else []
                    },
                    "question": {
                        "data": [{"id": self.question.id, "type": "Question"}] if self.question else []
                    },
                    "event": {
                        "data": [{"id": self.resource.id, "type": "Event"}] if self.resource else []
                    },
                    "person": {
                        "data": [{"id": self.person.id, "type": "Person"}] if self.person else []
                    },
                },
            }],
        }

        if include:
            included = []
            serialized = []
            if self.resource:
                rs = self.resource.serialize()
                serialized += rs["data"] + rs["included"]
            if self.question:
                qs = self.question.serialize()
                serialized += qs["data"] + qs["included"]
            if self.person:
                ps = self.person.serialize()
                serialized += ps["data"] + ps["included"]

            for entry in serialized:
                if entry not in included:
                    included.append(entry)

            userrec_ser = self.goal.userrecommender.serialize(include=False)["data"][0]
            if userrec_ser not in included:
                included.append(userrec_ser)
            goal_ser = self.goal.serialize(include=False)["data"][0]
            if goal_ser not in included:
                included.append(goal_ser)
            user_ser = self.goal.userrecommender.user.serialize(include=[])["data"][0]
            if user_ser not in included:
                included.append(user_ser)

            response_data['included'] = included
        return response_data


class ActivityTemplate(Activity):
    """Represents an activity template

    Basic usage:
        Below is explained how a template and an activity from a template could be created and
        how the template id could be used in conditions (e.g. in process_activity).
        For more information see backend wiki.

        Creating Templates:
            Templates need to be defined in the "initialize_templates(self)" function of a recommender.
            A Template is created like an activity and contains dynamic attributes which are used for
            all activities of this template. If a dynamic attribute is not set the activity uses his own attribute
            which is set in the activity creating function. In addition the status of a template is "template" to make
            templates distinguishable from activities.

            In a recommender each template must have an unique template id. An unique id is get by
            "get_template_id(self, template_name, origin=None)". Template name or pair of template name and origin
            must be unique. Otherwise a template couldn't clearly identified in the
            "activity_create_from_template" function.


            Example:
            def initialize_templates(self):

                super().initialize_templates()                          # creates the teaser template

                sid_question = models.Question.objects.get_or_create(
                    question_text="Hallo, ich bin Sid und gebe dir ein paar Tipps für den Einstieg in den Siddata "
                                  "Studienassistenten. ",
                    answer_type="selection",
                    selection_answers=["Ich möchte alles genau wissen",
                                       "Die Basics bitte",
                                       "Keine Tipps"]
                )[0]

                models.ActivityTemplate.objects.update_or_create(
                    template_id=self.get_template_id("welcome"),        # unique template id
                    defaults={                                          # contains dynamic attributes
                        "title": "Herzlich willkommen",
                        "type": "question",
                        "question": sid_question,
                        "status": "template",                           # template status
                        "image": "sid.png",
                        "feedback_size": 0,
                        "order": 1000000001,
                    }
                )

        Creating Activities:
            Activities are created by using the following function:
                "create_activity_from_template(template_id, goal, status="new", **kwargs)"

            The template id must match with the id of an existing template. A goal must be assigned for each activity.
            The kwargs parameter allows setting of values which will be assigned to the activity and could be
            different from template (e.g. title).

            Example:
                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("welcome"),
                    goal=goal,
                )

        Conditions with template id:
            The activity model contains a method called "has_template(self, template_id)" which checks
            if the template id matches the containing template of an activity. This function could be used for
            the processing of an activity.

            Example:
                if activity.has_template(self.get_template_id("welcome")):
                    # do something with this activity
    """

    #: Textual template ID.
    template_id = models.CharField(max_length=256, primary_key=True)
    #: Related activity object.
    activity_ptr = models.OneToOneField(
        Activity, on_delete=models.CASCADE,
        parent_link=True,
    )


class RequestLog(models.Model):
    """Represents a Request. For evaluation purposes"""

    #: Unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #: Recommender included in the request.
    recommender = models.ForeignKey(Recommender, on_delete=models.CASCADE, null=True)
    #: User included in the request.
    user = models.ForeignKey(SiddataUser, on_delete=models.CASCADE, null=True)
    #: Request time.
    timestamp = models.DateTimeField(auto_now_add=True)
    #: Route of the request.
    route = models.CharField(max_length=1024)


class CourseMembership(models.Model):
    """ Course Enrollment"""

    #: Unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #: The user who is enrolled in the course.
    user = models.ForeignKey(SiddataUser, on_delete=models.CASCADE, null=True)
    #: The course.
    course = models.ForeignKey(StudipCourse, on_delete=models.CASCADE, null=True)
    #: If true, the user agreed to share this course enrollment for analysis purposes.
    share_brain = models.BooleanField(default=False)
    #: If true, the user agreed to share this course enrollment with other users.
    share_social = models.BooleanField(default=False)


class InstituteMembership(models.Model):
    """ Institute affiliation"""

    #: Unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #: The user who is affiliated to the institute.
    user = models.ForeignKey(SiddataUser, on_delete=models.CASCADE, null=True)
    #: The institute.
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE, null=True)
    #: If true, the user agreed to share this institute affiliation for analysis purposes.
    share_brain = models.BooleanField(default=False)
    #: If true, the user agreed to share this institute affiliation with other users.
    share_social = models.BooleanField(default=False)


class AdminReport(models.Model):
    #: Unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #: The date when the report was sent. This will only be set when the report has already been sent.
    send_date = models.DateTimeField(default=None, null=True)
    #: If true, the report has not been sent yet.
    pending = models.BooleanField(default=True)

    @staticmethod
    def get_pending_report():
        """ Get the one report which has not be sent yet. """
        report = None
        try:
            report, created = AdminReport.objects.get_or_create(pending=True)
        except AdminReport.MultipleObjectsReturned:
            # There should be only one report which has not been sent yet.
            # If that is not the case, resolve this issue.
            logging.warning("More than one report without send_date occured! Resolving the problem automatically...")
            old_reports = AdminReport.objects.filter(pending=True)
            messages = ReportMessage.objects.filter(report__pending=True)
            report = AdminReport()
            for m in messages:
                m.report = report
                m.save()
            report.save()
            old_reports.delete()

        return report

    def send_to_admins(self):
        """
        Send the report to all admins.
        """
        messages = ReportMessage.objects.filter(report=self)

        if messages.count() == 0:
            # skip, if there are no messages to be sent
            return 1

        admins = settings.ADMINS
        admin_addrs = [admin[1] for admin in admins]

        mail_text = ''
        for message in messages:
            mail_text += str(message) \
                         + "<br>---------------------------------------------------------------------<br>"

        date = datetime.datetime.now()

        success = send_mail(
            f'Siddata Backend Report for {date.strftime("%a, %d.%m.%Y")}',
            mail_text,
            None,
            admin_addrs
        )

        if success:
            self.send_date = date
            self.pending = False
            self.save()
        else:
            logging.error(f"Sending admin mails failed. {len(messages)} messages have not been sent.")

        return success


class ReportMessage(models.Model):
    """ Report to be sent via mail to the admins on a regular basis """

    #: Unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #: Creation date of the message.
    mkdate = models.DateTimeField(auto_now_add=True)
    #: Change date of the message.
    chdate = models.DateTimeField(auto_now=True)
    #: The actual message.
    message = models.TextField(max_length=2048)
    #: The title of the message.
    title = models.CharField(max_length=512)
    #: The report this message belongs to.
    report = models.ForeignKey(AdminReport, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        """String representation of the message."""
        return self.title + "\n" + self.message + "\n"
