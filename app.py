import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
import time
import random
import io
import tempfile
import os

# ==========================================
# 0. КОНФІГУРАЦІЯ ТА ДАНІ
# ==========================================

st.set_page_config(page_title="OmniSport Pro", layout="wide", initial_sidebar_state="expanded")

DEFAULT_DATA = pd.DataFrame({
    "Ім'я": ["Олександр", "Марія", "Іван", "Анна"],
    "Вік": [24, 21, 26, 23],
    "Вид спорту": ["Футбол", "Волейбол", "Біг", "Теніс"],
    "Матчі": [12, 15, 8, 20],
    "Очки": [5, 45, 0, 80],
    "Швидкість": [28.5, 22.0, 32.1, 25.0],
    "Витривалість": [85, 70, 95, 40],
    "Сила": [75, 85, 60, 70],
    "Навантаження_7днів": [2, 3, 1, 4]
})

if 'athletes_db' not in st.session_state:
    st.session_state.athletes_db = DEFAULT_DATA.copy()
else:
    if 'Вік' not in st.session_state.athletes_db.columns:
        st.session_state.athletes_db['Вік'] = 20

if 'tactic_points' not in st.session_state:
    st.session_state.tactic_points = []

if 'match_log' not in st.session_state:
    st.session_state.match_log = []

if 'video_notes' not in st.session_state:
    st.session_state.video_notes = ""

if 'tactical_photos' not in st.session_state:
    st.session_state.tactical_photos = []

# Стан CV аналізу
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

def calculate_per(row):
    base = (row['Швидкість'] * 1.5) + (row['Витривалість'] * 0.8) + (row['Сила'] * 0.9)
    bonus = row['Очки'] * 2 if row['Матчі'] > 0 else 0
    return round((base + bonus) / 3, 1)


# ==========================================
# ГОЛОВНА ЛОГІКА
# ==========================================

def main():
    st.session_state.athletes_db['PER (Рейтинг)'] = st.session_state.athletes_db.apply(calculate_per, axis=1)

    with st.sidebar:
        st.title("🏆 OmniSport Pro")
        st.caption("Performance Analytics v10.0")
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
                        if 'Навантаження_7днів' not in df_upload.columns:
                            df_upload['Навантаження_7днів'] = 0
                        if 'Вік' not in df_upload.columns:
                            df_upload['Вік'] = 20

                        st.session_state.athletes_db = df_upload
                        st.success(f"✅ Завантажено {len(df_upload)} гравців!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Помилка читання файлу: {e}")

            if st.button("🔄 Повернути демо-дані", use_container_width=True):
                st.session_state.athletes_db = DEFAULT_DATA.copy()
                st.rerun()

        st.divider()
        menu = [
            "🏠 Дашборд",
            "📊 Командна аналітика",
            "👥 База гравців",
            "⚔️ H2H Батл (Скаутинг)",
            "🗺️ Тактична дошка",
            "📹 Інтеграція з медіа",
            "🎥 CV Аналіз відео",           # НОВИЙ РОЗДІЛ
            "⚛️ Лабораторія Фізики",
            "🎲 AI-Симулятор Матчів",
            "🩹 Прогноз Травматизму",
            "🧬 AI-Тренер (Плани тренувань)",
            "📈 Історія форми",
            "📚 Ресурси та Освіта",
            "💾 Експорт Даних"
        ]
        choice = st.radio("Навігація", menu)
        st.divider()

        st.subheader("🔗 Корисні посилання")
        st.info("[SportAnalytic](https://sportanalytic.com/)")
        st.info("[Sport.ua](https://sport.ua/uk)")

        st.divider()
        st.info(f"Активних гравців: **{len(st.session_state.athletes_db)}**")

    if choice == "🏠 Дашборд": render_dashboard()
    elif choice == "📊 Командна аналітика": render_team_analytics()
    elif choice == "👥 База гравців": render_crm()
    elif choice == "⚔️ H2H Батл (Скаутинг)": render_scouting()
    elif choice == "🗺️ Тактична дошка": render_tactics()
    elif choice == "📹 Інтеграція з медіа": render_media_integration()
    elif choice == "🎥 CV Аналіз відео": render_cv_analysis()   # НОВИЙ
    elif choice == "⚛️ Лабораторія Фізики": render_physics()
    elif choice == "🎲 AI-Симулятор Матчів": render_simulator()
    elif choice == "🩹 Прогноз Травматизму": render_injury_prediction()
    elif choice == "🧬 AI-Тренер (Плани тренувань)": render_ai_advisor()
    elif choice == "📈 Історія форми": render_form_history()
    elif choice == "📚 Ресурси та Освіта": render_resources()
    elif choice == "💾 Експорт Даних": render_io()


# ==========================================
# 1. ДАШБОРД
# ==========================================
def render_dashboard():
    st.title("🏠 Аналітична панель")

    with st.expander("👋 Вітаємо в командному центрі OmniSport Pro!", expanded=True):
        st.markdown("""
        Цей розділ створений для швидкого моніторингу ключових показників вашої команди:
        * **Оцінити загальний стан:** кількість активних гравців у ростері.
        * **Визначити рекорди:** максимальні показники швидкості та витривалості.
        * **Виявити лідерів:** зведена таблиця на основі комплексного рейтингу **PER**.
        """)
        st.info("💡 **Порада:** Використовуйте бічне меню ліворуч для глибшої аналітики, порівняння гравців (H2H) або налаштування тактики.")

    st.markdown("<br>", unsafe_allow_html=True)

    df = st.session_state.athletes_db

    st.subheader("⚡ Ключові показники")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("👥 Всього спортсменів", len(df))
    with c2:
        st.metric("🚀 Макс. швидкість", f"{df['Швидкість'].max():.1f} км/год")
    with c3:
        st.metric("🫀 Топ Витривалість", int(df['Витривалість'].max()))
    with c4:
        st.metric("👑 Топ Рейтинг (PER)", f"{df['PER (Рейтинг)'].max():.1f}")

    st.divider()

    st.subheader("📊 Загальний рейтинг команди")
    st.caption("🏆 Гравці відсортовані за рейтингом ефективності. Чим насиченіший синій колір — тим вищий показник.")

    formatted_df = df.sort_values(by="PER (Рейтинг)", ascending=False).copy()

    styled_df = formatted_df.style.background_gradient(
        cmap='Blues', subset=['PER (Рейтинг)']
    ).format({
        'Швидкість': '{:.1f}',
        'Витривалість': '{:.0f}',
        'Сила': '{:.0f}',
        'PER (Рейтинг)': '{:.1f}'
    })

    st.dataframe(styled_df, use_container_width=True, hide_index=True)


# ==========================================
# 1.5 КОМАНДНА АНАЛІТИКА
# ==========================================
def render_team_analytics():
    st.title("📊 Командна аналітика (Team View)")
    df = st.session_state.athletes_db

    if df.empty:
        st.warning("Немає даних для аналізу.")
        return

    c1, c2, c3 = st.columns(3)

    if 'Вік' in df.columns:
        avg_age = df['Вік'].mean()
        c1.metric("Середній вік команди", f"{avg_age:.1f} років")
    else:
        c1.metric("Середній вік команди", "Дані відсутні")

    if 'Швидкість' in df.columns:
        avg_speed = df['Швидкість'].mean()
        ideal_speed = 30.0
        delta_speed = round(avg_speed - ideal_speed, 1)
        c2.metric("Середня швидкість", f"{avg_speed:.1f} км/год", f"{delta_speed} км/год від ідеалу (30)")
    else:
        c2.metric("Середня швидкість", "Дані відсутні")

    if 'PER (Рейтинг)' in df.columns:
        avg_per = df['PER (Рейтинг)'].mean()
        c3.metric("Середній командний PER", f"{avg_per:.1f}")

    st.divider()

    col_pie, col_bar = st.columns(2)

    with col_pie:
        st.subheader("Розподіл за видами спорту")
        if 'Вид спорту' in df.columns:
            sport_counts = df['Вид спорту'].value_counts()
            fig1, ax1 = plt.subplots(figsize=(6, 4))
            wedges, texts, autotexts = ax1.pie(
                sport_counts,
                labels=sport_counts.index,
                autopct='%1.1f%%',
                startangle=90,
                colors=plt.cm.Pastel1.colors,
                textprops=dict(color="w")
            )
            for text in texts:
                text.set_color('white')
            ax1.axis('equal')
            fig1.patch.set_alpha(0.0)
            st.pyplot(fig1)

    with col_bar:
        st.subheader("Поточні показники vs Ідеал")
        if all(col in df.columns for col in ['Витривалість', 'Сила', 'Швидкість']):
            avg_stats = pd.DataFrame({
                "Показник": ["Витривалість", "Сила", "Швидкість"],
                "Команда": [df['Витривалість'].mean(), df['Сила'].mean(), df['Швидкість'].mean()],
                "Ідеал": [85.0, 80.0, 30.0]
            }).set_index("Показник")
            st.bar_chart(avg_stats, color=["#448AFF", "#FF5252"])


# ==========================================
# 2. БАЗА ГРАВЦІВ (CRM)
# ==========================================
def render_crm():
    st.title("👥 Управління складом")
    st.markdown("Тут ви можете переглядати всю базу спортсменів, шукати конкретних гравців та додавати нових талантів до вашої команди.")

    df = st.session_state.athletes_db

    st.subheader("🔍 Пошук та фільтри")
    col_search, col_filter = st.columns(2)
    with col_search:
        search_query = st.text_input("Пошук за ім'ям", placeholder="Введіть ім'я гравця...")
    with col_filter:
        sport_options = ["Всі види"] + list(df['Вид спорту'].dropna().unique())
        selected_sport = st.selectbox("Фільтр за видом спорту", sport_options)

    filtered_df = df.copy()
    if search_query:
        filtered_df = filtered_df[filtered_df["Ім'я"].str.contains(search_query, case=False, na=False)]
    if selected_sport != "Всі види":
        filtered_df = filtered_df[filtered_df['Вид спорту'] == selected_sport]

    st.divider()

    with st.expander("➕ Додати нового спортсмена", expanded=False):
        with st.form("add_form"):
            c1, c_age, c2 = st.columns([2, 1, 2])
            name = c1.text_input("Ім'я")
            age = c_age.number_input("Вік", min_value=14, max_value=60, value=20)
            sport = c2.selectbox("Вид спорту", ["Волейбол", "Футбол", "Біг", "Теніс", "Баскетбол", "Бокс"])

            c3, c4, c5, c6, c7, c8 = st.columns(6)
            matches = c3.number_input("Матчі", min_value=0)
            score = c4.number_input("Очки", min_value=0)
            speed = c5.number_input("Швидк. (км/год)", 0.0, 50.0, 20.0)
            stamina = c6.number_input("Витривал.", 0, 100, 50)
            power = c7.number_input("Сила", 0, 100, 50)
            workload = c8.number_input("Матчів/тиж.", 0, 7, 0)

            if st.form_submit_button("Зберегти гравця", type="primary"):
                if name.strip() == "":
                    st.error("⚠️ Будь ласка, введіть ім'я спортсмена.")
                else:
                    new_row = pd.DataFrame({
                        "Ім'я": [name], "Вік": [age], "Вид спорту": [sport], "Матчі": [matches],
                        "Очки": [score], "Швидкість": [speed], "Витривалість": [stamina],
                        "Сила": [power], "Навантаження_7днів": [workload]
                    })
                    st.session_state.athletes_db = pd.concat([st.session_state.athletes_db, new_row], ignore_index=True)
                    st.success(f"✅ Спортсмена {name} успішно додано!")
                    st.rerun()

    st.subheader(f"📋 Список гравців (Знайдено: {len(filtered_df)})")
    st.caption("💡 **Підказка:** Ви можете сортувати колонки, натискаючи на їхні назви.")

    styled_df = filtered_df.style.format({
        'Швидкість': '{:.1f}',
        'Витривалість': '{:.0f}',
        'Сила': '{:.0f}',
        'PER (Рейтинг)': '{:.1f}'
    })

    st.dataframe(styled_df, use_container_width=True, hide_index=True, height=400)


# ==========================================
# 3. H2H СКАУТИНГ
# ==========================================
def render_scouting():
    st.title("⚔️ Head-to-Head: Порівняння гравців")
    df = st.session_state.athletes_db

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
                player['Витривалість'],
                player['Сила'],
                min(int((player['Швидкість'] / 40) * 100), 100),
                min(player['Очки'] * 5, 100),
                min(player['Матчі'] * 5, 100)
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

    with col_text:
        st.subheader("📈 Аналіз")
        age1 = p1_data.get('Вік', 'N/A')
        age2 = p2_data.get('Вік', 'N/A')

        st.info(f"**{p1_name} ({age1} р.)**: " + ("Лідер швидкості" if p1_data['Швидкість'] > 28 else "Витривалий боєць"))
        if p1_name != p2_name:
            st.info(f"**{p2_name} ({age2} р.)**: " + ("Лідер швидкості" if p2_data['Швидкість'] > 28 else "Витривалий боєць"))


# ==========================================
# 4. ТАКТИЧНА ДОШКА
# ==========================================
def render_tactics():
    st.title("🗺️ Інтерактивна Тактична Дошка")
    df = st.session_state.athletes_db
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
        else:
            selected_tactic = None
            st.info("Введіть координати, щоб додати точки активності.")
            cx = st.slider("X координата (0-100)", 0, 100, 50)
            cy = st.slider("Y координата (0-60)", 0, 60, 30)
            if st.button("📍 Додати точку"):
                st.session_state.tactic_points.append((cx, cy))
                st.success(f"Точку ({cx}, {cy}) додано!")
            if st.button("🗑️ Очистити всі точки"):
                st.session_state.tactic_points = []
                st.rerun()
            st.caption(f"Точок на полі: **{len(st.session_state.tactic_points)}**")

        st.divider()
        st.subheader("🏋️ AI-поради")
        if player_data['Витривалість'] < 60:
            st.error("⚠️ Потрібне кардіо-навантаження!")
        else:
            st.success("✅ Форма стабільна.")
        if player_data['Швидкість'] > 30:
            st.info("💨 Гравець — лідер швидкості. Рекомендовано флангові рухи.")
        if player_data['Сила'] > 80:
            st.info("💪 Висока сила — ефективний у єдиноборствах.")

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
        penalty_left = patches.Rectangle((2, 15), 16.5, 30, linewidth=1.5, edgecolor='white', facecolor='none')
        penalty_right = patches.Rectangle((81.5, 15), 16.5, 30, linewidth=1.5, edgecolor='white', facecolor='none')
        ax.add_patch(penalty_left)
        ax.add_patch(penalty_right)
        goal_left = patches.Rectangle((0, 24), 2, 12, linewidth=1.5, edgecolor='white', facecolor='#333333')
        goal_right = patches.Rectangle((98, 24), 2, 12, linewidth=1.5, edgecolor='white', facecolor='#333333')
        ax.add_patch(goal_left)
        ax.add_patch(goal_right)

        def get_preset_points(tactic, spread):
            presets = {
                "4-3-3 (Атака)": [(5, 30), (20, 12), (20, 22), (20, 38), (20, 48), (42, 18), (45, 30), (42, 42), (72, 12), (75, 30), (72, 48)],
                "4-4-2 (Баланс)": [(5, 30), (20, 12), (20, 24), (20, 36), (20, 48), (45, 12), (45, 24), (45, 36), (45, 48), (70, 22), (70, 38)],
                "5-3-2 (Захист)": [(5, 30), (18, 8), (18, 20), (18, 30), (18, 40), (18, 52), (40, 18), (40, 30), (40, 42), (65, 22), (65, 38)],
                "3-5-2 (Контроль)": [(5, 30), (20, 18), (20, 30), (20, 42), (42, 8), (42, 20), (42, 30), (42, 40), (42, 52), (68, 22), (68, 38)],
            }
            default_pts = [(random.gauss(50, spread), random.gauss(30, 10)) for _ in range(80)]

            if tactic in presets:
                base_pts = presets[tactic]
                pts = []
                for bx, by in base_pts:
                    for _ in range(8):
                        pts.append((np.clip(bx + random.gauss(0, spread / 2), 2, 98), np.clip(by + random.gauss(0, 4), 2, 58)))
                return pts
            return default_pts

        spread = 20 if player_data['Витривалість'] > 75 else 10

        if mode == "🎯 Пресет тактики":
            heat_points = get_preset_points(selected_tactic, spread)
            xs = [p[0] for p in heat_points]
            ys = [p[1] for p in heat_points]
            hb = ax.hexbin(xs, ys, gridsize=18, cmap='YlOrRd', alpha=0.75, extent=(0, 100, 0, 60))
            plt.colorbar(hb, ax=ax, label='Інтенсивність')
            ax.set_title(f"Тактика: {selected_tactic}", color='white', fontsize=12, pad=8)
        else:
            if len(st.session_state.tactic_points) >= 3:
                xs = [p[0] for p in st.session_state.tactic_points]
                ys = [p[1] for p in st.session_state.tactic_points]
                hb = ax.hexbin(xs, ys, gridsize=12, cmap='plasma', alpha=0.75, extent=(0, 100, 0, 60))
                plt.colorbar(hb, ax=ax, label='Інтенсивність')
            for px, py in st.session_state.tactic_points:
                ax.plot(px, py, 'o', color='cyan', markersize=8, zorder=5, markeredgecolor='white', markeredgewidth=1.5)
            ax.set_title(f"Ручні точки ({len(st.session_state.tactic_points)} шт.)", color='white', fontsize=12, pad=8)

        fig.patch.set_facecolor('#0d3318')
        ax.set_xticks([])
        ax.set_yticks([])
        st.pyplot(fig)


# ==========================================
# 5. ІНТЕГРАЦІЯ З МЕДІА
# ==========================================
def render_media_integration():
    st.title("📹 Інтеграція з медіа")
    st.markdown("Аналізуйте відео матчів та зберігайте фотографії тактичних схем.")

    tab_video, tab_photo = st.tabs(["📹 Аналіз Відео", "📸 Фото схем"])

    with tab_video:
        st.subheader("Відеоаналіз матчів")
        youtube_url = st.text_input("YouTube URL", placeholder="Вставте посилання тут...")

        col_vid, col_notes = st.columns([2, 1])
        with col_vid:
            if youtube_url:
                try:
                    st.video(youtube_url)
                except Exception:
                    st.error("Помилка завантаження відео. Перевірте правильність посилання.")
            else:
                st.info("👈 Введіть посилання на відео у поле вище.")

        with col_notes:
            st.subheader("📝 Нотатки аналітика")
            notes = st.text_area("Ваші спостереження:", value=st.session_state.video_notes, height=280)
            if st.button("💾 Зберегти нотатки", use_container_width=True, type="primary"):
                st.session_state.video_notes = notes
                st.success("Нотатки успішно збережено!")

    with tab_photo:
        st.subheader("Оцифрування тактичних схем")
        photo = st.camera_input("Сфотографувати тактичну схему")

        if photo is not None:
            st.success("✅ Фото успішно зроблено!")
            if st.button("💾 Додати в архів схем", type="primary"):
                st.session_state.tactical_photos.append(photo)
                st.rerun()

        if st.session_state.tactical_photos:
            st.divider()
            st.subheader(f"📂 Архів збережених схем ({len(st.session_state.tactical_photos)})")
            cols = st.columns(3)
            for i, saved_photo in enumerate(st.session_state.tactical_photos):
                with cols[i % 3]:
                    st.image(saved_photo, caption=f"Схема #{i+1}", use_container_width=True)
                    if st.button(f"🗑️ Видалити", key=f"del_photo_{i}", use_container_width=True):
                        st.session_state.tactical_photos.pop(i)
                        st.rerun()
        else:
            st.info("Архів схем наразі порожній.")


# ==========================================
# 5.5 CV АНАЛІЗ ВІДЕО — НОВИЙ РОЗДІЛ
# ==========================================

def simulate_tracking_data_internal(num_players_per_team=5, num_frames=300, fps=25,
                                     field_w=105.0, field_h=68.0):
    """Генерує симульовані дані трекінгу для демонстрації."""
    import math
    teams = {"Червона команда": [], "Синя команда": []}
    ball_positions = []
    events = []

    red_starts = [(15 + i*10, 15 + j*14) for i in range(3) for j in range(2)][:num_players_per_team]
    blue_starts = [(90 - i*10, 15 + j*14) for i in range(3) for j in range(2)][:num_players_per_team]

    red_pos = [list(p) for p in red_starts]
    blue_pos = [list(p) for p in blue_starts]
    ball = [52.5, 34.0]

    for frame in range(num_frames):
        t = frame / fps
        for p in red_pos:
            p[0] += np.clip(random.gauss(0.25, 0.7), -1.5, 2.5)
            p[1] += np.clip(random.gauss(0, 1.0), -2.5, 2.5)
            p[0] = np.clip(p[0], 2, 103)
            p[1] = np.clip(p[1], 2, 66)
        for p in blue_pos:
            p[0] += np.clip(random.gauss(-0.25, 0.7), -2.5, 1.5)
            p[1] += np.clip(random.gauss(0, 1.0), -2.5, 2.5)
            p[0] = np.clip(p[0], 2, 103)
            p[1] = np.clip(p[1], 2, 66)

        ball[0] += math.sin(t * 0.6) * 1.3 + random.gauss(0, 0.4)
        ball[1] += math.cos(t * 0.4) * 0.9 + random.gauss(0, 0.4)
        ball[0] = np.clip(ball[0], 2, 103)
        ball[1] = np.clip(ball[1], 2, 66)

        teams["Червона команда"].append([tuple(p) for p in red_pos])
        teams["Синя команда"].append([tuple(p) for p in blue_pos])
        ball_positions.append(tuple(ball))

        if frame % 60 == 0 and frame > 0:
            events.append({
                "frame": frame,
                "time": round(t, 1),
                "type": random.choice(["УДАР ПО ВОРОТАХ", "ПАС У РОЗРІЗ", "ПЕРЕХОПЛЕННЯ", "КУТОВИЙ"]),
                "team": random.choice(["Червона команда", "Синя команда"]),
                "icon": random.choice(["⚽", "🎯", "🛡️", "🚩"]),
                "confidence": round(random.uniform(0.68, 0.96), 2)
            })

    return teams, ball_positions, events


def generate_heatmap_internal(positions, field_w=105, field_h=68, resolution=40):
    """Генерує теплову карту активності з набору позицій."""
    heatmap = np.zeros((resolution, resolution))
    for pos_frame in positions:
        for (x, y) in (pos_frame if isinstance(pos_frame, list) else [pos_frame]):
            px = int(np.clip((x / field_w) * resolution, 0, resolution-1))
            py = int(np.clip((y / field_h) * resolution, 0, resolution-1))
            sigma = 2.0
            for i in range(max(0, px-4), min(resolution, px+5)):
                for j in range(max(0, py-4), min(resolution, py+5)):
                    dist = np.sqrt((i-px)**2 + (j-py)**2)
                    heatmap[j, i] += np.exp(-dist**2 / (2*sigma**2))
    return heatmap


def render_cv_analysis():
    """Головна функція рендерингу модуля CV аналізу відео."""
    st.title("🎥 Computer Vision: Автоматичний аналіз відео")

    with st.expander("ℹ️ Як працює цей модуль?", expanded=False):
        st.markdown("""
        Цей модуль реалізує **автоматичний комп'ютерний аналіз** відеозаписів матчів:

        | Функція | Технологія | Що робить |
        |---|---|---|
        | **Трекінг гравців** | OpenCV + HSV-маски | Розпізнає гравців за кольором форми, відстежує координати (x, y) кожну секунду |
        | **Виявлення м'яча** | Детектор кіл Хафа | Знаходить м'яч за круглою формою та яскравістю |
        | **Тактичний малюнок** | Геометричний аналіз | Малює трикутники між гравцями, виводить лінію офсайду |
        | **Фізичні показники** | Кінематика | Вираховує реальну швидкість (км/год) та дистанцію (км) |
        | **Теплова карта** | Gaussian density | Показує зони максимальної активності гравців на полі |
        | **Розпізнавання подій** | Патерн-аналіз | Автоматично виявляє удари, передачі, перехоплення |

        > **Для реального відео** завантажте MP4/AVI файл і оберіть кольори форм команд.  
        > **Для демо** натисніть «Запустити демо-аналіз» — система згенерує повноцінний звіт на основі симуляції.
        """)

    st.divider()

    # ---- ВКЛАДКИ ----
    tab_input, tab_tracking, tab_heatmap, tab_physics, tab_events = st.tabs([
        "📁 Джерело відео",
        "📍 Трекінг гравців",
        "🔥 Теплові карти",
        "⚡ Фізичні показники",
        "📋 Журнал подій"
    ])

    # ==========================================
    # ВКЛАДКА 1: ЗАВАНТАЖЕННЯ ВІДЕО
    # ==========================================
    with tab_input:
        st.subheader("Оберіть джерело для аналізу")

        source_mode = st.radio(
            "Режим аналізу:",
            ["🎮 Демо-симуляція (без відео)", "📹 Завантажити відеофайл"],
            horizontal=True
        )

        if source_mode == "📹 Завантажити відеофайл":
            st.info("📌 Підтримувані формати: MP4, AVI, MOV. Рекомендований розмір: до 200 МБ.")
            uploaded_video = st.file_uploader("Завантажте відеозапис матчу:", type=["mp4", "avi", "mov"])

            col_t1, col_t2 = st.columns(2)
            with col_t1:
                team1_color = st.selectbox("🔴 Колір форми команди 1:",
                    ["Червона команда", "Синя команда", "Жовта команда", "Зелена команда"])
            with col_t2:
                team2_color = st.selectbox("🔵 Колір форми команди 2:",
                    ["Синя команда", "Червона команда", "Жовта команда", "Зелена команда"],
                    index=1)

            max_frames = st.slider("Кількість кадрів для обробки:", 50, 300, 120,
                                   help="Більше кадрів = точніший аналіз, але довша обробка")

            if uploaded_video and st.button("🚀 Запустити аналіз відео", type="primary", use_container_width=True):
                try:
                    import cv2
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                        tmp_file.write(uploaded_video.read())
                        tmp_path = tmp_file.name

                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    status_text.text("⚙️ Ініціалізація OpenCV трекера...")
                    time.sleep(0.3)

                    from cv_analysis_module import (
                        process_real_video, TEAM_COLOR_RANGES
                    )

                    def update_progress(val):
                        progress_bar.progress(val)
                        status_text.text(f"🔍 Обробка кадрів... {int(val*100)}%")

                    teams_data, ball_positions, events, annotated_frames, fps = process_real_video(
                        tmp_path, team1_color, team2_color, max_frames, update_progress
                    )

                    os.unlink(tmp_path)

                    st.session_state.cv_teams_data = teams_data
                    st.session_state.cv_ball_positions = ball_positions
                    st.session_state.cv_events = events
                    st.session_state.cv_fps = fps
                    st.session_state.cv_analysis_done = True
                    st.session_state.cv_annotated_frames = annotated_frames

                    progress_bar.progress(1.0)
                    status_text.text("✅ Аналіз завершено!")
                    st.success(f"✅ Оброблено {max_frames} кадрів. Виявлено {len(events)} подій.")
                    st.rerun()

                except ImportError:
                    st.error("⚠️ OpenCV не встановлено. Встановіть: `pip install opencv-python-headless`")
                except Exception as e:
                    st.error(f"Помилка обробки відео: {e}")

        else:
            # ДЕМО РЕЖИМ
            st.info("🎮 Демо-режим: аналіз виконується на синтетичних даних, що імітують реальне відео.")

            col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
            with col_cfg1:
                demo_players = st.slider("Гравців у кожній команді:", 3, 8, 5)
            with col_cfg2:
                demo_frames = st.slider("Кількість кадрів симуляції:", 100, 500, 300)
            with col_cfg3:
                demo_fps = st.selectbox("FPS відео:", [25, 30, 50, 60], index=0)

            if st.button("🎬 Запустити демо-аналіз", type="primary", use_container_width=True):
                with st.spinner("Симулюємо трекінг гравців..."):
                    progress = st.progress(0)
                    for i in range(10):
                        time.sleep(0.08)
                        progress.progress((i+1)/10)

                    teams_data, ball_positions, events = simulate_tracking_data_internal(
                        num_players_per_team=demo_players,
                        num_frames=demo_frames,
                        fps=demo_fps
                    )

                    st.session_state.cv_teams_data = teams_data
                    st.session_state.cv_ball_positions = ball_positions
                    st.session_state.cv_events = events
                    st.session_state.cv_fps = demo_fps
                    st.session_state.cv_analysis_done = True
                    progress.progress(1.0)

                st.success(f"✅ Демо-аналіз завершено! Відстежено {demo_frames} кадрів, виявлено {len(events)} подій.")
                st.rerun()

        if st.session_state.cv_analysis_done:
            st.success("✅ Дані аналізу доступні. Перейдіть до вкладок вище для перегляду результатів.")

    # ==========================================
    # ВКЛАДКА 2: ТРЕКІНГ ГРАВЦІВ
    # ==========================================
    with tab_tracking:
        if not st.session_state.cv_analysis_done:
            st.info("👈 Спочатку запустіть аналіз у вкладці «Джерело відео».")
            return

        st.subheader("📍 Траєкторії руху гравців на полі")

        teams_data = st.session_state.cv_teams_data
        ball_positions = st.session_state.cv_ball_positions
        fps = st.session_state.cv_fps

        fig, ax = plt.subplots(figsize=(14, 9))
        ax.set_facecolor('#1a5c23')
        ax.set_xlim(0, 105)
        ax.set_ylim(0, 68)

        # Розмітка поля
        field = patches.Rectangle((0, 0), 105, 68, linewidth=2, edgecolor='white', facecolor='none')
        ax.add_patch(field)
        ax.plot([52.5, 52.5], [0, 68], 'w-', linewidth=1.5)
        center_circle = plt.Circle((52.5, 34), 9.15, color='white', fill=False, linewidth=1.5)
        ax.add_patch(center_circle)
        ax.plot(52.5, 34, 'wo', markersize=4)
        penalty_left = patches.Rectangle((0, 13.84), 16.5, 40.32, linewidth=1.5, edgecolor='white', facecolor='none')
        penalty_right = patches.Rectangle((88.5, 13.84), 16.5, 40.32, linewidth=1.5, edgecolor='white', facecolor='none')
        ax.add_patch(penalty_left)
        ax.add_patch(penalty_right)
        goal_left = patches.Rectangle((-2, 28.84), 2, 10.32, linewidth=1.5, edgecolor='white', facecolor='#444')
        goal_right = patches.Rectangle((105, 28.84), 2, 10.32, linewidth=1.5, edgecolor='white', facecolor='#444')
        ax.add_patch(goal_left)
        ax.add_patch(goal_right)

        TEAM_COLORS_PLOT = {
            "Червона команда": ("#FF4444", "o"),
            "Синя команда": ("#4488FF", "s"),
        }

        # Малюємо траєкторії
        show_trails = st.checkbox("Показати траєкторії руху", value=True)
        show_ball = st.checkbox("Показати траєкторію м'яча", value=True)
        frame_step = st.slider("Крок відображення (кадрів):", 1, 20, 5,
                               help="Менший крок = більше точок, детальніший маршрут")

        for team_name, color_info in TEAM_COLORS_PLOT.items():
            if team_name not in teams_data:
                continue
            team_color, marker = color_info
            team_frames = teams_data[team_name]

            # Збираємо всі позиції по гравцях
            num_players = max(len(f) for f in team_frames) if team_frames else 0
            for player_idx in range(num_players):
                player_xs = []
                player_ys = []
                for frame_positions in team_frames[::frame_step]:
                    if player_idx < len(frame_positions):
                        px, py = frame_positions[player_idx]
                        player_xs.append(px)
                        player_ys.append(py)

                if player_xs:
                    if show_trails:
                        ax.plot(player_xs, player_ys, '-', color=team_color, alpha=0.3, linewidth=1)

                    # Остання позиція — маркер гравця
                    ax.plot(player_xs[-1], player_ys[-1], marker=marker,
                           color=team_color, markersize=10, zorder=5,
                           markeredgecolor='white', markeredgewidth=1.5,
                           label=f"{team_name} #{player_idx+1}" if player_idx == 0 else "")

                    ax.text(player_xs[-1] + 1, player_ys[-1] + 1,
                           f"#{player_idx+1}", color='white', fontsize=7, zorder=6)

        # М'яч
        if show_ball and ball_positions:
            ball_xs = [p[0] for p in ball_positions[::frame_step]]
            ball_ys = [p[1] for p in ball_positions[::frame_step]]
            ax.plot(ball_xs, ball_ys, 'y--', alpha=0.4, linewidth=1)
            ax.plot(ball_xs[-1], ball_ys[-1], 'o', color='yellow',
                   markersize=8, zorder=7, markeredgecolor='black', markeredgewidth=1.5)

        # Лінія офсайду (приблизна)
        all_red_last_x = []
        if "Червона команда" in teams_data and teams_data["Червона команда"]:
            last_frame = teams_data["Червона команда"][-1]
            all_red_last_x = [p[0] for p in last_frame]

        if all_red_last_x:
            offside_x = max(all_red_last_x)
            ax.axvline(x=offside_x, color='yellow', linewidth=2, linestyle='--', alpha=0.7)
            ax.text(offside_x + 0.5, 65, 'ЛІНІЯ ОФСАЙДУ', color='yellow', fontsize=8, alpha=0.9)

        ax.legend(loc='upper right', facecolor='#1a5c23', labelcolor='white', fontsize=8)
        ax.set_title("Трекінг гравців та м'яча в реальних координатах поля (метри)",
                    color='white', fontsize=12, pad=10)
        fig.patch.set_facecolor('#0d3318')
        ax.tick_params(colors='white')
        ax.set_xlabel("Довжина поля (м)", color='white')
        ax.set_ylabel("Ширина поля (м)", color='white')
        for spine in ax.spines.values():
            spine.set_edgecolor('white')

        st.pyplot(fig)
        plt.close(fig)

        # Тактичні трикутники
        st.divider()
        st.subheader("📐 Тактичні трикутники (пресинг)")

        fig2, ax2 = plt.subplots(figsize=(14, 9))
        ax2.set_facecolor('#1a5c23')
        ax2.set_xlim(0, 105)
        ax2.set_ylim(0, 68)

        field2 = patches.Rectangle((0, 0), 105, 68, linewidth=2, edgecolor='white', facecolor='none')
        ax2.add_patch(field2)
        ax2.plot([52.5, 52.5], [0, 68], 'w-', linewidth=1.5)

        for team_name, color_info in TEAM_COLORS_PLOT.items():
            if team_name not in teams_data or not teams_data[team_name]:
                continue
            team_color, marker = color_info
            last_frame_positions = teams_data[team_name][-1]

            if len(last_frame_positions) >= 3:
                pts_arr = np.array([(p[0], p[1]) for p in last_frame_positions])

                for i in range(len(pts_arr) - 2):
                    tri_pts = pts_arr[i:i+3]
                    triangle = patches.Polygon(tri_pts, closed=True,
                                              facecolor=team_color, edgecolor=team_color,
                                              alpha=0.15, linewidth=1.5)
                    ax2.add_patch(triangle)
                    tri_edge = patches.Polygon(tri_pts, closed=True,
                                              fill=False, edgecolor=team_color,
                                              linewidth=1.5, linestyle='--')
                    ax2.add_patch(tri_edge)

                for idx, (px, py) in enumerate(last_frame_positions):
                    ax2.plot(px, py, marker=marker, color=team_color, markersize=10, zorder=5,
                            markeredgecolor='white', markeredgewidth=1.5)
                    ax2.text(px + 0.8, py + 0.8, f"#{idx+1}", color='white', fontsize=8, zorder=6)

        ax2.set_title("Тактичні трикутники (остання позиція гравців)", color='white', fontsize=12)
        fig2.patch.set_facecolor('#0d3318')
        ax2.set_xlabel("Довжина поля (м)", color='white')
        ax2.set_ylabel("Ширина поля (м)", color='white')
        ax2.tick_params(colors='white')
        for spine in ax2.spines.values():
            spine.set_edgecolor('white')

        st.pyplot(fig2)
        plt.close(fig2)

    # ==========================================
    # ВКЛАДКА 3: ТЕПЛОВІ КАРТИ
    # ==========================================
    with tab_heatmap:
        if not st.session_state.cv_analysis_done:
            st.info("👈 Спочатку запустіть аналіз у вкладці «Джерело відео».")
            return

        st.subheader("🔥 Теплові карти активності гравців")

        teams_data = st.session_state.cv_teams_data
        ball_positions = st.session_state.cv_ball_positions

        selected_team_hm = st.selectbox(
            "Оберіть команду для теплової карти:",
            list(teams_data.keys()) + ["М'яч"]
        )

        # Генеруємо теплову карту
        resolution = 40
        if selected_team_hm == "М'яч":
            heatmap = np.zeros((resolution, resolution))
            for (bx, by) in ball_positions:
                px = int(np.clip((bx / 105) * resolution, 0, resolution-1))
                py = int(np.clip((by / 68) * resolution, 0, resolution-1))
                sigma = 1.5
                for i in range(max(0, px-3), min(resolution, px+4)):
                    for j in range(max(0, py-3), min(resolution, py+4)):
                        dist = np.sqrt((i-px)**2 + (j-py)**2)
                        heatmap[j, i] += np.exp(-dist**2 / (2*sigma**2))
            title = "Теплова карта активності м'яча"
        else:
            heatmap = generate_heatmap_internal(teams_data[selected_team_hm])
            title = f"Теплова карта активності: {selected_team_hm}"

        # Нормалізуємо
        if heatmap.max() > 0:
            heatmap = heatmap / heatmap.max()

        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        fig.patch.set_facecolor('#0d3318')

        # Ліворуч — теплова карта на полі
        ax = axes[0]
        ax.set_facecolor('#1a5c23')
        ax.set_xlim(0, 105)
        ax.set_ylim(0, 68)

        field_bg = patches.Rectangle((0, 0), 105, 68, facecolor='#1a5c23', zorder=0)
        ax.add_patch(field_bg)

        # Теплова карта через imshow
        cmap = LinearSegmentedColormap.from_list('heat', ['#1a5c23', '#ffdd00', '#ff6600', '#cc0000'])
        hm_display = ax.imshow(
            heatmap,
            extent=[0, 105, 0, 68],
            origin='lower',
            cmap=cmap,
            alpha=0.75,
            aspect='auto',
            zorder=1
        )
        plt.colorbar(hm_display, ax=ax, label='Інтенсивність', fraction=0.035)

        # Розмітка поля поверх теплової карти
        field_rect = patches.Rectangle((0, 0), 105, 68, linewidth=2, edgecolor='white', facecolor='none', zorder=2)
        ax.add_patch(field_rect)
        ax.plot([52.5, 52.5], [0, 68], 'w-', linewidth=1.5, zorder=2)
        center_circ = plt.Circle((52.5, 34), 9.15, color='white', fill=False, linewidth=1.5, zorder=2)
        ax.add_patch(center_circ)
        pen_l = patches.Rectangle((0, 13.84), 16.5, 40.32, linewidth=1.5, edgecolor='white', facecolor='none', zorder=2)
        pen_r = patches.Rectangle((88.5, 13.84), 16.5, 40.32, linewidth=1.5, edgecolor='white', facecolor='none', zorder=2)
        ax.add_patch(pen_l)
        ax.add_patch(pen_r)

        ax.set_title(title, color='white', fontsize=11)
        ax.set_xlabel("Довжина поля (м)", color='white')
        ax.set_ylabel("Ширина поля (м)", color='white')
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_edgecolor('white')

        # Праворуч — 3D вид
        ax2 = axes[1]
        ax2.set_facecolor('#0d3318')
        x_coords = np.linspace(0, 105, resolution)
        y_coords = np.linspace(0, 68, resolution)
        X, Y = np.meshgrid(x_coords, y_coords)
        contour = ax2.contourf(X, Y, heatmap, levels=15, cmap='hot')
        plt.colorbar(contour, ax=ax2, label='Щільність присутності', fraction=0.035)
        ax2.set_title("Contour-карта (щільність)", color='white', fontsize=11)
        ax2.set_xlabel("Довжина поля (м)", color='white')
        ax2.set_ylabel("Ширина поля (м)", color='white')
        ax2.tick_params(colors='white')
        for spine in ax2.spines.values():
            spine.set_edgecolor('white')

        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        # Зони активності
        st.divider()
        st.subheader("📊 Розподіл активності по зонах поля")
        
        col_z1, col_z2, col_z3 = st.columns(3)
        zone_labels = ["Захисна зона\n(0–35 м)", "Центральна зона\n(35–70 м)", "Атакуюча зона\n(70–105 м)"]
        zone_bounds = [(0, 13), (13, 27), (27, 40)]

        for col, label, (z_start, z_end) in zip([col_z1, col_z2, col_z3], zone_labels, zone_bounds):
            zone_activity = heatmap[:, z_start:z_end].sum()
            total_activity = heatmap.sum() if heatmap.sum() > 0 else 1
            zone_pct = (zone_activity / total_activity) * 100
            col.metric(label, f"{zone_pct:.1f}%")

    # ==========================================
    # ВКЛАДКА 4: ФІЗИЧНІ ПОКАЗНИКИ
    # ==========================================
    with tab_physics:
        if not st.session_state.cv_analysis_done:
            st.info("👈 Спочатку запустіть аналіз у вкладці «Джерело відео».")
            return

        st.subheader("⚡ Фізичні показники гравців (вичислені з відео)")

        teams_data = st.session_state.cv_teams_data
        fps = st.session_state.cv_fps

        stats_rows = []
        for team_name, team_frames in teams_data.items():
            if not team_frames:
                continue
            num_players = max(len(f) for f in team_frames)

            for player_idx in range(num_players):
                player_positions = []
                for frame_positions in team_frames:
                    if player_idx < len(frame_positions):
                        player_positions.append(frame_positions[player_idx])

                if len(player_positions) < 2:
                    continue

                # Пройдена дистанція
                total_dist = 0.0
                speeds = []
                for i in range(1, len(player_positions)):
                    x1, y1 = player_positions[i-1]
                    x2, y2 = player_positions[i]
                    dist_m = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                    total_dist += dist_m

                    speed_ms = dist_m * fps  # м/кадр * fps = м/с
                    speeds.append(speed_ms * 3.6)  # → км/год

                avg_speed = np.mean(speeds) if speeds else 0.0
                max_speed = np.max(speeds) if speeds else 0.0
                time_analyzed = len(player_positions) / fps

                stats_rows.append({
                    "Команда": team_name,
                    "Гравець": f"#{player_idx+1}",
                    "Дистанція (м)": round(total_dist, 1),
                    "Дистанція (км)": round(total_dist / 1000, 3),
                    "Середня швидкість (км/год)": round(avg_speed, 1),
                    "Макс. швидкість (км/год)": round(max_speed, 1),
                    "Час аналізу (с)": round(time_analyzed, 1)
                })

        if stats_rows:
            stats_df = pd.DataFrame(stats_rows)

            # Відображення таблиці
            st.caption("📌 Показники розраховані на основі реальних розмірів футбольного поля (105×68 м)")
            styled_stats = stats_df.style.background_gradient(
                cmap='RdYlGn', subset=['Макс. швидкість (км/год)']
            ).format({
                'Дистанція (м)': '{:.1f}',
                'Дистанція (км)': '{:.3f}',
                'Середня швидкість (км/год)': '{:.1f}',
                'Макс. швидкість (км/год)': '{:.1f}',
            })
            st.dataframe(styled_stats, use_container_width=True, hide_index=True)

            st.divider()

            # Графік швидкостей гравців однієї команди
            st.subheader("📈 Динаміка швидкості у часі")
            selected_team_ph = st.selectbox("Команда:", list(teams_data.keys()), key="physics_team")
            selected_player_ph = st.selectbox("Гравець:", [f"#{i+1}" for i in range(
                max(len(f) for f in teams_data[selected_team_ph]) if teams_data[selected_team_ph] else 1
            )], key="physics_player")

            player_idx = int(selected_player_ph[1:]) - 1
            team_frames = teams_data[selected_team_ph]
            speed_timeline = []
            time_axis = []

            for frame_i, frame_positions in enumerate(team_frames):
                if player_idx < len(frame_positions) and frame_i > 0:
                    prev_frame = team_frames[frame_i - 1]
                    if player_idx < len(prev_frame):
                        x1, y1 = prev_frame[player_idx]
                        x2, y2 = frame_positions[player_idx]
                        dist = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                        speed = dist * fps * 3.6
                        speed_timeline.append(min(speed, 40))  # Обмежуємо 40 км/год (реалізм)
                        time_axis.append(frame_i / fps)

            if speed_timeline:
                speed_df = pd.DataFrame({
                    "Час (с)": time_axis,
                    "Швидкість (км/год)": speed_timeline
                }).set_index("Час (с)")

                # Згладжування
                speed_smooth = pd.Series(speed_timeline).rolling(window=7, center=True).mean().fillna(
                    pd.Series(speed_timeline)
                )

                fig_speed, ax_speed = plt.subplots(figsize=(12, 4))
                ax_speed.plot(time_axis, speed_timeline, alpha=0.25, color='#448AFF', linewidth=0.8)
                ax_speed.plot(time_axis, speed_smooth.tolist(), color='#FF5252', linewidth=2, label='Згладжена швидкість')
                ax_speed.axhline(y=np.mean(speed_timeline), color='#FFD700', linestyle='--',
                                linewidth=1.5, label=f"Середня: {np.mean(speed_timeline):.1f} км/год")
                ax_speed.set_xlabel("Час (секунди)")
                ax_speed.set_ylabel("Швидкість (км/год)")
                ax_speed.set_title(f"Профіль швидкості: {selected_team_ph} {selected_player_ph}")
                ax_speed.legend()
                ax_speed.set_facecolor('#f8f9fa')
                ax_speed.grid(True, alpha=0.3)
                st.pyplot(fig_speed)
                plt.close(fig_speed)

                # Підсумкові метрики
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Середня швидкість", f"{np.mean(speed_timeline):.1f} км/год")
                c2.metric("Максимальна швидкість", f"{np.max(speed_timeline):.1f} км/год")
                c3.metric("Час вище 20 км/год", f"{sum(1 for s in speed_timeline if s > 20) / fps:.1f} с")
                c4.metric("Sprint (> 25 км/год)", f"{sum(1 for s in speed_timeline if s > 25) / fps:.1f} с")
        else:
            st.warning("Недостатньо даних для розрахунку фізичних показників.")

    # ==========================================
    # ВКЛАДКА 5: ЖУРНАЛ ПОДІЙ
    # ==========================================
    with tab_events:
        if not st.session_state.cv_analysis_done:
            st.info("👈 Спочатку запустіть аналіз у вкладці «Джерело відео».")
            return

        st.subheader("📋 Автоматично розпізнані ігрові події")
        st.caption("Модель аналізує траєкторії м'яча та гравців для виявлення ключових моментів матчу.")

        events = st.session_state.cv_events

        if not events:
            st.info("Подій не виявлено. Спробуйте збільшити кількість кадрів для аналізу.")
        else:
            # Фільтр подій
            event_types = list(set(e["type"] for e in events))
            selected_types = st.multiselect("Фільтр за типом подій:", event_types, default=event_types)

            filtered_events = [e for e in events if e["type"] in selected_types]

            st.markdown(f"**Знайдено подій: {len(filtered_events)}**")
            st.divider()

            for event in filtered_events:
                team_name = event.get("team", "Невідома команда")
                conf = event.get("confidence", 0)
                t_sec = event.get("time", 0)
                mins = int(t_sec // 60)
                secs = int(t_sec % 60)

                col_time, col_icon, col_desc, col_conf = st.columns([1, 0.5, 5, 1.5])
                col_time.markdown(f"**{mins:02d}:{secs:02d}**")
                col_icon.write(event["icon"])
                col_desc.write(f"**{event['type']}** — {team_name}")
                col_conf.metric("Впевненість", f"{conf*100:.0f}%")

            st.divider()

            # Статистика подій
            st.subheader("📊 Статистика подій по командах")
            event_stats = {}
            for e in events:
                team = e.get("team", "Невідома")
                event_stats[team] = event_stats.get(team, 0) + 1

            if event_stats:
                stats_df = pd.DataFrame(list(event_stats.items()), columns=["Команда", "Кількість подій"])
                st.bar_chart(stats_df.set_index("Команда"))


# ==========================================
# 6. ЛАБОРАТОРІЯ ФІЗИКИ
# ==========================================
def render_physics():
    st.title("⚛️ Лабораторія Фізики")
    df = st.session_state.athletes_db
    player = st.selectbox("Оберіть спортсмена для симуляції:", df["Ім'я"])
    data = df[df["Ім'я"] == player].iloc[0]

    v0 = st.slider("Швидкість (м/с)", 5.0, 50.0, float(data['Сила'] * 0.4))
    angle = st.slider("Кут (°)", 10, 80, 35)

    g = 9.81
    rad = np.radians(angle)
    t_f = (2 * v0 * np.sin(rad)) / g
    t = np.linspace(0, t_f, 100)
    x = v0 * np.cos(rad) * t
    y = v0 * np.sin(rad) * t - 0.5 * g * t ** 2

    fig, ax = plt.subplots()
    ax.plot(x, y, color="#00BCD4")
    ax.set_title("Траєкторія руху снаряда (залежно від сили гравця)")
    st.pyplot(fig)


# ==========================================
# 7. СИМУЛЯТОР МАТЧІВ
# ==========================================
def render_simulator():
    st.title("🎲 AI-Симулятор Матчів")
    st.markdown("""
    Зіштовхніть двох гравців у віртуальному поєдинку!
    Система генерує хід матчу, спираючись на **PER (Рейтинг ефективності)**, швидкість та витривалість спортсменів.
    """)
    st.divider()

    df = st.session_state.athletes_db

    c1, c_vs, c2 = st.columns([3, 1, 3])

    p1 = c1.selectbox("🔴 Кут 1 (Червоні)", df["Ім'я"], key="s1")
    c_vs.markdown("<h2 style='text-align: center; margin-top: 25px;'>⚔️ VS</h2>", unsafe_allow_html=True)
    p2 = c2.selectbox("🔵 Кут 2 (Сині)", df["Ім'я"], index=min(1, len(df)-1), key="s2")

    p1_data = df[df["Ім'я"] == p1].iloc[0]
    p2_data = df[df["Ім'я"] == p2].iloc[0]

    per1 = p1_data['PER (Рейтинг)']
    per2 = p2_data['PER (Рейтинг)']

    total_per = per1 + per2
    win_prob_1 = (per1 / total_per) * 100 if total_per > 0 else 50
    win_prob_2 = (per2 / total_per) * 100 if total_per > 0 else 50

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📊 Передматчеве порівняння (Tale of the Tape)", expanded=True):
        st.progress(win_prob_1 / 100)
        st.caption(f"📈 Ймовірність домінування: **{p1}** ({win_prob_1:.1f}%) проти **{p2}** ({win_prob_2:.1f}%)")

        stat_c1, stat_c2, stat_c3 = st.columns(3)
        stat_c1.metric(f"Швидкість", f"{p1_data['Швидкість']} км/год", f"{p1_data['Швидкість'] - p2_data['Швидкість']:.1f} vs {p2}", delta_color="normal")
        stat_c2.metric(f"Витривалість", int(p1_data['Витривалість']), f"{int(p1_data['Витривалість'] - p2_data['Витривалість'])} vs {p2}", delta_color="normal")
        stat_c3.metric(f"PER", f"{per1:.1f}", f"{per1 - per2:.1f} vs {p2}", delta_color="normal")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 РОЗПОЧАТИ СИМУЛЯЦІЮ МАТЧУ", type="primary", use_container_width=True):
        with st.spinner("Свисток! Матч розпочався..."):
            time.sleep(1.5)

        log = []
        score1, score2 = 0, 0
        minutes = sorted(random.sample(range(1, 91), random.randint(6, 10)))

        event_templates = {
            "гол": ["{player} влучив у ворота!", "{player} реалізував штрафний удар!", "{player} потужно пробив під поперечину!"],
            "обіграв": ["{player} обіграв суперника на швидкості {speed:.1f} км/год.", "{player} зробив блискучий фінт."],
            "захист": ["{player} перехопив небезпечну передачу.", "{player} відбив атаку на останніх секундах!"],
            "пас": ["{player} віддав геніальний пас у розріз.", "{player} розпочав небезпечну контратаку."],
            "карточка": ["{player} отримав попередження за тактичний фол."]
        }

        for minute in minutes:
            weight1 = per1 / (per1 + per2)
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
            s1_final = per1 * random.uniform(0.9, 1.1)
            s2_final = per2 * random.uniform(0.9, 1.1)
            winner = p1 if s1_final > s2_final else p2
            winner_pen = True
        else:
            winner = p1 if score1 > score2 else p2
            winner_pen = False

        st.session_state.match_log = log

        st.divider()
        col_sc1, col_vs2, col_sc2 = st.columns([2, 1, 2])
        col_sc1.markdown(f"<h3 style='text-align: center;'>🔴 {p1}</h3>", unsafe_allow_html=True)
        col_sc1.markdown(f"<h1 style='text-align: center;'>{score1}</h1>", unsafe_allow_html=True)
        col_vs2.markdown("<h3 style='text-align: center; color: gray; margin-top: 20px;'>КІНЕЦЬ</h3>", unsafe_allow_html=True)
        col_sc2.markdown(f"<h3 style='text-align: center;'>🔵 {p2}</h3>", unsafe_allow_html=True)
        col_sc2.markdown(f"<h1 style='text-align: center;'>{score2}</h1>", unsafe_allow_html=True)

        if winner_pen:
            st.warning(f"⏱️ Нічия {score1}:{score2}. Перемога за додатковими показниками: **{winner}**!")
        else:
            st.balloons()
            st.success(f"🏆 Впевнена перемога: **{winner}** ({score1}:{score2})")

        st.divider()
        st.subheader("📋 Хронологія матчу")
        for event in st.session_state.match_log:
            col_m, col_i, col_e, col_s = st.columns([1, 0.5, 7, 1.5])
            col_m.write(f"**{event['хв']}'**")
            col_i.write(event['icon'])
            col_e.write(event['подія'])
            col_s.markdown(f"**[{event['рахунок']}]**")

    elif st.session_state.match_log:
        st.divider()
        st.info("Попередній матч збережено. Натисніть кнопку вище, щоб розпочати новий.")


# ==========================================
# 8. ПРОГНОЗ ТРАВМАТИЗМУ
# ==========================================
def render_injury_prediction():
    st.title("🩹 AI Health Monitor")
    st.markdown("""
    Цей модуль аналізує фізичний стан гравця та його поточне навантаження, щоб передбачити ймовірність отримання травми.
    """)
    st.divider()

    df = st.session_state.athletes_db

    col_select, col_status = st.columns([2, 1])
    with col_select:
        selected_player = st.selectbox("Оберіть гравця для медичного чекапу:", df["Ім'я"])
    player_data = df[df["Ім'я"] == selected_player].iloc[0]

    st.markdown("<br>", unsafe_allow_html=True)

    col_edit, col_info = st.columns([1.5, 2])
    with col_edit:
        st.subheader("📅 Навантаження (останні 7 днів)")
        workload = st.number_input("Кількість зіграних матчів/інтенсивних тренувань", min_value=0, max_value=7,
                                   value=int(player_data.get('Навантаження_7днів', 0)), key="workload_input")
        st.session_state.athletes_db.loc[st.session_state.athletes_db["Ім'я"] == selected_player, 'Навантаження_7днів'] = workload

    imbalance = abs(player_data['Сила'] - player_data['Витривалість'])
    base_risk = int((imbalance * 1.5) + (player_data['Швидкість'] * 0.5))

    if workload >= 3: workload_factor = 45
    elif workload == 2: workload_factor = 20
    else: workload_factor = 0

    if player_data['Витривалість'] < 55: stamina_penalty = 20
    else: stamina_penalty = 0

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
        st.write("<br>", unsafe_allow_html=True)
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
        risk_text = "Низький" if injury_risk < 40 else ("Середній" if injury_risk < 75 else "Високий")
        st.markdown(f"<h2 style='text-align: center; color: {color};'>{injury_risk}%</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center;'>Рівень загрози: <b>{risk_text}</b></p>", unsafe_allow_html=True)
        st.progress(injury_risk / 100)

    with c2:
        st.subheader("📊 Фізіологічні метрики")
        st.write("Базове навантаження на суглоби:")
        st.progress(min(base_risk, 100) / 100)
        st.write("Рівень накопиченої втоми:")
        st.progress(min(workload_factor * 2, 100) / 100)
        st.write("Дефіцит витривалості:")
        st.progress(min(stamina_penalty * 4, 100) / 100)

    with c3:
        st.subheader("💊 Протокол відновлення")
        if injury_risk >= 75:
            st.error("🛑 Відсторонити від тренувань на 48 годин.")
            st.write("✅ **Фізіотерапія:** Кріотерапія, глибокий масаж.")
        elif injury_risk >= 40:
            st.warning("⏳ Протокол часткового відновлення.")
            st.write("✅ **Тренування:** Легке кардіо, розтяжка.")
        else:
            st.success("💪 Спеціальні заходи не потрібні.")
            st.write("✅ **Тренування:** В загальній групі, 100% інтенсивність.")


# ==========================================
# 9. AI-ТРЕНЕР
# ==========================================
def render_ai_advisor():
    st.title("🧬 Індивідуальні плани тренувань (AI Advisor)")
    st.markdown("""
    Система автоматично аналізує фізичні показники гравця та генерує персоналізований розклад тренувань.
    """)
    st.divider()

    df = st.session_state.athletes_db

    if df.empty:
        st.warning("База даних порожня. Додайте гравців для аналізу.")
        return

    selected_player = st.selectbox("Оберіть гравця для генерації плану:", df["Ім'я"])
    player_data = df[df["Ім'я"] == selected_player].iloc[0]

    speed = player_data['Швидкість']
    stamina = player_data['Витривалість']
    power = player_data['Сила']
    workload = player_data.get('Навантаження_7днів', 0)

    st.subheader(f"📊 Поточний профіль: {selected_player}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Швидкість", f"{speed:.1f} км/год")
    c2.metric("Витривалість", f"{stamina:.0f}")
    c3.metric("Сила", f"{power:.0f}")
    c4.metric("Навантаження", f"{workload} (за 7 днів)")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🤖 Звіт генератора рекомендацій")

    report = []
    if stamina < 60 and speed > 28:
        report.append(f"Витривалість < 60, але швидкість > 28 — рекомендуємо інтервальні тренування низької інтенсивності.")
    elif stamina < 60:
        report.append(f"Витривалість критично низька (< 60). Необхідні базові аеробні навантаження (кроси 40-60 хвилин).")
    if power < 65:
        report.append("Показник сили нижчий за норму. 2-3 силові сесії на тиждень (тренажерний зал).")
    if speed < 25 and power >= 65:
        report.append("Достатня силова база, але дефіцит швидкості. Фокус на пліометрику та короткі спринти.")
    if workload >= 3:
        report.append("⚠️ Високе навантаження. Акцент на відновлення (басейн, масаж), тактичну підготовку.")
    if not report:
        report.append(f"Показники {selected_player} в оптимальному балансі. Стандартний підтримуючий режим.")

    formatted_report = "\n\n".join([f"🔸 {item}" for item in report])
    st.info("💡 **Персоналізовані рекомендації:**\n\n" + formatted_report)

    st.markdown("### 📅 Орієнтовний розклад на тиждень:")

    if workload >= 3:
        schedule = pd.DataFrame({
            "День": ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"],
            "Активність": ["Легке відновлення", "Масаж / Басейн", "Тактична дошка", "Повний відпочинок", "Легке тренування (45 хв)", "Матч", "Повний відпочинок"]
        })
    elif stamina < 60 and speed > 28:
        schedule = pd.DataFrame({
            "День": ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"],
            "Активність": ["Інтервальне тренування (низька інтенсивність)", "Відпочинок", "Техніка з м'ячем", "Спеціальна витривалість", "Тактика", "Матч", "Відновлення"]
        })
    else:
        schedule = pd.DataFrame({
            "День": ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"],
            "Активність": ["Силове тренування", "Аеробна база (крос)", "Відпочинок", "Пліометрика / Швидкість", "Передігрова розминка", "Матч", "Відновлення"]
        })

    st.table(schedule.set_index("День"))


# ==========================================
# 10. ІСТОРІЯ ФОРМИ
# ==========================================
def render_form_history():
    st.title("📈 Історія форми (Time-Series аналіз)")
    df = st.session_state.athletes_db

    if df.empty:
        st.warning("База даних порожня.")
        return

    selected_player = st.selectbox("Оберіть гравця для аналізу динаміки:", df["Ім'я"])
    player_data = df[df["Ім'я"] == selected_player].iloc[0]

    np.random.seed(hash(selected_player) % (2**32))

    curr_per = player_data['PER (Рейтинг)']
    curr_stamina = player_data['Витривалість']
    curr_speed = player_data['Швидкість']

    def generate_trend(current_val, volatility):
        trend = [current_val]
        for _ in range(9):
            val = trend[-1] + np.random.normal(0, volatility)
            trend.append(max(0, val))
        return trend[::-1]

    matches = [f"Матч {i}" for i in range(1, 11)]
    history_df = pd.DataFrame({
        "Матч": matches,
        "PER (Рейтинг)": generate_trend(curr_per, 2.5),
        "Витривалість": generate_trend(curr_stamina, 4.0),
        "Швидкість": generate_trend(curr_speed, 1.5)
    })
    history_df.set_index("Матч", inplace=True)

    st.markdown(f"### 📊 Динаміка показників: **{selected_player}** за останні 10 матчів")
    st.info("💡 *Дані генеруються автоматично на основі поточних показників гравця для демонстрації Time-Series аналітики.*")

    st.subheader("Зміна рейтингу ефективності (PER)")
    st.line_chart(history_df["PER (Рейтинг)"], color="#FF4B4B")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Витривалість")
        st.line_chart(history_df["Витривалість"], color="#0068C9")
    with c2:
        st.subheader("Швидкість (км/год)")
        st.line_chart(history_df["Швидкість"], color="#29B09D")


# ==========================================
# 11. РЕСУРСИ ТА ОСВІТА
# ==========================================
def render_resources():
    st.title("📚 Спортивна Аналітика та Новини")
    st.markdown("Вивчайте сучасні методи аналізу даних та слідкуйте за світом спорту.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📰 Новини та Аналітика")
        st.info("**SportAnalytic** — Огляди та футбольні новини.")
        st.link_button("Перейти на SportAnalytic", "https://sportanalytic.com/")
        st.divider()
        st.info("**Sport.ua** — Головний спортивний портал України.")
        st.link_button("Перейти на Sport.ua", "https://sport.ua/uk")

    with col2:
        st.subheader("🎓 Навчання та Статті")
        st.success("**Robot Dreams** — Як перетворити дані на результати.")
        st.link_button("Читати статтю", "https://robotdreams.cc/uk/blog/384-data-analiz-u-sporti-yak-peretvoriti-dani-na-rezultati")
        st.divider()
        st.success("**Наукова робота** — ІТ у спорті.")
        st.link_button("Відкрити публікацію", "https://enpuir.udu.edu.ua/entities/publication/c7becbfd-8d2c-4566-89f4-9a85d3c3062a")


# ==========================================
# 12. ЕКСПОРТ
# ==========================================
def render_io():
    st.title("💾 Експорт Даних")
    df = st.session_state.athletes_db

    st.download_button("📥 Завантажити CSV", df.to_csv(index=False).encode('utf-8'), "athletes_data.csv", mime="text/csv")
    st.download_button("📥 Завантажити JSON", df.to_json(orient='records', force_ascii=False), "athletes_data.json", mime="application/json")

    st.divider()
    st.subheader("📋 Шаблон для заповнення")
    template_df = pd.DataFrame(columns=["Ім'я", "Вік", "Вид спорту", "Матчі", "Очки", "Швидкість", "Витривалість", "Сила", "Навантаження_7днів"])
    st.download_button("📄 Завантажити порожній шаблон CSV", template_df.to_csv(index=False).encode('utf-8'), "template_athletes.csv", mime="text/csv")
    st.caption("Заповніть шаблон та завантажте через «📂 Завантажити свої дані» у сайдбарі.")


if __name__ == "__main__":
    main()
