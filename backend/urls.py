"""siddata_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import permission_required
from django.urls import path, include

from . import api_views
from . import views

urlpatterns = [
    # Authentication
    path('login', auth_views.LoginView.as_view(template_name="backend/login.html"), name='login'),
    path('logout', auth_views.LogoutView.as_view(), name='logout'),

    # HTML views for statistics interface
    path('', views.home, name="home"),
    path('home', views.home, name="home"),
    path('accounts/', include('django.contrib.auth.urls')),

    # dashboard stuff
    # TODO so far, this is a class-view, and hence it's not easy to put a decorator around it and we do the permission_required here
    # TODO explore if this can also be a callable-class and we call its __call__ or smth, thing is only we need the context
    path('export_csv', permission_required('auth.view_dashboard')(views.export_csv), name="export_csv"),
    path('export_single', permission_required('auth.view_dashboard')(views.export_single), name="export_single"),
    path('export_raw', permission_required('auth.view_dashboard')(views.export_raw), name="export_raw"),
    path('dashboard', permission_required('auth.view_dashboard')(views.DashboardView.as_view()), name="dashboard"),

    # simple integrated client
    path('backdoor', views.backdoor, name="backdoor"),
    path('backdoor/<uuid:userid>', views.backdoor, name="backdoor_user"),
    path('backdoor/<uuid:userid>/<str:view>', views.backdoor, name="backdoor_user_view"),
    path('backdoor/<uuid:userid>/list/<str:list>', views.backdoor, name="backdoor_user_list"),
    path('backdoor_interact/<uuid:userid>', views.backdoor_interact, name="backdoor_interact"),

    # OER / edu-sharing
    path('oer', views.oer, name="oer"),

    # js
    path('backend.js', views.backend_js, name='backend.js'),

    # API 2.0
    path('backend/api/student', api_views.student),
    path('backend/api/recommender', api_views.recommender),
    path('backend/api/recommender/<str:recommender_id>', api_views.recommender),
    path('backend/api/goal', api_views.goal),
    path('backend/api/goal/<str:goal_id>', api_views.goal),
    path('backend/api/activity', api_views.activity),
    path('backend/api/activity/<str:activity_id>', api_views.activity),


    path('backend/api/coursemembership', api_views.coursemembership),
    path('backend/api/institutemembership', api_views.institutemembership),
    path('backend/api/studycourse', api_views.studycourse),
    path('backend/api/studycourse/<str:studycourse_origin_id>', api_views.studycourse),
    path('backend/api/subject', api_views.subject),
    path('backend/api/degree', api_views.degree),
    path('backend/api/course', api_views.course),
    path('backend/api/course/<str:course_origin_id>', api_views.course),
    path('backend/api/event', api_views.event),
    path('backend/api/institute', api_views.institute),
    path('backend/api/person', api_views.person),

    path('api-auth/', include('rest_framework.urls')),

]

