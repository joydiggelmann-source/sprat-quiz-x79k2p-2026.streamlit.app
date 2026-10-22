import streamlit as st
import pandas as pd
import os
import random

st.set_page_config(page_title="SPRAT Prüfungs-Quiz", layout="centered")

st.title("SPRAT Prüfungs-Quiz")

EXCEL_FILE = "RAWT ENG-GER Final.xlsx"

@st.cache_data
def load_data():
    if os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE, header=4)
        df.columns = df.columns.astype(str).str.strip()
        return df
    return None

df = load_data()

if df is not None:
    # Level-Auswahl in der Seitenleiste
    level_selected = st.sidebar.selectbox("Wähle deine Stufe / Level:", [1, 2, 3])

    # 1. ZUERST leere/ungültige Fragetexte und Summenzeilen filtern
    q_col = 'Seilzugang' if 'Seilzugang' in df.columns else df.columns[3]
    df = df[
        df[q_col].notna() & 
        (df[q_col].astype(str).str.strip() != "") & 
        (df[q_col].astype(str).str.strip() != "Seilzugang")
    ].copy()

    # 2. ISOLIERTE LEVEL-FILTERUNG
    ebene_str = df['Ebene'].astype(str).str.upper() if 'Ebene' in df.columns else pd.Series([""] * len(df), index=df.index)

    if level_selected == 1:
        # Nur Stufe 1 (25L1 oder 25ALLE)
        cond = ebene_str.str.contains("L1|ALLE", na=False) & ~ebene_str.str.contains("L2|L3", na=False)
        filtered_df = df[cond]

    elif level_selected == 2:
        # Nur reine Stufe 2 Fragen (25L2)
        cond = ebene_str.str.contains("L2", na=False)
        filtered_df = df[cond]

    else:
        # Nur reine Stufe 3 Fragen (25L3)
        cond = ebene_str.str.contains("L3", na=False)
        filtered_df = df[cond]

    # Session State initialisieren
    if "correct_counts" not in st.session_state:
        st.session_state.correct_counts = {}
    
    if "question_queue" not in st.session_state or "current_level" not in st.session_state or st.session_state.current_level != level_selected:
        st.session_state.current_level = level_selected
        st.session_state.correct_counts = {}
        queue = [str(idx) for idx in filtered_df.index]
        random.shuffle(queue)
        st.session_state.question_queue = queue

    # Fortschritt zurücksetzen Button
    if st.sidebar.button("🗑️ Fortschritt für diese Sitzung zurücksetzen"):
        st.session_state.correct_counts = {}
        queue = [str(idx) for idx in filtered_df.index]
        random.shuffle(queue)
        st.session_state.question_queue = queue
        st.rerun()

    # Offene Fragen filtern (weniger als 2x richtig)
    active_ids = [
        q_id for q_id in st.session_state.question_queue 
        if st.session_state.correct_counts.get(q_id, 0) < 2
    ]

    st.write(f"### Stufe {level_selected}")
    st.write(f"Verbleibende offene Fragen im Übungspool: **{len(active_ids)}**")

    if active_ids:
        current_id_str = active_ids[0]
        current_idx = int(current_id_str)
        current_q = filtered_df.loc[current_idx]

        st.markdown("---")
        if 'Ref. Nr.' in current_q and pd.notna(current_q['Ref. Nr.']):
            st.write(f"**Kapitel / Ref. Nr.:** {current_q['Ref. Nr.']}")
        
        # Fragetext
        question_text = str(current_q[q_col]).strip()
        st.write(f"### {question_text}")

        # Frageart
        q_type = str(current_q.get('Frageart', '')).strip().upper()

        options = []
        if q_type == "TF":
            options = ["A: Wahr / Richtig", "B: Falsch"]
        else:
            for col in ['A', 'B', 'C', 'D', 'E']:
                if col in current_q and pd.notna(current_q[col]):
                    val = str(current_q[col]).strip()
                    if val != "" and val.lower() != "nan":
                        options.append(f"{col}: {val}")
            
            if not options:
                options = ["A: Wahr / Richtig", "B: Falsch"]

        user_choice = st.radio("Deine Antwort wählen:", options, key=f"radio_{current_id_str}")

        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("Antwort überprüfen", key=f"btn_check_{current_id_str}"):
                correct_letter = str(current_q.get('Antwort', '')).strip().upper()
                
                if user_choice.startswith(correct_letter):
                    st.success("✅ RICHTIG!")
                    st.session_state.correct_counts[current_id_str] = st.session_state.correct_counts.get(current_id_str, 0) + 1
                    
                    count = st.session_state.correct_counts[current_id_str]
                    if count >= 2:
                        st.info("🎉 Super! 2x richtig gewusst – diese Frage ist fertig gelernt.")
                else:
                    st.error(f"❌ FALSCH. Die richtige Antwort ist **{correct_letter}**.")

        with col2:
            if st.button("Nächste Frage ➡️", key=f"btn_next_{current_id_str}"):
                st.session_state.question_queue.remove(current_id_str)
                st.session_state.question_queue.append(current_id_str)
                st.rerun()

    else:
        st.balloons()
        st.success("🏆 Hervorragend! Du hast alle Fragen für diese Stufe mindestens 2-mal richtig beantwortet.")

else:
    st.error(f"Die Datei '{EXCEL_FILE}' wurde im Ordner nicht gefunden.")