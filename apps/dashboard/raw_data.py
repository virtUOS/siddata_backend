import os
from datetime import datetime

import pandas as pd
from django_pandas.io import read_frame

from django.conf import settings
import backend.models as models


def get_raw_data():
    activities = models.Activity.objects.filter(goal__userrecommender__user__data_donation=True, ).exclude(title="RESET")

    # add users who don't want to share their data as private users
    anchor_id = models.Activity.objects.filter(title="Was ist Siddata?")[0].template_ref.id
    private_data = models.Activity.objects.filter(template_ref__id=anchor_id, goal__userrecommender__user__data_donation=False)

    fieldnames = [
        "id",
        "title",
        "description",
        "status",
        "type",
        "feedback_size",
        "feedback_value",
        "mkdate",
        "question__question_text",
        "question__id",
        "resource__id",
        "resource__title",
        "resource__source",
        "answers",
        "question__selection_answers",
        "goal__id",
        "goal__description",
        "goal__order",
        "order",
        "goal__userrecommender__recommender__name",
        "goal__userrecommender__user__id",
        "goal__userrecommender__user__gender_brain",
        "goal__userrecommender__user__origin__name",
        "goal__userrecommender__user__data_donation",
        "template_ref__id",
        "template_ref__title"
    ]
    data = read_frame(activities, fieldnames=fieldnames)

    private_df = read_frame(private_data, fieldnames=fieldnames)
    private_df.loc[:, (private_df.columns != 'goal__userrecommender__user__data_donation') & (private_df.columns != 'id')] = None
    df_activities = pd.concat([data, private_df])

    df_activities.set_index('id', inplace=True)

    col_names = {
        'goal__userrecommender__user__id': 'user_id',
        'goal__userrecommender__user__gender_brain': 'gender',
        'feedback_size': 'feedback_scale_size',
        'feedback_value': 'given_feedback',
        'mkdate': 'timestamp',
        'question__question_text': 'quesiton',
        'question__id': 'question_id',
        'resource__id': 'resource_id',
        'resource__title': 'resource_title',
        'resource__source': 'resource_url',
        'answers': 'given_answers',
        'question__selection_answers': 'answers',
        'goal__id': 'goal_id',
        'goal__description': 'goal_description',
        'goal__order': 'goal_order',
        'goal__userrecommender__recommender__name': 'recommender',
        'goal__userrecommender__user__origin__name': 'student_university',
        'template_ref__id': 'template_id',
        'template_ref__title': 'template_title'
    }
    df_activities.rename(col_names, axis=1, inplace=True)

    resources_db = models.EducationalResource.objects.filter(activity__id__in=df_activities.index.tolist())
    studycourses_db = models.SiddataUserStudy.objects.filter(user__id__in=df_activities['user_id'].unique())
    instm_db = models.InstituteMembership.objects.filter(user__id__in=df_activities['user_id'].unique())
    coursems_db = models.CourseMembership.objects.filter(user__id__in=df_activities['user_id'].unique(), share_brain=True)

    def extend_df(x):
        # add resource types
        if x.resource_id is not None:
            types = []
            for r in resources_db.filter(id=x.resource_id):
                if r.type is not None:
                    types += r.type

            x['resource_types'] = list(set(types))
        else:
            x['resource_types'] = None

        # add study courses
        if x.user_id is not None:
            users_scs = studycourses_db.filter(user__id=x.user_id)
            sc_list = []
            for usc in users_scs:
                sc_list.append({
                    'subject': usc.subject if usc.share_subject_brain else None,
                    'degree': usc.degree if usc.share_degree_brain else None,
                    'semester': usc.semester if usc.share_semester_brain else None
                })
            x['student_studycourses'] = sc_list

            # add institutes
            user_instms = instm_db.filter(user__id=x.user_id)
            insts = []
            for im in user_instms:
                insts.append(im.institute.name)
            x['student_institutes'] = insts

            # make university names readable
            if "bremen" in x['student_university']:
                x['student_university'] = "Bremen"
            elif "hannover" in x['student_university']:
                x['student_university'] = "Hannover"
            elif "osnabrueck" in x['student_university']:
                x['student_university'] = "Osnabrück"

            # add course memberships
            user_cms = coursems_db.filter(user__id=x.user_id)
            courses = []
            for cm in user_cms:
                courses.append({
                    'id': cm.course.id,
                    'title': cm.course.title
                })
            x['student_visited_studip_courses'] = courses

        else:
            x['student_studycourses'] = None
            x['student_institutes'] = None
            x['student_visited_studip_courses'] = None
            # student_university should already be None

        return x

    data = df_activities.apply(extend_df, axis=1)

    save_dir = os.path.join(settings.BASE_DIR, "..", "data_export")
    os.makedirs(save_dir, exist_ok=True)

    data.to_csv(path_or_buf=os.path.join(save_dir, "activities_full.csv"), sep=';')
    with open(os.path.join(save_dir, "last_export"), "w") as wfile:
        wfile.write(datetime.now().strftime("%d.%m.%Y, %H:%M:%S"))




