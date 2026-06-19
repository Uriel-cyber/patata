import streamlit as st
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

# Configuración de la página
st.set_page_config(page_title="Simulador de Optimización RF Total", layout="wide")
# Inyectar CSS personalizado para cambiar el fondo de la pantalla y la barra lateral
st.markdown(
    """
    <style>
    /* Fondo de la aplicación principal */
    .stApp {
        background-color: #0f172a; /* Azul noche oscuro */
    }
    
    /* Fondo de la barra lateral (Sidebar) */
    [data-testid="stSidebar"] {
        background-color: #1e293b; /* Gris azulado */
    }
    
    /* Cambiar el color de los títulos a blanco brillante */
    h1, h2, h3 {
        color: #f8fafc !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🎛️ Simulador Universal de Programación Lineal para Drones RF")
st.markdown("""
Esta versión te permite **alterar cualquier coeficiente o matriz del sistema**. Puedes reconfigurar tanto la 
función objetivo como los pesos técnicos de cada restricción física.
""")

# --- PANEL IZQUIERDO: FUNCIÓN OBJETIVO Y LÍMITES GENERALES ---
st.sidebar.header("🎯 1. Coeficientes Función Objetivo (Mbps/W)")
mbps_celular = st.sidebar.slider("Eficiencia Celular (D1 a D4)", 1, 100, 15, step=1)
mbps_wifi = st.sidebar.slider("Eficiencia Wi-Fi (D1 a D4)", 1, 100, 40, step=1)

st.sidebar.header("⚠️ 2. Disponibilidad de Recursos (Límites)")
max_pot_dron = st.sidebar.slider("Capacidad Máxima por Dron (W)", 1, 50, 12, step=1)
max_pot_enjambre = st.sidebar.slider("Presupuesto Total Enjambre (W)", 5, 200, 40, step=1)
max_backhaul = st.sidebar.slider("Límite Backhaul Satelital (Mbps)", 100, 5000, 1200, step=1)

# --- PANEL CENTRAL: ALTERAR MATRIZ DE RESTRICCIONES (A) Y ENTREGAS ---
col1, col2 = st.columns([1.2, 1.8])

with col1:
    st.subheader("📋 3. Modificar Coeficientes de las Restricciones")
    
    st.markdown("**Interferencia Celular (D1 + D2):**")
    w_int_d1 = st.number_input("Peso Dron 1 en Interferencia", value=1, step=1)
    w_int_d2 = st.number_input("Peso Dron 2 en Interferencia", value=1, step=1)
    max_interf = st.slider("Límite Máximo de Interferencia (W)", 1, 50, 10, step=1)
    
    st.markdown("---")
    st.markdown("**Penetración en Bosque (D3 + D4):**")
    w_bos_d3 = st.number_input("Peso Dron 3 en Bosque", value=1, step=1)
    w_bos_d4 = st.number_input("Peso Dron 4 en Bosque", value=1, step=1)
    min_bosque = st.slider("Límite Mínimo Requerido para Bosque (W)", 1, 50, 8, step=1)
    
    st.markdown("---")
    boton_optimizar = st.button("🚀 Calcular Optimización", type="primary", use_container_width=True)

with col2:
    st.subheader("📊 Reporte Dinámico de Optimización")
    
    if boton_optimizar:
        # --- CONSTRUCCIÓN DINÁMICA DE MATRICES SEGÚN TUS ENTRADAS ---
        
        # Función objetivo dinámica
        c = [-mbps_celular] * 4 + [-mbps_wifi] * 4

        # Matriz A reconstruida con tus inputs del formulario
        A = [
            [1, 0, 0, 0,  1, 0, 0, 0],  # Potencia máxima D1
            [0, 1, 0, 0,  0, 1, 0, 0],  # Potencia máxima D2
            [0, 0, 1, 0,  0, 0, 1, 0],  # Potencia máxima D3
            [0, 0, 0, 1,  0, 0, 0, 1],  # Potencia máxima D4
            
            [1, 1, 1, 1,  1, 1, 1, 1],  # Presupuesto total enjambre
            [0, 0, 0, 0, mbps_wifi, mbps_wifi, mbps_wifi, mbps_wifi], # Límite Backhaul usando el Mbps Wi-Fi dinámico
            
            [w_int_d1, w_int_d2, 0, 0,  0, 0, 0, 0],  # Interferencia personalizada
            [0, 0, w_bos_d3, w_bos_d4,  0, 0, 0, 0]   # Cobertura de bosque personalizada
        ]

        # Cotas superiores (bu) dinámicas
        bu = [max_pot_dron, max_pot_dron, max_pot_dron, max_pot_dron, max_pot_enjambre, max_backhaul, max_interf, np.inf]

        # Cotas inferiores (bl) dinámicas
        bl = [-np.inf, -np.inf, -np.inf, -np.inf, -np.inf, -np.inf, -np.inf, min_bosque]

        # Resto del algoritmo estándar
        bounds = Bounds([0] * 8, [np.inf] * 8)
        constraints = LinearConstraint(A, bl, bu)

        # Ejecución
        res = milp(c=c, constraints=constraints, bounds=bounds, integrality=[0] * 8)

        # --- MOSTRAR RESULTADOS ---
        if res.success:
            st.success(f"**Estado:** {res.message}")
            st.metric(label="🎯 Capacidad Máxima Alcanzada", value=f"{-res.fun:.2f} Mbps")
            
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
                
            pot_total_real = sum(res.x)
            st.progress(min(pot_total_real / max_pot_enjambre, 1.0), 
                        text=f"Uso del presupuesto de potencia total: {pot_total_real:.2f}W / {max_pot_enjambre}W")
        else:
            st.error(f"❌ Configuración Incompatible: El optimizador no pudo encontrar una solución válida para estas restricciones. Prueba reduciendo las exigencias mínimas o aumentando los límites.")
    else:
        st.warning("👈 Altera cualquiera de los valores de la izquierda y haz clic en 'Calcular Optimización' para actualizar las ecuaciones.")
