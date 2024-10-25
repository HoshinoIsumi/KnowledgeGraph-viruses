from django.shortcuts import render, get_object_or_404
from .models import VirusInfo

def virus_list(request):
    viruses = VirusInfo.objects.all()
    return render(request, 'myapp/virus_list.html', {'viruses': viruses})

def virus_detail(request, virus_id):
    virus = get_object_or_404(VirusInfo, id=virus_id)
    return render(request, 'myapp/virus_detail.html', {'virus': virus})