"""Myanmar Story Dubbing - Streamlit Cloud (free)."""
import re, subprocess, urllib.request, wave
from pathlib import Path
import imageio_ffmpeg
import numpy as np
import streamlit as st

MU = "https://huggingface.co/willwade/mms-tts-multilingual-models-onnx/resolve/main/mya/"
MD, OD, FD = Path("model"), Path("outputs"), Path("fonts")
OD.mkdir(exist_ok=True)
FU = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosansmyanmar/NotoSansMyanmar%5Bwdth%2Cwght%5D.ttf"
ff = imageio_ffmpeg.get_ffmpeg_exe()
PH = "1\n00:00:00,000 --> 00:00:04,000\n\u1012\u102e\u1019\u102c \u1007\u102c\u1010\u103a\u1015\u103c\u1031\u102c\u1005\u102c\u1010\u102d\u102f\u1019\u103a\u1038 \u1005\u102c\u1010\u1014\u1031\u1038 \u101b\u1031\u1038\u1015\u102b"

@st.cache_resource(show_spinner="Model \u1006\u1031\u102c\u1004\u103a\u1038\u1014\u1031\u1010\u101a\u103a...")
def get_tts():
    import sherpa_onnx
    MD.mkdir(exist_ok=True)
    for n in ("model.onnx", "tokens.txt"):
        d = MD / n
        if not d.exists():
            urllib.request.urlretrieve(MU + n, d)
    c = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                model=str(MD / "model.onnx"), tokens=str(MD / "tokens.txt"),
                lexicon="", noise_scale=0.667, noise_scale_w=0.8, length_scale=1.0),
            num_threads=2, debug=False, provider="cpu"))
    return sherpa_onnx.OfflineTts(c)

def font():
    FD.mkdir(exist_ok=True)
    d = FD / "NotoSansMyanmar.ttf"
    if not d.exists():
        try:
            urllib.request.urlretrieve(FU, d)
        except Exception:
            raise RuntimeError("Font download \u1019\u1006\u102c\u1004\u103a\u1019\u103b\u1004\u103a\u1015\u102b - 'burn subtitles' \u1016\u103c\u102f\u1010\u103a\u1015\u102b")
    return d

def parse_srt(t):
    out = []
    for b in t.strip().split("\n\n"):
        L = b.strip().splitlines()
        if len(L) < 3:
            continue
        m = re.match(r"(\d+):(\d+):(\d+),(\d+)\s*-->\s*(\d+):(\d+):(\d+),(\d+)", L[1])
        if not m:
            continue
        g = list(map(int, m.groups()))
        s = " ".join(L[2:]).strip()
        if s:
            out.append((g[0]*3600+g[1]*60+g[2]+g[3]/1000, g[4]*3600+g[5]*60+g[6]+g[7]/1000, s))
    return out

def vdur(p):
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)",
                  subprocess.run([ff, "-i", str(p)], capture_output=True, text=True).stderr)
    return int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))

def synth(tts, text, out):
    a = tts.generate(text, sid=0, speed=1.0)
    pcm = (np.array(a.samples) * 32767).astype(np.int16)
    with wave.open(str(out), "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(a.sample_rate)
        w.writeframes(pcm.tobytes())

def wdur(p):
    with wave.open(str(p)) as w:
        return w.getnframes() / w.getframerate()

st.set_page_config(page_title="Myanmar Story Dubbing", page_icon="\U0001f1f2\U0001f1f2")
st.title("\U0001f1f2\U0001f1f2 Myanmar Story Dubbing")
st.write("Video + \u1019\u103c\u1014\u103a\u1019\u102c SRT \u1005\u102c\u1010\u1014\u103a\u1038 \u2192 \u1021\u1001\u103b\u102d\u1014\u103a\u1019\u103e\u1014\u103a\u1010\u1032\u1037 \u1019\u103c\u1014\u103a\u1019\u102c\u1007\u102c\u1010\u103a\u1015\u103c\u1031\u102c\u101e\u1036\u1015\u102b\u1010\u1032\u1037 video")
st.warning("\u26a0\ufe0f English \u1005\u102c\u101c\u102f\u1036\u1038\u1010\u103d\u1031\u1000\u102d\u102f \u1019\u103c\u1014\u103a\u1019\u102c\u101c\u102d\u102f \u1021\u101e\u1036\u1011\u103d\u1000\u103a\u101b\u1031\u1038\u1015\u1031\u1038\u1015\u102b (\u1025\u1015\u1019\u102c Thiha \u2192 \u101e\u102e\u101f)")
v = st.file_uploader("Video (.mp4) \u1010\u1004\u103a\u1015\u102b", type=["mp4", "mov"])
s = st.text_area("SRT \u1005\u102c\u1010\u102c\u1038", height=250, placeholder=PH,
                 help="\u1014\u1019\u1030\u1014\u102c\u1021\u1010\u102d\u102f\u1004\u103a\u1038 \u1021\u1001\u103b\u102d\u1014\u103a\u1019\u103e\u1014\u103a\u1010\u1032\u1037 \u101b\u1031\u1038\u1015\u102b")
burn = st.checkbox("\u1005\u102c\u1010\u1014\u103a\u1038\u1015\u102b video \u1011\u1032\u1019\u103e\u102c \u1000\u1015\u103a\u1019\u101a\u103a (burn subtitles)")

if st.button("\U0001f399\ufe0f Dub \u101c\u102f\u1015\u103a\u1019\u101a\u103a", type="primary"):
    if not v:
        st.error("Video file \u1010\u1004\u103a\u1015\u1031\u1038\u1015\u102b\u104b")
        st.stop()
    if not s.strip():
        st.error("SRT \u1005\u102c\u1010\u102c\u1038 \u1011\u100a\u1037\u103a\u1015\u1031\u1038\u1015\u102b\u104b")
        st.stop()
    E = parse_srt(s)
    if not E:
        st.error("SRT format \u1019\u103e\u102c\u1038\u1014\u1031\u1010\u101a\u103a - \u1014\u1019\u1030\u1014\u102c\u1021\u1010\u102d\u102f\u1004\u103a\u1038 \u1005\u1005\u103a\u1015\u1031\u1038\u1015\u102b\u104b")
        st.stop()
    if re.search(r"[a-zA-Z]", s):
        st.warning("English \u1005\u102c\u101c\u102f\u1036\u1038\u1010\u103d\u1031\u1010\u103d\u1032\u1015\u102b\u101d\u1004\u103a\u1014\u1031\u1010\u101a\u103a")
    vp = OD / "input.mp4"
    vp.write_bytes(v.getvalue())
    tts = get_tts()
    wd = OD / "segs"; wd.mkdir(exist_ok=True)
    ins, flt = [], []
    bar = st.progress(0, "\u1021\u101e\u1036\u1011\u103d\u1000\u103a\u1011\u102f\u1010\u103a\u1014\u1031\u1010\u101a\u103a...")
    for i, (a, b, t) in enumerate(E):
