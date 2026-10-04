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
 await edge_tts.Communicate(text,voice).save(out)
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
div.stTextArea textarea{background:rgba(255,255,255,.08)!important;color:#fff!important;border-radius:12px;border:1px solid rgba(255,255,255,.18)!important}
div.stSelectbox>div>div{background:rgba(255,255,255,.08)!important;color:#fff!important;border-radius:12px}
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
 tts=get_tts();voice=VOICES[vname]
 wd=OD/"segs";wd.mkdir(exist_ok=True)
 if voice!="mms":
  try:
   synth_edge("စမ်းသပ်နေပါတယ်",voice,wd/"_t.wav");(wd/"_t.wav").unlink()
  except Exception:
   st.warning("အွန်လိုင်းအသံ မရလို့ MMS offline အသံ သုံးမယ်")
   voice="mms"
 ins=[];flt=[]
 bar=st.progress(0,"အသံထုတ်နေတယ်...")
 for i,(a,b,t) in enumerate(E):
  sg=wd/f"seg{i:02d}.wav"
  if voice=="mms":synth_mms(tts,t,sg)
  else:synth_edge(t,voice,sg)
  d=wdur(sg);slot=b-a;ch=f"[{i+1}:a]"
  if d>slot:ch+=f"atempo={min(d/slot,1.6):.3f},"
  ms=int(a*1000);ch+=f"adelay={ms}|{ms}[s{i}]";flt.append(ch);ins+=["-i",str(sg)]
  bar.progress((i+1)/len(E),f"အပိုင်း {i+1}/{len(E)}...")
 flt.append("".join(f"[s{i}]"for i in range(len(E)))+f"amix=inputs={len(E)}:duration=longest:dropout_transition=0:normalize=0[mix]")
 st_tmp=wd/"subs.srt";st_tmp.write_text(s,encoding="utf-8")
 vfs=[]
 if crop:vfs.append("crop=iw:ih*0.88")
 if burn:vfs.append(f"subtitles={st_tmp}:fontsdir={FD}:force_style='FontName=Noto Sans Myanmar,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,BorderStyle=1,Outline=2,Alignment=2,MarginV=35'")
