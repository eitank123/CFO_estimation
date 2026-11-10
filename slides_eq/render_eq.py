"""Render the blind-receiver equations used in the CFO Estimation slides as PNG images.

Run:  python slides_eq/render_eq.py   (writes slides_eq/*.png)
Each equation is drawn with matplotlib mathtext in Computer Modern at FONT_PT points,
so an image placed at (width_px / DPI) x (height_px / DPI) inches shows the formula at FONT_PT.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

matplotlib.rcParams["mathtext.fontset"] = "cm"

DPI = 300
FONT_PT = 26
OUT = os.path.dirname(os.path.abspath(__file__))

EQ = {
    # signal model
    "model": r"$r_n = g\,e^{\,j(2\pi f n+\theta)}\,s_n + w_n,\qquad s_n\in\{e^{\,j(\pi/4+k\pi/2)}\},\quad |f|\leq 0.03$",
    # 4th power
    "s4": r"$s_n^4 = e^{\,j4(\pi/4+k\pi/2)} = e^{\,j\pi}\,e^{\,j2\pi k} = -1$",
    "y4": r"$y_n=-r_n^4=-g^4e^{\,j(2\pi\cdot 4f n+4\theta)}\,s_n^4+\varepsilon_n=g^4e^{\,j(2\pi\,\nu n+4\theta)}+\varepsilon_n$",
    "nu": r"$\nu = 4f,\qquad |\nu|\leq 0.12 < 1/2\ \Rightarrow\ \mathrm{no\ aliasing}$",
    # FFT
    "fft": r"$Y[k]=\sum_{n=0}^{1023} y_n\,e^{-j2\pi kn/4096}$",
    "kb": r"$k_b=\arg\max_{|k|/4096\,\leq\,0.12}\ |Y[k]|$",
    "delta": r"$\delta=\dfrac{1}{2}\,\dfrac{V_{-1}-V_{+1}}{V_{-1}-2V_0+V_{+1}},\qquad V_i=|Y[k_b+i]|$",
    "f0": r"$\hat f_0=\dfrac{k_b+\delta}{4\cdot 4096}$",
    "theta0": r"$\hat\theta_0=\dfrac{1}{4}\,\arg\sum_{n} y_n\,e^{-j2\pi\,4\hat f_0 n}\quad(\mathrm{mod}\ \pi/2)$",
    # pre-MF and pi ambiguity
    "premf": r"$r^{\prime}_n=\left[\left(r_x[m]\,e^{-j2\pi\hat f_0 m/8}\right)\star h\right]_{m=8n}\;e^{\,j2\pi\hat f_0 n}$",
    "branch": r"$b=\arg\min_{b\in\{0,1\}}\ M\!\left(\mathrm{LLR}(r';\,\hat f_0,\ \hat\theta_0+b\,\pi/2)\right)$",
    "picode": r"$\mathbf{c}\oplus\mathbf{1}=(\mathbf{u}\oplus\mathbf{e}_{N-1})\,G_N$",
    # path metric
    "pm": r"$M=\sum_{i=0}^{N-1}\ln\!\left(1+e^{-(1-2\hat u_i)\lambda_i}\right)\ \approx\ -\ln P(\hat{\mathbf{u}}\mid\mathbf{r})$",
    "frozen": r"$\mathrm{frozen}\ i:\quad \hat u_i=0\ \Rightarrow\ \mathrm{penalty}\ \ln(1+e^{-\lambda_i})$",
    "gap": r"$\mathrm{E}[M_{\mathrm{wrong}}]-\mathrm{E}[M_{\mathrm{right}}]\ \approx\ (N-K)\ln 2$",
    # grid / z-test
    "grid": r"$f_c=-0.03+c\,k\,\Delta,\qquad \theta_{c,q}=\theta_c+q\,\dfrac{\pi}{4},\qquad \Delta=7.5\cdot 10^{-5}$",
    "z": r"$z_c=\dfrac{\mathrm{median}(M)-M_c}{1.4826\ \mathrm{MAD}(M)}$",
    # stage 3
    "zdd": r"$z_n=r^{\prime}_n\,\hat s_n^{\,*}$",
    "lam": r"$\Lambda(f)=\left|\sum_n z_n\,e^{-j2\pi f n}\right|^2,\qquad f\leftarrow f-\dfrac{\Lambda'(f)}{\Lambda''(f)}$",
    "thdd": r"$\hat\theta=\arg\sum_n z_n\,e^{-j2\pi \hat f n}$",
    # re-encoding
    "rho": r"$\rho=\dfrac{\left|\sum_n r^{\prime}_n\,\tilde s_n^{\,*}\,e^{-j2\pi\hat f n}\right|}{\sqrt{N\sum_n|r^{\prime}_n|^2}}$",
    "rho_right": r"$\rho_{\mathrm{right}}\approx\sqrt{\dfrac{\mathrm{SNR}}{1+\mathrm{SNR}}}\ \ (0.49\ \mathrm{at}\ -5\ \mathrm{dB})$",
    "rho_wrong": r"$P(\rho_{\mathrm{wrong}}>t)\approx e^{-Nt^2}\ \ (4\cdot 10^{-7}\ \mathrm{at}\ t=0.12)$",
    "rho_th": r"$\rho>\max\!\left(0.12,\ c(\mathrm{SNR})\sqrt{\dfrac{s}{1+s}}\right)$",
}


def render(name, tex):
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, tex, fontsize=FONT_PT, color="#111111")
    path = os.path.join(OUT, f"{name}.png")
    fig.savefig(path, dpi=DPI, bbox_inches="tight", pad_inches=0.04, transparent=False, facecolor="white")
    plt.close(fig)
    return path


if __name__ == "__main__":
    for k, v in EQ.items():
        print(render(k, v))
