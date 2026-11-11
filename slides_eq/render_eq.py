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
    # signal model and 4th power
    "model": r"$y_n = s_n\,e^{\,j(2\pi f n+\theta)} + w_n,\qquad s_n\in\{e^{\,j(\pi/4+k\pi/2)}\},\quad |f|\leq 0.03$",
    "s4": r"$s_n^4 = e^{\,j4(\pi/4+k\pi/2)} = e^{\,j\pi}\,e^{\,j2\pi k} = -1$",
    "v4": r"$v_n=-y_n^4=-s_n^4\,e^{\,j(2\pi\cdot 4f\cdot n+4\theta)}+\varepsilon_n=e^{\,j(2\pi\cdot 4f\cdot n+4\theta)}+\varepsilon_n$",
    "nu": r"$|4f|\leq 4\cdot 0.03=0.12 < 1/2\ \Rightarrow\ \mathrm{no\ aliasing}$",
    # FFT: why the peak bin is the coarse CFO
    "fft": r"$V[k]=\sum_{n=0}^{1023} v_n\,e^{-j2\pi kn/4096}\ \approx\ e^{\,j4\theta}\sum_{n=0}^{1023} e^{\,j2\pi\,(4f-k/4096)\,n}$",
    "dir": r"$|V[k]|\approx\left|\dfrac{\sin(1024\,\pi x_k)}{\sin(\pi x_k)}\right|\leq 1024,\qquad x_k=4f-\dfrac{k}{4096}$",
    "kb": r"$k_b=\arg\max_{|k|/4096\,\leq\,0.12}\ |V[k]|\quad\Rightarrow\quad \dfrac{k_b}{4096}\approx 4f\ \ (\pm\,\mathrm{half\ a\ bin})$",
    "delta": r"$|V[k_b+x]|\approx a x^2+bx+c\ \ \Rightarrow\ \ \delta=-\dfrac{b}{2a}=\dfrac{1}{2}\,\dfrac{V_{-1}-V_{+1}}{V_{-1}-2V_0+V_{+1}}$",
    "f0": r"$\dfrac{k_b+\delta}{4096}\approx 4f\quad\Rightarrow\quad\hat f_0=\dfrac{k_b+\delta}{4\cdot 4096}$",
    # phase
    "ph1": r"$\sum_{n} v_n\,e^{-j2\pi\cdot 4\hat f_0 n}=e^{\,j4\theta}\sum_n e^{\,j2\pi\cdot 4(f-\hat f_0)n}+\mathrm{noise}\ \approx\ 1024\,e^{\,j4\theta}$",
    "theta0": r"$\hat\theta_0=\dfrac{1}{4}\,\arg\sum_{n} v_n\,e^{-j2\pi\cdot 4\hat f_0 n}$",
    "mod": r"$\arg(\cdot)=4\theta+2\pi m\ \ \Rightarrow\ \ \hat\theta_0=\theta+m\,\dfrac{\pi}{2}:\ \ \theta\ \mathrm{known\ only\ mod}\ \pi/2$",
    "premf": r"$y^{\prime}_n=\left[\left(y_8[m]\,e^{-j2\pi\hat f_0 m/8}\right)\star h\right]_{m=8n}\;e^{\,j2\pi\hat f_0 n}$",
    # one hypothesis -> LLRs -> metric
    "xh": r"$x_n(f,\theta)=y^{\prime}_n\,e^{-j(2\pi f n+\theta)}\ \ \rightarrow\ \ \mathbf{L}=\mathrm{channel\ LLRs\ of}\ x_n$",
    "lam": r"$\lambda_i(\mathbf{L})=\ln\dfrac{P(u_i=0\mid \mathbf{L},\,\hat u_0\ldots\hat u_{i-1})}{P(u_i=1\mid \mathbf{L},\,\hat u_0\ldots\hat u_{i-1})}$",
    "fg": r"$\mathrm{SC\ tree:}\ \ F(a,b)=\mathrm{sgn}(a)\,\mathrm{sgn}(b)\min(|a|,|b|),\qquad G(a,b)=b+(1-2\hat u)\,a$",
    "mdef": r"$M(\mathbf{L})=\sum_{i=0}^{N-1}\ln\!\left(1+e^{-(1-2\hat u_i)\lambda_i(\mathbf{L})}\right)$",
    "branch": r"$M_b=M(\hat f_0,\ \hat\theta_0+b\,\pi/2),\qquad \hat b=\arg\min_{b\in\{0,1\}} M_b$",
    # the pi ambiguity
    "qpsk": r"$s_n=\dfrac{(1-2c_{2n})+j\,(1-2c_{2n+1})}{\sqrt{2}}$",
    "rotpi": r"$e^{\,j\pi}s_n=-s_n\ \Rightarrow\ c_{2n}\rightarrow 1\oplus c_{2n},\ \ c_{2n+1}\rightarrow 1\oplus c_{2n+1}:\ \ \mathbf{c}\rightarrow\mathbf{c}\oplus\mathbf{1}$",
    "rotpi2": r"$e^{\,j\pi/2}s_n=j\,s_n\ \Rightarrow\ c_{2n}\rightarrow 1\oplus c_{2n+1},\ \ c_{2n+1}\rightarrow c_{2n}$",
    "picode": r"$\mathbf{c}=\mathbf{u}\,G_N,\ \ \mathbf{1}=\mathbf{e}_{N-1}G_N\ \ \Rightarrow\ \ \mathbf{c}\oplus\mathbf{1}=(\mathbf{u}\oplus\mathbf{e}_{N-1})\,G_N$",
    "crcpi": r"$\mathrm{accept\ if}\ \ \mathrm{CRC}(\hat{\mathbf{d}})\in\{\hat{\mathbf{p}},\ \hat{\mathbf{p}}\oplus\mathbf{e}_{16}\},\qquad P(\mathrm{wrong\ path\ passes})=2\cdot 2^{-16}$",
    # path metric as detector
    "pm": r"$M=\sum_{i=0}^{N-1}\ln\!\left(1+e^{-(1-2\hat u_i)\lambda_i}\right)\ \approx\ -\ln P(\hat{\mathbf{u}}\mid\mathbf{y})$",
    "frozen": r"$\mathrm{frozen}\ i:\quad \hat u_i=0\ \Rightarrow\ \mathrm{penalty}\ \ln(1+e^{-\lambda_i})$",
    "gap": r"$\mathrm{E}[M_{\mathrm{wrong}}]-\mathrm{E}[M_{\mathrm{right}}]\ \approx\ (N-K)\ln 2$",
    "nk": r"$N=2048,\quad K=A+16:\ \ 221\ (R=1/10),\ 835\ (R=2/5),\ 1040\ (R=1/2)$",
    # grid
    "grid": r"$f_c=-0.03+c\,k\,\Delta,\quad c=0,\ldots,C-1,\qquad \Delta=7.5\cdot 10^{-5}$",
    "gridq": r"$\theta_{c,q}=\theta_c+q\,\dfrac{\pi}{4},\qquad q\in\{0,1,2,3\}\ (\mathrm{SNR}<-1\,\mathrm{dB}),\quad q\in\{0,2\}\ (\mathrm{SNR}\geq -1\,\mathrm{dB})$",
    # z-test, simple form
    "zmed": r"$\bar M=\mathrm{median}_c\,(M_c)$",
    "zsig": r"$\hat\sigma=1.4826\cdot\mathrm{median}_c\,|M_c-\bar M|$",
    "z": r"$z_c=\dfrac{\bar M-M_c}{\hat\sigma}$",
    "tail": r"$P(z_c>6\mid \mathrm{wrong\ cell})\approx Q(6)\approx 10^{-9}$",
    # stage 3
    "ref1": r"$f=f_c+o\,\Delta,\qquad o\in\{-\dfrac{k}{2},\ldots,\dfrac{k}{2}\}=\{-2,\ldots,2\}\ (R=1/10),\ \{-1,0,1\}\ (R=2/5,\,1/2)$",
    "ref2": r"$\theta=\theta_c+\varphi,\qquad \varphi\in\{-\dfrac{\pi}{12},\,0,\,+\dfrac{\pi}{12}\}\ (\mathrm{SNR}<-1\,\mathrm{dB}),\quad \varphi=0\ \mathrm{otherwise}$",
    "dd": r"$d_n=y^{\prime}_n\cdot\hat s_n^{\,*}\ \approx\ e^{\,j(2\pi f n+\theta)}+\mathrm{noise}$",
    "fdd": r"$\hat f=\arg\max_f\ \left|\sum_n d_n\,e^{-j2\pi f n}\right|^2$",
    "thdd": r"$\hat\theta=\mathrm{angle}\left(\sum_n d_n\,e^{-j2\pi \hat f n}\right)$",
    # re-encoding
    "re0": r"$y^{\prime}_n\,\tilde s_n^{\,*}\,e^{-j2\pi\hat f n}=s_n\tilde s_n^{\,*}\,e^{\,j\theta}e^{\,j2\pi(f-\hat f)n}+\tilde w_n\ \approx\ \{e^{\,j\theta}+\tilde w_n\ \ \mathrm{right};\ \ \mathrm{random\ phase}\ \ \mathrm{wrong}\}$",
    "rho": r"$\rho=\dfrac{\left|\sum_n y^{\prime}_n\,\tilde s_n^{\,*}\,e^{-j2\pi\hat f n}\right|}{\sqrt{N\sum_n|y^{\prime}_n|^2}}\ \in[0,1]$",
    "rho_right": r"$\rho_{\mathrm{right}}\approx\dfrac{N}{\sqrt{N\cdot N(1+1/\mathrm{SNR})}}=\sqrt{\dfrac{\mathrm{SNR}}{1+\mathrm{SNR}}}\ \ (0.49\ \mathrm{at}\ -5\ \mathrm{dB})$",
    "rho_wrong": r"$\left|\sum\right|\sim\sqrt{N}\ \Rightarrow\ P(\rho_{\mathrm{wrong}}>t)\approx e^{-Nt^2}\ \ (4\cdot 10^{-7}\ \mathrm{at}\ t=0.12)$",
    "rho_th": r"$\rho>\max\!\left(0.12,\ c(\mathrm{SNR})\sqrt{\dfrac{s}{1+s}}\right)$",
    # baseline: M&M and CRC search
    "drift": r"$\Delta\phi_n=2\pi\,(f-\hat f)\,n:\qquad f-\hat f=10^{-4}\ \Rightarrow\ \Delta\phi_{1023}\approx 0.64\ \mathrm{rad}\approx 37^\circ$",
    "mm1": r"$y_n=p_n\,e^{\,j(2\pi fn+\theta)}+w_n,\qquad n=0,\ldots,L_0-1\quad(L_0=128\ \mathrm{known\ pilots}\ p_n)$",
    "mm2": r"$z_n=y_n\,p_n^{\,*}=e^{\,j(2\pi fn+\theta)}+w^{\prime}_n$",
    "mm3": r"$R(m)=\dfrac{1}{L_0-m}\sum_{n=m}^{L_0-1} z_n\,z_{n-m}^{\,*}\ \approx\ e^{\,j2\pi fm},\qquad 1\leq m\leq D=L_0/2$",
    "mm4": r"$\hat f=\dfrac{1}{2\pi}\sum_{m=1}^{D} w(m)\,[\arg R(m)-\arg R(m-1)]_{2\pi}$",
    "mm5": r"$w(m)=3\,\dfrac{(L_0-m)(L_0-m+1)-D(L_0-D)}{D\,(4D^2-6DL_0+3L_0^2-1)}$",
    "crcs": r"$f_i=\hat f+i\,\Delta,\qquad i=0,+1,-1,+2,-2,\ldots,\pm 34,\qquad \Delta=7.5\cdot 10^{-5}$",
    # parallel decoding
    "crit": r"$T_{\mathrm{crit}}=T_{\mathrm{serial}}+\sum_{\mathrm{passes}\ p}\ \max_{\mathrm{core}}\ \mathrm{cost}_p$",
    "tot": r"$\mathrm{MAC}_{\mathrm{total}}=\sum_{\mathrm{all\ work}}\mathrm{cost}\qquad(\mathrm{energy})$",
    "tdec": r"$T_{\mathrm{dec}}=\dfrac{8N\log_2 N}{8}+6144+K\cdot 2L\log_2(2L)$",
    "tdec2": r"$R=1/10:\ \ 22.5\mathrm{k}+6.1\mathrm{k}+14.1\mathrm{k}\approx 43\mathrm{k}\ \ \mathrm{vs}\ \ 186\mathrm{k}\ \mathrm{on\ one\ core}$",
    "jseed": r"$\mathrm{path}\ h\ \mathrm{starts\ on}\ \ \mathbf{L}_h=\mathrm{LLR}(y^{\prime};\,f_h,\theta_h),\qquad h=1,\ldots,8\ \ (4\ \mathrm{cells}\times 2)$",
    "jsplit": r"$16\ \mathrm{paths}\times\{\hat u_i=0,\ \hat u_i=1\}=32\ \mathrm{children}\ \rightarrow\ 32\ \mathrm{cores}$",
    "jprune": r"$\mathrm{keep\ the\ 16\ smallest}\ \ M_h(\mathrm{path})=\sum_{j\leq i}\ln\!\left(1+e^{-(1-2\hat u_j)\lambda_j(\mathbf{L}_h)}\right)$",
    "jvalid": r"$M_h\approx-\ln P(\hat{\mathbf{u}}\mid\mathbf{y}^{\prime},\,h)\ :\ \mathrm{same\ samples,\ same\ code}\ \Rightarrow\ \mathrm{comparable\ across}\ h$",
}

EQ.update({
    "premf": r"$y^{\prime}_n=\left[\left(y_8[m]\,e^{-j2\pi\hat f_0 m/8}\right)\star h\right]_{m=80+8n}\;e^{\,j2\pi\hat f_0 (n+5)}$",
    "nc": r"$n_c=n-511.5,\qquad y_n=s_n\,e^{\,j(2\pi f n_c+\theta)}+w_n\quad(\theta:\ \mathrm{phase\ at\ the\ packet\ centre})$",
    "ph1": r"$\sum_{n} v_n\,e^{-j2\pi\cdot 4\hat f_0 n_c}=e^{\,j4\theta}\sum_n e^{\,j2\pi\cdot 4(f-\hat f_0)n_c}+\mathrm{noise}\ \approx\ 1024\,e^{\,j4\theta}$",
    "theta0": r"$\hat\theta_0=\dfrac{1}{4}\,\arg\sum_{n} v_n\,e^{-j2\pi\cdot 4\hat f_0 n_c}$",
    "xh": r"$x_n(f,\theta)=y^{\prime}_n\,e^{-j(2\pi f n_c+\theta)}\ \ \rightarrow\ \ \mathbf{L}=\mathrm{channel\ LLRs\ of}\ x_n$",
    "mm4": r"$\hat f=\dfrac{1}{2\pi}\sum_{m=1}^{D} w(m)\,\arg\!\left[R(m)\,R^*(m-1)\right],\qquad R(0)\equiv 1$",
    "crcs": r"$f_k=\hat f+k\,\Delta,\quad k=0,-1,+1,-2,+2,\ldots,\quad |k|\leq\left\lceil 5.2\sqrt{\mathrm{CRB}_{128}}/\Delta\right\rceil\ (=34\ \mathrm{at}\ -5\,\mathrm{dB})$",
    "refph": r"$\theta_o=\hat\theta_0(f_c+o\Delta)+\mathrm{round}\!\left(\dfrac{\theta_c-\hat\theta_0(f_c+o\Delta)}{\pi/2}\right)\dfrac{\pi}{2}$",
    "dd": r"$d_n=y^{\prime}_n\,\hat s_n^{\,*}\ \approx\ e^{\,j(2\pi f n_c+\theta)}+\mathrm{noise}\quad(\hat s:\ \mathrm{SC\ hard\ decisions})$",
    "newton": r"$\Lambda(f)=\left|\sum_n d_n\,e^{-j2\pi f n_c}\right|^2,\qquad f_{t+1}=f_t-\dfrac{\Lambda^{\prime}(f_t)}{\Lambda^{\prime\prime}(f_t)},\quad t=0,1$",
    "thdd": r"$\hat\theta=\arg\sum_n d_n\,e^{-j2\pi f_2 n_c}$",
    "re0": r"$y^{\prime}_n\,\tilde s_n^{\,*}\,e^{-j2\pi\hat f n_c}\ \approx\ e^{\,j\theta}+\tilde w_n\quad(\tilde s=s),\qquad N_s=1024$",
    "rho": r"$\rho=\dfrac{\left|\sum_n y^{\prime}_n\,\tilde s_n^{\,*}\,e^{-j2\pi\hat f n_c}\right|}{\sqrt{N_s\sum_n|y^{\prime}_n|^2}}\ \in[0,1]$",
    "rho_right": r"$\rho_{\mathrm{right}}\approx\dfrac{N_s}{\sqrt{N_s\cdot N_s(1+1/s)}}=\sqrt{\dfrac{s}{1+s}}\ \ (0.49\ \mathrm{at}\ -5\ \mathrm{dB})$",
    "rho_wrong": r"$P(\rho_{\mathrm{wrong}}>t)\approx e^{-N_s t^2}\ \ (4\cdot 10^{-7}\ \mathrm{at}\ t=0.12,\ \mathrm{one\ test})$",
    "rho_th": r"$\rho>\max\!\left(0.12,\ \dfrac{1}{2}\sqrt{\dfrac{s}{1+s}},\ c_R(s)\sqrt{\dfrac{s}{1+s}}\right)=c_R(s)\sqrt{\dfrac{s}{1+s}}$",
    "ci": r"$0\ \mathrm{events\ in}\ n\ \mathrm{trials}:\quad p<-\ln(0.05)/n\approx 3/n\quad(95\,\%\ \mathrm{one\ sided})$",
    "crit": r"$W_{\mathrm{crit}}=W_{\mathrm{serial}}+\sum_{\mathrm{passes}\ p}\ \max_{\mathrm{core}}\ W_{p,\mathrm{core}}$",
    "tot": r"$W_{\mathrm{total}}=\sum_{\mathrm{all\ work}}W\qquad(\mathrm{energy})$",
    "test": r"$T_{\mathrm{est}}\approx\dfrac{W_{\mathrm{crit}}}{F_{\mathrm{MAC}}}+T_{\mathrm{overhead}}\qquad(\mathrm{model,\ not\ measured})$",
    "tdec": r"$W_{\mathrm{dec}}=\dfrac{8N\log_2 N}{8}+6144+K\cdot 2L\log_2(2L)$",
    "tput": r"$\eta=\dfrac{A\,(1-\mathrm{BLER})}{N_{\mathrm{tx}}}\ \ \mathrm{bits/symbol},\qquad N_{\mathrm{tx}}=1024\ (\mathrm{blind}),\ \ 1152\ (128+1024)$",
    "tgain": r"$\dfrac{\eta_{\mathrm{blind}}}{\eta_{\mathrm{pilot}}}=\dfrac{1152}{1024}\cdot\dfrac{1-\mathrm{BLER}_b}{1-\mathrm{BLER}_p}\approx 1.125$",
    "fft_s": r"$V[k]=\sum_{n=0}^{1023} v_n\,e^{-j2\pi kn/4096},\qquad v_n\approx e^{\,j(2\pi\cdot 4f\cdot n+4\theta)}$",
    "kb_s": r"$k_b=\arg\max_{k}\ |V[k]|\ \approx\ 4096\cdot 4f$",
    "f0_s": r"$\hat f_0=\dfrac{k_b+\delta}{4\cdot 4096}$",
})


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
