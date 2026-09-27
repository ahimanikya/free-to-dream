// Engagement describes observable site actions, never a confirmed social post.
export const METRIC_EVENTS = new Set(['page_view','play_start','play_30s','listen_progress','listen_complete','share_intent','download_click','contribution_handoff']);
const textParams = new Set(['recording_id','language','method','media_kind','contribution_type']);
export function cleanEvent(name, params = {}) {
  if (!METRIC_EVENTS.has(name)) return null;
  const clean = {};
  for (const [key,value] of Object.entries(params)) {
    if (textParams.has(key) && typeof value === 'string' && /^[a-z0-9_-]{1,100}$/.test(value)) clean[key] = value;
    if (['progress_percent','listen_seconds'].includes(key) && Number.isFinite(value) && value >= 0) clean[key] = Math.round(value);
  }
  return {name,params:clean};
}
export function mediaMeter(media, emit, clock = () => performance.now()) {
  let key = '', started = false, finished = false, running = false, seconds = 0, lastTime = null, lastWall = null;
  const sent = new Set();
  const context = () => ({recording_id:media.dataset.recordingId, language:media.dataset.language, media_kind:media.tagName?.toLowerCase() === 'video' ? 'video' : 'audio'});
  const reset = () => {started=false;finished=false;running=false;seconds=0;lastTime=null;lastWall=null;sent.clear();};
  function marks() {
    const send = (name, extra={}) => emit(name,{...context(),listen_seconds:seconds,...extra});
    if(seconds >= 30 && !sent.has('30s')) {sent.add('30s');send('play_30s');}
    if(!Number.isFinite(media.duration)||media.duration<=0)return;
    for(const percent of [25,50,75,90]) if(seconds >= media.duration*percent/100 && !sent.has(percent)) {
      sent.add(percent);send(percent===90?'listen_complete':'listen_progress',{progress_percent:percent});
    }
  }
  function sample() {
    const wall=clock(), time=media.currentTime;
    if(running && !media.seeking && lastTime!==null && Number.isFinite(time)) {
      const elapsed=Math.max(0,(wall-lastWall)/1000), movement=time-lastTime;
      // Seeking cannot turn a jumped position into listened time.
      if(movement>=0 && movement<=elapsed*2+1)seconds+=Math.min(elapsed,movement/Math.max(media.playbackRate||1,.1));
      marks();
    }
    lastWall=wall;lastTime=Number.isFinite(time)?time:null;
  }
  function begin() {
    const nextKey=[media.dataset.recordingId,media.dataset.playbackToken||'',media.currentSrc||media.src].join('|');
    if(nextKey!==key||finished){reset();key=nextKey;}
    if(!media.dataset.recordingId)return;
    if(!started){started=true;emit('play_start',context());}
    running=true;lastTime=media.currentTime;lastWall=clock();
  }
  media.addEventListener('playing',begin);
  media.addEventListener('timeupdate',sample);
  for(const event of ['pause','waiting','stalled'])media.addEventListener(event,()=>{sample();running=false;});
  media.addEventListener('seeking',()=>{lastTime=null;});
  media.addEventListener('seeked',()=>{lastTime=media.currentTime;lastWall=clock();});
  media.addEventListener('ended',()=>{sample();running=false;finished=true;});
  media.addEventListener('emptied',reset);
  return {reset,restart(){reset();if(!media.paused&&!media.ended)begin();},seconds:()=>seconds};
}
export function analyticsAllowed({id,site,location,consent,gpc=false,dnt=false}) {
  try {return /^G-[A-Z0-9]{6,20}$/.test(id||'') && new URL(site).origin===location.origin && location.pathname.startsWith(new URL(site).pathname.replace(/\/$/,'')+'/') && consent==='yes' && !gpc && !dnt;}
  catch{return false;}
}
export function setupEngagement(doc = document, win = window) {
  const id = doc.body.dataset.analyticsId || '', site = doc.body.dataset.siteUrl;
  const key='world-is-one-analytics-consent-v1';
  let consent='unknown', tagLoaded=false, active=false, viewed=false;
  const meters=[];
  try{consent=win.localStorage.getItem(key)||'unknown';}catch{}
  const blocked = win.navigator.globalPrivacyControl === true || win.navigator.doNotTrack === '1';
  const context=()=>{
    const player=doc.querySelector('audio[data-recording-id],video[data-recording-id]');
    return {language:doc.querySelector('.language-page')?.dataset.language||player?.dataset.language,
      recording_id:player?.dataset.recordingId};
  };
  function gtag(){win.dataLayer=win.dataLayer||[];win.dataLayer.push(arguments);}
  function send(name,params={}) {
    if(!active)return;
    const event=cleanEvent(name,params);if(!event)return;
    gtag('event',event.name,{...event.params,send_to:id,page_location:win.location.origin+win.location.pathname,page_referrer:doc.referrer?new URL(doc.referrer).origin:'',page_title:doc.title});
  }
  function enable() {
    active=analyticsAllowed({id,site,location:win.location,consent,gpc:blocked});
    if(!active)return;
    win['ga-disable-'+id]=false;
    if(!tagLoaded){
      gtag('consent','default',{analytics_storage:'granted',ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied'});
      gtag('js',new Date());
      gtag('config',id,{send_page_view:false,allow_google_signals:false,allow_ad_personalization_signals:false,
        cookie_path:new URL(site).pathname.replace(/\/$/,'')||'/',page_location:win.location.origin+win.location.pathname,page_referrer:doc.referrer?new URL(doc.referrer).origin:''});
      const script=doc.createElement('script');script.async=true;script.src='https://www.googletagmanager.com/gtag/js?id='+id;doc.head.append(script);tagLoaded=true;
    } else gtag('consent','update',{analytics_storage:'granted'});
    for(const meter of meters)meter.restart();
    if(!viewed){send('page_view',context());viewed=true;}
  }
  const settings=doc.querySelector('#analytics-settings'), banner=doc.querySelector('#analytics-consent');
  const message=doc.querySelector('#analytics-consent-message');
  const eligible=/^G-[A-Z0-9]{6,20}$/.test(id);
  const updateNotice=()=>{if(message)message.textContent=blocked?'Your browser asks not to be tracked. Analytics is off.':eligible?'Allow optional analytics to help us understand which songs people enjoy? Google Analytics receives page views and listening/share actions. It uses analytics cookies. No advertising features or feedback text are sent.':'Analytics is not connected. No visitor analytics is being collected.';};
  updateNotice();
  if(banner)banner.hidden=!(eligible&&consent==='unknown'&&!blocked);
  settings?.addEventListener('click',()=>{updateNotice();banner.hidden=!banner.hidden;});
  for(const button of doc.querySelectorAll('[data-analytics-consent]')) {
    if(button.dataset.analyticsConsent==='yes')button.disabled=!eligible||blocked;
    button.addEventListener('click',()=>{
      consent=button.dataset.analyticsConsent;
      try{win.localStorage.setItem(key,consent);}catch{}
      if(consent==='yes')enable();
      else {
        active=false;win['ga-disable-'+id]=true;
        if(tagLoaded)gtag('consent','update',{analytics_storage:'denied'});
        const path=new URL(site).pathname.replace(/\/$/,'')||'/';
        for(const name of ['_ga','_ga_'+id.slice(2)])for(const domain of ['',`; Domain=${win.location.hostname}`,`; Domain=.${win.location.hostname}`])doc.cookie=name+'=; Max-Age=0; Path='+path+domain+'; SameSite=Lax';
      }
      banner.hidden=true;
    });
  }
  for(const media of doc.querySelectorAll('audio,video')) {
    if(media.closest('#timing-workspace'))continue;
    meters.push(mediaMeter(media,(name,params)=>send(name,params)));
  }
  enable();
  doc.addEventListener('collection-engagement',event=>send(event.detail?.name,event.detail?.params));
  doc.addEventListener('click',event=>{
    const target=event.target.closest('a,button');if(!target||target.disabled)return;
    const panel=target.closest('.sharing');
    const recording=target.closest('[data-recording-id]');
    const params={...context(),...(recording?.dataset.recordingId?{recording_id:recording.dataset.recordingId}:{}),...(recording?.dataset.language?{language:recording.dataset.language}:{})};
    if(target.id==='github-submit')send('contribution_handoff',{language:doc.querySelector('#contribution-language')?.value,contribution_type:doc.querySelector('#contribution-type')?.value});
    if(panel&&['share-link','share-file','copy-link','copy-caption'].includes(target.dataset.action))send('share_intent',{...params,method:target.dataset.action.replaceAll('-','_')});
    if(target.tagName!=='A')return;
    const url=new URL(target.href,win.location.href);
    const methods={'www.facebook.com':'facebook','twitter.com':'x','www.linkedin.com':'linkedin','www.instagram.com':'instagram','wa.me':'whatsapp'};
    if(panel&&methods[url.hostname])send('share_intent',{...params,method:methods[url.hostname]});
    if(target.hasAttribute('download')||/\.(mp3|m4a|mp4|srt|vtt)$/.test(url.pathname))send('download_click',{...params,method:/\.(mp3|m4a|mp4|srt|vtt|png|jpg|md)$/.exec(url.pathname)?.[1]||'file'});
  });
  return {send};
}
