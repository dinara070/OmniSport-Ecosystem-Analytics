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

# ДОДАНО: поле "Вік"
DEFAULT_DATA = pd.DataFrame({
    "Ім'я": ["Олександр", "Марія", "Іван", "Анна"],
    "Вік": [24, 21, 26, 23], 
    "Вид спорту": ["Футбол", "Волейбол", "Біг", "Теніс"],
    "Матчі": [12, 15, 8, 20],
    "Очки": [5, 45, 0, 80],
    "Швидкість": [28.5, 22.0, 32.1, 25.0],
    "Витривалість": [85, 70, 95, 40],
    "Сила": [75, 85, 60, 70],
    "Навантаження_7днів": [2, 3, 1, 4]  # кількість матчів за тиждень
})

if 'athletes_db' not in st.session_state:
    st.session_state.athletes_db = DEFAULT_DATA.copy()

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
        st.caption("Performance Analytics v9.0")
        st.divider()

        # Завантаження власного файлу
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

                    required_cols = ["Ім'я", "Вік", "Вид спорту", "Матчі", "Очки", "Швидкість", "Витривалість", "Сила"]
                    missing = [c for c in required_cols if c not in df_upload.columns]

                    if missing:
                        st.error(f"Відсутні колонки: {', '.join(missing)}")
                    else:
                        if 'Навантаження_7днів' not in df_upload.columns:
                            df_upload['Навантаження_7днів'] = 0
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
            "📊 Командна аналітика", # НОВИЙ РОУТ
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
    elif choice == "📊 Командна аналітика": render_team_analytics() # НОВА ВКЛАДКА
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
    df = st.session_state.athletes_db

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Всього спортсменів", len(df))
    c2.metric("Макс. швидкість", f"{df['Швидкість'].max()} км/год")
    c3.metric("Топ Витривалість", df['Витривалість'].max())
    c4.metric("Топ Рейтинг (PER)", df['PER (Рейтинг)'].max())

    st.divider()
    st.subheader("📊 Загальний рейтинг команди")
    st.dataframe(
        df.sort_values(by="PER (Рейтинг)", ascending=False)
        .style.background_gradient(cmap='Blues', subset=['PER (Рейтинг)']),
        use_container_width=True
    )

# ==========================================
# 1.5 КОМАНДНА АНАЛІТИКА (TEAM VIEW) — НОВА ФІЧА
# ==========================================
def render_team_analytics():
    st.title("📊 Командна аналітика (Team View)")
    df = st.session_state.athletes_db

    if df.empty:
        st.warning("Немає даних для аналізу.")
        return

    # Загальні метрики команди
    c1, c2, c3 = st.columns(3)
    
    avg_age = df['Вік'].mean()
    c1.metric("Середній вік команди", f"{avg_age:.1f} років")

    avg_speed = df['Швидкість'].mean()
    ideal_speed = 30.0 # Встановлений еталон
    delta_speed = round(avg_speed - ideal_speed, 1)
    # Колір дельти: зелений якщо швидше еталона, червоний якщо повільніше
    c2.metric("Середня швидкість", f"{avg_speed:.1f} км/год", f"{delta_speed} км/год від ідеалу (30)")

    avg_per = df['PER (Рейтинг)'].mean()
    c3.metric("Середній командний PER", f"{avg_per:.1f}")

    st.divider()

    col_pie, col_bar = st.columns(2)

    with col_pie:
        st.subheader("Розподіл за видами спорту")
        sport_counts = df['Вид спорту'].value_counts()
        
        # Створення кругової діаграми
        fig1, ax1 = plt.subplots(figsize=(6, 4))
        wedges, texts, autotexts = ax1.pie(
            sport_counts, 
            labels=sport_counts.index, 
            autopct='%1.1f%%', 
            startangle=90, 
            colors=plt.cm.Pastel1.colors,
            textprops=dict(color="w") # Білий текст для кращого контрасту в темній темі
        )
        # Змінюємо колір зовнішніх лейблів, якщо потрібно
        for text in texts:
            text.set_color('white') # Можна адаптувати під світлу/темну тему
            
        ax1.axis('equal') 
        fig1.patch.set_alpha(0.0) # Прозорий фон
        st.pyplot(fig1)

    with col_bar:
        st.subheader("Поточні показники vs Ідеал")
        
        # Підготовка даних для порівняльної діаграми
        avg_stats = pd.DataFrame({
            "Показник": ["Витривалість", "Сила", "Швидкість"],
            "Команда": [df['Витривалість'].mean(), df['Сила'].mean(), df['Швидкість'].mean()],
            "Ідеал": [85.0, 80.0, ideal_speed]
        }).set_index("Показник")

        # Відображення групованої стовпчикової діаграми
        st.bar_chart(avg_stats, color=["#448AFF", "#FF5252"])

# ==========================================
# 2. БАЗА ГРАВЦІВ (CRM)
# ==========================================
def render_crm():
    st.title("👥 Управління складом")
    with st.expander("➕ Додати нового спортсмена", expanded=False):
        with st.form("add_form"):
            c1, c_age, c2 = st.columns([2, 1, 2])
            name = c1.text_input("Ім'я")
            age = c_age.number_input("Вік", min_value=14, max_value=60, value=20)
            sport = c2.selectbox("Вид спорту", ["Волейбол", "Футбол", "Біг", "Теніс"])

            c3, c4, c5, c6, c7, c8 = st.columns(6)
            matches = c3.number_input("Матчі", min_value=0)
            score = c4.number_input("Очки", min_value=0)
            speed = c5.number_input("Швидк. (км/год)", 0.0, 50.0, 20.0)
            stamina = c6.number_input("Витривал.", 0, 100, 50)
            power = c7.number_input("Сила", 0, 100, 50)
            workload = c8.number_input("Матчів/тиж.", 0, 7, 0)

            if st.form_submit_button("Зберегти гравця"):
                new_row = pd.DataFrame({
                    "Ім'я": [name], "Вік": [age], "Вид спорту": [sport], "Матчі": [matches],
                    "Очки": [score], "Швидкість": [speed], "Витривалість": [stamina],
                    "Сила": [power], "Навантаження_7днів": [workload]
                })
                st.session_state.athletes_db = pd.concat([st.session_state.athletes_db, new_row], ignore_index=True)
                st.success(f"Спортсмена {name} успішно додано!")
                st.rerun()

    st.dataframe(st.session_state.athletes_db, use_container_width=True)

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
        st.info(f"**{p1_name} ({p1_data['Вік']} р.)**: " + ("Лідер швидкості" if p1_data['Швидкість'] > 28 else "Витривалий боєць"))
        if p1_name != p2_name:
            st.info(f"**{p2_name} ({p2_data['Вік']} р.)**: " + ("Лідер швидкості" if p2_data['Швидкість'] > 28 else "Витривалий боєць"))

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
    df = st.session_state.athletes_db
    c1, _, c2 = st.columns([2, 0.5, 2])

    p1 = c1.selectbox("🔴 Гравець 1", df["Ім'я"], key="s1")
    p2 = c2.selectbox("🔵 Гравець 2", df["Ім'я"], index=min(1, len(df)-1), key="s2")

    if st.button("🚀 Почати симуляцію", use_container_width=True):
        p1_data = df[df["Ім'я"] == p1].iloc[0]
        p2_data = df[df["Ім'я"] == p2].iloc[0]

        per1 = p1_data['PER (Рейтинг)']
        per2 = p2_data['PER (Рейтинг)']

        with st.spinner("Симуляція матчу..."):
            time.sleep(1)

        log = []
        score1, score2 = 0, 0
        minutes = sorted(random.sample(range(1, 91), random.randint(6, 10)))

        event_templates = {
            "гол": ["{player} влучив у ворота!", "{player} реалізував штрафний удар!", "{player} головою відправив м'яч у сітку!", "{player} забив з-за меж штрафної!"],
            "обіграв": ["{player} обіграв суперника на швидкості {speed:.1f} км/год.", "{player} зробив ключний дриблінг."],
            "захист": ["{player} перехопив небезпечну передачу.", "{player} відбив удар на останніх секундах!"],
            "пас": ["{player} зробив ключний пас у штрафну зону.", "{player} розпочав небезпечну атаку."],
            "карточка": ["{player} отримав жовту картку за грубий фол.", "{player} зупинив атаку ціною жовтої картки."]
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
        col_sc1, col_vs, col_sc2 = st.columns([2, 1, 2])
        col_sc1.markdown(f"### 🔴 {p1}")
        col_sc1.metric("Голи", score1)
        col_vs.markdown("## VS", unsafe_allow_html=False)
        col_sc2.markdown(f"### 🔵 {p2}")
        col_sc2.metric("Голи", score2)

        if winner_pen:
            st.warning(f"⏱️ Основний час — нічия {score1}:{score2}. Перемога по PER: **{winner}**!")
        else:
            st.balloons()
            st.success(f"🏆 Переможець: **{winner}** ({score1}:{score2})")

        st.divider()
        st.subheader("📋 Лог матчу")
        for event in st.session_state.match_log:
            col_m, col_i, col_e, col_s = st.columns([1, 0.5, 6, 1.5])
            col_m.write(f"**{event['хв']}'**")
            col_i.write(event['icon'])
            col_e.write(event['подія'])
            col_s.write(f"`{event['рахунок']}`")

    elif st.session_state.match_log:
        st.info("Попередній матч збережено. Натисніть «Симуляцію» для нового.")
        st.subheader("📋 Лог попереднього матчу")
        for event in st.session_state.match_log:
            col_m, col_i, col_e, col_s = st.columns([1, 0.5, 6, 1.5])
            col_m.write(f"**{event['хв']}'**")
            col_i.write(event['icon'])
            col_e.write(event['подія'])
            col_s.write(f"`{event['рахунок']}`")

# ==========================================
# 7. ПРОГНОЗ ТРАВМАТИЗМУ
# ==========================================
def render_injury_prediction():
    st.title("🩹 AI Health Monitor")
    df = st.session_state.athletes_db
    selected_player = st.selectbox("Оберіть гравця для чекапу:", df["Ім'я"])
    player_data = df[df["Ім'я"] == selected_player].iloc[0]

    st.divider()
    col_edit, col_info = st.columns([1, 2])
    with col_edit:
        st.subheader("📅 Навантаження за тиждень")
        workload = st.number_input("Кількість матчів за останні 7 днів", min_value=0, max_value=7, value=int(player_data.get('Навантаження_7днів', 0)), key="workload_input")
        st.session_state.athletes_db.loc[st.session_state.athletes_db["Ім'я"] == selected_player, 'Навантаження_7днів'] = workload

    with col_info:
        if workload >= 3: st.error(f"🚨 **{workload} матчі поспіль** — перевантаження! Ризик травми автоматично підвищено до КРИТИЧНОГО рівня.")
        elif workload == 2: st.warning(f"⚠️ **{workload} матчі за тиждень** — підвищене навантаження. Стежте за відновленням.")
        else: st.success(f"✅ **{workload} матч(ів) за тиждень** — нормальне навантаження.")

    st.divider()
    imbalance = abs(player_data['Сила'] - player_data['Витривалість'])
    base_risk = int((imbalance * 1.5) + (player_data['Швидкість'] * 0.5))
    
    if workload >= 3: workload_factor = 40
    elif workload == 2: workload_factor = 20
    else: workload_factor = 0

    if player_data['Витривалість'] < 50: stamina_penalty = 15
    else: stamina_penalty = 0

    injury_risk = min(base_risk + workload_factor + stamina_penalty, 100)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("🎯 Ризик травми")
        if injury_risk < 40:
            st.success(f"**Низький: {injury_risk}%**")
            st.progress(injury_risk / 100)
        elif injury_risk < 75:
            st.warning(f"**Середній: {injury_risk}%**")
            st.progress(injury_risk / 100)
        else:
            st.error(f"**КРИТИЧНИЙ: {injury_risk}%**")
            st.progress(injury_risk / 100)

    with c2:
        st.subheader("📊 Фактори ризику")
        factors = {"Базовий ризик": base_risk, "Навантаження (+)": workload_factor, "Виснаження (+)": stamina_penalty}
        factor_df = pd.DataFrame.from_dict(factors, orient='index', columns=['Значення'])
        st.bar_chart(factor_df)

    with c3:
        st.subheader("💊 Відновлення")
        if workload >= 3: st.error("🛑 **Обов'язковий відпочинок 48 год!**")
        st.write(f"**Дієта:** {random.choice(['Більше білка', 'Магній+', 'Гідратація'])}")
        st.write("**Сон:** 8.5 год")
        if player_data['Витривалість'] < 60: st.write("**Тренування:** Легке кардіо, без контакту")
        else: st.write("**Тренування:** Стандартний план")

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
