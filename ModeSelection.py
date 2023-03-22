from utils import *
from QuasinormalMode import *
from Fit import *
from Waveforms import *
import numpy as np
import pickle
import json
import os

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
SCRATCH_PATH = "/expanse/lustre/scratch/mcheung1/temp_project/Ringdown/jaxqualin/"
MODE_SEARCHERS_SAVE_PATH = os.path.join(ROOT_PATH, "pickle/mode_searchers")
MODE_SEARCHERS_SAVE_PATH_SCRATCH = os.path.join(SCRATCH_PATH, "pickle/mode_searchers")
JSON_SAVE_PATH = os.path.join(ROOT_PATH, "json")


class IterativeFlatnessChecker:
    
    def __init__(self, h, t0_arr, M, a, l, m, found_modes, **kwargs_in):
        self.h = h
        self.t0_arr = t0_arr
        self.l = l
        self.m = m
        self.M = M
        self.a = a
        self.found_modes = found_modes
        self.fitter_list = []
        kwargs = {"run_string_prefix": "Default", "flatness_tol": 0.2,
                  "flatness_range": 10, "retro": False, "load_pickle": True,
                  "confusion_tol": 0.03, "quantile_range": 0.95,
                  "med_min" : 1e-3,
                  "weight_1": 1.0, "weight_2": 1.5,
                  }
        kwargs.update(kwargs_in)
        self.kwargs = kwargs
        self.run_string_prefix = self.kwargs["run_string_prefix"]
        self.flatness_tol = self.kwargs["flatness_tol"]
        self.confusion_tol = self.kwargs["confusion_tol"]
        self.flatness_range = self.kwargs["flatness_range"] 
        self.flatness_length = int(self.flatness_range/(self.t0_arr[1] - self.t0_arr[0])+1)
        self.quantile_range = self.kwargs["quantile_range"]
        self.med_min = self.kwargs["med_min"]
        self.weight_1 = self.kwargs["weight_1"]
        self.weight_2 = self.kwargs["weight_2"]
        
        self.retro = self.kwargs["retro"]
        self.load_pickle = self.kwargs["load_pickle"]
        
        
    def do_iterative_flatness_check(self):
        if self.retro:
            _fund_mode_string = f"{self.l}.-{self.m}.0"
        else:
            _fund_mode_string = f"{self.l}.{self.m}.0"
        _current_modes = self.found_modes
        _current_modes_string = qnms_to_string(_current_modes)
        if _fund_mode_string not in _current_modes_string:
            _current_modes.append(mode(_fund_mode_string, self.M, self.a, retro=self.retro))
        i = 0
        _discard_mode = True
        _more_than_one_mode = True
        while _discard_mode and _more_than_one_mode:
            self.fitter_list.append(QNMFitVaryingStartingTime(
                    self.h,
                    self.t0_arr,
                    0,
                    _current_modes,
                    run_string_prefix=self.run_string_prefix,
                    load_pickle = self.load_pickle))
            _current_modes_string = qnms_to_string(_current_modes)
            _fund_mode_indx = _current_modes_string.index(_fund_mode_string)
            _fitter = self.fitter_list[i]
            _fitter.do_fits()
            _fluc_least_list = []
            _fluc_least_indx_list = []
            _fluc_least_list = []
            _fluc_least_indx_list = []
            for j in range(len(_current_modes)):
                _A_fix_j_arr = np.abs(list(_fitter.result_full.A_fix_dict["A_" + _current_modes_string[j]]))
                _phi_fix_j_arr = list(_fitter.result_full.phi_fix_dict["phi_" + _current_modes_string[j]])
                _fluc_least_indx, _fluc_least = flattest_region_quadrature(
                    self.flatness_length,
                    _A_fix_j_arr, _phi_fix_j_arr, 
                    quantile_range = self.quantile_range,
                    med_min = self.med_min,
                    weight_1 = self.weight_1, weight_2 = self.weight_2)
                _fluc_least_list.append(_fluc_least)
                _fluc_least_indx_list.append(_fluc_least_indx)
            if len(_current_modes) <= 1:
                break
            _fluc_least_list_no_fund = _fluc_least_list.copy()
            del _fluc_least_list_no_fund[_fund_mode_indx]
            _worst_mode_indx = _fluc_least_list.index(max(_fluc_least_list_no_fund))
            bad_mode_indx_list = []
            bad_mode_fluc_list = []
            for ii, fluc_least in enumerate(_fluc_least_list):
                if fluc_least > self.flatness_tol:
                    bad_mode_indx_list.append(ii)
                    bad_mode_fluc_list.append(fluc_least)
            _discard_mode = _fluc_least_list[_worst_mode_indx] > self.flatness_tol
            worst_mode = _current_modes[_worst_mode_indx]
            worst_l, worst_m = worst_mode.sum_lm()
            sacrifice_mode = False
            sacrifice_fluc = 0
            if worst_mode.is_overtone() and worst_l == self.l and worst_m == self.m:
                for jj in bad_mode_indx_list:
                    if jj == _worst_mode_indx:
                        continue
                    bad_mode = _current_modes[jj]
                    if np.abs(bad_mode.omega - worst_mode.omega) < self.confusion_tol:
                        sacrifice_mode = True
                        if _fluc_least_list[jj] > sacrifice_fluc:
                            sacrifice_fluc = _fluc_least_list[jj]
                            sacrifice_mode_indx = jj
            # print(_fluc_least_list)
            if _discard_mode:
                if sacrifice_mode:
                    print(f"Although the {_current_modes[_worst_mode_indx].string()} mode fluctuates the most, "
                           "the {_current_modes[sacrifice_mode_indx].string()} mode is sacrificed instead.")
                    del _current_modes[sacrifice_mode_indx]
                else:
                    print(f"discarding {_current_modes[_worst_mode_indx].string()} mode because it failed flatness test.")
                    del _current_modes[_worst_mode_indx]
            _more_than_one_mode = len(_current_modes)>1
            i += 1
        self.fluc_least_indx_list = _fluc_least_indx_list
        self.found_modes_screened = _current_modes


class ModeSelectorAllFree:
    def __init__(
            self,
            result_full,
            potential_mode_list,
            omega_r_tol=0.05,
            omega_i_tol=0.05,
            t_tol=10,
            fraction_tol=0.95):
        self.result_full = result_full
        self.potential_mode_list = potential_mode_list
        self.omega_r_tol = omega_r_tol
        self.omega_i_tol = omega_i_tol
        self.t_tol = t_tol
        self.fraction_tol = fraction_tol
        self.passed_mode_list = []
        self.passed_mode_indx = []

    def select_modes(self):
        for i, _mode in enumerate(self.potential_mode_list):
            min_distance = closest_free_mode_distance(self.result_full, _mode,
                                                      r_scale=self.omega_r_tol,
                                                      i_scale=self.omega_i_tol)
            _start_indx, _end_indx = max_consecutive_trues(
                min_distance < 1, tol=self.fraction_tol)
            _t0_arr = self.result_full.t0_arr
            if _t0_arr[_end_indx] - _t0_arr[_start_indx] > self.t_tol:
                self.passed_mode_list.append(_mode)
                self.passed_mode_indx.append(i)

    def do_selection(self):
        self.select_modes()


class ModeSearchAllFreeLM:
    def __init__(
            self,
            h,
            M,
            a,
            relevant_lm_list=[],
            t0_arr=np.linspace(
                0,
                50,
                num=501),
            N_init=5,
            N_step=3,
            iterations=2,
            **kwargs_in):
        self.h = h
        self.l = self.h.l
        self.m = self.h.m
        self.M = M
        self.a = a
        self.relevant_lm_list = relevant_lm_list
        self.t0_arr = t0_arr
        self.N_init = N_init
        self.N_step = N_step
        self.iterations = iterations
        kwargs = {"retro": False, "run_string_prefix": "Default", "load_pickle": True,
                  "a_recoil_tol": 0., "recoil_n_max" : 0,
                  "omega_r_tol" : 0.05, "omega_i_tol" : 0.05,
                  "t_tol" : 10, "fraction_tol" : 0.95, 'fit_kwargs' : {}, 
                  "initial_num" : 1, "random_initial" : False, "initial_dict" : {},
                  "A_guess_relative" : True, "set_seed" : 1234}
        kwargs.update(kwargs_in)
        self.kwargs = kwargs
        self.retro = self.kwargs["retro"]
        self.run_string_prefix = self.kwargs["run_string_prefix"]
        self.a_recoil_tol = self.kwargs["a_recoil_tol"]
        self.omega_r_tol = self.kwargs["omega_r_tol"]
        self.omega_i_tol = self.kwargs["omega_i_tol"]
        self.t_tol = self.kwargs["t_tol"]
        self.fraction_tol = self.kwargs["fraction_tol"]
        self.recoil_n_max = self.kwargs["recoil_n_max"]
        if self.a >= self.a_recoil_tol:
            self.potential_modes_full = potential_modes(
                self.l, self.m, self.M, self.a, self.relevant_lm_list, retro = self.retro)
        else:
            self.potential_modes_full = potential_modes(
                self.l, self.m, self.M, self.a, [(self.l, self.m)], retro = self.retro,
                  recoil_n_max = self.recoil_n_max)
        self.potential_modes = self.potential_modes_full.copy()
        self.load_pickle = self.kwargs["load_pickle"]
        self.fit_kwargs = self.kwargs["fit_kwargs"]
        self.initial_num = self.kwargs["initial_num"]
        self.random_initial = self.kwargs["random_initial"]
        self.initial_dict = self.kwargs["initial_dict"]
        self.A_guess_relative = self.kwargs["A_guess_relative"]
        self.set_seed = self.kwargs["set_seed"]

    def mode_search_all_free(self):
        _N = self.N_init
        self.found_modes = []
        for i in range(self.iterations):
            if i > 0:
                _N = self.N_step
            self.full_fit = QNMFitVaryingStartingTime(
                self.h,
                self.t0_arr,
                _N,
                self.found_modes,
                run_string_prefix=self.run_string_prefix,
                load_pickle = self.load_pickle,
                fit_kwargs = self.fit_kwargs,
                initial_num = self.initial_num,
                random_initial = self.random_initial,
                initial_dict = self.initial_dict,
                A_guess_relative = self.A_guess_relative,
                set_seed = self.set_seed)
            self.full_fit.do_fits()
            self.mode_selector = ModeSelectorAllFree(
                self.full_fit.result_full, self.potential_modes, omega_r_tol = self.omega_r_tol,
                omega_i_tol=self.omega_i_tol, t_tol=self.t_tol, fraction_tol=self.fraction_tol)
            self.mode_selector.do_selection()
            print(qnms_to_string(self.mode_selector.passed_mode_list))
            _jump_mode_indx = []
            for j in range(len(self.mode_selector.passed_mode_list)):
                if not lower_overtone_present(
                        self.mode_selector.passed_mode_list[j],
                        self.mode_selector.passed_mode_list + self.found_modes):
                    _jump_mode_indx.append(j)
                if not lower_l_mode_present(self.l, self.m, 
                                            self.relevant_lm_list, 
                                            self.mode_selector.passed_mode_list[j], 
                                            self.mode_selector.passed_mode_list + self.found_modes):
                    _jump_mode_indx.append(j)
            print(list(set(_jump_mode_indx)))
            for k in sorted(list(set(_jump_mode_indx)), reverse=True):
                del self.mode_selector.passed_mode_list[k]
            if len(self.mode_selector.passed_mode_list) == 0:
                break
            self.found_modes.extend(self.mode_selector.passed_mode_list)
            print(qnms_to_string(self.mode_selector.passed_mode_list))
            for j in sorted(self.mode_selector.passed_mode_indx, reverse=True):
                del self.potential_modes[j]

    def do_mode_search(self):
        self.mode_search_all_free()


class ModeSearchAllFreeLMSXS:
    def __init__(
            self,
            SXSnum,
            l,
            m,
            N_init=5,
            N_step=3,
            iterations=2,
            **kwargs):
        self.SXSnum = SXSnum
        self.l = l
        self.m = m
        self.N_init = N_init
        self.N_step = N_step
        self.iterations = iterations
        self.get_waveform()
        self.kwargs = kwargs

    def mode_search_all_free_sxs(self):
        self.mode_searcher = ModeSearchAllFreeLM(
            self.h,
            self.M,
            self.a,
            self.relevant_lm_list,
            N_init=self.N_init,
            N_step=self.N_step,
            iterations=self.iterations,
            retro = self.retro,
            set_seed = int(self.SXSnum),
            **self.kwargs)
        self.mode_searcher.do_mode_search()
        self.found_modes = self.mode_searcher.found_modes

    def do_mode_search(self):
        self.mode_search_all_free_sxs()

    def get_waveform(self):
        _relevant_modes_dict, self.retro = get_relevant_lm_waveforms_SXS(self.SXSnum)
        self.relevant_lm_list = relevant_modes_dict_to_lm_tuple(
            _relevant_modes_dict)
        peaktime_dom = list(_relevant_modes_dict.values())[0].peaktime
        self.h, self.M, self.a, self.Lev, _retro = get_waveform_SXS(
            self.SXSnum, self.l, self.m)
        self.h.update_peaktime(peaktime_dom)


class ModeSearchAllFreeVaryingN:
    def __init__(
            self,
            h,
            M,
            a,
            relevant_lm_list=[],
            t0_arr=np.linspace(
                0,
                50,
                num=501),
            flatness_checker_kwargs = {},
            mode_searcher_kwargs = {},
            **kwargs_in):
        self.h = h
        self.l = self.h.l
        self.m = self.h.m
        self.M = M
        self.a = a
        self.relevant_lm_list = relevant_lm_list
        self.t0_arr = t0_arr
        kwargs = {'run_string_prefix' : 'Default',
                  'load_pickle' : True,
                  'N_list' : [5, 6, 7, 8, 9, 10]}
        kwargs.update(kwargs_in)
        self.N_list = kwargs['N_list']
        self.kwargs = kwargs
        self.flatness_checker_kwargs = flatness_checker_kwargs
        self.mode_searcher_kwargs = mode_searcher_kwargs
        self.mode_searchers = []
        self.init_searchers()
        self.found_modes_final = []
        self.run_string_prefix = kwargs["run_string_prefix"]
        self.load_pickle = self.kwargs["load_pickle"]

    def init_searchers(self):
        for _N_init in self.N_list:
            self.mode_searchers.append(
                ModeSearchAllFreeLM(
                    self.h,
                    self.M,
                    self.a,
                    self.relevant_lm_list,
                    N_init=_N_init,
                    iterations=1,
                    **self.mode_searcher_kwargs,
                    **self.kwargs))

    def do_mode_searches(self):
        self.fixed_fitters = []
        self.flatness_checkers = []
        for i, _mode_searcher in enumerate(self.mode_searchers):
            _mode_searcher.do_mode_search()
            self.flatness_checkers.append(IterativeFlatnessChecker(self.h, self.t0_arr, self.M, self.a, self.l, self.m,
            _mode_searcher.found_modes, **self.flatness_checker_kwargs, **self.kwargs))
            _flatness_checker = self.flatness_checkers[i]
            _flatness_checker.do_iterative_flatness_check()
            _flatness_checker.found_modes_screened
            self.fixed_fitters.append(
                QNMFitVaryingStartingTime(
                    self.h,
                    self.t0_arr,
                    0,
                    qnm_fixed_list=_flatness_checker.found_modes_screened,
                    run_string_prefix=self.run_string_prefix,
                    load_pickle = self.load_pickle))
            self.fixed_fitters[i].do_fits()
            if len(_mode_searcher.found_modes) >= len(self.found_modes_final):
                self.best_run_indx = i
                self.found_modes_final = _mode_searcher.found_modes


class ModeSearchAllFreeVaryingNSXS:

    def __init__(
            self,
            SXSnum,
            l,
            m,
            t0_arr=np.linspace(
                0,
                50,
                num=501),
            **kwargs_in):
        self.SXSnum = SXSnum
        self.l = l
        self.m = m
        self.t0_arr = t0_arr
        kwargs = {'load_pickle' : True,
                  'N_list' : [5, 6, 7, 8, 9, 10],
                  'postfix_string' : '',
                  'pickle_in_scratch' : False,
                  'set_seed_SXS' : True,
                  'default_seed' : 1234}
        kwargs.update(kwargs_in)
        self.N_list = kwargs['N_list']
        self.postfix_string = kwargs['postfix_string']
        self.kwargs = kwargs
        self.get_waveform()
        self.N_list_string = '_'.join(list(map(str, self.N_list)))
        self.run_string = f"SXS{self.SXSnum}_lm_{self.l}.{self.m}_N_{self.N_list_string}"
        if kwargs["pickle_in_scratch"]:
            save_path = MODE_SEARCHERS_SAVE_PATH_SCRATCH
        else:
            save_path = MODE_SEARCHERS_SAVE_PATH
        if self.postfix_string == '':
            self.file_path = os.path.join(save_path,
                                           f"ModeSearcher_{self.run_string}.pickle")
        else:
            self.file_path = os.path.join(save_path,
                                           f"ModeSearcher_{self.run_string}_{self.postfix_string}.pickle")
        self.load_pickle = self.kwargs["load_pickle"]
        if self.kwargs['set_seed_SXS']:
            self.set_seed = int(self.SXSnum)
        else:
            self.set_seed = self.kwargs['default_seed']

    def mode_search_varying_N_sxs(self):
        self.mode_searcher_vary_N = ModeSearchAllFreeVaryingN(
            self.h,
            self.M,
            self.a,
            self.relevant_lm_list,
            t0_arr=self.t0_arr,
            retro = self.retro,
            set_seed = self.set_seed,
            **self.kwargs)
        self.mode_searcher_vary_N.do_mode_searches()
        self.found_modes_final = self.mode_searcher_vary_N.found_modes_final

    def do_mode_search_varying_N(self):
        self.mode_search_varying_N_sxs()
        self.pickle_save()

    def get_waveform(self):
        _relevant_modes_dict, self.retro = get_relevant_lm_waveforms_SXS(self.SXSnum)
        self.relevant_lm_list = relevant_modes_dict_to_lm_tuple(
            _relevant_modes_dict)
        peaktime_dom = list(_relevant_modes_dict.values())[0].peaktime
        self.h, self.M, self.a, self.Lev, _retro = get_waveform_SXS(
            self.SXSnum, self.l, self.m)
        self.h.update_peaktime(peaktime_dom)

    def pickle_save(self):
        with open(self.file_path, "wb") as f:
            pickle.dump(self, f)

    def pickle_exists(self):
        if self.load_pickle:
            return os.path.exists(self.file_path)
        else:
            return False


class ModeSearchAllFreeVaryingNSXSAllRelevant:

    def __init__(
            self,
            SXSnum,
            t0_arr=np.linspace(
                0,
                50,
                num=501),
            **kwargs_in):
        self.SXSnum = SXSnum
        self.t0_arr = t0_arr
        kwargs = {'load_pickle' : True,
                  'N_list' : [5, 6, 7, 8, 9, 10],
                  'postfix_string' : ''}
        kwargs.update(kwargs_in)
        self.kwargs = kwargs
        self.load_pickle = kwargs['load_pickle']
        self.N_list = kwargs['N_list']
        self.postfix_string = kwargs['postfix_string']
        self.get_relevant_lm_list()
        self.get_relevant_lm_mode_searcher_varying_N()

    def do_all_searches(self):
        for _i, _searcher in enumerate(
                self.relevant_lm_mode_searcher_varying_N):
            if _searcher.pickle_exists() and self.load_pickle:
                _file_path = _searcher.file_path
                with open(_file_path, "rb") as f:
                    self.relevant_lm_mode_searcher_varying_N[_i] = pickle.load(
                        f)
                print(
                    f"reloaded lm = {self.relevant_lm_list[_i][0]}.{self.relevant_lm_list[_i][0]} from an old run.")
            else:
                self.relevant_lm_mode_searcher_varying_N[_i].do_mode_search_varying_N(
                )

    def get_relevant_lm_list(self):
        _relevant_modes_dict, self.retro = get_relevant_lm_waveforms_SXS(self.SXSnum)
        self.relevant_lm_list = relevant_modes_dict_to_lm_tuple(
            _relevant_modes_dict)

    def get_relevant_lm_mode_searcher_varying_N(self):
        self.relevant_lm_mode_searcher_varying_N = []
        for _lm in self.relevant_lm_list:
            _l, _m = _lm
            _run_string_prefix = f"SXS{self.SXSnum}_lm_{_l}.{_m}"
            # if self.postfix_string != '':
            #     _run_string_prefix += self.postfix_string
            self.relevant_lm_mode_searcher_varying_N. append(
                ModeSearchAllFreeVaryingNSXS(
                    self.SXSnum,
                    _l,
                    _m,
                    t0_arr=self.t0_arr,
                    run_string_prefix=_run_string_prefix,
                    **self.kwargs))


def closest_free_mode_distance(result_full, mode, r_scale=1, i_scale=1):
    omega_r_dict = result_full.omega_dict["real"]
    omega_i_dict = result_full.omega_dict["imag"]
    omega_r_arr = np.array(list(omega_r_dict.values()))
    omega_i_arr = np.array(list(omega_i_dict.values()))
    scaled_distance_arr = ((omega_r_arr - mode.omegar) / \
                           r_scale)**2 + ((omega_i_arr - mode.omegai) / i_scale)**2
    min_distance = np.nanmin(scaled_distance_arr, axis=0)
    return min_distance

# def flattest_region(length, arr, quantile_range = 0.95, normalize_by = None):
#     total_length = len(arr)
#     quantile_low = (1 - quantile_range)/2
#     quantile_hi = 1 - quantile_low
#     fluc_least = np.inf
#     fluc_least_indx = 0
#     for i in range(total_length - length):
#         arr_in_range = arr[i:i+length]
#         hi = np.quantile(arr_in_range,quantile_hi)
#         low = np.quantile(arr_in_range,quantile_low)
#         med = np.quantile(arr_in_range, 0.5)
#         if normalize_by is None:
#             normalize = med
#         else:
#             normalize = normalize_by
#         fluc = (hi - low)/normalize
#         if fluc < fluc_least:
#             fluc_least = fluc
#             fluc_least_indx = i
#     return fluc_least_indx, fluc_least

def flattest_region_quadrature(length, arr1, arr2, quantile_range = 0.95, 
                               normalize_1_by = None, normalize_2_by = 2*np.pi, 
                               med_min = 1e-3, weight_1 = 1, weight_2 = 1.5):
    if len(arr1) != len(arr2):
        raise Exception("The length of the two arrays do not match")
    nan_tol = 1 - quantile_range
    total_length = len(arr1)
    quantile_low = (1 - quantile_range)/2
    quantile_hi = 1 - quantile_low
    fluc_least = np.inf
    fluc_least_indx = 0
    for i in range(total_length - length):
        arr1_in_range = arr1[i:i+length]
        arr2_in_range = arr2[i:i+length]
        if length > 0:
            arr1_nan_frac = np.sum(np.isnan(arr1_in_range))/length
            arr2_nan_frac = np.sum(np.isnan(arr2_in_range))/length
        else:
            arr1_nan_frac = 1
            arr2_nan_frac = 1
        quantile_adj = min(arr1_nan_frac/2, nan_tol/2)
        hi1 = np.nanquantile(arr1_in_range,min(1, quantile_hi+quantile_adj))
        low1 = np.nanquantile(arr1_in_range,max(0, quantile_low-quantile_adj))
        med1 = max(np.nanquantile(arr1_in_range, 0.5), med_min)
        if normalize_1_by is None:
            normalize1 = med1
        else:
            normalize1 = normalize_1_by
        fluc1 = (hi1 - low1)/normalize1
        
        hi2 = np.nanquantile(arr2_in_range,min(1, quantile_hi+quantile_adj))
        low2 = np.nanquantile(arr2_in_range,max(0, quantile_low-quantile_adj))
        med2 = max(np.nanquantile(arr2_in_range, 0.5), med_min)
        if normalize_2_by is None:
            normalize2 = med2
        else:
            normalize2 = normalize_2_by
        fluc2 = (hi2 - low2)/normalize2
        
        fluc = np.sqrt((fluc1*weight_1)**2 + (fluc2*weight_2)**2)
        
        if fluc < fluc_least and arr1_nan_frac < nan_tol:
            fluc_least = fluc
            fluc_least_indx = i
            # hi1_best, low1_best, med1_best, normalize1_best, fluc1_best, hi2_best, low2_best, med2_best, normalize2_best, fluc2_best = (hi1, low1, med1, normalize1, fluc1, hi2, low2, med2, normalize2, fluc2)
    # print(hi1_best, low1_best, med1_best, normalize1_best, fluc1_best, hi2_best, low2_best, med2_best, normalize2_best, fluc2_best)
    return fluc_least_indx, fluc_least
    

def eff_mode_search(inject_params, runname, retro = False, load_pickle = True, delay = True,
                     **kwargs):
    
    Mf = inject_params['Mf']
    af = inject_params['af']
    relevant_lm_list = inject_params['relevant_lm_list']
    h_eff = make_eff_ringdown_waveform_from_param(inject_params, delay = delay)
    mode_searcher = ModeSearchAllFreeVaryingN(h_eff, Mf, af, relevant_lm_list = relevant_lm_list, 
                                          retro = retro, run_string_prefix = runname,
                                          load_pickle = load_pickle, **kwargs)
    mode_searcher.do_mode_searches()
    
    return mode_searcher
    
# def all_eff_mode_searches(inject_params_full, runname, N_list, retro = False, load_pickle = True):
    
#     mode_searcher_list = []
    
#     for inject_params in inject_params_full:
#         eff_mode_search(inject_params, runname, N_list, 
#                         retro = retro, load_pickle = load_pickle)
#         mode_searcher_list.append(mode_searcher)

def read_json_eff_mode_search(i, batch_runname, retro = False, load_pickle = True, delay = True, **kwargs):
    
    with open(f"{JSON_SAVE_PATH}/{batch_runname}.json", 'r') as f:
        inject_params_full = json.load(f)
    
    runname = f"{batch_runname}_{i:03d}"
    mode_searcher = eff_mode_search(inject_params_full[runname], runname,
                                    retro = retro, load_pickle = load_pickle,
                                    delay = delay, **kwargs)
    
    return mode_searcher

def read_json_for_param_dict(i, batch_runname):
    
    with open(f"{JSON_SAVE_PATH}/{batch_runname}.json", 'r') as f:
        inject_params_full = json.load(f)
    
    runname = f"{batch_runname}_{i:03d}"
    
    return inject_params_full[runname]