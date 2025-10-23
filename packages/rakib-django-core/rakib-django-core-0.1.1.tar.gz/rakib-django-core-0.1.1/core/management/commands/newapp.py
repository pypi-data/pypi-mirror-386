from os import path, mkdir
from shutil import rmtree

from django.core.management.base import BaseCommand

from config.settings import BASE_DIR


class Command(BaseCommand):
    help = 'For creating new django app'
    
    """#! Run This Command To Create New APP
    ##?>> python manage.py newapp <YOUR_APP_NAME>
    """

    def add_arguments(self, parser):
        # take app name
        parser.add_argument('app_name', type=str, help='Enter App name')

    def handle(self, *args, **options):
        app_name = options['app_name']
        app_name_capitalize = "".join([name.capitalize() for name in app_name.split("_")])

        base_dir = path.join(BASE_DIR, "apps", app_name)

        if path.exists(base_dir):
            # ask user if he wants to overwrite the app
            # if yes, delete the app and create new one
            # if no, exit
            self.stdout.write(self.style.ERROR(f"{app_name} app already exists"))
            # get user input
            user_input = input("Do you want to overwrite the app? (y/n): ")
            if user_input == "y":
                self.stdout.write(self.style.SUCCESS(f"Deleting {app_name} app"))
                # delete app recursively
                rmtree(base_dir)

        ## create app folder
        if not path.exists(base_dir):

            self.stdout.write(self.style.SUCCESS(f"Creating {app_name} app"))
            mkdir(base_dir)

            # create app folder structure
            self.stdout.write(self.style.SUCCESS(f"Creating {app_name} app structure"))
            mkdir(path.join(base_dir, "migrations"))
            mkdir(path.join(base_dir, "models"))
            mkdir(path.join(base_dir, "tasks"))
            mkdir(path.join(base_dir, "consumers"))
            

            ##! Create app Files
            self.stdout.write(self.style.SUCCESS(f"Creating {app_name} app files"))
            
            ##? __init__.py
            with open(path.join(base_dir, "__init__.py"), "w") as f:
                f.write("")
                
            ##? migrations/__init__.py
            with open(path.join(base_dir, "migrations", "__init__.py"), "w") as f:
                f.write("")
                
                
            ##? apps.py
            with open(path.join(base_dir, "apps.py"), "w") as f:
                f.write(f"from django.apps import AppConfig \n\n\n")
                f.write(f"class {app_name_capitalize}Config(AppConfig): \n")
                f.write(f"    default_auto_field = 'django.db.models.BigAutoField' \n")
                f.write(f"    name         = 'apps.{app_name}' \n")
                f.write(f"    verbose_name = '{app_name_capitalize}' \n")
                
            
            ##? tests.py
            with open(path.join(base_dir, "tests.py"), "w") as f:
                f.write("from django.test import TestCase \n\n")
                
                
            ##? tasks.py
            with open(path.join(base_dir, "tasks/your_tasks.py"), "w") as f:
                f.write("#from celery import shared_task\n\n\n")
                f.write("#@shared_task\n")
                f.write("#def sample_background_task():\n")
                f.write("#     return 'Task completed\n")
                f.write("#\n\n\n")
                
                
            ##? consumers.py
            with open(path.join(base_dir, "consumers/your_consumers.py"), "w") as f:
                f.write("#from channels.generic.websocket import AsyncWebsocketConsumer\n\n\n")
                f.write("#class YourConsumer(AsyncWebsocketConsumer):\n")
                f.write("#    async def connect(self):\n")
                f.write("#        await self.accept()\n")
                f.write("#\n\n\n")
                f.write("#    async def disconnect(self):\n")
                f.write("#        await self.close()\n")
                f.write("#\n\n\n")
                f.write("#    async def receive(self, text_data):\n")
                f.write("#        print(text_data)\n")
                
                
            ##? admin.py
            with open(path.join(base_dir, "admin.py"), "w") as f:
                f.write("from django.contrib import admin \n\n\n")
                f.write("##? Import Models \n")
                f.write(f"from apps.{app_name}.models import * \n\n")
                f.write("#@admin.register(YourModel) \n")
                f.write("#class YourModelAdmin(admin.ModelAdmin): \n")
                f.write("#    list_display  = ['id', 'name'] \n")
                f.write("#    search_fields = ['id', 'name'] \n")
                f.write("#    list_filter   = ['id', 'name'] \n")
                f.write("#    ordering      = ['-created_at',] \n")

        
            ##? urls.py
            with open(path.join(base_dir, "urls.py"), "w") as f:
                f.write("from django.urls import path, include \n\n")
                f.write("app_name = 'outbound' \n\n")
                f.write("##? Import Views \n")
                f.write(f"#from apps.{app_name}.views import {app_name_capitalize}View \n\n\n")
                f.write("urlpatterns = [ \n")
                f.write(f"    #path('list/', ListPage.as_view(), name='product_list'), \n")
                f.write(f"    #path('details/<int:id>/', DetailsPage.as_view(), name='product_details'), \n")
                f.write(f"    #path( \n")
                f.write(f"    #    'entry/', \n")
                f.write(f"    #    include( \n")
                f.write(f"    #        [ \n")
                f.write(f"    #            path('create/', CreatePage.as_view(), name='product_create'), \n")
                f.write(f"    #            path('list/', ListPage.as_view(), name='product_list'), \n")
                f.write(f"    #            path('details/<int:id>/', DetailsPage.as_view(), name='product_details'), \n")
                f.write(f"    #            path('update/<int:id>/', UpdatePage.as_view(), name='product_update'), \n")
                f.write(f"    #            path('delete/<int:id>/', DeletePage.as_view(), name='product_delete'), \n")
                f.write(f"    #        ] \n")
                f.write(f"    #    ), \n")
                f.write(f"    #), \n")
                f.write(f"] \n")
                
                
            ##? models.py
            with open(path.join(base_dir,"models", f"{app_name}.py"), "w") as f:
                f.write("import uuid, json, random, datetime\n")
                f.write("from django.db import models\n")
                f.write("from django.conf import settings\n\n")
                
                f.write("from django.utils import timezone\n")
                f.write("from django.utils.text import slugify\n")
                f.write("from django.utils.translation import gettext_lazy as _\n\n")
                
                f.write("from datetime import timedelta\n")
                f.write("from django.contrib.auth import get_user_model\n\n")
                f.write("##? Import Users\n")
                f.write("User = get_user_model() \n\n")
                f.write("##? Import TimestampedModel \n")
                f.write("from core.models.time_stamped import TimestampedModel\n\n\n")
                f.write(f"#class YourModelName(TimestampedModel): \n")
                f.write(f"#     pass \n")

            
            ##? views.py
            with open(path.join(base_dir, "views.py"), "w") as f:
                f.write("import json, random, decimal, time\n")
                f.write("from django.conf import settings\n")
                f.write("from django.shortcuts import render, redirect\n")
                f.write("from django.urls import reverse, reverse_lazy\n\n")
                f.write("from django.views import View, generic\n")
                
                f.write("from django.contrib import messages\n")
                f.write("from django.contrib.auth import get_user_model\n")
                f.write("from django.contrib.auth.mixins import LoginRequiredMixin\n")
                f.write("from django.contrib.sessions.models import Session\n\n")
                
                f.write("from django.db.models.functions import Concat, ExtractMonth, ExtractYear\n")
                f.write("from django.db.models import Q, Count, F, Value as V, CharField, Sum\n\n")
                
                f.write("from django.http import HttpRequest, HttpResponse, JsonResponse, Http404, HttpResponseRedirect\n\n")
                
                f.write("from django.core.paginator import Paginator, EmptyPage\n")
                f.write("from django.core.exceptions import ValidationError\n\n")
                
                f.write("from datetime import datetime, timedelta\n")
                f.write("from django.utils import timezone\n\n")
                
                f.write("from django.views.decorators.csrf import csrf_exempt\n\n")
                
                f.write("##? Import Models\n")
                f.write("User = get_user_model()\n\n\n\n")
                
                f.write("#class TemplateView(LoginRequiredMixin, generic.TemplateView):\n")
                f.write("#     login_url = reverse_lazy('auth:login')\n")
                f.write("#     template_name = 'index.html'\n\n")
                f.write("#     def get_context_data(self, **kwargs):\n")
                f.write("#          context = super().get_context_data(**kwargs)\n")
                f.write("#          context['total_products'] = Product.objects.count()\n")
                f.write("#          context['user'] = self.request.user\n")
                f.write("#          return context\n\n\n\n")
                
                f.write("#class CreatePage(LoginRequiredMixin, generic.CreateView):\n")
                f.write("#     login_url     = reverse_lazy('auth:login')\n")
                f.write("#     template_name = 'create.html'\n")
                f.write("#     success_url   = reverse_lazy('your_app:list') \n\n\n\n")
                
                f.write("#class ListPage(LoginRequiredMixin, generic.ListView):\n")
                f.write("#     model         = YourModel\n")
                f.write("#     template_name = 'list.html'\n")
                f.write("#     login_url     = reverse_lazy('auth:login')\n")
                f.write("#     context_object_name = 'objects'\n")
                f.write("#     paginate_by         = 25\n")
                f.write("#     ordering            = ['-created_at']\n\n\n\n")
                
                f.write("#class DetailPage(LoginRequiredMixin, generic.DetailView):\n")
                f.write("#     model         = YourModel\n")
                f.write("#     template_name = 'detail.html'\n")
                f.write("#     login_url     = reverse_lazy('auth:login')\n")
                f.write("#     context_object_name = 'object'\n\n\n\n")
                
                f.write("#class UpdatePage(LoginRequiredMixin, generic.UpdateView):\n")
                f.write("#     model         = YourModel\n")
                f.write("#     form_class    = YourForm\n")
                f.write("#     template_name = 'update.html'\n")
                f.write("#     login_url     = reverse_lazy('auth:login')\n")
                f.write("#     context_object_name = 'object'\n\n\n\n")
              
              
                
            self.stdout.write(self.style.SUCCESS(f"{app_name} app created successfully"))

        else:
            self.stdout.write(self.style.ERROR(f"{app_name} app already exists"))

        self.stdout.write(self.style.WARNING("Done. Don't forget to add app to INSTALLED_APPS in settings.py"))





##* If you don't use this command then you create menualy app like this
"""#! To Cretae App on apps folder
    #?>> mkdir -p apps/<APP_NAME>
    #?>> python manage.py startapp <APP_NAME> apps/<APP_NAME>
"""
