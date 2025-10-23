# Mediaflow video plugin for Wagtail


## Installation
      pip install mediaflowvideo

### Edit the settings file (mysite/settings/base.py):

 - Add "mediaflowvideo" to the array **INSTALLED_APPS** (near the top of the file)

- Add "mf-video" to the feature list for the Draftail Rich Text Editor 

      WAGTAILADMIN_RICH_TEXT_EDITORS = {
      	'default': {
      		'WIDGET': 'wagtail.admin.rich_text.DraftailRichTextArea',
      		'OPTIONS': {
      			'features': ['mf-video' .....]
      		}
      	}
      }


- Add your API keys
  
      MEDIAFLOW_CLIENT_ID = <YOUR SERVER ID>
      MEDIAFLOW_CLIENT_SECRET = <YOUR CLIENT SECRET>
      MEDIAFLOW_SERVER_KEY = <YOUR SERVER KEY>

  
### Using the plugin

TODO
