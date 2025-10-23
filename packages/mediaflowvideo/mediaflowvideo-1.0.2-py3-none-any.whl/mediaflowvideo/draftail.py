from django.utils.crypto import get_random_string
from draftjs_exporter.dom import DOM
from wagtail.admin.rich_text.converters.html_to_contentstate import \
    InlineEntityElementHandler


def video_entity_decorator(props):
    """
    Draft.js ContentState to database HTML.
    Converts the video entities into an iframe tag.
    """

    s_param = ""
    src = ""
    m_id = props["mediaId"]
    if props["autoPlay"] == "1":
        s_param = s_param + "autoplay=1&"
    if props["startOffset"] != "0":
        s_param = s_param + "start=" + str(props["startOffset"]) + "&"
    if s_param == "":
        src = "//play.mediaflowpro.com/ovp/11/" + m_id
    else:
        src = "//play.mediaflowpro.com/ovp/11/" + m_id + "?" + s_param[:-1]

    if props["embedMethod"] == "iframe":
        return DOM.create_element(
            "div",
            {
                "id": get_random_string(
                    length=10, allowed_chars="abcdefghijklmnopqrstuvwxyz"
                ),
                "style": "background-image: url(" + props["poster"] + ");",
                "class": "mf-video",
                "data-mediaid": props["mediaId"],
                "data-embed-method": props["embedMethod"],
                "data-autoplay": props["autoPlay"],
                "data-start-offset": props["startOffset"],
                "data-poster": props["poster"],
            },
            DOM.create_element("iframe", {"src": src}, props["children"]),
        )
    return DOM.create_element(
        "div",
        {
            "id": get_random_string(
                length=10, allowed_chars="abcdefghijklmnopqrstuvwxyz"
            ),
            "style": "background-image: url(" + props["poster"] + ");",
            "class": "mf-video",
            "data-mediaid": props["mediaId"],
            "data-embed-method": props["embedMethod"],
            "data-autoplay": props["autoPlay"],
            "data-start-offset": props["startOffset"],
            "data-poster": props["poster"],
        },
        DOM.create_element(
            "script", {"src": "static/js/mediaflow-embed-js.js"}, props["children"]
        ),
    )


class VideoEntityElementHandler(InlineEntityElementHandler):
    mutability = "MUTABLE"

    def get_attribute_data(self, attrs):
        return {
            "mediaId": attrs["data-mediaid"],
            "embedMethod": attrs["data-embed-method"],
            "autoPlay": attrs["data-autoplay"],
            "startOffset": attrs["data-start-offset"],
            "poster": attrs["data-poster"],
        }
