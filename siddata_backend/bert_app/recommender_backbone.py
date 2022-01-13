import datetime
import json
import re
import logging
import numpy as np

from django.apps import apps
from django.db.models import Q
from django.utils import timezone

from backend import models

class ProfessionsRecommenderBackbone:
    """
    This class acts as an interface between the backend and the AI functionalities regarding semantic analysis of strings
    """

    def __init__(self, max_courses=20):
        try:
            self.predictor = apps.get_app_config('bert_app').predictor
        except ModuleNotFoundError:
            logging.info("Could not load BERT APP predictor!")
        self.course_max = max_courses
        self.current_semester = self.check_current_semester()
        self.next_semester = self.check_next_semester()
        self.now = timezone.now()
        self.formats = models.EducationalResource.FORMAT_CHOICES
        self.types = models.EducationalResource.TYPE_CHOICES

    #################### Scheduled task function start ###############################
    def update_resources_bert(self):
        """
        Update function to classify all Resources, Courses and Events that are located in the backend.
        """



        self.set_new_semester()
        update_list = [models.StudipCourse.objects.filter(ddc_code__isnull=True, title__isnull=False, start_time__gte=self.current_semester),
                       models.StudipEvent.objects.filter(ddc_code__isnull=True, title__isnull=False, start_time__gte=self.current_semester),
                       models.EducationalResource.objects.filter(ddc_code__isnull=True, title__isnull=False).exclude(title='Ohne Titel')
                       ]
        update_n = 0
        for query_set in update_list:
            for query_object in query_set:
                try:
                    ddc_code = self.generate_ddc_label(query_object.title)
                except query_object.title is None:
                    continue
                query_object.ddc_code = json.dumps(ddc_code)
                query_object.save()
                update_n += 1
        return update_n

    def check_current_semester(self):
        today = datetime.datetime.today()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        if today.month in range(4,10): #This assumes that semesters always start on October 1st and April 1st.
            today = today.replace(month=3, day=31)
        elif today.month < 4:
            today = today.replace(year=today.year-1, month=9, day=30)
        elif today.month > 9:
            today = today.replace(month=9, day=30)
        today = timezone.make_aware(today)
        return today

    def check_next_semester(self):
        next_semester = datetime.datetime.today()
        if self.current_semester.month in range(4,10):
            next_semester = next_semester.replace(year=self.current_semester.year+1, month=3, day=31)
        elif self.current_semester.month < 4:
            next_semester = next_semester.replace(year=self.current_semester.year, month=9, day=30)
        else:
            next_semester = next_semester.replace(self.current_semester.year+1, month=3, day=31)
        next_semester = timezone.make_aware(next_semester)
        return next_semester

    def set_new_semester(self):
        self.current_semester = self.check_current_semester()
        self.next_semester = self.check_next_semester()


    #################### BERT DDC mapping start ###############################
    def generate_ddc_label(self, input_strings):
        ddc_mapping = self.predictor.predict_single_example(input_strings)
        return sorted([(key,val) for key,val in ddc_mapping.items()], key=lambda x:x[1], reverse=True)[0][0]

    def generate_sidbert_resources(self, label, filter_tags=None, origin=None, amount=None):
        """
        Generates a list of EducationalResource type object that match the DDC codes obtained from SIDBERT
        if no or too little courses exist, a semantic search for nearest courses is conducted.
        :param label: DDC label generated from an input string
        :param origin: origin object that constraints search to local university resources.
        :param filter_tags: list of tag words which resources can be filtered by
        :param amount: number of resources to generate
        """
        self.set_new_semester()
        matching_resources = []
        if len(label) == 0 or not filter_tags:
            return matching_resources
        label = '\"' +label+'\"'
        if not amount:
            amount = self.course_max
        local_amount = amount // len(filter_tags)
        local_top = local_amount // 3 * 2

        if 'local_course' in filter_tags:
            matching_internal_courses = []
            # exhaustively search for courses with fitting labels. Also searches for courses in parent / sister DDC class
            local_label = label
            while len(matching_internal_courses) < local_amount:
                if len(local_label) == 0:
                    break
                matching_internal_courses += self.get_matching_campus_courses(origin=origin, label=local_label, external_course=False)
                local_label = local_label.strip('\"')[:-1]
                for i in np.arange(10):
                    parent_label = local_label + str(i)
                    search_label = '\"' + parent_label + '\"'
                    matching_internal_courses += self.get_matching_campus_courses(origin=origin, label=search_label, external_course=False)
            if len(matching_internal_courses) > local_amount:
                non_top = matching_internal_courses[local_top:]
                matching_internal_courses = matching_internal_courses[:local_top]
                if len(matching_internal_courses) < local_amount and non_top:
                    if len(non_top) < local_amount - local_top:
                        size = len(non_top)
                    else:
                        size = local_amount-local_top
                    matching_internal_courses += np.random.choice(a=non_top, size=size).tolist()

            matching_resources += matching_internal_courses


        if 'external_course' in filter_tags:
            # exhaustively search for courses with fitting labels. Also searches for courses in parent / sister DDC class
            matching_external_courses = []
            local_label = label
            while len(matching_external_courses) < local_amount:
                if len(local_label) == 0:
                    break
                matching_external_courses += self.get_matching_campus_courses(origin=origin, label=local_label, external_course=True)
                local_label = local_label.strip('\"')[:-1]
                for i in np.arange(10):
                    parent_label = local_label + str(i)
                    search_label = '\"' + parent_label + '\"'
                    matching_external_courses += self.get_matching_campus_courses(origin=origin, label=search_label, external_course=True)
            if len(matching_external_courses) > local_amount:
                non_top = matching_external_courses[local_top:]
                matching_external_courses = matching_external_courses[:local_top]
                if len(matching_external_courses) < local_amount and non_top:
                    if len(non_top) < local_amount - local_top:
                        size = len(non_top)
                    else:
                        size = local_amount-local_top
                    matching_external_courses += np.random.choice(a=non_top, size=size).tolist()

            matching_resources += matching_external_courses


        if 'MOOC' in filter_tags:
            origins = models.Origin.objects.filter(type='mooc_provider')
            matching_moocs = []
            for origin in origins:
                matching_moocs += self.get_matching_extra_campus_course(label=label, origin=origin)
                #todo:
                # This may need to be changed in a future version as now only moocs from one
                # platform may be returned if there are lots of moocs on one platform with a certain label

            if len(matching_moocs) > local_amount:
                non_top = matching_moocs[local_top:]
                matching_moocs = matching_moocs[:local_top]
                if len(matching_moocs) < local_amount and non_top:
                    if len(non_top) < local_amount - local_top:
                        size = len(non_top)
                    else:
                        size = local_amount-local_top
                    matching_moocs += np.random.choice(a=non_top,size=size).tolist()
            matching_resources += matching_moocs

        if 'OER' in filter_tags:
            origins = models.Origin.objects.filter(type='edu-sharing_provider')
            matching_oers = []
            for local_origin in origins:
                matching_oers += self.get_matching_oer(label=label, origin=local_origin)
            if len(matching_oers) > local_amount:
                non_top = matching_oers[local_top:]
                matching_oers = matching_oers[:local_top]
                if len(matching_oers) < local_amount and non_top:
                    if len(non_top) < local_amount - local_top:
                        size = len(non_top)
                    else:
                        size = local_amount-local_top
                    matching_oers += np.random.choice(a=non_top, size=size).tolist()
            matching_resources += matching_oers

        if 'Event' in filter_tags:
            matching_events = self.get_matching_events(label=label,origin=origin)
            if len(matching_events) > local_amount:
                non_top = matching_events[local_top:]
                matching_events = matching_events[:local_top]
                if len(matching_events) < local_amount:
                    if len(non_top) < local_amount - local_top:
                        size = len(non_top)
                    else:
                        size = local_amount-local_top
                    matching_events += np.random.choice(a=non_top,size=size).tolist()
            matching_resources += matching_events


        # filtering out recommendations for the same Resource
        matching_resources = list(set(matching_resources))
        return matching_resources

    def get_matching_campus_courses(self, origin, label, external_course = False):
        """
        filters for matching courses on a campus.
        :param origin: origin to be searched for
        :param label: DDC label to be searched for
        :param external_course: whether to invert origin search to only include external courses.
        """
        query = Q(ddc_code=label) & \
                ((Q(start_time__gte=self.current_semester) & Q(start_time__lt=self.next_semester))
                | Q(start_time__gte=self.next_semester))

        if external_course:
            query &= ~Q(origin=origin)
        else:
            query &= Q(origin=origin)
        active_courses = models.StudipCourse.objects.filter(query)
        return list(active_courses)

    def get_matching_events(self, origin, label, external_event = False):
        self.now = timezone.now()
        query = Q(ddc_code=label) & \
                ((Q(start_time__gte=self.now) & Q(start_time__lt=self.next_semester))
                 | Q(start_time__gte=self.next_semester))
        if external_event:
            query &= ~Q(origin=origin)
        else:
            query &= Q(origin=origin)
        matching_events = models.StudipEvent.objects.filter(query)
        return list(matching_events)

    def get_matching_oer(self, origin, label):
        """
        Filter function to get Resources from external sources such as MOOC or OER repositories
        """
        query = Q(ddc_code=label) & Q(origin=origin) & Q(type__icontains='OER')
        matching_resources = models.EducationalResource.objects.filter(query)
        return list(matching_resources)

    def get_matching_extra_campus_course(self, origin, label):
        """
        Filters for moocs
        """
        query = Q(ddc_code = label) & Q(origin=origin) & Q(type__icontains='MOOC')
        matching_moocs = models.InheritingCourse.objects.filter(query)
        return list(matching_moocs)

    def fetch_resources_sidbert(self, goal, origin, filter_tags=None):
        """
        Wrapper function that generates DDC label from interest input text and searches for matching resources
        """
        res = self.generate_ddc_label(goal)
        logging.info("goal: "+goal+" was classified as: "+res)
        logging.info('Received filtered tags: '+str(filter_tags))
        sidbert_resources = self.generate_sidbert_resources(res, origin=origin, filter_tags=filter_tags)
        logging.info("Resources generated: ")
        logging.info(sidbert_resources)
        return sidbert_resources

    def compare_strings_by_ddc(self, str1, str2, is_same = False):
        """
        This function compares the relative semantic distance between two strings regarding their DDC distance.

        :param str1: The first string to be compared
        :type str1: str
        :param str2: The second string to be compared
        :type str2: str
        :return: A similarity value for str1 and str2
        :rtype: float between 1 (semantically orthogonal) and 0 (semantically equal)
        """
        max_depth = 4 # hard coded depth should be changed if we ever deploy a new model
        string_1_ddc = self.generate_ddc_label(str1)
        string_2_ddc = self.generate_ddc_label(str2)
        if is_same:
            if string_1_ddc == string_2_ddc:
                return True
            else:
                return False
        if len(string_1_ddc) >= len(string_2_ddc):
            target = string_1_ddc
            start = string_2_ddc
        else:
            target = string_2_ddc
            start = string_1_ddc
        steps = 0
        search = True
        current_position = start
        while search:
            if target.startswith(current_position):
                remain_index = len(current_position)
                steps += len(target[remain_index:])
                search = False
            else:
                steps += 1
                current_position = current_position[:-1]
        distance = steps / (max_depth * 2)
        return distance