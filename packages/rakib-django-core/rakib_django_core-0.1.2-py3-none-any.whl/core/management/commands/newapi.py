from os import path, mkdir
from shutil import rmtree

from django.core.management.base import BaseCommand

from config.settings import BASE_DIR


class Command(BaseCommand):
    help = 'For creating new django app'
    
    """#! Run This Command To Create New API
    ##?>> python manage.py newapi <YOUR_API_NAME>
    """

    def add_arguments(self, parser):
        # take app name
        parser.add_argument('app_name', type=str, help='Enter App name')

    def handle(self, *args, **options):
        app_name = options['app_name']
        app_name_capitalize = "".join([name.capitalize() for name in app_name.split("_")])

        base_dir = path.join(BASE_DIR, "apis/v1", app_name)

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

        # create app folder
        if not path.exists(base_dir):

            self.stdout.write(self.style.SUCCESS(f"Creating {app_name} app"))
            mkdir(base_dir)
            
            mkdir(path.join(base_dir, "serializers"))
            mkdir(path.join(base_dir, "views"))
            mkdir(path.join(base_dir, "services"))

            ##! Create app Files
            self.stdout.write(self.style.SUCCESS(f"Creating {app_name} app files"))
            
            ##? __init__.py
            with open(path.join(base_dir, "__init__.py"), "w") as f:
                f.write("")
                    
                                
            ##? serializers.py
            with open(path.join(base_dir, "serializers", f"{app_name}.py"), "w") as f:
                f.write("from rest_framework import serializers \n")
                f.write("from django.conf import settings \n\n")
                
                f.write("from django.db import transaction \n")
                f.write("from django.db.models import Q, F, Count, Value, Prefetch \n")
                f.write("from django.contrib.auth import get_user_model \n")
                f.write("from django.utils.timezone import localtime \n\n")
                
                f.write("##? Utils Importn \n")
                f.write("from apis.utils.field_error_messages import get_field_error_messages \n")
                f.write("from apis.utils.apiResponse import * \n\n")
                
                f.write("##? Models Importn\n\n\n\n")
                
                f.write("##? Serializers Creation\n\n")
                f.write("#class StatusSerializer(serializers.ModelSerializer): \n")
                f.write("#    class Meta: \n")
                f.write("#        model  = Status \n")
                f.write("#        fields = ['id', 'name'] \n\n")
                    
                f.write(f"#class {app_name_capitalize}Serializer(serializers.ModelSerializer): \n")
                f.write("#     is_active = serializers.BooleanField(write_only=True, required=False, default=False) \n\n")
                f.write("#     status    = StatusSerializer(read_only=True) \n")
                
                f.write("#     status_id = serializers.PrimaryKeyRelatedField( \n")
                f.write("#         source     = 'status', \n")
                f.write("#         queryset   = Status.objects.all(), \n")
                f.write("#         write_only = True, \n")
                f.write("#         required   = False, \n")
                f.write("#         allow_null = True, \n")
                f.write("#         error_messages = get_field_error_messages('Status', 'PrimaryKeyRelated')\n")
                f.write("#     ) \n\n")
                
                f.write("#     test_field = TestSerializer(read_only=True, source='test') \n")
                f.write("#     test_id    = serializers.PrimaryKeyRelatedField( \n")
                f.write("#         source     = 'test', \n")
                f.write("#         queryset   = Test.objects.all(), \n")
                f.write("#         write_only = True, \n")
                f.write("#         required   = False, \n")
                f.write("#         allow_null = True, \n")
                f.write("#         error_messages = get_field_error_messages('Test (item)', 'PrimaryKeyRelated') \n")
                f.write("#     ) \n\n")
                
                f.write("#     class Meta: \n")
                f.write("#         model = YourModel \n")
                f.write("#         fields = ['is_active', 'status', 'status_id', 'test_field', 'test_id'] \n\n")
                
                f.write("#     def validate(self, attrs): \n")
                f.write("#         request = self.context.get('request', None) \n")
                f.write("#         return attrs \n\n")
                
                f.write("#     ##! Create \n")
                f.write("#     def create(self, validated_data): \n")
                f.write("#         request  = self.context.get('request', None) \n")
                f.write("#         is_draft = validated_data.pop('is_draft', False) \n")
                f.write("#         items_data = validated_data.pop('itemsData', []) \n")
                
                f.write("#         try: \n")
                f.write("#             with transaction.atomic(): \n")
                f.write("#                 objects = YourModel.objects.create( \n")
                f.write("#                     created_by=request.user, \n")
                f.write("#                     **validated_data \n")
                f.write("#                 ) \n")
                f.write("#                 for item_data in items_data: \n")
                f.write("#                     YourDetailsModel.objects.create(parent=objects, **item_data) \n")
                f.write("#         except Exception as e: \n")
                f.write("#             return response_error(str(e), status=500, message='Internal server error') \n")
                f.write("#         return objects \n\n")
                
                f.write("#     ##! Update \n")
                f.write("#     def update(self, instance, validated_data): \n")
                f.write("#         request  = self.context.get('request', None) \n")
                f.write("#         items_data = validated_data.pop('details_model_related_name', []) \n\n")
                
                f.write("#         # Main fields update \n")
                f.write("#         for attr, value in validated_data.items(): \n")
                f.write("#             setattr(instance, attr, value) \n")
                f.write("#         instance.save() \n\n")
                
                f.write("#         # Handle items \n")
                f.write("#         existing_items = {item.id: item for item in instance.details_model_related_name.all()} \n")
                f.write("#         incoming_ids = [] \n")
                
                f.write("#         try: \n")
                f.write("#             with transaction.atomic(): \n")
                f.write("#                 for item_data in items_data: \n")
                f.write("#                     item_id = item_data.pop('id', None) \n")
                
                f.write("#                     if item_id and item_id in existing_items: \n")
                f.write("#                         item_instance = existing_items[item_id] \n")
                
                f.write("#                         for attr, value in item_data.items(): \n")
                f.write("#                             setattr(item_instance, attr, value) \n")
                f.write("#                         item_instance.save() \n")
                f.write("#                         incoming_ids.append(item_id) \n")
                f.write("#                     else: \n")
                f.write("#                         YourDetailsModel.objects.create(parent=instance, **item_data) \n\n")
                f.write("#             # Delete removed items \n")
                f.write("#             for existing_id in existing_items: \n")
                f.write("#                 if existing_id not in incoming_ids: \n")
                f.write("#                     existing_items[existing_id].delete() \n")
                
                f.write("#         except Exception as e: \n")
                f.write("#             return response_error(str(e), status=500, message='Internal server error) \n")
                
                f.write("#         return instance \n\n")




            ##? api views.py
            with open(path.join(base_dir, "views", f"{app_name}.py"), "w") as f:
                f.write("import json, csv, requests, datetime \n")
                f.write("from django.http import HttpResponse \n")
                f.write("from django.conf import settings \n")
                f.write("from django.contrib.auth import get_user_model, get_permission_codename \n\n")
                
                f.write("from django.db import models, transaction, IntegrityError \n")
                f.write("from django.db.models import Q, F, Count, Value, Prefetch \n")
                f.write("from django.db.models.functions import Concat \n\n")
                
                f.write("from django.utils import timezone \n")
                f.write("from django.utils.dateformat import format \n")
                f.write("from django.utils.timezone import make_aware, localtime \n\n")
                
                f.write("from rest_framework import status, generics, permissions \n")
                f.write("from rest_framework.views import APIView \n")
                f.write("from rest_framework.response import Response \n")
                f.write("from rest_framework.validators import ValidationError \n")
                f.write("from rest_framework.filters import SearchFilter, OrderingFilter \n")
                f.write("from rest_framework_simplejwt.authentication import JWTAuthentication \n")
                f.write("from django_filters.rest_framework import DjangoFilterBackend \n\n")
                
                f.write("##? Utils Import \n")
                f.write("#from apis.utils.apiResponse import * \n")
                f.write("#from apis.utils.pagination import CustomPageNumberPagination, get_paginated_response \n\n")
                
                f.write("##? Service Import \n")
                f.write("#ffrom apis.inbound.service import query, filtering, searching, permissions \n\n")
                
                f.write(f"##? Model Import \n")
                f.write("User = get_user_model() \n\n")
                f.write(f"#from apps.{app_name}.models import YourModel, RelatedModel \n\n")
                
                f.write(f"##? Serializer Import \n")
                f.write(f"#from apis.v1.{app_name}.serializers.{app_name} import {app_name_capitalize}Serializer \n\n\n")
                
                f.write("##! Create API Views (POST) \n")
                f.write("#class YourCreateAPIView(generics.CreateAPIView): \n")
                f.write("#    queryset = YourModel.objects.all().order_by('id') \n")
                f.write("#    authentication_classes = [JWTAuthentication] \n")
                f.write("#    permission_classes     = [IsAuthenticatedOrReadOnly] \n")
                f.write("#    serializer_class       = YourModelSerializer \n\n")
                
                f.write("#    def get_queryset(self): \n")
                f.write("#        queryset = super().get_queryset() \n")
                f.write("#        return queryset \n\n")
                f.write("#    def perform_create(self, serializer): \n")
                f.write("#        serializer.save(created_by=self.request.user) \n\n\n")
                f.write("#    def create(self, request, *args, **kwargs): \n")
                f.write("#        try: \n")
                f.write("#            serializer = self.get_serializer(data=request.data) \n")
                f.write("#            if serializer.is_valid(): \n")
                f.write("#                self.perform_create(serializer) \n")
                f.write("#                return response_create(serializer.data, item_name='YourModel') \n")
                f.write("#            else: \n")
                f.write("#                return response_error(serializer.errors, status=400, message='Validation failed') \n")
                f.write("#        except IntegrityError as e: \n")
                f.write("#            return response_error(e, status=400, message='Database integrity error') \n")
                f.write("#        except Exception as e: \n")
                f.write("#            return response_error(e, status=500, message='Internal server error') \n\n\n\n")
                
                f.write("##! List API View (GET) \n")
                f.write("#class YourListAPIView(generics.ListAPIView): \n")
                f.write("#    queryset = YourModel.objects.all().order_by('id') \n")
                f.write("#    authentication_classes = [JWTAuthentication] \n")
                f.write("#    permission_classes     = [IsAuthenticatedOrReadOnly] \n")
                f.write("#    pagination_class       = CustomPageNumberPagination \n")
                f.write("#    serializer_class       = YourModelSerializer \n\n")
                
                f.write("#    def get_queryset(self): \n")
                f.write("#        queryset = query.YourModelData() \n")
                f.write("#        ##? Filtering \n")
                f.write("#        status     = self.request.GET.get('status', 'active') \n")
                f.write("#        start_date = self.request.GET.get('startDate', None) \n")
                f.write("#        end_date   = self.request.GET.get('endDate', None) \n")
                f.write("#        unit_id    = self.request.GET.get('unit_id', None) \n")
                f.write("#        filter_service = filtering.YourFilterService( \n")
                f.write("#            status     = status, \n")
                f.write("#            start_date = start_date, \n")
                f.write("#            end_date   = end_date, \n")
                f.write("#            unit_id    = unit_id, \n")
                f.write("#        ) \n")
                f.write("#        queryset = filter_service.apply_filter(queryset) \n")
                f.write("#        ##? Searching \n")
                f.write("#        search = self.request.GET.get('search', None) \n")
                f.write("#        if search: \n")
                f.write("#            search_service = searching.YourSearchService(search) \n")
                f.write("#            queryset = search_service.apply_search(queryset) \n")
                f.write("#        return queryset \n\n")
                f.write("#    def list(self, request, *args, **kwargs): \n")
                f.write("#        queryset = self.filter_queryset(self.get_queryset()) \n")
                f.write("#        ##? Disable pagination if pagination= 0 or '0' is in query params \n")
                f.write("#        if request.query_params.get('pagination') in (0, '0', 'false', 'False'): \n")
                f.write("#            response_data = get_paginated_response( \n")
                f.write("#                queryset   = queryset, \n")
                f.write("#                request    = request, \n")
                f.write("#                pagination = 0, \n")
                f.write("#                serializer_class = self.get_serializer \n")
                f.write("#            ) \n")
                f.write("#            return response_list(response_data, item_name='YourModel') \n")
                f.write("#        ##? For paginated response  \n")
                f.write("#        else: \n")
                f.write("#            response_data = get_paginated_response( \n")
                f.write("#                queryset = queryset, \n")
                f.write("#                request  = request, \n")
                f.write("#                serializer_class = self.get_serializer \n")
                f.write("#            ) \n")
                f.write("#            return response_list(response_data, item_name='YourModel') \n\n")
                
                f.write("##! Detail API View (GET) \n")
                f.write("#class YourDetailAPIView(generics.RetrieveAPIView): \n") 
                f.write("#    queryset = YourModel.objects.all().order_by('id') \n")
                f.write("#    authentication_classes = [JWTAuthentication] \n")
                f.write("#    permission_classes     = [IsAuthenticatedOrReadOnly] \n")
                f.write("#    serializer_class       = YourModelSerializer \n")
                f.write("#    lookup_field           = 'id' \n\n")   # or 'pk', 'slug', 'uuid' etc field find data from your model
                f.write("#    lookup_url_kwarg       = 'id' \n") # in url.py path('<int:id>/')
                
                f.write("#    def get_queryset(self): \n")
                f.write("#        queryset = query.YourModelData() \n")
                f.write("#        return queryset \n\n")
                
                f.write("#    def retrieve(self, request, *args, **kwargs): \n")
                f.write("#        try: \n")
                f.write("#            instance = self.get_object() \n")
                f.write("#            serializer = self.get_serializer(instance) \n")
                f.write("#            return response_details(serializer.data, item_name='YourModel') \n")
                f.write("#        except Exception as e: \n")
                f.write("#            return response_error(e, status=400, message='Something went wrong') \n\n")
                
                f.write("##! Update API View (PUT/PATCH) \n")
                f.write("#class YourUpdateAPIView(generics.UpdateAPIView): \n")
                f.write("#    queryset = YourModel.objects.all().order_by('id') \n")
                f.write("#    authentication_classes = [JWTAuthentication] \n")
                f.write("#    permission_classes     = [IsAuthenticatedOrReadOnly] \n")
                f.write("#    serializer_class       = YourModelSerializer \n")
                f.write("#    lookup_field           = 'id' \n\n") # or 'pk', 'slug', 'uuid' etc field find data from your model
                f.write("#    lookup_url_kwarg       = 'id' \n") # in url.py path('<int:id>/')
                
                f.write("#    def get_queryset(self): \n")
                f.write("#        queryset = query.YourModelData() \n")
                f.write("#        return queryset \n\n")
                
                f.write("#    def update(self, request, *args, **kwargs): \n")
                f.write("#        partial    = kwargs.pop('partial', False) \n")
                f.write("#        try: \n")
                f.write("#            instance = self.get_object() \n")
                f.write("#            serializer = self.get_serializer(instance, data=request.data, partial=partial) \n")
                f.write("#            #serializer.is_valid(raise_exception=True) \n")
                f.write("#            if serializer.is_valid(): \n")
                f.write("#                self.perform_update(serializer) \n")
                f.write("#                return response_update(serializer.data, serializer=serializer, item_name='YourModel') \n")
                f.write("#            else: \n")
                f.write("#                return response_error(serializer.errors, status=400, message='Validation failed') \n")
                f.write("#        except IntegrityError as e: \n")
                f.write("#            return response_error(str(e), status=400, message='Database integrity error') \n")
                f.write("#        except Exception as e: \n")
                f.write("#            return response_error(str(e), status=500, message='Internal server error') \n\n")
                
                f.write("#def partial_update(self, request, *args, **kwargs): \n")
                f.write("#    kwargs['partial'] = True \n")
                f.write("#    return self.update(request, *args, **kwargs) \n")

                f.write("##! Delete API View (DELETE) \n")
                f.write("#class YourDeleteAPIView(generics.DestroyAPIView): \n")
                f.write("#    queryset = YourModel.objects.all().order_by('id') \n")
                f.write("#    authentication_classes = [JWTAuthentication] \n")
                f.write("#    permission_classes     = [IsAuthenticatedOrReadOnly] \n")
                f.write("#    lookup_field           = 'id' \n\n") # or 'pk', 'slug', 'uuid' etc field find data from your model
                f.write("#    lookup_url_kwarg       = 'id' \n") # in url.py path('<int:id>/')
                
                f.write("#    def get_queryset(self): \n")
                f.write("#        queryset = query.YourModelData() \n")
                f.write("#        return queryset \n\n")
                
                f.write("#    def destroy(self, request, *args, **kwargs): \n")
                f.write("#        try: \n")
                f.write("#            instance = self.get_object() \n")
                f.write("#            self.perform_destroy(instance) \n")
                f.write("#            return response_delete(item=instance, item_name='YourModel', request=request,) \n")
                f.write("#        except IntegrityError as e: \n")
                f.write("#            return response_error(str(e), status=400, message='Database integrity error') \n")
                f.write("#        except Exception as e: \n")
                f.write("#            return response_error(str(e), status=400, message='Something went wrong') \n\n")
                
                f.write("##! Combined Create and List API View \n")
                f.write("#class YourListCreateAPIView(generics.ListCreateAPIView): \n")
                f.write("#    queryset = YourModel.objects.all().order_by('id') \n")
                f.write("#    serializer_class       = YourModelSerializer \n")
                f.write("#    authentication_classes = [JWTAuthentication] \n")
                f.write("#    permission_classes     = [IsAuthenticatedOrReadOnly] \n")
                f.write("#    pagination_class       = CustomPageNumberPagination \n")
                f.write("#    http_method_names      = ['get', 'post'] \n\n")
                
                f.write("#    filter_backends  = [SearchFilter, OrderingFilter, DjangoFilterBackend] \n")
                f.write("#    ordering_fields  = ['id', 'name'] \n")
                f.write("#    search_fields    = ['name'] \n")
                f.write("#    filterset_fields = { \n")  # Some example fields
                f.write("#        'status__name' : ['exact', 'icontains'], \n")
                f.write("#        'created_at'   : ['gte', 'lte'], \n")
                f.write("#        'updated_at'   : ['gte', 'lte'], \n")
                f.write("#        'deleted_at'   : ['isnull'], \n")
                f.write("#        'id'           : ['exact'], \n")
                f.write("#        'name'         : ['exact', 'icontains'], \n")
                f.write("#        'email'        : ['exact', 'icontains'], \n")
                f.write("#        'phone'        : ['exact', 'icontains'], \n")
                f.write("#        'address__zip_code__id' : ['in'], \n")
                f.write("#    } \n\n")
                
                f.write("#    def get_queryset(self): \n")
                f.write("#        #queryset = super().get_queryset() \n")
                f.write("#        queryset = query.YourModelData() \n")
                f.write("#        return queryset \n\n")

                f.write("#    ##? Create (POST) \n")
                f.write("#    def create(self, request, *args, **kwargs): \n")
                f.write("#        try: \n")
                f.write("#            serializer = self.get_serializer(data=request.data) \n")
                f.write("#            if serializer.is_valid(): \n")
                f.write("#                self.perform_create(serializer) \n")
                f.write("#                return response_create(serializer.data, item_name='YourModel') \n")
                f.write("#            else: \n")
                f.write("#                return response_error(serializer.errors, status=400, message='Validation failed') \n")
                f.write("#        except IntegrityError as e: \n")
                f.write("#            return response_error(str(e), status=400, message='Database integrity error') \n")
                f.write("#        except Exception as e: \n")
                f.write("#            return response_error(str(e), status=500, message='Something went wrong') \n\n")
                
                f.write("#    ##? List (GET) \n")
                f.write("#    def list(self, request, *args, **kwargs): \n")
                f.write("#        queryset = self.filter_queryset(self.get_queryset()) \n")
                f.write("#        ##? Disable pagination if pagination= 0 or '0' is in query params \n")
                f.write("#        if request.query_params.get('pagination') in (0, '0', 'false', 'False'): \n")
                f.write("#            response_data = get_paginated_response( \n")
                f.write("#                queryset   = queryset, \n")
                f.write("#                request    = request, \n")
                f.write("#                pagination = 0, \n")
                f.write("#                serializer_class = self.get_serializer \n")
                f.write("#            ) \n")
                f.write("#            return response_list(response_data, item_name='YourModel') \n\n")
                f.write("#        ##! For paginated response \n")
                f.write("#        response_data = get_paginated_response( \n")
                f.write("#            queryset = queryset, \n")
                f.write("#            request  = request, \n")
                f.write("#            serializer_class = self.get_serializer \n")
                f.write("#        ) \n")
                f.write("#        return response_list(response_data, item_name='YourModel') \n\n")

                f.write("##! Combined  Details, Update, Delete (GET/PUT/PATCH/DELETE) API View \n")
                f.write("#class YourRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView): \n")
                f.write("#    queryset = YourModel.objects.all().order_by('id') \n")
                f.write("#    serializer_class       = YourModelSerializer \n")
                f.write("#    authentication_classes = [JWTAuthentication] \n")
                f.write("#    permission_classes     = [IsAuthenticatedOrReadOnly] \n")
                f.write("#    lookup_field           = 'id' \n") # or 'pk', 'slug', 'uuid' etc field find data from your model
                f.write("#    lookup_url_kwarg       = 'id' \n") # in url.py path('<int:id>/')                
                f.write("#    http_method_names      = ['get', 'put', 'patch', 'delete'] \n\n") # Allow only these methods

                f.write("#    ##? Details (GET) \n")
                f.write("#    def retrieve(self, request, *args, **kwargs): \n")
                f.write("#        try: \n")
                f.write("#            instance = self.get_object() \n")
                f.write("#            serializer = self.get_serializer(instance) \n")
                f.write("#            return response_details(serializer.data, item_name='YourModel') \n")
                f.write("#        except Exception as e: \n")
                f.write("#            return response_error(str(e), status=500, message='Something went wrong') \n\n")

                f.write("#    ##? Update (PUT/PATCH) \n")
                f.write("#    def update(self, request, *args, **kwargs): \n")
                f.write("#        partial    = kwargs.pop('partial', False) \n")
                f.write("#        try: \n")
                f.write("#            instance = self.get_object() \n")
                f.write("#            serializer = self.get_serializer(instance, data=request.data, partial=partial) \n")
                f.write("#            if serializer.is_valid(): \n")
                f.write("#                self.perform_update(serializer) \n")
                f.write("#                return response_update(serializer.data, serializer=serializer, item_name='YourModel') \n")
                f.write("#            else: \n")
                f.write("#                return response_error(serializer.errors, status=400, message='Validation failed') \n")
                f.write("#        except IntegrityError as e: \n")
                f.write("#            return response_error(str(e), status=400, message='Database integrity error') \n")
                f.write("#        except Exception as e: \n")
                f.write("#            return response_error(str(e), status=500, message='Something went wrong') \n\n")
                
                f.write("#    def partial_update(self, request, *args, **kwargs): \n")
                f.write("#        kwargs['partial'] = True \n")
                f.write("#        return self.update(request, *args, **kwargs) \n\n")

                f.write("#    ##? Delete (DELETE) \n")
                f.write("#    def destroy(self, request, *args, **kwargs): \n")
                f.write("#        try: \n")
                f.write("#            instance = self.get_object() \n")
                f.write("#            self.perform_destroy(instance) \n")
                f.write("#            return response_delete( \n")
                f.write("#                item      = instance, \n")
                f.write("#                item_name = 'Brand',  # Or self.serializer_class.Meta.model.__name__.lower() \n")
                f.write("#                request   = request, \n")
                f.write("#            ) \n")
                f.write("#        except ProtectedError as e: \n")
                f.write("#            return response_error(error=e, message=\"Cannot delete this item, it's referenced by other records.\") \n")
                f.write("#        except Exception as e: \n")
                f.write("#            return response_error(error=str(e), message=\"An error occurred while deleting the item.\") \n\n")


            ##? urls.py
            with open(path.join(base_dir, "urls.py"), "w") as f:
                f.write("from django.urls import path, include \n\n")
                f.write("#app_name = 'Your APP Name' \n\n")
                
                f.write("##? APIs Import \n\n")
                
                f.write("urlpatterns = [ \n")
                f.write("#    path('', YourCreateAPIView.as_view(), name='your_app_name.create'), # POST (Create)\n")
                f.write("#    path('', YourListAPIView.as_view(), name='your_app_name.list'), # GET (List) \n")
                f.write("#    path('<int:id>/', YourDetailAPIView.as_view(), name='your_app_name.details'), # GET (Details) \n")
                f.write("#    path('<int:id>/update/', YourUpdateAPIView.as_view(), name='your_app_name.update'), # PUT/PATCH (Update) \n")
                f.write("#    path('<int:id>/delete/', YourDeleteAPIView.as_view(), name='your_app_name.delete'), # DELETE (Delete) \n")
                f.write("#    ##? Combined APIs \n")
                f.write("#    path('', YourListCreateAPIView.as_view(), name='your_app_name.list_create'), # GET (List) & POST (Create) \n")
                f.write("#    path('<int:id>/', YourRetrieveUpdateDestroyAPIView.as_view(), name='your_app_name.retrieve_update_destroy'), # GET (Details), PUT/PATCH (Update), DELETE (Delete) \n")
                
                f.write("\n\n")
                f.write("#    path( \n")
                f.write("#        'your_path' \n")
                f.write("#        include([ \n")
                f.write("#            path('create/', YourCreateAPIView.as_view(), name='your_app_name.create'), \n")
                f.write("#            path('list/', YourListAPIView.as_view(), name='your_app_name.list'), \n")
                f.write("#            path('<int:id>/', YourDetailAPIView.as_view(), name='your_app_name.details'), \n")
                f.write("#            path('<int:id>/update/', YourUpdateAPIView.as_view(), name='your_app_name.update'), \n")
                f.write("#            path('<int:id>/delete/', YourDeleteAPIView.as_view(), name='your_app_name.delete'), \n")
                f.write("#        ]) \n")
                f.write("#    ), \n")
                
                f.write(f"] \n\n\n")

            
            ##? Services
            ##* Permissions.py
            with open(path.join(base_dir, "services", "permissions.py"), "w") as f:
                f.write("from rest_framework.permissions import BasePermission \n")
                f.write("from apis.utils.group_checker import user_in_group \n\n")
                
                f.write("#class IsInAllCommercialGroups(BasePermission): \n")
                f.write("#     allowed_groups = ['INBOUND_COMMERCIAL', 'ADMIN'] \n\n")
                f.write("#     def has_permission(self, request, view): \n")
                f.write("#        return user_in_group(request.user, self.allowed_groups) or request.user.is_superuser \n")
                
            ##* searching.py
            with open(path.join(base_dir, "services", "searching.py"), "w") as f:
                f.write("from django.db.models import Q, Prefetch \n\n")
                
                f.write("#class YourSearchService: \n")
                f.write("#    def __init__(self, search_value): \n")
                f.write("#        self.search_value = search_value.strip() \n\n")
                f.write("#    def apply_search(self, queryset): \n")
                f.write("#        if self.search_value: \n")
                f.write("#            queryset = queryset.filter( \n")
                f.write("#                Q(field_name__icontains=self.search_value) \n")
                f.write("#                | Q(another_field__icontains=self.search_value) \n")
                f.write("#            ).distinct() \n")
                f.write("#        return queryset \n")
                
            ##* queries.py
            with open(path.join(base_dir, "services", "queries.py"), "w") as f:
                f.write("from django.db.models import Q, F, Count, Value, Prefetch \n\n")
                f.write("##? Models Import \n\n")
                f.write("#from apps.{app_name}.models import YourModel, RelatedModel \n\n")

                f.write("# def YourQueryService: \n")
                f.write("#     queryset = InboundCourier.objects.select_related( \n")
                f.write("#         'related_field1', \n")
                f.write("#         'related_field2', \n")
                f.write("#         'related_field3', \n")
                f.write("#         'related_field4', \n")
                f.write("#     ).prefetch_related( \n")
                f.write("#         Prefetch('related_set1', queryset=RelatedModel1.objects.all()), \n")
                f.write("#         Prefetch('related_set2', queryset=RelatedModel2.objects.all()), \n")
                f.write("#         Prefetch('related_set3', queryset=RelatedModel3.objects.all()), \n")
                f.write("#         Prefetch('related_set4', queryset=RelatedModel4.objects.all()), \n")
                f.write("#     ).annotate( \n")
                f.write("#         field1_count=Count('related_field1'), \n")
                f.write("#         field2_count=Count('related_field2'), \n")
                f.write("#         field3_count=Count('related_field3'), \n")
                f.write("#         field4_count=Count('related_field4'), \n")
                f.write("#     ).filter( \n")
                f.write("#         Q(field1=F('related_field1')) \n")
                f.write("#         | Q(field2=F('related_field2')) \n")
                f.write("#         | Q(field3=F('related_field3')) \n")
                f.write("#         | Q(field4=F('related_field4')) \n")
                f.write("#     ).order_by('-created_at').distinct() \n")
                f.write("#     return queryset \n")

            ##* filters.py
            with open(path.join(base_dir, "services", "filters.py"), "w") as f:
                f.write("from django.db.models import Q, Prefetch, F, Count, Value \n\n")
                
                f.write("##? Utils Import \n\n")
                f.write("#from apis.utils.time import StartDate, EndDate \n\n")
                
                f.write("##? Models Import \n\n")
                f.write("#from apps.{app_name}.models import YourModel \n\n")
                
                f.write("#class YourFilterService: \n")
                f.write("#    def __init__(self, \n")
                f.write("#        supplier_id = None, \n")
                f.write("#        start_date = None, \n")
                f.write("#        end_date = None, \n")
                f.write("#    ): \n")
                f.write("#        self.supplier_id = supplier_id \n")
                f.write("#        self.start_date = start_date \n")
                f.write("#        self.end_date = end_date \n\n")
                f.write("#    def apply_filters(self, queryset): \n")
                f.write("#        if self.supplier_id: \n")
                f.write("#            queryset = queryset.filter(supplier_id=self.supplier_id) \n")
                f.write("#        if self.start_date: \n")
                f.write("#            queryset =  queryset.filter(date__gte=DateStart(self.start_date)) \n")
                f.write("#        if self.end_date: \n")
                f.write("#            queryset =  queryset.filter(date__lte=DateEnd(self.end_date)) \n")
                f.write("#        return queryset \n")

            self.stdout.write(self.style.SUCCESS(f"{app_name} app created successfully"))


        else:
            self.stdout.write(self.style.ERROR(f"{app_name} app already exists"))

        self.stdout.write(self.style.WARNING("Done. Don't forget to add app to INSTALLED_APPS in settings.py"))






"""#! To Cretae App on apps folder
    #?>> mkdir -p apps/<APP_NAME>
    #?>> python manage.py startapp <APP_NAME> apps/<APP_NAME>
"""
