import os
import time
import numpy as np
try:
    from .units import (
        unitprint,
        unitprint_block,
        number_converter,
        unitprint2,
        unitprint2_block,
        VERBOSE
    )
except ImportError:
    try:  # should only be used in dev
        from units import(
            unitprint,
            unitprint_block,
            number_converter,
            unitprint2,
            unitprint2_block,
            VERBOSE
        )
        print("UNITS SUBMODULE IMPORTED WITHOUT PARRENT REFERENCE")
        print("THIS SHOULD ONLY HAPPEN WHILE DEVELOPPING; NOT IN PRODUCTION")
    except ImportError:
        raise ImportError("units submodule not found; package broken")


NAN = float("nan")
INF = float("inf")


def timed(f):
    """time a function"""
    def fx(*args, **kwargs):
        f"""
        timed function
        {f.__doc__}"""
        start = time.perf_counter_ns()
        res = f(*args, **kwargs)
        end = time.perf_counter_ns()
        print(f'{f.__name__} took {unitprint((end - start) * 1e-9, "s")}')
        return res

    return fx


def ask_option(question, options, /, ignore_case=True):
    """
    Asks the user for an input from the `outputs` list and returns the index
    :param question: the question
    :type question: str
    :param options: the options the user will choose from
    :type options: list[str]
    :param ignore_case: wether the case is important to the choice
    :returns: the index the user has chosen
    :rtype: int
    """
    if ignore_case:
        options = map(lambda i: i.lower(), options)
    while True:
        x = input(question)
        if ignore_case:
            x = x.lower()
        if x in options:
            return options.index(x)
        print("Invalid option, please try again ...")


def ask_float(question):
    """
    Asks the user for a float by printing the question and returning a valid float
    Engineering prefixes are supported
    :param question: the question in question
    :type question: str
    :returns: a float provided from the user
    :rtype: float
    """
    while (x := number_converter(input(question))) is None:
        print("Number not recognized, please try again ...")
    return x


def progress_bar(status, total, passed_time=None, force_warning=False):
    """
    Returns a nice progress bar
    :param status: the current position
    :param total: the maximum position
    :param passed_time: the time passed since the start
    :param force_warning: if true forces '!' instead of '='
    :returns: the progress bar
    """
    base_char = "!" if force_warning else "="
    arrow_base = base_char * int(status / total * 50)
    spaces = ' ' * (50 - len(arrow_base) - 1)

    eta = ""
    elapsed = ""

    percentage = f"{(status / total * 100):8.4f}%"

    if passed_time is not None:
        eta_ = passed_time * (total - status) / (status or NAN)
        if status <= 100e-6:  # Predictions within the first 100us definetly do not make sense
            eta = f"ETA {str(NAN): ^12}"
        else:
            eta = (f"ETA: {eta_ // 3600:2.0f}h "
                   f"{eta_ // 60 % 60:2.0f}m "
                   f"{eta_ % 60:2.0f}s")
        elapsed = (f"Elapsed: "
                   f"{passed_time // 3600:2.0f}h "
                   f"{passed_time // 60 % 60:2.0f}m "
                   f"{passed_time % 60:2.0f}s")
    if status < total:
        return f'\r[{arrow_base}>{spaces}] {percentage} {eta} {elapsed}'
    elif status == total:
        return f'\r[{base_char * 50}] {percentage} {eta} {elapsed}'
    else:
        return f"\r[{'!' * 50}] {percentage} ETA {str(NAN): ^12} {elapsed}"


class ProgressBar:
    """
    Alive-like progress bar, but with time predictions
    """

    def __init__(self, iterable, expected_iterations, redraw_interval=0.033):
        """
        :param iterable: the iterable to wrap
        :param expected_iterations: 
        :param redraw_interval: minimum time between draws in s (default 30fps)
        """
        self.start_time = time.time()
        self.last_draw = 0
        self.iterable = iterable
        self.current_iteration = 0
        self.expected_iterations = expected_iterations
        self.redraw_interval = redraw_interval

    def _print_bar(self, end=False):
        if (self.last_draw + self.redraw_interval < time.time()
            or end or self.current_iteration == self.expected_iterations):
            print(progress_bar(
                self.current_iteration, 
                self.expected_iterations, 
                time.time() - self.start_time,
                force_warning=(end and self.current_iteration != self.expected_iterations),
            ), flush=True, end="")
            self.last_draw = time.time()

    def __iter__(self):
        for obj in self.iterable:
            self._print_bar()
            yield obj
            self.current_iteration += 1
            self._print_bar()
        self._print_bar(end=True)
        print()

    def __call__(self):
        self.current_iteration += 1
        self._print_bar()
        return self.current_iteration - 1


class PTimer:
    """
    Wrapper for timing a function over all calls. 
    """
    def __init__(self, func=None, *, print_rate=None, redraw_interval=None, length="short"):
        if print_rate is not None and redraw_interval is not None:
            raise ValueError("Must set either print rate or redraw interval")
        if print_rate is None:
            print_rate = 0
        if redraw_interval is None:
            redraw_interval = 0

        if length not in ["short", "long"]:
            raise ValueError("length must be either short or long")
        self.length = length

        self.print_rate = print_rate
        self.counter = 0
        self.counter_total = 0

        self.redraw_interval = redraw_interval
        self.last_draw = 0

        self.func = func
        self.times = []

    def __call__(self, *args, **kwargs):
        if self.func is None:
            # Validate args
            if len(args) != 1:
                raise ValueError("must provide one fuction")
            if not callable(args[0]):
                raise ValueError("function must be callable")

            self.func = args[0]
            return self
        else:
            # get a rough estimate on how long getting the time takes
            time_bench1 = time.perf_counter_ns()
            time_bench2 = time.perf_counter_ns()
            start = time.perf_counter_ns()
            res = self.func(*args, **kwargs)
            end = time.perf_counter_ns()
            self.log_time((end - start) - (time_bench2 - time_bench1))
            return res

    def log_time(self, exec_time):
        """
        log a run
        :param exec_time: execution time in ns
        """
        self.times.append(exec_time)
        self.counter += 1
        self.counter_total += 1
        if self.counter_total <= 1:
            return  # printing stats is impossible
        if self.print_rate:
            if self.counter >= self.print_rate:
                self._print()
        if self.redraw_interval:
            if self.last_draw + self.print_rate > time.time():
                self._print()

    def _print(self):
         self.counter = 0
         self.last_draw = time.time()
         if self.length == "short":
             print(self.summary_short())
         elif self.length == "long":
             print(self.summary_long())
         else:
             raise ValueError(f"invalid length: {repr(self.length)} "
                              f"not in ('short', 'long')")

    def get_stats(self):
        """
        Calculates the timing stats and returns them in a namespace.
        Stats:
        - avg: average runtime
        - med: median runtime
        - q3: 25% highs (shortest times)
        - q1: 25% lows (longest times)
        - d1: 10% lows (longest times)
        - c1: 1% lows (longest times)
        - std_abs: the absolute standard deviation
        - std_rel: the relative standard deviation (in factor, NOT %)
        """
        if not len(self.times) - 1:
            raise ValueError("not enough times were recorded")
        
        data = np.array(self.times)
        
        avg = np.mean(data)
        med = np.median(data)
        q3 = np.percentile(data, 25)
        q1 = np.percentile(data, 75)
        d1 = np.percentile(data, 90)
        c1 = np.percentile(data, 99)
        std_abs = np.std(data, ddof=1)
        std_rel = (std_abs / avg) if avg != 0 else (NAN if std_abs == 0 else INF)

        return Namespace(**{
            "avg": avg,
            "med": med,
            "q1": q1,
            "q3": q3,
            "d1": d1,
            "c1": c1,
            "std_abs": std_abs,
            "std_rel": std_rel,
        })

    def summary_short(self):
        stats = self.get_stats()
        return (f"{self.func.__name__} took {unitprint(stats.avg * 1e-9, 's')}"
                f" ± {stats.std_rel * 100:.3f}% ({unitprint(stats.std_abs * 1e-9, 's')})")

    def summary_long(self, sep="\n"):
        stats = self.get_stats()
        return sep.join((
            f"{self.func.__name__} took {unitprint(stats.avg * 1e-9, 's')}"
            f" ± {stats.std_rel * 100:.3f}% ({unitprint(stats.std_abs * 1e-9, 's')}) ",
            f"25% Hi: {unitprint_block(stats.q3 * 1e-9, 's')}",
            f"25% Lo: {unitprint_block(stats.q1 * 1e-9, 's')}",
            f"10% Lo: {unitprint_block(stats.d1 * 1e-9, 's')}",
            f" 1% Lo: {unitprint_block(stats.c1 * 1e-9, 's')}",
            f"measured over {self.counter_total: 3} calls"
        ))


class Namespace(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __setattr__(self, key, value):
        self.__dict__[key] = value

    def __getattr__(self, item):
        return self.__dict__[item]

    def __delattr__(self, item):
        del self.__dict__[item]
