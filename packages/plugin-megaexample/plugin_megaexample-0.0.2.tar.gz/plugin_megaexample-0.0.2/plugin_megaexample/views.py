
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView
from rest_framework.generics import CreateAPIView
from rest_framework.serializers import Serializer
from testy.core.models import Project

from plugin_megaexample.xlsx_parser_lib.xlsx_parser import XlsxParser


class ProjectListView(ListView):
    model = Project
    queryset = Project.objects.all()
    template_name = 'upload.html'
    context_object_name = 'projects'


class UploadFileApiView(CreateAPIView):
    serializer_class = Serializer

    def create(self, request, *args, **kwargs):
        model_name = request.POST.get('selector')
        project = get_object_or_404(Project, name=model_name)
        file = request.FILES.get('file')
        parser = XlsxParser(file, project.id)
        try:
            suites_count, cases_count = parser.create_suites_with_cases()
            response_text = (
                f'{suites_count} created suites, '
                f'{cases_count} created cases'
            )
        except Exception as ex:
            response_text = f'An error occurred: {ex}'

        request.session['response'] = response_text
        return redirect(reverse('plugins:plugin_megaexample:index'))
