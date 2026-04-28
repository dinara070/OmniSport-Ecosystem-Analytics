import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import random

# ==========================================
# 0. КОНФІГУРАЦІЯ ТА ДАНІ
# ==========================================

st.set_page_config(page_title="OmniSport Pro", layout="wide", initial_sidebar_state="expanded")

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
    """Розрахунок рейтингу ефективності (Player Efficiency Rating)"""
    base = (row['Швидкість'] * 1.5) + (row['Витривалість'] * 0.8) + (row['Сила'] * 0.9)
    bonus = row['Очки'] * 2 if row['Матчі'] > 0 else 0
    return round((base + bonus) / 3, 1)

# ==========================================
# ГОЛОВНА ЛОГІКА
# ==========================================

def main():
    # Актуалізуємо рейтинг PER
    st.session_state.athletes_db['PER (Рейтинг)'] = st.session_state.athletes_db.apply(calculate_per, axis=1)

    with st.sidebar:
        st.title("🏆 OmniSport Pro")
        st.caption("Performance Analytics v6.0")
        st.divider()
        menu = [
            "🏠 Дашборд", 
            "👥 База гравців", 
            "⚔️ H2H Батл (Скаутинг)", 
            "🗺️ Тактика та Теплова карта", 
            "⚛️ Лабораторія Фізики",
            "🎲 AI-Симулятор Матчів",
            "🩹 Прогноз Травматизму",
            "💾 Експорт Даних"
        ]
        choice = st.radio("Навігація", menu)
        st.divider()
        st.info(f"Активних гравців: **{len(st.session_state.athletes_db)}**")

    # Роутинг сторінок
    if choice == "🏠 Дашборд": render_dashboard()
    elif choice == "👥 База гравців": render_crm()
    elif choice == "⚔️ H2H Батл (Скаутинг)": render_scouting()
    elif choice == "🗺️ Тактика та Теплова карта": render_tactics()
    elif choice == "⚛️ Лабораторія Фізики": render_physics()
    elif choice == "🎲 AI-Симулятор Матчів": render_simulator()
    elif choice == "🩹 Прогноз Травматизму": render_injury_prediction()
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
                new_row = pd.DataFrame({
                    "Ім'я": [name], "Вид спорту": [sport], "Матчі": [matches], 
                    "Очки": [score], "Швидкість": [speed], "Витривалість": [stamina], "Сила": [power]
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
        st.info(f"**{p1_name}**: " + ("Лідер швидкості" if p1_data['Швидкість'] > 28 else "Витривалий боєць"))
        if p1_name != p2_name:
            st.info(f"**{p2_name}**: " + ("Лідер швидкості" if p2_data['Швидкість'] > 28 else "Витривалий боєць"))

# ==========================================
# 4. ТАКТИКА
# ==========================================
def render_tactics():
    st.title("🗺️ Тактика та AI-Тренер")
    df = st.session_state.athletes_db
    selected_player = st.selectbox("Оберіть гравця:", df["Ім'я"])
    player_data = df[df["Ім'я"] == selected_player].iloc[0]
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader(f"🔥 Зони активності: {selected_player}")
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.set_facecolor('#2E7D32')
        ax.plot([0, 0, 100, 100, 0], [0, 60, 60, 0, 0], color='white')
        ax.plot([50, 50], [0, 60], color='white')
        
        spread = 20 if player_data['Витривалість'] > 75 else 10
        x = np.random.normal(50, spread, 500)
        y = np.random.normal(30, 10, 500)
        ax.hexbin(x, y, gridsize=15, cmap='YlOrRd', alpha=0.7)
        st.pyplot(fig)
        
    with col2:
        st.subheader("🏋️ Поради AI")
        if player_data['Витривалість'] < 60: st.error("Потрібне кардіо!")
        else: st.success("Форма стабільна.")

# ==========================================
# 5. ЛАБОРАТОРІЯ ФІЗИКИ
# ==========================================
def render_physics():
    st.title("⚛️ Лабораторія Фізики")
    df = st.session_state.athletes_db
    player = st.selectbox("Оберіть спортсмена для симуляції:", df["Ім'я"])
    data = df[df["Ім'я"] == player].iloc[0]
    
    v0 = st.slider("Швидкість (м/с)", 5.0, 50.0, float(data['Сила']*0.4))
    angle = st.slider("Кут (°)", 10, 80, 35)
    
    g = 9.81
    rad = np.radians(angle)
    t_f = (2 * v0 * np.sin(rad)) / g
    t = np.linspace(0, t_f, 100)
    x = v0 * np.cos(rad) * t
    y = v0 * np.sin(rad) * t - 0.5 * g * t**2
    
    fig, ax = plt.subplots()
    ax.plot(x, y, color="#00BCD4")
    st.pyplot(fig)

# ==========================================
# 6. СИМУЛЯТОР МАТЧІВ
# ==========================================
def render_simulator():
    st.title("🎲 AI-Симулятор Матчів")
    df = st.session_state.athletes_db
    c1, mid, c2 = st.columns([2, 0.5, 2])
    
    p1 = c1.selectbox("Гравець 1", df["Ім'я"], key="s1")
    p2 = c2.selectbox("Гравець 2", df["Ім'я"], index=1, key="s2")
    
    if st.button("🚀 Почати симуляцію", use_container_width=True):
        with st.spinner("Аналіз тактики..."):
            time.sleep(1)
            per1 = df[df["Ім'name"] == p1].iloc[0]['PER (Рейтинг)'] if "Ім'name" in df else df[df["Ім'я"] == p1].iloc[0]['PER (Рейтинг)']
            per2 = df[df["Ім'я"] == p2].iloc[0]['PER (Рейтинг)']
            
            s1 = per1 * random.uniform(0.8, 1.2)
            s2 = per2 * random.uniform(0.8, 1.2)
            
            winner = p1 if s1 > s2 else p2
            st.balloons()
            st.success(f"🏆 Переміг {winner}!")

# ==========================================
# 7. ПРОГНОЗ ТРАВМАТИЗМУ (NEW)
# ==========================================
def render_injury_prediction():
    st.title("🩹 AI Health Monitor")
    df = st.session_state.athletes_db
    selected_player = st.selectbox("Оберіть гравця для чекапу:", df["Ім'я"])
    player_data = df[df["Ім'я"] == selected_player].iloc[0]

    # Логіка ризику
    imbalance = abs(player_data['Сила'] - player_data['Витривалість'])
    injury_risk = min(int((imbalance * 1.5) + (player_data['Швидкість'] * 0.5)), 100)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("Ризик травми")
        if injury_risk < 40: st.success(f"Низький: {injury_risk}%")
        elif injury_risk < 75: st.warning(f"Середній: {injury_risk}%")
        else: st.error(f"ВИСОКИЙ: {injury_risk}%")

    with c2:
        st.subheader("Баланс")
        st.bar_chart([imbalance, player_data['Швидкість']])

    with c3:
        st.subheader("Відновлення")
        st.write(f"**Дієта:** {random.choice(['Більше білка', 'Магній+', 'Гідратація']) }")
        st.write("**Сон:** 8.5 год")

    st.divider()
    st.line_chart(np.random.randint(60, 100, 7))

# ==========================================
# 8. ЕКСПОРТ
# ==========================================
def render_io():
    st.title("💾 Експорт Даних")
    df = st.session_state.athletes_db
    st.download_button("📥 CSV", df.to_csv(index=False).encode('utf-8'), "data.csv")
    st.download_button("📥 JSON", df.to_json(orient='records'), "data.json")

if __name__ == "__main__":
    main()
