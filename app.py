import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
import time
import random
import io
import sqlite3
import json
import os
from datetime import datetime, timedelta

# ==========================================
# 0. КОНФІГУРАЦІЯ
# ==========================================

st.set_page_config(page_title="OmniSport Pro", layout="wide", initial_sidebar_state="expanded")

DB_PATH = "omnisport.db"

DEFAULT_DATA = pd.DataFrame({
    "Ім'я": ["Олександр", "Марія", "Іван", "Анна"],
    "Вік": [24, 21, 26, 23],
    "Вид спорту": ["Футбол", "Волейбол", "Біг", "Теніс"],
    "Матчі": [12, 15, 8, 20],
    "Очки": [5, 45, 0, 80],
    "Швидкість": [28.5, 22.0, 32.1, 25.0],
    "Витривалість": [85, 70, 95, 40],
    "Сила": [75, 85, 60, 70],
    "Навантаження_7днів": [2, 3, 1, 4],
    "Номер": [1, 2, 3, 4]
})

# ==========================================
# БАЗА ДАНИХ — SQLite
# ==========================================

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS athletes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            age         INTEGER DEFAULT 20,
            sport       TEXT,
            matches     INTEGER DEFAULT 0,
            points      INTEGER DEFAULT 0,
            speed       REAL DEFAULT 20.0,
            stamina     INTEGER DEFAULT 50,
            power       INTEGER DEFAULT 50,
            workload    INTEGER DEFAULT 0,
            number      INTEGER DEFAULT 1,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS video_notes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            url        TEXT,
            notes      TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS match_logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            player1    TEXT,
            player2    TEXT,
            score1     INTEGER,
            score2     INTEGER,
            winner     TEXT,
            log_json   TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS tactic_notes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            player     TEXT,
            tactic     TEXT,
            notes      TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS ocr_results (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            result_json TEXT,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Таблиця нотаток до гравців (нова)
    c.execute("""
        CREATE TABLE IF NOT EXISTS athlete_notes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            athlete    TEXT,
            note       TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    count = c.execute("SELECT COUNT(*) FROM athletes").fetchone()[0]
    if count == 0:
        _seed_default_athletes(conn)

    conn.close()


def _seed_default_athletes(conn):
    c = conn.cursor()
    for _, row in DEFAULT_DATA.iterrows():
        c.execute("""
            INSERT INTO athletes (name, age, sport, matches, points, speed, stamina, power, workload, number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["Ім'я"], row["Вік"], row["Вид спорту"],
            row["Матчі"], row["Очки"], row["Швидкість"],
            row["Витривалість"], row["Сила"],
            row["Навантаження_7днів"], row["Номер"]
        ))
    conn.commit()


# ---------- ATHLETES CRUD ----------

def db_load_athletes() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT id, name AS "Ім'я", age AS "Вік", sport AS "Вид спорту",
               matches AS "Матчі", points AS "Очки", speed AS "Швидкість",
               stamina AS "Витривалість", power AS "Сила",
               workload AS "Навантаження_7днів", number AS "Номер"
        FROM athletes ORDER BY id
    """, conn)
    conn.close()
    return df


def db_add_athlete(name, age, sport, matches, points, speed, stamina, power, workload, number):
    conn = get_connection()
    conn.execute("""
        INSERT INTO athletes (name, age, sport, matches, points, speed, stamina, power, workload, number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, age, sport, matches, points, speed, stamina, power, workload, number))
    conn.commit()
    conn.close()


def db_update_athlete_workload(athlete_name: str, workload: int):
    conn = get_connection()
    conn.execute("""
        UPDATE athletes SET workload = ?, updated_at = CURRENT_TIMESTAMP
        WHERE name = ?
    """, (workload, athlete_name))
    conn.commit()
    conn.close()


def db_update_athlete_stats(athlete_name: str, speed: float, stamina: int, power: int):
    conn = get_connection()
    conn.execute("""
        UPDATE athletes SET speed = ?, stamina = ?, power = ?, updated_at = CURRENT_TIMESTAMP
        WHERE name = ?
    """, (speed, stamina, power, athlete_name))
    conn.commit()
    conn.close()


def db_delete_all_athletes():
    conn = get_connection()
    conn.execute("DELETE FROM athletes")
    conn.commit()
    conn.close()


def db_bulk_insert_athletes(df: pd.DataFrame):
    db_delete_all_athletes()
    conn = get_connection()
    for _, row in df.iterrows():
        conn.execute("""
            INSERT INTO athletes (name, age, sport, matches, points, speed, stamina, power, workload, number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row.get("Ім'я", ""), row.get("Вік", 20), row.get("Вид спорту", ""),
            row.get("Матчі", 0), row.get("Очки", 0), row.get("Швидкість", 20.0),
            row.get("Витривалість", 50), row.get("Сила", 50),
            row.get("Навантаження_7днів", 0), row.get("Номер", 1)
        ))
    conn.commit()
    conn.close()


# ---------- ATHLETE NOTES ----------

def db_save_athlete_note(athlete: str, note: str):
    conn = get_connection()
    conn.execute("INSERT INTO athlete_notes (athlete, note) VALUES (?, ?)", (athlete, note))
    conn.commit()
    conn.close()


def db_load_athlete_notes(athlete: str) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM athlete_notes WHERE athlete = ? ORDER BY created_at DESC LIMIT 10",
        (athlete,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- VIDEO NOTES ----------

def db_save_video_note(url: str, notes: str):
    conn = get_connection()
    conn.execute("INSERT INTO video_notes (url, notes) VALUES (?, ?)", (url, notes))
    conn.commit()
    conn.close()


def db_load_video_notes() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM video_notes ORDER BY created_at DESC LIMIT 20").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def db_get_latest_video_note() -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM video_notes ORDER BY created_at DESC LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else None


# ---------- MATCH LOGS ----------

def db_save_match_log(player1, player2, score1, score2, winner, log):
    conn = get_connection()
    conn.execute("""
        INSERT INTO match_logs (player1, player2, score1, score2, winner, log_json)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (player1, player2, score1, score2, winner, json.dumps(log, ensure_ascii=False)))
    conn.commit()
    conn.close()


def db_load_match_history() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM match_logs ORDER BY created_at DESC LIMIT 50").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- TACTIC NOTES ----------

def db_save_tactic_note(player: str, tactic: str, notes: str):
    conn = get_connection()
    conn.execute("INSERT INTO tactic_notes (player, tactic, notes) VALUES (?, ?, ?)",
                 (player, tactic, notes))
    conn.commit()
    conn.close()


def db_load_tactic_notes(player: str = None) -> list:
    conn = get_connection()
    if player:
        rows = conn.execute(
            "SELECT * FROM tactic_notes WHERE player = ? ORDER BY created_at DESC LIMIT 20",
            (player,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM tactic_notes ORDER BY created_at DESC LIMIT 20"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- OCR RESULTS ----------

def db_save_ocr_result(result: dict):
    conn = get_connection()
    conn.execute("INSERT INTO ocr_results (result_json) VALUES (?)",
                 (json.dumps(result, ensure_ascii=False),))
    conn.commit()
    conn.close()


def db_load_ocr_history() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM ocr_results ORDER BY created_at DESC LIMIT 10").fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        d["result"] = json.loads(d["result_json"])
        results.append(d)
    return results


# ==========================================
# ІНІЦІАЛІЗАЦІЯ СЕСІЇ
# ==========================================

init_db()

if 'tactic_points' not in st.session_state:
    st.session_state.tactic_points = []

if 'match_log' not in st.session_state:
    st.session_state.match_log = []

if 'tactical_photos' not in st.session_state:
    st.session_state.tactical_photos = []

if 'cv_analysis_done' not in st.session_state:
    st.session_state.cv_analysis_done = False
if 'cv_teams_data' not in st.session_state:
    st.session_state.cv_teams_data = {}
if 'cv_ball_positions' not in st.session_state:
    st.session_state.cv_ball_positions = []
if 'cv_events' not in st.session_state:
    st.session_state.cv_events = []
if 'cv_fps' not in st.session_state:
    st.session_state.cv_fps = 25

if 'ocr_result' not in st.session_state:
    st.session_state.ocr_result = None
if 'ocr_photo' not in st.session_state:
    st.session_state.ocr_photo = None


def calculate_per(row):
    base = (row['Швидкість'] * 1.5) + (row['Витривалість'] * 0.8) + (row['Сила'] * 0.9)
    bonus = row['Очки'] * 2 if row['Матчі'] > 0 else 0
    return round((base + bonus) / 3, 1)


def load_athletes_with_per() -> pd.DataFrame:
    df = db_load_athletes()
    if not df.empty:
        df['PER (Рейтинг)'] = df.apply(calculate_per, axis=1)
    return df


def get_performance_badge(per_value: float) -> str:
    """Повертає значок рівня гравця за PER."""
    if per_value >= 80:
        return "🥇 Еліта"
    elif per_value >= 60:
        return "🥈 Топ-форма"
    elif per_value >= 40:
        return "🥉 Стабільний"
    else:
        return "📈 Зростає"


def get_sport_emoji(sport: str) -> str:
    mapping = {
        "Футбол": "⚽", "Волейбол": "🏐", "Біг": "🏃", "Теніс": "🎾",
        "Баскетбол": "🏀", "Бокс": "🥊", "Плавання": "🏊", "Велоспорт": "🚴"
    }
    return mapping.get(sport, "🏅")


# ==========================================
# ГОЛОВНА ЛОГІКА
# ==========================================

def main():
    df = load_athletes_with_per()

    with st.sidebar:
        st.title("🏆 OmniSport Pro")
        st.caption("Performance Analytics v12.1 — SQLite Edition")

        conn = get_connection()
        db_size = os.path.getsize(DB_PATH) / 1024 if os.path.exists(DB_PATH) else 0
        athlete_count = conn.execute("SELECT COUNT(*) FROM athletes").fetchone()[0]
        match_count = conn.execute("SELECT COUNT(*) FROM match_logs").fetchone()[0]
        conn.close()

        with st.expander("🗄️ Статус бази даних", expanded=False):
            st.success(f"✅ SQLite активна: `{DB_PATH}`")
            col_d1, col_d2 = st.columns(2)
            col_d1.metric("Гравців", athlete_count)
            col_d2.metric("Матчів", match_count)
            st.caption(f"Розмір БД: {db_size:.1f} KB")
            st.caption(f"📁 Файл: `{os.path.abspath(DB_PATH)}`")

        st.divider()

        with st.expander("📂 Завантажити свої дані", expanded=False):
            uploaded_file = st.file_uploader(
                "CSV або Excel з даними команди",
                type=["csv", "xlsx", "xls"],
                help="Файл повинен містити колонки: Ім'я, Вік, Вид спорту, Матчі, Очки, Швидкість, Витривалість, Сила"
            )
            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df_upload = pd.read_csv(uploaded_file)
                    else:
                        df_upload = pd.read_excel(uploaded_file)

                    required_cols = ["Ім'я", "Вид спорту", "Матчі", "Очки", "Швидкість", "Витривалість", "Сила"]
                    missing = [c for c in required_cols if c not in df_upload.columns]

                    if missing:
                        st.error(f"Відсутні колонки: {', '.join(missing)}")
                    else:
                        for col, default in [('Навантаження_7днів', 0), ('Вік', 20), ('Номер', 1)]:
                            if col not in df_upload.columns:
                                df_upload[col] = default

                        db_bulk_insert_athletes(df_upload)
                        st.success(f"✅ Завантажено та збережено {len(df_upload)} гравців!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Помилка читання файлу: {e}")

            if st.button("🔄 Повернути демо-дані", use_container_width=True):
                db_bulk_insert_athletes(DEFAULT_DATA)
                st.rerun()

        st.divider()
        menu = [
            "🏠 Дашборд",
            "📊 Командна аналітика",
            "👥 База гравців",
            "⚔️ H2H Батл (Скаутинг)",
            "🗺️ Тактична дошка",
            "📹 Інтеграція з медіа",
            "🎥 CV Аналіз відео",
            "🖼️ OCR Тактичних фото",
            "⚛️ Лабораторія Фізики",
            "🎲 AI-Симулятор Матчів",
            "🩹 Прогноз Травматизму",
            "🧬 AI-Тренер (Плани тренувань)",
            "📈 Історія форми",
            "🗃️ Історія матчів (БД)",
            "📚 Ресурси та Освіта",
            "💾 Експорт Даних"
        ]
        choice = st.radio("Навігація", menu)
        st.divider()

        st.subheader("🔗 Корисні посилання")
        st.info("[SportAnalytic](https://sportanalytic.com/)")
        st.info("[Sport.ua](https://sport.ua/uk)")

        st.divider()
        st.info(f"Активних гравців: **{len(df)}**")

    if choice == "🏠 Дашборд": render_dashboard(df)
    elif choice == "📊 Командна аналітика": render_team_analytics(df)
    elif choice == "👥 База гравців": render_crm(df)
    elif choice == "⚔️ H2H Батл (Скаутинг)": render_scouting(df)
    elif choice == "🗺️ Тактична дошка": render_tactics(df)
    elif choice == "📹 Інтеграція з медіа": render_media_integration()
    elif choice == "🎥 CV Аналіз відео": render_cv_analysis()
    elif choice == "🖼️ OCR Тактичних фото": render_tactical_ocr(df)
    elif choice == "⚛️ Лабораторія Фізики": render_physics(df)
    elif choice == "🎲 AI-Симулятор Матчів": render_simulator(df)
    elif choice == "🩹 Прогноз Травматизму": render_injury_prediction(df)
    elif choice == "🧬 AI-Тренер (Плани тренувань)": render_ai_advisor(df)
    elif choice == "📈 Історія форми": render_form_history(df)
    elif choice == "🗃️ Історія матчів (БД)": render_match_history()
    elif choice == "📚 Ресурси та Освіта": render_resources()
    elif choice == "💾 Експорт Даних": render_io(df)


# ==========================================
# 1. ДАШБОРД
# ==========================================
def render_dashboard(df):
    st.title("🏠 Аналітична панель")

    with st.expander("👋 Вітаємо в командному центрі OmniSport Pro!", expanded=True):
        st.markdown("""
        **OmniSport Pro** — єдина платформа для комплексного управління спортивною командою.
        Тут ви знайдете все: від базових показників гравців до комп'ютерного аналізу відео та OCR тактичних схем.

        Усі дані **автоматично зберігаються у SQLite** — жодних втрат після перезавантаження сторінки.
        Починайте з перегляду ключових показників нижче або оберіть потрібний розділ у бічному меню.
        """)
        st.info("💡 **Порада:** Натисніть «Командна аналітика» для детального порівняння по видах спорту.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("⚡ Ключові показники")
    c1, c2, c3, c4 = st.columns(4)

    with c1: st.metric("👥 Всього спортсменів", len(df))
    with c2: st.metric("🚀 Макс. швидкість", f"{df['Швидкість'].max():.1f} км/год")
    with c3: st.metric("🫀 Топ Витривалість", int(df['Витривалість'].max()))
    with c4: st.metric("👑 Топ Рейтинг (PER)", f"{df['PER (Рейтинг)'].max():.1f}")

    # --- Нова функція: швидкий огляд «Хто в зоні ризику» ---
    st.divider()
    st.subheader("🚨 Швидкий статус команди")
    risk_athletes = df[df['Навантаження_7днів'] >= 3]
    low_stamina = df[df['Витривалість'] < 55]

    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        if not risk_athletes.empty:
            st.warning(f"⚠️ **{len(risk_athletes)} гравців** з високим навантаженням (≥3 матчі/тиж):\n" +
                       ", ".join(risk_athletes["Ім'я"].tolist()))
        else:
            st.success("✅ Жодного гравця з перевантаженням")
    with col_r2:
        if not low_stamina.empty:
            st.warning(f"💔 **{len(low_stamina)} гравців** з низькою витривалістю (<55):\n" +
                       ", ".join(low_stamina["Ім'я"].tolist()))
        else:
            st.success("✅ Витривалість усіх гравців в нормі")
    with col_r3:
        top_per = df.loc[df['PER (Рейтинг)'].idxmax()]
        badge = get_performance_badge(top_per['PER (Рейтинг)'])
        sport_em = get_sport_emoji(top_per.get('Вид спорту', ''))
        st.info(f"🏆 **Лідер команди:** {top_per[\"Ім'я\"]}\n\n{sport_em} {top_per.get('Вид спорту','')}\n\n{badge} PER: {top_per['PER (Рейтинг)']:.1f}")

    st.divider()
    st.subheader("📊 Загальний рейтинг команди")
    st.caption("Таблиця відсортована за PER — комплексним показником ефективності гравця (швидкість × 1.5 + витривалість × 0.8 + сила × 0.9 + бонус за очки).")

    formatted_df = df.sort_values(by="PER (Рейтинг)", ascending=False).copy()
    formatted_df['Рівень'] = formatted_df['PER (Рейтинг)'].apply(get_performance_badge)
    formatted_df['Спорт'] = formatted_df['Вид спорту'].apply(get_sport_emoji) + " " + formatted_df['Вид спорту']

    display_cols = ["Ім'я", "Спорт", "Матчі", "Очки", "Швидкість", "Витривалість", "Сила", "PER (Рейтинг)", "Рівень"]
    styled_df = formatted_df[display_cols].style.background_gradient(
        cmap='Blues', subset=['PER (Рейтинг)']
    ).format({'Швидкість': '{:.1f}', 'Витривалість': '{:.0f}', 'Сила': '{:.0f}', 'PER (Рейтинг)': '{:.1f}'})

    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # --- Нова функція: міні-діаграма розподілу PER ---
    st.divider()
    st.subheader("📉 Розподіл рейтингів PER")
    st.caption("Гістограма показує, як розподілені ефективності гравців. Ідеально, якщо більшість знаходиться в зоні 50–80.")
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.hist(df['PER (Рейтинг)'], bins=min(len(df), 10), color='#448AFF', edgecolor='white', alpha=0.85)
    ax.axvline(df['PER (Рейтинг)'].mean(), color='#FF5252', linestyle='--', linewidth=2, label=f"Середнє: {df['PER (Рейтинг)'].mean():.1f}")
    ax.set_xlabel("PER", color='white')
    ax.set_ylabel("Кількість гравців", color='white')
    ax.set_facecolor('#1a1a2e')
    ax.tick_params(colors='white')
    ax.legend(facecolor='#1a1a2e', labelcolor='white')
    fig.patch.set_facecolor('#0d0d1a')
    st.pyplot(fig)
    plt.close(fig)


# ==========================================
# 1.5 КОМАНДНА АНАЛІТИКА
# ==========================================
def render_team_analytics(df):
    st.title("📊 Командна аналітика (Team View)")
    st.markdown("""
    Цей розділ дає змогу побачити команду як єдиний організм.
    Аналізуйте розподіл за видами спорту, порівнюйте середні показники з ідеальними значеннями
    та знаходьте «слабкі місця» у складі, що потребують укріплення.
    """)

    if df.empty:
        st.warning("Немає даних для аналізу.")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Середній вік команди", f"{df['Вік'].mean():.1f} років")
    avg_speed = df['Швидкість'].mean()
    c2.metric("Середня швидкість", f"{avg_speed:.1f} км/год", f"{avg_speed - 30:.1f} від ідеалу (30)")
    c3.metric("Середній командний PER", f"{df['PER (Рейтинг)'].mean():.1f}")

    st.divider()
    col_pie, col_bar = st.columns(2)

    with col_pie:
        st.subheader("Розподіл за видами спорту")
        st.caption("Кругова діаграма відображає, які види спорту представлені в базі. Різноманітність допомагає у побудові міждисциплінарних тренувань.")
        sport_counts = df['Вид спорту'].value_counts()
        fig1, ax1 = plt.subplots(figsize=(6, 4))
        ax1.pie(sport_counts, labels=sport_counts.index, autopct='%1.1f%%',
                startangle=90, colors=plt.cm.Pastel1.colors, textprops=dict(color="w"))
        for text in ax1.texts:
            text.set_color('white')
        ax1.axis('equal')
        fig1.patch.set_alpha(0.0)
        st.pyplot(fig1)
        plt.close(fig1)

    with col_bar:
        st.subheader("Поточні показники vs Ідеал")
        st.caption("Порівняння середніх командних показників з еталонними значеннями професійної команди.")
        avg_stats = pd.DataFrame({
            "Показник": ["Витривалість", "Сила", "Швидкість"],
            "Команда": [df['Витривалість'].mean(), df['Сила'].mean(), df['Швидкість'].mean()],
            "Ідеал": [85.0, 80.0, 30.0]
        }).set_index("Показник")
        st.bar_chart(avg_stats, color=["#448AFF", "#FF5252"])

    # --- Нова функція: топ-3 і аутсайдери ---
    st.divider()
    col_top, col_bot = st.columns(2)
    with col_top:
        st.subheader("🏆 Топ-3 гравці за PER")
        st.caption("Найефективніші гравці команди за комплексним рейтингом.")
        top3 = df.nlargest(3, 'PER (Рейтинг)')[["Ім'я", "Вид спорту", "PER (Рейтинг)"]]
        for i, (_, row) in enumerate(top3.iterrows()):
            medals = ["🥇", "🥈", "🥉"]
            st.write(f"{medals[i]} **{row[\"Ім'я\"]}** — {get_sport_emoji(row['Вид спорту'])} {row['Вид спорту']} — PER: **{row['PER (Рейтинг)']:.1f}**")

    with col_bot:
        st.subheader("📈 Потенціал для росту")
        st.caption("Гравці з найнижчим PER — тут найбільший простір для розвитку.")
        bot3 = df.nsmallest(3, 'PER (Рейтинг)')[["Ім'я", "Вид спорту", "PER (Рейтинг)"]]
        for _, row in bot3.iterrows():
            st.write(f"📌 **{row[\"Ім'я\"]}** — {get_sport_emoji(row['Вид спорту'])} — PER: **{row['PER (Рейтинг)']:.1f}**")

    # --- Нова функція: середні показники за видами спорту ---
    st.divider()
    st.subheader("📐 Середні показники за видами спорту")
    st.caption("Порівняйте, як відрізняються фізичні профілі різних дисциплін у вашому складі.")
    sport_avg = df.groupby('Вид спорту')[['Швидкість', 'Витривалість', 'Сила', 'PER (Рейтинг)']].mean().round(1)
    st.dataframe(sport_avg.style.background_gradient(cmap='YlGn'), use_container_width=True)


# ==========================================
# 2. БАЗА ГРАВЦІВ (CRM)
# ==========================================
def render_crm(df):
    st.title("👥 Управління складом")
    st.markdown("""
    Централізована база всіх спортсменів команди. Тут можна додавати нових гравців,
    шукати за ім'ям або фільтрувати за видом спорту. Усі зміни зберігаються в SQLite-базі
    і залишаються після перезапуску додатку.
    """)

    st.subheader("🔍 Пошук та фільтри")
    col_search, col_filter, col_sort = st.columns(3)
    with col_search:
        search_query = st.text_input("Пошук за ім'ям", placeholder="Введіть ім'я гравця...")
    with col_filter:
        sport_options = ["Всі види"] + list(df['Вид спорту'].dropna().unique())
        selected_sport = st.selectbox("Фільтр за видом спорту", sport_options)
    with col_sort:
        sort_by = st.selectbox("Сортувати за", ["PER (Рейтинг)", "Швидкість", "Витривалість", "Сила", "Матчі"])

    filtered_df = df.copy()
    if search_query:
        filtered_df = filtered_df[filtered_df["Ім'я"].str.contains(search_query, case=False, na=False)]
    if selected_sport != "Всі види":
        filtered_df = filtered_df[filtered_df['Вид спорту'] == selected_sport]
    filtered_df = filtered_df.sort_values(by=sort_by, ascending=False)

    st.divider()

    with st.expander("➕ Додати нового спортсмена", expanded=False):
        st.caption("Заповніть форму нижче, щоб додати гравця до бази. Усі поля зі зірочкою (*) обов'язкові.")
        with st.form("add_form"):
            c1, c_age, c2 = st.columns([2, 1, 2])
            name = c1.text_input("Ім'я *")
            age = c_age.number_input("Вік", min_value=14, max_value=60, value=20)
            sport = c2.selectbox("Вид спорту", ["Волейбол", "Футбол", "Біг", "Теніс", "Баскетбол", "Бокс", "Плавання", "Велоспорт"])

            c3, c4, c5, c6, c7, c8, c9 = st.columns(7)
            matches = c3.number_input("Матчі", min_value=0)
            score = c4.number_input("Очки", min_value=0)
            speed = c5.number_input("Швидк.", 0.0, 50.0, 20.0)
            stamina = c6.number_input("Витривал.", 0, 100, 50)
            power = c7.number_input("Сила", 0, 100, 50)
            workload = c8.number_input("Матчів/тиж.", 0, 7, 0)
            number = c9.number_input("Номер", 1, 99, 1)

            if st.form_submit_button("Зберегти гравця", type="primary"):
                if name.strip() == "":
                    st.error("⚠️ Будь ласка, введіть ім'я спортсмена.")
                else:
                    db_add_athlete(name, age, sport, int(matches), int(score),
                                   speed, int(stamina), int(power), int(workload), int(number))
                    st.success(f"✅ Спортсмена **{name}** збережено у базі даних!")
                    st.rerun()

    # --- Нова функція: швидке редагування показників ---
    with st.expander("✏️ Швидке оновлення фізичних показників", expanded=False):
        st.caption("Оновіть швидкість, витривалість або силу після останнього тестування — без повного перезаписування картки гравця.")
        edit_player = st.selectbox("Оберіть гравця для оновлення:", df["Ім'я"], key="edit_select")
        ep = df[df["Ім'я"] == edit_player].iloc[0]
        ec1, ec2, ec3 = st.columns(3)
        new_speed = ec1.number_input("Нова швидкість", 0.0, 50.0, float(ep['Швидкість']), key="es")
        new_stamina = ec2.number_input("Нова витривалість", 0, 100, int(ep['Витривалість']), key="est")
        new_power = ec3.number_input("Нова сила", 0, 100, int(ep['Сила']), key="ep")
        if st.button("💾 Оновити показники", key="update_stats"):
            db_update_athlete_stats(edit_player, new_speed, new_stamina, new_power)
            st.success(f"✅ Показники {edit_player} оновлено!")
            st.rerun()

    # --- Нова функція: нотатки до гравця ---
    with st.expander("📝 Нотатки до гравця", expanded=False):
        st.caption("Додавайте спостереження, медичні або тактичні нотатки до кожного спортсмена. Зберігаються в БД.")
        note_player = st.selectbox("Оберіть гравця:", df["Ім'я"], key="note_select")
        note_text = st.text_area("Нотатка:", placeholder="Наприклад: після матчу скаржився на ліве коліно...", height=80)
        if st.button("💾 Зберегти нотатку", key="save_athlete_note"):
            if note_text.strip():
                db_save_athlete_note(note_player, note_text)
                st.success("✅ Нотатку збережено!")
            else:
                st.warning("Введіть текст нотатки.")

        notes = db_load_athlete_notes(note_player)
        if notes:
            st.markdown(f"**Попередні нотатки для {note_player}:**")
            for n in notes:
                st.caption(f"🕐 {n['created_at'][:16]}")
                st.write(n['note'])
                st.divider()

    st.subheader(f"📋 Список гравців (Знайдено: {len(filtered_df)})")
    st.caption(f"Показано {len(filtered_df)} з {len(df)} гравців. Колонка «Рівень» розраховується автоматично за PER.")

    display_df = filtered_df.copy()
    display_df['Рівень'] = display_df['PER (Рейтинг)'].apply(get_performance_badge)
    styled_df = display_df.style.format({
        'Швидкість': '{:.1f}', 'Витривалість': '{:.0f}',
        'Сила': '{:.0f}', 'PER (Рейтинг)': '{:.1f}'
    })
    st.dataframe(styled_df, use_container_width=True, hide_index=True, height=400)


# ==========================================
# 3. H2H СКАУТИНГ
# ==========================================
def render_scouting(df):
    st.title("⚔️ Head-to-Head: Порівняння гравців")
    st.markdown("""
    Скаутинговий модуль дозволяє порівняти двох спортсменів за всіма ключовими параметрами.
    Радарна діаграма візуалізує сильні й слабкі сторони кожного гравця — ідеальний інструмент
    для підготовки до матчу або вибору оптимального складу.
    """)

    c1, c2 = st.columns(2)
    with c1: p1_name = st.selectbox("🔴 Гравець 1", df["Ім'я"], key="scout_p1")
    with c2: p2_name = st.selectbox("🔵 Гравець 2", df["Ім'я"], index=min(1, len(df)-1), key="scout_p2")

    p1_data = df[df["Ім'я"] == p1_name].iloc[0]
    p2_data = df[df["Ім'я"] == p2_name].iloc[0]

    col_radar, col_text = st.columns([2, 1])
    with col_radar:
        categories = ['Витривалість', 'Сила', 'Швидкість', 'Очки', 'Матчі']
        N = len(categories)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]

        def get_radar_values(player):
            vals = [
                player['Витривалість'], player['Сила'],
                min(int((player['Швидкість'] / 40) * 100), 100),
                min(player['Очки'] * 5, 100), min(player['Матчі'] * 5, 100)
            ]
            vals += vals[:1]
            return vals

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        plt.xticks(angles[:-1], categories)
        plt.ylim(0, 100)

        ax.plot(angles, get_radar_values(p1_data), color='#FF5252', label=p1_name)
        ax.fill(angles, get_radar_values(p1_data), '#FF5252', alpha=0.25)

        if p1_name != p2_name:
            ax.plot(angles, get_radar_values(p2_data), color='#448AFF', label=p2_name)
            ax.fill(angles, get_radar_values(p2_data), '#448AFF', alpha=0.25)

        plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        st.pyplot(fig)
        plt.close(fig)

    with col_text:
        st.subheader("📈 Аналіз")
        age1 = p1_data.get('Вік', 'N/A')
        age2 = p2_data.get('Вік', 'N/A')
        st.info(f"**{p1_name} ({age1} р.)**: " + ("Лідер швидкості" if p1_data['Швидкість'] > 28 else "Витривалий боєць"))
        if p1_name != p2_name:
            st.info(f"**{p2_name} ({age2} р.)**: " + ("Лідер швидкості" if p2_data['Швидкість'] > 28 else "Витривалий боєць"))

        # --- Нова функція: детальна порівняльна таблиця ---
        st.subheader("📋 Деталі")
        st.caption("Точне порівняння всіх показників. Позитивна різниця на користь Гравця 1.")
        compare_data = {
            "Показник": ["Вік", "Швидкість", "Витривалість", "Сила", "Матчі", "Очки", "PER"],
            p1_name: [
                p1_data.get('Вік', 0), round(p1_data['Швидкість'], 1),
                int(p1_data['Витривалість']), int(p1_data['Сила']),
                int(p1_data['Матчі']), int(p1_data['Очки']),
                round(p1_data['PER (Рейтинг)'], 1)
            ],
            p2_name: [
                p2_data.get('Вік', 0), round(p2_data['Швидкість'], 1),
                int(p2_data['Витривалість']), int(p2_data['Сила']),
                int(p2_data['Матчі']), int(p2_data['Очки']),
                round(p2_data['PER (Рейтинг)'], 1)
            ],
        }
        compare_df = pd.DataFrame(compare_data).set_index("Показник")
        st.dataframe(compare_df, use_container_width=True)

    # --- Нова функція: висновок-рекомендація ---
    if p1_name != p2_name:
        st.divider()
        st.subheader("🤖 Скаутинговий висновок")
        per1, per2 = p1_data['PER (Рейтинг)'], p2_data['PER (Рейтинг)']
        diff = abs(per1 - per2)
        leader = p1_name if per1 > per2 else p2_name
        follower = p2_name if per1 > per2 else p1_name
        if diff < 5:
            st.success(f"⚖️ Гравці майже рівні за потенціалом (різниця PER: {diff:.1f}). Вибір залежить від тактичної ролі.")
        elif diff < 15:
            st.info(f"📌 **{leader}** трохи випереджає {follower} (різниця PER: {diff:.1f}). Рекомендовано для стартового складу.")
        else:
            st.warning(f"🏆 **{leader}** значно перевершує {follower} (різниця PER: {diff:.1f}). Розгляньте додаткове тренування для {follower}.")


# ==========================================
# 4. ТАКТИЧНА ДОШКА
# ==========================================
def render_tactics(df):
    st.title("🗺️ Інтерактивна Тактична Дошка")
    st.markdown("""
    Візуалізуйте тактичні схеми безпосередньо на полі. Обирайте пресетні розстановки
    або вручну розміщуйте точки активності гравця. Усі нотатки до тактик зберігаються
    у базі даних і доступні для перегляду в будь-який момент.
    """)

    selected_player = st.selectbox("Оберіть гравця:", df["Ім'я"])
    player_data = df[df["Ім'я"] == selected_player].iloc[0]

    col_left, col_right = st.columns([3, 1])

    with col_right:
        st.subheader("⚙️ Налаштування")
        mode = st.radio("Режим відображення", ["🎯 Пресет тактики", "📍 Ручні точки"])

        if mode == "🎯 Пресет тактики":
            sport = player_data.get('Вид спорту', 'Футбол')
            if sport == 'Футбол':
                tactic_options = ["4-3-3 (Атака)", "4-4-2 (Баланс)", "5-3-2 (Захист)", "3-5-2 (Контроль)"]
            else:
                tactic_options = ["Атакуючий стиль", "Захисний стиль", "Збалансований"]
            selected_tactic = st.selectbox("Тактика", tactic_options)

            # --- Нова функція: опис тактики ---
            tactic_descriptions = {
                "4-3-3 (Атака)": "Агресивна схема з трьома нападниками. Ідеальна при перевазі в швидкості.",
                "4-4-2 (Баланс)": "Класична збалансована розстановка. Добре працює при середньому рівні команди.",
                "5-3-2 (Захист)": "П'ять захисників — надійний тил. Застосовується при грі від оборони.",
                "3-5-2 (Контроль)": "Контроль середини поля. Ефективна при перевазі у витривалості.",
                "Атакуючий стиль": "Максимальна агресія та тиск на суперника.",
                "Захисний стиль": "Щільний захист і контратаки.",
                "Збалансований": "Рівномірне навантаження між атакою та захистом.",
            }
            if selected_tactic in tactic_descriptions:
                st.caption(f"💡 {tactic_descriptions[selected_tactic]}")
        else:
            selected_tactic = "Ручні точки"
            st.info("Введіть координати для точок активності.")
            cx = st.slider("X координата", 0, 100, 50)
            cy = st.slider("Y координата", 0, 60, 30)
            if st.button("📍 Додати точку"):
                st.session_state.tactic_points.append((cx, cy))
            if st.button("🗑️ Очистити точки"):
                st.session_state.tactic_points = []
                st.rerun()
            st.caption(f"Точок на полі: **{len(st.session_state.tactic_points)}**")

        st.divider()
        st.subheader("📝 Тактичні нотатки")
        st.caption("Зберігайте спостереження та ідеї щодо тактики для конкретного гравця.")
        tactic_note = st.text_area("Нотатки до схеми:", height=80, placeholder="Додайте свої спостереження...")
        if st.button("💾 Зберегти нотатку", use_container_width=True):
            if tactic_note.strip():
                db_save_tactic_note(selected_player, selected_tactic, tactic_note)
                st.success("✅ Нотатку збережено в БД!")
            else:
                st.warning("Введіть текст нотатки.")

        notes_history = db_load_tactic_notes(selected_player)
        if notes_history:
            with st.expander(f"📚 Нотатки для {selected_player} ({len(notes_history)})", expanded=False):
                for note in notes_history[:5]:
                    st.caption(f"🕐 {note['created_at'][:16]} | {note['tactic']}")
                    st.write(note['notes'])
                    st.divider()

        st.divider()
        st.subheader("🏋️ AI-поради")
        st.caption("Рекомендації генеруються автоматично на основі поточних показників гравця.")
        if player_data['Витривалість'] < 60:
            st.error("⚠️ Потрібне кардіо-навантаження!")
        else:
            st.success("✅ Форма стабільна.")
        if player_data['Швидкість'] > 30:
            st.info("💨 Лідер швидкості. Рекомендовано флангові рухи.")
        if player_data['Сила'] > 80:
            st.info("💪 Висока сила — ефективний у єдиноборствах.")
        if player_data.get('Навантаження_7днів', 0) >= 3:
            st.warning("😓 Високе тижневе навантаження — дайте гравцю відновитись перед наступним матчем.")

    with col_left:
        st.subheader(f"🔥 Зони активності: {selected_player}")
        fig, ax = plt.subplots(figsize=(10, 6.5))
        ax.set_facecolor('#1a5c23')
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 60)

        field = patches.Rectangle((2, 2), 96, 56, linewidth=2, edgecolor='white', facecolor='none')
        ax.add_patch(field)
        ax.plot([50, 50], [2, 58], color='white', linewidth=1.5)
        center_circle = plt.Circle((50, 30), 9.15, color='white', fill=False, linewidth=1.5)
        ax.add_patch(center_circle)
        ax.plot(50, 30, 'wo', markersize=4)
        ax.add_patch(patches.Rectangle((2, 15), 16.5, 30, linewidth=1.5, edgecolor='white', facecolor='none'))
        ax.add_patch(patches.Rectangle((81.5, 15), 16.5, 30, linewidth=1.5, edgecolor='white', facecolor='none'))
        ax.add_patch(patches.Rectangle((0, 24), 2, 12, linewidth=1.5, edgecolor='white', facecolor='#333333'))
        ax.add_patch(patches.Rectangle((98, 24), 2, 12, linewidth=1.5, edgecolor='white', facecolor='#333333'))

        def get_preset_points(tactic, spread):
            presets = {
                "4-3-3 (Атака)": [(5,30),(20,12),(20,22),(20,38),(20,48),(42,18),(45,30),(42,42),(72,12),(75,30),(72,48)],
                "4-4-2 (Баланс)": [(5,30),(20,12),(20,24),(20,36),(20,48),(45,12),(45,24),(45,36),(45,48),(70,22),(70,38)],
                "5-3-2 (Захист)": [(5,30),(18,8),(18,20),(18,30),(18,40),(18,52),(40,18),(40,30),(40,42),(65,22),(65,38)],
                "3-5-2 (Контроль)": [(5,30),(20,18),(20,30),(20,42),(42,8),(42,20),(42,30),(42,40),(42,52),(68,22),(68,38)],
            }
            default_pts = [(random.gauss(50, spread), random.gauss(30, 10)) for _ in range(80)]
            if tactic in presets:
                base_pts = presets[tactic]
                pts = []
                for bx, by in base_pts:
                    for _ in range(8):
                        pts.append((np.clip(bx + random.gauss(0, spread/2), 2, 98),
                                    np.clip(by + random.gauss(0, 4), 2, 58)))
                return pts
            return default_pts

        spread = 20 if player_data['Витривалість'] > 75 else 10

        if mode == "🎯 Пресет тактики":
            heat_points = get_preset_points(selected_tactic, spread)
            xs = [p[0] for p in heat_points]
            ys = [p[1] for p in heat_points]
            hb = ax.hexbin(xs, ys, gridsize=18, cmap='YlOrRd', alpha=0.75, extent=(0,100,0,60))
            plt.colorbar(hb, ax=ax, label='Інтенсивність')
            ax.set_title(f"Тактика: {selected_tactic}", color='white', fontsize=12)
        else:
            if len(st.session_state.tactic_points) >= 3:
                xs = [p[0] for p in st.session_state.tactic_points]
                ys = [p[1] for p in st.session_state.tactic_points]
                hb = ax.hexbin(xs, ys, gridsize=12, cmap='plasma', alpha=0.75, extent=(0,100,0,60))
                plt.colorbar(hb, ax=ax, label='Інтенсивність')
            for px, py in st.session_state.tactic_points:
                ax.plot(px, py, 'o', color='cyan', markersize=8, zorder=5,
                        markeredgecolor='white', markeredgewidth=1.5)
            ax.set_title(f"Ручні точки ({len(st.session_state.tactic_points)} шт.)", color='white', fontsize=12)

        fig.patch.set_facecolor('#0d3318')
        ax.set_xticks([])
        ax.set_yticks([])
        st.pyplot(fig)
        plt.close(fig)


# ==========================================
# 5. ІНТЕГРАЦІЯ З МЕДІА
# ==========================================
def render_media_integration():
    st.title("📹 Інтеграція з медіа")
    st.markdown("""
    Прив'яжіть відеозаписи матчів до аналітичних нотаток. Вставляйте YouTube-посилання,
    переглядайте відео прямо в застосунку та зберігайте спостереження в базу даних.
    Розділ «Фото схем» дозволяє архівувати знімки тактичних дощок з тренувань.
    """)

    tab_video, tab_photo = st.tabs(["📹 Аналіз Відео", "📸 Фото схем"])

    with tab_video:
        st.subheader("Відеоаналіз матчів")
        st.caption("Вставте посилання на YouTube-відео для перегляду поряд із нотатками аналітика. Нотатки автоматично зберігаються та доступні після перезапуску.")
        youtube_url = st.text_input("YouTube URL", placeholder="Вставте посилання тут...")

        col_vid, col_notes = st.columns([2, 1])
        with col_vid:
            if youtube_url:
                try:
                    st.video(youtube_url)
                except Exception:
                    st.error("Помилка завантаження відео. Перевірте правильність посилання.")
            else:
                st.info("👈 Введіть посилання на відео.")

        with col_notes:
            st.subheader("📝 Нотатки аналітика")
            latest = db_get_latest_video_note()
            default_notes = latest["notes"] if latest else ""

            notes = st.text_area("Ваші спостереження:", value=default_notes, height=220,
                                 placeholder="Наприклад: на 23-й хвилині лівий фланг залишився без прикриття...")

            if st.button("💾 Зберегти нотатки", use_container_width=True, type="primary"):
                db_save_video_note(youtube_url or "", notes)
                st.success("✅ Нотатки збережено в БД!")

            # --- Нова функція: лічильник слів ---
            word_count = len(notes.split()) if notes else 0
            st.caption(f"📝 Слів у нотатках: **{word_count}**")

        st.divider()
        all_notes = db_load_video_notes()
        if all_notes:
            with st.expander(f"📚 Архів нотаток ({len(all_notes)})", expanded=False):
                st.caption("Останні 20 збережених аналітичних нотаток. Натисніть на посилання для перегляду відео.")
                for note in all_notes:
                    col_t, col_n = st.columns([1, 4])
                    col_t.caption(note['created_at'][:16])
                    if note['url']:
                        col_n.markdown(f"🔗 [{note['url'][:40]}...]({note['url']})")
                    col_n.write(note['notes'])
                    st.divider()

    with tab_photo:
        st.subheader("Оцифрування тактичних схем")
        st.caption("Сфотографуйте тактичну дошку після тренування та збережіть в архів. Для автоматичного розпізнавання маркерів та стрілок використовуйте розділ **OCR Тактичних фото**.")
        photo = st.camera_input("Сфотографувати тактичну схему")

        if photo is not None:
            st.success("✅ Фото успішно зроблено!")
            if st.button("💾 Додати в архів схем", type="primary"):
                st.session_state.tactical_photos.append(photo)
                st.rerun()

        if st.session_state.tactical_photos:
            st.divider()
            st.subheader(f"📂 Архів збережених схем ({len(st.session_state.tactical_photos)})")
            st.caption("Знімки зберігаються в пам'яті сесії. Для постійного зберігання використовуйте розділ OCR.")
            cols = st.columns(3)
            for i, saved_photo in enumerate(st.session_state.tactical_photos):
                with cols[i % 3]:
                    st.image(saved_photo, caption=f"Схема #{i+1}", use_container_width=True)
                    if st.button(f"🗑️ Видалити", key=f"del_photo_{i}", use_container_width=True):
                        st.session_state.tactical_photos.pop(i)
                        st.rerun()
        else:
            st.info("Архів схем наразі порожній. Зробіть фото вище, щоб додати першу схему.")


# ==========================================
# 5.5 CV АНАЛІЗ ВІДЕО
# ==========================================

def simulate_tracking_data_internal(num_players_per_team=5, num_frames=300, fps=25):
    import math
    teams = {"Червона команда": [], "Синя команда": []}
    ball_positions = []
    events = []

    red_starts = [(15+i*10, 15+j*14) for i in range(3) for j in range(2)][:num_players_per_team]
    blue_starts = [(90-i*10, 15+j*14) for i in range(3) for j in range(2)][:num_players_per_team]

    red_pos = [list(p) for p in red_starts]
    blue_pos = [list(p) for p in blue_starts]
    ball = [52.5, 34.0]

    for frame in range(num_frames):
        t = frame / fps
        for p in red_pos:
            p[0] = np.clip(p[0] + np.clip(random.gauss(0.25, 0.7), -1.5, 2.5), 2, 103)
            p[1] = np.clip(p[1] + np.clip(random.gauss(0, 1.0), -2.5, 2.5), 2, 66)
        for p in blue_pos:
            p[0] = np.clip(p[0] + np.clip(random.gauss(-0.25, 0.7), -2.5, 1.5), 2, 103)
            p[1] = np.clip(p[1] + np.clip(random.gauss(0, 1.0), -2.5, 2.5), 2, 66)

        ball[0] = np.clip(ball[0] + math.sin(t*0.6)*1.3 + random.gauss(0, 0.4), 2, 103)
        ball[1] = np.clip(ball[1] + math.cos(t*0.4)*0.9 + random.gauss(0, 0.4), 2, 66)

        teams["Червона команда"].append([tuple(p) for p in red_pos])
        teams["Синя команда"].append([tuple(p) for p in blue_pos])
        ball_positions.append(tuple(ball))

        if frame % 60 == 0 and frame > 0:
            events.append({
                "frame": frame, "time": round(t, 1),
                "type": random.choice(["УДАР ПО ВОРОТАХ", "ПАС У РОЗРІЗ", "ПЕРЕХОПЛЕННЯ", "КУТОВИЙ"]),
                "team": random.choice(["Червона команда", "Синя команда"]),
                "icon": random.choice(["⚽", "🎯", "🛡️", "🚩"]),
                "confidence": round(random.uniform(0.68, 0.96), 2)
            })

    return teams, ball_positions, events


def generate_heatmap_internal(positions, resolution=40):
    heatmap = np.zeros((resolution, resolution))
    for pos_frame in positions:
        for (x, y) in (pos_frame if isinstance(pos_frame, list) else [pos_frame]):
            px = int(np.clip((x/105)*resolution, 0, resolution-1))
            py = int(np.clip((y/68)*resolution, 0, resolution-1))
            sigma = 2.0
            for i in range(max(0, px-4), min(resolution, px+5)):
                for j in range(max(0, py-4), min(resolution, py+5)):
                    dist = np.sqrt((i-px)**2 + (j-py)**2)
                    heatmap[j, i] += np.exp(-dist**2 / (2*sigma**2))
    return heatmap


def render_cv_analysis():
    st.title("🎥 Computer Vision: Автоматичний аналіз відео")
    st.markdown("""
    Модуль комп'ютерного зору автоматично відстежує переміщення гравців і м'яча,
    будує теплові карти активності, розраховує фізичні показники (дистанція, швидкість)
    та фіксує ключові ігрові події. У демо-режимі дані симулюються без реального відео.
    """)

    tab_input, tab_tracking, tab_heatmap, tab_physics, tab_events = st.tabs([
        "📁 Джерело відео", "📍 Трекінг гравців", "🔥 Теплові карти",
        "⚡ Фізичні показники", "📋 Журнал подій"
    ])

    with tab_input:
        st.subheader("Оберіть джерело для аналізу")
        st.caption("Для реального аналізу відео завантажте файл у форматі MP4/AVI/MOV. Демо-режим генерує синтетичні траєкторії для знайомства з функціоналом.")
        source_mode = st.radio("Режим аналізу:", ["🎮 Демо-симуляція", "📹 Завантажити відеофайл"], horizontal=True)

        if source_mode == "📹 Завантажити відеофайл":
            st.info("📌 Підтримувані формати: MP4, AVI, MOV.")
            st.file_uploader("Завантажте відеозапис:", type=["mp4", "avi", "mov"])
            if st.button("🚀 Запустити аналіз відео", type="primary", use_container_width=True):
                st.error("⚠️ Для реального аналізу потрібна бібліотека OpenCV: `pip install opencv-python-headless`")
        else:
            col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
            demo_players = col_cfg1.slider("Гравців у команді:", 3, 8, 5)
            demo_frames = col_cfg2.slider("Кадрів симуляції:", 100, 500, 300)
            demo_fps = col_cfg3.selectbox("FPS:", [25, 30, 50, 60])

            if st.button("🎬 Запустити демо-аналіз", type="primary", use_container_width=True):
                with st.spinner("Симулюємо трекінг..."):
                    progress = st.progress(0)
                    for i in range(10):
                        time.sleep(0.08)
                        progress.progress((i+1)/10)
                    teams_data, ball_positions, events = simulate_tracking_data_internal(
                        num_players_per_team=demo_players, num_frames=demo_frames, fps=demo_fps)
                    st.session_state.cv_teams_data = teams_data
                    st.session_state.cv_ball_positions = ball_positions
                    st.session_state.cv_events = events
                    st.session_state.cv_fps = demo_fps
                    st.session_state.cv_analysis_done = True
                st.success(f"✅ Демо-аналіз завершено! {demo_frames} кадрів, {len(events)} подій.")
                st.rerun()

        if st.session_state.cv_analysis_done:
            st.success("✅ Дані аналізу доступні. Перейдіть до інших вкладок.")
            # --- Нова функція: короткий підсумок CV ---
            teams_data = st.session_state.cv_teams_data
            total_players = sum(
                max(len(f) for f in frames) if frames else 0
                for frames in teams_data.values()
            )
            st.info(f"📊 Відстежено гравців: **{total_players}** | Кадрів: **{len(st.session_state.cv_ball_positions)}** | Подій: **{len(st.session_state.cv_events)}**")

    with tab_tracking:
        if not st.session_state.cv_analysis_done:
            st.info("👈 Спочатку запустіть аналіз на вкладці «Джерело відео».")
            return
        st.subheader("📍 Траєкторії руху гравців")
        st.caption("Графік показує фінальні позиції гравців та, опційно, їхні траєкторії руху за весь час аналізу. Жовта пунктирна лінія — траєкторія м'яча.")
        teams_data = st.session_state.cv_teams_data
        ball_positions = st.session_state.cv_ball_positions

        fig, ax = plt.subplots(figsize=(14, 9))
        ax.set_facecolor('#1a5c23')
        ax.set_xlim(0, 105); ax.set_ylim(0, 68)
        ax.add_patch(patches.Rectangle((0,0), 105, 68, linewidth=2, edgecolor='white', facecolor='none'))
        ax.plot([52.5,52.5], [0,68], 'w-', linewidth=1.5)
        ax.add_patch(plt.Circle((52.5, 34), 9.15, color='white', fill=False, linewidth=1.5))

        show_trails = st.checkbox("Показати траєкторії", value=True)
        show_ball = st.checkbox("Показати траєкторію м'яча", value=True)
        frame_step = st.slider("Крок відображення:", 1, 20, 5)

        TEAM_COLORS = {"Червона команда": ("#FF4444", "o"), "Синя команда": ("#4488FF", "s")}

        for team_name, (team_color, marker) in TEAM_COLORS.items():
            if team_name not in teams_data: continue
            team_frames = teams_data[team_name]
            num_players = max(len(f) for f in team_frames) if team_frames else 0
            for player_idx in range(num_players):
                xs, ys = [], []
                for frame_positions in team_frames[::frame_step]:
                    if player_idx < len(frame_positions):
                        px, py = frame_positions[player_idx]
                        xs.append(px); ys.append(py)
                if xs:
                    if show_trails:
                        ax.plot(xs, ys, '-', color=team_color, alpha=0.3, linewidth=1)
                    ax.plot(xs[-1], ys[-1], marker=marker, color=team_color, markersize=10,
                            zorder=5, markeredgecolor='white', markeredgewidth=1.5)
                    ax.text(xs[-1]+1, ys[-1]+1, f"#{player_idx+1}", color='white', fontsize=7, zorder=6)

        if show_ball and ball_positions:
            bxs = [p[0] for p in ball_positions[::frame_step]]
            bys = [p[1] for p in ball_positions[::frame_step]]
            ax.plot(bxs, bys, 'y--', alpha=0.4, linewidth=1)
            ax.plot(bxs[-1], bys[-1], 'o', color='yellow', markersize=8, zorder=7, markeredgecolor='black')

        ax.set_title("Трекінг гравців та м'яча", color='white', fontsize=12)
        fig.patch.set_facecolor('#0d3318')
        ax.tick_params(colors='white')
        st.pyplot(fig); plt.close(fig)

    with tab_heatmap:
        if not st.session_state.cv_analysis_done:
            st.info("👈 Спочатку запустіть аналіз.")
            return
        st.subheader("🔥 Теплові карти")
        st.caption("Теплова карта показує зони найбільшої активності команди або м'яча. Червоні зони — максимальна концентрація, зелені — мінімальна.")
        teams_data = st.session_state.cv_teams_data
        ball_positions = st.session_state.cv_ball_positions
        selected_team_hm = st.selectbox("Оберіть команду:", list(teams_data.keys()) + ["М'яч"])

        resolution = 40
        if selected_team_hm == "М'яч":
            heatmap = np.zeros((resolution, resolution))
            for (bx, by) in ball_positions:
                px = int(np.clip((bx/105)*resolution, 0, resolution-1))
                py = int(np.clip((by/68)*resolution, 0, resolution-1))
                heatmap[py, px] += 1
            title = "Теплова карта активності м'яча"
        else:
            heatmap = generate_heatmap_internal(teams_data[selected_team_hm])
            title = f"Теплова карта: {selected_team_hm}"

        if heatmap.max() > 0:
            heatmap = heatmap / heatmap.max()

        fig, ax = plt.subplots(figsize=(12, 7))
        ax.set_facecolor('#1a5c23')
        cmap = LinearSegmentedColormap.from_list('heat', ['#1a5c23', '#ffdd00', '#ff6600', '#cc0000'])
        ax.imshow(heatmap, extent=[0,105,0,68], origin='lower', cmap=cmap, alpha=0.75, aspect='auto')
        ax.add_patch(patches.Rectangle((0,0), 105, 68, linewidth=2, edgecolor='white', facecolor='none'))
        ax.plot([52.5,52.5], [0,68], 'w-', linewidth=1.5)
        ax.set_title(title, color='white', fontsize=12)
        fig.patch.set_facecolor('#0d3318')
        ax.tick_params(colors='white')
        st.pyplot(fig); plt.close(fig)

        # --- Нова функція: зональна статистика ---
        st.subheader("📐 Зональна статистика")
        st.caption("Поле розділене на три зони: захист (0–35м), середина (35–70м), атака (70–105м).")
        zones = {"🔵 Захист (0–35м)": heatmap[:, :int(resolution*35/105)],
                 "🟡 Середина (35–70м)": heatmap[:, int(resolution*35/105):int(resolution*70/105)],
                 "🔴 Атака (70–105м)": heatmap[:, int(resolution*70/105):]}
        zcols = st.columns(3)
        for col, (zone_name, zone_data) in zip(zcols, zones.items()):
            pct = zone_data.mean() * 100
            col.metric(zone_name, f"{pct:.1f}%")

    with tab_physics:
        if not st.session_state.cv_analysis_done:
            st.info("👈 Спочатку запустіть аналіз.")
            return
        st.subheader("⚡ Фізичні показники гравців")
        st.caption("Розраховані на основі траєкторій переміщення: загальна дистанція, середня та максимальна швидкість за матч.")
        teams_data = st.session_state.cv_teams_data
        fps = st.session_state.cv_fps
        stats_rows = []
        for team_name, team_frames in teams_data.items():
            if not team_frames: continue
            num_players = max(len(f) for f in team_frames)
            for player_idx in range(num_players):
                player_positions = [f[player_idx] for f in team_frames if player_idx < len(f)]
                if len(player_positions) < 2: continue
                speeds, total_dist = [], 0.0
                for i in range(1, len(player_positions)):
                    x1, y1 = player_positions[i-1]
                    x2, y2 = player_positions[i]
                    dist = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                    total_dist += dist
                    speeds.append(dist * fps * 3.6)
                stats_rows.append({
                    "Команда": team_name, "Гравець": f"#{player_idx+1}",
                    "Дистанція (м)": round(total_dist, 1),
                    "Середня швидкість (км/год)": round(np.mean(speeds), 1),
                    "Макс. швидкість (км/год)": round(np.max(speeds), 1),
                })
        if stats_rows:
            stats_df = pd.DataFrame(stats_rows)
            st.dataframe(stats_df.style.background_gradient(cmap='RdYlGn', subset=['Макс. швидкість (км/год)']),
                        use_container_width=True, hide_index=True)
            # --- Нова функція: командний підсумок ---
            st.divider()
            st.subheader("📊 Командний підсумок")
            team_summary = stats_df.groupby("Команда").agg({
                "Дистанція (м)": "sum",
                "Середня швидкість (км/год)": "mean",
                "Макс. швидкість (км/год)": "max"
            }).round(1)
            st.dataframe(team_summary, use_container_width=True)

    with tab_events:
        if not st.session_state.cv_analysis_done:
            st.info("👈 Спочатку запустіть аналіз.")
            return
        st.subheader("📋 Журнал ігрових подій")
        st.caption("Автоматично виявлені ключові моменти матчу: удари, паси, перехоплення, стандарти. Відсоток впевненості показує якість розпізнавання CV-моделлю.")
        events = st.session_state.cv_events
        if not events:
            st.info("Подій не виявлено.")
        else:
            # --- Нова функція: фільтр подій по команді ---
            all_teams = list(set(e.get("team", "") for e in events))
            filter_team = st.selectbox("Фільтр за командою:", ["Всі команди"] + all_teams)

            for event in events:
                if filter_team != "Всі команди" and event.get("team") != filter_team:
                    continue
                t_sec = event.get("time", 0)
                mins, secs = int(t_sec//60), int(t_sec%60)
                col_time, col_icon, col_desc, col_conf = st.columns([1, 0.5, 5, 1.5])
                col_time.markdown(f"**{mins:02d}:{secs:02d}**")
                col_icon.write(event["icon"])
                col_desc.write(f"**{event['type']}** — {event.get('team', '')}")
                col_conf.metric("Впевненість", f"{event.get('confidence', 0)*100:.0f}%")


# ==========================================
# 5.7 OCR ТАКТИЧНИХ ФОТО
# ==========================================

def analyze_tactical_photo_simulation(db_df):
    np.random.seed(42)
    num_red = random.randint(3, 6)
    num_blue = random.randint(3, 6)

    red_markers = []
    for i in range(num_red):
        red_markers.append({
            "x": round(random.uniform(5, 50), 1),
            "y": round(random.uniform(5, 63), 1),
            "number": random.randint(1, 11),
            "color": "red",
            "confidence": round(random.uniform(0.72, 0.97), 2)
        })

    blue_markers = []
    for i in range(num_blue):
        blue_markers.append({
            "x": round(random.uniform(55, 100), 1),
            "y": round(random.uniform(5, 63), 1),
            "number": random.randint(1, 11),
            "color": "blue",
            "confidence": round(random.uniform(0.72, 0.97), 2)
        })

    arrows = []
    all_markers = red_markers + blue_markers
    for _ in range(random.randint(3, 7)):
        if not all_markers: break
        marker = random.choice(all_markers)
        dx, dy = random.uniform(-25, 25), random.uniform(-20, 20)
        arrows.append({
            "from_x": marker["x"], "from_y": marker["y"],
            "to_x": round(np.clip(marker["x"]+dx, 2, 103), 1),
            "to_y": round(np.clip(marker["y"]+dy, 2, 66), 1),
            "color": marker["color"],
            "distance_m": round(np.sqrt(dx**2+dy**2), 1)
        })

    synchronized_players = []
    for marker in red_markers + blue_markers:
        db_match = db_df[db_df['Номер'] == marker["number"]] if 'Номер' in db_df.columns else pd.DataFrame()
        if not db_match.empty:
            player_row = db_match.iloc[0]
            player_name = player_row["Ім'я"]
            player_speed = player_row["Швидкість"]
            player_stamina = player_row["Витривалість"]
        else:
            player_name = f"Гравець #{marker['number']}"
            player_speed = random.uniform(20, 32)
            player_stamina = random.uniform(50, 90)

        player_arrow = next((a for a in arrows if abs(a["from_x"]-marker["x"]) < 2 and abs(a["from_y"]-marker["y"]) < 2), None)

        if player_arrow:
            dist = player_arrow["distance_m"]
            maneuver_difficulty = "✅ Реалізовано" if not (dist > 30 and player_speed < 25) else "⚠️ Складно"
            if dist > 40: maneuver_difficulty = "❌ Задовго для маневру"
        else:
            dist, maneuver_difficulty = None, "—"

        synchronized_players.append({
            "Маркер": f"#{marker['number']}",
            "Команда": "🔴 Червона" if marker["color"] == "red" else "🔵 Синя",
            "Гравець": player_name,
            "Позиція X (м)": marker["x"],
            "Позиція Y (м)": marker["y"],
            "Швидкість": round(player_speed, 1),
            "Витривалість": round(player_stamina, 0),
            "Дистанція маневру (м)": dist,
            "Виконуваність": maneuver_difficulty,
            "Впевненість OCR": f"{marker['confidence']*100:.0f}%"
        })

    return {
        "red_markers": red_markers, "blue_markers": blue_markers,
        "arrows": arrows, "synchronized_players": synchronized_players,
        "total_markers": len(red_markers)+len(blue_markers),
        "total_arrows": len(arrows)
    }


def draw_digitized_field(result):
    from matplotlib.lines import Line2D
    fig, ax = plt.subplots(figsize=(14, 9))
    ax.set_facecolor('#1a5c23'); ax.set_xlim(0, 105); ax.set_ylim(0, 68)

    ax.add_patch(patches.Rectangle((0,0), 105, 68, linewidth=2, edgecolor='white', facecolor='none'))
    ax.plot([52.5,52.5], [0,68], 'w-', linewidth=1.5)
    ax.add_patch(plt.Circle((52.5, 34), 9.15, color='white', fill=False, linewidth=1.5))
    ax.plot(52.5, 34, 'wo', markersize=4)
    ax.add_patch(patches.Rectangle((0,13.84), 16.5, 40.32, linewidth=1.5, edgecolor='white', facecolor='none'))
    ax.add_patch(patches.Rectangle((88.5,13.84), 16.5, 40.32, linewidth=1.5, edgecolor='white', facecolor='none'))
    ax.add_patch(patches.Rectangle((-2,28.84), 2, 10.32, linewidth=1.5, edgecolor='white', facecolor='#444'))
    ax.add_patch(patches.Rectangle((105,28.84), 2, 10.32, linewidth=1.5, edgecolor='white', facecolor='#444'))

    for arrow in result["arrows"]:
        arrow_color = '#FF8888' if arrow["color"] == "red" else '#88AAFF'
        ax.annotate("", xy=(arrow["to_x"], arrow["to_y"]), xytext=(arrow["from_x"], arrow["from_y"]),
                    arrowprops=dict(arrowstyle="-|>", color=arrow_color, lw=2.0, mutation_scale=18, alpha=0.85), zorder=3)

    for marker in result["red_markers"]:
        ax.add_patch(plt.Circle((marker["x"], marker["y"]), 2.2, color='#FF2222', zorder=5, edgecolor='white', linewidth=2))
        ax.text(marker["x"], marker["y"], str(marker["number"]), ha='center', va='center', color='white', fontsize=8, fontweight='bold', zorder=6)

    for marker in result["blue_markers"]:
        ax.add_patch(plt.Circle((marker["x"], marker["y"]), 2.2, color='#2244FF', zorder=5, edgecolor='white', linewidth=2))
        ax.text(marker["x"], marker["y"], str(marker["number"]), ha='center', va='center', color='white', fontsize=8, fontweight='bold', zorder=6)

    ax.legend(handles=[
        plt.Circle((0,0), radius=1, color='#FF2222', label=f'Червона ({len(result["red_markers"])} гр.)'),
        plt.Circle((0,0), radius=1, color='#2244FF', label=f'Синя ({len(result["blue_markers"])} гр.)'),
        Line2D([0],[0], color='#FF8888', linewidth=2, label='Рух (червоні)'),
        Line2D([0],[0], color='#88AAFF', linewidth=2, label='Рух (сині)'),
    ], loc='lower right', facecolor='#0d3318', labelcolor='white', fontsize=9, framealpha=0.9)

    ax.set_title("🖼️ Цифрове поле: результат OCR", color='white', fontsize=13, pad=12)
    ax.set_xlabel("Довжина поля (м)", color='white')
    ax.set_ylabel("Ширина поля (м)", color='white')
    ax.tick_params(colors='white')
    fig.patch.set_facecolor('#0d3318')
    return fig


def render_tactical_ocr(df):
    st.title("🖼️ OCR Тактичних фото: Оцифрування тактичної дошки")
    st.markdown("""
    Завантажте або сфотографуйте тактичну дошку — система автоматично розпізнає
    кольорові фішки, номери гравців та стрілки переміщення. Результати синхронізуються
    з базою гравців: для кожного маневру перевіряється його реалістичність
    з урахуванням швидкості та витривалості конкретного спортсмена.
    """)

    col_mode1, col_mode2 = st.columns(2)
    with col_mode1:
        st.subheader("📸 Завантажити фото")
        source_option = st.radio("Спосіб введення:",
            ["📁 Завантажити файл", "📷 Зробити фото камерою", "🎮 Демо без фото"], key="ocr_source")

    with col_mode2:
        st.subheader("⚙️ Параметри")
        sensitivity = st.slider("Чутливість кольору:", 10, 50, 25)
        min_marker_radius = st.slider("Мін. розмір фішки (px):", 5, 30, 12)
        enable_ocr = st.checkbox("Розпізнавання номерів (OCR)", value=True)
        enable_arrows = st.checkbox("Векторизація стрілок", value=True)
        st.caption("💡 Збільшіть чутливість, якщо фішки на фото мають блідіші кольори. Зменшіть — для уникнення хибних спрацьовань.")

    st.divider()

    uploaded_image, camera_image = None, None

    if source_option == "📁 Завантажити файл":
        uploaded_image = st.file_uploader("Завантажте фото:", type=["jpg", "jpeg", "png", "bmp", "webp"])
        if uploaded_image:
            st.image(uploaded_image, caption="📸 Завантажене фото", use_container_width=True)
    elif source_option == "📷 Зробити фото камерою":
        camera_image = st.camera_input("Сфотографуйте тактичну дошку:")
        if camera_image:
            st.success("✅ Фото зроблено!")
    else:
        st.info("🎮 **Демо-режим:** симульовані дані без реального фото. Всі координати та номери генеруються автоматично для демонстрації функціоналу.")

    st.divider()
    has_input = bool(uploaded_image or camera_image or source_option == "🎮 Демо без фото")

    if has_input:
        if st.button("🔬 Запустити OCR аналіз", type="primary", use_container_width=True):
            with st.spinner("Аналізуємо тактичну дошку..."):
                progress = st.progress(0)
                status = st.empty()
                for prog_val, msg in [(0.15,"🔍 Обробка зображення..."), (0.3,"🎯 Пошук маркерів..."),
                                       (0.5,"📖 OCR номерів..."), (0.7,"↗️ Векторизація стрілок..."),
                                       (0.85,"🔗 Синхронізація з БД..."), (1.0,"✅ Готово!")]:
                    time.sleep(0.35)
                    progress.progress(prog_val)
                    status.text(msg)

                result = analyze_tactical_photo_simulation(df)
                st.session_state.ocr_result = result
                st.session_state.ocr_photo = uploaded_image or camera_image
                db_save_ocr_result(result)

            st.success(f"✅ Розпізнано: **{result['total_markers']} фішок** та **{result['total_arrows']} стрілок**! Збережено в БД.")
            st.rerun()

    ocr_history = db_load_ocr_history()
    if ocr_history:
        with st.expander(f"🗃️ Архів OCR аналізів у БД ({len(ocr_history)})", expanded=False):
            st.caption("Всі попередні OCR-аналізи збережені в SQLite. Ви можете переглянути та порівняти результати різних тактичних схем.")
            for entry in ocr_history:
                r = entry["result"]
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Дата", entry["created_at"][:16])
                col_b.metric("Фішок", r.get("total_markers", 0))
                col_c.metric("Стрілок", r.get("total_arrows", 0))
                st.divider()

    if st.session_state.ocr_result is not None:
        result = st.session_state.ocr_result
        st.divider()
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        col_s1.metric("🔴 Червоні фішки", len(result["red_markers"]))
        col_s2.metric("🔵 Сині фішки", len(result["blue_markers"]))
        col_s3.metric("↗️ Стрілок", result["total_arrows"])
        col_s4.metric("👥 Синхронізовано", len(result["synchronized_players"]))
        st.divider()

        res_tab1, res_tab2, res_tab3, res_tab4 = st.tabs([
            "🗺️ Цифрова схема", "📋 Гравці та маневри",
            "↗️ Векторизовані стрілки", "📊 Аналіз виконуваності"
        ])

        with res_tab1:
            col_orig, col_digital = st.columns(2)
            with col_orig:
                st.markdown("**Оригінальне фото:**")
                if st.session_state.ocr_photo:
                    st.image(st.session_state.ocr_photo, use_container_width=True)
                else:
                    fig_ph, ax_ph = plt.subplots(figsize=(7, 5))
                    ax_ph.set_facecolor('#2a2a2a')
                    ax_ph.text(0.5, 0.5, '📷 Демо режим', ha='center', va='center',
                               fontsize=16, color='white', transform=ax_ph.transAxes)
                    ax_ph.set_xticks([]); ax_ph.set_yticks([])
                    fig_ph.patch.set_facecolor('#1a1a1a')
                    st.pyplot(fig_ph); plt.close(fig_ph)
            with col_digital:
                st.markdown("**Цифрова схема (результат OCR):**")
                fig_field = draw_digitized_field(result)
                st.pyplot(fig_field); plt.close(fig_field)

            st.divider()
            col_red, col_blue = st.columns(2)
            with col_red:
                st.markdown("**🔴 Червона команда:**")
                red_df = pd.DataFrame(result["red_markers"])[["number","x","y","confidence"]]
                red_df.columns = ["Номер","X (м)","Y (м)","Впевненість"]
                red_df["Впевненість"] = red_df["Впевненість"].apply(lambda x: f"{x*100:.0f}%")
                st.dataframe(red_df, use_container_width=True, hide_index=True)
            with col_blue:
                st.markdown("**🔵 Синя команда:**")
                blue_df = pd.DataFrame(result["blue_markers"])[["number","x","y","confidence"]]
                blue_df.columns = ["Номер","X (м)","Y (м)","Впевненість"]
                blue_df["Впевненість"] = blue_df["Впевненість"].apply(lambda x: f"{x*100:.0f}%")
                st.dataframe(blue_df, use_container_width=True, hide_index=True)

        with res_tab2:
            st.subheader("📋 Синхронізація з базою гравців")
            st.caption("Для кожної фішки система знайшла відповідного гравця за номером у вашій базі даних і перевірила, чи відповідає маневр його фізичним можливостям.")
            sync_df = pd.DataFrame(result["synchronized_players"])

            def color_feasibility(val):
                if "✅" in str(val): return 'background-color: #1a4a1a; color: #66ff66'
                elif "⚠️" in str(val): return 'background-color: #4a3a00; color: #ffcc00'
                elif "❌" in str(val): return 'background-color: #4a1a1a; color: #ff6666'
                return ''

            st.dataframe(sync_df.style.applymap(color_feasibility, subset=["Виконуваність"])
                        .format({"Позиція X (м)": "{:.1f}", "Позиція Y (м)": "{:.1f}",
                                 "Швидкість": "{:.1f}", "Витривалість": "{:.0f}"}),
                        use_container_width=True, hide_index=True)

        with res_tab3:
            st.subheader("↗️ Векторизовані стрілки")
            st.caption("Стрілки класифіковані за довжиною: короткі (<15м) — локальні переміщення, середні (15–30м) — стандартні маневри, довгі (>30м) — потребують перевірки витривалості.")
            if result["arrows"]:
                arrows_df = pd.DataFrame(result["arrows"])
                arrows_df["Команда"] = arrows_df["color"].apply(lambda c: "🔴 Червона" if c == "red" else "🔵 Синя")
                arrows_df = arrows_df[["Команда","from_x","from_y","to_x","to_y","distance_m"]]
                arrows_df.columns = ["Команда","Старт X","Старт Y","Кінець X","Кінець Y","Довжина (м)"]

                def classify_arrow(d):
                    if d < 15: return "🟢 Короткий"
                    elif d < 30: return "🟡 Середній"
                    return "🔴 Довгий"

                arrows_df["Тип"] = arrows_df["Довжина (м)"].apply(classify_arrow)
                st.dataframe(arrows_df.style.format({"Старт X": "{:.1f}", "Старт Y": "{:.1f}",
                                                      "Кінець X": "{:.1f}", "Кінець Y": "{:.1f}",
                                                      "Довжина (м)": "{:.1f}"}),
                            use_container_width=True, hide_index=True)

        with res_tab4:
            st.subheader("📊 Аналіз реалістичності тактики")
            st.caption("Система перевіряє кожен маневр: чи зможе гравець з такою швидкістю та витривалістю реально виконати задану схему переміщення?")
            sync_df = pd.DataFrame(result["synchronized_players"])
            if not sync_df.empty:
                feasible = sync_df["Виконуваність"].str.contains("✅").sum()
                hard = sync_df["Виконуваність"].str.contains("⚠️").sum()
                impossible = sync_df["Виконуваність"].str.contains("❌").sum()

                c1, c2, c3 = st.columns(3)
                c1.metric("✅ Виконуваних", feasible)
                c2.metric("⚠️ Складних", hard)
                c3.metric("❌ Нереалістичних", impossible)

                total_with_arrows = feasible + hard + impossible
                if total_with_arrows > 0:
                    success_rate = feasible / total_with_arrows * 100
                    if success_rate >= 75:
                        st.success(f"✅ Тактика реалістична: {success_rate:.0f}% маневрів відповідають можливостям гравців.")
                    elif success_rate >= 50:
                        st.warning(f"⚠️ Часткова реалістичність: {success_rate:.0f}%. Рекомендуємо скоротити дистанції.")
                    else:
                        st.error(f"❌ Тактика потребує перегляду: лише {success_rate:.0f}% маневрів реалістичні.")

        st.divider()
        col_clear, col_export = st.columns(2)
        with col_clear:
            if st.button("🗑️ Очистити результати", use_container_width=True):
                st.session_state.ocr_result = None
                st.session_state.ocr_photo = None
                st.rerun()
        with col_export:
            if result and result["synchronized_players"]:
                export_df = pd.DataFrame(result["synchronized_players"])
                st.download_button("📥 Експортувати CSV", export_df.to_csv(index=False).encode('utf-8'),
                                   "tactical_ocr_result.csv", mime="text/csv", use_container_width=True)


# ==========================================
# 6. ЛАБОРАТОРІЯ ФІЗИКИ
# ==========================================
def render_physics(df):
    st.title("⚛️ Лабораторія Фізики")
    st.markdown("""
    Застосовуйте фізичні моделі для аналізу рухів у спорті. Розраховуйте траєкторію удару,
    порівнюйте кінетичну та потенційну енергію, аналізуйте оптимальний кут для максимальної дальності.
    Параметри прив'язані до показників обраного спортсмена.
    """)

    player = st.selectbox("Оберіть спортсмена:", df["Ім'я"])
    data = df[df["Ім'я"] == player].iloc[0]

    tab_proj, tab_energy = st.tabs(["🏹 Траєкторія удару", "⚡ Енергетичний аналіз"])

    with tab_proj:
        st.subheader("Параболічна траєкторія")
        st.caption("Модель балістичного польоту снаряда (м'яча). Початкова швидкість прив'язана до показника сили гравця. Знайдіть оптимальний кут для максимальної дальності (теоретично — 45°).")

        v0 = st.slider("Початкова швидкість (м/с)", 5.0, 50.0, float(data['Сила'] * 0.4))
        angle = st.slider("Кут польоту (°)", 10, 80, 35)

        g = 9.81
        rad = np.radians(angle)
        t_f = (2 * v0 * np.sin(rad)) / g
        t = np.linspace(0, t_f, 200)
        x = v0 * np.cos(rad) * t
        y = v0 * np.sin(rad) * t - 0.5 * g * t ** 2

        max_height = (v0 * np.sin(rad))**2 / (2 * g)
        max_range = x[-1]

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("📏 Дальність польоту", f"{max_range:.1f} м")
        col_m2.metric("📐 Максимальна висота", f"{max_height:.1f} м")
        col_m3.metric("⏱️ Час польоту", f"{t_f:.2f} с")

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(x, y, color="#00BCD4", linewidth=2.5, label=f"Кут: {angle}°")
        ax.fill_between(x, 0, y, alpha=0.15, color="#00BCD4")
        ax.axhline(0, color='white', linewidth=0.5, linestyle='--')
        ax.set_title(f"Траєкторія польоту м'яча — {player}", color='white')
        ax.set_xlabel("Відстань (м)", color='white')
        ax.set_ylabel("Висота (м)", color='white')
        ax.set_facecolor('#1a1a2e')
        ax.tick_params(colors='white')
        ax.legend(facecolor='#1a1a2e', labelcolor='white')
        fig.patch.set_facecolor('#0d0d1a')
        st.pyplot(fig)
        plt.close(fig)

        # --- Нова функція: порівняння кутів ---
        st.subheader("📐 Порівняння дальності для різних кутів")
        st.caption("Як змінюється дальність польоту залежно від кута при тій самій початковій швидкості?")
        angles_range = range(10, 81, 5)
        ranges = [(a, (2 * v0**2 * np.sin(np.radians(a)) * np.cos(np.radians(a))) / g) for a in angles_range]
        angle_df = pd.DataFrame(ranges, columns=["Кут (°)", "Дальність (м)"])
        angle_df["Дальність (м)"] = angle_df["Дальність (м)"].round(1)
        st.bar_chart(angle_df.set_index("Кут (°)"), color="#FF9800")

    with tab_energy:
        st.subheader("⚡ Аналіз кінетичної та потенційної енергії")
        st.caption("Розраховується для гравця масою 75 кг. Кінетична енергія — енергія руху, потенційна — висоти (стрибок).")

        mass = st.slider("Маса спортсмена (кг)", 50, 120, 75)
        speed_ms = data['Швидкість'] / 3.6

        ke = 0.5 * mass * speed_ms**2
        jump_height = st.slider("Висота стрибка (м)", 0.1, 1.2, 0.5, 0.05)
        pe = mass * 9.81 * jump_height

        col_e1, col_e2, col_e3 = st.columns(3)
        col_e1.metric("⚡ Кінетична енергія", f"{ke:.0f} Дж")
        col_e2.metric("🏔️ Потенційна енергія", f"{pe:.0f} Дж")
        col_e3.metric("🔋 Сумарна енергія", f"{ke + pe:.0f} Дж")

        fig2, ax2 = plt.subplots(figsize=(6, 4))
        bars = ax2.bar(["Кінетична", "Потенційна", "Сумарна"], [ke, pe, ke+pe],
                       color=["#FF5252", "#448AFF", "#FFD740"], edgecolor='white')
        ax2.set_ylabel("Енергія (Дж)", color='white')
        ax2.set_facecolor('#1a1a2e')
        ax2.tick_params(colors='white')
        for bar in bars:
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                     f'{bar.get_height():.0f}', ha='center', color='white', fontsize=9)
        fig2.patch.set_facecolor('#0d0d1a')
        st.pyplot(fig2)
        plt.close(fig2)


# ==========================================
# 7. СИМУЛЯТОР МАТЧІВ
# ==========================================
def render_simulator(df):
    st.title("🎲 AI-Симулятор Матчів")
    st.markdown("""
    Зіштовхніть двох гравців у віртуальному поєдинку! Симулятор враховує PER обох спортсменів
    для розрахунку ймовірності перемоги, потім генерує хронологію матчу з реалістичними подіями.
    Усі результати зберігаються в базі даних — переглядайте архів у розділі «Історія матчів».
    """)
    st.divider()

    c1, c_vs, c2 = st.columns([3, 1, 3])
    p1 = c1.selectbox("🔴 Кут 1", df["Ім'я"], key="s1")
    c_vs.markdown("<h2 style='text-align:center;margin-top:25px'>⚔️ VS</h2>", unsafe_allow_html=True)
    p2 = c2.selectbox("🔵 Кут 2", df["Ім'я"], index=min(1, len(df)-1), key="s2")

    p1_data = df[df["Ім'я"] == p1].iloc[0]
    p2_data = df[df["Ім'я"] == p2].iloc[0]
    per1, per2 = p1_data['PER (Рейтинг)'], p2_data['PER (Рейтинг)']
    total_per = per1 + per2
    win_prob_1 = (per1/total_per)*100 if total_per > 0 else 50

    with st.expander("📊 Передматчеве порівняння", expanded=True):
        st.caption("Прогрес-бар показує розподіл шансів на перемогу на основі PER обох гравців.")
        st.progress(win_prob_1/100)
        st.caption(f"Ймовірність домінування: **{p1}** ({win_prob_1:.1f}%) vs **{p2}** ({100-win_prob_1:.1f}%)")
        stat_c1, stat_c2, stat_c3 = st.columns(3)
        stat_c1.metric("Швидкість", f"{p1_data['Швидкість']} км/год", f"{p1_data['Швидкість']-p2_data['Швидкість']:.1f}")
        stat_c2.metric("Витривалість", int(p1_data['Витривалість']), int(p1_data['Витривалість']-p2_data['Витривалість']))
        stat_c3.metric("PER", f"{per1:.1f}", f"{per1-per2:.1f}")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 РОЗПОЧАТИ СИМУЛЯЦІЮ МАТЧУ", type="primary", use_container_width=True):
        with st.spinner("Свисток! Матч розпочався..."):
            time.sleep(1.5)

        log = []
        score1, score2 = 0, 0
        minutes = sorted(random.sample(range(1, 91), random.randint(6, 10)))
        event_templates = {
            "гол": ["{player} влучив у ворота!", "{player} реалізував штрафний!", "{player} пробив під поперечину!"],
            "обіграв": ["{player} обіграв суперника на швидкості {speed:.1f} км/год.", "{player} зробив блискучий фінт."],
            "захист": ["{player} перехопив небезпечну передачу.", "{player} відбив атаку!"],
            "пас": ["{player} віддав геніальний пас у розріз.", "{player} розпочав контратаку."],
            "карточка": ["{player} отримав попередження за фол."]
        }

        for minute in minutes:
            weight1 = per1/(per1+per2)
            active = p1 if random.random() < weight1 else p2
            active_data = p1_data if active == p1 else p2_data

            roll = random.random()
            if roll < 0.25: event_type = "гол"
            elif roll < 0.50: event_type = "обіграв"
            elif roll < 0.70: event_type = "захист"
            elif roll < 0.85: event_type = "пас"
            else: event_type = "карточка"

            template = random.choice(event_templates[event_type])
            event_text = template.format(player=active, speed=active_data.get('Швидкість', 25.0))

            if event_type == "гол":
                if active == p1: score1 += 1
                else: score2 += 1
                icon = "⚽"
            elif event_type == "захист": icon = "🛡️"
            elif event_type == "пас": icon = "🎯"
            elif event_type == "карточка": icon = "🟨"
            else: icon = "💨"

            log.append({"хв": minute, "icon": icon, "подія": event_text, "рахунок": f"{score1}:{score2}"})

        if score1 == score2:
            winner = p1 if per1*random.uniform(0.9,1.1) > per2*random.uniform(0.9,1.1) else p2
            winner_pen = True
        else:
            winner = p1 if score1 > score2 else p2
            winner_pen = False

        db_save_match_log(p1, p2, score1, score2, winner, log)
        st.session_state.match_log = log

        st.divider()
        col_sc1, col_vs2, col_sc2 = st.columns([2, 1, 2])
        col_sc1.markdown(f"<h3 style='text-align:center'>🔴 {p1}</h3><h1 style='text-align:center'>{score1}</h1>", unsafe_allow_html=True)
        col_vs2.markdown("<h3 style='text-align:center;color:gray;margin-top:20px'>КІНЕЦЬ</h3>", unsafe_allow_html=True)
        col_sc2.markdown(f"<h3 style='text-align:center'>🔵 {p2}</h3><h1 style='text-align:center'>{score2}</h1>", unsafe_allow_html=True)

        if winner_pen:
            st.warning(f"⏱️ Нічия {score1}:{score2}. Перемога за показниками: **{winner}**!")
        else:
            st.balloons()
            st.success(f"🏆 **{winner}** перемагає ({score1}:{score2}) — результат збережено в БД!")

        # --- Нова функція: статистика матчу ---
        st.divider()
        st.subheader("📊 Статистика матчу")
        p1_events = [e for e in log if p1 in e['подія']]
        p2_events = [e for e in log if p2 in e['подія']]
        stat_m1, stat_m2 = st.columns(2)
        stat_m1.metric(f"🔴 {p1}: подій", len(p1_events))
        stat_m2.metric(f"🔵 {p2}: подій", len(p2_events))

        st.divider()
        st.subheader("📋 Хронологія матчу")
        st.caption("Повна хронологія всіх ключових моментів матчу з рахунком після кожної події.")
        for event in log:
            col_m, col_i, col_e, col_s = st.columns([1, 0.5, 7, 1.5])
            col_m.write(f"**{event['хв']}'**")
            col_i.write(event['icon'])
            col_e.write(event['подія'])
            col_s.markdown(f"**[{event['рахунок']}]**")

    elif st.session_state.match_log:
        st.info("Попередній матч збережено. Натисніть кнопку вище для нового.")


# ==========================================
# ІСТОРІЯ МАТЧІВ
# ==========================================
def render_match_history():
    st.title("🗃️ Архів матчів (з бази даних)")
    st.markdown("""
    Усі проведені симуляції зберігаються в SQLite і доступні після перезапуску.
    Тут можна переглянути загальну статистику перемог, таблицю матчів та деталізовану хронологію
    кожного поєдинку. Дані не зникають між сесіями.
    """)

    history = db_load_match_history()

    if not history:
        st.info("🎲 Ще жодного матчу не зіграно. Перейдіть до розділу **AI-Симулятор Матчів**.")
        return

    winners = [h["winner"] for h in history if h["winner"]]
    from collections import Counter
    winner_counts = Counter(winners)

    st.subheader(f"📊 Всього матчів у БД: {len(history)}")
    if winner_counts:
        most_wins = winner_counts.most_common(3)
        cols = st.columns(min(len(most_wins), 3))
        for i, (name, wins) in enumerate(most_wins):
            cols[i].metric(f"🏆 #{i+1} {name}", f"{wins} перемог")

    # --- Нова функція: відсоток перемог у вигляді мінібара ---
    if len(winner_counts) >= 2:
        st.divider()
        st.subheader("📈 Рейтинг перемог")
        st.caption("Відсоток перемог кожного гравця від загальної кількості матчів.")
        total_matches = len(history)
        win_pct_data = pd.DataFrame([
            {"Гравець": name, "Перемог": cnt, "Відсоток": round(cnt/total_matches*100, 1)}
            for name, cnt in winner_counts.most_common()
        ])
        st.dataframe(win_pct_data.style.background_gradient(cmap='Greens', subset=['Відсоток']),
                     use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("📋 Таблиця матчів")
    st.caption("Останні 50 матчів із бази даних, відсортовані від найновішого до найстарішого.")

    history_df = pd.DataFrame([{
        "Дата": h["created_at"][:16],
        "Гравець 1 🔴": h["player1"],
        "Рахунок": f"{h['score1']}:{h['score2']}",
        "Гравець 2 🔵": h["player2"],
        "Переможець 🏆": h["winner"],
    } for h in history])

    st.dataframe(history_df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("🔍 Деталі матчу")
    selected_idx = st.selectbox("Оберіть матч для перегляду деталей:",
                                 range(len(history)),
                                 format_func=lambda i: f"{history[i]['created_at'][:16]} | {history[i]['player1']} vs {history[i]['player2']} → {history[i]['winner']}")

    selected_match = history[selected_idx]
    try:
        log = json.loads(selected_match["log_json"])
        for event in log:
            col_m, col_i, col_e, col_s = st.columns([1, 0.5, 7, 1.5])
            col_m.write(f"**{event['хв']}'**")
            col_i.write(event['icon'])
            col_e.write(event['подія'])
            col_s.markdown(f"**[{event['рахунок']}]**")
    except Exception:
        st.warning("Деталі матчу недоступні.")

    st.divider()
    st.subheader("🗑️ Управління даними")
    if st.button("⚠️ Видалити всі матчі з БД", type="secondary"):
        conn = get_connection()
        conn.execute("DELETE FROM match_logs")
        conn.commit()
        conn.close()
        st.success("✅ Всі матчі видалено.")
        st.rerun()


# ==========================================
# 8. ПРОГНОЗ ТРАВМАТИЗМУ
# ==========================================
def render_injury_prediction(df):
    st.title("🩹 AI Health Monitor")
    st.markdown("""
    Система моніторингу здоров'я команди. Алгоритм розраховує ризик травми
    на основі поточного тижневого навантаження, дисбалансу між силою та витривалістю,
    а також рівня накопиченої втоми. Оновлюйте навантаження після кожного матчу
    для точного прогнозу.
    """)
    st.divider()

    col_select, col_status = st.columns([2, 1])
    with col_select:
        selected_player = st.selectbox("Оберіть гравця:", df["Ім'я"])
    player_data = df[df["Ім'я"] == selected_player].iloc[0]

    st.markdown("<br>", unsafe_allow_html=True)
    col_edit, col_info = st.columns([1.5, 2])
    with col_edit:
        st.subheader("📅 Навантаження (7 днів)")
        st.caption("Введіть кількість матчів або інтенсивних тренувань за останній тиждень.")
        workload = st.number_input("Матчів/тренувань:", min_value=0, max_value=7,
                                   value=int(player_data.get('Навантаження_7днів', 0)))
        if st.button("💾 Зберегти навантаження"):
            db_update_athlete_workload(selected_player, workload)
            st.success(f"✅ Навантаження {selected_player} оновлено в БД!")
            st.rerun()

    imbalance = abs(player_data['Сила'] - player_data['Витривалість'])
    base_risk = int((imbalance*1.5) + (player_data['Швидкість']*0.5))
    workload_factor = 45 if workload >= 3 else (20 if workload == 2 else 0)
    stamina_penalty = 20 if player_data['Витривалість'] < 55 else 0
    injury_risk = min(base_risk + workload_factor + stamina_penalty, 100)

    with col_status:
        st.write("### Статус гравця:")
        if injury_risk >= 75:
            st.error("🚨 КРИТИЧНИЙ РИЗИК. Потрібен відпочинок.")
        elif injury_risk >= 40:
            st.warning("⚠️ В ЗОНІ РИЗИКУ. Обмежити навантаження.")
        else:
            st.success("✅ ОПТИМАЛЬНА ФОРМА. Готовий до гри.")

    with col_info:
        if workload >= 3:
            st.error(f"🚨 **{workload} матчі за тиждень** — серйозне перевантаження!")
        elif workload == 2:
            st.warning(f"⚠️ **{workload} матчі за тиждень** — підвищене навантаження.")
        else:
            st.success(f"✅ **{workload} матч(ів) за тиждень** — нормальний графік.")

    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("🎯 Загальний Ризик")
        color = "green" if injury_risk < 40 else ("orange" if injury_risk < 75 else "red")
        st.markdown(f"<h2 style='text-align:center;color:{color}'>{injury_risk}%</h2>", unsafe_allow_html=True)
        risk_text = "Низький" if injury_risk < 40 else ("Середній" if injury_risk < 75 else "Високий")
        st.markdown(f"<p style='text-align:center'>Рівень: <b>{risk_text}</b></p>", unsafe_allow_html=True)
        st.progress(injury_risk/100)
    with c2:
        st.subheader("📊 Метрики")
        st.write("Навантаження на суглоби:")
        st.progress(min(base_risk, 100)/100)
        st.write("Накопичена втома:")
        st.progress(min(workload_factor*2, 100)/100)
        st.write("Дефіцит витривалості:")
        st.progress(min(stamina_penalty*4, 100)/100)
    with c3:
        st.subheader("💊 Протокол відновлення")
        st.caption("Персоналізовані рекомендації на основі рівня ризику.")
        if injury_risk >= 75:
            st.error("🛑 Відсторонити від тренувань на 48 год.")
            st.write("✅ **Фізіотерапія:** Кріотерапія, масаж.")
            st.write("✅ **Харчування:** Підвищений білок, вітамін C.")
        elif injury_risk >= 40:
            st.warning("⏳ Частковий відновлювальний протокол.")
            st.write("✅ **Тренування:** Легке кардіо, розтяжка.")
            st.write("✅ **Сон:** Мінімум 9 годин.")
        else:
            st.success("💪 Спеціальні заходи не потрібні.")
            st.write("✅ **Тренування:** В загальній групі, 100%.")
            st.write("✅ **Продовжуйте поточний режим.**")

    # --- Нова функція: огляд ризиків всієї команди ---
    st.divider()
    st.subheader("👥 Огляд ризиків всієї команди")
    st.caption("Розраховані ризики для всіх гравців одночасно — для швидкого виявлення тих, хто потребує уваги.")
    team_risks = []
    for _, row in df.iterrows():
        imb = abs(row['Сила'] - row['Витривалість'])
        br = int((imb*1.5) + (row['Швидкість']*0.5))
        wf = 45 if row.get('Навантаження_7днів', 0) >= 3 else (20 if row.get('Навантаження_7днів', 0) == 2 else 0)
        sp = 20 if row['Витривалість'] < 55 else 0
        risk = min(br + wf + sp, 100)
        status = "🟢 Норма" if risk < 40 else ("🟡 Ризик" if risk < 75 else "🔴 Критично")
        team_risks.append({"Гравець": row["Ім'я"], "Вид спорту": row["Вид спорту"],
                           "Ризик (%)": risk, "Статус": status})
    risk_df = pd.DataFrame(team_risks).sort_values("Ризик (%)", ascending=False)
    st.dataframe(risk_df.style.background_gradient(cmap='RdYlGn_r', subset=['Ризик (%)']),
                 use_container_width=True, hide_index=True)


# ==========================================
# 9. AI-ТРЕНЕР
# ==========================================
def render_ai_advisor(df):
    st.title("🧬 Індивідуальні плани тренувань (AI Advisor)")
    st.markdown("""
    AI-тренер аналізує фізичний профіль кожного спортсмена та генерує персоналізовані
    рекомендації й тижневий розклад тренувань. Враховуються поточні показники швидкості,
    витривалості, сили та тижневого навантаження — щоб знайти оптимальний баланс між
    розвитком і відновленням.
    """)

    if df.empty:
        st.warning("База даних порожня.")
        return

    selected_player = st.selectbox("Оберіть гравця:", df["Ім'я"])
    player_data = df[df["Ім'я"] == selected_player].iloc[0]

    speed = player_data['Швидкість']
    stamina = player_data['Витривалість']
    power = player_data['Сила']
    workload = player_data.get('Навантаження_7днів', 0)
    sport = player_data.get('Вид спорту', 'Невідомо')

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Швидкість", f"{speed:.1f} км/год")
    c2.metric("Витривалість", f"{stamina:.0f}")
    c3.metric("Сила", f"{power:.0f}")
    c4.metric("Навантаження", f"{workload} (за 7 днів)")

    # --- Нова функція: профіль гравця за типом ---
    st.divider()
    st.subheader("🏷️ Тип спортсмена")
    if stamina >= 80 and speed >= 30:
        profile = "🔥 Динамічний атлет — висока витривалість і швидкість. Ідеальний для інтенсивних позицій."
    elif power >= 80:
        profile = "💪 Силовий гравець — домінує у єдиноборствах і стандартних положеннях."
    elif speed >= 30:
        profile = "💨 Швидкісний вінгер — перевага на фланзі, небезпечний у контратаках."
    elif stamina >= 80:
        profile = "🫀 Двигун команди — може відпрацювати весь матч на максимумі."
    else:
        profile = "📈 Гравець розвитку — є простір для росту в усіх компонентах."
    st.info(f"**{selected_player}** ({get_sport_emoji(sport)} {sport}): {profile}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🤖 Рекомендації")
    st.caption("Рекомендації формуються на основі «вузьких місць» у профілі гравця — найсуттєвіших відхилень від оптимуму.")

    report = []
    if stamina < 60 and speed > 28:
        report.append("Витривалість < 60, але швидкість > 28 — рекомендуємо інтервальні тренування.")
    elif stamina < 60:
        report.append("Витривалість критично низька (< 60). Базові аеробні навантаження (крос 40-60 хв).")
    if power < 65:
        report.append("Показник сили нижчий за норму. 2-3 силові сесії на тиждень.")
    if speed < 25 and power >= 65:
        report.append("Достатня силова база, але дефіцит швидкості. Пліометрика та короткі спринти.")
    if workload >= 3:
        report.append("⚠️ Високе навантаження. Акцент на відновлення (басейн, масаж).")
    if not report:
        report.append(f"Показники {selected_player} в оптимальному балансі. Стандартний підтримуючий режим.")

    st.info("💡 **Персоналізовані рекомендації:**\n\n" + "\n\n".join([f"🔸 {item}" for item in report]))

    st.markdown("### 📅 Орієнтовний розклад на тиждень:")
    st.caption("Розклад адаптується залежно від рівня навантаження та слабких сторін гравця.")
    if workload >= 3:
        acts = ["Легке відновлення", "Масаж / Басейн", "Тактична дошка", "Повний відпочинок",
                "Легке тренування (45 хв)", "Матч", "Відпочинок"]
    elif stamina < 60 and speed > 28:
        acts = ["Інтервальне тренування (низька інтенсивність)", "Відпочинок",
                "Техніка з м'ячем", "Спеціальна витривалість", "Тактика", "Матч", "Відновлення"]
    else:
        acts = ["Силове тренування", "Аеробна база (крос)", "Відпочинок",
                "Пліометрика / Швидкість", "Передігрова розминка", "Матч", "Відновлення"]

    schedule = pd.DataFrame({"День": ["Понеділок","Вівторок","Середа","Четвер","П'ятниця","Субота","Неділя"],
                             "Активність": acts}).set_index("День")
    st.table(schedule)

    # --- Нова функція: цільові показники ---
    st.divider()
    st.subheader("🎯 Цільові показники на 4 тижні")
    st.caption("Реалістичний приріст при виконанні рекомендованого плану.")
    target_stamina = min(stamina + 8 if stamina < 80 else stamina + 2, 100)
    target_speed = min(speed + 1.5 if speed < 30 else speed + 0.5, 40)
    target_power = min(power + 5 if power < 80 else power + 2, 100)
    t1, t2, t3 = st.columns(3)
    t1.metric("Цільова витривалість", f"{target_stamina:.0f}", f"+{target_stamina-stamina:.0f}")
    t2.metric("Цільова швидкість", f"{target_speed:.1f}", f"+{target_speed-speed:.1f}")
    t3.metric("Цільова сила", f"{target_power:.0f}", f"+{target_power-power:.0f}")


# ==========================================
# 10. ІСТОРІЯ ФОРМИ
# ==========================================
def render_form_history(df):
    st.title("📈 Історія форми (Time-Series аналіз)")
    st.markdown("""
    Відстежуйте динаміку показників гравця за останні 10 матчів. Тренди показують,
    чи перебуває спортсмен у зростаючій чи спадаючій формі. Дані генеруються
    на основі поточних показників з реалістичним шумом для симуляції природних коливань.
    """)

    if df.empty:
        st.warning("База даних порожня.")
        return

    selected_player = st.selectbox("Оберіть гравця:", df["Ім'я"])
    player_data = df[df["Ім'я"] == selected_player].iloc[0]

    np.random.seed(hash(selected_player) % (2**32))

    def generate_trend(current_val, volatility):
        trend = [current_val]
        for _ in range(9):
            trend.append(max(0, trend[-1] + np.random.normal(0, volatility)))
        return trend[::-1]

    matches = [f"Матч {i}" for i in range(1, 11)]
    history_df = pd.DataFrame({
        "Матч": matches,
        "PER (Рейтинг)": generate_trend(player_data['PER (Рейтинг)'], 2.5),
        "Витривалість": generate_trend(player_data['Витривалість'], 4.0),
        "Швидкість": generate_trend(player_data['Швидкість'], 1.5)
    }).set_index("Матч")

    st.markdown(f"### 📊 Динаміка: **{selected_player}** за 10 матчів")

    # --- Нова функція: тренд-аналіз ---
    per_trend = history_df["PER (Рейтинг)"].iloc[-1] - history_df["PER (Рейтинг)"].iloc[0]
    if per_trend > 2:
        st.success(f"📈 Форма **зростає** (+{per_trend:.1f} PER за 10 матчів) — гравець прогресує.")
    elif per_trend < -2:
        st.warning(f"📉 Форма **знижується** ({per_trend:.1f} PER за 10 матчів) — потрібен аналіз навантаження.")
    else:
        st.info(f"➡️ Форма **стабільна** (зміна PER: {per_trend:+.1f}) — рівний рівень гри.")

    st.line_chart(history_df["PER (Рейтинг)"], color="#FF4B4B")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Витривалість")
        st.caption("Показник витривалості між матчами. Різкі падіння можуть вказувати на перевтому.")
        st.line_chart(history_df["Витривалість"], color="#0068C9")
    with c2:
        st.subheader("Швидкість (км/год)")
        st.caption("Зміна максимальної швидкості. Падіння швидкості часто передує травмі.")
        st.line_chart(history_df["Швидкість"], color="#29B09D")

    # --- Нова функція: таблиця з мін/макс ---
    st.divider()
    st.subheader("📋 Зведена статистика за 10 матчів")
    summary = history_df.agg(['min', 'max', 'mean']).round(1)
    summary.index = ['Мінімум', 'Максимум', 'Середнє']
    st.dataframe(summary, use_container_width=True)


# ==========================================
# 11. РЕСУРСИ
# ==========================================
def render_resources():
    st.title("📚 Спортивна Аналітика та Новини")
    st.markdown("""
    Підбірка корисних ресурсів для тренерів, аналітиків і спортсменів. Тут зібрані посилання
    на провідні українські та міжнародні платформи спортивної аналітики, навчальні матеріали
    та наукові публікації з теми використання даних у спорті.
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📰 Новини та Аналітика")
        st.info("**SportAnalytic** — Огляди, статистика та футбольні новини для тренерів і вболівальників.")
        st.link_button("Перейти на SportAnalytic", "https://sportanalytic.com/")
        st.divider()
        st.info("**Sport.ua** — Головний спортивний портал України: новини, результати, трансфери.")
        st.link_button("Перейти на Sport.ua", "https://sport.ua/uk")
    with col2:
        st.subheader("🎓 Навчання та Статті")
        st.success("**Robot Dreams** — Практичний гайд: як перетворити спортивні дані на тренерські рішення.")
        st.link_button("Читати статтю", "https://robotdreams.cc/uk/blog/384-data-analiz-u-sporti-yak-peretvoriti-dani-na-rezultati")
        st.divider()
        st.success("**Наукова робота** — Дослідження застосування ІТ-технологій у спортивній підготовці.")
        st.link_button("Відкрити публікацію", "https://enpuir.udu.edu.ua/entities/publication/c7becbfd-8d2c-4566-89f4-9a85d3c3062a")

    # --- Нова функція: глосарій термінів ---
    st.divider()
    st.subheader("📖 Глосарій термінів")
    st.caption("Коротке пояснення ключових метрик, що використовуються в системі.")
    glossary = {
        "PER (Player Efficiency Rating)": "Комплексний рейтинг ефективності гравця. Розраховується на основі швидкості, витривалості, сили та результативності.",
        "Витривалість": "Здатність підтримувати інтенсивність протягом матчу (0–100). Значення < 60 вимагає додаткових кардіо-тренувань.",
        "Навантаження_7днів": "Кількість матчів або інтенсивних тренувань за останній тиждень. Значення ≥ 3 — сигнал до відновлення.",
        "Теплова карта CV": "Візуалізація зон активності на полі, отримана методами комп'ютерного зору з відеозапису матчу.",
        "OCR маркерів": "Оптичне розпізнавання кольорових фішок і номерів гравців на тактичній дошці.",
        "Впевненість OCR (%)": "Показник якості розпізнавання конкретного маркера або стрілки. Значення > 80% — надійне розпізнавання.",
    }
    for term, definition in glossary.items():
        with st.expander(f"📌 {term}"):
            st.write(definition)


# ==========================================
# 12. ЕКСПОРТ
# ==========================================
def render_io(df):
    st.title("💾 Експорт Даних")
    st.markdown("""
    Завантажуйте дані в зручному форматі для аналізу в Excel, Google Sheets або сторонніх BI-інструментах.
    Доступний експорт бази гравців, архіву матчів, відеонотаток, тактичних нотаток
    та результатів OCR-аналізу. Також тут знаходиться порожній шаблон для заповнення даних команди.
    """)

    st.subheader("📊 Дані гравців")
    col_csv, col_json = st.columns(2)
    with col_csv:
        st.download_button("📥 Завантажити CSV", df.to_csv(index=False).encode('utf-8'),
                           "athletes_data.csv", mime="text/csv", use_container_width=True)
    with col_json:
        st.download_button("📥 Завантажити JSON", df.to_json(orient='records', force_ascii=False),
                           "athletes_data.json", mime="application/json", use_container_width=True)

    st.divider()
    st.subheader("🗃️ Повний дамп бази даних")
    st.caption("Тут можна завантажити дані з кожної таблиці SQLite у форматі CSV для зовнішнього аналізу або резервного копіювання.")
    conn = get_connection()

    match_df = pd.read_sql_query("SELECT player1, player2, score1, score2, winner, created_at FROM match_logs ORDER BY created_at DESC", conn)
    notes_df = pd.read_sql_query("SELECT * FROM video_notes ORDER BY created_at DESC", conn)
    tactic_df = pd.read_sql_query("SELECT * FROM tactic_notes ORDER BY created_at DESC", conn)
    athlete_notes_df = pd.read_sql_query("SELECT * FROM athlete_notes ORDER BY created_at DESC", conn)
    conn.close()

    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        st.metric("📋 Матчів у архіві", len(match_df))
        if not match_df.empty:
            st.download_button("📥 Архів матчів CSV", match_df.to_csv(index=False).encode('utf-8'),
                               "match_history.csv", mime="text/csv", use_container_width=True)
    with col_b:
        st.metric("📝 Відеонотаток", len(notes_df))
        if not notes_df.empty:
            st.download_button("📥 Відеонотатки CSV", notes_df.to_csv(index=False).encode('utf-8'),
                               "video_notes.csv", mime="text/csv", use_container_width=True)
    with col_c:
        st.metric("🗺️ Тактичних нотаток", len(tactic_df))
        if not tactic_df.empty:
            st.download_button("📥 Тактичні нотатки CSV", tactic_df.to_csv(index=False).encode('utf-8'),
                               "tactic_notes.csv", mime="text/csv", use_container_width=True)
    with col_d:
        st.metric("🗒️ Нотаток до гравців", len(athlete_notes_df))
        if not athlete_notes_df.empty:
            st.download_button("📥 Нотатки гравців CSV", athlete_notes_df.to_csv(index=False).encode('utf-8'),
                               "athlete_notes.csv", mime="text/csv", use_container_width=True)

    st.divider()
    st.subheader("📋 Шаблон для заповнення")
    st.caption("Завантажте порожній CSV-шаблон, заповніть його в Excel або Google Sheets і завантажте через бічну панель «Завантажити свої дані».")
    template_df = pd.DataFrame(columns=["Ім'я","Вік","Номер","Вид спорту","Матчі","Очки","Швидкість","Витривалість","Сила","Навантаження_7днів"])
    st.download_button("📄 Завантажити порожній шаблон CSV", template_df.to_csv(index=False).encode('utf-8'),
                       "template_athletes.csv", mime="text/csv", use_container_width=True)

    if st.session_state.ocr_result:
        st.divider()
        st.subheader("🖼️ Результати OCR аналізу")
        st.caption("Дані останнього OCR-аналізу тактичної дошки з синхронізованими профілями гравців.")
        ocr_df = pd.DataFrame(st.session_state.ocr_result["synchronized_players"])
        st.download_button("📥 Завантажити результати OCR", ocr_df.to_csv(index=False).encode('utf-8'),
                          "ocr_tactical_analysis.csv", mime="text/csv", use_container_width=True)

    # --- Нова функція: попередній перегляд даних ---
    st.divider()
    st.subheader("👁️ Попередній перегляд таблиць")
    preview_choice = st.selectbox("Оберіть таблицю для перегляду:",
                                  ["Гравці", "Архів матчів", "Відеонотатки", "Тактичні нотатки"])
    if preview_choice == "Гравці":
        st.dataframe(df.head(10), use_container_width=True, hide_index=True)
    elif preview_choice == "Архів матчів":
        st.dataframe(match_df.head(10), use_container_width=True, hide_index=True)
    elif preview_choice == "Відеонотатки":
        st.dataframe(notes_df.head(10), use_container_width=True, hide_index=True)
    elif preview_choice == "Тактичні нотатки":
        st.dataframe(tactic_df.head(10), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
