import logging
import os

import pandas as pd
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import generic
from django.http import HttpResponse
from django.conf import settings
from sickle import Sickle
import xml.etree.ElementTree as ET

import requests

from .models import Goal, SiddataUser, SiddataUserStudy, Degree, Subject, Activity
from recommenders.recommender_functions import get_active_recommenders
# from dashboard.create_chart import build_eval_df
from dashboard import create_plots
from django.utils.text import slugify

def home(request):
    """Start page.

    :param request The view's request object."""

    logger = logging.getLogger("backend.views.home")
    logger.debug("Home loaded...")
    page = 'home'  # for highlighting navbar entry
    return render(request, "backend/home.html")


@login_required
def list_goals(request):
    """Display all goals.

    :param request The view's request object.
    :returns renderable response from form template."""

    page = 'list_goals'  # for highlighting navbar entry

    goals = Goal.objects.all().order_by('-makedate')  # fetch all goals

    num_goals = Goal.objects.count()
    num_users = SiddataUser.objects.count()

    degrees = Degree.objects.annotate(num=Count('siddatauserstudy')).order_by('name')
    subjects = Subject.objects.annotate(num=Count('siddatauserstudy')).order_by('name')

    return render(request, "backend/goallist.html", locals())


@login_required
def goals_data(request):
    subjects = []  # subjects filter
    degrees = []  # degrees filter
    for param_key in request.POST:
        if param_key.startswith('subject-'):  # subjects to include
            try:
                subjects.append(Subject.objects.get(pk=int(param_key.split("-", 1)[1])))
            except ValueError:  # malformed id
                continue
        if param_key.startswith('degree-'):  # competencies to include
            try:
                degrees.append(Degree.objects.get(pk=param_key.split("-", 1)[1]))
            except ValueError:
                continue
    all_goals = Goal.objects.all()
    if subjects:
        all_goals = all_goals.filter(userrecommender__user__siddatauserstudy__subject__in=subjects)
    if degrees:
        all_goals = all_goals.filter(userrecommender__user_siddatauserstudy__degree__in=degrees)

    if 'nopaging' in request.POST:  # all on one page...
        wpp = len(all_goals)  # goals per page
        page = 1
    else:
        wpp = 25
        page = request.POST.get('page')

    paginator = Paginator(all_goals, wpp)  # Show 25 contacts per page

    try:
        goals = paginator.page(page)
        offset = (int(page) - 1) * 25
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        goals = paginator.page(1)
        offset = 0
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        goals = paginator.page(paginator.num_pages)
        offset = (paginator.num_pages - 1) * 25

    return render(request, 'backend/goals_data.html', locals())


@login_required
def goal_form(request):
    """Display goal form.

    :param request The view's request object.
    :returns renderable response from form template."""

    page = 'goal_form'  # for highlighting navbar entry
    goals = Goal.objects.all()
    return render(request, "backend/goalform.html", locals())


@login_required
def add_goal(request):
    goal = request.POST.get("goal", None)
    if goal:
        u = SiddataUser.objects.get_or_create(origin_id='internal', origin='internal')[0]
        for study in [{"degree": {"name": "Bachelor of Science (B.Sc.)", "degree_origin_id": "14"},
                       "subject": {"name": "Cognitive Science", "subject_origin_id": "729"},
                       "semester": 3}]:
            us = SiddataUserStudy.objects.get_or_create(user=u,
                                                        degree_id=Degree.objects.get(name=study['degree']['name'],
                                                                                     degree_origin_id=study['degree'][
                                                                                         'degree_origin_id']).pk,
                                                        subject_id=Subject.objects.get(name=study['subject']['name'],
                                                                                       subject_origin_id=
                                                                                       study['subject'][
                                                                                           'subject_origin_id']).pk,
                                                        semester=study['semester'])[0]
        g = Goal(goal=goal, userrecommender__user=u)
        g.save()
        messages.info(request, "Ziel '{}' angelegt.".format(goal))
    else:
        messages.warning(request, 'Ziel konnte nicht angelegt werden.')
    return redirect('list_goals')


def backend_js(request):
    return render(request, "backend/backend.js", locals())


@login_required
def backdoor(request, userid=None, view=None, list=None):
    """Provide simple client interface in Django backend."""

    if not userid:
        user = None  # perhaps there is no user yet
        username = request.GET.get('user', 'test001')  # default: test001
        originname = request.GET.get('origin', 'UOS')  # default: UOS
    else:
        user = get_object_or_404(SiddataUser, pk=userid)
        username = user.user_origin_id
        originname = user.origin.api_endpoint

    if not view and not list:
        view = 'stats'

    # fetch data via API
    # this would not strictly be necessary because we have database access, but we want to use the standard api mechanisms
    # e.g. for creating new users
    import requests, json
    r = requests.get('http://localhost:8000/backend/api/lists?origin={}&user_origin_id={}'.format(originname, username))
    json_result = json.loads(r.text)
    result = [json_result['lists'][x] for x in json_result['lists'].keys()]  # reorganize as list of list dictionaries (TODO: Sorting)
    lists = json_result['lists'].keys()

    if not user:  # data passed from form, perhaps new user?
        user = get_object_or_404(SiddataUser, origin__api_endpoint=originname, user_origin_id=username)

    if view == 'stats':
        # fetch some statictics from database
        num_recommenders = Goal.objects.filter(userrecommender__user=user).distinct('recommender').count()  # number of active recommenders
        num_goals = Goal.objects.filter(userrecommender__user=user).count()  # number of goals for user
        num_activities = Activity.objects.filter(goal__userrecommender__user=user).count()  # number of activities for user
        num_done_activities = Activity.objects.filter(goal__userrecommender__user=user, status="done").count()  # number of activities for user
        recommenders = get_active_recommenders()
    # one template for everything
    return render(request, "backend/backdoor.html", locals())


@login_required
def backdoor_interact(request, userid):
    """Receive and handle interaction feedback for backdoor client."""

    type = request.GET.get("type", None)  # determine type of interaction (question or ...)
    user = get_object_or_404(SiddataUser, pk=userid)

    if type == 'question':
        activity_id = request.GET.get("activity_id", None)
        answers = request.GET.get("answers", None)
        if activity_id and answers:
            data = {'data': {'activity_id': activity_id, 'type': 'Activity', 'attributes': {'answers': [answers], 'status': 'done'}}}
            response = requests.patch('http://localhost:8000/backend/api/activity', json=data)
            if response.ok:
                messages.add_message(request, messages.INFO, 'Answer was processed.')
            else: # code >= 400
                messages.add_message(request, messages.ERROR, 'Error {} {}: {}'.format(response.status_code, response.reason, response.text))
        else: # not all parameters given
            messages.add_message(request, messages.WARNING, 'Malformed request (activtiy_id or answers missing for question.'.format(type))
    elif type == 'reset':
        if user:
            uname = "{} ({})".format(user.user_origin_id, user.origin.api_endpoint)
            user.delete()
            messages.add_message(request, messages.INFO, 'User {} deleted.'.format(uname))
            return redirect(reverse('backdoor'))  # redirect to start of backdoor
        else:
            messages.add_message(request, messages.WARNING, 'Unknown user: {}'.format(userid))

    else: # unknown type
        messages.add_message(request, messages.WARNING, 'Unknown type: {}'.format(type))


    next = request.GET.get('next', reverse('backdoor_user', kwargs={'userid':user.id}))  # redirect to where we came from (filled by template as GET parameter next ro to user's backddor start)

    return redirect(next) # show activities for current user again


def oer(request):
    # rest Api test
    # response = requests.post(
    #     url="https://www.twillo.de/edu-sharing/rest/node/v1/nodes/-home-",
    #     params={"query": "title:*"},
    #     headers={
    #         "Accept": "application/json",
    #         "Content-Type": "application/json",
    #     },
    # )
    # print(json.loads(response.content))
    # return redirect('home')

    # Get all resources by using oai service
    sickle = Sickle("https://www.twillo.de/edu-sharing/eduservlet/oai/provider")
    records = sickle.ListRecords(metadataPrefix='lom')
    ns = {"oai": "http://www.openarchives.org/OAI/2.0/",
          "lom": "http://ltsc.ieee.org/xsd/LOM"}
    for record in records:
        # Parse LOM-XML
        root = ET.fromstring(record.raw)
        header = root.find("oai:header", ns)
        metadata = root.find("oai:metadata/lom:lom", ns)
        # Mapping lom to Dublin Core partially based on
        # https://www.researchgate.net/figure/Mapping-between-Unqualified-Dublin-Core-and-IEEE-LOM_tbl1_221425064
        dcmes = {
            "Contributor": list(elem.text for elem in metadata.findall(".//lom:lifeCycle/lom:contribute/lom:entity", namespaces=ns)),
            "Coverage": list(elem.text for elem in metadata.findall(".//lom:classification/lom:taxonPath/lom:taxon/lom:entry/string", namespaces=ns)),
            "Creator": metadata.findtext(".//lom:metaMetadata/lom:contribute/lom:entity", namespaces=ns),
            "Date": header.findtext(".//oai:datestamp", namespaces=ns),
            "Description": metadata.findtext(".//lom:general/lom:description/string", namespaces=ns),
            "Format": metadata.findtext(".//lom:technical/lom:format", namespaces=ns),
            "Identifier": metadata.findtext(".//lom:general/lom:identifier/lom:entry", namespaces=ns),
            "Language": metadata.findtext(".//lom:general/lom:language", namespaces=ns),
            "Publisher": metadata.findtext(".//lom:lifeCycle/lom:contribute[lom:role='publisher']/lom:entity", namespaces=ns),
            "Relation": metadata.findtext(".//lom:technical/lom:location", namespaces=ns),
            "Rights": metadata.findtext(".//lom:rights/lom:description/string", namespaces=ns),
            "Source": metadata.findtext(".//lom:relation/lom:kind/lom:source", namespaces=ns),
            "Subject": list(metadata.find(".//lom:general/lom:keyword", namespaces=ns).itertext()),
            "Title": metadata.findtext(".//lom:general/lom:title/string", namespaces=ns),
            "Type": list(metadata.find(".//lom:educational/lom:learningResourceType", namespaces=ns).itertext()),
        }
        print(dcmes)
    return redirect('home')


################################### for dashboard ###################################


#path('export_csv', permission_required('auth.view_dashboard')(views.export_csv), name="export_csv"),
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="csv_dump.csv"'
    charts = create_plots.create()
    final_df = pd.DataFrame()
    for chart in charts:
        if isinstance(chart.data, pd.DataFrame):
            final_df = pd.concat((final_df, chart.data))
        else:
            try:
                final_df = pd.concat((final_df, pd.DataFrame(chart.data)))
            except:
                final_df = pd.concat((final_df, pd.Series(chart.data, name=chart.title)), axis=1)
    final_df.to_csv(path_or_buf=response, index=True, sep=',', decimal='.', float_format='%.2f')
    return response

def export_single(request):
    response = HttpResponse(content_type='text/csv')
    which_plot = request.GET["plot"]
    response['Content-Disposition'] = f'attachment; filename="{which_plot}.csv"'
    charts = create_plots.create()
    chart = [i for i in charts if slugify(i.title) == which_plot][0]
    chart.data.to_csv(path_or_buf=response, index=True, sep=',')
    return response


def export_raw(request):
    save_dir = settings.DATA_EXPORT_DIR
    if os.path.isdir(save_dir) and os.path.isfile(os.path.join(save_dir, "activities_full.csv")):
        if os.path.isfile(os.path.join(save_dir, "last_export")):
            with open(os.path.join(save_dir, "last_export"), "r") as rfile:
                date = rfile.read()
        else:
            date = ""
        filename = "data_export_"+date.replace(":","-").replace(".","-").replace(" ","_").replace(",","")+".csv"
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        res = pd.read_csv(os.path.join(save_dir, "activities_full.csv"), index_col=0)
        res.to_csv(path_or_buf=response, index=True, sep=',', decimal='.', float_format='%.2f')
    else:
        from django.http import HttpResponseNotFound
        response = HttpResponseNotFound("Currently, there is no raw data to export! Check again in a few minutes, and if the problem remains, let a Siddata Admin know!")
    return response



class DashboardView(generic.TemplateView):
    template_name = "backend/dashboard.html"
    sum_col_width = 12
    assumed_screen_width = 1000

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        charts = create_plots.create()
        for chart in charts:
            chart.min_width = round(chart.min_width/self.assumed_screen_width*self.sum_col_width)
            chart.min_height = round((chart.min_height/50)+0.5)*50 #rounds up to next 50's
            chart.html = '<div style="height:100%">'+chart.html[5:]
            chart.downloadlink = f'<a href="export_single?plot={slugify(chart.title)}">download</a>'
        context['charts_and_titles'] = charts
        return context
