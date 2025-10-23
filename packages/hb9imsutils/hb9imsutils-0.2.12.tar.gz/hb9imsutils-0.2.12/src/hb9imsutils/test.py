import time, sys, os

try:  # for dev testing
	import __init__ as ims
	import units
	print("LOCAL IMPORT")
except ImportError:
	try:
		import hb9imsutils as ims
		import hb9imsutils.units as units
	except ImportError:
		raise ImportError(
			f"hb9imsutils could not be found. Have you downloaded the lib?\n"
			f"path is set as {sys.path}\n"
			f"BTW if you got here if you cloned the repo or installed via pypi:\n"
			f" PLEASE make an issue and give me more info (like the path)\n"
			f"and/or write me a mail with 'hb9imsutils' in the subject line.\n"
		)

DELAY = "7m3"

units.VERBOSE = "-d" in sys.argv


@ims.PTimer(redraw_interval=0.033)
def high_accuracy_sleep(duration):
	end = duration + time.perf_counter()
	while time.perf_counter() < end:
		pass


def _test_number_converter(string):
	converted = units.number_converter(string)
	print(f"{string} -> {units.unitprint(converted) if converted is not None else converted} ({converted})")


@ims.timed
def test(untiprint_test_number, unitprint2_test_number,
	     prog_bar_correct_range, prog_bar_incorrect_range,
	     ptimer_num_runs, ptimer_sleep_duration):
	# number_converter test
	delay = units.number_converter(DELAY)
	# unitprint tests
	print(f"Delay in loop set to {delay} ({units.unitprint(delay, 's')})")
	print()
	print("UNITPRINT TESTS")
	print()
	print(untiprint_test_number)
	print(units.unitprint(untiprint_test_number, "m"))
	print(units.unitprint(untiprint_test_number, "m", power=1))
	print(units.unitprint(untiprint_test_number, "m", power=2))
	print(units.unitprint(untiprint_test_number, "m", power=3))
	print()
	print("BLOCK TESTS")
	print()
	print(units.unitprint_block(untiprint_test_number, "m"))
	print(units.unitprint_block(untiprint_test_number, "m", power=1))
	print(units.unitprint_block(untiprint_test_number, "m", power=2))
	print(units.unitprint_block(untiprint_test_number, "m", power=3))
	print()
	print("UNITPRINT2 TESTS")
	print()
	print(unitprint2_test_number)
	print(units.unitprint2(unitprint2_test_number, "B"))  # normal test
	print(units.unitprint2(unitprint2_test_number * 1024, "B"))  # one more test
	print(units.unitprint2(unitprint2_test_number * 1024 ** 10, "B"))  # too many test
	print()
	print("BLOCK TESTS")
	print()
	print(units.unitprint2_block(unitprint2_test_number, "B"))  # normal test
	print(units.unitprint2_block(unitprint2_test_number * 1024, "B"))  # one more test
	print(units.unitprint2_block(unitprint2_test_number * 1024 ** 10, "B"))  # too many test
	print()


	# number_converter tests
	print("+ NUMBER_CONVERTER TESTS")
	_test_number_converter("5k6")
	_test_number_converter("5.6k")
	_test_number_converter("5ex6")
	_test_number_converter("5.6ex")
	_test_number_converter("56e8")
	_test_number_converter("5.6e9")
	_test_number_converter(".56e10")
	print()
	print("- NUMBER_CONVERTER TESTS")
	_test_number_converter("5.6ex9")
	_test_number_converter("5.6.e9")
	_test_number_converter(".5.6e9")
	_test_number_converter("5.6e")
	_test_number_converter("5.6f9")
	print()

	print()
	print("PROGRESSBAR TESTS")
	print()

	# progres_bar tests
	progress_bar_long_str =  "long (estim. too low)"
	progress_bar_short_str =  "short (estim. too high)"
	progress_bar_correct_str =  "correct (estim. == max)"
	print()
	print("progress_bar (function)")
	print()
	print(progress_bar_short_str)
	print()

	t_s = time.time()
	for i in range(prog_bar_incorrect_range):
		print(ims.progress_bar(i, prog_bar_correct_range, time.time() - t_s), end="")
		time.sleep(delay)
	print(ims.progress_bar(prog_bar_incorrect_range, prog_bar_correct_range, time.time() - t_s))

	print()
	print(progress_bar_correct_str)
	print()

	t_s = time.time()
	for i in range(prog_bar_correct_range):
		print(ims.progress_bar(i, prog_bar_correct_range, time.time() - t_s), end="")
		time.sleep(delay)
	print(ims.progress_bar(prog_bar_correct_range, prog_bar_correct_range, time.time() - t_s))

	print()
	print(progress_bar_long_str)
	print()

	t_s = time.time()
	for i in range(prog_bar_correct_range):
		print(ims.progress_bar(i, prog_bar_incorrect_range, time.time() - t_s), end="")
		time.sleep(delay)
	print(ims.progress_bar(prog_bar_correct_range, prog_bar_incorrect_range, time.time() - t_s))
	print()

	# ProgressBar tests
	print()
	print("ProgressBar, as iterator")
	print()
	print(progress_bar_short_str)
	print()

	for i in ims.ProgressBar(range(prog_bar_incorrect_range), prog_bar_correct_range):
		time.sleep(delay)

	print()
	print(progress_bar_correct_str)
	print()

	for i in ims.ProgressBar(range(prog_bar_correct_range), prog_bar_correct_range):
		time.sleep(delay)

	print()
	print(progress_bar_long_str)
	print()

	for i in ims.ProgressBar(range(prog_bar_correct_range), prog_bar_incorrect_range):
		time.sleep(delay)

	print()
	print()
	print("ProgressBar, as seperate object")
	print()
	print(progress_bar_short_str)
	print()

	pb = ims.ProgressBar(None, prog_bar_correct_range)
	for i in range(prog_bar_incorrect_range):
		time.sleep(delay)
		pb()
	print()
	print(progress_bar_correct_str)
	print()

	pb = ims.ProgressBar(None, prog_bar_correct_range)
	for i in range(prog_bar_correct_range):
		time.sleep(delay)
		pb()
	print()
	print(progress_bar_long_str)
	print()

	pb = ims.ProgressBar(None, prog_bar_incorrect_range)
	for i in range(prog_bar_correct_range):
		time.sleep(delay)
		pb()
	print()
	print()

	# PTimer Test
	print()
	print("high_accuracy_sleep timing testing")
	print()
	for _ in range(ptimer_num_runs):
		high_accuracy_sleep(ptimer_sleep_duration)
	print(high_accuracy_sleep.summary_long())
	print()
	print(f"time.sleep timing testing")
	print(f"(we aim for {units.unitprint(ptimer_sleep_duration, 's')})(yeah it's that bad)")
	print(f"(at least in Py3.10.11)")
	print()
	timed_sleep = ims.PTimer(time.sleep, print_rate=100, length="long")
	for _ in range(ptimer_num_runs):
		timed_sleep(ptimer_sleep_duration)
	print(timed_sleep.summary_long())


def main():
	test(1e-18, 3**42, 20, 10, 1000, 0.001)
	time.sleep(5)


if __name__ == '__main__':
	main()
