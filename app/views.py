from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from .forms import CreateRackForm, UpdateRackForm
from .models import Rack


# Create your views here.
def index(request):
    context = {}
    return render(request, 'app/index.html', context)


class RackCreateView(CreateView):
    model = Rack
    form_class = CreateRackForm
    template_name = "app/rack_create_form.html"


class RackUpdateView(UpdateView):
    model = Rack
    form_class = UpdateRackForm
    template_name = "app/rack_update_form.html"


class RackDetailView(DetailView):
    model = Rack
    template_name = "app/rack_detail.html"


class RackListView(ListView):
    model = Rack
    template_name = "app/rack_list.html"


class RackDeleteView(DeleteView):
    model = Rack
    template_name = "app/rack_delete.html"
    success_url = reverse_lazy('rack-list')
