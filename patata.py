import streamlit as st
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

# Configuración de la página
st.set_page_config(page_title="Optimización de Drones RF", layout="wide")

st.title("🛸 Optimización de Potencia en Enjambre de Drones de Rescate")
st.markdown("""
Esta aplicación utiliza **Programación Lineal (`scipy.optimize.milp`)** para determinar la asignación óptima de potencia 
de transmisión en vatios ($W$) para un enjambre de 4 drones repetidores, maximizando la tasa de datos total ($Mbps$).
""")

st.sidebar.header("🎛️ Parámetros de Radiofrecuencia (RF)")

# 1. Sliders para la Función Objetivo (Beneficios por Vatio)
mbps_celular = st.sidebar.slider("Eficiencia Celular (Mbps por Vatio)", 5, 30, 15)
mbps_wifi = st.sidebar.slider("Eficiencia Wi-Fi (Mbps por Vatio)", 20, 60, 40)

st.sidebar.header("⚠️ Restricciones del Sistema")

# 2. Sliders para las Restricciones
max_pot_dron = st.sidebar.slider("Potencia máxima por Dron (W)", 5, 20, 12)
max_pot_enjambre = st.sidebar.slider("Presupuesto Total Enjambre (W)", 20, 80, 40)
max_backhaul = st.sidebar.slider("Límite Backhaul Satelital Wi-Fi (Mbps)", 500, 2000, 1200)

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📋 Restricciones Geográficas / Interferencia")
    max_interf = st.number_input("Máxima potencia Celular D1 + D2 (Evitar Interferencia)", value=10.0)
    min_bosque = st.number_input("Mínima potencia Celular D3 + D4 (Penetración Bosque)", value=8.0)

# --- PROCESAMIENTO MATEMÁTICO ---

# Coeficientes de la función objetivo (Negativos para maximizar)
c = [-mbps_celular] * 4 + [-mbps_wifi] * 4

# Matriz de restricciones (A)
A = [
    [1, 0, 0, 0,  1, 0, 0, 0],  # Potencia máxima Dron 1
    [0, 1, 0, 0,  0, 1, 0, 0],  # Potencia máxima Dron 2
    [0, 0, 1, 0,  0, 0, 1, 0],  # Potencia máxima Dron 3
    [0, 0, 0, 1,  0, 0, 0, 1],  # Potencia máxima Dron 4
    
    [1, 1, 1, 1,  1, 1, 1, 1],  # Presupuesto total enjambre
    [0, 0, 0, 0, mbps_wifi, mbps_wifi, mbps_wifi, mbps_wifi], # Límite Backhaul Wi-Fi
    
    [1, 1, 0, 0,  0, 0, 0, 0],  # Interferencia Celular D1 + D2
    [0, 0, 1, 1,  0, 0, 0, 0]   # Cobertura Bosque Celular D3 + D4
]

# Cotas superiores (bu)
bu = [max_pot_dron, max_pot_dron, max_pot_dron, max_pot_dron, max_pot_enjambre, max_backhaul, max_interf, np.inf]

# Cotas inferiores (bl)
bl = [-np.inf, -np.inf, -np.inf, -np.inf, -np.inf, -np.inf, -np.inf, min_bosque]

# Límites de las variables (Potencia >= 0 W)
bounds = Bounds([0] * 8, [np.inf] * 8)
constraints = LinearConstraint(A, bl, bu)

# Ejecución del optimizador
res = milp(c=c, constraints=constraints, bounds=bounds, integrality=[0] * 8)

# --- RENDERIZADO DE RESULTADOS ---
with col2:
    st.subheader("📊 Reporte Técnico de Optimización")
    
    if res.success:
        st.success(f"**Estado:** {res.message}")
        
        # Métrica principal destacada
        st.metric(label="🎯 Capacidad Máxima del Sistema", value=f"{-res.fun:.2f} Mbps")
        
        # Formatear resultados en columnas para una mejor vista en el Dashboard
        d1, d2, d3, d4 = st.columns(4)
        
        with d1:
            st.info("**🛸 DRON 1**")
            st.write(f"📶 Celular: `{res.x[0]:.2f} W`")
            st.write(f"🌐 Wi-Fi: `{res.x[4]:.2f} W`")
            st.caption(f"Total: {res.x[0]+res.x[4]:.2f} W")
            
        with d2:
            st.info("**🛸 DRON 2**")
            st.write(f"📶 Celular: `{res.x[1]:.2f} W`")
            st.write(f"🌐 Wi-Fi: `{res.x[5]:.2f} W`")
            st.caption(f"Total: {res.x[1]+res.x[5]:.2f} W")
            
        with d3:
            st.info("**🛸 DRON 3**")
            st.write(f"📶 Celular: `{res.x[2]:.2f} W`")
            st.write(f"🌐 Wi-Fi: `{res.x[6]:.2f} W`")
            st.caption(f"Total: {res.x[2]+res.x[6]:.2f} W")
            
        with d4:
            st.info("**🛸 DRON 4**")
            st.write(f"📶 Celular: `{res.x[3]:.2f} W`")
            st.write(f"🌐 Wi-Fi: `{res.x[7]:.2f} W`")
            st.caption(f"Total: {res.x[3]+res.x[7]:.2f} W")
            
        # Alertas de uso de recursos
        pot_total_real = sum(res.x)
        st.progress(min(pot_total_real / max_pot_enjambre, 1.0), 
                    text=f"Uso del presupuesto de potencia total: {pot_total_real:.2f}W / {max_pot_enjambre}W")
            
    else:
        st.error(f"❌ No se encontró una solución factible con los parámetros actuales: {res.message}")
      
