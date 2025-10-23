var elid = document.currentScript.parentNode.getAttribute('id');
var mid = document.currentScript.parentNode.getAttribute('data-mediaid');
var autoPlay = document.currentScript.parentNode.getAttribute('data-autoplay') == "1";
var startOffset = parseInt(document.currentScript.parentNode.getAttribute('data-start-offset'));
var opts = {env:"production", autoPlay: autoPlay, startAt: startOffset};
if(!document.querySelector('link[href="https://mfstatic.com/css/mediaflowplayer.min.css"]')) {
        const lel =document.createElement('link');
        lel.setAttribute('rel','stylesheet');
        lel.setAttribute('type','text/css');
        lel.setAttribute('href','https://mfstatic.com/css/mediaflowplayer.min.css');
        document.getElementsByTagName('head')[0].appendChild(lel);
    }
    if(typeof(MFPlayer)=='undefined') {
        const sel = document.createElement('script');
        sel.setAttribute('crossorigin','anonymous');
        document.body.appendChild(sel);
        sel.onload=function(){
            new MFPlayer('#'+elid, mid, opts);
        };
        sel.src='https://mfstatic.com/js/mediaflowplayer.min.js';
    } else {
        new MFPlayer('#'+elid,mid, opts); 
    }
