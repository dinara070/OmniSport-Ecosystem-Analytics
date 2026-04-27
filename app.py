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
        "Витривалість": [85, 70, 95, 60],
        "Сила": [75, 85, 60, 70]
    })

def calculate_per(row):
    base = (row['Швидкість'] * 1.5) + (row['Витривалість'] * 0.8) + (row['Сила'] * 0.9)
    bonus = row['Очки'] * 2 if row['Матчі'] > 0 else 0
    return round((base + bonus) / 3, 1)

def main():
    with st.sidebar:
        st.title("🏆 OmniSport Pro")
        st.caption("Performance Analytics v3.1 (Stable)")
        st.divider()
        menu = ["🏠 Дашборд", "👥 База гравців", "⚔️ H2H Батл (Скаутинг)", "⚛️ Лабораторія Фізики", "💾 Експорт Даних"]
        choice = st.radio("Навігація", menu)
        st.divider()
        st.info(f"Активних гравців: **{len(st.session_state.athletes_db)}**")

    if choice == "🏠 Дашборд":
        render_dashboard()
    elif choice == "👥 База гравців":
        render_crm()
    elif choice == "⚔️ H2H Батл (Скаутинг)":
        render_scouting()
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
# 3. H2H СКАУТИНГ (MATPLOTLIB RADAR)
# ==========================================
def render_scouting():
    st.title("⚔️ Head-to-Head: Порівняння гравців")
    st.markdown("Оберіть двох гравців для прямого порівняння характеристик.")
    
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
        # Налаштування Радарної діаграми через Matplotlib
        categories = ['Витривалість', 'Сила', 'Швидкість', 'Очки', 'Матчі']
        N = len(categories)
        
        # Обчислення кутів для осей
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1] # Замикаємо коло
        
        def get_radar_values(player):
            vals = [
                player['Витривалість'], 
                player['Сила'], 
                min(int((player['Швидкість'] / 40) * 100), 100),
                min(player['Очки'] * 5, 100),
                min(player['Матчі'] * 5, 100)
            ]
            vals += vals[:1] # Замикаємо коло
            return vals

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        
        plt.xticks(angles[:-1], categories, size=10)
        ax.set_rlabel_position(0)
        plt.yticks([20, 40, 60, 80], ["20", "40", "60", "80"], color="grey", size=8)
        plt.ylim(0, 100)

        # Графік Гравця 1
        val1 = get_radar_values(p1_data)
        ax.plot(angles, val1, linewidth=2, linestyle='solid', label=p1_name, color='#FF5252')
        ax.fill(angles, val1, '#FF5252', alpha=0.25)

        # Графік Гравця 2 (якщо обрано іншого)
        if p1_name != p2_name:
            val2 = get_radar_values(p2_data)
            ax.plot(angles, val2, linewidth=2, linestyle='solid', label=p2_name, color='#448AFF')
            ax.fill(angles, val2, '#448AFF', alpha=0.25)

        plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        st.pyplot(fig)
        
    with col_text:
        st.subheader("🤖 AI-Аналітик")
        st.markdown(f"**Висновки по: {p1_name}**")
        if p1_data['Витривалість'] < 65:
            st.warning("⚠️ Низька витривалість. Рекомендовано інтервальні тренування.")
        elif p1_data['Сила'] < 65:
            st.warning("⚠️ Нестача фізичної сили. Додати силові тренування.")
        else:
            st.success("✅ Гравець у чудовій фізичній формі!")
            
        if p1_name != p2_name:
            st.markdown(f"**Висновки по: {p2_name}**")
            if p2_data['Витривалість'] < 65:
                st.warning("⚠️ Низька витривалість. Рекомендовано інтервальні тренування.")
            elif p2_data['Сила'] < 65:
                st.warning("⚠️ Нестача фізичної сили. Додати силові тренування.")
            else:
                st.success("✅ Гравець у чудовій фізичній формі!")

# ==========================================
# 4. ЛАБОРАТОРІЯ ФІЗИКИ (MATPLOTLIB)
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
        
        # Надійний графік через Matplotlib
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
# 5. ДАНІ
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
