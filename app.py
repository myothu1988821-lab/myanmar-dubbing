import re,subprocess,urllib.request,wave,asyncio
from pathlib import Path
import imageio_ffmpeg,numpy as np,streamlit as st
MU="https://huggingface.co/willwade/mms-tts-multilingual-models-onnx/resolve/main/mya/"
MD,OD,FD=Path("model"),Path("outputs"),Path("fonts");OD.mkdir(exist_ok=True)
FU="https://raw.githubusercontent.com/google/fonts/main/ofl/notosansmyanmar/NotoSansMyanmar%5Bwdth%2Cwght%5D.ttf"
ff=imageio_ffmpeg.get_ffmpeg_exe()
PH="1\n00:00:00,000 --> 00:00:04,000\nဒီမှာ ဇာတ်ပြောစာသား ရေးပါ"
VOICES={"Nilar (မိန်းကလေးအသံ)":"my-MM-NilarNeural","Thiha (ယောက်ျားအသံ)":"my-MM-ThihaNeural","MMS (offline အသံ)":"mms"}
@st.cache_resource(show_spinner="Model ဒေါင်းနေတယ်...")
def get_tts():
 import sherpa_onnx;MD.mkdir(exist_ok=True)
 for n in("model.onnx","tokens.txt"):
  d=MD/n
  if not d.exists():urllib.request.urlretrieve(MU+n,d)
 m=sherpa_onnx.OfflineTtsVitsModelConfig(model=str(MD/"model.onnx"),tokens=str(MD/"tokens.txt"),lexicon="",noise_scale=0.667,noise_scale_w=0.8,length_scale=1.0)
 c=sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(vits=m,num_threads=2,debug=False,provider="cpu"))
 return sherpa_onnx.OfflineTts(c)
def font():
 FD.mkdir(exist_ok=True);d=FD/"NotoSansMyanmar.ttf"
 if not d.exists():
  try:urllib.request.urlretrieve(FU,d)
  except Exception:raise RuntimeError("Font download မအောင်မြင်ပါ")
 return d
def parse_srt(t):
 o=[]
 for b in t.strip().split("\n\n"):
  L=b.strip().splitlines()
  if len(L)<3:continue
  m=re.match(r"(\d+):(\d+):(\d+),(\d+)\s*-->\s*(\d+):(\d+):(\d+),(\d+)",L[1])
  if not m:continue
  g=list(map(int,m.groups()));s=" ".join(L[2:]).strip()
  if s:o.append((g[0]*3600+g[1]*60+g[2]+g[3]/1000,g[4]*3600+g[5]*60+g[6]+g[7]/1000,s))
 return o
def synth_mms(tts,text,out):
 a=tts.generate(text,sid=0,speed=1.0);p=(np.array(a.samples)*32767).astype(np.int16)
 w=wave.open(str(out),"w");w.setnchannels(1);w.setsampwidth(2);w.setframerate(a.sample_rate);w.writeframes(p.tobytes());w.close()
async def _edge(text,voice,out):
 import edge_tts
 await asyncio.wait_for(edge_tts.Communicate(text,voice).save(out),timeout=20)
def synth_edge(text,voice,out):
 mp3=str(out)[:-4]+".mp3"
 asyncio.run(_edge(text,voice,mp3))
 subprocess.run([ff,"-y","-v","error","-i",mp3,"-ar","24000","-ac","1",str(out)],check=True,stdin=subprocess.DEVNULL)
 Path(mp3).unlink()
def wdur(p):
 w=wave.open(str(p));d=w.getnframes()/w.getframerate();w.close();return d
st.set_page_config(page_title="Myanmar Story Dubbing",page_icon="🇲🇲")
CSS="""<style>
.stApp{background:linear-gradient(135deg,#0f2027 0%,#203a43 55%,#2c5364 100%)}
.stApp h1{background:linear-gradient(90deg,#7fe7dc,#ffd76e);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:800}
.stApp p,.stApp label,.stMarkdown{color:#eaf6f6!important}
div.stButton>button{background:linear-gradient(90deg,#00bfa5,#00acc1);color:#fff;border:none;border-radius:12px;padding:.6rem 2rem;font-size:1.1rem;font-weight:700;box-shadow:0 4px 14px rgba(0,191,165,.35);width:100%}
div.stButton>button:hover{filter:brightness(1.12)}
div[data-testid="stTextArea"] textarea{background-color:#16323c!important;color:#fff!important;border-radius:12px;border:1px solid rgba(255,255,255,.3)!important}
div[data-testid="stTextArea"] textarea::placeholder{color:rgba(255,255,255,.45)!important}
div[data-testid="stSelectbox"] div[data-baseweb="select"]>div{background-color:#16323c!important;border-radius:12px}
div[data-testid="stSelectbox"] span{color:#fff!important}
section[data-testid="stFileUploader"]{background:rgba(255,255,255,.06);border-radius:14px;padding:1rem;border:1px dashed rgba(255,255,255,.3)}
.stAlert{border-radius:12px}
header[data-testid="stHeader"]{background:rgba(0,0,0,0)}
footer{visibility:hidden}
</style>"""
st.markdown(CSS,unsafe_allow_html=True)
st.title("🇲🇲 Myanmar Story Dubbing")
st.markdown("🎬 <b>Video</b> + 📝 <b>မြန်မာ SRT</b> → 🔊 <b>အသံမြန်မာဇာတ်ပြောသံ video</b>",unsafe_allow_html=True)
st.write("")
st.warning("⚠️ English စာလုံးတွေကို မြန်မာလို အသံထွက်ရေးပေးပါ")
v=st.file_uploader("Video (.mp4) တင်ပါ",type=["mp4","mov"])
s=st.text_area("SRT စာတား",height=250,placeholder=PH)
vname=st.selectbox("အသံ ရွေးပါ",list(VOICES.keys()))
burn=st.checkbox("စာတန်းပါ video ထဲမှာ ကပ်မယ် (burn subtitles)")
crop=st.checkbox("🔇 မူရင်း Eng/China စာတန်း ဖျောက်မယ် (အောက်ခြေ 12% ဖြတ်မယ်)")
if st.button("🎙️ Dub လုပ်မယ်",type="primary"):
 if not v:st.error("Video file တင်ပေးပါ။");st.stop()
 if not s.strip():st.error("SRT စာတား ထည့်ပေးပါ။");st.stop()
 E=parse_srt(s)
 if not E:st.error("SRT format မှားနေတယ်");st.stop()
 vp=OD/"input.mp4";vp.write_bytes(v.getvalue())
 voice=VOICES[vname];tts=None
 wd=OD/"segs";wd.mkdir(exist_ok=True)
 status=st.empty()
 bar=st.progress(0,"စတင်နေတယ်...")
 SR=24000
 def prep(p,slot):
  d=wdur(p);q=p.with_suffix(".adj.wav")
  fa=f"atempo={min(d/slot,1.6):.3f}," if d>slot else ""
  subprocess.run([ff,"-y","-v","error","-i",str(p),"-filter:a",f"{fa}aresample={SR}","-ac","1",str(q)],check=True,stdin=subprocess.DEVNULL,capture_output=True)
  return q
 def rwav(p):
  w=wave.open(str(p));n=w.getnframes();pcm=np.frombuffer(w.readframes(n),dtype=np.int16).astype(np.float32);w.close();return pcm
 bar=st.progress(0,"အသံထုတ်နေတယ်...")
 segs=[];use_edge=(voice!="mms")
 for i,(a,b,t) in enumerate(E):
  sg=wd/f"seg{i:02d}.wav";ok=False
  if use_edge:
   status.info(f"🌐 အွန်လိုင်းအသံဖြင့် အပိုင်း {i+1}/{len(E)} ထုတ်နေတယ်...")
   try:synth_edge(t,voice,sg);ok=True
   except Exception:st.warning("အွန်လိုင်းအသံ မရလို့ MMS offline အသံနဲ့ ဆက်လုပ်မယ်");use_edge=False
  if not ok:
