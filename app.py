import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import json

# Налаштування сторінки: широка версія і завжди відкрите меню зліва
st.set_page_config(page_title="OmniSport Pro", layout="wide", initial_sidebar_state="expanded")

# Ініціалізація розширеної бази даних
if 'athletes_db' not in st.session_state:
    st.session_state.athletes_db = pd.DataFrame({
        "Ім'я": ["Олександр", "Марія", "Іван"],
        "Вид спорту": ["Футбол", "Волейбол", "Біг"],
        "Матчі": [12, 15, 8],
        "Очки": [5, 45, 0],
        "Швидкість": [28.5, 22.0, 32.1],
        "Витривалість": [85, 70, 95], # Оцінка 0-100
        "Сила": [75, 85, 60]          # Оцінка 0-100
    })

def calculate_per(row):
    """Алгоритмічний розрахунок рейтингу гравця (Player Efficiency Rating)"""
    base = (row['Швидкість'] * 1.5) + (row['Витривалість'] * 0.8) + (row['Сила'] * 0.9)
    bonus = row['Очки'] * 2 if row['Матчі'] > 0 else 0
    return round((base + bonus) / 3, 1)

def main():
    # ==========================================
    # ЛІВА ПАНЕЛЬ (SIDEBAR)
    # ==========================================
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/5113/5113764.png", width=80)
        st.title("OmniSport Pro")
        st.caption("Ecosystem & Analytics v2.0")
        
        st.divider()
        menu = ["🏠 Дашборд", "👥 База гравців", "🕸️ Скаутинг (Радар)", "⚛️ Лабораторія Фізики", "💾 Дані"]
        choice = st.radio("Навігація", menu)
        
        st.divider()
        st.markdown("### 📊 Статус бази")
        st.info(f"Зареєстровано гравців: **{len(st.session_state.athletes_db)}**")
        
        st.markdown("### 💡 AI Порада")
        st.success("Аналіз показує, що збільшення кута вильоту на 2° покращить дальність подачі у волейболістів на 4%.")

    # Перемикач сторінок
    if choice == "🏠 Дашборд":
        render_dashboard()
    elif choice == "👥 База гравців":
        render_crm()
    elif choice == "🕸️ Скаутинг (Радар)":
        render_scouting()
    elif choice == "⚛️ Лабораторія Фізики":
        render_physics()
    elif choice == "💾 Дані":
        render_io()

# ==========================================
# 1. ДАШБОРД (Головна)
# ==========================================
def render_dashboard():
    st.title("🏠 Панель управління (Dashboard)")
    df = st.session_state.athletes_db
    
    # Вираховуємо PER для всіх
    df['PER (Рейтинг)'] = df.apply(calculate_per, axis=1)
    
    # Віджети з головними цифрами
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Всього спортсменів", len(df))
    col2.metric("Видів спорту", df["Вид спорту"].nunique())
    col3.metric("Макс. швидкість", f"{df['Швидкість'].max()} км/год")
    col4.metric("Топ Рейтинг (PER)", df['PER (Рейтинг)'].max())
    
    st.divider()
    st.subheader("🏆 Таблиця лідерів (Топ за рейтингом)")
    st.dataframe(df.sort_values(by="PER (Рейтинг)", ascending=False).style.background_gradient(cmap='viridis', subset=['PER (Рейтинг)']), use_container_width=True)

# ==========================================
# 2. БАЗА ГРАВЦІВ (CRM)
# ==========================================
def render_crm():
    st.title("👥 Управління складом")
    
    with st.expander("➕ Додати нового спортсмена", expanded=True):
        with st.form("add_form"):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("Ім'я")
            sport = c2.selectbox("Вид спорту", ["Волейбол", "Футбол", "Біг", "Теніс"])
            matches = c3.number_input("Матчі", min_value=0)
            
            c4, c5, c6, c7 = st.columns(4)
            score = c4.number_input("Очки/Голи", min_value=0)
            speed = c5.number_input("Швидкість (км/год)", 0.0, 50.0, 20.0)
            stamina = c6.slider("Витривалість (0-100)", 0, 100, 50)
            power = c7.slider("Сила (0-100)", 0, 100, 50)
            
            if st.form_submit_button("Зберегти гравця"):
                new_row = pd.DataFrame({"Ім'я": [name], "Вид спорту": [sport], "Матчі": [matches], 
                                      "Очки": [score], "Швидкість": [speed], "Витривалість": [stamina], "Сила": [power]})
                st.session_state.athletes_db = pd.concat([st.session_state.athletes_db, new_row], ignore_index=True)
                st.success("Додано!")

    st.dataframe(st.session_state.athletes_db, use_container_width=True)

# ==========================================
# 3. СКАУТИНГ (Та сама "Цікава фіча")
# ==========================================
def render_scouting():
    st.title("🕸️ AI Скаутинг: Профілі гравців")
    st.markdown("Візуальне порівняння характеристик спортсменів для прийняття тактичних рішень.")
    
    df = st.session_state.athletes_db
    player = st.selectbox("Оберіть гравця для аналізу:", df["Ім'я"])
    
    player_data = df[df["Ім'я"] == player].iloc[0]
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### " + player_data["Ім'я"])
        st.caption(f"Спорт: {player_data['Вид спорту']}")
        st.progress(int(player_data['Витривалість']), text=f"Витривалість: {player_data['Витривалість']}%")
        st.progress(int(player_data['Сила']), text=f"Сила: {player_data['Сила']}%")
        
        # Перераховуємо швидкість у відсотки (макс 40 км/год = 100%)
        speed_pct = min(int((player_data['Швидкість'] / 40) * 100), 100)
        st.progress(speed_pct, text=f"Швидкість: {player_data['Швидкість']} км/год")
        
    with col2:
        # Будуємо круту радарну діаграму через Plotly
        categories = ['Витривалість', 'Сила', 'Швидкість', 'Очки', 'Матчі']
        # Нормалізуємо значення для красивого графіку
        values = [player_data['Витривалість'], player_data['Сила'], speed_pct, 
                  min(player_data['Очки']*5, 100), min(player_data['Матчі']*5, 100)]
        
        fig = go.Figure(data=go.Scatterpolar(
          r=values,
          theta=categories,
          fill='toself',
          line_color='#FF5722'
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 4. ЛАБОРАТОРІЯ ФІЗИКИ
# ==========================================
def render_physics():
    st.title("⚛️ Біомеханічна лабораторія")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.info("Введіть параметри удару або кидка для розрахунку ідеальної траєкторії.")
        v0 = st.slider("Швидкість ($v_0$, м/с)", 10.0, 40.0, 22.0)
        angle_deg = st.slider("Кут вильоту ($\\theta$, градуси)", 10.0, 80.0, 35.0)
        h0 = st.slider("Висота удару ($h_0$, метри)", 0.0, 3.5, 1.2)
        
    with col2:
        g = 9.81
        angle_rad = np.radians(angle_deg)
        t_flight = (v0 * np.sin(angle_rad) + np.sqrt((v0 * np.sin(angle_rad))**2 + 2 * g * h0)) / g
        t = np.linspace(0, t_flight, num=100)
        x = v0 * np.cos(angle_rad) * t
        y = h0 + x * np.tan(angle_rad) - (g * x**2) / (2 * v0**2 * np.cos(angle_rad)**2)
        
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(x, y, color="#00BCD4", linewidth=3)
        ax.fill_between(x, y, 0, color='#00BCD4', alpha=0.1)
        ax.axhline(0, color='gray', linewidth=2)
        ax.set_title(f"Точка падіння: {x[-1]:.2f} метрів")
        ax.set_xlabel("Дистанція (м)"); ax.set_ylabel("Висота (м)")
        st.pyplot(fig)

# ==========================================
# 5. ДАНІ
# ==========================================
def render_io():
    st.title("💾 Синхронізація даних")
    df = st.session_state.athletes_db
    
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📥 Експорт CSV", df.to_csv(index=False).encode('utf-8'), "data.csv", "text/csv", use_container_width=True)
    with c2:
        st.download_button("📥 Експорт JSON", df.to_json(orient='records', force_ascii=False), "data.json", "application/json", use_container_width=True)

if __name__ == "__main__":
    main()
