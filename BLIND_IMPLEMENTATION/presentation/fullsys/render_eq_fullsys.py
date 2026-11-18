"""Equation images for the full-system deck (2026-11-18): the equations that still showed the old 1024-symbol /
CRC-16 / R = 1/10, 2/5, 1/2 setup, rewritten for the real-system bursts. Same style as slides_eq/render_eq.py on the
slides branch (matplotlib mathtext, Computer Modern, 26 pt, dpi 300).

    py BLIND_IMPLEMENTATION/presentation/fullsys/render_eq_fullsys.py      -> eq/<name>.png
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

matplotlib.rcParams["mathtext.fontset"] = "cm"
DPI, FONT_PT = 300, 26
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eq")

EQ = {
    "model": r"$y_n = s_n\,e^{\,j(2\pi f n+\theta)} + w_n,\qquad s_n\in\{e^{\,j(\pi/4+k\pi/2)}\}\ \mathrm{(QPSK)}\ \mathrm{or}\ \{\pm 1\}\ \mathrm{(BPSK)},\quad |f|\leq 0.03$",
    "drift": r"$\Delta\phi_n=2\pi\,(f-\hat f)\,n:\qquad f-\hat f=10^{-4}\ \Rightarrow\ \Delta\phi_{1475}\approx 0.93\ \mathrm{rad}\approx 53^\circ\ \ (\mathrm{1476\ symbols})$",
    "fft_s": r"$V[k]=\sum_{n=0}^{n_{\mathrm{sym}}-1} v_n\,e^{-j2\pi kn/N_{\mathrm{FFT}}},\qquad v_n\approx e^{\,j(2\pi\cdot 4f\cdot n+4\theta)}$",
    "kb_s": r"$k_b=\arg\max_{k}\ |V[k]|\ \approx\ N_{\mathrm{FFT}}\cdot 4f$",
    "f0_s": r"$\hat f_0=\dfrac{k_b+\delta}{4\,N_{\mathrm{FFT}}}$",
    "ph1": r"$\sum_{n} v_n\,e^{-j2\pi\cdot 4\hat f_0 n_c}=e^{\,j4\theta}\sum_n e^{\,j2\pi\cdot 4(f-\hat f_0)n_c}+\mathrm{noise}\ \approx\ n_{\mathrm{sym}}\,e^{\,j4\theta}$",
    "premf": r"$y^{\prime}_n=\left[\left(y_8[m]\,e^{-j2\pi\hat f_0 m/8}\right)\star h\right]_{m=8n}\;e^{\,j2\pi\hat f_0 n}$",
    "nk": r"$K=A+32=304\ (\mathrm{ID\ 3}),\ 984\ (\mathrm{IDs\ 13,\,42}),\ 1504\ (\mathrm{ID\ 14}),\ 312\ (\mathrm{VDE{-}SAT})$",
    "grid": r"$f_c=-0.03+c\,k\,\Delta,\quad c=0,\ldots,C-1,\qquad \Delta=1.5\cdot 10^{-4}\cdot\dfrac{512}{n_{\mathrm{sym}}}$",
    "gridq": r"$\theta_{c,q}=\theta_c+q\,\dfrac{\pi}{4}:\quad q\in\{0,2\}\ (\mathrm{IDs\ 3,\,13,\,42}),\ \ \{0,2,4,6\}\ (\mathrm{ID\ 14}),\ \ q=0\ (\mathrm{VDE{-}SAT})$",
    "f5b": r"$\mathrm{stop\ the\ decode\ if}\ \ \min_{\ell}\ \psi_\ell>t,\qquad\mathrm{checked\ once,\ at}\ n_F=q\,F$",
    "re0": r"$y^{\prime}_n\,\tilde s_n^{\,*}\,e^{-j2\pi\hat f n_c}\ \approx\ e^{\,j\theta}+\tilde w_n\quad(\tilde s=s),\qquad N_s=n_{\mathrm{sym}}$",
}


def render(name, tex):
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, tex, fontsize=FONT_PT, color="#111111")
    path = os.path.join(OUT, f"{name}.png")
    fig.savefig(path, dpi=DPI, bbox_inches="tight", pad_inches=0.04, facecolor="white")
    plt.close(fig)
    return path


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for k, v in EQ.items():
        print(render(k, v))
