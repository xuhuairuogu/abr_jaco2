import numpy as np

from .interface_files import jaco2_rs485
from abr_control.interfaces import interface


class interface(interface.interface):
    """ Interface class for the Jaco2 Kinova arm.
    Handles the overhead of interacting with the cython code,
    conforms the functions to the abr_control interface system.
    """

    def __init__(self, robot_config):
        super(interface, self).__init__(robot_config)
        self.jaco2 = jaco2_rs485.pyJaco2()

    def connect(self):
        """ All initial setup
        """
        self.jaco2.Connect()

    def disconnect(self):
        """ Any socket closing etc that must be done
        when done with the arm
        """
        self.jaco2.Disconnect()

    def get_feedback(self):
        """ Returns a dictionary of relevant feedback to the
        controller. At very least this contains q, dq.
        """
        # convert from degrees from the Jaco into radians
        feedback = self.jaco2.GetFeedback()
        feedback['q'] = (np.array(feedback['q']) * np.pi / 180.0) % (2 * np.pi)
        feedback['dq'] = np.array(feedback['dq']) * np.pi / 180.0
        return feedback

    def get_position(self):
        """ Returns the last set of joint angles and velocities
        read in from the arm as a dictionary, with keys 'q' and 'dq'
        """
        # NOTE: this does the same thing as GetFeedback
        # TODO: set this up to send a message to query current position
        # convert from degrees from the Jaco into radians
        return self.get_feedback()

    def get_torque_load(self):
        """ Returns the torque at each joint
        """
        return self.jaco2.GetTorqueLoad()

    def init_force_mode(self):
        """ Changes the arm to torque control mode
        """
        self.jaco2.InitForceMode()

    def init_position_mode(self):
        """ Changes the arm into position control mode, where
        target joint angles can be provided, and the on-board PD
        controller will move the arm.
        """
        self.jaco2.InitPositionMode()

    def open_hand(self, open):
        """ Send true to open hand, false to close, moves in
        increments for each function call
        """
        self.jaco2.ApplyQHand(open)

    # TODO: change name to send_forces in C++ code
    def send_forces(self, u):
        """ Applies the set of torques u to the arm.

        NOTE: if a torque is not applied every 200ms then
        the arm reverts back to position control and the
        InitForceMode function must be called again.
        """
        self.jaco2.ApplyU(u)

    # TODO: change name to send_target_angles in C++
    def send_target_angles(self, q):
        """ Moves the arm to the specified joint angles using
        the on-board PD controller.

        q np.array: the target joint angles (radians)
        """
        # convert from radians into degrees the Jaco expects
        q = np.array(q) * 180.0 / np.pi
        self.jaco2.ApplyQ(q)