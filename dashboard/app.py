"""Run with: python -m streamlit run dashboard/app.py"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from src.dashboard_data import read_upload, recording_profile
from src.data_manager import DataValidationError, FIELDS
from src.motor_profile import ContractError
from src.sensor_interface import CsvSensorSource


st.set_page_config(page_title="Dr. Motor", page_icon="⚙️", layout="wide")
st.markdown(
    "<style>" + (Path(__file__).with_name("ambient.css")).read_text(encoding="utf-8") + "</style>",
    unsafe_allow_html=True,
)
st.title("Dr. Motor")
st.caption("Motor ölçümlerini yükle, kontrol et ve incele.")

with st.sidebar:
    st.header("Çalışma alanı")
    page = st.radio("Sayfa", ("Genel bakış", "Sensör ölçümleri", "Motor profili", "Kayıt geçmişi"))
    st.divider()
    mode = st.radio("Veri kaynağı", ("CSV yükle", "Yerel kayıtlar"))
    upload = None
    local_file = None
    if mode == "CSV yükle":
        upload = st.file_uploader("Ölçüm dosyası", type=["csv"])
    else:
        files = sorted((ROOT / "data" / "raw").glob("*.csv"))
        safe_files = [p for p in files if p.resolve().parent == (ROOT / "data" / "raw").resolve()]
        local_file = st.selectbox("data/raw içindeki kayıt", safe_files,
                                  format_func=lambda p: p.name) if safe_files else None
        if not safe_files:
            st.info("Henüz yerel kayıt yok. CSV yükleyebilirsin.")
    st.download_button("Boş CSV şablonunu indir", ",".join(FIELDS) + "\n",
                       file_name="dr-motor-template.csv", mime="text/csv")
    st.caption("Şablon yalnızca başlık içerir; incelemek için gerçek ölçüm satırları ekle.")

records = []
try:
    if upload is not None:
        if upload.size > 20 * 1024 * 1024:
            st.error("Bu sürümde dosya sınırı 20 MB.")
            st.stop()
        records = read_upload(upload.getvalue())
    elif local_file is not None:
        if local_file.stat().st_size > 20 * 1024 * 1024:
            st.error("Bu sürümde dosya sınırı 20 MB.")
            st.stop()
        records = list(CsvSensorSource(local_file))
except (DataValidationError, UnicodeError, OSError) as error:
    st.error(f"Kayıt açılamadı: {error}")
    st.stop()

st.info("Model henüz yok. Sağlık skoru ve arıza teşhisi üretilmiyor.")
if not records:
    st.subheader("İlk ölçümünü yükle")
    st.write("Sol panelden CSV dosyanı seç. Doğrulanan ölçümler burada görüntülenecek.")
    st.caption("UNO Q canlı bağlantısı henüz eklenmedi. Bu ekranda örnek ölçüm gösterilmez.")
    st.stop()

with st.sidebar:
    motors = sorted({r.motor_id for r in records})
    motor = st.selectbox("Motor seç", motors)
    sessions = sorted({r.session_id for r in records if r.motor_id == motor})
    session = st.selectbox("Oturum / kayıt profili", sessions)
    motor_type = st.selectbox("Motor tipi", ("Belirtilmedi", "DC", "BLDC", "PMSM", "Asenkron", "Diğer"))

selected = [r for r in records if r.motor_id == motor and r.session_id == session]
try:
    profile = recording_profile(selected, motor_type)
except ContractError as error:
    st.error(f"Profil doğrulanamadı: {error}")
    st.stop()

rows = [{"Zaman": r.timestamp, "Kanal": r.channel, "Değer": r.value,
         "Birim": r.unit, "Örnek": r.sample_index} for r in selected]
frame = pd.DataFrame(rows)
frame["Zaman"] = pd.to_datetime(frame["Zaman"], utc=True)

if page == "Genel bakış":
    st.subheader("Kayıt özeti")
    a, b, c = st.columns(3)
    a.metric("Ölçüm sayısı", len(selected))
    b.metric("Sensör kanalı", len(profile.channels))
    c.metric("Kayıt süresi", f"{(max(r.timestamp for r in selected) - min(r.timestamp for r in selected)).total_seconds():.3f} sn")
    st.write(f"**Motor:** {motor} · **Oturum:** {session}")
    st.write(f"**Deney etiketi:** {selected[0].label}")
    st.caption("Zamanlar UTC olarak gösterilir. Özet yalnızca seçili oturumu kapsar.")
    st.dataframe(frame.head(20), hide_index=True, width="stretch")

elif page == "Sensör ölçümleri":
    st.subheader("Ölçüm grafiği")
    channel = st.selectbox("Sensör kanalı", [c.channel for c in profile.channels])
    channel_records = [r for r in selected if r.channel == channel]
    channel_frame = frame[frame["Kanal"] == channel].sort_values("Zaman")
    gap_count = sum(b.sample_index != a.sample_index + 1
                    for a, b in zip(channel_records, channel_records[1:]))
    if gap_count:
        st.warning(f"{gap_count} örnek aralığında kesinti var. Eksik ölçümler tamamlanmadı.")
    st.caption(f"Birim: {channel_records[0].unit} · Zaman: UTC. Noktalar kayıtlı ölçümlerdir.")
    if len(channel_frame) > 10000:
        st.info("Grafikte ilk 10.000 ölçüm gösteriliyor; tabloda tüm kanal kayıtları mevcut.")
    st.scatter_chart(channel_frame.head(10000), x="Zaman", y="Değer")
    st.dataframe(channel_frame, hide_index=True, width="stretch")

elif page == "Motor profili":
    st.subheader("Seçili kayıt profili")
    st.write(f"**Motor:** {profile.motor_id} · **Tip:** {profile.motor_type}")
    st.caption("Kanal ayarları CSV'den okunmuştur; donanım uygunluğunu doğrulamaz. Motor tipi bu oturumdaki seçiminizdir.")
    st.dataframe([{"Kanal": c.channel, "Birim": c.unit, "Örnekleme (Hz)": c.sample_rate_hz}
                  for c in profile.channels], hide_index=True, width="stretch")
    st.write("**Model:** Henüz atanmadı")

else:
    st.subheader("Dosyadaki kayıt oturumları")
    history = {}
    for record in records:
        key = (record.motor_id, record.session_id)
        entry = history.setdefault(key, {"Motor": record.motor_id, "Oturum": record.session_id,
                                        "Etiket": record.label, "Ölçümler": 0,
                                        "Başlangıç (UTC)": record.timestamp, "Bitiş (UTC)": record.timestamp})
        entry["Ölçümler"] += 1
        entry["Başlangıç (UTC)"] = min(entry["Başlangıç (UTC)"], record.timestamp)
        entry["Bitiş (UTC)"] = max(entry["Bitiş (UTC)"], record.timestamp)
    history_frame = pd.DataFrame(history.values())
    for col in ("Başlangıç (UTC)", "Bitiş (UTC)"):
        history_frame[col] = pd.to_datetime(history_frame[col], utc=True)
    st.dataframe(history_frame, hide_index=True, width="stretch")
    st.caption("Bu liste yalnızca açık dosyanın oturumlarıdır. Kalıcı Motor Passport geçmişi henüz eklenmedi.")
