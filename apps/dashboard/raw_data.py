import os
from datetime import datetime

import pandas as pd

from django.conf import settings
import backend.models as models

def get_raw_data():
    save_dir = os.path.join(settings.BASE_DIR, "../../siddata_backend", "data_export")
    os.makedirs(save_dir, exist_ok=True)

    activities = models.Activity.objects.filter(goal__userrecommender__user__data_donation=True)
    # print(len(activities))

    data = pd.DataFrame(list(activities.values()))
    # print(data)
    new_columns = {
        "goal_id": [],
        "goal_description": [],
        "goal_title": [],
        "recommender": [],
        "user_id": [],
        "user_university": [],
        "user_institute": [],
        "subject": [],
        "subject_id": [],
        "subject_destatis_id": [],
        "degree_id": [],
        "degree_name": [],
        "degree_origin_id": [],
        "degree_description": [],
        "semester": [],
    }
    for activity in activities:

        goal = activity.goal
        new_columns["goal_id"].append(goal.id)
        new_columns["goal_description"].append(goal.description)
        new_columns["goal_title"].append(goal.title)

        recommender = goal.userrecommender.recommender
        new_columns["recommender"].append(recommender.name)

        user = goal.userrecommender.user
        new_columns["user_id"].append(user.id)

        origin = user.origin
        new_columns["user_university"].append(origin.api_endpoint)

        institute_memberships = models.InstituteMembership.objects.filter(user=user)
        new_columns["user_institute"].append([])
        for i in institute_memberships:
            new_columns["user_institute"][-1].append(i.institute.name)

        studies = models.SiddataUserStudy.objects.filter(user=user)
        new_columns["subject"].append([])
        new_columns["subject_id"].append([])
        new_columns["subject_destatis_id"].append([])
        new_columns["degree_id"].append([])
        new_columns["degree_name"].append([])
        new_columns["degree_origin_id"].append([])
        new_columns["degree_description"].append([])
        new_columns["semester"].append([])
        for sus in studies:
            new_columns["subject"][-1].append(("None" if sus.subject is None else sus.subject.name))
            new_columns["subject_id"][-1].append(("None" if sus.subject is None else sus.subject.id))
            new_columns["subject_destatis_id"][-1].append(
                ("None" if sus.subject is None else sus.subject.destatis_subject_id))
            new_columns["degree_id"][-1].append(("None" if sus.degree is None else sus.degree.id))
            new_columns["degree_name"][-1].append(("None" if sus.degree is None else sus.degree.name))
            new_columns["degree_origin_id"][-1].append(("None" if sus.degree is None else sus.degree.degree_origin_id))
            new_columns["degree_description"][-1].append(("None" if sus.degree is None else sus.degree.description))
            new_columns["semester"][-1].append(sus.semester)
    for column_name in new_columns.keys():
        data[column_name] = new_columns[column_name]


    data.to_csv(path_or_buf=os.path.join(save_dir, "activities_full.csv"), sep=',')
    with open(os.path.join(save_dir, "last_export"), "w") as wfile:
        wfile.write(datetime.now().strftime("%d.%m.%Y, %H:%M:%S"))




