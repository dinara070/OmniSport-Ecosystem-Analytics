import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import io

# Налаштування сторінки
st.set_page_config(page_title="OmniSport: Analytics & Physics", layout="wide")

# Ініціалізація бази даних (в пам'яті для MVP)
if 'athletes_db' not in st.session_state:
    st.session_state.athletes_db = pd.DataFrame(
        columns=["Ім'я", "Вид спорту", "Матчі", "Очки", "Середня швидкість (км/год)"]
    )

def main():
    st.title("🏆 OmniSport: Ecosystem & Analytics")
    st.markdown("Інтегрована платформа для управління, аналітики та біомеханіки.")

    # Бокова панель для навігації
    menu = ["Управління (CRM)", "Аналітика", "Лабораторія Фізики", "Імпорт/Експорт"]
    choice = st.sidebar.selectbox("Навігація", menu)

    if choice == "Управління (CRM)":
        render_crm()
    elif choice == "Аналітика":
        render_analytics()
    elif choice == "Лабораторія Фізики":
        render_physics()
    elif choice == "Імпорт/Експорт":
        render_io()

# ==========================================
# БЛОК 1: УПРАВЛІННЯ (CRM)
# ==========================================
def render_crm():
    st.header("👥 Менеджмент спортсменів")
    
    with st.form("add_athlete_form"):
        st.subheader("Додати нового спортсмена")
        col1, col2 = st.columns(2)
        name = col1.text_input("Ім'я гравця")
        sport = col2.selectbox("Вид спорту", ["Волейбол", "Футбол", "Біг"])
        
        col3, col4, col5 = st.columns(3)
        matches = col3.number_input("Кількість матчів/забігів", min_value=0, step=1)
        score = col4.number_input("Очки/Голи", min_value=0, step=1)
        speed = col5.number_input("Сер. швидкість (км/год)", min_value=0.0, step=0.1)
        
        submit = st.form_submit_button("Додати в базу")
        
        if submit and name:
            new_data = pd.DataFrame({
                "Ім'я": [name], "Вид спорту": [sport], "Матчі": [matches], 
                "Очки": [score], "Середня швидкість (км/год)": [speed]
            })
            st.session_state.athletes_db = pd.concat([st.session_state.athletes_db, new_data], ignore_index=True)
            st.success(f"Гравця {name} успішно додано!")

    st.subheader("Поточний склад")
    st.dataframe(st.session_state.athletes_db, use_container_width=True)

# ==========================================
# БЛОК 2: АНАЛІТИКА
# ==========================================
def render_analytics():
    st.header("📊 Спортивна Аналітика")
    df = st.session_state.athletes_db
    
    if df.empty:
        st.warning("База даних порожня. Додайте спортсменів у розділі CRM.")
        return

    sport_filter = st.selectbox("Фільтр за видом спорту", ["Всі"] + list(df["Вид спорту"].unique()))
    if sport_filter != "Всі":
        df = df[df["Вид спорту"] == sport_filter]

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Результативність (Очки/Голи)")
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(df["Ім'я"], df["Очки"], color='#4CAF50')
        plt.xticks(rotation=45)
        st.pyplot(fig)

    with col2:
        st.subheader("Швидкісні показники")
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(df["Ім'я"], df["Середня швидкість (км/год)"], marker='o', linestyle='-', color='#2196F3')
        plt.xticks(rotation=45)
        ax.grid(True, linestyle='--', alpha=0.7)
        st.pyplot(fig)

# ==========================================
# БЛОК 3: ФІЗИКА ТА БІОМЕХАНІКА
# ==========================================
def render_physics():
    st.header("⚛️ Біомеханіка: Аналіз траєкторії")
    st.markdown("Симуляція удару (подача у волейболі або штрафний у футболі) з урахуванням кінематики.")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Параметри удару")
        v0 = st.slider("Початкова швидкість ($v_0$, м/с)", 10.0, 40.0, 20.0)
        angle_deg = st.slider("Кут вильоту ($\\theta$, градуси)", 10.0, 80.0, 45.0)
        h0 = st.slider("Початкова висота ($h_0$, метри)", 0.0, 3.5, 0.0)
        
    with col2:
        # Фізичні розрахунки
        g = 9.81
        angle_rad = np.radians(angle_deg)
        
        # Час польоту (з розв'язання квадратного рівняння для y=0)
        t_flight = (v0 * np.sin(angle_rad) + np.sqrt((v0 * np.sin(angle_rad))**2 + 2 * g * h0)) / g
        
        t = np.linspace(0, t_flight, num=100)
        x = v0 * np.cos(angle_rad) * t
        
        # Рівняння траєкторії
        y = h0 + x * np.tan(angle_rad) - (g * x**2) / (2 * v0**2 * np.cos(angle_rad)**2)
        
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(x, y, label="Траєкторія м'яча", color="red", linewidth=2)
        ax.axhline(0, color='black', linewidth=1)
        ax.set_xlabel("Дистанція (м)")
        ax.set_ylabel("Висота (м)")
        ax.set_title(f"Дальність польоту: {x[-1]:.2f} м")
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
        st.pyplot(fig)

# ==========================================
# БЛОК 4: ІМПОРТ ТА ЕКСПОРТ (УСІ ФОРМАТИ)
# ==========================================
def render_io():
    st.header("💾 Імпорт та Експорт даних")
    df = st.session_state.athletes_db

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Експорт бази")
        
        # Експорт у CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Завантажити як CSV", data=csv, file_name='omnisport_data.csv', mime='text/csv')
        
        # Експорт у JSON
        json_str = df.to_json(orient='records', force_ascii=False)
        st.download_button(label="📥 Завантажити як JSON", data=json_str, file_name='omnisport_data.json', mime='application/json')

    with col2:
        st.subheader("Імпорт бази")
        uploaded_file = st.file_uploader("Завантажити файл", type=['csv', 'json'])
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    imported_df = pd.read_csv(uploaded_file)
                elif uploaded_file.name.endswith('.json'):
                    imported_df = pd.read_json(uploaded_file)
                
                if st.button("Оновити базу даними з файлу"):
                    st.session_state.athletes_db = imported_df
                    st.success("Базу успішно оновлено!")
                    st.dataframe(st.session_state.athletes_db)
            except Exception as e:
                st.error(f"Помилка зчитування файлу: {e}")

if __name__ == "__main__":
    main()
