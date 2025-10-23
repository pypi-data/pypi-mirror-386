import requests
from django import forms
from django.utils.crypto import get_random_string
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from wagtail.blocks import BooleanBlock, CharBlock, ChoiceBlock, IntegerBlock
from wagtail.blocks.struct_block import (StructBlock, StructBlockAdapter,
                                         StructValue)
from wagtail.telepath import register


class MediaflowVideoblockValue(StructValue):
    def __init__(self, block, *args):
        self.element_id = get_random_string(
            length=10, allowed_chars="abcdefghijklmnopqrstuvwxyz"
        )
        super().__init__(self, *args)

    @cached_property
    def get_video_data(self):
        r = requests.get(
            "https://m.mediaflow.com/json/" + self.get("media_id"),
            headers={"Accept": "application/json"},
        )
        return r.json()

    @property
    def random_element_id(self):
        return self.element_id

    @property
    def src(self):
        s_param = ""
        m_id = self.get("media_id")
        if self.get("autoplay"):
            s_param = s_param + "autoplay=1&"
        if self.get("start_offset") > 0:
            s_param = s_param + "start=" + str(self.get("start_offset")) + "&"
        if s_param == "":
            return "//play.mediaflowpro.com/ovp/11/" + m_id
        else:
            return "//play.mediaflowpro.com/ovp/11/" + m_id + "?" + s_param[:-1]

    @property
    def name(self):
        try:
            title = (self.get_video_data)["title"]
        except:
            title = ""
        return title

    @property
    def poster(self):
        try:
            p = (self.get_video_data)["poster"]
        except:
            p = "https://assets.mediaflowpro.com/a/ee80c59d46c348ff4bb07b8294d5fad4/poster.jpg"
        return p


class MediaflowVideoBlock(StructBlock):
    media_id = CharBlock(help_text="Media ID")
    autoplay = BooleanBlock(
        help_text="Start playback automatically if possible",
        default=False,
        required=False,
    )
    file_id = IntegerBlock(default=0, required=False)
    folder_id = IntegerBlock(default=0, required=False)
    start_offset = IntegerBlock(
        help_text="Start playback at n seconds into the movie",
        default=0,
        required=False,
    )
    embed_method = ChoiceBlock(
        choices=[
            ("iframe", "IFrame"),
            ("js", "Javascript"),
        ],
        icon="embed",
        help_text="Embed method",
        default="js",
        required=False,
    )

    def get_form_context(self, value, prefix="", errors=None):
        context = super().get_form_context(value, prefix=prefix, errors=errors)
        return context

    class Meta:
        template = "mediaflowvideo/mediaflow-video-block.html"
        icon = "media"
        admin_text = mark_safe("<b>Image Block</b>")
        label = "Mediaflow Video Block"
        value_class = MediaflowVideoblockValue
        form_template = "mediaflowvideo/mediaflow-video-form.html"

    class Media:
        js = ("js/customer_detail.js",)


class MountVideoAdapter(StructBlockAdapter):
    js_constructor = "mediaflowvideo.MediaflowVideoBlock"

    @cached_property
    def media(self):
        structblock_media = super().media
        return forms.Media(
            js=structblock_media._js + ["js/mediaflowvideoblock-telepath.js"],
            # css={"all": ("css/mount-video.css",)},
        )


register(MountVideoAdapter(), MediaflowVideoBlock)
