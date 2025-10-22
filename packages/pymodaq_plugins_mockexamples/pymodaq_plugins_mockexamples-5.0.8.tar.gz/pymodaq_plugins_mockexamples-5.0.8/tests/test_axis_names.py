# -*- coding: utf-8 -*-
"""
Created the 04/11/2023

@author: Sebastien Weber
"""


from pymodaq_plugins_mockexamples.daq_move_plugins.daq_move_MockNamedAxes import DAQ_Move_MockNamedAxes

import pytest
from pytest import fixture, approx


@fixture
def init_qt(qtbot):
    return qtbot


def test_stage_names(init_qt):
    qtbot = init_qt
    axis_names = DAQ_Move_MockNamedAxes._axis_names.copy()
    prog = DAQ_Move_MockNamedAxes()

    prog.ini_stage()
    assert axis_names == prog.axis_names
    name_axis = 'anotheraxis'
    index_axis = 45
    axis_names.update({name_axis: index_axis})

    prog.axis_names = axis_names
    assert prog.axis_names == axis_names

    assert name_axis in prog.axis_names
    prog.axis_name = name_axis
    assert name_axis == prog.axis_name
    assert prog.settings.child('multiaxes', 'axis').value() == index_axis
    assert prog.axis_value == index_axis
