"""Compare warmed call overhead, with descriptor lookup measured separately."""

import argparse
import json
import platform
from collections.abc import Callable
from statistics import median
from timeit import Timer
from typing import cast

import alternative


def raw(value: int) -> int:
    """Perform minimal work so dispatch overhead stays visible."""
    return value + 1


class Methods:
    """Expose ordinary and decorated methods with the same small workload."""

    def raw(self, value: int) -> int:
        """Return an integer through an ordinary method."""
        return value + 1

    @alternative.reference
    def instance(self, value: int) -> int:
        """Return an integer through an instance alternative."""
        return value + 1

    @alternative.reference
    @classmethod
    def factory(cls, value: int) -> int:
        """Return an integer through a class alternative."""
        return value + 1

    @alternative.reference
    @staticmethod
    def static(value: int) -> int:
        """Return an integer through a static alternative."""
        return value + 1


def build_cases() -> dict[str, Timer]:
    """Freeze and warm every implementation before constructing timers."""
    implicit = alternative.reference(raw)
    explicit = alternative.reference(raw)
    implementation = explicit.add(raw, default=True)
    instance = Methods()
    calls: dict[str, Callable[[int], int]] = {
        "raw_function": raw,
        "implicit_default": implicit,
        "explicit_default": explicit,
        "implementation": implementation,
        "resolved_callable": cast(Callable[[int], int], explicit.callable),
        "raw_bound_method": instance.raw,
        "bound_instance": instance.instance,
        "bound_class": Methods.factory,
        "bound_static": instance.static,
    }
    for target in calls.values():
        assert target(1) == 2
    timers = {
        name: Timer("target(1)", globals={"target": target})
        for name, target in calls.items()
    }
    for name in ("raw", "instance", "factory", "static"):
        timers[name + "_lookup"] = Timer(
            f"receiver.{name}(1)", globals={"receiver": instance}
        )
    return timers


def positive_int(value: str) -> int:
    """Accept positive measurement counts."""
    result = int(value)
    if result <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return result


def main() -> None:
    """Report minimum and median nanoseconds per call with environment metadata."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--number", type=positive_int, default=100_000)
    parser.add_argument("--repeat", type=positive_int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    measurements = {}
    for name, timer in build_cases().items():
        seconds = timer.repeat(number=args.number, repeat=args.repeat)
        measurements[name] = {
            "minimum_ns": min(seconds) * 1e9 / args.number,
            "median_ns": median(seconds) * 1e9 / args.number,
        }
    report = {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "number": args.number,
        "repeat": args.repeat,
        "measurements": measurements,
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"{report['implementation']} {report['python']}; {report['platform']}")
        print(
            f"{args.repeat} repeats of {args.number} warmed calls; timeit GC disabled"
        )
        print(f"{'case':24} {'minimum ns':>12} {'median ns':>12}")
        for name, values in measurements.items():
            print(f"{name:24} {values['minimum_ns']:12.1f} {values['median_ns']:12.1f}")


if __name__ == "__main__":
    main()
