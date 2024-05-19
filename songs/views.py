from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST


def submit(request):
    return render(request=request, template_name="songs/submit.html")


def detail(request, song_id):
    return HttpResponse("You're looking at song %s." % song_id)


@require_POST
def process_form(request):
    user_input = request.POST.get("userInput")
    return redirect("songs/" + user_input)
