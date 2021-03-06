"""Uses force control to compensate for gravity.  The arm will
hold its position while maintaining compliance.  """

import numpy as np
import traceback
import timeit

import abr_jaco2
from abr_control.controllers import Floating

# initialize our robot config
robot_config = abr_jaco2.Config(
    use_cython=True, hand_attached=True)
ctrlr = Floating(robot_config)
# run controller once to generate functions / take care of overhead
# outside of the main loop, because force mode auto-exits after 200ms
zeros = np.zeros(robot_config.N_JOINTS)
ctrlr.generate(zeros, zeros)

# create our interface for the jaco2
interface = abr_jaco2.Interface(robot_config)

time_track = []

# connect to the jaco
interface.connect()
interface.init_position_mode()

# Move to home position
interface.send_target_angles(robot_config.INIT_TORQUE_POSITION)
try:
    print('Running loop speed test for the next 10 seconds...')
    print('During this time the arm will be in float mode and'
           + ' should not move unless it is perturbed')
    interface.init_force_mode()
    run_time = 0
    while run_time<10:
        start = timeit.default_timer()
        feedback = interface.get_feedback()

        u = ctrlr.generate(q=feedback['q'], dq=feedback['dq'])
        interface.send_forces(np.array(u, dtype='float32'))

        # track data
        loop_time = timeit.default_timer() - start
        run_time += loop_time
        time_track.append(np.copy(loop_time))


except Exception as e:
    print(traceback.format_exc())

finally:
    interface.init_position_mode()
    interface.send_target_angles(robot_config.INIT_TORQUE_POSITION)
    interface.disconnect()

    time_track = np.array(time_track)
    avg_loop = np.mean(time_track)
    avg_loop_ms = avg_loop*1000
    if avg_loop > 0.005:
        print('W A R N I N G: You may run into performance issues with your'
                + ' current loop speed of %fms'%avg_loop_ms)
        print('It is not recommended to use force control with a loop speed'
                + ' > 5ms')
    elif avg_loop > 0.0035:
        print('Your average loop speed is %fms' % avg_loop_ms)
        print('For best performance your loop speed should be ~3ms, you may'
                + ' notice minimal loss in performance')
    else:
        print('Your average loop speed is %fms'%avg_loop_ms
                +' and is within the recommended limit')
    # plot joint angles throughout trial
    import matplotlib
    matplotlib.use("TKAgg")
    import matplotlib.pyplot as plt
    plt.figure()
    plt.title('Loop Speed')
    plt.ylabel('time [sec]')
    plt.plot(time_track, label='Average: %fms' %avg_loop_ms)
    plt.legend()
    plt.show()
