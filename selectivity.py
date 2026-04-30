import numpy as np
import matplotlib.pyplot as plt

# Funcția care calculează timpii pentru toate cele 3 trepte (I>, I>>, I>>>)
def calculeaza_curba(I_vector, I_set, TMS, I_dt, T_dt, I_inst):
    timpi = []
    for I in I_vector:
        if I <= I_set:
            timpi.append(np.nan)  # Sub curentul nominal, releul nu acționează
        elif I >= I_inst:
            timpi.append(0.02)    # Treapta instantanee (0s teoretic, 20ms fizic)
        elif I >= I_dt:
            timpi.append(T_dt)    # Treapta de scurtcircuit temporizat
        else:
            # Curba Normal Inverse (NI) pentru suprasarcină
            t = (0.14 * TMS) / ((I / I_set)**0.02 - 1)
            timpi.append(t)
    return timpi

# Setările extrase din Tabelul tău
# Format: "Nume Releu": [I> (A), TMS, I>> (A), Timp I>> (s), I>>> (A)]
setari_relee = {
    "PV 1,2,3,4": [180, 0.05, 500, 0.1, 1000],
    "K4":         [500, 0.05, 1500, 0.2, 4000],
    "K2":         [600, 0.05, 1500, 0.2, 4000],
    "K5":         [750, 0.05, 1500, 0.2, 4000],
    "K3 - 20kV":  [1750, 0.05, 2400, 0.35, 4500]
}

# Adăugăm releul de 60kV raportat la 20kV (înmulțim curenții cu 3.15)
raport_trafo = 63 / 20
setari_relee["60kV Relay (Ref. 20kV)"] = [
    600 * raport_trafo, 
    0.08, 
    800 * raport_trafo, 
    0.5, 
    1500 * raport_trafo
]

# Generăm valorile curenților pe axa X (de la 100 A la 20.000 A)
curenti_x = np.logspace(2, 4.3, 3000) 

# Inițializăm graficul
plt.figure(figsize=(14, 9))

# Desenăm fiecare curbă iterând prin dicționar
for nume, setari in setari_relee.items():
    I_set, TMS, I_dt, T_dt, I_inst = setari
    timpi_y = calculeaza_curba(curenti_x, I_set, TMS, I_dt, T_dt, I_inst)
    plt.plot(curenti_x, timpi_y, label=f"{nume} (TMS={TMS})", linewidth=2.5)

# Formatarea scărilor în format Log-Log
plt.xscale('log')
plt.yscale('log')

# Linii de grid detaliate specifice ingineriei electrice
plt.grid(True, which="both", ls="-", color='lightgray', alpha=0.7)
plt.grid(True, which="minor", ls=":", color='lightgray', alpha=0.5)

# Etichete și limite
plt.title('Grafic de Coordonare a Protecțiilor (Toate Releele, Referință 20kV)', fontsize=16, pad=15)
plt.xlabel('Curent (A) - la nivel de 20kV', fontsize=12)
plt.ylabel('Timp de declanșare (s)', fontsize=12)
plt.ylim(0.01, 100)       # Axa timpului de la 10ms la 100 de secunde
plt.xlim(100, 20000)      # Axa curentului de la 100 A la 20 kA

# Adăugăm legenda
plt.legend(fontsize=11, loc='upper right')

# Afișarea graficului
plt.tight_layout()
plt.show()