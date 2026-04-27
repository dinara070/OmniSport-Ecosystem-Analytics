import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Налаштування сторінки
st.set_page_config(page_title="OmniSport Pro", layout="wide", initial_sidebar_state="expanded")

# Ініціалізація бази даних
if 'athletes_db' not in st.session_state:
    st.session_state.athletes_db = pd.DataFrame({
        "Ім'я": ["Олександр", "Марія", "Іван", "Анна"],
        "Вид спорту": ["Футбол", "Волейбол", "Біг", "Теніс"],
        "Матчі": [12, 15, 8, 20],
        "Очки": [5, 45, 0, 80],
        "Швидкість": [28.5, 22.0, 32.1, 25.0],
        "Витривалість": [85, 70, 95, 40],
        "Сила": [75, 85, 60, 70]
    })

def calculate_per(row):
    base = (row['Швидкість'] * 1.5) + (row['Витривалість'] * 0.8) + (row['Сила'] * 0.9)
    bonus = row['Очки'] * 2 if row['Матчі'] > 0 else 0
    return round((base + bonus) / 3, 1)

def main():
    with st.sidebar:
        st.title("🏆 OmniSport Pro")
        st.caption("Performance Analytics v4.0 (Ultimate)")
        st.divider()
        menu = [
            "🏠 Дашборд", 
            "👥 База гравців", 
            "⚔️ H2H Батл (Скаутинг)", 
            "🗺️ Тактика та Теплова карта", # НОВИЙ РОЗДІЛ
            "⚛️ Лабораторія Фізики", 
            "💾 Експорт Даних"
        ]
        choice = st.radio("Навігація", menu)
        st.divider()
        st.info(f"Активних гравців: **{len(st.session_state.athletes_db)}**")

    if choice == "🏠 Дашборд":
        render_dashboard()
    elif choice == "👥 База гравців":
        render_crm()
    elif choice == "⚔️ H2H Батл (Скаутинг)":
        render_scouting()
    elif choice == "🗺️ Тактика та Теплова карта":
        render_tactics()
    elif choice == "⚛️ Лабораторія Фізики":
        render_physics()
    elif choice == "💾 Експорт Даних":
        render_io()

# ==========================================
# 1. ДАШБОРД
# ==========================================
def render_dashboard():
    st.title("🏠 Аналітична панель")
    df = st.session_state.athletes_db
    df['PER (Рейтинг)'] = df.apply(calculate_per, axis=1)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Всього спортсменів", len(df))
    c2.metric("Макс. швидкість", f"{df['Швидкість'].max()} км/год")
    c3.metric("Топ Витривалість", df['Витривалість'].max())
    c4.metric("Топ Рейтинг (PER)", df['PER (Рейтинг)'].max())
    
    st.divider()
    st.subheader("📊 Загальний рейтинг команди")
    st.dataframe(df.sort_values(by="PER (Рейтинг)", ascending=False).style.background_gradient(cmap='Blues', subset=['PER (Рейтинг)']), use_container_width=True)

# ==========================================
# 2. БАЗА ГРАВЦІВ (CRM)
# ==========================================
def render_crm():
    st.title("👥 Управління складом")
    with st.expander("➕ Додати нового спортсмена", expanded=False):
        with st.form("add_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Ім'я")
            sport = c2.selectbox("Вид спорту", ["Волейбол", "Футбол", "Біг", "Теніс"])
            
            c3, c4, c5, c6, c7 = st.columns(5)
            matches = c3.number_input("Матчі", min_value=0)
            score = c4.number_input("Очки", min_value=0)
            speed = c5.number_input("Швидк. (км/год)", 0.0, 50.0, 20.0)
            stamina = c6.number_input("Витривал. (0-100)", 0, 100, 50)
            power = c7.number_input("Сила (0-100)", 0, 100, 50)
            
            if st.form_submit_button("Зберегти гравця"):
                new_row = pd.DataFrame({"Ім'я": [name], "Вид спорту": [sport], "Матчі": [matches], 
                                      "Очки": [score], "Швидкість": [speed], "Витривалість": [stamina], "Сила": [power]})
                st.session_state.athletes_db = pd.concat([st.session_state.athletes_db, new_row], ignore_index=True)
                st.success(f"Спортсмена {name} успішно додано!")

    st.dataframe(st.session_state.athletes_db, use_container_width=True)

# ==========================================
# 3. H2H СКАУТИНГ
# ==========================================
def render_scouting():
    st.title("⚔️ Head-to-Head: Порівняння гравців")
    df = st.session_state.athletes_db
    
    c1, c2 = st.columns(2)
    with c1:
        p1_name = st.selectbox("🔴 Гравець 1", df["Ім'я"])
    with c2:
        default_index = 1 if len(df) > 1 else 0
        p2_name = st.selectbox("🔵 Гравець 2", df["Ім'я"], index=default_index)

    p1_data = df[df["Ім'я"] == p1_name].iloc[0]
    p2_data = df[df["Ім'я"] == p2_name].iloc[0]

    col_radar, col_text = st.columns([2, 1])
    with col_radar:
        categories = ['Витривалість', 'Сила', 'Швидкість', 'Очки', 'Матчі']
        N = len(categories)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]
        
        def get_radar_values(player):
            vals = [player['Витривалість'], player['Сила'], min(int((player['Швидкість'] / 40) * 100), 100), min(player['Очки'] * 5, 100), min(player['Матчі'] * 5, 100)]
            vals += vals[:1]
            return vals

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        plt.xticks(angles[:-1], categories, size=10)
        ax.set_rlabel_position(0)
        plt.yticks([20, 40, 60, 80], ["20", "40", "60", "80"], color="grey", size=8)
        plt.ylim(0, 100)

        val1 = get_radar_values(p1_data)
        ax.plot(angles, val1, linewidth=2, linestyle='solid', label=p1_name, color='#FF5252')
        ax.fill(angles, val1, '#FF5252', alpha=0.25)

        if p1_name != p2_name:
            val2 = get_radar_values(p2_data)
            ax.plot(angles, val2, linewidth=2, linestyle='solid', label=p2_name, color='#448AFF')
            ax.fill(angles, val2, '#448AFF', alpha=0.25)

        plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        st.pyplot(fig)
        
    with col_text:
        st.subheader("📈 Швидкий висновок")
        st.info(f"**{p1_name}**: Сильна сторона — " + ("Швидкість" if p1_data['Швидкість'] > 25 else "Витривалість"))
        if p1_name != p2_name:
            st.info(f"**{p2_name}**: Сильна сторона — " + ("Швидкість" if p2_data['Швидкість'] > 25 else "Витривалість"))

# ==========================================
# 4. ТАКТИКА ТА ТЕПЛОВА КАРТА (НОВА ФІЧА!)
# ==========================================
def render_tactics():
    st.title("🗺️ Тактика та AI-Тренер")
    st.markdown("Аналіз пересувань гравця на полі та автоматична генерація тренувального плану.")
    
    df = st.session_state.athletes_db
    selected_player = st.selectbox("Оберіть гравця для тактичного розбору:", df["Ім'я"])
    player_data = df[df["Ім'я"] == selected_player].iloc[0]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔥 Теплова карта активності (Heatmap)")
        
        # Малюємо спортивне поле
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.set_facecolor('#2E7D32') # Зелений колір газону
        
        # Контури поля
        ax.plot([0, 0, 100, 100, 0], [0, 60, 60, 0, 0], color='white', linewidth=2)
        ax.plot([50, 50], [0, 60], color='white', linewidth=2) # Центральна лінія
        ax.add_patch(plt.Circle((50, 30), 10, color="white", fill=False, linewidth=2)) # Центральне коло
        
        # Генерація даних для теплової карти (симуляція на основі характеристик)
        # Якщо гравець швидкий, радіус розкиду більший
        spread = 15 if player_data['Швидкість'] > 25 else 8
        x = np.random.normal(50, spread, 500)
        y = np.random.normal(30, spread + 5, 500)
        
        # Обмежуємо точки межами поля
        x = np.clip(x, 2, 98)
        y = np.clip(y, 2, 58)
        
        # Створення самої теплової карти
        hb = ax.hexbin(x, y, gridsize=20, cmap='YlOrRd', alpha=0.7, mincnt=1)
        
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"Зони найбільшої присутності: {selected_player}", color="white", pad=15)
        
        # Темний фон для всієї картинки, щоб виглядало стильно
        fig.patch.set_facecolor('#1E1E1E')
        st.pyplot(fig)
        
    with col2:
        st.subheader("🏋️ План від AI-Тренера")
        
        # Проста логіка генерації плану тренувань
        weakness = "None"
        if player_data['Витривалість'] < 60:
            weakness = "Витривалість"
        elif player_data['Сила'] < 60:
            weakness = "Сила"
        elif player_data['Швидкість'] < 20:
            weakness = "Швидкість"
            
        if weakness == "Витривалість":
            st.error("⚠️ Виявлено критичну зону: Низька витривалість.")
            st.markdown("""
            **План на тиждень:**
            * **Пн:** Крос 5 км (легкий темп)
            * **Ср:** Інтервальний біг (4х400м)
            * **Пт:** Плавання (45 хв)
            * **Нд:** Відпочинок або розтяжка
            """)
        elif weakness == "Сила":
            st.warning("⚠️ Виявлено критичну зону: Нестача фізичної сили.")
            st.markdown("""
            **План на тиждень:**
            * **Вт:** Тренажерний зал (Присідання, станова)
            * **Чт:** Пліометрика (стрибки на тумбу)
            * **Сб:** Робота з власною вагою (TRX)
            """)
        elif weakness == "Швидкість":
            st.info("⚠️ Виявлено критичну зону: Брак вибухової швидкості.")
            st.markdown("""
            **План на тиждень:**
            * **Пн:** Спринти 10х30 метрів
            * **Ср:** Вправи на координаційній драбині
            * **Пт:** Човниковий біг
            """)
        else:
            st.success("✅ Гравець має збалансовані показники.")
            st.markdown("""
            **План на тиждень:**
            * Підтримуючі командні тренування.
            * Фокус на тактиці (перегляд відеозаписів ігор).
            """)

# ==========================================
# 5. ЛАБОРАТОРІЯ ФІЗИКИ
# ==========================================
def render_physics():
    st.title("⚛️ Інтерактивна Біомеханіка")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Налаштування удару")
        v0 = st.slider("Швидкість ($v_0$, м/с)", 10.0, 40.0, 22.0)
        angle_deg = st.slider("Кут вильоту ($\\theta$, градуси)", 10.0, 80.0, 35.0)
        h0 = st.slider("Початкова висота ($h_0$, метри)", 0.0, 3.5, 1.2)
        
    with col2:
        g = 9.81
        angle_rad = np.radians(angle_deg)
        t_flight = (v0 * np.sin(angle_rad) + np.sqrt((v0 * np.sin(angle_rad))**2 + 2 * g * h0)) / g
        
        t = np.linspace(0, t_flight, num=100)
        x = v0 * np.cos(angle_rad) * t
        y = h0 + x * np.tan(angle_rad) - (g * x**2) / (2 * v0**2 * np.cos(angle_rad)**2)
        
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(x, y, color="#00BCD4", linewidth=3)
        ax.fill_between(x, y, 0, color='#00BCD4', alpha=0.15)
        ax.axhline(0, color='gray', linestyle='--', linewidth=1.5)
        
        ax.set_title(f"Точка падіння: {x[-1]:.2f} метрів", fontsize=14, pad=10)
        ax.set_xlabel("Дистанція (метри)")
        ax.set_ylabel("Висота (метри)")
        ax.grid(True, linestyle=':', alpha=0.7)
        st.pyplot(fig)

# ==========================================
# 6. ДАНІ
# ==========================================
def render_io():
    st.title("💾 Експорт Даних")
    df = st.session_state.athletes_db
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📥 Завантажити CSV", df.to_csv(index=False).encode('utf-8'), "omnisport_data.csv", "text/csv")
    with c2:
        st.download_button("📥 Завантажити JSON", df.to_json(orient='records', force_ascii=False), "omnisport_data.json", "application/json")

if __name__ == "__main__":
    main()
