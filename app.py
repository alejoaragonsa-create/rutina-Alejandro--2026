import streamlit as st
import pandas as pd
from datetime import date, datetime
import json
import os

st.set_page_config(page_title="Rutina 2026", layout="wide")

st.title("🏋️ Rutina 2026 — versión web para rellenar rápido")

# ---- storage helpers (simple local files) ----
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def _safe_name(s: str) -> str:
    return "".join(ch for ch in s.strip() if ch.isalnum() or ch in ("-","_")).strip("-_") or "mi_rutina"

def load_state(profile: str):
    fp = os.path.join(DATA_DIR, f"{_safe_name(profile)}.json")
    if os.path.exists(fp):
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(profile: str, state: dict):
    fp = os.path.join(DATA_DIR, f"{_safe_name(profile)}.json")
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# ---- default structure ----
DEFAULT_SESSIONS = {
    "Sesión 1": [
        {"Ejercicio":"Elevación de piernas colgado","Series_obj":"3x12-15"},
        {"Ejercicio":"Gemelos multipower","Series_obj":"4x15-20"},
        {"Ejercicio":"Aductores","Series_obj":"3x12-15"},
        {"Ejercicio":"Curl femoral sentado","Series_obj":"3x12-15"},
        {"Ejercicio":"Sentadilla Jaka","Series_obj":"2x8-10"},
        {"Ejercicio":"Hip thrust (máquina)","Series_obj":"3x10-12"},
        {"Ejercicio":"Sentadilla búlgara","Series_obj":"3x10-12"},
        {"Ejercicio":"Patada de glúteo","Series_obj":"3x12-15"},
    ],
    "Sesión 2": [],
    "Sesión 3": [],
    "Sesión 4": [],
    "Sesión 5": [],
}

def ensure_defaults(state: dict) -> dict:
    state.setdefault("perfil", "MiRutina")
    state.setdefault("datos", {
        "Nombre": "",
        "Fase": "",
        "Objetivo": "",
        "Fecha inicio": str(date.today()),
        "Fecha fin": "",
    })
    state.setdefault("sesiones", DEFAULT_SESSIONS)
    state.setdefault("logs_entrenos", [])  # each: {fecha, sesion, semana, ejercicio, serie, peso, reps, notas}
    state.setdefault("peso_corporal", [])  # each: {fecha, kg}
    return state

# ---- profile selector ----
with st.sidebar:
    st.header("⚙️ Perfil")
    profile = st.text_input("Nombre del perfil", value=st.session_state.get("profile", "MiRutina"))
    st.session_state["profile"] = profile
    state = ensure_defaults(load_state(profile))

    st.caption("Se guarda localmente en la carpeta `data/`.")
    if st.button("💾 Guardar ahora"):
        save_state(profile, state)
        st.success("Guardado.")

# ---- Tabs ----
tab1, tab2, tab3 = st.tabs(["🧾 Datos generales", "📋 Rutina (sesiones)", "📝 Registro (entrenos y peso)"])

with tab1:
    st.subheader("Datos generales")
    c1, c2 = st.columns(2)
    with c1:
        state["datos"]["Nombre"] = st.text_input("Nombre", value=state["datos"].get("Nombre",""))
        state["datos"]["Fase"] = st.text_input("Fase", value=state["datos"].get("Fase",""))
        state["datos"]["Objetivo"] = st.text_area("Objetivo", value=state["datos"].get("Objetivo",""), height=90)
    with c2:
        fi = state["datos"].get("Fecha inicio", str(date.today()))
        try:
            fi_dt = datetime.fromisoformat(fi).date()
        except Exception:
            fi_dt = date.today()
        state["datos"]["Fecha inicio"] = str(st.date_input("Fecha inicio", value=fi_dt))

        ff = state["datos"].get("Fecha fin","")
        if ff:
            try:
                ff_dt = datetime.fromisoformat(ff).date()
            except Exception:
                ff_dt = date.today()
        else:
            ff_dt = date.today()
        state["datos"]["Fecha fin"] = str(st.date_input("Fecha fin", value=ff_dt))

    st.divider()
    st.info("Tip: si quieres, puedes tener varios perfiles (p. ej. 'Volumen', 'Definición', etc.).")

with tab2:
    st.subheader("Rutina por sesiones (editable)")
    sesion = st.selectbox("Elige sesión", list(state["sesiones"].keys()))
    ejercicios = state["sesiones"].get(sesion, [])
    df = pd.DataFrame(ejercicios) if ejercicios else pd.DataFrame(columns=["Ejercicio","Series_obj"])
    st.caption("Edita la tabla: añade/quita ejercicios y ajusta las series objetivo.")
    edited = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        key=f"editor_{sesion}",
        column_config={
            "Ejercicio": st.column_config.TextColumn(required=True),
            "Series_obj": st.column_config.TextColumn(help="Ej: 3x8-10, 4x12-15"),
        },
    )
    # persist back
    state["sesiones"][sesion] = edited.fillna("").to_dict(orient="records")

    st.divider()
    st.subheader("Exportar rutina a CSV (por si la quieres imprimir o guardar)")
    export_df = []
    for s, exs in state["sesiones"].items():
        for e in exs:
            export_df.append({"Sesion": s, **e})
    export_df = pd.DataFrame(export_df) if export_df else pd.DataFrame(columns=["Sesion","Ejercicio","Series_obj"])
    st.download_button(
        "⬇️ Descargar rutina.csv",
        data=export_df.to_csv(index=False).encode("utf-8"),
        file_name="rutina.csv",
        mime="text/csv",
    )

with tab3:
    st.subheader("Registro de entrenos (pesos/reps)")

    c1, c2, c3, c4 = st.columns([1.2,1,1,1])
    with c1:
        fecha = st.date_input("Fecha del entreno", value=date.today())
    with c2:
        sesion_log = st.selectbox("Sesión", list(state["sesiones"].keys()), key="sesion_log")
    with c3:
        semana = st.number_input("Semana", min_value=1, max_value=52, value=1, step=1)
    with c4:
        notas_general = st.text_input("Notas (opcional)", value="")

    exs = state["sesiones"].get(sesion_log, [])
    if not exs:
        st.warning("Esa sesión no tiene ejercicios todavía. Ve a la pestaña 'Rutina' y añádelos.")
    else:
        st.caption("Rellena rápido: una fila = una serie.")
        rows = []
        for e in exs:
            rows.append({"Ejercicio": e.get("Ejercicio",""), "Serie": 1, "Peso (kg)": "", "Reps": "", "RPE": ""})
        base_df = pd.DataFrame(rows)
        log_df = st.data_editor(
            base_df,
            num_rows="dynamic",
            use_container_width=True,
            key="log_editor",
            column_config={
                "Ejercicio": st.column_config.TextColumn(disabled=False),
                "Serie": st.column_config.NumberColumn(min_value=1, step=1),
                "Peso (kg)": st.column_config.TextColumn(help="Puedes poner 80 o 80.5"),
                "Reps": st.column_config.TextColumn(help="Ej: 10, 12-10-8"),
                "RPE": st.column_config.TextColumn(help="Opcional"),
            },
        )

        if st.button("➕ Guardar entreno"):
            new_rows = log_df.fillna("").to_dict(orient="records")
            for r in new_rows:
                if str(r.get("Ejercicio","")).strip()=="":
                    continue
                state["logs_entrenos"].append({
                    "fecha": str(fecha),
                    "sesion": sesion_log,
                    "semana": int(semana),
                    "ejercicio": r.get("Ejercicio",""),
                    "serie": r.get("Serie",""),
                    "peso_kg": r.get("Peso (kg)",""),
                    "reps": r.get("Reps",""),
                    "rpe": r.get("RPE",""),
                    "notas": notas_general,
                })
            save_state(profile, state)
            st.success("Entreno guardado ✅")

    st.divider()
    st.subheader("Peso corporal (rápido)")
    c1, c2 = st.columns(2)
    with c1:
        fecha_p = st.date_input("Fecha", value=date.today(), key="fecha_p")
    with c2:
        kg = st.number_input("Kg", min_value=0.0, max_value=300.0, value=0.0, step=0.1, format="%.1f")

    if st.button("➕ Guardar peso"):
        state["peso_corporal"].append({"fecha": str(fecha_p), "kg": float(kg)})
        save_state(profile, state)
        st.success("Peso guardado ✅")

    st.divider()
    st.subheader("Historial")
    colA, colB = st.columns(2)

    with colA:
        st.markdown("**Entrenos**")
        if state["logs_entrenos"]:
            hist = pd.DataFrame(state["logs_entrenos"])
            st.dataframe(hist.sort_values(["fecha","sesion","ejercicio","serie"], ascending=[False,True,True,True]), use_container_width=True, height=320)
            st.download_button(
                "⬇️ Descargar entrenos.csv",
                data=hist.to_csv(index=False).encode("utf-8"),
                file_name="entrenos.csv",
                mime="text/csv",
            )
        else:
            st.write("Aún no hay registros.")
    with colB:
        st.markdown("**Peso corporal**")
        if state["peso_corporal"]:
            p = pd.DataFrame(state["peso_corporal"]).sort_values("fecha", ascending=False)
            st.dataframe(p, use_container_width=True, height=320)
            st.download_button(
                "⬇️ Descargar peso.csv",
                data=p.to_csv(index=False).encode("utf-8"),
                file_name="peso.csv",
                mime="text/csv",
            )
        else:
            st.write("Aún no hay registros.")

st.sidebar.divider()
st.sidebar.markdown("### 🚀 Publicarlo como web")
st.sidebar.markdown(
"""
- **Opción 1 (rápida)**: ejecutar en tu PC con Streamlit.
- **Opción 2 (online gratis)**: subir estos archivos a GitHub y desplegar en *Streamlit Community Cloud*.

Si quieres, dime si lo vas a usar **en iPhone** o en **PC**, y lo dejo aún más cómodo (botones grandes, menos columnas, etc.).
"""
)
