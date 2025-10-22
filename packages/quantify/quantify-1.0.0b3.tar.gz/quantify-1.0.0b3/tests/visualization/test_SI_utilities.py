# pylint: disable=invalid-name # disabled because of capital SI in module name
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import warnings

import matplotlib.pyplot as plt
import numpy as np
import uncertainties
from lmfit.parameter import Parameter

from quantify.visualization.SI_utilities import (
    SafeFormatter,
    SI_prefix_and_scale_factor,
    SI_val_to_msg_str,
    adjust_axeslabels_SI,
    format_value_string,
    set_xlabel,
    set_ylabel,
    value_precision,
)


def test_non_si() -> None:
    unit = "arb.unit."
    scale_factor, post_unit = SI_prefix_and_scale_factor(val=5, unit=unit)
    assert scale_factor == 1
    assert unit == post_unit


def test_si_scale_factors() -> None:
    unit = "V"
    scale_factor, post_unit = SI_prefix_and_scale_factor(val=5, unit=unit)
    assert scale_factor == 1
    assert unit == post_unit

    scale_factor, post_unit = SI_prefix_and_scale_factor(val=5000, unit=unit)
    assert scale_factor, 1 == 1000  # noqa: PLR0133
    assert "k" + unit == post_unit

    scale_factor, post_unit = SI_prefix_and_scale_factor(val=0.05, unit=unit)
    assert scale_factor == 1000
    assert "m" + unit == post_unit

    unit = "ns"
    scale_factor, post_unit = SI_prefix_and_scale_factor(val=5000.4, unit=unit)
    assert scale_factor == 1e-3
    assert post_unit == "μs"

    unit = "Gunknown"
    scale_factor, post_unit = SI_prefix_and_scale_factor(val=126, unit=unit)
    assert scale_factor == 1
    assert post_unit == "Gunknown"

    unit = "m$\\Phi_0$"
    scale_factor, post_unit = SI_prefix_and_scale_factor(val=1000.0, unit=unit)
    assert scale_factor == 1e-3
    assert post_unit == "$\\Phi_0$"

    unit = None
    scale_factor, post_unit = SI_prefix_and_scale_factor(val=5000.4, unit=unit)
    assert scale_factor == 1
    assert not post_unit

    unit = "s"
    scale_factor, post_unit = SI_prefix_and_scale_factor(val=150, unit=unit)
    assert scale_factor == 1 / 60
    assert post_unit == "min"

    unit = "s"
    scale_factor, post_unit = SI_prefix_and_scale_factor(val=10000, unit=unit)
    assert scale_factor == 1 / 3600
    assert post_unit == "hrs"


def test_label_scaling() -> None:
    """
    This test creates a dummy plot and checks if the tick labels are
    rescaled correctly
    """
    _, ax = plt.subplots()
    x = np.linspace(-6, 6, 101) + 60000
    y = np.cos(x)
    ax.plot(x * 1000, y / 1e5)

    set_xlabel("Distance", "m", axis=ax)
    set_ylabel("Amplitude", "V")

    xlab = ax.get_xlabel()
    ylab = ax.get_ylabel()
    xticklabs = [lab.get_text() for lab in ax.get_xticklabels()]
    yticklabs = [lab.get_text() for lab in ax.get_yticklabels()]
    assert xlab == "Distance [km]"
    assert ylab == "Amplitude [μV]"
    assert xticklabs == ["-8", "-6", "-4", "-2", "0", "2", "4", "6", "8"]
    assert yticklabs == [
        "-12.5",
        "-10",
        "-7.5",
        "-5",
        "-2.5",
        "0",
        "2.5",
        "5",
        "7.5",
        "10",
        "12.5",
    ]


def test_set_xlabel_auto_scale() -> None:
    """
    This test creates a dummy plot and checks if the tick labels are
    rescaled correctly
    """
    _, ax = plt.subplots()
    x = np.linspace(-6, 6, 101)
    y = np.cos(x)
    ax.plot(x * 10_000, y / 1e3)
    set_xlabel("Distance", unit="m", auto_scale=False)
    assert ax.get_xlabel() == "Distance [m]"
    set_xlabel("Distance", unit="m")
    assert ax.get_xlabel() == "Distance [km]"

    set_ylabel("Amplitude", unit="V", auto_scale=False)
    assert ax.get_ylabel() == "Amplitude [V]"
    set_ylabel("Amplitude", unit="V")
    assert ax.get_ylabel() == "Amplitude [mV]"


def test_adjust_adjust_axeslabels_SI() -> None:  # noqa: N802
    """
    This test creates a dummy plot and checks if the tick labels are
    rescaled correctly
    """
    _, ax = plt.subplots()
    x = np.linspace(-6, 6, 101)
    y = np.cos(x)
    ax.plot(x * 1000, y / 1e5)
    ax.set_xlabel("Distance [m]")
    ax.set_ylabel("Amplitude [V]")
    adjust_axeslabels_SI(ax)

    xlab = ax.get_xlabel()
    ylab = ax.get_ylabel()
    assert xlab == "Distance [km]"
    assert ylab == "Amplitude [μV]"


def test_adjust_adjust_axeslabels_SI_no_unit() -> None:  # noqa: N802
    """
    This test creates a dummy plot and checks if the tick labels are
    rescaled correctly
    """
    _, ax = plt.subplots()
    x = np.linspace(-6, 6, 101)
    y = np.cos(x)
    ax.plot(x * 1000, y / 1e5)
    ax.set_xlabel("Distance")
    ax.set_ylabel("Amplitude")
    adjust_axeslabels_SI(ax)

    xlab = ax.get_xlabel()
    ylab = ax.get_ylabel()
    assert xlab == "Distance"
    assert ylab == "Amplitude"


def test_si_val_to_msg_str() -> None:
    val, unit = SI_val_to_msg_str(1030, "m")
    assert val == str(1.03)
    assert unit == "km"


BASE_STR = "my_test_values_{:.2f}_{:.3f}"
fmt = SafeFormatter()


def test_safe_formatter() -> None:
    fmt_string = fmt.format(BASE_STR, 4, 4.32497)
    assert fmt_string == "my_test_values_4.00_4.325"


def test_safe_formatter_missing() -> None:
    fmt_string = fmt.format(BASE_STR, 4, None)
    assert fmt_string == "my_test_values_4.00_~~"
    fmt_custom = SafeFormatter(missing="?")
    fmt_string = fmt_custom.format(BASE_STR, 4, None)
    assert fmt_string == "my_test_values_4.00_?"


def test_safe_formatter_bad_format() -> None:
    fmt_string = fmt.format(BASE_STR, 4, "myvalue")
    assert fmt_string == "my_test_values_4.00_!!"

    fmt_custom = SafeFormatter(bad_fmt="!")
    fmt_string = fmt_custom.format(BASE_STR, 4, "myvalue")
    assert fmt_string == "my_test_values_4.00_!"


def test_save_formatter_named_args() -> None:
    plot_title = fmt.format(
        "{measurement}\n{timestamp}", timestamp="190101_001122", measurement="test"
    )
    assert plot_title == "test\n190101_001122"


def test_format_value_string() -> None:
    """
    If no stderr is given, display to 5 significant figures. Otherwise, use
    a precision one order of magnitude more precise
    than the stderr magnitude and display the stderr itself to 2 significant figures.
    """
    tau = Parameter("tau", value=5123456.123456)
    formatted_string = format_value_string("tau", tau)
    assert formatted_string == r"tau: 5.1235e+06 "

    tau.stderr = 3.1456
    formatted_string = format_value_string("tau", tau)
    assert formatted_string == r"tau: 5123456.1$\pm$3.1 "

    tau.stderr = 0
    formatted_string = format_value_string("tau", tau)
    assert formatted_string == r"tau: 5.1235e+06$\pm$0.0 "

    tau.stderr = 31456
    formatted_string = format_value_string("tau", tau)
    assert formatted_string == r"tau: 5.123e+06$\pm$3.1e+04 "

    tau = Parameter("tau", value=0.0000123456)
    formatted_string = format_value_string("tau", tau)
    assert formatted_string == r"tau: 1.2346e-05 "

    tau.stderr = 0.0000031456
    formatted_string = format_value_string("tau", tau)
    assert formatted_string == r"tau: 1.23e-05$\pm$3.1e-06 "

    tau = Parameter("tau", value=5.123456)
    formatted_string = format_value_string("tau", tau)
    assert formatted_string == r"tau: 5.1235 "

    tau.stderr = 0.03
    formatted_string = format_value_string("tau", tau)
    assert formatted_string == r"tau: 5.123$\pm$0.030 "

    tau = Parameter("tau", value=37608)
    tau.stderr = 933
    formatted_string = format_value_string("tau", tau)
    assert formatted_string == r"tau: 3.761e+04$\pm$9.3e+02 "

    tau = Parameter("tau", value=7767)
    tau.stderr = 36
    formatted_string = format_value_string("tau", tau)
    assert formatted_string == r"tau: 7767$\pm$36 "


def test_format_value_string_unit_aware() -> None:
    """
    If no stderr is given, display to 5 significant figures in the appropriate units.
    Otherwise, the stderr use a precision one order of magnitude more precise than the
    stderr magnitude and display the stderr itself to two significant figures in
    standard index notation in the same units as the value.
    """
    formatted_string = format_value_string("tau", 5.123456e-6, unit="s")
    assert formatted_string == r"tau: 5.1235 μs"

    tau = Parameter("tau", value=5.123456e-6)
    formatted_string = format_value_string("tau", tau, unit="s")
    assert formatted_string == r"tau: 5.1235 μs"

    tau.stderr = 0.03e-6
    formatted_string = format_value_string("tau", tau, unit="s")
    assert formatted_string == r"tau: 5.123$\pm$0.030 μs"

    tau = Parameter("tau", value=5123456.123456)
    formatted_string = format_value_string("tau", tau, unit="Hz")
    assert formatted_string == r"tau: 5.1235 MHz"

    tau = Parameter("tau", value=5123456.123456)
    formatted_string = format_value_string("tau", tau, unit="SI_PREFIX_ONLY")
    assert formatted_string == r"tau: 5.1235 M"

    tau.stderr = 3.1234
    formatted_string = format_value_string("tau", tau, unit="Hz")
    assert formatted_string == r"tau: 5.1234561$\pm$3.1e-06 MHz"

    tau = Parameter("tau", value=5123.456)
    tau.stderr = 10
    formatted_string = format_value_string("tau", tau)
    assert formatted_string == r"tau: 5123$\pm$10 "


def test_value_precision() -> None:
    """
    The precision should be 5 significant figures if there is no stderr.
    Otherwise the precision should be one order of magnitude  more precise than
    the stderr magnitude (and include trailing zeros)
    """
    val = 5.123456

    format_specifier = value_precision(val)
    assert format_specifier == ("{:.5g}", "{:.1f}")

    format_specifier = value_precision(val, stderr=0.31)
    assert format_specifier == ("{:#.3g}", "{:#.2g}")

    format_specifier = value_precision(930, stderr=31)
    assert format_specifier == ("{:.0f}", "{:.0f}")

    format_specifier = value_precision(930, stderr=float("nan"))
    assert format_specifier == ("{:.5g}", "{:.1f}")


def test_value_precision_raises_no_warnings():
    # There was a warning that was raised due to a log10(0) line
    # here we test that this does not raise a warning
    with warnings.catch_warnings():
        # we filter for warnings with the word error in them.
        # if any of them is caught, this test will fail.
        warnings.simplefilter("error")
        _ = value_precision(0, stderr=0)
        _ = value_precision(1, stderr=0)
        _ = value_precision(0, stderr=5)


def test_format_value_ufloat() -> None:
    tau = uncertainties.ufloat(2.0, 0.1)
    formatted_string = format_value_string("tau", tau)
    assert formatted_string == r"tau: 2.00$\pm$0.10 "

    tau = uncertainties.ufloat(0.0, np.nan)
    formatted_string = format_value_string("tau", tau)
    assert formatted_string == r"tau: 0 "
