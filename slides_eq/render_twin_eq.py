"""Equation images for the native twin slides (Computer Modern mathtext, 20 pt at 300 dpi; place at px/300 inches).
    python slides_eq/render_twin_eq.py  -> slides_eq/twin_eq/*.png"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams["mathtext.fontset"] = "cm"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "twin_eq")
EQ = {
    "s": r"$s=\frac{b_I+j\,b_Q}{\sqrt{2}},\quad b_I=b_Q\ \Rightarrow\ s\in\left\{\pm\frac{1+j}{\sqrt{2}}\right\}\ \Rightarrow\ s^2=j$",
    "r": r"$r_n=s_n\,e^{\,j(2\pi f n+\theta)}+w_n$",
    "w": r"$\omega_n\,r_n^2=e^{\,j(4\pi f n+2\theta)}+\mathrm{noise}$",
    "x": r"$x=u\,G_N,\quad G_N=F^{\otimes n}\ \Rightarrow\ x_j=\bigoplus_{i\,\supseteq\,j}u_i$",
    "pair": r"$k<N/2:\quad x_k\oplus x_{k+N/2}=\bigoplus_{i<N/2,\ i\,\supseteq\,k}u_i$",
    "ub": r"$\mathrm{UB}=\sum_{u\,\in\,\mathrm{info}} Q\!\left(\sqrt{m_u/2}\right)$",
    "e": r"$e=[\,e_1,\ e_1[\mathrm{rep}]\,],\quad |\mathrm{rep}|=t$",
    "mrc": r"$\ell_1[\mathrm{rep}]\ \leftarrow\ \ell_1[\mathrm{rep}]+\ell_{\mathrm{copy}}\quad\Rightarrow\quad \mathrm{GA\ mean}\ 2\mu$",
    "xk": r"$x_k$",
    "xkn": r"$x_{k+N/2}$",
    "biq": r"$b_I=b_Q$",
}
for k, s in EQ.items():
    f = plt.figure(figsize=(0.1, 0.1))
    f.text(0, 0, s, fontsize=20, color="#1f2937" if k not in ("xk", "xkn", "biq") else "#003366")
    f.savefig(os.path.join(OUT, f"{k}.png"), dpi=300, bbox_inches="tight", pad_inches=0.03, facecolor="white")
    plt.close(f)
