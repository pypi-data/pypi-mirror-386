"""STH specific test code

Use this test code in addition to the one for the sensor node:

    icotest run -k 'sensor_node or sth'

"""

# -- Imports ------------------------------------------------------------------

from logging import getLogger

from icotronic.can import STH, StreamingConfiguration
from icotronic.measurement.constants import ADC_MAX_VALUE
from icotronic.measurement import convert_raw_to_g, ratio_noise_max

from icotest.config import settings
from icotest.test.support.node import check_write_read_eeprom_close
from icotest.test.support.sensor_node import read_streaming_data
from icotest.test.support.sth import read_self_test_voltages

# -- Functions ----------------------------------------------------------------


async def test_acceleration_sensor_self_test(sth: STH):
    """Use the self test of a acceleration sensor to check for problems"""

    voltage_diff_abs, voltage_diff_before_after = (
        await read_self_test_voltages(sth)
    )

    sensor = settings.acceleration_sensor()

    voltage_diff_expected = sensor.self_test.voltage.difference
    voltage_diff_tolerance = sensor.self_test.voltage.tolerance

    voltage_diff_minimum = voltage_diff_expected - voltage_diff_tolerance
    voltage_diff_maximum = voltage_diff_expected + voltage_diff_tolerance

    assert voltage_diff_before_after <= voltage_diff_tolerance, (
        "Measured voltage difference between voltage before and after "
        f"test {voltage_diff_before_after:.2f} mV is larger than "
        f"tolerance of {voltage_diff_tolerance:.2f} mV"
    )
    possible_failure_reason = (
        "\n\nPossible Reason:\n\n• Acceleration sensor config value "
        f"“{settings.sth.acceleration_sensor.sensor}” is incorrect"
    )

    assert voltage_diff_minimum <= voltage_diff_abs, (
        f"Measured voltage difference of {voltage_diff_abs:.2f} mV is "
        "lower than expected minimum voltage difference of "
        f"{voltage_diff_minimum:.2f} mV{possible_failure_reason}"
    )
    assert voltage_diff_abs <= voltage_diff_maximum, (
        f"Measured voltage difference of {voltage_diff_abs:.2f} mV is "
        "greater than expected minimum voltage difference of "
        f"{voltage_diff_maximum:.2f} mV{possible_failure_reason}"
    )


async def test_acceleration_single_value(sth: STH):
    """Test stationary acceleration value"""

    stream_data = await sth.get_streaming_data_single()
    sensor = settings.acceleration_sensor()
    acceleration = convert_raw_to_g(
        stream_data.values[0], sensor.acceleration.maximum
    )

    logger = getLogger(__file__)
    logger.info("Measured acceleration value: %.2f g", acceleration)

    # We expect a stationary acceleration between -g₀ and g₀ (g₀ = 9.807 m/s²)
    expected_acceleration = 0
    tolerance_acceleration = sensor.acceleration.tolerance
    expected_minimum_acceleration = (
        expected_acceleration - tolerance_acceleration
    )
    expected_maximum_acceleration = (
        expected_acceleration + tolerance_acceleration
    )

    assert expected_minimum_acceleration <= acceleration, (
        f"Measured acceleration {acceleration:.3f} g is lower "
        "than expected minimum acceleration "
        f"{expected_minimum_acceleration:.3f} g"
    )
    assert acceleration <= expected_maximum_acceleration, (
        f"Measured acceleration {acceleration:.3f} g is greater "
        "than expected maximum acceleration "
        f"{expected_maximum_acceleration:.3f} g"
    )


async def test_acceleration_noise(sth: STH):
    """Test ratio of noise to maximal possible measurement value"""

    acceleration = await read_streaming_data(
        sth, StreamingConfiguration(first=True), length=10000
    )

    ratio_noise_maximum = ratio_noise_max(acceleration)
    sensor = settings.acceleration_sensor()
    maximum_ratio_allowed = sensor.acceleration.ratio_noise_to_max_value

    assert ratio_noise_maximum <= maximum_ratio_allowed, (
        "The ratio noise to possible maximum measured value of "
        f"{ratio_noise_maximum} dB is higher than the maximum allowed level "
        f"of {maximum_ratio_allowed} dB"
    )


async def test_eeprom(sth: STH):
    """Test if reading and writing STH EEPROM data works"""

    sensor = settings.acceleration_sensor()
    acceleration_max = sensor.acceleration.maximum

    acceleration_slope = acceleration_max / ADC_MAX_VALUE
    acceleration_offset = -(acceleration_max / 2)

    for axis in ("x", "y", "z"):
        await check_write_read_eeprom_close(
            sth, f"{axis} axis acceleration slope", acceleration_slope
        )
        await check_write_read_eeprom_close(
            sth, f"{axis} axis acceleration offset", acceleration_offset
        )
