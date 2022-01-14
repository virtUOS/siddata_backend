from django.db.models import Q
import pandas as pd
import numpy as np
from difflib import SequenceMatcher
import random
import datetime
from backend import models

class CollaborativeInterlink:
    def __init__(self):
        #self.ddc_class_names = pd.read_csv('././data/Sidbert(bert_data(classes.tsv',names=['ddc_classes'],dtype='str')['ddc_classes'].to_list()
        self.current_semester = self.get_current_semester()
        self.next_semester = self.get_next_semester()
        self.ddc_weight = 10

    def get_current_semester(self):
        """
        Generates a datetime object signifying the current semester
        """
        today = datetime.datetime.today().timetuple()
        year = today[0]
        month = today[1]
        start_date = datetime.date(year,3, 31)
        if month in range(4,10): #This assumes that semesters always start on October 1st and April 1st.
            start_date = datetime.date(year, 3, 31)
        elif month < 4:
            start_date = datetime.date(year-1, 9, 30)
        elif month > 9:
            start_date = datetime.date(year, 9, 30)
        return start_date

    def get_next_semester(self):
        current_semester = self.current_semester
        if current_semester.month == 3:
            next_month = 9
            next_year = current_semester.year
            next_day = 30
        else:
            next_month = 3
            next_year = current_semester.year+1
            next_day = 31
        return datetime.date(year=next_year,month=next_month,day=next_day)

    def compare_user_history(self, history_1, history_2):
        similarity_score = 0.0
        if len(history_2) >= len(history_1):
            max_courses = history_2
            min_courses = history_1
            num_compare_items = len(history_2)
        else:
            max_courses = history_1
            min_courses = history_2
            num_compare_items = len(history_1)

        for course in max_courses:
            if course in min_courses:
                similarity_score += 1.0
                max_courses = max_courses.exclude(id=course.id)
                min_courses = min_courses.exclude(id=course.id)

        if len(max_courses) == 0 or len(min_courses) == 0:
            return num_compare_items / similarity_score
        else:
            for course_left_max in max_courses:
                for course_left_min in min_courses:
                    add_score = self.compute_course_equivalence(course_left_max,course_left_min)
                    if add_score != 0:
                        max_courses = max_courses.exclude(id=course_left_max.id)
                        min_courses = min_courses.exclude(id=course_left_min.id)
                        similarity_score += add_score
        if len(max_courses) == 0 or len(min_courses) == 0:
            return num_compare_items / similarity_score
        else:
            similarity_score += self.compute_average_ddc_distance(max_courses, min_courses) * self.ddc_weight
        return num_compare_items / similarity_score


    def compute_course_equivalence(self, course, other_course):
        if course.institute == other_course.institute:
            if course.title == other_course.title:
                return 1.0
            elif SequenceMatcher(None, course.name, other_course.name).ratio() > 0.8:
                return 0.8
            elif len(course.description) > 80 and len(other_course.description) > 80 and SequenceMatcher(None, course.description, other_course.description).ratio() > 0.9:
                return 0.9
        return 0


    def compute_average_ddc_distance(self, max_courses, min_courses):
        """
        Computes rate of geometric intersection coefficient between course history
        projected into DDC space
        follows greedy best first search and omits missing courses.
        return: coefficient indicating how well course histories match with 0 being a perfect match
        and 1 being a total missmatch
        """
        maximum_distance = len(max_courses) * 8
        distance_matrix = np.zeros((len(max_courses),len(min_courses)))
        for x, candidate in enumerate(max_courses):
            candidate_ddc = candidate.ddc_code.strip('\"')
            for y, comparing_course in enumerate(min_courses):
                comparing_ddc = comparing_course.ddc_code.strip('\"')
                distance_matrix[x][y] = self.calculate_ddc_distance(candidate_ddc,comparing_ddc)

        total_distance = 0
        while len(distance_matrix.shape) == 2:
            print(distance_matrix)
            if distance_matrix.shape[1] == 1:
                total_distance += min(distance_matrix)
                total_distance = total_distance[0]
                break
            elif distance_matrix.shape[0] == 1:
                break
            min_x = 0
            min_y = 0
            argmin_column = distance_matrix.argmin(axis=1)
            min_value = distance_matrix[0][argmin_column[0]] + 1
            for n, index in enumerate(argmin_column):
                if distance_matrix[n][index] < min_value:
                    min_y = index
                    min_x = n
                    min_value = distance_matrix[n][index]
            total_distance += min_value
            distance_matrix = np.delete(distance_matrix, min_y, axis=1)
            distance_matrix = np.delete(distance_matrix, min_x, axis=0)
        return (maximum_distance - total_distance / maximum_distance) / 8


    def calculate_ddc_distance(self, candidate, comparing_course):
        if candidate == comparing_course:
            return 0
        if len(candidate) >= len(comparing_course):
            start = candidate
            goal = comparing_course
        else:
            start = comparing_course
            goal = candidate

        for n, level_index in enumerate(start):
            if n == len(goal) or level_index != goal[n]:
                remaining_steps = len(start) - n + len(goal[n:])
                break
            if level_index == goal[n]:
                continue
        return remaining_steps

    def check_for_shared_data(self, user):
        return True if models.CourseMembership.objects.filter(user=user, share_brain=True).exists() else False

    def generate_similarity_resources(self, user, top_n = 5):
        if not self.check_for_shared_data(user):
            return []
        else:
            top_scores = pd.DataFrame(columns=['id','score'])
            user_courses = models.CourseMembership.objects.filter(user=user, share_brain=True)
            other_users = models.SiddataUser.objects.filter(origin=user.origin).exclude(id=user.id)
            no_search = False
            if len(other_users) < top_n:
                top_n = len(other_users)
                no_search = True
            top_scores['id'] = [user for user in other_users[:top_n]]
            top_scores['score'] = [self.compare_user_history(user_courses, i) for i in [models.CourseMembership.objects.filter(user=ou, share_brain=True) for ou in other_users[:top_n]]]
            other_users = other_users[:top_n]
            top_scores = top_scores.sort_values('score')
            if not no_search:
                for other_user in other_users:
                    if not models.CourseMembership.objects.filter(user=other_user, share_brain=True).exists():
                        continue
                    else:
                        other_user_courses = models.CourseMembership.objects.filter(user=other_user, share_brain=True)
                        local_similarity_score = self.compare_user_history(user_courses, other_user_courses)
                        top_scores = top_scores.append({'id':other_user.id,'score':local_similarity_score},ignore_index=True).sort_values('score')[:top_n]

            top_ids = top_scores['id'].to_list()
            other_user_query = Q(user__id__isin=[top_ids])
            top_other_user_courses = models.CourseMembership.objects.filter(other_user_query).course
            user_course_objects = user_courses.course
            top_other_user_courses = top_other_user_courses.exclude(user_course_objects)
            return top_other_user_courses

