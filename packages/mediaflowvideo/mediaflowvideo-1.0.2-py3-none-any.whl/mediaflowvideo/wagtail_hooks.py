import re

import requests
import wagtail.admin.rich_text.editors.draftail.features as draftail_features
from django.conf import settings
from django.urls import path, reverse
from django.utils.html import format_html
from wagtail import hooks
from wagtail.admin.rich_text.converters.html_to_contentstate import \
    BlockElementHandler

from .draftail import VideoEntityElementHandler, video_entity_decorator
from .views import mediaflow_modal


@hooks.register("register_admin_urls")
def register_mediaflow_urls():
    return [
        path("mediaflowmodal/", mediaflow_modal, name="Mediaflow Video Selector"),
    ]


@hooks.register("insert_editor_js")
def fileselector_js():
    return format_html(
        '<script src="https://mfstatic.com/js/fileselector.min.js"></script>'
    )


@hooks.register("after_publish_page")
def register_file_usage(request, page):    
    # Call the process_data method on the page
    for field in page.specific._meta.fields:
        name = str(field)        
        try:
            short_name = name[name.rindex(".") + 1 :]
        except:
            break
        if ("wagtailcore" not in name) and ("page_ptr" not in short_name):

            val = str(getattr(page.specific, short_name, None))            
            matches = re.findall(r"data-mf-video-id=\"([0-9]+)\"",val)            
            
            for id_image in matches:
                try:
                    report_usage(page, id_image)                   
                except:                    
                    pass


@hooks.register("register_rich_text_features")
def register_help_text_feature(features):
    """
    Registering the `mf-video` feature, which uses the `mf-video` Draft.js block type,
    and is stored as HTML with a `<div class="mf-video">` tag.
    """
    feature_name = "mf-video"
    type_ = "mf-video"

    control = {
        "type": type_,
        "icon": "media",
        "description": "Mediaflow Video",
        # Optionally, we can tell Draftail what element to use when displaying those blocks in the editor.
        "element": "div",
    }

    features.register_editor_plugin(
        "draftail",
        feature_name,
        draftail_features.BlockFeature(
            control, css={"all": ["mf-video.css"]}, js=["js/draftail-videoblock.js"]
        ),
    )

    features.register_converter_rule(
        "contentstate",
        feature_name,
        {
            "from_database_format": {
                "iframe[class=mf-video]": BlockElementHandler(type_)
            },
            "to_database_format": {
                "block_map": {
                    type_: {"element": "iframe", "props": {"class": "mf-video"}}
                }
            },
        },
    )


@hooks.register("register_rich_text_features")
def register_video_feature(features):
    features.default_features.append("mf-video")
    feature_name = "mf-video"
    type_ = "MF_VIDEO"

    control = {
        "type": type_,
        "icon": "media",
        "description": "Mediaflow video",
    }

    features.register_editor_plugin(
        "draftail",
        feature_name,
        draftail_features.EntityFeature(
            control,
            js=["js/draftail-videoentity.js"],
            css={"all": ["css/draftail-videoentity.css"]},
        ),
    )

    features.register_converter_rule(
        "contentstate",
        feature_name,
        {
            # Note here that the conversion is more complicated than for blocks and inline styles.
            "from_database_format": {
                "div[class=mf-video]": VideoEntityElementHandler(type_)
            },
            "to_database_format": {
                "entity_decorators": {type_: video_entity_decorator}
            },
        },
    )

                       
def report_usage(page, id_image):
    req = requests.get(
        "https://api.mediaflow.com/1/oauth2/token?client_id=" + getattr(settings, "MEDIAFLOW_CLIENT_ID", "") + 
        "&client_secret=" + getattr(settings, "MEDIAFLOW_CLIENT_SECRET", "") + "&grant_type=refresh_token&refresh_token=" + getattr(settings, "MEDIAFLOW_SERVER_KEY", ""),
        headers={"Accept": "application/json"},
    )
    token = req.json()["access_token"]
    web = {"page": page.full_url, "pageName": page.title}
    post_data = {
        "contact": str(page.owner),
        "types": ["web"],
        "web": web,
        "project": str(page.get_site()),
        "date": str(page.last_published_at),
    }
    req = requests.post(
        "https://api.mediaflow.com/1/file/"
        + str(id_image)
        + "/usage?access_token="
        + token,
        json=post_data,
        headers={"Accept": "application/json"},
    )
    
# Inject the Wagtail admin path into a global JS variable so we can use it in our JS code
@hooks.register("insert_global_admin_js")
def set_admin_path():
    return str("<script> window.mf = window.mf || { admin_route: '" + reverse("wagtailadmin_home") + "' } </script>")