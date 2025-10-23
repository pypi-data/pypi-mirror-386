class VideoSource extends window.React.Component {
  componentDidMount() {
    var dialogOwnerRef = 'draftail' + Math.random().toString().substring(3)

    const { editorState, entityType, onComplete } = this.props
    let adminpath = window.mf.admin_route || "/admin";

    ModalWorkflow({
      url: adminpath + 'mediaflowmodal/?trigger=' + dialogOwnerRef,
    });

    // const content = editorState.getCurrentContent();
    // const entity = content.getEntity()

    // Uses the Draft.js API to create a new entity with the right data.

    window.addEventListener('mf-video-selected', (e) => {
      if (e.detail.trigger == dialogOwnerRef) {
        window.jQuery
          .ajax({
            type: 'GET',
            url: `https://m.mediaflow.com/json/${e.detail.mediaId}`,
          })
          .done((data) => {
            const content = editorState.getCurrentContent()
            const selection = editorState.getSelection()
            const method = e.detail.embedMethod || 'iframe';
            const contentWithEntity = content.createEntity(
              entityType.type,
              'MUTABLE',
              {
                mediaId: e.detail.mediaId || '',
                embedMethod: method,
                autoPlay: e.detail.autoPlay ? '1' : '0',
                startOffset: e.detail.startOffset || 0,
                poster: data.poster
              },
            )
            const entityKey = contentWithEntity.getLastCreatedEntityKey()
            var text = data.title + " (" + method + " embed)";
            console.log(data);
            const newContent = window.DraftJS.Modifier.replaceText(
              content,
              selection,
              text,
              null,
              entityKey,
            )
            const nextState = window.DraftJS.EditorState.push(
              editorState,
              newContent,
              'insert-characters',
            )
            onComplete(nextState)
          })
      }
    })
    onComplete(editorState)
  }

  render() {
    return null
  }
}

const Video = (props) => {
  const { entityKey, contentState } = props
  const data = contentState.getEntity(entityKey).getData()
/*
  if (data.embedMethod == 'iframe') {
    return window.React.createElement(
      'div',
      {
        class: 'mf-video',
        'style': {backgroundImage: `url(${data.poster})`, width:'160px', height:'90px'},
        'data-mediaid': data.mediaId,
        'data-autoplay': data.autoPlay,
        'data-start-offset': data.startOffset,
        'data-embed-method': data.embedMethod,
        'data-poster': data.poster
      },
      window.React.createElement(
        'iframe',
        {          
          src: `https://play.mediaflowpro.com/ovp/11/${data.mediaId}`,
        },
        props.children,
      ),
    )
  }
*/
  return window.React.createElement(
    'div',
    {
      class: 'mf-video',
      'style': {backgroundImage: `url(${data.poster})`, width:'320px', height:'180px'},
      'data-mediaid': data.mediaId,
      'data-autoplay': data.autoPlay,
      'data-start-offset': data.startOffset,
      'data-embed-method': data.embedMethod,
      'data-poster': data.poster
    },
    window.React.createElement('div', {}, props.children),
  )
}

// Register the plugin directly on script execution so the editor loads it when initialising.
window.draftail.registerPlugin(
  {
    type: 'MF_VIDEO',
    source: VideoSource,
    decorator: Video,
  },
  'entityTypes',
)
