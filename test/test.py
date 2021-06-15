#! /usr/bin/python3
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  06/01/2020
#-----------------------------------------------------------------------------
""" test_wbgpio
"""
import os
import sys
import cocotb
import logging
from cocotb.log import SimLog
from cocotb.result import raise_error, TestError, ReturnValue
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge, FallingEdge, ClockCycles
from cocotb.binary import BinaryValue

from cocotbext.wishbone.driver import WishboneMaster
from cocotbext.wishbone.driver import WBOp

class Newmot(object):
    """ test class for newmot SoC built with Litex
    """
    LOGLEVEL = logging.INFO

    # clock frequency is 50Mhz
    PERIOD = (20, "ns")

    CSR_BASE = 0x30000000

    PWM_ENABLE = (CSR_BASE + 0) >> 2
    PWM_WIDTH  = (CSR_BASE + 0x4) >> 2
    PWM_PERIOD = (CSR_BASE + 0x8) >> 2

    AXIS_X     = (CSR_BASE + 0x800) >> 2

    GENERATOR_AXIS_X_POSITION = (CSR_BASE + 0x1000) >> 2
    GENERATOR_AXIS_X_TARGET_POSITION = (CSR_BASE + 0x100c) >> 2
    GENERATOR_AXIS_X_START_SPEED = (CSR_BASE + 0x1010) >> 2
    GENERATOR_AXIS_X_ACCELERATION = (CSR_BASE + 0x1014) >> 2
    GENERATOR_PUSH_MOTION = (CSR_BASE + 0x1018) >> 2
    GENERATOR_HOME_DONE = (CSR_BASE + 0x101c) >> 2

    QEI_CNT = (CSR_BASE + 0x1800) >> 2
    QEI_INDEX_CNT = (CSR_BASE + 0x1804) >> 2


    def __init__(self, dut):
        if sys.version_info[0] < 3:
            raise Exception("Must be using Python 3")
        self._dut = dut
        self.log = SimLog("newmot.{}".format(self.__class__.__name__))
        self._dut._log.setLevel(self.LOGLEVEL)
        self.log.setLevel(self.LOGLEVEL)
        self.clock = Clock(self._dut.sys_clk, self.PERIOD[0], self.PERIOD[1])
        self._clock_thread = cocotb.fork(self.clock.start())

        self.wbs = WishboneMaster(dut, "wb", dut.sys_clk,
                          width=16,   # size of data bus
                          timeout=10, # in clock cycle number
                          signals_dict={"datwr":"dat_w",
                                      "datrd":"dat_r",
                                      "cyc":"cyc",
                                      "stb":"stb",
                                      "we":"we",
                                      "adr":"adr",
                                      "ack":"ack"})
    def get_dut_version_str(self):
        return "{}".format(self._dut.version)

    @cocotb.coroutine
    def reset(self):
        self._dut.sys_rst <= 1
        short_per = Timer(100, units="ns")
        yield short_per
        self._dut.sys_rst <= 1
        yield short_per
        self._dut.sys_rst <= 0
        yield short_per

dir(Newmot)

@cocotb.test()
def test_pwm(dut):
    period = 10
    newmot = Newmot(dut)
    yield newmot.reset()
    newmot.log.info("newmot reset done")
    yield Timer(1)
    assert dut.pwm == 0
    newmot.log.info("PWM value after reset OK")
    wbRes = yield newmot.wbs.send_cycle([WBOp(adr=Newmot.PWM_PERIOD), WBOp(adr=Newmot.PWM_PERIOD, dat=period), WBOp(adr=Newmot.PWM_PERIOD)])
    newmot.log.info("R, W, R to Width done")
    yield Timer(1)
    assert wbRes[0].datrd == 0
    assert wbRes[2].datrd == period
    wbRes = yield newmot.wbs.send_cycle([WBOp(Newmot.PWM_WIDTH, int(period/2)), WBOp(Newmot.PWM_ENABLE, 1)])
    newmot.log.info("W to enable done")
    yield Timer(100*Newmot.PERIOD[0], units=Newmot.PERIOD[1])


@cocotb.test()
async def test_stepgen(dut):
    target = 10
    newmot = Newmot(dut)
    await newmot.reset()
    newmot.log.info("newmot reset done")
    await Timer(1)

    await newmot.wbs.send_cycle([WBOp(Newmot.AXIS_X, 0b01 << 1),
                                 WBOp(Newmot.GENERATOR_AXIS_X_TARGET_POSITION, target),
                                 WBOp(Newmot.GENERATOR_AXIS_X_START_SPEED, 10000),
                                 WBOp(Newmot.GENERATOR_AXIS_X_ACCELERATION, 20000),
                                 WBOp(Newmot.GENERATOR_PUSH_MOTION, 1)])
    newmot.log.info(f"Pushed a motion to target position {target}")

    await Timer(1)

    done = await newmot.wbs.send_cycle([WBOp(Newmot.GENERATOR_HOME_DONE)])
    assert done[0].datrd == 0
    newmot.log.info(f"Motion being processed")

    await Timer(20, 'us') # Ideally we should wait 10 steps, but for some reason RisingEdge(dut.stepper0_step) triggers each clock cycle

    wbRes = await newmot.wbs.send_cycle([WBOp(Newmot.GENERATOR_HOME_DONE),
                                         WBOp(Newmot.GENERATOR_AXIS_X_POSITION)])
    assert wbRes[0].datrd == 0
    assert wbRes[1].datrd == target


@cocotb.test()
async def test_qei(dut):
    newmot = Newmot(dut)
    dut.qei_a <= 0
    dut.qei_b <= 0
    dut.qei_i <= 0
    await newmot.reset()
    newmot.log.info("newmot reset done")
    await Timer(1)

    newmot.log.info(f"check QEI reset state")
    wbRes = await newmot.wbs.send_cycle([WBOp(Newmot.QEI_CNT),
                                 WBOp(Newmot.QEI_INDEX_CNT)])
    assert wbRes[0].datrd == 0
    assert wbRes[1].datrd == 0

    dut.qei_a <= 0
    dut.qei_b <= 0
    dut.qei_i <= 0
    await Timer(1, 'us')
    dut.qei_a <= 1
    dut.qei_b <= 0
    dut.qei_i <= 0
    await Timer(1, 'us')
    dut.qei_a <= 1
    dut.qei_b <= 1
    dut.qei_i <= 1
    await Timer(1, 'us')
    dut.qei_a <= 0
    dut.qei_b <= 1
    dut.qei_i <= 0
    await Timer(1, 'us')
    dut.qei_a <= 0
    dut.qei_b <= 0
    dut.qei_i <= 0
    await Timer(1, 'us')

    newmot.log.info(f"check QEI reset state")
    wbRes = await newmot.wbs.send_cycle([WBOp(Newmot.QEI_CNT),
                                 WBOp(Newmot.QEI_INDEX_CNT)])
    dut.log.info(f"cnt={wbRes[0].datrd}, index_cnt={wbRes[1].datrd}")
    assert wbRes[0].datrd == 4
    assert wbRes[1].datrd == 2


    dut.qei_a <= 0
    dut.qei_b <= 0
    dut.qei_i <= 0
    await Timer(1, 'us')
    dut.qei_a <= 0
    dut.qei_b <= 1
    dut.qei_i <= 0
    await Timer(1, 'us')
    dut.qei_a <= 1
    dut.qei_b <= 1
    dut.qei_i <= 1
    await Timer(1, 'us')
    dut.qei_a <= 1
    dut.qei_b <= 0
    dut.qei_i <= 0
    await Timer(1, 'us')
    dut.qei_a <= 0
    dut.qei_b <= 0
    dut.qei_i <= 0
    await Timer(1, 'us')

    newmot.log.info(f"check QEI reset state")
    wbRes = await newmot.wbs.send_cycle([WBOp(Newmot.QEI_CNT),
                                 WBOp(Newmot.QEI_INDEX_CNT)])
    dut.log.info(f"cnt={wbRes[0].datrd}, index_cnt={wbRes[1].datrd}")
    assert wbRes[0].datrd == 0
    assert wbRes[1].datrd == 2
