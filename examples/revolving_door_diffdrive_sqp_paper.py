# This file is part of OMG-tools.
#
# OMG-tools -- Optimal Motion Generation-tools
# Copyright (C) 2016 Ruben Van Parys & Tim Mercy, KU Leuven.
# All rights reserved.
#
# OMG-tools is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
import os, sys
sys.path.insert(0, os.getcwd()+'/..')
from omgtools import *
import numpy as np

# create vehicle
vehicle = Dubins(bounds={'vmax': 0.7, 'wmin': -30., 'wmax': 30.})
vehicle.define_knots(knot_intervals=6)
vehicle.set_initial_conditions([0., -2.0, np.pi/2])
vehicle.set_terminal_conditions([-1.5, 2.0, np.pi/2])

# create environment
environment = Environment(room={'shape': Square(5.)})
beam1 = Beam(width=2.2, height=0.2)
environment.add_obstacle(Obstacle({'position': [-2., 0.]}, shape=beam1))
environment.add_obstacle(Obstacle({'position': [2., 0.]}, shape=beam1))

beam2 = Beam(width=1.4, height=0.2)
horizon_time = 15.
omega = 0.1*1.*(2*np.pi/horizon_time)
velocity = [0., 0.]
# velocity = [0., -0.2] # crazy revolving door
environment.add_obstacle(Obstacle({'position': [0., 0.], 'velocity': velocity,
    'orientation': 0.+np.pi/4., 'angular_velocity': omega},
     shape=beam2, simulation={}, options={'horizon_time': horizon_time}))
environment.add_obstacle(Obstacle({'position': [0., 0.], 'velocity': velocity,
    'orientation': 0.5*np.pi+np.pi/4., 'angular_velocity': omega},
    shape=beam2, simulation={}, options={'horizon_time': horizon_time}))

# create a point-to-point problem
solver = 'ipopt'
if solver is 'ipopt':
    options = {}
    options={'solver': solver, 'horizon_time': horizon_time, 'hard_term_con': True}
    problem0 = Point2point(vehicle, environment, options, freeT=False)
    problem0.set_options(
        {'solver_options': {'ipopt': {'ipopt.linear_solver': 'ma57',
        							  'ipopt.hessian_approximation': 'limited-memory',
        							  'ipopt.warm_start_mult_bound_push': 1e-6,
                                      'ipopt.tol':1e-3}}}) 
problem0.init()

#####ipopt

method = 'blocksqp'

if method == 'ipopt':
    # create simulator
    simulator = Simulator(problem0, sample_time=0.01, update_time=0.1)
    vehicle.plot('input', knots=True)
    problem0.plot('scene', view=[20, -80])
    simulator.run()

else:
#####blocksqp
    # create simulator
    simulator = Simulator(problem0, sample_time=0.01, update_time=0.1)
    simulator.run_once(simulate=False)

    options={}
    options={'solver': solver, 'horizon_time': horizon_time, 'hard_term_con': True}
    # options['codegen'] = {'build': 'shared', 'flags': '-O2'} # just-in-time compilation
    problem = Point2point(vehicle, environment, options, freeT=False)
    problem.set_options({'solver': 'blocksqp', 'solver_options': {'blocksqp': {'verbose':True, 'warmstart': True, 'qp_init' : False,
                         'print_header': False, 'opttol':1e-3, 'max_iter':20,
                         'block_hess':1, 'hess_update':2, 'hess_lim_mem':0}}})  #1
                         # 'block_hess':1, 'hess_update':2, 'hess_lim_mem':1 }}}) #2
                         # 'block_hess':1, 'hess_update':1, 'fallback_update':2, 'hess_lim_mem':0 }}}) #3
                         # 'block_hess':1, 'hess_update':1, 'fallback_update':2, 'hess_lim_mem':1 }}}) #4
                         # 'block_hess':0, 'hess_update':2, 'hess_lim_mem':0 }}}) #5
                         # 'block_hess':0, 'hess_update':1, 'fallback_update':2, 'hess_lim_mem':0 }}}) #6

    # options['codegen'] = {'build': 'jit', 'flags': '-O2'} # just-in-time compilation

    # problem.set_options({'hard_term_con': True, 'horizon_time': 12})
    vehicle.problem = problem
    # problem.init()
    simulator = Simulator(problem, sample_time=0.01, update_time=0.1, options={'debugging':False})
    problem.father._var_result = problem0.father._var_result
    problem.father._dual_var_result = problem0.father._dual_var_result

    problem.plot('scene')
    vehicle.plot('input', knots=True, labels=['v_x (m/s)', 'v_y (m/s)'])

    # run it!
    simulator.run(init_reset=False)