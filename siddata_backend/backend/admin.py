#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  3 12:12:15 2018

@author: fweber
"""

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import *


# für import-export app
@admin.register(Degree)
@admin.register(Subject)
@admin.register(Origin)
@admin.register(SiddataUser)
@admin.register(SiddataUserStudy)
@admin.register(UserProperty)
@admin.register(Goal)
@admin.register(GoalProperty)
@admin.register(Category)
@admin.register(GoalCategory)
@admin.register(InheritingCourse)
@admin.register(InheritingEvent)
@admin.register(WebResource)
@admin.register(Question)
@admin.register(Activity)
@admin.register(ActivityTemplate)
@admin.register(RequestLog)
@admin.register(Recommender)
@admin.register(SiddataUserRecommender)
@admin.register(Institute)
@admin.register(InstituteMembership)
@admin.register(CourseMembership)
@admin.register(EducationalResource)
@admin.register(StudipEvent)
@admin.register(StudipCourse)
@admin.register(Person)
@admin.register(Lecturer)
@admin.register(CourseLecturer)
@admin.register(LecturerInstitute)
# ohne import-export app
# admin.site.register(Degree)
# admin.site.register(Subject)
# admin.site.register(SiddataUser)
# admin.site.register(SiddataUserStudy)
# admin.site.register(Goal)
# admin.site.register(Category)
# admin.site.register(ReviewerGoalCategory)

class ViewAdmin(ImportExportModelAdmin):
    pass
