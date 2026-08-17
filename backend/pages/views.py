from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def scan(request):
    return render(request, "pages/scan.html", {"active_page": "scan"})


@login_required
def result(request, session_id):
    return render(
        request, "pages/result.html", {"active_page": "scan", "session_id": session_id}
    )


@login_required
def history(request):
    return render(request, "pages/history.html", {"active_page": "history"})


@login_required
def profile(request):
    return render(request, "pages/profile.html", {"active_page": "profile"})
