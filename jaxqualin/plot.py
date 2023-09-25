import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import (
    MultipleLocator, AutoMinorLocator, LogLocator, NullFormatter)
from matplotlib.patches import Ellipse
import numpy as np
from QuasinormalMode import *
from ModeSelection import *
from bisect import bisect_right

from adjustText import adjust_text

from scipy.odr import Model, ODR, RealData
from scipy.optimize import curve_fit

import os


plt.rc('text', usetex=False)
plt.rc('font', family='qpl')
plt.rc('text.latex', preamble=r'\usepackage{amsmath}')

mpl.rcParams['xtick.major.size'] = 4
mpl.rcParams['ytick.major.size'] = 4
mpl.rcParams['xtick.minor.size'] = 2
mpl.rcParams['ytick.minor.size'] = 2

mpl.rcParams['xtick.direction'] = 'in'
mpl.rcParams['ytick.direction'] = 'in'
plt.rcParams['xtick.bottom'] = plt.rcParams['xtick.top'] = True
plt.rcParams['ytick.left'] = plt.rcParams['ytick.right'] = True
plt.rcParams['xtick.labeltop'] = plt.rcParams['ytick.labelright'] = False
mpl.rcParams['axes.unicode_minus'] = False

params = {'axes.labelsize': 18,
          'font.family': 'serif',
          'font.size': 9,
          'legend.fontsize': 12,
          'xtick.labelsize': 11,
          'ytick.labelsize': 11,
          'savefig.dpi': 200,
          'lines.markersize': 6,
          'axes.formatter.limits': (-3, 3)}

mpl.rcParams.update(params)

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
PLOT_SAVE_PATH = os.path.join(ROOT_PATH, "plots")


def plot_omega_free(
        results_full,
        ax=None,
        plot_indxs=[],
        t0_min=None,
        t0_max=None,
        indicate_start = False,
        color = None,
        line_alpha = 0.3,
        scatter_alpha = 0.5,
        scatter_size = 1,
        color_indicate = False,
        color_indicate_list = []):
    omega_dict = results_full.omega_dict
    t0_arr = results_full.t0_arr
    if t0_min is not None:
        t0_min_indx = bisect_right(t0_arr, t0_min)
    else:
        t0_min_indx = 0
    if t0_max is not None:
        t0_max_indx = bisect_right(t0_arr, t0_max)
    else:
        t0_max_indx = len(t0_arr)

    if ax is None:
        fig, ax = plt.subplots()
    omega_r_dict = omega_dict["real"]
    omega_i_dict = omega_dict["imag"]
    omega_r_list = list(omega_r_dict.values())
    omega_i_list = list(omega_i_dict.values())
    length = len(omega_r_dict)
    for i in range(length):
        if color_indicate:
            color = f"C{color_indicate_list[i]}"
        if len(plot_indxs) == 0 or i in plot_indxs:
            if indicate_start:
                ax.scatter(omega_r_list[i][t0_min_indx],
                       omega_i_list[i][t0_min_indx], alpha=1, s=15, c = color)
            ax.plot(omega_r_list[i][t0_min_indx:t0_max_indx],
                    omega_i_list[i][t0_min_indx:t0_max_indx], alpha=line_alpha, c = color)
            ax.scatter(omega_r_list[i][t0_min_indx:t0_max_indx],
                       omega_i_list[i][t0_min_indx:t0_max_indx], alpha=scatter_alpha, s=scatter_size, c = color)
    ax.invert_yaxis()


def plot_predicted_qnms(
        ax,
        predicted_qnm_list,
        predicted_qnm_list_retro = [],
        ellipse_qnm_list = [],
        ellipse_qnm_list_retro = [],
        ellipse_x = 0.05,
        ellipse_y = 0.05,
        ellipse_edgecolor = 'gray',
        ellipse_facecolor = 'lightgray',
        ellipse_alpha = 0.5,
        fix_indx = [],
        label_offset=(
            0,
            0.),
        change_lim = True,
        facecolor="none",
        edgecolor="gray",
        cut_at_0 = False,
        pred_alpha = 1,
        present_modes = [],
        present_modes_retro = [],
        edgecolor_present = 'k',
        expand_points = (1.1, 1.7),
        physical_notation = False,
        xminmin = -2,
        xmaxmax = 2,
        yminmin = 0.05,
        ymaxmax = -0.7,
        positive_y_alpha = 0.5,
        ):
    ax.axvline(0, color='gray', ls='--')
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    ax.set_xlim(max(xmin, xminmin), min(xmax, xmaxmax))
    if change_lim:
        if cut_at_0:
            ax.set_ylim(0, max(ymax, ymaxmax))
        else:
            ax.set_ylim(yminmin, max(ymax, ymaxmax))
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    texts = []
    circles = []
    for i, mode in enumerate(predicted_qnm_list + predicted_qnm_list_retro):
        if i >= len(predicted_qnm_list):
            omegar = -mode.omegar
            retro_string = r'$r$'
            if mode.string() in present_modes_retro:
                present = True
            else:
                present = False
        else:
            omegar = mode.omegar
            retro_string = ''
            if mode.string() in present_modes:
                present = True
            else:
                present = False
        if present:
            edgecolor_adj = edgecolor_present
        else:
            edgecolor_adj = edgecolor
        if xmin < omegar < xmax and ymax < mode.omegai < ymin:  # remember that y-axis is flipped
            if i in fix_indx:
                circle = ax.scatter(omegar, mode.omegai, marker='o',
                       facecolor='k', edgecolor='k')
            else:
                circle = ax.scatter(omegar, mode.omegai, marker='o',
                           facecolor=facecolor, edgecolor=edgecolor_adj, alpha = pred_alpha)
            circles.append(circle)
            transform = ax.transData.transform((omegar, mode.omegai))
            mode_ax_coord = ax.transAxes.inverted().transform(transform)
            label_ax_coord = mode_ax_coord + label_offset
            if physical_notation:
                tex_string = tex_string_physical_notation(mode)
            else:
                tex_string = mode.tex_string()
            text = ax.text(
                        *label_ax_coord,
                        retro_string + tex_string,
                        color=edgecolor_adj,
                        transform=ax.transAxes,
                        horizontalalignment="center",
                        verticalalignment="center",
                        alpha = pred_alpha
                            )
            texts.append(text)
    adjust_text(texts, expand_points=expand_points, ax = ax)
    
    ells = []
    for i, mode in enumerate(predicted_qnm_list + predicted_qnm_list_retro):
        if i >= len(predicted_qnm_list):
            omegar = -mode.omegar
        else:
            omegar = mode.omegar
        if xmin < omegar < xmax and ymax < mode.omegai < ymin:  # remember that y-axis is flipped
            ells.append(Ellipse(xy = (omegar, mode.omegai),
                     width = 2*ellipse_x, height = 2*ellipse_y,
                     fill = True, 
                     facecolor = ellipse_facecolor,
                     edgecolor = ellipse_edgecolor,
                     alpha = ellipse_alpha))
    for e in ells:
        ax.add_artist(e)
        e.set_clip_box(ax.bbox)

    ymin, ymax = ax.get_ylim()
    ax.set_ylim(ymin, ymax)
    xmin, xmax = ax.get_xlim()
    ax.set_xlim(xmin, xmax)
    ax.axhspan(0, 1e2, color="gray", alpha=positive_y_alpha)

    ax.set_xlabel(r"$M \omega_r$")
    ax.set_ylabel(r"$M \omega_i$")
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())

def plot_M(
        results_full,
        Mf = None,
        ax=None,
        t0_min=None,
        t0_max=None):
    Ma_dict = results_full.Ma_dict
    t0_arr = results_full.t0_arr
    if t0_min is not None:
        t0_min_indx = bisect_right(t0_arr, t0_min)
    else:
        t0_min_indx = 0
    if t0_max is not None:
        t0_max_indx = bisect_right(t0_arr, t0_max)
    else:
        t0_max_indx = len(t0_arr)

    if ax is None:
        fig, ax = plt.subplots()
    M = Ma_dict["M"]
    ax.plot(t0_arr[t0_min_indx:t0_max_indx], M[t0_min_indx:t0_max_indx], alpha = 0.3)
    if Mf is not None:
        ax.axhline(Mf, c = 'k', alpha = 0.5)
    ax.set_xlabel(r"$(t_0 - t_{\rm peak})/M$")
    ax.set_ylabel(r"$M$")
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    
def plot_M_a(
        results_full,
        Mf = None,
        af = None,
        ax=None,
        t0_min=None,
        t0_max=None,
        color = None,
        indicate_start = False):
    Ma_dict = results_full.Ma_dict
    t0_arr = results_full.t0_arr
    if t0_min is not None:
        t0_min_indx = bisect_right(t0_arr, t0_min)
    else:
        t0_min_indx = 0
    if t0_max is not None:
        t0_max_indx = bisect_right(t0_arr, t0_max)
    else:
        t0_max_indx = len(t0_arr)

    if ax is None:
        fig, ax = plt.subplots()
    M = Ma_dict["M"]
    a = Ma_dict["a"]
    if indicate_start:
        ax.scatter(M[t0_min_indx], a[t0_min_indx], alpha=1, s=15, c = color)
    ax.scatter(M[t0_min_indx:t0_max_indx], a[t0_min_indx:t0_max_indx], alpha=0.5, s=1, c = color)
    ax.plot(M[t0_min_indx:t0_max_indx], a[t0_min_indx:t0_max_indx], alpha = 0.2, c = color)
    if (Mf is not None) and (af is not None):
        ax.axvline(Mf, c = 'k', alpha = 0.5)
        ax.axhline(af, c = 'k', alpha = 0.5)
    ax.set_xlabel(r"$M$")
    ax.set_ylabel(r"$a$")
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())

def plot_amplitudes(results_full, fixed_modes=None, ax=None, alpha = 1, ls = "-", use_label = True,
                    legend = True, color_dict = {}, lw = 2, bold_dict = {}, lw_bold = 4, alpha_bold = 1,
                    t_flat_start_dict = {}, flat_start_s = 20, flat_start_marker = 'o', plot_retro_pred = False,
                    iota = None, af = None, phi = 0, A_fac = 1, physical_notation = True):
    colori = 0
    if ax is None:
        fig, ax = plt.subplots()
    A_fix_dict = results_full.A_fix_dict
    A_free_dict = results_full.A_free_dict
    t0_arr = results_full.t0_arr
    if fixed_modes is not None:
        if physical_notation:
            fixed_mode_string_tex_list = qnms_to_tex_string_physical_notation(fixed_modes)
        else:
            fixed_mode_string_tex_list = qnms_to_tex_string(fixed_modes)
        fixed_mode_string_list = qnms_to_string(fixed_modes)
        for i, fixed_mode_string in enumerate(fixed_mode_string_list):
                lmnx = fixed_modes[i].lmnx_retro
                if fixed_mode_string in color_dict:
                    color = color_dict[fixed_mode_string]
                else:
                    color = f"C{colori}"
                if use_label:
                    label = fixed_mode_string_tex_list[i]
                else:
                    label = None
                ax.semilogy(t0_arr, A_fac*np.abs(A_fix_dict[f"A_{fixed_mode_string}"]), 
                            lw=lw, label=label, c = color,
                            alpha = alpha, ls = ls)
                if len(lmnx) == 1 and plot_retro_pred:
                        l, m, n = lmnx[0]
                        if l > 0:
                            S_fac = S_retro_fac(iota, af, 
                                                l, m, n, phi = phi)
                            ax.semilogy(t0_arr, A_fac*np.abs(A_fix_dict[f"A_{fixed_mode_string}"])*np.abs(S_fac), 
                            lw=lw*0.7,c = color,
                            alpha = alpha, ls = '--')
                if fixed_mode_string in bold_dict:
                    start_i, end_i = bold_dict[fixed_mode_string]
                    ax.semilogy(t0_arr[start_i:end_i], 
                                A_fac*np.abs(A_fix_dict[f"A_{fixed_mode_string}"])[start_i:end_i], 
                                lw=lw_bold, c = color,
                                label = fixed_mode_string_tex_list[i],
                                alpha = alpha_bold, ls = ls)
                colori += 1
                if fixed_mode_string in t_flat_start_dict:
                    t_flat_start = t_flat_start_dict[fixed_mode_string]
                    idx = np.argmin(np.abs(t0_arr - t_flat_start))
                    ax.scatter(t0_arr[idx], A_fac*np.abs(A_fix_dict[f"A_{fixed_mode_string}"])[idx],
                               c = color, s = flat_start_s, marker = flat_start_marker)
    for A in list(A_free_dict.values()):
        ax.semilogy(t0_arr, A_fac*np.abs(A), lw=lw, c = f"C{colori}", alpha = alpha, ls = ls)
        colori += 1
    if fixed_modes is not None and use_label:
        if legend:
            ax.legend()

    ax.set_xlim(t0_arr[0], t0_arr[-1])
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.set_xlabel(r"$(t_0 - t_{\rm peak})/M$")
    ax.set_ylabel(r"$A$")
    
def plot_amplitudes_unadj(results_full, fixed_modes=None, ax=None, alpha = 1, ls = "-", use_label = True,
                          legend = True, physical_notation = True):
    colori = 0
    if ax is None:
        fig, ax = plt.subplots()
    A_fix_dict = results_full.A_fix_dict
    A_free_dict = results_full.A_free_dict
    t0_arr = results_full.t0_arr
    if fixed_modes is not None:
        if physical_notation:
            fixed_mode_string_tex_list = qnms_to_tex_string_physical_notation(fixed_modes)
        else:
            fixed_mode_string_tex_list = qnms_to_tex_string(fixed_modes)
        fixed_mode_string_list = qnms_to_string(fixed_modes)
        for i, fixed_mode_string in enumerate(fixed_mode_string_list):
                if use_label:
                    label = fixed_mode_string_tex_list[i]
                else:
                    label = None
                ax.semilogy(t0_arr, np.exp(fixed_modes[i].omegai*t0_arr)*np.abs(A_fix_dict[f"A_{fixed_mode_string}"]), 
                            lw=2, label=label, c = f"C{colori}",
                            alpha = alpha, ls = ls)
                colori += 1
    for A in list(A_free_dict.values()):
        ax.semilogy(t0_arr, np.abs(A), lw=1, c = f"C{colori}", alpha = alpha, ls = ls)
        colori += 1
    if fixed_modes is not None and use_label:
        if legend:
            ax.legend()

    ax.set_xlim(t0_arr[0], t0_arr[-1])
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.set_xlabel(r"$(t_0 - t_{\rm peak})/M$")
    ax.set_ylabel(r"$A$")


def plot_phases(results_full, fixed_modes=None, ax=None, alpha = 1, ls = "-",
                 use_label = True, shift_phase = True,
                legend = True, color_dict = {}, lw = 2, bold_dict = {}, 
                lw_bold = 4, alpha_bold = 1,
                t_flat_start_dict = {}, flat_start_s = 20, flat_start_marker = 'o',
                plot_retro_pred = False, iota = None, af = None, phi = 0,
                physical_notation = True):
    colori = 0
    if ax is None:
        fig, ax = plt.subplots()
    phi_fix_dict = results_full.phi_fix_dict
    phi_free_dict = results_full.phi_free_dict
    A_fix_dict = results_full.A_fix_dict
    A_free_dict = results_full.A_free_dict
    t0_arr = results_full.t0_arr
    if fixed_modes is not None:
        if physical_notation:
            fixed_mode_string_tex_list = qnms_to_tex_string_physical_notation(fixed_modes)
        else:
            fixed_mode_string_tex_list = qnms_to_tex_string(fixed_modes)
        fixed_mode_string_list = qnms_to_string(fixed_modes)
        for i, fixed_mode_string in enumerate(fixed_mode_string_list):
            lmnx = fixed_modes[i].lmnx_retro
            if fixed_mode_string in color_dict:
                color = color_dict[fixed_mode_string]
            else:
                color = f"C{colori}"
            phase_shift = np.where(A_fix_dict[f"A_{fixed_mode_string}"] > 0, 0, np.pi)
            t_breaks, phi_breaks = phase_break_for_plot(t0_arr, phi_fix_dict[f"phi_{fixed_mode_string}"] + phase_shift)
            if len(lmnx) == 1 and plot_retro_pred:
                l, m, n = lmnx[0]
                if l > 0:
                    S_phase_diff = S_retro_phase_diff(iota, af, 
                                        l, m, n, phi = phi)
                    t_breaks_S, phi_breaks_S = phase_break_for_plot(t0_arr, 
                                            -phi_fix_dict[f"phi_{fixed_mode_string}"] + phase_shift)
            for j, (t_break, phi_break) in enumerate(zip(t_breaks, phi_breaks)):
                if use_label:
                    label = fixed_mode_string_tex_list[i]
                else:
                    label = None
                if j == 0:
                    ax.plot(t_break, phi_break, lw=lw,
                            c=color, label = label, alpha = alpha, ls = ls)
                else:
                    ax.plot(t_break, phi_break, lw=lw, c=color, alpha = alpha, ls = ls)
            if len(lmnx) == 1 and plot_retro_pred:
                if l > 0:
                    for t_break_S, phi_break_S in zip(t_breaks_S, phi_breaks_S):
                        ax.plot(t_break_S, phi_break_S, lw=lw*0.7, c=color, alpha = alpha, ls = "--")
                

            if fixed_mode_string in bold_dict:
                start_i, end_i = bold_dict[fixed_mode_string]
                t_breaks, phi_breaks = phase_break_for_plot(
                                t0_arr[start_i:end_i], 
                                phi_fix_dict[f"phi_{fixed_mode_string}"][start_i:end_i] + phase_shift[start_i:end_i])
                for j, (t_break, phi_break) in enumerate(zip(t_breaks, phi_breaks)):
                    if use_label:
                        label = fixed_mode_string_tex_list[i]
                    else:
                        label = None
                    if j == 0:
                        ax.plot(t_break, phi_break, lw=lw_bold,
                                c=color, label = label, alpha = alpha_bold, ls = ls)
                    else:
                        ax.plot(t_break, phi_break, lw=lw_bold, c=color, alpha = alpha_bold, ls = ls)
            if fixed_mode_string in t_flat_start_dict:
                t_flat_start = t_flat_start_dict[fixed_mode_string]
                idx = np.argmin(np.abs(t0_arr - t_flat_start))
                phi_flat_start = phi_fix_dict[f"phi_{fixed_mode_string}"][idx] + phase_shift[idx]
                ax.scatter(t0_arr[idx], phi_flat_start%(2*np.pi),
                            c = color, s = flat_start_s, marker = flat_start_marker)
                
            colori += 1
    for i, phi in enumerate(list(phi_free_dict.values())):
        t_breaks, phi_breaks = phase_break_for_plot(t0_arr, phi)
        for t_break, phi_break in zip(t_breaks, phi_breaks):
            ax.plot(t_break, phi_break, lw=lw, c=f"C{colori + i}", ls = ls)
    ax.set_ylim(0, 2 * np.pi)
    if fixed_modes is not None and use_label:
        if legend:
            ax.legend()
    ax.set_xlim(t0_arr[0], t0_arr[-1])
    ax.set_yticks([0, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi])
    ax.set_yticklabels([r"$0$", r"$\pi/2$", r"$\pi$", r"$3\pi/2$", r"$2\pi$"])
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.set_xlabel(r"$(t_0 - t_{\rm peak})/M$")
    ax.set_ylabel(r"$\phi$")


def plot_mismatch(results_full, ax=None, c = 'k', make_ax = True,
                  alpha = 1):
    if ax is None:
        fig, ax = plt.subplots()
    t0_arr = results_full.t0_arr
    mismatch_arr = results_full.mismatch_arr
    ax.semilogy(t0_arr, mismatch_arr, c=c, alpha = alpha)

    if make_ax:
        ax.set_xlim(t0_arr[0], t0_arr[-1])
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.set_xlabel(r"$(t_0 - t_{\rm peak})/M$")
        ax.set_ylabel(r"$\mathcal{M}$")


def plot_mode_distance(
        result_full,
        fixed_modes,
        omega_r_tol,
        omega_i_tol,
        ax=None):
    t0_arr = result_full.t0_arr
    if ax is None:
        fig, ax = plt.subplots()
    for mode in fixed_modes:
        delta = closest_free_mode_distance(result_full, mode,
                                           r_scale=omega_r_tol,
                                           i_scale=omega_i_tol)
        ax.semilogy(t0_arr, delta, lw=2, label=mode.tex_string())
    ax.legend()

    ymin, ymax = ax.get_ylim()
    ax.set_ylim(ymin, ymax)
    ax.axhspan(1, 1e20, color="gray", alpha=0.5)
    ax.set_xlim(t0_arr[0], t0_arr[-1])
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.set_xlabel(r"$(t_0 - t_{\rm peak})/M$")
    ax.set_ylabel(r"$\tilde{\delta} \omega$")


def plot_lm_row(
        mode_searcher_vary_N,
        predicted_qnm_list=[],
        indx=None,
        axs=None,
        lm=None):
    if indx is None:
        indx = mode_searcher_vary_N.best_run_indx
    if not hasattr(axs, "__iter__"):
        fig, axs = plt.subplots(1, 7, figsize=(45, 5),
                                gridspec_kw={'width_ratios': [2, 1, 1, 1, 1, 1, 1]})
    mode_searcher = mode_searcher_vary_N.mode_searchers[indx]
    plot_omega_free(mode_searcher.full_fit.result_full,
                    ax=axs[0])
    plot_predicted_qnms(axs[0], predicted_qnm_list)
    plot_mode_distance(
        mode_searcher.full_fit.result_full,
        mode_searcher.found_modes,
        mode_searcher.mode_selector.omega_r_tol,
        mode_searcher.mode_selector.omega_i_tol,
        ax=axs[1])
    plot_amplitudes(mode_searcher.full_fit.result_full,
                    ax=axs[2])
    plot_phases(mode_searcher.full_fit.result_full,
                ax=axs[3])
    plot_amplitudes(mode_searcher_vary_N.fixed_fitters[indx].result_full,
                    fixed_modes=mode_searcher.found_modes, ax=axs[4])
    plot_phases(mode_searcher_vary_N.fixed_fitters[indx].result_full,
                fixed_modes=mode_searcher.found_modes, ax=axs[5])
    plot_mismatch(
        mode_searcher_vary_N.fixed_fitters[indx].result_full, ax=axs[6])
    if lm is not None:
        axs[0].text(0.95, 0.05, r"$\ell m = {}{}$".format(*lm), ha="right",
                    va="bottom", transform=axs[0].transAxes)


def plot_relevant_mode_search_full(
        mode_search_complete,
        predicted_qnm_list=[],
        indxs=None,
        postfix_string = "default"):

    varying_N_searcher_list = mode_search_complete.relevant_lm_mode_searcher_varying_N
    relevant_lm_list = mode_search_complete.relevant_lm_list
    n_rows = len(varying_N_searcher_list)
    if indxs is None:
        indxs = [None] * n_rows

    fig, ax_mat = plt.subplots(n_rows, 7, figsize=(45, 5 * n_rows),
                               gridspec_kw={'width_ratios': [2, 1, 1, 1, 1, 1, 1]})

    for i, ax_row in enumerate(ax_mat):
        if predicted_qnm_list == []:
            predicted_qnm_list_lm = varying_N_searcher_list[i].mode_searcher_vary_N.mode_searchers[0].potential_modes_full
        else:
            predicted_qnm_list_lm = predicted_qnm_list
        plot_lm_row(varying_N_searcher_list[i].mode_searcher_vary_N,
                    predicted_qnm_list=predicted_qnm_list_lm,
                    indx=indxs[i], axs=ax_row, lm=relevant_lm_list[i])

    fig.tight_layout()
    save_file_path = os.path.join(PLOT_SAVE_PATH, f"lmplots/{mode_search_complete.SXSnum}_{postfix_string}.pdf")
    
    plt.savefig(save_file_path)


def phase_break_for_plot(times, phis_in):
    phis = phis_in % (2 * np.pi)
    timeslist = []
    phislist = []
    j = 0
    for i in range(len(phis) - 1):
        if (phis[i] < 1 and phis[i + 1] > 2 * np.pi - 1):
            if i - j > 0:
                timeslist.append(times[i - j:i + 2])
                phiseg = np.copy(phis[i - j:i + 2])
                phiseg[0] += nextadjust
            else:
                timeslist.append(times[i - j:i + 2])
                phiseg = np.copy(phis[i - j:i + 2])
            phiseg[-1] -= 2 * np.pi
            phislist.append(phiseg)
            nextadjust = 2 * np.pi
            j = 0
        elif (phis[i + 1] < 1 and phis[i] > 2 * np.pi - 1):
            if i - j > 0:
                timeslist.append(times[i - j:i + 2])
                phiseg = np.copy(phis[i - j:i + 2])
                phiseg[0] += nextadjust
            else:
                timeslist.append(times[i - j:i + 2])
                phiseg = np.copy(phis[i - j:i + 2])
            phiseg[-1] += 2 * np.pi
            phislist.append(phiseg)
            nextadjust = -2 * np.pi
            j = 0
        if i == len(phis) - 2:
            if i - j > 0:
                timeslist.append(times[i - j:i + 2])
                phiseg = np.copy(phis[i - j:i + 2])
                phiseg[0] += nextadjust
            else:
                timeslist.append(times[i - j:i + 2])
                phiseg = np.copy(phis[i - j:i + 2])
            phislist.append(phiseg)
        j += 1
    return timeslist, phislist


def mode_plot_3D(df, l, m, mode_string_pro, mode_string_retro, quantile_low = 0.01, quantile_hi = 0.99):
    df_mode = df.loc[((df["l"] == l) & (df["m"] == m) & (df["mode_string"] == mode_string_pro) & (df["retro"] == False)) | 
              ((df["l"] == l) & (df["m"] == m) & (df["mode_string"] == mode_string_retro)& (df["retro"] == True))]
    xyz = df[["SXS_num", "chi_1_z", "chi_2_z", "q"]].drop_duplicates()
    df_missing = xyz[(~xyz["SXS_num"].isin(df_mode["SXS_num"]))]
    
    fig, axs = plt.subplots(2,2, figsize = (9, 7))
    
    vmin = np.quantile(np.log10(df_mode["A_med"]), quantile_low)
    vmax = np.quantile(np.log10(df_mode["A_med"]), quantile_hi)
    
    axs[1,1].scatter(df_mode["chi_1_z"], df_mode["chi_2_z"], c=np.log10(df_mode["A_med"]), vmin = vmin, vmax = vmax)
    axs[1,1].scatter(df_missing["chi_1_z"], df_missing["chi_2_z"], c = "gray", alpha = 0.1)
    axs[1,1].set_xlabel(r"$\chi_1$")
    axs[1,1].set_ylabel(r"$\chi_2$")
    axs[1,0].scatter(df_mode["chi_1_z"], df_mode["q"], c=np.log10(df_mode["A_med"]), vmin = vmin, vmax = vmax)
    axs[1,0].scatter(df_missing["chi_1_z"], df_missing["q"], c = "gray", alpha = 0.1)
    axs[1,0].set_xlabel(r"$\chi_1$")
    axs[1,0].set_ylabel(r"$q$")
    axs[0,1].scatter(df_mode["chi_2_z"], df_mode["q"], c=np.log10(df_mode["A_med"]), vmin = vmin, vmax = vmax)
    axs[0,1].scatter(df_missing["chi_2_z"], df_missing["q"], c = "gray", alpha = 0.1)
    axs[0,1].set_xlabel(r"$\chi_2$")
    axs[0,1].set_ylabel(r"$q$")
    
    axs[0,0].remove()

    ax = fig.add_subplot(2,2,1,projection='3d')
    sc = ax.scatter3D(df_mode["chi_1_z"], df_mode["chi_2_z"], df_mode["q"], c = np.log10(df_mode["A_med"]), vmin = vmin, vmax = vmax)
    ax.scatter3D(df_missing["chi_1_z"], df_missing["chi_2_z"], df_missing["q"], c = "gray", alpha = 0.1)
    sc = ax.scatter3D(df_mode["chi_1_z"], df_mode["chi_2_z"], df_mode["q"], c = np.log10(df_mode["A_med"]), vmin = vmin, vmax = vmax)
    for i in range(len(sc.get_facecolors())):
        ax.plot([df_mode["chi_1_z"].to_numpy()[i], df_mode["chi_1_z"].to_numpy()[i]], 
                [df_mode["chi_2_z"].to_numpy()[i], df_mode["chi_2_z"].to_numpy()[i]], 
                [1, df_mode["q"].to_numpy()[i]], c = sc.get_facecolors()[i].tolist(), alpha = 0.5, lw = 1.5)
    ax.scatter3D(df_missing["chi_1_z"], df_missing["chi_2_z"], df_missing["q"], c = "gray", alpha = 0.2)
    for i in range(len(df_missing["chi_1_z"].to_numpy())):
        ax.plot([df_missing["chi_1_z"].to_numpy()[i], df_missing["chi_1_z"].to_numpy()[i]], 
                [df_missing["chi_2_z"].to_numpy()[i], df_missing["chi_2_z"].to_numpy()[i]], 
                [1, df_missing["q"].to_numpy()[i]], c = "gray", alpha = 0.2, lw = 1.5)
    ax.set_xlabel(r"$\chi_1$", fontsize = 12, labelpad = -4)
    ax.set_ylabel(r"$\chi_2$", fontsize = 12, labelpad = -4)
    ax.set_zlabel(r"$q$", fontsize = 12, labelpad = -4)
    ax.tick_params(axis = 'x', labelsize = 9, pad = -0.75)
    ax.tick_params(axis = 'y', labelsize = 9, pad = -0.75)
    ax.tick_params(axis = 'z', labelsize = 9, pad = -0.75)
    
    # fig.tight_layout()
    fig.suptitle(f"{mode_string_pro} in lm = {l}{m}", fontsize = 24)
    fig.subplots_adjust(right=0.9,wspace=0.25, hspace=0.3)
    ax.set_position([0,0.45,0.55,0.55])
    cb_ax = fig.add_axes([0.93, 0.2, 0.02, 0.6])
    cbar = fig.colorbar(sc, cax=cb_ax)
    cb_ax.set_ylabel(r"$\log_{10} A$")

def mode_plot_3D_eta(df, l, m, mode_string_pro, mode_string_retro, quantile_low = 0.01, quantile_hi = 0.99,
                     adjust_eta = True, adjust_delta = False, plot_log = True, eta_cut = 0.2499,
                     adjust_eta_poly = "1"):
    if adjust_delta:
        df_mode = df.loc[(((df["l"] == l) & (df["m"] == m) & (df["mode_string"] == mode_string_pro) & (df["retro"] == False)) | 
                        ((df["l"] == l) & (df["m"] == m) & (df["mode_string"] == mode_string_retro)& (df["retro"] == True))) & (df['eta'] < eta_cut)]
    else:
        df_mode = df.loc[((df["l"] == l) & (df["m"] == m) & (df["mode_string"] == mode_string_pro) & (df["retro"] == False)) | 
              ((df["l"] == l) & (df["m"] == m) & (df["mode_string"] == mode_string_retro)& (df["retro"] == True))]
    xyz = df[["SXS_num", "chi_1_z", "chi_2_z", "eta"]].drop_duplicates()
    df_missing = xyz[(~xyz["SXS_num"].isin(df_mode["SXS_num"]))]
    
    fig, axs = plt.subplots(2,2, figsize = (9, 7))
    
    A = df_mode["A_med"]
    if adjust_eta:
        A /= df_mode["eta"]
    if adjust_delta:
        A /= np.sqrt(1 - 4*df_mode["eta"])
    x = df_mode["eta"]
    eta_poly = eval(adjust_eta_poly)
    A /= eta_poly

    if plot_log:
        A_plot = np.log10(A)
    else:
        A_plot = A

    vmin = np.quantile(A_plot, quantile_low)
    vmax = np.quantile(A_plot, quantile_hi)
    
    axs[1,1].scatter(df_mode["chi_1_z"], df_mode["chi_2_z"], c=A_plot, vmin = vmin, vmax = vmax)
    axs[1,1].scatter(df_missing["chi_1_z"], df_missing["chi_2_z"], c = "gray", alpha = 0.1)
    axs[1,1].set_xlabel(r"$\chi_1$")
    axs[1,1].set_ylabel(r"$\chi_2$")
    axs[1,0].scatter(df_mode["chi_1_z"], df_mode["eta"], c=A_plot, vmin = vmin, vmax = vmax)
    axs[1,0].scatter(df_missing["chi_1_z"], df_missing["eta"], c = "gray", alpha = 0.1)
    axs[1,0].set_xlabel(r"$\chi_1$")
    axs[1,0].set_ylabel(r"$\eta$")
    axs[1,0].invert_yaxis()
    axs[0,1].scatter(df_mode["chi_2_z"], df_mode["eta"], c=A_plot, vmin = vmin, vmax = vmax)
    axs[0,1].scatter(df_missing["chi_2_z"], df_missing["eta"], c = "gray", alpha = 0.1)
    axs[0,1].set_xlabel(r"$\chi_2$")
    axs[0,1].set_ylabel(r"$\eta$")
    axs[0,1].invert_yaxis()
    
    axs[0,0].remove()

    ax = fig.add_subplot(2,2,1,projection='3d')
    sc = ax.scatter3D(df_mode["chi_1_z"], df_mode["chi_2_z"], df_mode["eta"], c = A_plot, vmin = vmin, vmax = vmax)
    ax.scatter3D(df_missing["chi_1_z"], df_missing["chi_2_z"], df_missing["eta"], c = "gray", alpha = 0.1)
    sc = ax.scatter3D(df_mode["chi_1_z"], df_mode["chi_2_z"], df_mode["eta"], c = A_plot, vmin = vmin, vmax = vmax)
    for i in range(len(sc.get_facecolors())):
        ax.plot([df_mode["chi_1_z"].to_numpy()[i], df_mode["chi_1_z"].to_numpy()[i]], 
                [df_mode["chi_2_z"].to_numpy()[i], df_mode["chi_2_z"].to_numpy()[i]], 
                [0.25, df_mode["eta"].to_numpy()[i]], c = sc.get_facecolors()[i].tolist(), alpha = 0.5, lw = 1.5)
    ax.scatter3D(df_missing["chi_1_z"], df_missing["chi_2_z"], df_missing["eta"], c = "gray", alpha = 0.2)
    for i in range(len(df_missing["chi_1_z"].to_numpy())):
        ax.plot([df_missing["chi_1_z"].to_numpy()[i], df_missing["chi_1_z"].to_numpy()[i]], 
                [df_missing["chi_2_z"].to_numpy()[i], df_missing["chi_2_z"].to_numpy()[i]], 
                [0.25, df_missing["eta"].to_numpy()[i]], c = "gray", alpha = 0.2, lw = 1.5)
    ax.set_xlabel(r"$\chi_1$", fontsize = 12, labelpad = -4)
    ax.set_ylabel(r"$\chi_2$", fontsize = 12, labelpad = -4)
    ax.set_zlabel(r"$\eta$", fontsize = 12, labelpad = -4)
    ax.tick_params(axis = 'x', labelsize = 9, pad = -0.75)
    ax.tick_params(axis = 'y', labelsize = 9, pad = -0.75)
    ax.tick_params(axis = 'z', labelsize = 9, pad = -0.75)
    ax.invert_zaxis()
    
    # fig.tight_layout()
    fig.suptitle(f"{mode_string_pro} in lm = {l}{m}", fontsize = 24)
    fig.subplots_adjust(right=0.9,wspace=0.25, hspace=0.3)
    ax.set_position([0,0.45,0.55,0.55])
    cb_ax = fig.add_axes([0.93, 0.2, 0.02, 0.6])
    cbar = fig.colorbar(sc, cax=cb_ax)
    if plot_log:
        cb_ax.set_ylabel(r"$\log_{10} A$")
    else:
        cb_ax.set_ylabel(r"$A$")

def linfunc(p, x):
    m, c= p
    return m * x + c 

def linfunc1(p, x):
    c = p
    return x + c 

def linfunc2(p, x):
    c = p
    return 2*x + c 

def linfunc3(p, x):
    m = p
    return m * x

def adjust_phase_for_fit(xs, ys):
    xs_2pi = xs % (2*np.pi)
    ys_2pi = ys % (2*np.pi)
    ys_adj_1 = np.where(ys_2pi < (xs_2pi + np.pi), ys_2pi, ys_2pi - 2*np.pi)
    ys_adj_2 = np.where(ys_adj_1 > (xs_2pi - np.pi), ys_adj_1, ys_adj_1 + 2*np.pi)
    return xs_2pi, ys_adj_2

def plot_mode_vs_lin_mode_ampltiude(df, l_quad, m_quad, mode_string_pro_quad, mode_string_retro_quad, l1, m1, mode_string_pro_1, mode_string_retro_1,
                                    l2, m2, mode_string_pro_2, mode_string_retro_2, fit_type = "agnostic",
                                    colorbar = True,
                                    return_sc = False, ax = None,
                                    fit = False,
                                    skip_num = [],
                                    norm = None):
    df_1 = df.loc[((df["l"] == l1) & (df["m"] == m1) & (df["mode_string"] == mode_string_pro_1) & (df["retro"] == False)) |
                ((df["l"] == l1) & (df["m"] == m1) & (df["mode_string"] == mode_string_retro_1)& (df["retro"] == True))]
    df_2 = df.loc[((df["l"] == l2) & (df["m"] == m2) & (df["mode_string"] == mode_string_pro_2) & (df["retro"] == False)) |
                ((df["l"] == l2) & (df["m"] == m2) & (df["mode_string"] == mode_string_retro_2)& (df["retro"] == True))]
    df_quad = df.loc[((df["l"] == l_quad) & (df["m"] == m_quad) & (df["mode_string"] == mode_string_pro_quad) & (df["retro"] == False)) |
                ((df["l"] == l_quad) & (df["m"] == m_quad) & (df["mode_string"] == mode_string_retro_quad)& (df["retro"] == True))]
    df_merged_lin = df_1.merge(df_2, on = "SXS_num", how = "inner", suffixes = ("_1", "_2"))
    df_merged = df_merged_lin.merge(df_quad, on = "SXS_num", how = "inner")
    df_merged = df_merged.loc[~df_merged["SXS_num"].isin(skip_num)]
    df_merged.reset_index(drop = True, inplace = True)
    xerr = np.sqrt((df_merged["A_hi_1"]-df_merged["A_low_1"])**2 + (df_merged["A_hi_2"]-df_merged["A_low_2"])**2)
    yerr = df_merged["A_hi"] - df_merged["A_low"]
    errxlogs = xerr/(df_merged["A_med_1"]*df_merged["A_med_2"])/np.log(10)
    errylogs = yerr/df_merged["A_med"]/np.log(10)
    xs = df_merged["A_med_1"]*df_merged["A_med_2"]*df_merged["M_rem_1"]**2
    ys = df_merged["A_med"]*df_merged["M_rem_1"]
    if fit:
        fitfunc = linfunc3
        beta0 = [0.]
        lin_model = Model(fitfunc)
        data = RealData(xs, ys, 
                        sx=xerr, sy=yerr)
        odr = ODR(data, lin_model, beta0=beta0)
        out = odr.run()
    if ax == None:
        fig, ax = plt.subplots(figsize = (8,5))
    sc = ax.scatter(xs, ys, c = df_merged["chi_rem_1"], cmap = "cividis", norm = norm)
    plt.draw()
    for i in range(len(sc.get_facecolors())):
        ax.errorbar(xs[i], ys[i], xerr = xerr.to_numpy()[i],
                 yerr = yerr.to_numpy()[i], ecolor = sc.get_facecolors()[i].tolist(),
                     fmt = "None")
    if colorbar:
        cb = fig.colorbar(sc, ax = ax)
        cb.ax.set_ylabel(r"$\chi_{\rm rem}$")

    x_lim = ax.get_xlim()

    if fit:
        xsfit = np.linspace(*x_lim, num = 100)
        ax.plot(xsfit, fitfunc(out.beta, xsfit), c = "k", ls = "--")
    xlabel_string = r"$A_{{{}}} \times A_{{{}}}$".format(mode_string_pro_1, mode_string_pro_2)
    ylabel_string = r"$A_{{{}}}$".format(mode_string_pro_quad)
    ax.set_xlabel(xlabel_string.replace('x', r" \times "))
    ax.set_ylabel(ylabel_string.replace('x', r" \times "))

    ax.set_xlim(*x_lim)

    if return_sc:
        return sc, out.beta
    else:
        return out.beta

def plot_mode_vs_lin_mode_phase(df, l_quad, m_quad, mode_string_pro_quad, mode_string_retro_quad, l1, m1, mode_string_pro_1, mode_string_retro_1,
                                l2, m2, mode_string_pro_2, mode_string_retro_2, fit_type = "agnostic",
                                colorbar = True,
                                return_sc = False, ax = None,
                                fit_fac = 1, fit = False,
                                skip_num = [],
                                norm = None):
    df_1 = df.loc[((df["l"] == l1) & (df["m"] == m1) & (df["mode_string"] == mode_string_pro_1) & (df["retro"] == False)) |
                ((df["l"] == l1) & (df["m"] == m1) & (df["mode_string"] == mode_string_retro_1)& (df["retro"] == True))]
    df_2 = df.loc[((df["l"] == l2) & (df["m"] == m2) & (df["mode_string"] == mode_string_pro_2) & (df["retro"] == False)) |
                ((df["l"] == l2) & (df["m"] == m2) & (df["mode_string"] == mode_string_retro_2)& (df["retro"] == True))]
    df_quad = df.loc[((df["l"] == l_quad) & (df["m"] == m_quad) & (df["mode_string"] == mode_string_pro_quad) & (df["retro"] == False)) |
                ((df["l"] == l_quad) & (df["m"] == m_quad) & (df["mode_string"] == mode_string_retro_quad)& (df["retro"] == True))]
    df_merged_lin = df_1.merge(df_2, on = "SXS_num", how = "inner", suffixes = ("_1", "_2"))
    df_merged = df_merged_lin.merge(df_quad, on = "SXS_num", how = "inner")
    df_merged = df_merged.loc[~df_merged["SXS_num"].isin(skip_num)]
    df_merged.reset_index(drop = True, inplace = True)
    xerr = np.sqrt((df_merged["phi_hi_1"]-df_merged["phi_low_1"])**2 + (df_merged["phi_hi_2"]-df_merged["phi_low_2"])**2)
    yerr = df_merged["phi_hi"] - df_merged["phi_low"]
    xs = df_merged["phi_med_1"] + df_merged["phi_med_2"]
    ys = df_merged["phi_med"]
    if fit:
        fitfunc = linfunc1
        beta0 = [0.]
        lin_model = Model(fitfunc)
        xs_adj, ys_adj = adjust_phase_for_fit(xs, ys)
        data = RealData(xs_adj, ys_adj, 
                        sx=xerr, sy=yerr)
        odr = ODR(data, lin_model, beta0=beta0)
        out = odr.run() 

    if ax == None:
        fig, ax = plt.subplots(figsize = (8,5))
    sc = ax.scatter(fit_fac*xs%(2*np.pi), ys%(2*np.pi), c = df_merged["chi_rem_1"], 
                    cmap = "cividis", norm = norm)
    plt.draw()
    for i in range(len(sc.get_facecolors())):
        ax.errorbar(fit_fac*xs[i]%(2*np.pi), ys[i]%(2*np.pi), xerr = xerr.to_numpy()[i],
                 yerr = yerr.to_numpy()[i], ecolor = sc.get_facecolors()[i].tolist(),
                     fmt = "None")
    if colorbar:
        cb = fig.colorbar(sc)
        cb.ax.set_ylabel(r"$\chi_{\rm rem}$")
    ax.set_xlim(0, 2*np.pi)
    ax.set_ylim(0, 2*np.pi)
    ax.set_xticks([0, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi])
    ax.set_xticklabels(["0", r"$\pi/2$", r"$\pi$", r"$3\pi/2$", r"$2\pi$"])
    ax.set_yticks([0, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi])
    ax.set_yticklabels(["0", r"$\pi/2$", r"$\pi$", r"$3\pi/2$", r"$2\pi$"])

    x_lim = ax.get_xlim()

    if fit:
        xsfit = np.linspace(*x_lim, num = 100)
        ysfit = fitfunc(out.beta, xsfit)
        ax.plot(xsfit, ysfit, c = "k", ls = "--")
        ax.plot(xsfit, ysfit + 2*np.pi, c = "k", ls = "--")
        ax.plot(xsfit, ysfit - 2*np.pi, c = "k", ls = "--")
    # ax.plot(xsfit, ysfit, c = "k", ls = ":")
    xlabel_string = r"$\phi_{{{}}} + \phi_{{{}}}$".format(mode_string_pro_1, mode_string_pro_2)
    ylabel_string = r"$\phi_{{{}}}$".format(mode_string_pro_quad)
    ax.set_xlabel(xlabel_string.replace('x', r" \times "))
    ax.set_ylabel(ylabel_string.replace('x', r" \times "))

    if return_sc:
        return sc, out.beta
    else:
        return out.beta
    
def plot_mode_vs_mode_amplitude(df, l1, m1, mode_string_pro_1, mode_string_retro_1,
                                l2, m2, mode_string_pro_2, mode_string_retro_2, fit_type = "agnostic",
                                fig = None, ax = None, colorbar = True, return_sc = False,
                                fit = False,
                                skip_num = [],
                                norm = None):
    df_1 = df.loc[((df["l"] == l1) & (df["m"] == m1) & (df["mode_string"] == mode_string_pro_1) & (df["retro"] == False)) | 
              ((df["l"] == l1) & (df["m"] == m1) & (df["mode_string"] == mode_string_retro_1)& (df["retro"] == True))]
    df_2 = df.loc[((df["l"] == l2) & (df["m"] == m2) & (df["mode_string"] == mode_string_pro_2) & (df["retro"] == False)) | 
              ((df["l"] == l2) & (df["m"] == m2) & (df["mode_string"] == mode_string_retro_2)& (df["retro"] == True))]
    df_merged_raw = df_1.merge(df_2, on = "SXS_num", how = "inner", suffixes = ("_1", "_2"))
    df_merged = df_merged_raw[~df_merged_raw["SXS_num"].isin(skip_num)]
    df_merged.reset_index(drop=True, inplace = True)
    xerr_low = df_merged["A_med_2"]-df_merged["A_low_2"]
    xerr_hi = df_merged["A_hi_2"]-df_merged["A_med_2"]
    yerr_low = df_merged["A_med_1"]-df_merged["A_low_1"]
    yerr_hi = df_merged["A_hi_1"]-df_merged["A_med_1"]
    xerr = xerr_low + xerr_hi
    yerr = yerr_low + yerr_hi
    xs = df_merged["A_med_2"]
    ys = df_merged["A_med_1"]
    
    if fit:
        if fit_type == "linear":
            fitfunc = linfunc1
            beta0 = [0.]
        if fit_type == "quadratic":
            fitfunc = linfunc2
            beta0 = [0.]
        if fit_type == "agnostic":
            fitfunc = linfunc
            beta0 = [1., 0.]
        lin_model = Model(fitfunc)
        errxlogs = (xerr)/xs/np.log(10)
        errylogs = (yerr)/ys/np.log(10)
        data = RealData(np.log10(xs), np.log10(ys), 
                        sx=errxlogs, sy=errylogs)
        odr = ODR(data, lin_model, beta0=beta0)
        out = odr.run()
    
    if ax == None:
        fig, ax = plt.subplots(figsize = (8,5))
    sc = ax.scatter(xs, ys, c = df_merged["chi_rem_1"], cmap = "cividis", norm = norm)
    plt.draw()
    xerr_max = 0
    for i in range(len(sc.get_facecolors())):
        ax.errorbar(xs[i], ys[i], xerr = xerr[i],
                 yerr = yerr[i], ecolor = sc.get_facecolors()[i].tolist(),
                     fmt = "None")
    #     if xerr.to_numpy()[i] > xerr_max:
    #         xerr_max_SXS_num = df_merged["SXS_num"].to_numpy()[i]
    #         xerr_max = xerr.to_numpy()[i]
    # print(xerr_max_SXS_num, xerr_max)
    if colorbar:
        cb = fig.colorbar(sc, ax = ax)
        cb.ax.set_ylabel(r"$\chi_{\rm rem}$")
    x_lim = ax.get_xlim()
    if fit:
        xsfit = np.linspace(*x_lim, num = 100)
        ysfit = fitfunc(out.beta, np.log10(xsfit))
        ax.loglog(xsfit, 10**ysfit, c = "k", ls = "--")
    xlabel_string = r"$A_{{{}}}$".format(mode_string_pro_2)
    ylabel_string = r"$A_{{{}}}$".format(mode_string_pro_1)
    ax.set_xlabel(xlabel_string.replace('x', r" \times "))
    ax.set_ylabel(ylabel_string.replace('x', r" \times "))

    ax.set_xlim(*x_lim)

    if return_sc:
        return sc, out.beta
    else:
        return out.beta
    
def plot_mode_vs_mode_phase(df, l1, m1, mode_string_pro_1, mode_string_retro_1,
                                l2, m2, mode_string_pro_2, mode_string_retro_2, fit_type = "quadratic",
                                fig = None, ax = None, colorbar = True, return_sc = False, fit = False,
                                skip_num = [], norm = None):
    if fit_type == "quadratic":
        fit_fac = 2
    elif fit_type == "linear":
        fit_fac = 1
    else:
        raise ValueError
    df_1 = df.loc[((df["l"] == l1) & (df["m"] == m1) & (df["mode_string"] == mode_string_pro_1) & (df["retro"] == False)) | 
              ((df["l"] == l1) & (df["m"] == m1) & (df["mode_string"] == mode_string_retro_1)& (df["retro"] == True))]
    df_2 = df.loc[((df["l"] == l2) & (df["m"] == m2) & (df["mode_string"] == mode_string_pro_2) & (df["retro"] == False)) | 
              ((df["l"] == l2) & (df["m"] == m2) & (df["mode_string"] == mode_string_retro_2)& (df["retro"] == True))]
    df_merged = df_1.merge(df_2, on = "SXS_num", how = "inner", suffixes = ("_1", "_2")) 
    df_merged = df_merged.loc[~df_merged["SXS_num"].isin(skip_num)]  
    df_merged.reset_index(drop=True, inplace = True) 
    xerr_low = df_merged["phi_med_2"]-df_merged["phi_low_2"]
    xerr_hi = df_merged["phi_hi_2"]-df_merged["phi_med_2"]
    yerr_low = df_merged["phi_med_1"]-df_merged["phi_low_1"]
    yerr_hi = df_merged["phi_hi_1"]-df_merged["phi_med_1"]
    xerr = xerr_low + xerr_hi
    yerr = yerr_low + yerr_hi
    xs = df_merged["phi_med_2"]
    ys = df_merged["phi_med_1"]

    if fit:
        fitfunc = linfunc1
        beta0 = [0.]
        lin_model = Model(fitfunc)
        xs_adj, ys_adj = adjust_phase_for_fit(fit_fac*xs, ys)
        data = RealData(xs_adj, ys_adj, 
                        sx=xerr_low + xerr_hi, sy=yerr_low + yerr_hi)
        odr = ODR(data, lin_model, beta0=beta0)
        out = odr.run()

    if ax == None:
        fig, ax = plt.subplots(figsize = (8,5))
    sc = ax.scatter(fit_fac*xs%(2*np.pi), ys%(2*np.pi), c = df_merged["chi_rem_1"], 
                    cmap = "cividis", norm = norm)
    plt.draw()
    for i in range(len(sc.get_facecolors())):
        ax.errorbar(fit_fac*xs[i]%(2*np.pi), ys[i]%(2*np.pi), xerr = xerr.to_numpy()[i],
                 yerr = yerr.to_numpy()[i], ecolor = sc.get_facecolors()[i].tolist(),
                     fmt = "None")
    if colorbar:
        cb = fig.colorbar(sc)
        cb.ax.set_ylabel(r"$\chi_{\rm rem}$")

    x_lim = ax.get_xlim()

    if fit:
        xsfit = np.linspace(*x_lim, num = 100)
        ysfit = fitfunc(out.beta, xsfit)
        ax.plot(xsfit, ysfit, c = "k", ls = "--")
        ax.plot(xsfit, ysfit + 2*np.pi, c = "k", ls = "--")
        ax.plot(xsfit, ysfit - 2*np.pi, c = "k", ls = "--")

    ax.set_xlim(0, 2*np.pi)
    ax.set_ylim(0, 2*np.pi)
    ax.set_xticks([0, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi])
    ax.set_xticklabels(["0", r"$\pi/2$", r"$\pi$", r"$3\pi/2$", r"$2\pi$"])
    ax.set_yticks([0, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi])
    ax.set_yticklabels(["0", r"$\pi/2$", r"$\pi$", r"$3\pi/2$", r"$2\pi$"])
    xsfit = np.linspace(0, 2*np.pi, num = 100)
    ysfit = xsfit
    # ax.plot(xsfit, ysfit, c = "k", ls = ":")
    xlabel_string = r"${}\phi_{{{}}}$".format(fit_fac, mode_string_pro_2)
    ylabel_string = r"$\phi_{{{}}}$".format(mode_string_pro_1)
    ax.set_xlabel(xlabel_string.replace('x', r" \times "))
    ax.set_ylabel(ylabel_string.replace('x', r" \times "))

    if return_sc:
        return sc, out.beta
    else:
        return out.beta

def plot_mode_vs_lin_mode_ratio(df, l_quad, m_quad, mode_string_pro_quad, mode_string_retro_quad, l1, m1, mode_string_pro_1, mode_string_retro_1,
                                    l2, m2, mode_string_pro_2, mode_string_retro_2, fit_type = "agnostic",
                                    colorbar = True,
                                    return_sc = False, fig = None, ax = None,
                                    fit = False,
                                    skip_num = [],
                                    norm = None,
                                    eta_color = True):
    df_1 = df.loc[((df["l"] == l1) & (df["m"] == m1) & (df["mode_string"] == mode_string_pro_1) & (df["retro"] == False)) |
                ((df["l"] == l1) & (df["m"] == m1) & (df["mode_string"] == mode_string_retro_1)& (df["retro"] == True))]
    df_2 = df.loc[((df["l"] == l2) & (df["m"] == m2) & (df["mode_string"] == mode_string_pro_2) & (df["retro"] == False)) |
                ((df["l"] == l2) & (df["m"] == m2) & (df["mode_string"] == mode_string_retro_2)& (df["retro"] == True))]
    df_quad = df.loc[((df["l"] == l_quad) & (df["m"] == m_quad) & (df["mode_string"] == mode_string_pro_quad) & (df["retro"] == False)) |
                ((df["l"] == l_quad) & (df["m"] == m_quad) & (df["mode_string"] == mode_string_retro_quad)& (df["retro"] == True))]
    df_merged_lin = df_1.merge(df_2, on = "SXS_num", how = "inner", suffixes = ("_1", "_2"))
    df_merged = df_merged_lin.merge(df_quad, on = "SXS_num", how = "inner")
    df_merged = df_merged.loc[~df_merged["SXS_num"].isin(skip_num)]
    df_merged.reset_index(drop=True, inplace = True)
    xerr = np.sqrt((df_merged["A_hi_1"]-df_merged["A_low_1"])**2 + (df_merged["A_hi_2"]-df_merged["A_low_2"])**2)
    yerr = df_merged["A_hi"] - df_merged["A_low"]
    errxlogs = xerr/(df_merged["A_med_1"]*df_merged["A_med_2"])/np.log(10)
    errylogs = yerr/df_merged["A_med"]/np.log(10)
    xs = df_merged["A_med_1"]*df_merged["A_med_2"]*df_merged["M_rem_1"]**2
    ys = df_merged["A_med"]*df_merged["M_rem_1"]
    chis = df_merged["chi_rem_1"]
    etas = df_merged["eta_1"]
    ratio = ys/xs
    ratio_err = ratio*np.sqrt((yerr/ys)**2+(xerr/xs)**2)
    
    if ax == None:
        fig, ax = plt.subplots(figsize = (8,5))
    if ax == None:
        fig, ax = plt.subplots(figsize = (8,5))
    if eta_color:
        sc = ax.scatter(chis, ratio, c = etas)
    else:
        sc = ax.scatter(chis, ratio, c = chis, cmap = "cividis", norm = norm)
    plt.draw()
    for i in range(len(sc.get_facecolors())):
        ax.errorbar(chis[i], ratio[i],
                 yerr = ratio_err.to_numpy()[i], ecolor = sc.get_facecolors()[i].tolist(),
                     fmt = "None")
    if colorbar:
        cb = fig.colorbar(sc, ax = ax)
        if eta_color:
            cb.ax.set_ylabel(r"$\eta$")
        else:
            cb.ax.set_ylabel(r"$\chi_{\rm rem}$")

    x_lim = ax.get_xlim()

    if fit:
        fitfunc = lin_func_scipy
        out = curve_fit(fitfunc, chis, ratio, sigma = ratio_err, absolute_sigma = True)
        xsfit = np.linspace(*x_lim, num = 100)
        ysfit = fitfunc(xsfit, *out[0])
        ax.plot(xsfit, ysfit, c = "gray", ls = ":")
    
        ax.set_xlim(*x_lim)

        return out
    return

def lin_func_scipy(x, m, c):
    return m*x + c

def plot_mode_vs_mode_amplitude_quad_ratio(df, l1, m1, mode_string_pro_1, mode_string_retro_1,
                                l2, m2, mode_string_pro_2, mode_string_retro_2, fit_type = "agnostic",
                                fig = None, ax = None, colorbar = True, return_sc = False, fit = False,
                                skip_num = [], norm = None, color_string = "eta", label_SXS = False,
                                outlier_tol = 0.4):
    df_1 = df.loc[((df["l"] == l1) & (df["m"] == m1) & (df["mode_string"] == mode_string_pro_1) & (df["retro"] == False)) | 
              ((df["l"] == l1) & (df["m"] == m1) & (df["mode_string"] == mode_string_retro_1)& (df["retro"] == True))]
    df_2 = df.loc[((df["l"] == l2) & (df["m"] == m2) & (df["mode_string"] == mode_string_pro_2) & (df["retro"] == False)) | 
              ((df["l"] == l2) & (df["m"] == m2) & (df["mode_string"] == mode_string_retro_2)& (df["retro"] == True))]
    df_merged = df_1.merge(df_2, on = "SXS_num", how = "inner", suffixes = ("_1", "_2"))
    df_merged = df_merged.loc[~df_merged["SXS_num"].isin(skip_num)]
    df_merged.reset_index(drop=True, inplace = True)
    xerr_low = df_merged["A_med_2"]-df_merged["A_low_2"]
    xerr_hi = df_merged["A_hi_2"]-df_merged["A_med_2"]
    yerr_low = df_merged["A_med_1"]-df_merged["A_low_1"]
    yerr_hi = df_merged["A_hi_1"]-df_merged["A_med_1"]
    xerr = xerr_low + xerr_hi
    yerr = yerr_low + yerr_hi
    xs = df_merged["A_med_2"]
    ys = df_merged["A_med_1"]
    chis = df_merged["chi_rem_1"]
    etas = df_merged["eta_1"]
    chi_ps = df_merged["chi_p_1"]
    chi_ms = df_merged["chi_m_1"]
    ratio = ys/xs**2
    ratio_err = ratio*np.sqrt((yerr/ys)**2+(2*xerr/xs)**2)
    
    if ax == None:
        fig, ax = plt.subplots(figsize = (8,5))

    if color_string == "eta":
        sc = ax.scatter(chis, ratio, c = etas)
    elif color_string == "chi_p":
        sc = ax.scatter(chis, ratio, c = chi_ps)
    elif color_string == "chi_m":
        sc = ax.scatter(chis, ratio, c = chi_ms)
    else:
        sc = ax.scatter(chis, ratio, c = chis, cmap = "cividis", norm = norm)
    plt.draw()
    for i in range(len(sc.get_facecolors())):
        ax.errorbar(chis[i], ratio[i],
                 yerr = ratio_err.to_numpy()[i], ecolor = sc.get_facecolors()[i].tolist(),
                     fmt = "None")
        if label_SXS:
            ax.text(chis[i], ratio[i], df_merged["SXS_num"].to_numpy()[i], fontsize = 8)
    if colorbar:
        cb = fig.colorbar(sc, ax = ax)
        if color_string == "eta":
            cb.ax.set_ylabel(r"$\eta$")
        elif color_string == "chi_p":
            cb.ax.set_ylabel(r"$\chi_+$")
        elif color_string == "chi_m":
            cb.ax.set_ylabel(r"$\chi_-$")
        else:
            cb.ax.set_ylabel(r"$\chi_{\rm rem}$")

    x_lim = ax.get_xlim()

    if fit:
        fitfunc = lin_func_scipy
        out = curve_fit(fitfunc, chis, ratio, sigma = ratio_err, absolute_sigma = True)
        xsfit = np.linspace(*x_lim, num = 100)
        ysfit = fitfunc(xsfit, *out[0])
        ax.plot(xsfit, ysfit, c = "gray", ls = ":")

        ax.set_xlim(*x_lim)

        preds = fitfunc(chis, *out[0])
        outlier_indxs = np.where(np.abs(ratio - preds)/preds > outlier_tol)[0]
        outlier_SXS_nums = df_merged["SXS_num"].to_numpy()[outlier_indxs]

        return out, outlier_SXS_nums
    return

def visualize_outliers_n_modes(df, l, m, outlier_SXS_nums, ax = None):
    df_lm = df.loc[(df["l"] == l) & (df["m"] == m)]
    counts = df_lm['SXS_num'].value_counts()
    counts_outliers = counts.loc[outlier_SXS_nums]
    if ax is None:
        fig, ax = plt.subplots()
    ax.hist(counts, bins = 20)
    ax.hist(counts_outliers, bins = 20)

def visualize_outliers_individual_modes(df, l, m, outlier_SXS_nums, ax = None):
    df_lm = df.loc[(df["l"] == l) & (df["m"] == m)]
    if ax is None:
        fig, ax = plt.subplots()
    for _, row in df_lm.iterrows():
        if row["SXS_num"] in outlier_SXS_nums:
            c = 'r'
            s = 10
            alpha = 1 
        else:
            c = 'C0'
            s = 5
            alpha = 0.3
        ax.scatter(row["SXS_num"], row["mode_string"], c = c, s = s, alpha = alpha)

def plot_mode_searcher_results(mode_searcher, axs = None):
    if axs is None:
        fig, axs = plt.subplots(1, 3, figsize = (18, 5))
    
    present_mode_strings = qnms_to_string(mode_searcher.found_modes_final)
    mode_searcher_vary_N = mode_searcher.mode_searcher_vary_N
    best_run_indx = mode_searcher_vary_N.best_run_indx
    best_N = mode_searcher_vary_N.N_list[best_run_indx]
    best_mode_searcher = mode_searcher_vary_N.mode_searchers[best_run_indx]
    potential_modes_list = best_mode_searcher.potential_modes_full
    best_N_free_result = mode_searcher_vary_N.mode_searchers[best_run_indx].full_fit.result_full

    best_flatness_checker = mode_searcher_vary_N.flatness_checkers[best_run_indx]
    best_fitter_list = best_flatness_checker.fitter_list
    best_fluc_least_indx_list = best_flatness_checker.fluc_least_indx_list
    best_start_flat_indx_list = best_flatness_checker.start_flat_indx_list

    plot_omega_free(best_N_free_result, ax = axs[0])
    plot_predicted_qnms(axs[0], potential_modes_list,
                        present_modes = present_mode_strings)

    axs[0].text(0.95, 0.03, f'$N_f = {best_N}$',
            transform = axs[0].transAxes, fontsize = 18, ha = 'right', va = 'bottom')

    result = best_fitter_list[-1].result_full

    bold_dict = {}
    t_start_dict = {}
    for start_flat_indx, fluc_least_indx, found_mode_string in zip(best_start_flat_indx_list, best_fluc_least_indx_list, present_mode_strings):
        bold_dict[found_mode_string] = (fluc_least_indx, fluc_least_indx + 100)
        t_start_dict[found_mode_string] = result.t0_arr[start_flat_indx]

    for key in t_start_dict:
        t_start_dict[key] += 0.5      

    for qnm in result.qnm_fixed_list:
        if not hasattr(qnm, 'lmnx_retro'):
            qnm.init_lmnx_retro()
            
    plot_amplitudes(result, fixed_modes = result.qnm_fixed_list, ax = axs[1], use_label = False, 
                    legend = True, bold_dict = bold_dict, alpha = 0.3,
                    t_flat_start_dict = t_start_dict, flat_start_s = 30)
    plot_phases(result, fixed_modes = result.qnm_fixed_list, ax = axs[2], legend = False, bold_dict = bold_dict, 
                alpha = 0.3, t_flat_start_dict = t_start_dict, flat_start_s = 30)

    axs[1].legend(fontsize = 9)  



        
    