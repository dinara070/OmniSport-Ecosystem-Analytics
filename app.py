import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time
import random
import io

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
    # ВИПРАВЛЕННЯ: Якщо в збереженій сесії немає колонки 'Вік' (старі дані)
    if 'Вік' not in st.session_state.athletes_db.columns:
        st.session_state.athletes_db['Вік'] = 20  # Встановлюємо дефолтний вік

if 'tactic_points' not in st.session_state:
    st.session_state.tactic_points = []

if 'match_log' not in st.session_state:
    st.session_state.match_log = []

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
        st.caption("Performance Analytics v9.1")
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
                        # Захист: якщо у файлі немає колонки Вік
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
            "⚛️ Лабораторія Фізики",
            "🎲 AI-Симулятор Матчів",
            "🩹 Прогноз Травматизму",
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
    elif choice == "⚛️ Лабораторія Фізики": render_physics()
    elif choice == "🎲 AI-Симулятор Матчів": render_simulator()
    elif choice == "🩹 Прогноз Травматизму": render_injury_prediction()
    elif choice == "📈 Історія форми": render_form_history()
    elif choice == "📚 Ресурси та Освіта": render_resources()
    elif choice == "💾 Експорт Даних": render_io()

# ==========================================
# 1. ДАШБОРД
# ==========================================
def render_dashboard():
    st.title("🏠 Аналітична панель")
    
    # 1. Компактний блок з інформацією (можна згорнути)
    with st.expander("👋 Вітаємо в командному центрі OmniSport Pro!", expanded=True):
        st.markdown("""
        Цей розділ створений для швидкого моніторингу ключових показників вашої команди:
        * **Оцінити загальний стан:** кількість активних гравців у ростері.
        * **Визначити рекорди:** максимальні показники швидкості та витривалості.
        * **Виявити лідерів:** зведена таблиця на основі комплексного рейтингу **PER**.
        """)
        st.info("💡 **Порада:** Використовуйте бічне меню ліворуч для глибшої аналітики, порівняння гравців (H2H) або налаштування тактики.")

    st.markdown("<br>", unsafe_allow_html=True) # Додаємо трохи візуального простору

    df = st.session_state.athletes_db

    # 2. Стилізовані метрики з іконками
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

    # 3. Чистіша таблиця без зайвих нулів та системного індексу
    st.subheader("📊 Загальний рейтинг команди")
    st.caption("🏆 Гравці відсортовані за рейтингом ефективності. Чим насиченіший синій колір — тим вищий показник.")
    
    # Сортуємо дані
    formatted_df = df.sort_values(by="PER (Рейтинг)", ascending=False).copy()
    
    # Налаштовуємо градієнт та форматуємо колонки (забираємо купу нулів після коми)
    styled_df = formatted_df.style.background_gradient(
        cmap='Blues', subset=['PER (Рейтинг)']
    ).format({
        'Швидкість': '{:.1f}',
        'Витривалість': '{:.0f}',
        'Сила': '{:.0f}',
        'PER (Рейтинг)': '{:.1f}'
    })

    # Виводимо таблицю на всю ширину і приховуємо системний індекс
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
    
    # ВИПРАВЛЕННЯ: Безпечний підрахунок віку
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

    # 1. Панель пошуку та фільтрації (Робить вигляд справжньої CRM)
    st.subheader("🔍 Пошук та фільтри")
    col_search, col_filter = st.columns(2)
    with col_search:
        search_query = st.text_input("Пошук за ім'ям", placeholder="Введіть ім'я гравця...")
    with col_filter:
        sport_options = ["Всі види"] + list(df['Вид спорту'].dropna().unique())
        selected_sport = st.selectbox("Фільтр за видом спорту", sport_options)

    # Логіка фільтрації
    filtered_df = df.copy()
    if search_query:
        filtered_df = filtered_df[filtered_df["Ім'я"].str.contains(search_query, case=False, na=False)]
    if selected_sport != "Всі види":
        filtered_df = filtered_df[filtered_df['Вид спорту'] == selected_sport]

    st.divider()

    # 2. Форма додавання (зробили кнопку акцентною і додали перевірку на порожнє ім'я)
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

    # 3. Інтерактивна таблиця з результатами
    st.subheader(f"📋 Список гравців (Знайдено: {len(filtered_df)})")
    st.caption("💡 **Підказка:** Ви можете сортувати колонки, натискаючи на їхні назви.")

    # Форматуємо дані перед виводом (забираємо нулі, залишаємо акуратні числа)
    styled_df = filtered_df.style.format({
        'Швидкість': '{:.1f}',
        'Витривалість': '{:.0f}',
        'Сила': '{:.0f}',
        'PER (Рейтинг)': '{:.1f}'
    })

    # Виводимо красиво відформатовану таблицю без системних індексів
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=400  # Фіксуємо висоту, щоб візуально відділити таблицю
    )

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
        # ВИПРАВЛЕННЯ: Безпечний вивід віку
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
# 5. ЛАБОРАТОРІЯ ФІЗИКИ
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
# 6. СИМУЛЯТОР МАТЧІВ
# ==========================================
def render_simulator():
    st.title("🎲 AI-Симулятор Матчів")
    st.markdown("""
    Зіштовхніть двох гравців у віртуальному поєдинку! 
    Система генерує хід матчу, спираючись на **PER (Рейтинг ефективності)**, швидкість та витривалість спортсменів. Чим вищі показники, тим більше шансів на домінування.
    """)
    st.divider()

    df = st.session_state.athletes_db
    
    # 1. Вибір гравців з яскравим "VS" по центру
    c1, c_vs, c2 = st.columns([3, 1, 3])

    p1 = c1.selectbox("🔴 Кут 1 (Червоні)", df["Ім'я"], key="s1")
    
    # Візуальний акцент по центру
    c_vs.markdown("<h2 style='text-align: center; margin-top: 25px;'>⚔️ VS</h2>", unsafe_allow_html=True)
    
    p2 = c2.selectbox("🔵 Кут 2 (Сині)", df["Ім'я"], index=min(1, len(df)-1), key="s2")

    p1_data = df[df["Ім'я"] == p1].iloc[0]
    p2_data = df[df["Ім'я"] == p2].iloc[0]

    per1 = p1_data['PER (Рейтинг)']
    per2 = p2_data['PER (Рейтинг)']
    
    # Підрахунок ймовірності перемоги на основі PER
    total_per = per1 + per2
    win_prob_1 = (per1 / total_per) * 100 if total_per > 0 else 50
    win_prob_2 = (per2 / total_per) * 100 if total_per > 0 else 50

    # 2. Передматчеве порівняння (завжди видиме)
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📊 Передматчеве порівняння (Tale of the Tape)", expanded=True):
        st.progress(win_prob_1 / 100)
        st.caption(f"📈 Ймовірність домінування: **{p1}** ({win_prob_1:.1f}%) проти **{p2}** ({win_prob_2:.1f}%)")
        
        stat_c1, stat_c2, stat_c3 = st.columns(3)
        stat_c1.metric(f"Швидкість", f"{p1_data['Швидкість']} км/год", f"{p1_data['Швидкість'] - p2_data['Швидкість']:.1f} vs {p2}", delta_color="normal")
        stat_c2.metric(f"Витривалість", int(p1_data['Витривалість']), f"{int(p1_data['Витривалість'] - p2_data['Витривалість'])} vs {p2}", delta_color="normal")
        stat_c3.metric(f"PER", f"{per1:.1f}", f"{per1 - per2:.1f} vs {p2}", delta_color="normal")

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. Кнопка старту (велика і помітна)
    if st.button("🚀 РОЗПОЧАТИ СИМУЛЯЦІЮ МАТЧУ", type="primary", use_container_width=True):
        
        with st.spinner("Свисток! Матч розпочався..."):
            time.sleep(1.5) # Трохи затримки для інтриги

        log = []
        score1, score2 = 0, 0
        minutes = sorted(random.sample(range(1, 91), random.randint(6, 10)))

        event_templates = {
            "гол": ["{player} влучив у ворота!", "{player} реалізував штрафний удар!", "{player} потужно пробив під поперечину!", "{player} забив з-за меж штрафної!"],
            "обіграв": ["{player} обіграв суперника на швидкості {speed:.1f} км/год.", "{player} зробив блискучий фінт."],
            "захист": ["{player} перехопив небезпечну передачу.", "{player} відбив атаку на останніх секундах!"],
            "пас": ["{player} віддав геніальний пас у розріз.", "{player} розпочав небезпечну контратаку."],
            "карточка": ["{player} отримав попередження за тактичний фол.", "{player} зупинив атаку суперника грубо."]
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
            st.warning(f"⏱️ Основний час завершився внічию {score1}:{score2}. Перемога за додатковими показниками: **{winner}**!")
        else:
            st.balloons()
            st.success(f"🏆 Впевнена перемога: **{winner}** ({score1}:{score2})")

        st.divider()
        st.subheader("📋 Хронологія матчу")
        
        # Відображення логу в красивому контейнери
        with st.container():
            for event in st.session_state.match_log:
                col_m, col_i, col_e, col_s = st.columns([1, 0.5, 7, 1.5])
                col_m.write(f"**{event['хв']}'**")
                col_i.write(event['icon'])
                col_e.write(event['подія'])
                col_s.markdown(f"**[{event['рахунок']}]**")

    # Відображення попереднього логу, якщо симуляція не запущена в цей момент
    elif st.session_state.match_log:
        st.divider()
        st.info("Попередній матч збережено. Натисніть кнопку вище, щоб розпочати новий.")
        with st.expander("📋 Лог попереднього матчу", expanded=False):
            for event in st.session_state.match_log:
                col_m, col_i, col_e, col_s = st.columns([1, 0.5, 7, 1.5])
                col_m.write(f"**{event['хв']}'**")
                col_i.write(event['icon'])
                col_e.write(event['подія'])
                col_s.markdown(f"**[{event['рахунок']}]**")

# ==========================================
# 7. ПРОГНОЗ ТРАВМАТИЗМУ
# ==========================================
def render_injury_prediction():
    st.title("🩹 AI Health Monitor")
    st.markdown("""
    Цей модуль аналізує фізичний стан гравця та його поточне навантаження, щоб передбачити ймовірність отримання травми.
    Система враховує баланс сили та витривалості, а також накопичену втому за останні 7 днів.
    """)
    st.divider()

    df = st.session_state.athletes_db
    
    col_select, col_status = st.columns([2, 1])
    with col_select:
        selected_player = st.selectbox("Оберіть гравця для медичного чекапу:", df["Ім'я"])
    player_data = df[df["Ім'я"] == selected_player].iloc[0]

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 1. Блок навантаження
    col_edit, col_info = st.columns([1.5, 2])
    with col_edit:
        st.subheader("📅 Навантаження (останні 7 днів)")
        workload = st.number_input("Кількість зіграних матчів/інтенсивних тренувань", min_value=0, max_value=7, value=int(player_data.get('Навантаження_7днів', 0)), key="workload_input")
        # Оновлюємо дані в сесії
        st.session_state.athletes_db.loc[st.session_state.athletes_db["Ім'я"] == selected_player, 'Навантаження_7днів'] = workload

    # Логіка розрахунку ризику
    imbalance = abs(player_data['Сила'] - player_data['Витривалість'])
    base_risk = int((imbalance * 1.5) + (player_data['Швидкість'] * 0.5))
    
    if workload >= 3: workload_factor = 45
    elif workload == 2: workload_factor = 20
    else: workload_factor = 0

    if player_data['Витривалість'] < 55: stamina_penalty = 20
    else: stamina_penalty = 0

    injury_risk = min(base_risk + workload_factor + stamina_penalty, 100)
    
    # Показ статусу вгорі
    with col_status:
        st.write("### Статус гравця:")
        if injury_risk >= 75:
            st.error("🚨 КРИТИЧНИЙ РИЗИК. Потрібен відпочинок.")
        elif injury_risk >= 40:
            st.warning("⚠️ В ЗОНІ РИЗИКУ. Обмежити навантаження.")
        else:
            st.success("✅ ОПТИМАЛЬНА ФОРМА. Готовий до гри.")

    with col_info:
        st.write("<br>", unsafe_allow_html=True) # Вирівнювання
        if workload >= 3: 
            st.error(f"🚨 **{workload} матчі за тиждень** — це серйозне перевантаження! Ризик м'язових травм зростає експоненційно.")
        elif workload == 2: 
            st.warning(f"⚠️ **{workload} матчі за тиждень** — підвищене навантаження. Організму потрібен час на регенерацію.")
        else: 
            st.success(f"✅ **{workload} матч(ів) за тиждень** — нормальний графік. Організм встигає відновлюватися.")

    st.divider()

    # 2. Детальна аналітика замість графіка
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.subheader("🎯 Загальний Ризик")
        
        # Визначаємо колір для прогрес-бару через HTML/CSS хак
        if injury_risk < 40:
            color = "green"
            risk_text = "Низький"
        elif injury_risk < 75:
            color = "orange"
            risk_text = "Середній"
        else:
            color = "red"
            risk_text = "Високий"
            
        st.markdown(f"<h2 style='text-align: center; color: {color};'>{injury_risk}%</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center;'>Рівень загрози: <b>{risk_text}</b></p>", unsafe_allow_html=True)
        st.progress(injury_risk / 100)

    with c2:
        st.subheader("📊 Фізіологічні метрики")
        st.caption("Фактори, що формують ризик")
        
        st.write("Базове навантаження на суглоби:")
        st.progress(min(base_risk, 100) / 100)
        
        st.write("Рівень накопиченої втоми:")
        st.progress(min(workload_factor * 2, 100) / 100)
        
        st.write("Дефіцит витривалості:")
        st.progress(min(stamina_penalty * 4, 100) / 100)

    with c3:
        st.subheader("💊 Протокол відновлення")
        st.caption("AI Рекомендації для медштабу")
        
        if injury_risk >= 75:
            st.error("🛑 Відсторонити від тренувань на 48 годин.")
            st.write("✅ **Фізіотерапія:** Кріотерапія, глибокий масаж.")
            st.write("✅ **Тренування:** Повний спокій.")
        elif injury_risk >= 40:
            st.warning("⏳ Застосувати протокол часткового відновлення.")
            st.write(f"✅ **Дієта:** {random.choice(['Збільшити споживання вуглеводів', 'Додати ізотоніки та магній'])}.")
            st.write("✅ **Тренування:** Легке кардіо (велотренажер), розтяжка.")
        else:
            st.success("💪 Спеціальні заходи не потрібні.")
            st.write("✅ **Сон:** Не менше 8 годин.")
            st.write("✅ **Тренування:** В загальній групі, 100% інтенсивність.")

# ==========================================
# 8. ІСТОРІЯ ФОРМИ (Time-Series)
# ==========================================
def render_form_history():
    st.title("📈 Історія форми (Time-Series аналіз)")
    df = st.session_state.athletes_db
    
    if df.empty:
        st.warning("База даних порожня. Завантажте або додайте гравців.")
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
    st.info("💡 *Наразі застосунок генерує ці історичні дані автоматично на основі поточних статичних показників гравця для демонстрації Time-Series аналітики.*")

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
# 9. РЕСУРСИ ТА ОСВІТА
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
        st.success("**Robot Dreams** — Стаття: Як перетворити дані на результати.")
        st.link_button("Читати статтю", "https://robotdreams.cc/uk/blog/384-data-analiz-u-sporti-yak-peretvoriti-dani-na-rezultati")
        st.divider()
        st.success("**Наукова робота** — Використання інформаційних технологій у спорті.")
        st.link_button("Відкрити публікацію", "https://enpuir.udu.edu.ua/entities/publication/c7becbfd-8d2c-4566-89f4-9a85d3c3062a")

# ==========================================
# 10. ЕКСПОРТ
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
