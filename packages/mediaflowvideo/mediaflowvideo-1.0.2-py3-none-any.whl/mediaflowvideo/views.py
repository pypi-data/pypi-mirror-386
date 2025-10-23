from django.conf import settings
from django.utils import translation
from wagtail.admin.modal_workflow import render_modal_workflow


# Create your views here.
def mediaflow_modal(request):
    client_id = getattr(settings, "MEDIAFLOW_CLIENT_ID", "")
    client_secret = getattr(settings, "MEDIAFLOW_CLIENT_SECRET", "")
    server_key = getattr(settings, "MEDIAFLOW_SERVER_KEY", "")

    return render_modal_workflow(
        request,
        "mediaflowvideo/mediaflow-video-modal.html",  # html template
        None,
        {
            "locale": translation.get_language(),
            "trigger": request.GET.get("trigger"),
            "client_secret": client_secret,
            "client_id": client_id,
            "server_key": server_key,            
        },  # html template vars
        json_data={"step": "choose"},
    )
