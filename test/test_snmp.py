import subprocess
from time import sleep
from typing import Union
from pathlib import Path

import pytest
from run_iocsh import IOC
from epics import PV


TEST_DIR = Path(__file__).absolute().parent


@pytest.fixture(scope="session")  # use the same IOC for all tests
def connected_ioc():
    simulator_address = "127.0.0.1:1024"
    sim_proc = subprocess.Popen(
        [
            "snmpsim-command-responder",
            f"--data-dir={TEST_DIR / 'data'}",
            f"--agent-udpv4-endpoint={simulator_address}",
        ]
    )
    sleep(2)

    cmd = TEST_DIR / "cmds" / "pv_test.cmd"
    ioc = IOC(cmd)

    yield ioc

    sim_proc.terminate()


class TestIOCConnection:

    pv_wait_in_seconds = 1
    sleep_in_seconds = 10

    @pytest.mark.parametrize("num_runs", range(5))
    def test_connect(self, connected_ioc: IOC, num_runs) -> None:

        with connected_ioc:
            sleep(self.sleep_in_seconds)
            assert connected_ioc.is_running()

    @pytest.mark.parametrize("num_runs", range(5))
    def test_disconnect(self, connected_ioc: IOC, num_runs) -> None:

        with connected_ioc:
            sleep(self.sleep_in_seconds)
        assert not connected_ioc.is_running()


class TestReadWrite:

    pv_wait_in_seconds = 1
    sleep_in_seconds = 10

    @pytest.mark.parametrize(
        "pv_name_read, expected_val",
        [
            ("TestSnmp:TestString-R", "This is a test string"),
            ("TestSnmp:TestInteger-R", 255),
            ("TestSnmp:TestEnum-R", 10),
            ("TestSnmp:TestGauge32-R", 123456),
        ],
    )
    def test_read_variable(
        self,
        connected_ioc: IOC,
        pv_name_read: str,
        expected_val: Union[str, int],
    ) -> None:

        with connected_ioc:
            sleep(self.sleep_in_seconds)

            # Read back via input PV
            pv_read = PV(pv_name_read)
            res = pv_read.get(use_monitor=False, timeout=self.pv_wait_in_seconds)

        assert res == expected_val

    @pytest.mark.parametrize(
        "pv_name_read, pv_name_write, write_val",
        [
            (
                "TestSnmp:TestString-R",
                "TestSnmp:TestString",
                "Replace with another string",
            ),
            ("TestSnmp:TestInteger-R", "TestSnmp:TestInteger", 123),
            ("TestSnmp:TestEnum-R", "TestSnmp:TestEnum", 15),
            ("TestSnmp:TestGauge32-R", "TestSnmp:TestGauge32", 654321),
        ],
    )
    def test_write_variable(
        self,
        connected_ioc: IOC,
        pv_name_read: str,
        pv_name_write: str,
        write_val: Union[str, int],
    ) -> None:

        with connected_ioc:
            sleep(self.sleep_in_seconds)

            # Read back via input PV
            pv_read = PV(pv_name_read)
            pv_write = PV(pv_name_write)

            pv_write.put(write_val, timeout=self.pv_wait_in_seconds)

            sleep(self.pv_wait_in_seconds)

            res = pv_read.get(use_monitor=False, timeout=self.pv_wait_in_seconds)

        assert res == write_val

    @pytest.mark.parametrize(
        "pv_name_read, pv_name_write, write_val",
        [
            ("TestSnmp:TestInteger-R", "TestSnmp:TestInteger", -5.8),
            ("TestSnmp:TestInteger-R", "TestSnmp:TestInteger", 9e18),
            ("TestSnmp:TestEnum-R", "TestSnmp:TestEnum", -3.5),
            ("TestSnmp:TestEnum-R", "TestSnmp:TestEnum", 9e18),
            ("TestSnmp:TestGauge32-R", "TestSnmp:TestGauge32", -65.4321),
            ("TestSnmp:TestGauge32-R", "TestSnmp:TestGauge32", 9e18),
        ],
    )
    def test_invalid_write(
        self,
        connected_ioc: IOC,
        pv_name_read: str,
        pv_name_write: str,
        write_val: Union[int, float],
    ) -> None:

        with connected_ioc:
            sleep(self.sleep_in_seconds)

            pv_read = PV(pv_name_read)
            pv_write = PV(pv_name_write)

            pv_write.put(write_val, timeout=self.pv_wait_in_seconds)

            assert not pv_write.put_complete

            sleep(self.pv_wait_in_seconds)

            res = pv_read.get(use_monitor=False, timeout=self.pv_wait_in_seconds)

        assert res != write_val

    def test_read_counter(self, connected_ioc: IOC):

        pv_read = PV("TestSnmp:TestCounter-R")

        with connected_ioc:
            sleep(self.sleep_in_seconds)

            number_of_samples_to_capture = 5
            time_increment_in_seconds = 5

            samples = []
            for _ in range(number_of_samples_to_capture):
                read_value = int(pv_read.get(timeout=self.pv_wait_in_seconds))
                samples.append(read_value)
                sleep(time_increment_in_seconds)

        tolerance = 5
        for first, second in zip(samples, samples[1:]):
            assert abs(time_increment_in_seconds - (second - first)) <= tolerance
