from dataclasses import dataclass
from typing import Any

import pandas as pd
import plotly.express as px
from plotly.io import to_html

from django.db.models import Count
from dashboard import plotly_plots


FILTER_DATADONATION = True
FILTER_FINEGRAN = False

#for semesters
K_ANONYMIZE = False
MERGE_OVERTEN= True


def main():
    # quick & dirty way to setup Django without the forever-loading BERT module. Have this before getting backend-models
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "siddata_backend.settings")
    import django
    from django.core.wsgi import get_wsgi_application
    django.conf.settings.INSTALLED_APPS = [i for i in django.conf.settings.INSTALLED_APPS if not 'BertAppConfig' in i]
    get_wsgi_application()
    print("".join([i.html for i in create()])) #this can be a print as it's not run in the backend, only manually


def create():
    # only import on-demand, because we cannot import before the setup happened either by manage.py or our dirty way in main()
    import backend.models as models
    return (
            recommenderusage_hbars(models),
            standort_piechart(models),
            activity_averageresponse_per_recommender(models),
            degree_course_sunburst(models),
            degree_semester_bars(models),
            )
    # TODO I'm really not good with HTML/Bootstrap, for some examples on how to place the cards see
    # https://github.com/hobbyhack/django_chartsjs_demo/blob/main/django_charts_demo/data/templates/dashboard.html
    # https://www.codeply.com/go/nIB6oSbv6q
    # https://www.codeply.com/go/8qpkLw5Dfv, https://stackoverflow.com/questions/51610770/bootstrap-4-card-deck-containing-cards-with-different-width,
    # https://stackoverflow.com/questions/35868756/how-to-make-bootstrap-4-cards-the-same-height-in-card-columns


def uni_name(studip_name):
    if 'bremen' in studip_name:
        return 'Bremen'
    elif 'hannover' in studip_name:
        return 'Hannover'
    elif 'osnabrueck' in studip_name:
        return 'Osnabrück'
    return False


@dataclass
class Chart():
    html: str
    data: Any
    title: str
    min_height: int=100
    min_width: int=100


def standort_piechart(models):
    if FILTER_DATADONATION:
        places = [i for i in models.SiddataUser.objects.filter(data_donation=True).values('origin__name').annotate(total=Count('origin'))]
    else:
        places = [i for i in models.SiddataUser.objects.values('origin__name').annotate(total=Count('origin'))]
    places = {uni_name(i['origin__name']): i['total'] for i in places if uni_name(i['origin__name']) != False} #remove localhost-users from statistic

    index_sort = lambda yourlist, indices: [i[1] for i in sorted(enumerate(yourlist), key=lambda x: indices[x[0]], reverse=True)]
    colors = ['rgb(0, 50, 109)', 'rgb(0,81,158', 'rgb(159,5,48)'] #alphabetically by uni-name
    #TODO plotly is native for pandas-dataframes, is there a nice native way for django-db-objects?
    uni_names = list(places.keys())
    sorted_indices = sorted(range(len(uni_names)), key=lambda k: uni_names[k]) #we need to sort keys & values
    html = plotly_plots.pichart_plot(index_sort(uni_names, sorted_indices), index_sort(places.values(), sorted_indices), colors)

    places = pd.DataFrame.from_dict(places, orient='index', columns=['n'])
    return Chart(html, places, 'Benutzer pro Standort', 500, 500)


def recommenderusage_hbars(models):
    if FILTER_DATADONATION:
        all_answers = [i for i in models.Activity.objects.filter(description__contains='Teaser_', goal__userrecommender__user__data_donation=True).values('answers', 'title').annotate(dcount=Count('goal_id'))]
    else:
        all_answers = [i for i in models.Activity.objects.filter(description__contains='Teaser_').values('answers', 'title').annotate(dcount=Count('goal_id'))]
    if len(all_answers) < 1:
        return Chart('', pd.DataFrame(), "Nutzung pro Recommender", 450, 1000)
    recommender_usage = pd.DataFrame(all_answers)
    recommender_usage['answers'] = recommender_usage['answers'].apply(str).replace("['Ja']", "Ja").replace("['Nein']", "Nein").replace("[]", "Nicht interagiert")
    recommender_usage = recommender_usage.pivot(index='title', columns='answers', values='dcount')

    top_labels = ['Aktiviert', 'Deaktiviert', 'Nicht interagiert']
    colors = ['rgba(0, 255, 0, 0.5)', 'rgba(255, 0, 0, 0.5)', 'rgba(190, 192, 213, 1)']
    x_data = [list(i[1]) for i in recommender_usage.T.iteritems()]
    y_data = list(recommender_usage.index)
    html = plotly_plots.hbars_plot(top_labels, colors, x_data, y_data)
    return Chart(html, recommender_usage, 'Nutzung pro Recommender', 450, 1000)


def degree_course_sunburst(models):
    filters = {}
    if FILTER_DATADONATION:
        filters["user__data_donation"] = True
    if FILTER_FINEGRAN:
        filters["share_degree_brain"] = True
        filters["share_subject_brain"] = True
    degree_course = [i for i in models.SiddataUserStudy.objects.filter(**filters).values('degree__name', 'subject__name')]
    degree_course = pd.DataFrame([[i['degree__name'], i['subject__name']] for i in degree_course], columns=['Degree', 'Course of Study'])
    degree_course = degree_course.groupby(degree_course.columns.tolist(),as_index=False).size() #see https://stackoverflow.com/a/35584675/5122790

    fig = px.sunburst(degree_course, path=['Degree', 'Course of Study'], values='size')
    html = to_html(fig, full_html=False)
    return Chart(html, degree_course, 'Benutzer pro Studiengang', 800, 800)


def degree_semester_bars(models):
    filters = {}
    if FILTER_DATADONATION:
        filters["user__data_donation"] = True
    if FILTER_FINEGRAN:
        filters["share_degree_brain"] = True
        filters["share_semester_brain"] = True
    degree_sem = [i for i in models.SiddataUserStudy.objects.filter(**filters).values('degree__name', 'semester')]
    degrees = set([i["degree__name"] for i in degree_sem])
    BASE_DEGREES = ["Bachelor", "Master", "Magister", "Promotion"]
    base_mapper = {i:base for i in degrees for base in BASE_DEGREES if any([j.lower() == base.lower() for j in (i or "None").replace("-"," ").split(" ")])}
    base_mapper.update({i: "Andere" for i in degrees - set(base_mapper.keys())})
    # degree_sem_cnt = {key: {"ges": 0} for key in BASE_DEGREES+["Andere"]}
    degree_sem_cnt = {key: {} for key in BASE_DEGREES + ["Andere"]}
    for i in degree_sem:
        if i["semester"] in degree_sem_cnt[base_mapper[i["degree__name"]]]:
            degree_sem_cnt[base_mapper[i["degree__name"]]][i["semester"]] += 1
        else:
            degree_sem_cnt[base_mapper[i["degree__name"]]][i["semester"]] = 1
        # degree_sem_cnt[base_mapper[i["degree__name"]]]["ges"] += 1
    degree_sem_cnt = {key: dict(sorted({k:v for k,v in val.items() if k!=0}.items(), key=lambda x: x[0] or 0)) for key, val in degree_sem_cnt.items()}
    # #if you want to keep Magister & Promotion and drop Andere:
    degree_sem_cnt.pop("Andere")
    # #if you want to merge Magister, Promotion & Andere
    # for key in ["Magister", "Promotion"]:
    #     for sem, num in degree_sem_cnt[key].items():
    #         degree_sem_cnt["Andere"][sem] = degree_sem_cnt["Andere"].get(sem, 0) + degree_sem_cnt[key][sem]
    # [degree_sem_cnt.pop(i) for i in ["Magister", "Promotion"]]

    if K_ANONYMIZE:
        degree_sem_cnt = {key: k_anonymize(val, K_ANONYMIZE) for key, val in degree_sem_cnt.items()}
    elif MERGE_OVERTEN:
        degree_sem_cnt = {key: merge_overten(val) for key, val in degree_sem_cnt.items()}
    title = "Studiengang und Semester"
    degree_sem_cnt = {key: {str(k2): v2 for k2, v2 in val.items()} for key, val in degree_sem_cnt.items()}
    html = plotly_plots.grouped_barplot(degree_sem_cnt, show_legend=False)

    df = pd.DataFrame(degree_sem_cnt)
    df.index = df.index.astype('str')
    df.sort_index(inplace=True)
    df['new_idx'] = range(1, len(df) + 1)
    df.loc['None', 'new_idx'] = 0
    df = df.sort_values("new_idx").drop("new_idx", axis=1)
    df.fillna(0, inplace=True)

    return Chart(html, df, title, 500, 1000)


def merge_overten(data):
    res = {}
    overten = 0
    for sem, nstuds in data.items():
        if isinstance(sem, int) and sem >= 10:
            overten += nstuds
        else:
            res[sem] = nstuds
    if overten:
        res["≥10"] = overten
    return res


def k_anonymize(data, k, return_exceptions="asnone"):
    assert return_exceptions in [True, False, "asnone"]
    #TODO: this is greedy, a way to keep the #groups maximal would be better!
    res = {}
    iterator = iter({str(k): v for k,v in data.items()}.items())
    lastsem = None
    is_exception = False #exception: the sum of ALL groups < k
    for sem, nstuds in iterator:
        nextsem, nexstud = None, None
        while nstuds < k and sem != "None":
            try:
                nextsem, nexstud = next(iterator)
            except StopIteration:
                if lastsem:
                    # if we're already at the last entry and the it's too small, pop the last group and add this as well
                    nstuds = res.pop(lastsem)
                    sem = lastsem
                else: #if there is NO GROUP big enough, nothing we can do
                    is_exception = True
                    break
            if nextsem and nexstud:
                sem = sem.split("-")[0] + "-" + nextsem
                nstuds += nexstud
        lastsem = sem
        if is_exception:
            if not return_exceptions:
                continue
            else:
                return {"None": nstuds}
        res[sem] = nstuds
    return res


def activity_averageresponse_per_recommender(models):
    #wie viele activities wurden im Schnitt pro recommender als erledigt markiert.
    all_acs = [i for i in models.Activity.objects.filter(goal__userrecommender__user__data_donation=True).values('goal__userrecommender', 'goal__userrecommender', 'goal__userrecommender__recommender__name', 'goal__userrecommender__user_id', 'answers')]
    tmp = [[str(i['goal__userrecommender__user_id']), i['goal__userrecommender__recommender__name'], i['answers']] for i in all_acs]
    tmp = pd.DataFrame(tmp, columns=['User', 'Recommender', 'Answer'])
    tmp['Answer'] = tmp['Answer'].apply(str).replace("['Ja']", "Ja").replace("['Nein']", "Nein")
    tmp['no_act'] = (tmp['Answer'] == 'None') | (tmp['Answer'] == '[]')
    unique_nresponds_user_rec = tmp[['User', 'Recommender', 'no_act']].groupby(tmp[['User', 'Recommender', 'no_act']].columns.tolist(), as_index=False).size()
    yesno_per_recommender = unique_nresponds_user_rec.groupby(['Recommender', 'no_act'])['size'].mean().unstack().rename(columns={False: "Beantwortet", True: "Unbeantwortet"})
    #wie viele activities gibt es im schnitt pro user auf die reagiert wurde (False) oder nicht reagiert wurde (True)
    fig = px.bar(yesno_per_recommender.reset_index().fillna(0).round(1), x="Recommender", y=["Beantwortet", "Unbeantwortet"], title="User-Durchschnitt der Activities pro Recommender", labels={"value": "Anzahl Activities", "variable": ""})
    html = to_html(fig, full_html=False)
    return Chart(html, yesno_per_recommender, "Durchschnittliche Anzahl un/beantworteter Aktivitäten pro Recommender", 500, 750)


if __name__ == '__main__':
    main()

