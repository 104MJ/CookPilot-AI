from django.shortcuts import render


def scan(request):
    return render(request, "pages/scan.html", {"active_page": "scan"})


def result(request, session_id):
    return render(
        request, "pages/result.html", {"active_page": "scan", "session_id": session_id}
    )


def history(request):
    return render(request, "pages/history.html", {"active_page": "history"})
