from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from NEMO.models import Project, User
from NEMO.utilities import EmailCategory, render_email_template, send_mail
from NEMO.views.customization import ApplicationCustomization, EmailsCustomization, get_media_file_contents


@login_required
@require_http_methods(["GET", "POST"])
def facility_rules(request):
    if request.method == "GET":
        tutorial = get_media_file_contents("facility_rules_tutorial.html")
        if tutorial:
            dictionary = {
                "active_user_count": User.objects.filter(is_active=True).count(),
                "active_project_count": Project.objects.filter(active=True).count(),
            }
            tutorial = render_email_template(tutorial, dictionary, request)
        return render(request, "facility_rules.html", {"facility_rules_tutorial": tutorial})
    elif request.method == "POST":
        facility_name = ApplicationCustomization.get("facility_name")
        summary = request.POST.get("making_reservations_summary", "").strip()[:3000]
        dictionary = {"user": request.user, "making_reservations_rule_summary": summary}
        abuse_email = EmailsCustomization.get("abuse_email_address")
        email_contents = get_media_file_contents("facility_rules_tutorial_email.html")
        if abuse_email and email_contents:
            message = render_email_template(email_contents, dictionary, request)
            send_mail(
                subject=f"{facility_name} rules tutorial",
                content=message,
                from_email=abuse_email,
                to=[abuse_email],
                email_category=EmailCategory.SYSTEM,
            )
        dictionary = {
            "title": f"{facility_name} rules tutorial",
            "heading": "Tutorial complete!",
            "content": "Tool usage and reservation privileges have been enabled on your user account.",
        }
        request.user.training_required = False
        request.user.save()
        return render(request, "acknowledgement.html", dictionary)
