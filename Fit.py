import numpy as np
import jax.numpy as jnp
from jaxfit import CurveFit
import scipy
from scipy.optimize import curve_fit
from utils import *
from QuasinormalMode import *
from tqdm import tqdm
import os
import pickle
from copy import copy
import random

from jax.config import config
config.update("jax_enable_x64", True)

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
SCRATCH_PATH = "/expanse/lustre/scratch/mcheung1/temp_project/Ringdown/jaxqualin/"
FIT_SAVE_PATH = os.path.join(SCRATCH_PATH, "pickle/fits")


def qnm_fit_func_mirror_fixed(
        t,
        qnm_fixed_list,
        fix_mode_params_list,
        mirror_ratio_list,
        part=None):
    Q = 0
    for qnm_fixed, fix_mode_params, mirror_ratio in zip(
            qnm_fixed_list, fix_mode_params_list, mirror_ratio_list):
        A, phi = tuple(fix_mode_params)
        omegar = qnm_fixed.omegar
        omegai = qnm_fixed.omegai
        if part is None:
            Q += A * jnp.exp(-1.j * ((omegar + 1.j * omegai) * t + phi))
            Q += mirror_ratio * A * jnp.exp(-1.j * ((-omegar + 1.j * omegai) * t - phi))
        elif part == "real":
            Q += A * jnp.exp(omegai * t) * jnp.cos(omegar * t + phi)
            Q += mirror_ratio * A * jnp.exp(omegai * t) * jnp.cos(-omegar * t - phi)
        elif part == "imag":
            Q += -A * jnp.exp(omegai * t) * jnp.sin(omegar * t + phi)
            Q += - mirror_ratio * A * jnp.exp(omegai * t) * jnp.sin(-omegar * t - phi)
    return Q


def qnm_fit_func(
        t,
        qnm_fixed_list,
        fix_mode_params_list,
        free_mode_params_list,
        part=None):
    Q = 0
    for qnm_fixed, fix_mode_params in zip(
            qnm_fixed_list, fix_mode_params_list):
        A, phi = tuple(fix_mode_params)
        omegar = qnm_fixed.omegar
        omegai = qnm_fixed.omegai
        if part is None:
            Q += A * jnp.exp(-1.j * ((omegar + 1.j * omegai) * t + phi))
        elif part == "real":
            Q += A * jnp.exp(omegai * t) * jnp.cos(omegar * t + phi)
        elif part == "imag":
            Q += -A * jnp.exp(omegai * t) * jnp.sin(omegar * t + phi)
    for free_mode_params in free_mode_params_list:
        A, phi, omegar, omegai = tuple(free_mode_params)
        if part is None:
            Q += A * jnp.exp(-1.j * ((omegar + 1.j * omegai) * t + phi))
        elif part == "real":
            Q += A * jnp.exp(omegai * t) * jnp.cos(omegar * t + phi)
        elif part == "imag":
            Q += -A * jnp.exp(omegai * t) * jnp.sin(omegar * t + phi)
    return Q


def qnm_fit_func_varMa(
        t,
        qnm_fixed_list,
        qnm_free_list,
        fix_mode_params_list,
        free_mode_params_list,
        M,
        a,
        retro=False,
        part=None):
    Q = 0
    for qnm_fixed, fix_mode_params in zip(
            qnm_fixed_list, fix_mode_params_list):
        A, phi = tuple(fix_mode_params)
        omegar = qnm_fixed.omegar
        omegai = qnm_fixed.omegai
        if part is None:
            Q += A * np.exp(-1.j * ((omegar + 1.j * omegai) * t + phi))
        elif part == "real":
            Q += A * np.exp(omegai * t) * np.cos(omegar * t + phi)
        elif part == "imag":
            Q += -A * np.exp(omegai * t) * np.sin(omegar * t + phi)
    for free_mode_params, qnm_free in zip(free_mode_params_list, qnm_free_list):
        A, phi = tuple(free_mode_params)
        qnm_free.fix_mode(M, a, retro=retro)
        omegar = qnm_free.omegar
        omegai = qnm_free.omegai
        if part is None:
            Q += A * np.exp(-1.j * ((omegar + 1.j * omegai) * t + phi))
        elif part == "real":
            Q += A * np.exp(omegai * t) * np.cos(omegar * t + phi)
        elif part == "imag":
            Q += -A * np.exp(omegai * t) * np.sin(omegar * t + phi)
    return Q


def qnm_fit_func_varMa_mirror(
        t,
        qnm_fixed_list,
        qnm_free_list,
        fix_mode_params_list,
        free_mode_params_list,
        iota,
        psi,
        M,
        a,
        retro=False,
        part=None):
    Q = 0
    N_fix = len(qnm_fixed_list)
    for qnm_fixed, fix_mode_params in zip(
            qnm_fixed_list, fix_mode_params_list):
        A, phi = tuple(fix_mode_params)
        omegar = qnm_fixed.omegar
        omegai = qnm_fixed.omegai
        lmnx = qnm_fixed.lmnx
        mirror_ratio = 1
        for lmn in lmnx:
            l, m, n = tuple(lmn)
            S_fac = S_retro_fac(iota, a, l, m, n, phi = psi)
            mirror_ratio *= S_fac
        if part is None:
            Q += A * np.exp(-1.j * ((omegar + 1.j * omegai) * t + phi))
            Q += mirror_ratio * A * np.exp(-1.j * ((-omegar + 1.j * omegai) * t - phi))
        elif part == "real":
            Q += A * np.exp(omegai * t) * np.cos(omegar * t + phi)
            Q += mirror_ratio * A * np.exp(omegai * t) * np.cos(-omegar * t - phi)
        elif part == "imag":
            Q += -A * np.exp(omegai * t) * np.sin(omegar * t + phi)
            Q += - mirror_ratio * A * np.exp(omegai * t) * np.sin(-omegar * t - phi)
    for free_mode_params, qnm_free in zip(
            free_mode_params_list, qnm_free_list):
        A, phi = tuple(free_mode_params)
        qnm_free.fix_mode(M, a, retro=retro)
        omegar = qnm_free.omegar
        omegai = qnm_free.omegai
        lmnx = qnm_free.lmnx
        mirror_ratio = 1
        for lmn in lmnx:
            l, m, n = tuple(lmn)
            S_fac = S_retro_fac(iota, a, l, m, n, phi = psi)
            mirror_ratio *= S_fac
        if part is None:
            Q += A * np.exp(-1.j * ((omegar + 1.j * omegai) * t + phi))
            Q += mirror_ratio * A * np.exp(-1.j * ((-omegar + 1.j * omegai) * t - phi))
        elif part == "real":
            Q += A * np.exp(omegai * t) * np.cos(omegar * t + phi)
            Q += mirror_ratio * A * np.exp(omegai * t) * np.cos(-omegar * t - phi)
        elif part == "imag":
            Q += -A * np.exp(omegai * t) * np.sin(omegar * t + phi)
            Q += - mirror_ratio * A * np.exp(omegai * t) * np.sin(-omegar * t - phi)
    return Q

# https://stackoverflow.com/questions/34136737/using-scipy-curve-fit-for-a-variable-number-of-parameters


def qnm_fit_func_wrapper(t, qnm_fixed_list, N_free, *args, part=None):
    N_fix = len(qnm_fixed_list)
    fix_mode_params_list = []
    for i in range(N_fix):
        A = args[0][2 * i]
        phi = args[0][2 * i + 1]
        fix_mode_params_list.append([A, phi])
    free_mode_params_list = []
    for j in range(N_free):
        try:
            A = args[0][2 * N_fix + 4 * j]
            phi = args[0][2 * N_fix + 4 * j + 1]
            omegar = args[0][2 * N_fix + 4 * j + 2]
            omegai = args[0][2 * N_fix + 4 * j + 3]
            free_mode_params_list.append([A, phi, omegar, omegai])
        except:
            print(args)
            print(2 * N_fix + 4 * j)
            raise ValueError
    return qnm_fit_func(t, qnm_fixed_list, fix_mode_params_list,
                        free_mode_params_list, part=part)


def qnm_fit_func_mirror_wrapper(t, qnm_fixed_list, mirror_ratio_list, *args, part=None):
    N_fix = len(qnm_fixed_list)
    fix_mode_params_list = []
    for i in range(N_fix):
        A = args[0][2 * i]
        phi = args[0][2 * i + 1]
        fix_mode_params_list.append([A, phi])
    return qnm_fit_func_mirror_fixed(t, qnm_fixed_list, fix_mode_params_list,
                        mirror_ratio_list, part=part)


def qnm_fit_func_wrapper_varMa(t, qnm_fixed_list, qnm_free_list, retro, *args, Schwarzschild=False, part=None):
    N_fix = len(qnm_fixed_list)
    N_free = len(qnm_free_list)
    fix_mode_params_list = []
    for i in range(N_fix):
        A = args[0][2 * i]
        phi = args[0][2 * i + 1]
        fix_mode_params_list.append([A, phi])
    free_mode_params_list = []
    for j in range(N_free):
        A = args[0][2 * N_fix + 2 * j]
        phi = args[0][2 * N_fix + 2 * j + 1]
        free_mode_params_list.append([A, phi])
    M = args[0][2 * (N_fix + N_free)]
    if Schwarzschild:
        return qnm_fit_func_varMa(t, qnm_fixed_list, qnm_free_list, fix_mode_params_list,
                                  free_mode_params_list, M, 0., retro=retro, part=part)
    else:
        a = args[0][2 * (N_fix + N_free) + 1]
        return qnm_fit_func_varMa(t, qnm_fixed_list, qnm_free_list, fix_mode_params_list,
                                  free_mode_params_list, M, a, retro=retro, part=part)


def qnm_fit_func_wrapper_varMa_mirror(
        t, qnm_fixed_list, qnm_free_list, iota, psi, retro, *args, Schwarzschild=False, part=None):
    N_fix = len(qnm_fixed_list)
    N_free = len(qnm_free_list)
    fix_mode_params_list = []
    for i in range(N_fix):
        A = args[0][2 * i]
        phi = args[0][2 * i + 1]
        fix_mode_params_list.append([A, phi])
    free_mode_params_list = []
    for j in range(N_free):
        A = args[0][2 * N_fix + 2 * j]
        phi = args[0][2 * N_fix + 2 * j + 1]
        free_mode_params_list.append([A, phi])
    M = args[0][2 * (N_fix + N_free)]
    if Schwarzschild:
        return qnm_fit_func_varMa_mirror(t, qnm_fixed_list, qnm_free_list, fix_mode_params_list,
                                  free_mode_params_list, iota, psi, M, 0., retro=retro, part=part)
    else:
        a = args[0][2 * (N_fix + N_free) + 1]
        return qnm_fit_func_varMa_mirror(t, qnm_fixed_list, qnm_free_list, fix_mode_params_list,
                                  free_mode_params_list, iota, psi, M, a, retro=retro, part=part)


# https://stackoverflow.com/questions/50203879/curve-fitting-of-complex-data


def qnm_fit_func_wrapper_complex(t, qnm_fixed_list, N_free, *args, Schwarzschild=False):
    N = len(t)
    t_real = t[0::2]
    t_imag = t[1::2]
    h_real = qnm_fit_func_wrapper(
        t_real, qnm_fixed_list, N_free, *args, part="real")
    if Schwarzschild:
        h_imag = jnp.zeros(int(N/2))
    else:
        h_imag = qnm_fit_func_wrapper(
            t_imag, qnm_fixed_list, N_free, *args, part="imag")
    h_riffle = interweave(h_real, h_imag)
    return h_riffle


def qnm_fit_func_wrapper_complex_mirror(t, qnm_fixed_list, mirror_ratio_list, N_free, *args, Schwarzschild=False):
    N = len(t)
    t_real = t[0::2]
    t_imag = t[1::2]
    h_real = qnm_fit_func_mirror_wrapper(
        t_real, qnm_fixed_list, mirror_ratio_list, *args, part="real")
    if Schwarzschild:
        h_imag = jnp.zeros(int(N/2))
    else:
        h_imag = qnm_fit_func_mirror_wrapper(
            t_imag, qnm_fixed_list, mirror_ratio_list, *args, part="imag")
    h_riffle = interweave(h_real, h_imag)
    return h_riffle


def qnm_fit_func_wrapper_complex_varMa(t, qnm_fixed_list, qnm_free_list, retro, *args):
    N = len(t)
    t_real = t[0::2]
    t_imag = t[1::2]
    h_real = qnm_fit_func_wrapper_varMa(
        t_real, qnm_fixed_list, qnm_free_list, retro, *args, part="real")
    h_imag = qnm_fit_func_wrapper_varMa(
        t_imag, qnm_fixed_list, qnm_free_list, retro, *args, part="imag")
    h_riffle = interweave(h_real, h_imag)
    return h_riffle


def qnm_fit_func_wrapper_complex_varMa_mirror(t, qnm_fixed_list, qnm_free_list, iota, psi, retro, *args):
    N = len(t)
    t_real = t[0::2]
    t_imag = t[1::2]
    h_real = qnm_fit_func_wrapper_varMa_mirror(
        t_real, qnm_fixed_list, qnm_free_list, iota, psi, retro, *args, part="real")
    h_imag = qnm_fit_func_wrapper_varMa_mirror(
        t_imag, qnm_fixed_list, qnm_free_list, iota, psi, retro, *args, part="imag")
    h_riffle = interweave(h_real, h_imag)
    return h_riffle
 

class QNMFitResult:

    def __init__(self, popt, pcov, mismatch,
                 cost = np.nan, grad = np.nan, nfev = np.nan,
                 status = np.nan):
        self.popt = popt
        self.pcov = pcov
        self.mismatch = mismatch
        self.cost = cost
        self.grad = grad
        self.nfev = nfev
        self.status = status


class QNMFit:

    def __init__(
            self,
            h,
            t0,
            N_free,
            qnm_fixed_list=[],
            Schwarzschild=False,
            params0=None,
            max_nfev=200000,
            A_bound=np.inf,
            weighted = False,
            include_mirror = False,
            mirror_ratio_list = None,
            **fit_kwargs):
        self.h = h
        self.t0 = t0
        self.N_free = N_free
        self.qnm_fixed_list = qnm_fixed_list
        self.params0 = params0
        self.N_fix = len(qnm_fixed_list)
        self.Schwarzschild = Schwarzschild
        self.max_nfev = max_nfev
        self.fit_done = False
        self.A_bound = A_bound
        self.fit_kwargs = fit_kwargs
        self.weighted = weighted
        self.include_mirror = include_mirror
        if self.include_mirror and self.N_free != 0:
            raise ValueError("Mirror is only allowed for fixed modes.")
        if self.include_mirror and mirror_ratio_list is None:
            raise ValueError("Mirror ratio list is not provided.")
        self.mirror_ratio_list = mirror_ratio_list

    def make_weights(self, hr, hi):
        habs = np.abs(hr + 1.j*hi)
        weight = interweave(habs, habs)
        return np.array(weight)

    def do_fit(self, jcf=CurveFit(), return_jcf=False):
        self.time, self.hr, self.hi = self.h.postmerger(self.t0)
        if self.weighted:
            weight = self.make_weights(self.hr, self.hi)
            sigma = weight
        else:
            sigma = None
        self._h_interweave = interweave(self.hr, self.hi)
        self._time_interweave = interweave(self.time, self.time)
        if not hasattr(self.params0, "__iter__"):
            self.params0 = jnp.array(
                [1, 1] * self.N_fix + [1, 1, 1, -1] * self.N_free)
        upper_bound = [self.A_bound, np.inf] * self.N_fix + \
            ([self.A_bound] + 3 * [np.inf]) * self.N_free
        lower_bound = [-self.A_bound, -np.inf] * self.N_fix + \
            ([-self.A_bound] + 3 * [-np.inf]) * self.N_free
        # upper_bound = [self.A_bound, np.inf] * self.N_fix + \
        #     [self.A_bound, np.pi, np.inf, np.inf] * self.N_free
        # lower_bound = [-self.A_bound, -np.inf] * self.N_fix + \
        #     [-self.A_bound, 0, -np.inf, -np.inf] * self.N_free
        bounds = (np.array(lower_bound), np.array(upper_bound))
        if self.include_mirror:
            self.popt, self.pcov, self.res, _, _ = jcf.curve_fit(
                lambda t, *params: qnm_fit_func_wrapper_complex_mirror(
                    t, self.qnm_fixed_list, self.mirror_ratio_list, self.N_free, params, Schwarzschild=self.Schwarzschild), np.array(
                    self._time_interweave), np.array(
                    self._h_interweave), bounds=bounds, p0=self.params0, max_nfev=self.max_nfev,
                method="trf", sigma = sigma, **self.fit_kwargs, timeit = True)
        else:
            self.popt, self.pcov, self.res, _, _ = jcf.curve_fit(
                # self.popt, self.pcov = scipy.optimize.curve_fit(
                lambda t, *params: qnm_fit_func_wrapper_complex(
                    t, self.qnm_fixed_list, self.N_free, params, Schwarzschild=self.Schwarzschild), np.array(
                    self._time_interweave), np.array(
                    self._h_interweave), bounds=bounds, p0=self.params0, max_nfev=self.max_nfev,
                method="trf", sigma = sigma, **self.fit_kwargs, timeit = True)
        try:
            self.cost = self.res.cost
            self.grad = self.res.grad
            self.nfev = self.res.nfev
            self.status = self.res.status
        except:
            self.cost = np.nan
            self.grad = np.nan
            self.nfev = np.nan
            self.status = np.nan
        if self.Schwarzschild:
            self.reconstruct_h = qnm_fit_func_wrapper(
                self.time, self.qnm_fixed_list, self.N_free, self.popt, part="real")
        elif self.include_mirror:
            self.reconstruct_h = qnm_fit_func_mirror_wrapper(
                self.time, self.qnm_fixed_list, self.mirror_ratio_list, self.popt)    
        else:
            self.reconstruct_h = qnm_fit_func_wrapper(
                self.time, self.qnm_fixed_list, self.N_free, self.popt)
        self.h_true = self.hr + 1.j * self.hi
        self.mismatch = 1 - (np.abs(np.vdot(self.h_true, self.reconstruct_h) / (
            np.linalg.norm(self.h_true) * np.linalg.norm(self.reconstruct_h))))
        self.result = QNMFitResult(self.popt, self.pcov, self.mismatch,
                                   self.cost, self.grad, self.nfev, self.status)
        self.fit_done = True
        if return_jcf:
            return jcf

    def copy_from_result(self, other_result):
        if self.fit_done == False:
            self.popt = other_result.popt
            self.pcov = other_result.pcov
            try:
                self.cost = other_result.cost
                self.grad = other_result.grad
                self.nfev = other_result.nfev
                self.status = other_result.status
            except:
                pass
            self.time, self.hr, self.hi = self.h.postmerger(self.t0)
            self._h_interweave = interweave(self.hr, self.hi)
            self._time_interweave = interweave(self.time, self.time)
            self.reconstruct_h = qnm_fit_func_wrapper(
                self.time, self.qnm_fixed_list, self.N_free, self.popt)
            self.h_true = self.hr + 1.j * self.hi
            self.mismatch = 1 - (np.real(np.vdot(self.h_true, self.reconstruct_h) / (
                np.linalg.norm(self.h_true) * np.linalg.norm(self.reconstruct_h))))
            self.result = QNMFitResult(self.popt, self.pcov, self.mismatch)


class QNMFitVarMa:

    def __init__(
            self,
            h,
            t0,
            qnm_free_list,
            qnm_fixed_list=[],
            retro=False,
            Schwarzschild=False,
            jcf=CurveFit(),
            params0=None,
            max_nfev=200000,
            include_mirror = False,
            iota = None,
            psi = None,
            **fit_kwargs):
        self.h = h
        self.t0 = t0
        self.N_free = len(qnm_free_list)
        self.qnm_free_list = qnm_free_list
        self.qnm_fixed_list = qnm_fixed_list
        self.params0 = params0
        self.N_fix = len(qnm_fixed_list)
        # self.jcf = jcf
        self.max_nfev = max_nfev
        self.fit_done = False
        self.retro = retro
        self.Schwarzschild = Schwarzschild
        self.fit_kwargs = fit_kwargs
        self.include_mirror = include_mirror
        if self.include_mirror:
            self.iota = iota
            self.psi = psi

    def do_fit(self, jcf=CurveFit(), return_jcf=False):
        self.time, self.hr, self.hi = self.h.postmerger(self.t0)
        self._h_interweave = interweave(self.hr, self.hi)
        self._time_interweave = interweave(self.time, self.time)
        if self.Schwarzschild:
            if not hasattr(self.params0, "__iter__"):
                self.params0 = np.array(
                    [1, 1] * self.N_fix + [1, 1] * self.N_free + [1])
            if self.include_mirror:
                fit_func = lambda t, *params: qnm_fit_func_wrapper_varMa_mirror(
                    t, self.qnm_fixed_list, self.qnm_free_list, self.iota, self.psi,
                    self.retro, params, 0, Schwarzschild=True, part="real")
                self.popt, self.pcov = curve_fit(fit_func, np.array(
                    self.time), np.array(
                    self.hr), p0=self.params0, max_nfev=self.max_nfev,
                    method="trf")
                self.reconstruct_h = qnm_fit_func_wrapper_varMa_mirror(
                    self.time, self.qnm_fixed_list, self.qnm_free_list, self.iota, self.psi,
                      self.retro, self.popt,
                    0, Schwarzschild=True, part="real")
            else:
                fit_func = lambda t, *params: qnm_fit_func_wrapper_varMa(
                    t, self.qnm_fixed_list, self.qnm_free_list, self.retro, params, 0, Schwarzschild=True, part="real")
                self.popt, self.pcov = curve_fit(fit_func, np.array(
                    self.time), np.array(
                    self.hr), p0=self.params0, max_nfev=self.max_nfev,
                    method="trf")
                self.reconstruct_h = qnm_fit_func_wrapper_varMa(
                    self.time, self.qnm_fixed_list, self.qnm_free_list, self.retro, self.popt,
                    0, Schwarzschild=True, part="real")
        else:
            if not hasattr(self.params0, "__iter__"):
                self.params0 = np.array(
                    [1, 1] * self.N_fix + [1, 1] * self.N_free + [1, 0.5])
            lower_bound = [-np.inf] * \
                (2 * self.N_fix + 2 * self.N_free + 1) + [-0.99]
            upper_bound = [np.inf] * \
                (2 * self.N_fix + 2 * self.N_free + 1) + [0.99]
            bounds = (np.array(lower_bound), np.array(upper_bound))
            if self.include_mirror:
                fit_func = lambda t, *params: qnm_fit_func_wrapper_complex_varMa_mirror(
                    t, self.qnm_fixed_list, self.qnm_free_list,self.iota, self.psi,
                      self.retro, params)
            else:
                fit_func = lambda t, *params: qnm_fit_func_wrapper_complex_varMa(
                    t, self.qnm_fixed_list, self.qnm_free_list, self.retro, params)
            self.popt, self.pcov = curve_fit(fit_func, np.array(
                self._time_interweave), np.array(
                    self._h_interweave), p0=self.params0,
                bounds=bounds, max_nfev=self.max_nfev,
                method="trf", **self.fit_kwargs)
            if self.include_mirror:
                self.reconstruct_h = qnm_fit_func_wrapper_varMa_mirror(
                    self.time, self.qnm_fixed_list, self.qnm_free_list, 
                    self.iota, self.psi,
                    self.retro, self.popt)
            else:
                self.reconstruct_h = qnm_fit_func_wrapper_varMa(
                    self.time, self.qnm_fixed_list, self.qnm_free_list, 
                    self.retro, self.popt)
        self.h_true = self.hr + 1.j * self.hi
        self.mismatch = 1 - (np.abs(np.vdot(self.h_true, self.reconstruct_h) / (
            np.linalg.norm(self.h_true) * np.linalg.norm(self.reconstruct_h))))
        self.result = QNMFitResult(self.popt, self.pcov, self.mismatch)
        self.fit_done = True

    def copy_from_result(self, other_result):
        if self.fit_done == False:
            self.popt = other_result.popt
            self.pcov = other_result.pcov
            self.time, self.hr, self.hi = self.h.postmerger(self.t0)
            self._h_interweave = interweave(self.hr, self.hi)
            self._time_interweave = interweave(self.time, self.time)
            self.reconstruct_h = qnm_fit_func_wrapper(
                self.time, self.qnm_fixed_list, self.N_free, self.popt)
            self.h_true = self.hr + 1.j * self.hi
            self.mismatch = 1 - (np.abs(np.vdot(self.h_true, self.reconstruct_h) / (
                np.linalg.norm(self.h_true) * np.linalg.norm(self.reconstruct_h))))
            self.result = QNMFitResult(self.popt, self.pcov, self.mismatch)

def make_initial_guess(N_free, guess_num, A_log_low = -1, A_log_hi = 1, phi_low = 0, phi_hi = 2*np.pi,
                       omega_r_low = -2, omega_r_hi = 2, omega_i_low = 0, omega_i_hi = -1, seed = 1234,
                       A_val = 1, A_guess_relative = True):
    if not A_guess_relative:
        A_val = 1
    rng = np.random.RandomState(seed)
    A_guesses = A_val*10**(rng.uniform(A_log_low, A_log_hi, size = (guess_num, N_free)))
    phi_guesses = rng.uniform(phi_low, phi_hi, size = (guess_num, N_free))
    omegar_guesses = rng.uniform(omega_r_low, omega_r_hi, size = (guess_num, N_free))
    omegai_guesses = rng.uniform(omega_i_low, omega_i_hi, size = (guess_num, N_free))

    guesses_stack = np.empty((guess_num, 4 * N_free), dtype = A_guesses.dtype)
    guesses_stack[:,0::4] = A_guesses 
    guesses_stack[:,1::4] = phi_guesses 
    guesses_stack[:,2::4] = omegar_guesses
    guesses_stack[:,3::4] = omegai_guesses

    guess_list = [jnp.array(guess) for guess in guesses_stack]

    return guess_list


class QNMFitVaryingStartingTimeResult:

    def __init__(
            self,
            t0_arr,
            qnm_fixed_list,
            N_free,
            run_string_prefix="Default",
            nonconvergence_cut=False,
            nonconvergence_indx=[],
            initial_num = 1,
            include_mirror = False,
            mirror_ratio_list = None,
            iota = None,
            psi = None
            ):
        self.t0_arr = t0_arr
        self.qnm_fixed_list = qnm_fixed_list
        self.N_fix = len(self.qnm_fixed_list)
        self.N_free = N_free
        self._popt_full = np.zeros(
            (2 * self.N_fix + 4 * self.N_free, len(self.t0_arr)), dtype=float)
        self.popt_initial = np.zeros(
            (2 * self.N_fix + 4 * self.N_free, initial_num), dtype=float)
        self._mismatch_arr = np.zeros(len(self.t0_arr), dtype=float)
        self.mismatch_initial_arr = np.zeros(initial_num, dtype=float)
        self.cost_arr = np.zeros(len(self.t0_arr), dtype=float)
        self.grad_arr = np.zeros(len(self.t0_arr), dtype=float)
        self.nfev_arr = np.zeros(len(self.t0_arr), dtype=int)
        self.status_arr = np.zeros(len(self.t0_arr), dtype=int)
        self.result_processed = False
        if self.N_fix > 0:
            _qnm_fixed_string_list = sorted(qnms_to_string(qnm_fixed_list))
            self.qnm_fixed_string_ordered = '_'.join(_qnm_fixed_string_list)
            self.run_string = f"{run_string_prefix}_N_{self.N_free}_fix_{self.qnm_fixed_string_ordered}_t0_{t0_arr[0]:.4f}_{t0_arr[-1]:.4f}_{len(t0_arr)}"
        else:
            self.qnm_fixed_string_ordered = ''
            self.run_string = f"{run_string_prefix}_N_{self.N_free}_t0_{t0_arr[0]:.4f}_{t0_arr[-1]:.4f}_{len(t0_arr)}"
        if nonconvergence_cut:
            self.run_string += "_nc"
        self.nonconvergence_indx = nonconvergence_indx
        self.file_path = os.path.join(
            FIT_SAVE_PATH, f"{self.run_string}_result.pickle")
        self.initila_guess_results = []
        self.include_mirror = include_mirror
        if self.include_mirror:
            self.mirror_ratio_list = mirror_ratio_list
            self.iota = iota
            self.psi = psi

    def fill_result(self, i, result):
        self._popt_full[:, i] = result.popt
        self._mismatch_arr[i] = result.mismatch
        self.cost_arr[i] = result.cost
        # self.grad_arr[i] = result.grad
        self.nfev_arr[i] = result.nfev
        self.status_arr[i] = result.status

    def fill_initial_guess(self, i, result):
        self.popt_initial[:, i] = result.popt
        self.mismatch_initial_arr[i] = result.mismatch

    def process_results(self):
        self.popt_full = self._popt_full
        self.mismatch_arr = self._mismatch_arr
        self.A_fix_dict = {}
        self.phi_fix_dict = {}
        self.A_free_dict = {}
        self.phi_free_dict = {}
        self.omega_r_dict = {}
        self.omega_i_dict = {}
        for i in range(0, 2 * self.N_fix, 2):
            self.A_fix_dict[f"A_{self.qnm_fixed_list[i//2].string()}"] = self.popt_full[i]
            self.phi_fix_dict[f"phi_{self.qnm_fixed_list[i//2].string()}"] = self.popt_full[i + 1]
        for i in range(2 * self.N_fix, 2 * self.N_fix + 4 * self.N_free, 4):
            self.A_free_dict[f"A_free_{(i-2*self.N_fix)//4}"] = self.popt_full[i]
            self.phi_free_dict[f"phi_free_{(i-2*self.N_fix)//4}"] = self.popt_full[i + 1]
            self.omega_r_dict[f"omega_r_free_{(i-2*self.N_fix)//4}"] = self.popt_full[i + 2]
            self.omega_i_dict[f"omega_i_free_{(i-2*self.N_fix)//4}"] = self.popt_full[i + 3]
        self.A_dict = {**self.A_fix_dict, **self.A_free_dict}
        self.phi_dict = {**self.phi_fix_dict, **self.phi_free_dict}
        self.results_dict = {
            **self.A_fix_dict,
            **self.A_free_dict,
            **self.phi_fix_dict,
            **self.phi_free_dict,
            **self.omega_r_dict,
            **self.omega_i_dict}
        self.omega_dict = {"real": self.omega_r_dict,
                           "imag": self.omega_i_dict}
        self.result_processed = True
        self.pickle_save()

    def pickle_save(self):
        with open(self.file_path, "wb") as f:
            pickle.dump(self, f)

    def pickle_exists(self):
        return os.path.exists(self.file_path)

    def reconstruct_waveform(self, indx, t_arr):
        popt = self.popt_full[:, indx]
        if self.include_mirror:
            Q = qnm_fit_func_mirror_wrapper(
                t_arr, self.qnm_fixed_list, self.mirror_ratio_list, popt, part=None)
        else:
            Q = qnm_fit_func_wrapper(
                t_arr, self.qnm_fixed_list, self.N_free, popt, part=None)
        return Q

    def reconstruct_mode_by_mode(self, indx, t_arr):
        Q_fix_list = []
        Q_free_list = []
        popt = self.popt_full[:, indx]
        for j in range(self.N_fix):
            Q = qnm_fit_func_wrapper(
                t_arr, [self.qnm_fixed_list[j]], 0, popt[2*j:2*j+2], part=None)
            Q_fix_list.append(Q)
        for j in range(self.N_free):
            Q = qnm_fit_func_wrapper(
                t_arr, [], 1, popt[2 * self.N_fix + 4*j:2 * self.N_fix + 4*j + 4], part=None)
            Q_free_list.append(Q)
        return Q_fix_list, Q_free_list


class QNMFitVaryingStartingTimeResultVarMa:

    def __init__(
            self,
            t0_arr,
            qnm_fixed_list,
            qnm_free_list,
            Schwarzschild=False,
            run_string_prefix="Default",
            nonconvergence_cut=False,
            include_mirror = False,
            nonconvergence_indx=[],
            iota = None,
            psi = None):
        self.t0_arr = t0_arr
        self.qnm_fixed_list = qnm_fixed_list
        self.qnm_free_list = qnm_free_list
        self.N_fix = len(self.qnm_fixed_list)
        self.N_free = len(qnm_free_list)
        self.Schwarzschild = Schwarzschild
        if Schwarzschild:
            M_a_len = 1
        else:
            M_a_len = 2
        self._popt_full = np.zeros(
            (2 * self.N_fix + 2 * self.N_free + M_a_len, len(self.t0_arr)), dtype=float)
        self._mismatch_arr = np.zeros(len(self.t0_arr), dtype=float)
        self.result_processed = False
        _qnm_free_string_list = sorted(qnms_to_string(qnm_fixed_list))
        self.qnm_free_string_ordered = '_'.join(_qnm_free_string_list)
        if self.N_fix > 0:
            _qnm_fixed_string_list = sorted(qnms_to_string(qnm_fixed_list))
            self.qnm_fixed_string_ordered = '_'.join(_qnm_fixed_string_list)
            self.run_string = f"{run_string_prefix}_varMa_free_{self.qnm_free_string_ordered}_fix_{self.qnm_fixed_string_ordered}_t0_{t0_arr[0]:.4f}_{t0_arr[-1]:.4f}_{len(t0_arr)}"
        else:
            self.qnm_fixed_string_ordered = ''
            self.run_string = f"{run_string_prefix}_varMa_free_{self.qnm_free_string_ordered}_t0_{t0_arr[0]:.4f}_{t0_arr[-1]:.4f}_{len(t0_arr)}"
        if nonconvergence_cut:
            self.run_string += "_nc"
        self.nonconvergence_indx = nonconvergence_indx
        self.file_path = os.path.join(
            FIT_SAVE_PATH, f"{self.run_string}_result.pickle")
        self.include_mirror = include_mirror
        if self.include_mirror:
            self.iota = iota
            self.psi = psi

    def fill_result(self, i, result):
        self._popt_full[:, i] = result.popt
        self._mismatch_arr[i] = result.mismatch

    def process_results(self):
        self.popt_full = self._popt_full
        self.mismatch_arr = self._mismatch_arr
        self.A_fix_dict = {}
        self.phi_fix_dict = {}
        self.A_free_dict = {}
        self.phi_free_dict = {}
        self.omega_r_dict = {}
        self.omega_i_dict = {}
        for i in range(0, 2 * self.N_fix, 2):
            self.A_fix_dict[f"A_{self.qnm_fixed_list[i//2].string()}"] = self.popt_full[i]
            self.phi_fix_dict[f"phi_{self.qnm_fixed_list[i//2].string()}"] = self.popt_full[i + 1]
        for i in range(2 * self.N_fix, 2 * self.N_fix + 2 * self.N_free, 2):
            self.A_free_dict[f"A_free_{(i-2*self.N_fix)//2}"] = self.popt_full[i]
            self.phi_free_dict[f"phi_free_{(i-2*self.N_fix)//2}"] = self.popt_full[i + 1]
        j = 2 * self.N_fix + 2 * self.N_free
        M_arr = self.popt_full[j]
        if not self.Schwarzschild:
            a_arr = self.popt_full[j + 1]
        self.A_dict = {**self.A_fix_dict, **self.A_free_dict}
        self.phi_dict = {**self.phi_fix_dict, **self.phi_free_dict}
        if self.Schwarzschild:
            self.Ma_dict = {"M": M_arr}
        else:
            self.Ma_dict = {"M": M_arr, "a": a_arr}
        self.results_dict = {
            **self.A_fix_dict,
            **self.A_free_dict,
            **self.phi_fix_dict,
            **self.phi_free_dict,
            **self.Ma_dict}
        self.result_processed = True
        self.pickle_save()

    def pickle_save(self):
        with open(self.file_path, "wb") as f:
            pickle.dump(self, f)

    def pickle_exists(self):
        return os.path.exists(self.file_path)


class QNMFitVaryingStartingTime:

    def __init__(
            self,
            h,
            t0_arr,
            N_free=0,
            qnm_fixed_list=[],
            qnm_free_list=[],
            var_M_a=False,
            retro=False,
            Schwarzschild=False,
            run_string_prefix="Default",
            params0=None,
            max_nfev=200000,
            sequential_guess=True,
            load_pickle=True,
            nonconvergence_cut=False,
            A_bound=np.inf,
            jcf=None,
            fit_kwargs={},
            initial_num = 1,
            random_initial = False,
            initial_dict = {},
            A_guess_relative = True,
            set_seed = 1234,
            weighted = False,
            double_skip = True,
            include_mirror = False,
            iota = None,
            psi = None,
            mirror_ignore_phase = True,
            skip_i_init = 1):
        self.h = h
        if A_guess_relative:
            A_rel = np.abs(h.h[0])
        else:
            A_rel = 1
        self.t0_arr = t0_arr
        self.N_fix = len(qnm_fixed_list)
        self.var_M_a = var_M_a
        if var_M_a:
            self.N_free = len(qnm_free_list)
            self.qnm_free_list = qnm_free_list
        else:
            self.N_free = N_free
        self.qnm_fixed_list = qnm_fixed_list
        self.params0 = params0
        self.max_nfev = max_nfev
        if not hasattr(self.params0, "__iter__"):
            if var_M_a:
                if Schwarzschild:
                    self.params0 = jnp.array(
                        [A_rel, 1] * self.N_fix + [A_rel, 1] * self.N_free + [1])
                else:
                    self.params0 = jnp.array(
                        [A_rel, 1] * self.N_fix + [A_rel, 1] * self.N_free + [1, 0.5])
            else:
                self.params0 = jnp.array(
                    [A_rel, 1] * self.N_fix + [A_rel, 1, 1, -1] * self.N_free)
        self.sequential_guess = sequential_guess
        self.run_string_prefix = run_string_prefix
        self.load_pickle = load_pickle
        self.retro = retro
        self.Schwarzschild = Schwarzschild
        self.nonconvergence_cut = nonconvergence_cut
        self.A_bound = A_bound
        self.jcf = jcf
        self.fit_kwargs = fit_kwargs
        self.initial_num = initial_num
        self.random_initial = (random_initial and not self.var_M_a and self.N_free != 0)
        self.initial_dict = initial_dict
        self.A_guess_relative = A_guess_relative
        self.set_seed = set_seed
        self.weighted = weighted
        self.double_skip = double_skip
        self.include_mirror = include_mirror
        if self.include_mirror and self.N_free != 0:
            raise ValueError("Cannot include mirror if there are free parameters")
        self.iota = iota
        self.psi = psi
        if self.include_mirror and (self.iota is None or self.psi is None):
            raise ValueError("Must specify iota and phi to include mirror mode")
        self.mirror_ignore_phase = mirror_ignore_phase
        if self.include_mirror and not self.var_M_a:
            self.mirror_ratio_list = self.get_mirror_ratio_list()
        else:
            self.mirror_ratio_list = None

        self.skip_i_init = skip_i_init

    def get_mirror_ratio_list(self):
        self.mirror_ratio_list = []
        for mode in self.qnm_fixed_list:
            lmnx = mode.lmnx
            af = mode.a
            mirror_ratio = 1
            for lmn in lmnx:
                l, m, n = tuple(lmn)
                S_fac = S_retro_fac(self.iota, af, l, m, n, phi = self.psi)
                if self.mirror_ignore_phase:
                    mirror_ratio *= S_fac
                else:
                    raise ValueError("mirror including phase not implemented")
            self.mirror_ratio_list.append(mirror_ratio)
        return self.mirror_ratio_list

    def initial_guesses(self, jcf = None):
        A_val = np.abs(self.h.h[0])
        guess_list = make_initial_guess(self.N_free, self.initial_num, 
                                        A_guess_relative=self.A_guess_relative,
                                        seed = self.set_seed, A_val = A_val,
                                        **self.initial_dict)
        if isinstance(jcf, CurveFit):
            _jcf = jcf
        else:
            _jcf = CurveFit(flength=2 * len(self._time_longest))
        qnm_fit_list = []
        for j, guess in tqdm(enumerate(guess_list)):
            qnm_fit = QNMFit(
                        self.h,
                        self.t0_arr[0],
                        self.N_free,
                        qnm_fixed_list=self.qnm_fixed_list,
                        Schwarzschild=self.Schwarzschild,
                        params0=guess,
                        max_nfev=self.max_nfev,
                        A_bound=self.A_bound,
                        weighted=self.weighted,
                        include_mirror = self.include_mirror,
                        mirror_ratio_list = self.mirror_ratio_list,
                        **self.fit_kwargs)
            try:
                qnm_fit.do_fit(jcf = _jcf)
            except RuntimeError:
                print(f"{j}-th initial guess fit did not reach tolerance.\n")
                qnm_fit = None
            qnm_fit_list.append(qnm_fit)
        
        mismatches = []
        for i in range(self.initial_num):
            if qnm_fit_list[i] is None:
                mismatches.append(np.nan)
            else:
                mismatches.append(qnm_fit_list[i].result.mismatch)
        mismatches = np.array(mismatches)
        try:
            best_guess_index = np.nanargmin(mismatches)
        except ValueError:
            best_guess_index = None

        return best_guess_index, qnm_fit_list, guess_list

    def make_nan_result(self):

        nan_mismatch = np.nan
        if self.var_M_a:
            if self.Schwarzschild:
                nan_popt = np.full(
                    self.N_fix*2 + self.N_free*2 + 1, np.nan)
                nan_pcov = nan_popt
            else:
                nan_popt = np.full(
                    self.N_fix*2 + self.N_free*2 + 2, np.nan)
                nan_pcov = nan_popt
        else:
            nan_popt = np.full(
                self.N_fix*2 + self.N_free*4, np.nan)
            nan_pcov = nan_popt
        nan_cost = np.nan
        nan_grad = np.empty(self.N_fix*2 + self.N_free*4)
        nan_grad[:] = np.nan
        nan_nfev = self.max_nfev
        max_status = 0
        nan_result = QNMFitResult(
            nan_popt, nan_pcov, nan_mismatch, 
            nan_cost, nan_grad, nan_nfev, max_status)
        
        return nan_result


    def do_fits(self, jcf=None, return_jcf=False):
        
        skip_i = 0
        skip_consect = 0
        self.not_converged = False
        self.nonconvergence_indx = []
        self._time_longest, _, _ = self.h.postmerger(self.t0_arr[0])
        if isinstance(jcf, CurveFit):
            _jcf = self.jcf
        else:
            _jcf = CurveFit(flength=2 * len(self._time_longest))
        if self.var_M_a:
            self.result_full = QNMFitVaryingStartingTimeResultVarMa(
                self.t0_arr,
                self.qnm_fixed_list,
                self.qnm_free_list,
                self.Schwarzschild,
                run_string_prefix=self.run_string_prefix,
                nonconvergence_cut=self.nonconvergence_cut,
                include_mirror=self.include_mirror,
                iota = self.iota,
                psi = self.psi)
        else:
            self.result_full = QNMFitVaryingStartingTimeResult(
                self.t0_arr,
                self.qnm_fixed_list,
                self.N_free,
                run_string_prefix=self.run_string_prefix,
                nonconvergence_cut=self.nonconvergence_cut,
                initial_num = self.initial_num,
                include_mirror = self.include_mirror,
                mirror_ratio_list = self.mirror_ratio_list,
                iota = self.iota,
                psi = self.psi)
        loaded_results = False
        if self.result_full.pickle_exists() and self.load_pickle:
            try:
                _file_path = self.result_full.file_path
                with open(_file_path, "rb") as f:
                    self.result_full = pickle.load(f)
                print(
                    f"reloaded fit {self.result_full.run_string} from an old run.")
                loaded_results = True
            except EOFError:
                print("EOFError when loading pickle for fit. Doing new fit now...")
                loaded_results = False
        if loaded_results == False:
            if self.random_initial:
                best_guess_index, qnm_initial_fit_list, guess_list = self.initial_guesses(jcf = _jcf)
                if best_guess_index is None:
                    initial_converged = False
                else:
                    self.result_full.guess_list = guess_list
                    for i, qnm_initial_fit in enumerate(qnm_initial_fit_list):
                        if qnm_initial_fit is None:
                            fit_result = self.make_nan_result()
                        else:
                            fit_result = qnm_initial_fit.result
                        self.result_full.fill_initial_guess(i, fit_result)
                    initial_converged = True
            _params0 = self.params0
            for i, _t0 in tqdm(enumerate(self.t0_arr)):
                if self.var_M_a:
                    qnm_fit = QNMFitVarMa(
                        self.h,
                        _t0,
                        self.qnm_free_list,
                        qnm_fixed_list=self.qnm_fixed_list,
                        Schwarzschild=self.Schwarzschild,
                        params0=_params0,
                        max_nfev=self.max_nfev,
                        include_mirror = self.include_mirror,
                        iota = self.iota,
                        psi = self.psi,
                        **self.fit_kwargs)
                else:
                    qnm_fit = QNMFit(
                        self.h,
                        _t0,
                        self.N_free,
                        qnm_fixed_list=self.qnm_fixed_list,
                        Schwarzschild=self.Schwarzschild,
                        params0=_params0,
                        max_nfev=self.max_nfev,
                        A_bound=self.A_bound,
                        weighted=self.weighted,
                        include_mirror = self.include_mirror,
                        mirror_ratio_list = self.mirror_ratio_list,
                        **self.fit_kwargs)
                if self.nonconvergence_cut and self.not_converged:
                    qnm_fit.copy_from_result(qnm_fit_result_temp)
                else:
                    try:
                        if i == 0 and self.random_initial:
                            if initial_converged:
                                qnm_fit = qnm_initial_fit_list[best_guess_index]
                            else:
                                raise RuntimeError
                        else:
                            if skip_consect < skip_i  and self.double_skip:
                                raise RuntimeError
                            else:
                                qnm_fit.do_fit(jcf=_jcf)
                    except RuntimeError:
                        if skip_consect < skip_i:
                            print(f"skipped t0 = {_t0}.")
                        else:
                            print(f"fit did not reach tolerance at t0 = {_t0}.")
                        qnm_fit.result = self.make_nan_result()
                        self.nonconvergence_indx.append(i)
                        self.not_converged = True
                        if self.double_skip:
                            if skip_consect >= skip_i:
                                skip_consect = 0
                                if skip_i == 0:
                                    skip_i = self.skip_i_init
                                else:
                                    skip_i *= 2
                            skip_consect += 1
                    else:
                        skip_consect = 0
                        skip_i = 0
                        if self.sequential_guess:
                            _params0 = qnm_fit.result.popt
                self.result_full.fill_result(i, qnm_fit.result)
                qnm_fit_result_temp = qnm_fit.result
            self.result_full.nonconvergence_indx = self.nonconvergence_indx
            jcf = _jcf
            self.result_full.process_results()
            if return_jcf:
                return jcf


def fit_effective(omega_fund, A_merger, phi_merger, Mf, h):
    t_comp = np.concatenate((h.time, h.time))
    h_comp = np.concatenate((h.hr, h.hi))

    def fit_func(t_comp, c2, c3, d3, d4): return \
        effective_ringdown_for_fit(
            omega_fund, A_merger, phi_merger, Mf, t_comp, c2, c3, d3, d4)
    popt, pcov = curve_fit(fit_func, t_comp, h_comp, maxfev=10000)
    return popt, pcov


def effective_ringdown(omega_fund, A_merger, phi_merger, Mf, t, c2, c3, d3, d4, part="complex"):
    c1 = -A_merger*np.imag(omega_fund)*np.cosh(c3)**2/c2
    c4 = A_merger - c1*np.tanh(c3)
    d2 = 2*c2
    d1 = Mf*(1 + d3 + d4) / (d2 * (d3 + 2*d4)) * \
        (np.real(omega_fund) - phi_merger)
    A = c1*np.tanh(c2*t + c3) + c4
    phi = - d1 * np.log((1 + d3 * np.exp(-d2*t) + d4 *
                        np.exp(-2*d2*t)) / (1 + d3 + d4))
    if part == "complex":
        return A*np.exp(1.j*phi)*np.exp(-1.j*(omega_fund*t + phi_merger))
    elif part == "real":
        return np.real(A*np.exp(1.j*phi)*np.exp(-1.j*(omega_fund*t + phi_merger)))
    elif part == "imag":
        return np.imag(A*np.exp(1.j*phi)*np.exp(-1.j*(omega_fund*t + phi_merger)))
    else:
        raise ValueError("part must be complex, real or imag")
        return


def effective_ringdown_for_fit(omega_fund, A_merger, phi_merger, Mf, t_comp, c2, c3, d3, d4):
    fit_params = (c2, c3, d3, d4)
    N = int(len(t_comp)/2)
    h_real = effective_ringdown(
        omega_fund, A_merger, phi_merger, Mf, t_comp[:N], *fit_params, part="real")
    h_imag = effective_ringdown(
        omega_fund, A_merger, phi_merger, Mf, t_comp[N:], *fit_params, part="imag")
    h_comp = np.concatenate((h_real, h_imag))
    return h_comp


def fit_effective_2(h, A_fund, phi_fund, omega_fund, t_match):
    t_comp = np.concatenate((h.time, h.time))
    h_comp = np.concatenate((h.hr, h.hi))

    def fit_func(t_comp, c1, c2, d1, d2): return \
        effective_ringdown_for_fit_2(
            t_comp, A_fund, phi_fund, omega_fund, t_match, c1, c2, d1, d2)
    popt, pcov = curve_fit(fit_func, t_comp, h_comp, maxfev=1000000, bounds=([-np.inf, 0, 0, 0],
                                                                             [np.inf, np.inf, np.inf, np.inf]))
    return popt, pcov


def effective_ringdown_2(t, A_fund, phi_fund, omega_fund, t_match, c1, c2, d1, d2, part="complex"):
    A = -c1*(np.tanh((t - t_match)/c2)-1)/2 + A_fund
    # d1*np.log(1+d2*np.exp(-d3*(t-t_match)))
    phi = phi_fund - d1*(np.tanh((t - t_match)/d2)-1)/2
    if part == "complex":
        return A*np.exp(-1.j*(omega_fund * t + phi))
    elif part == "real":
        return np.real(A*np.exp(-1.j*(omega_fund * t + phi)))
    elif part == "imag":
        return np.imag(A*np.exp(-1.j*(omega_fund * t + phi)))
    else:
        raise ValueError("part must be complex, real or imag")
        return


def effective_ringdown_for_fit_2(t_comp, A_fund, phi_fund, omega_fund, t_match, c1, c2, d1, d2):
    fit_params = (c1, c2, d1, d2)
    N = int(len(t_comp)/2)
    h_real = effective_ringdown_2(
        t_comp[:N], A_fund, phi_fund, omega_fund, t_match, *fit_params, part="real")
    h_imag = effective_ringdown_2(
        t_comp[N:], A_fund, phi_fund, omega_fund, t_match, *fit_params, part="imag")
    h_comp = np.concatenate((h_real, h_imag))
    return h_comp
