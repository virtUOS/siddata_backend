import logging

from bert_app.recommender_backbone import ProfessionsRecommenderBackbone
from bert_app.bert_utils import BertPredictor

COURSE_MAX = 10
COURSES_TO_DISPLAY = 5

goal = 'Machine Learning'

COURSES = [("0000","Grundlegende Aspekte der Informationsverarbeitung in natürlichen und künstlichen Systemen, die Phänomene Information, Intelligenz und Bewusstsein"),
           ("0013","Das Haupt des Thomas Morus in der St. Dunstan-Kirche zu Canterbury"),
           ("0063","14th International Conference, MLDM 2018, New York, NY, USA, July 15-19, 2018, Proceedings, Part I, Machine Learning and Data Mining in Pattern Recognition"),
           ("2900","ein Beitrag zur Erforschung des islamischen Reformdenkens im frühen 18. Jahrhundert, Šāh Walīy Allāh ad-Dihlawīy (1703 - 1762) und sein Aufenthalt in Mekka und Medina"),
           ("6500","Erfolgsfaktor Design-Management, ein Leitfaden für Unternehmer und Designer"),
           ]

########################################################################################################################
#Mock-objects that the backbone expects (in the productive system this comes from django)

class AppConfig():
    name = 'bert_app'
    predictor = BertPredictor()

class Course():
    def __init__(self, name, ddc, TF_IDF_scores=None):
        self.name = name
        self.ddc = ddc
        self.TF_IDF_scores = TF_IDF_scores or {}

    def __repr__(self):
        return f"Course(Name:{self.name};DDC:{self.ddc})"

class CourseObjects():
    def __init__(self, courses):
        self.courses = courses

    def filter(self, ddc_code):
        return [i for i in self.courses if i.ddc == ddc_code]

    def all(self):
        return self.courses

########################################################################################################################


def main():
    course_objects = CourseObjects([Course(name, ddc) for ddc, name in COURSES])
    appconfig = AppConfig()
    backbone = ProfessionsRecommenderBackbone(course_objects, appconfig, COURSE_MAX, COURSES_TO_DISPLAY)

    #this part should call the backbone the same way the RM_professions module does in process_activity
    tf_idf_courses = backbone.fetch_courses_tf_idf(goal)
    tf_idf_courses = tf_idf_courses[:COURSE_MAX//2]
    sidbert_courses = backbone.fetch_courses_sidbert(goal)
    flatten = lambda l: [item for sublist in l for item in sublist]
    alternate = lambda a, b: flatten(list(zip(a, b))) + a[len(b):] + b[len(a):]
    alternate_with_name = lambda a, b: alternate(list(zip('a' * len(a), a)), list(zip('b' * len(b), b)))

    logging.info("Relevant Results:")
    for fromwhere, what in alternate_with_name(sidbert_courses, tf_idf_courses):
        if fromwhere == 'a':
            logging.info("Sidbert-Course:", what)
        else:
            logging.info("TF-IDF-Course:", what)


if __name__ == '__main__':
    main()
