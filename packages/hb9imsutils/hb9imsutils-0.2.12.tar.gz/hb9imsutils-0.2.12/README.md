# hb9imsutils
This python package is a small collection of tools accumulated over some time.

currently WIP... (when I need to update it; I'm not that active :C)

## Most important docs:
### Progress bars

I mostly recommend making a wrapped iterator using the `ProgressBar` class,
even though you don't need it to be an iterator. 

The ETA is calculated with the assumption that your code
takes the about same time for each iteration

Inspired by TQDM (but in any way or form worse)

#### How to use
You initiate a progress bar with:

`ProgressBar(an iterable object or None, expected iterations, redraw interval (in seconds, default 0.033))`

Then you can either call the ProgressBar or iterate over it.

```
# recommended:
for i in ProgressBar(something_that_yields, how_often_you_expect_it_to_yield):
	DoSomethingWithYourDataThatTakesSomeTime(i)

# possible, not recommended:
pb = ProgressBar(None, how_often_you_expect_to_call_it)
for i in something_you_know_pretty_well_how_long_it_should_take:
	DoSomethingWithYourDataThatTakesSomeTime(i)
```

### Unitprint
Ok, I'll admit. `unitprint` is the main feature of my library but wasn't even my idea.
Props to this go to the IT admin where I interned and implemented his idea.
I improved the concept a little (like f.ex. using a dict with the $log_1000$ / $log_1024$ values
instead of elif matching them to fixed values).

Originally, the only `unitprint` function was fixed size; if you still want it padded correctly,
add the `_block` suffix.
(so `unitprint_block` `unitprint2_block`)(note that they share their syntax with the non-padded version).

`unitprint2` is base 2, so it formats $2^18$ bytes `256.000 KiB` instead of `262.144 kB`.

The base 10 version of `unitprint`, you can specify a power, so $10^-6 m^2$ can be printed as `1.000 mm^2`.
For that, use the optional power parameter.
(Please specify the `power=n` parameter directly. It makes it WAY more readable)

In order to avoid mibibytes (miB), the `unitprint2` function ceils the value to be printed.
If you need a decimal with bytes please mail me why.
I am genuinely interested on why one would need fractional bytes/bits!
(No, bits do not count. I'd set the unit as a bit.)

#### How to use

It is as simple as `unitprint(float_to_format, symbol_if_any, power_if_any)`
or `unitprint2(positive_float_to_format, symbol_if_any, power_if_any)`

### PTimer

Yes, that one is inspired by IPythons %%timeit.
I thought it was cool and wanted to use it in scripts, not just the console.
It is an extension of the `@timed` decorator
(but I upgraded it to a class because some implementation was easier). 

Open issue: inoperable in classes, use `@timed`

FUN FACT: If you want a short summary (or long idc) every n samples xor every t seconds, 
you can call the decorator with parameters `print_rate=n` xor `redraw_interval=t`

#### How to use

```
@PTimer
def some_func(whatever):
	something = magic(whatever)
	return wizardry * np.sum(something)
```

### Namespaces

Just a container for data. Rarely useful. A dozen lines of uncommented code. Great fun.

```
n = Namespace(a=1)
n.b = "None"
n.c += len(n.b) + n.a

print(n)
```

#### How to use

Create it. Assign to it. Read from it. Delete from it. wow

You can even put namespaces (while True: into namespaces)
