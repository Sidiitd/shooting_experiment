'''   Header
@file:          PR2_arm_kinematics.py
@brief:    	    Contains specific functions that define all geometric and kinematic parameters for PR2 robot arm

@author:        Nima Ramezani Taghiabadi
                PhD Researcher
                Faculty of Engineering and Information Technology
                University of Technology Sydney (UTS)
                Broadway, Ultimo, NSW 2007, Australia
                Room No.: CB10.03.512
                Phone:    02 9514 4621
                Mobile:   04 5027 4611
                Email(1): Nima.RamezaniTaghiabadi@student.uts.edu.au 
                Email(2): nima.ramezani@gmail.com
                Email(3): nima_ramezani@yahoo.com
                Email(4): ramezanitn@alum.sharif.edu
@version:	    3.0
Last Revision:  12 September 2014

Changes from ver 2.0:
    the class is now supported by an instance of class Inverse_Kinematics() from package inverse_kinematics.py
    This class is for numeric(velocity based IK) and contains the Geometric, Analytic and Error Jacobians.
    The instance is called pr2_arm_ik and becomes a property of the main class PR2_ARM() and is always synced with the configuration.       
    This property is usded to compute joint velocities for trajectory projection.
    function project_to_js() now uses velocity-based ik to find an approximation to the joint values, then 
    these approximations are corrected using IK_config() function that implements an analytic(position-based) IK.
    The phi(redundant parameter) is extracted from joint approximations.
    previous function project_to_js() is now changed name to project_to_js_analytic()  
'''

import copy, time, math
import numpy as np
import packages.nima.mathematics.general as gen
from interval import interval, inf, imath
from sets import Set


'''
The most convenient way to install "pyinterval" library is by means of easy_install:
sudo easy_install pyinterval
Alternatively, it is possible to download the sources from PyPI and invoking
python setup.py install
from sets import Set
Please refer to:
http://pyinterval.googlecode.com/svn-history/r25/trunk/html/index.html
'''
import packages.nima.robotics.kinematics.kinematicpy.general as genkin
import packages.nima.robotics.kinematics.kinematicpy.inverse_kinematics as iklib
import packages.nima.robotics.kinematics.kinematicpy.manipulator_library as maniplib
import packages.nima.robotics.kinematics.joint_space.configuration as configlib
import packages.nima.robotics.kinematics.task_space.trajectory as trajlib
import packages.nima.robotics.kinematics.joint_space.trajectory as jtrajlib
import packages.nima.mathematics.general as gen
import packages.nima.mathematics.trigonometry as trig
import packages.nima.mathematics.vectors_and_matrices as vecmat

drc        = math.pi/180.00
default_ql = drc*np.array([-130.0, 70.0 , -180.0,   0.0, -180.0,   0.0, -180.0])
default_qh = drc*np.array([  40.0, 170.0,   44.0, 130.0,  180.0, 130.0,  180.0])
default_W  = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

class PR2_ARM_Configuration():

    def joint_in_range(self,i, qi):
        '''
        returns True if the given joint angle qi is in feasible range for the i-th joint (within the specified joint limits for that joint)
        '''
        qi = trig.angle_standard_range(qi) 
        if abs(qi - self.ql[i]) < gen.epsilon:
            qi = self.ql[i]
        if abs(qi - self.qh[i]) < gen.epsilon:
            qi = self.qh[i]

        return ((qi <= self.qh[i]) and (qi >= self.ql[i]))
    
    def all_joints_in_range(self, qd):
        '''
        Then, if The given joints "qd" are out of the range specified by properties: ql and qh, returns False, otherwise returns True  
        '''
        flag = True
        for i in range(0, 7):
            if not gen.equal(self.w[i], 0.0):
                flag = flag and self.joint_in_range(i, qd[i])
        return flag

    def midrange_error(self):
        return trig.angles_standard_range(self.q - self.qm)*self.w 

    def joint_stepsize_interval(self, direction, max_speed = gen.infinity, delta_t = 0.001):
        etta_l = []
        etta_h = []

        for i in range(7):
            if not gen.equal(direction[i], 0.0):
                if (self.w[i] != 0.0):
                    a = (self.ql[i] - self.q[i])/direction[i]    
                    b = (self.qh[i] - self.q[i])/direction[i]
                    etta_l.append(gen.sign_choice(a, b, direction[i]))
                    etta_h.append(gen.sign_choice(b, a, direction[i]))

                a = delta_t*max_speed/direction[i]
                etta_l.append(gen.sign_choice(-a, a, direction[i]))
                etta_h.append(gen.sign_choice( a,-a, direction[i]))

        if (etta_l == []) or (etta_h == []):
            return (0.0, 0.0)
        else:
            return (max(etta_l), min(etta_h))

    def set_config(self, qd):
        '''
        sets the configuration to "qd"
        This function should not be called by the end user. Use function "set_config" in class PR2_ARM  
        '''    

        if not len(qd) == 7:
            print "set_config error: Number of input elements must be 7"
            return False

        if self.all_joints_in_range(qd):
            for i in range(0, 7):
                if gen.equal(self.w[i], 0.0):
                    self.q[i] = qd[i]
                else:
                    self.q[i] = trig.angle_standard_range(qd[i])

            self.c = [math.cos(self.q[i]) for i in range(0,7)]
            self.s = [math.sin(self.q[i]) for i in range(0,7)]

            [s0, s1, s2, s3, s4, s5, s6] = self.s
            [c0, c1, c2, c3, c4, c5, c6] = self.c

            self.s1_mult1 = [s1*s0]
            [s10]         = self.s1_mult1

            self.s2_mult1 = s2*np.array([s0, s1, s2, s10])
            [s20,s21, s22, s210]  = self.s2_mult1

            self.s3_mult1 = s3*np.array([s0, s1, s2, s10, s20, s21, s22, s3,s210])
            [s30, s31, s32, s310, s320, s321, s322, s33,s3210] = self.s3_mult1

            self.c0_mult = c0*np.array([s0,s1,s2,s10,s20,s21,s30,s31,s32,s321])
            [c0s0,c0s1,c0s2,c0s10,c0s20,c0s21,c0s30,c0s31,c0s32,c0s321] = self.c0_mult

            self.c1_mult = c1*np.array([c0, s0, s1, s2, s3, s10, s20,s30,s32, s320])
            [c10, c1s0, c1s1, c1s2, c1s3, c1s10, c1s20,c1s30,c1s32,c1s320] = self.c1_mult

            self.c2_mult = c2*np.array([c0,c1,c2,c10,s0,s1,s2,s3,s10,s20,s30,s31,s310, c1s30,c0s31])
            [c20,c21,c22,c210,c2s0,c2s1,c2s2,c2s3,c2s10,c2s20,c2s30,c2s31,c2s310,c21s30,c20s31] = self.c2_mult

            self.c3_mult = c3*np.array([c0,c1,c2,c3, s0,s1,s2,s3,s10,s20,s21,s30,c10,c20,c21,c210,c2s0,c2s10])
            [c30,c31,c32,c33,c3s0,c3s1,c3s2,c3s3,c3s10,c3s20,c3s21,c3s30,c310,c320,c321,c3210,c32s0,c32s10] = self.c3_mult

            self.s0_mult = s0*np.array([c21,c31,c321])
            [c21s0,c31s0,c321s0]  = self.s0_mult

            self.s1_mult2 = s1*np.array([c10,c20,c30, c32,c320])
            [c10s1,c20s1,c30s1, c32s1,c320s1] = self.s1_mult2

            self.s2_mult2 = s2*np.array([c10,c20,c30, c32,c310])
            [c10s2,c20s2,c30s2, c32s2,c310s2]  = self.s2_mult2

            self.s3_mult2 = s3*np.array([c10, c20, c30, c21, c210,s32])
            [c10s3, c20s3, c30s3, c21s3, c210s3,s332]  = self.s3_mult2

            self.cs_mult = [c10*s32, c31*s20, s5*s4]
            [c10s32, c31s20, s54] = self.cs_mult

            self.c5_mult = c5*np.array([c4, s4, s5])
            [c54, c5s4, c5s5] = self.c5_mult

            self.s6_mult = s6*np.array([s4, s5, c4, c5, c54, s54])
            [s64, s65, c4s6, c5s6, c54s6, s654] = self.s6_mult

            self.c6_mult = c6*np.array([c4, c5, s4, s5, c54, s54])
            [c64, c65, c6s4, c6s5, c654, C6s54] = self.c6_mult

            self.mid_dist_sq = None
            '''
            Do not set any other environmental variables here
            '''    
            return True
        else:
            print "Error from PR2_ARM.set_config(): Given joints are not in their feasible range"
            print "Lower Limit  :", self.ql
            print "Upper Limit  :", self.qh
            print "Desired Value:", qd
            return False
       
    def closest_config_metric(self, q):
        dist = 0
        cc   = np.zeros(7)
        for i in range(7):
            (qq, dd) = trig.closest_angle_metric(self.q[i], q[i])
            dist  = dist + dd
            cc[i] = qq
        return (cc, dd)

    def objective_function(self):
        if self.mid_dist_sq == None:
            e = self.midrange_error()
            self.mid_dist_sq = np.dot(e.T,e)
        return self.mid_dist_sq

    def __init__(self, ql = default_ql, qh = default_qh, W = default_W):
        '''
        ql and qh define the lower and higher bounds of the joints
        '''    

        assert (len(ql) == 7) and (len(qh) == 7)

        self.ql = ql
        self.qh = qh
        self.qm = (qh + ql)/2

        self.Delta  = None
        self.Phi    = None

        self.w = np.zeros(7)
        self.q = np.copy(self.qm)
        for i in range(0,7):
            self.w[i] = math.sqrt(W[i])

        # sets all angles to the midrange by default
        self.set_config(self.qm)


class PR2_ARM():

    def set_config(self, qd):
        if self.config.set_config(qd):
            self.wrist_position_vector    = None
            self.wrist_orientation_matrix = None
            self.JJ          = None
            self.E           = None
            self.F           = None
            self.Delta       = None
            if self.velocity_based_ik_required:
                self.ik.configuration.q = np.copy(qd)
                self.ik.configuration.initialize()
                self.ik.forward_update()
    
            return True
        else:
            print "Could not set the given joints."
            return False

    def set_target(self, target_position, target_orientation):
        '''
        sets the endeffector target to the given position and orientation
        variables self.xd and self.Rd should not be manipulated by the user. Always use this function
        '''    
        assert gen.equal(np.linalg.det(target_orientation), 1.0)
        self.xd = target_position
        self.Rd = target_orientation

        [Q, Q2, d42, d44, a00, d22_plus_d44, foura00d44, alpha] = self.additional_dims

        sai = math.atan2(self.xd[0], self.xd[1])
        r2  = self.xd[0]**2 + self.xd[1]**2
        ro2 = r2 + self.xd[2]**2
        R2  = ro2 - d22_plus_d44 + a00
        '''
        alpha, betta and gamma are selected so that w^2 * (1 - v^2) = alpha*v^2 + betta*v + gamma
        '''
        
        T2    = R2**2 - 4*a00*r2
        betta = - 2*R2*Q/foura00d44
        gamma = - T2/foura00d44

        self.Phi            = None
        self.Delta          = None

        self.target_parameters = [r2, ro2, R2, T2, alpha, betta, gamma, sai]

    def elbow_position(self):        
        X =  self.a0*self.config.c[0] + self.config.c[0]*self.d2*self.config.s[1]
        Y =  self.a0*self.config.s[0] + self.d2*self.config.s[0]*self.config.s[1]
        Z =  self.config.c[1]*self.d2
        return np.array([X,Y,Z])
    
            
    def wrist_position(self):        
        '''
        Returns the cartesian coordiantes of the origin of the wrist. The origin of the wrist is the wrist joint center 
        '''    
        if self.wrist_position_vector == None:
            [s0, s1, s2, s3, s4, s5, s6] = self.config.s
            [c0, c1, c2, c3, c4, c5, c6] = self.config.c
            [s10]         = self.config.s1_mult1
            [s30, s31, s32, s310, s320, s321, s322, s33,s3210] = self.config.s3_mult1
            [c0s0,c0s1,c0s2,c0s10,c0s20,c0s21,c0s30,c0s31,c0s32,c0s321] = self.config.c0_mult
            [c20,c21,c22,c210,c2s0,c2s1,c2s2,c2s3,c2s10,c2s20,c2s30,c2s31,c2s310,c21s30,c20s31] = self.config.c2_mult
            [c30,c31,c32,c33,c3s0,c3s1,c3s2,c3s3,c3s10,c3s20,c3s21,c3s30,c310,c320,c321,c3210,c32s0,c32s10] = self.config.c3_mult
            [c10s1,c20s1,c30s1, c32s1,c320s1] = self.config.s1_mult2
            [c10s3, c20s3, c30s3, c21s3,c210s3,s332]  = self.config.s3_mult2

            X =  c0*self.a0 + c0s1*self.d2 + (c30s1 + c210s3 - s320)*self.d4

            Y =  s0*self.a0 + s10*self.d2 + (c3s10 + c0s32 + c21s30)*self.d4

            Z =  c1*self.d2 + (c31 - c2s31)*self.d4
        
            self.wrist_position_vector = np.array([X, Y, Z])

        return copy.copy(self.wrist_position_vector)

    def wrist_orientation(self):        

        if self.wrist_orientation_matrix == None:
            [s0, s1, s2, s3, s4, s5, s6] = self.config.s
            [c0, c1, c2, c3, c4, c5, c6] = self.config.c
            [s10]         = self.config.s1_mult1
            [s20,s21, s22, s210]  = self.config.s2_mult1
            [c0s0,c0s1,c0s2,c0s10,c0s20,c0s21,c0s30,c0s31,c0s32,c0s321] = self.config.c0_mult
            [c10, c1s0, c1s1, c1s2, c1s3, c1s10, c1s20,c1s30,c1s32,c1s320] = self.config.c1_mult
            [c20,c21,c22,c210,c2s0,c2s1,c2s2,c2s3,c2s10,c2s20,c2s30,c2s31,c2s310,c21s30,c20s31] = self.config.c2_mult
            [c21s0,c31s0,c321s0]  = self.config.s0_mult
            [c10s2,c20s2,c30s2, c32s2,c310s2]  = self.config.s2_mult2
            [c10s32, c31s20, s54] = self.config.cs_mult
            [s64, s65, c4s6, c5s6, c54s6, s654] = self.config.s6_mult
            [c64, c65, c6s4, c6s5, c654, C6s54] = self.config.c6_mult

            R03 = np.array([[-s20 + c210, -c0s1, -c2s0 - c10s2],
                               [c0s2 + c21s0, -s10, c20 - c1s20],                
                               [-c2s1, -c1, s21]]) 

            R47 = np.array([[-s64 + c654, -c6s4 - c54s6, c4*s5],
                               [c4s6 + c65*s4, c64 - c5*s64, s54],                
                               [-c6s5, s65, c5]]) 

            R34 =  np.array([[  c3,     0,     s3 ],
                                [  s3,     0,    -c3 ],
                                [  0,      1,     0  ]])

            self.wrist_orientation_matrix = np.dot(np.dot(R03, R34), R47)

        return copy.copy(self.wrist_orientation_matrix)

    def in_target(self, norm_precision = 0.01):
        return vecmat.equal(self.xd, self.wrist_position(), epsilon = norm_precision) and vecmat.equal(self.Rd, self.wrist_orientation(), epsilon = norm_precision)

    def div_phi_err(self):
        '''
        '''
        if self.F == None:
            self.div_theta_err()

        return copy.copy(self.F)

    def div_theta_err(self):
        '''
        '''
        if self.E == None:
            [[r11, r12, r13],
            [r21, r22, r23],
            [r31, r32, r33]] = self.Rd

            [s0, s1, s2, s3, s4, s5, s6] = self.config.s
            [c0, c1, c2, c3, c4, c5, c6] = self.config.c

            [s10]         = self.config.s1_mult1
            [s20,s21, s22, s210]  = self.config.s2_mult1
            [s30, s31, s32, s310, s320, s321, s322, s33,s3210] = self.config.s3_mult1
            [c0s0,c0s1,c0s2,c0s10,c0s20,c0s21,c0s30,c0s31,c0s32,c0s321] = self.config.c0_mult
            [c10, c1s0, c1s1, c1s2, c1s3, c1s10, c1s20,c1s30,c1s32,c1s320] = self.config.c1_mult
            [c20,c21,c22,c210,c2s0,c2s1,c2s2,c2s3,c2s10,c2s20,c2s30,c2s31,c2s310,c21s30,c20s31] = self.config.c2_mult
            [c30,c31,c32,c33,c3s0,c3s1,c3s2,c3s3,c3s10,c3s20,c3s21,c3s30,c310,c320,c321,c3210,c32s0,c32s10] = self.config.c3_mult
            [c21s0,c31s0,c321s0]  = self.config.s0_mult
            [c10s1,c20s1,c30s1, c32s1,c320s1] = self.config.s1_mult2
            [c10s2,c20s2,c30s2, c32s2,c310s2]  = self.config.s2_mult2
            [c10s3, c20s3, c30s3, c21s3, c210s3,s332]  = self.config.s3_mult2
            [c10s32, c31s20, s54] = self.config.cs_mult
            [c54, c5s4, c5s5] = self.config.c5_mult
            [s64, s65, c4s6, c5s6, c54s6, s654] = self.config.s6_mult
            [c64, c65, c6s4, c6s5, c654, C6s54] = self.config.c6_mult

            [Q, Q2, d42, d44, a00, d22_plus_d44, foura00d44, alpha] = self.additional_dims

            [r2, ro2, R2, T2, alpha, betta, gamma, sai] = self.target_parameters

            self.E = np.zeros((7,7))
            self.F = np.zeros(7)

            self.E[0,0] = 1.0
            
            self.E[1,3] = - Q*s3

            self.E[2,2] = - 2*c2*s332
            self.E[2,3] = - 2*alpha*c3s3 - betta*s3 - 2*c3*s322

            self.E[3,1] = - self.d2*s1 - (c3*s1 + c2*c1*s3)*self.d4
            self.E[3,2] =   s321*self.d4
            self.E[3,3] =   - (c1s3 + c32s1)*self.d4
            
            self.E[4,1] = r13*(- c20*s31 + c310) + r23*(- c2s310 + c31s0) - r33*(c3s1 + c21*s3)
            self.E[4,2] = - r13*(c2s30 + c10s32) + r23*(c20s3 - c1s320) + r33*s321

            self.E[4,3] = r13*(- c3s20 + c3210 - c0s31) + r23*(c30s2 + c321s0 - s310) + r33*(- c1s3 - c32s1)
            self.E[4,5] = s5

            self.E[5,1] = r13*c0s21 - r23*s210 + r33*c1s2
            self.E[5,2] = r13*(s20 - c210) - r23*(c0s2 + c21s0) + r33*c2s1
            self.E[5,4] = - c4*s5
            self.E[5,5] = - c5*s4

            self.E[6,1] =   r11*(- c20s31 + c310) + r21*(- c2s310 + c31s0) - r31*(c3s1 + c21s3)
            self.E[6,2] = - r11*(c2s30 + c10s32) + r21*(c20s3 - c1s320) + r31*s321
            self.E[6,3] =   r11*(- c3s20 + c3210 - c0s31) + r21*(c30s2 + c321s0 - s310) - r31*(c1s3 + c32s1)
            self.E[6,5] =   c65
            self.E[6,6] = - s65

            self.F[0] = -1.0
            self.F[1] =   2*self.a0*(s0*self.xd[0] - c0*self.xd[1])
            self.F[4] = r13*(- c0s32 - c21s30 - c3s10) + r23*(- s320  + c210s3 + c30s1)  
            self.F[5] = r13*(-c20 + c1s20) - r23*(c2s0 + c10s2)
            self.F[6] = - r11*(c0s32 + c21s30 + c3s10) + r21*(- s320 + c210s3 + c30s1)

        return copy.copy(self.E)
        
    def joint_jacobian(self):  
        '''
        Returns the Joint Jacobian (in this case a vector of 7 elements: rond q_i/rond phi)
        make sure that the IK is already run or:
        Current joints must lead to x_d and R_d  
        
        '''

        if self.JJ == None:

            E = self.div_theta_err()
            F = self.div_phi_err()
            if gen.equal(E[1,3],0.0) or gen.equal(E[2,2],0.0) or gen.equal(E[3,1],0.0) or gen.equal(E[4,5],0.0) or gen.equal(E[5,4],0.0) or gen.equal(E[6,6],0.0):
                return None
            else:
                self.JJ = np.zeros(7)

                self.JJ[0] =   1.0
                self.JJ[3] = - F[1]/E[1,3]
                self.JJ[2] = - E[2,3]*self.JJ[3]/E[2,2]
                self.JJ[1] = - (E[3,2]*self.JJ[2] + E[3,3]*self.JJ[3])/E[3,1]

                self.JJ[5] = - (F[4] + np.dot(E[4,1:4],self.JJ[1:4]))/E[4,5]
                #J[5] = - (F[4,0] + F[4,1]*J[1] + F[4,2]*J[2] + F[4,3]*J[3])/F[4,5]
                self.JJ[4] = - (F[5] + E[5,1]*self.JJ[1] + E[5,2]*self.JJ[2] + E[5,5]*self.JJ[5])/E[5,4] 
                self.JJ[6] = - (F[6] + np.dot(E[6,1:6],self.JJ[1:6]))/E[6,6]
                #F60*J0 + F61*J1 + F62*J2 + F63*J3 + F64*J4 + F65*J5 + F66*J6 = 0  ==> J6 = - (F60 + F61*J1 + F62*J2 + F63*J3 + F64*J4 + F65*J5)/ J66

        return copy.copy(self.JJ)

    def grown_phi(self, eta, k = 0.99):
        '''
        grows the redundant parameter by eta (adds eta to the current phi=q[0] and returns the new value for phi
        1 - this function does NOT set the configuration so the joint values do not change
        2 - if the grown phi is not in the feasible interval Delta, it will return the closest point in the range with a safety coefficient k so that
        new phi = old phi + eta        : if    eta in Delta
        new phi = old phi + k*Delta_h  : if    eta > Delta_h
        new phi = old phi + k*Delta_l  : if    eta < Delta_l
        '''  
        Delta = self.delta_phi_interval()

        # if Delta contains more than one interval, then we need to find which interval contains zero

        assert len(Delta) > 0
        j = 0
        while (j < len(Delta)):
           if 0.0 in interval(Delta[j]):
               (dl,dh) = Delta[j] 
           j = j + 1

        if eta in Delta:
            return self.config.q[0] + eta
        elif eta >= dh:   # if zero is not in any of the intervals, this line will raise an error because dh is not defined
            return self.config.q[0] + k*dh
        else:
            assert eta <= dl  # eta must now be smaller than Delta_l
            return self.config.q[0] + k*dl

    def position_permission_workspace(self,fixed):
        '''
        returns the permission range of x, y and z of the endeffector.
        fixed is an array of size 4, specifying if the corresponding joint is fixed or free
        The size is 4 because only the first four joints influence the position of the EE
        '''
        int_c = []
        int_s = []

        for i in range(0,4):
            if fixed[i]:
                int_c.append(imath.cos(interval(self.config.q[i])))
                int_s.append(imath.sin(interval(self.config.q[i])))
            else:
                int_c.append(imath.cos(interval([self.config.ql[i], self.config.qh[i]])))
                int_s.append(imath.sin(interval([self.config.ql[i], self.config.qh[i]])))

        int_s10    = int_s[1]*int_s[0]
        int_s32    = int_s[3]*int_s[2]        
        int_s31    = int_s[3]*int_s[1]        
        int_s320   = int_s32*int_s[0]

        int_c21    = int_c[2]*int_c[1]
        int_c31    = int_c[3]*int_c[1]
        int_c0s1   = int_c[0]*int_s[1]
        int_c30s1  = int_c[3]*int_c0s1
        int_c0s32  = int_s32*int_c[0]
        int_c21s3  = int_c21*int_s[3]
        int_c21s30 = int_c21s3*int_s[0]
        int_c210s3 = int_c21s3*int_c[0]
        int_c2s31  = int_s31*int_c[2]
        int_c3s10  = int_s10*int_c[3]

        int_X =  int_c[0]*interval(self.a0) + int_c0s1*interval(self.d2) + (int_c30s1 + int_c210s3 - int_s320)*interval(self.d4)

        int_Y =  int_s[0]*interval(self.a0) + int_s10*interval(self.d2) + (int_c3s10 + int_c0s32 + int_c21s30)*interval(self.d4)

        int_Z =  int_c[1]*interval(self.d2) + (int_c31 - int_c2s31)*interval(self.d4)

        return [int_X, int_Y, int_Z]
        
    def inverse_update_old(self):    
        '''
        Finds the inverse kinematic which is closest to the midrange of joints 
        The new joint angles will be set if all the kinematic equations are satisfied. 
        All kinematic parameters will be updated.
        '''
        # Finding a feasible phi (theta0)

        # first try the current theta0:

        phi     = self.config.q[0]
        phi_l   = self.config.ql[0]
        phi_h   = self.config.qh[0]
        q_d     = self.IK_config(phi)

        # If solution not found search within the range:
        
        n = 3
        while (q_d == None) and (n < 10):
            i = 0
            while (q_d == None) and (i < n):
                phi = phi_l + (2*i + 1)*(phi_h - phi_l)/(2*n)
                q_d = self.IK_config(phi)
                i = i + 1
            n = n + 1

        if q_d == None:
            print "Given pose out of workspace. No solution found"
            return False
        
        assert self.set_config(q_d)                        
        e = trig.angles_standard_range(q_d - self.config.qm)*self.config.w
        new_error = np.linalg.norm(e)
        old_error = 10000

        while (new_error < old_error - gen.epsilon) and (q_d != None) and (new_error > gen.epsilon):
            #old_error = new_error
            assert self.set_config(q_d)
            phi     = self.config.q[0]
            J = self.joint_jacobian()
            if J == None:
                q_d = None
            else:
                P = self.config.w*J
                e = trig.angles_standard_range(q_d - self.config.qm)*self.config.w
                den        = np.dot(P.T, P)
                if gen.equal(den, 0.0):
                    q_d = None
                else:
                    Delta_phi  = - np.dot(P.T, e) / den
                    old_error  = np.linalg.norm(e)
                    new_phi    = self.grown_phi(Delta_phi)
                    q_d        = self.IK_config(new_phi)

            if q_d == None:
                new_error = 0
            else:
                e = trig.angles_standard_range(q_d - self.config.qm)*self.config.w
                new_error  = np.linalg.norm(e)
          
        assert vecmat.equal(self.wrist_position(), self.xd)
        if self.orientation_respected:
            assert vecmat.equal(self.wrist_orientation(), self.Rd)
        return True

    def restore_config(self, q_old):
        q = np.copy(self.config.q)
        assert self.set_config(q_old)
        return q 

    def pose_metric(self):
        d  = np.linalg.norm(self.xd - self.wrist_position())
        d += np.linalg.norm(self.Rd - self.wrist_orientation())
        return d
        
    def optimal_config(self, show = False):
        '''
        Returns the optimal value for phi that minimizes the cost function. This function does not change the configuration
        If show = True, the values of phi and objective function are printed on the console
        '''
        
        keep_q     = np.copy(self.config.q)
        counter = 0
        while True:
            J   = self.joint_jacobian()
            e   = self.config.midrange_error()
            if show:
                print "Iteration          : ", counter
                print "Value of redundancy: ", self.config.q[0]
                print "Objective Function : ", self.config.objective_function()
            if J == None:
                if show:
                    print "No Jacobian! Optimum phi = ", self.config.q[0]
                return self.restore_config(keep_q)
            P   = self.config.w*J    
            den = np.dot(P.T, P)
            if gen.equal(den, 0.0):
                if show:
                    print "Division by Zero! Optimum phi = ", self.config.q[0]
                return self.restore_config(keep_q)
            Delta_phi  = - np.dot(P.T, e) / den
            old_err    = self.config.objective_function()
            new_phi    = self.grown_phi(Delta_phi)
            q          = self.IK_config(new_phi)
            if q == None:
                if show:
                    print "No solution for the updated phi! Optimum phi = ", self.config.q[0]
                return self.restore_config(keep_q)

            if not self.set_config(q):
                if show:
                    print "Solution found but not feasible! This should not happen. Optimum phi = ", self.config.q[0]
                return self.restore_config(keep_q)

            if show:
                print "A better phi is found: ", new_phi

            new_err = self.config.objective_function()

            if new_err > old_err - 0.01:
                if show:
                    print "Error is not reduced any more. Optimum phi = ", self.config.q[0]
                return self.restore_config(keep_q)

            counter = counter + 1
            
    def reduce_error(self, max_speed = gen.infinity, ttr = 0.1):
        if self.in_target():
            q0        = np.copy(self.config.q)
            err       = self.config.objective_function()
            q_opt     = self.optimal_config()
            (el, eh)  = self.config.joint_stepsize_interval(direction = q_opt - q0, max_speed = max_speed, delta_t = ttr) 
            assert el < 1.0
            if eh > 1.0:
                eh = 1.0
            q = q0 + eh*(q_opt - q0)
            if self.set_config(q):
                if self.config.objective_function() > err:
                    assert self.set_config(q0)
                    return False
            return True
        else:
            print "Error from PR2_ARM.reduce_error(): The endeffector is not in target."
            print self.wrist_position() - self.xd
            print self.wrist_orientation() - self.Rd
            return False

    def closest_feasible_phi(self, phi, PS, increment = math.pi/360.0):
        '''
        This function should be used when given phi is in permission set PS and yet
        there is no IK solution for it. So the neighborhood of phi is searched for a feasible IK solution
        If a solution is found, the config is set and a True is returned, 
        If all the permission set is searched with no solution, False is returned and the configuration does not change
        '''
        (phi_l, phi_h) = gen.accommodating_interval(phi, PS)

        assert (phi < phi_h) and (phi > phi_l)

        phi_up   = phi
        phi_down = phi
        while True:
            stay_up   = (phi_up < phi_h)
            stay_down = (phi_down > phi_l)

            if stay_up:
                phi_up = phi_up + increment
                q = self.IK_config(phi_up)
                if q != None:
                    if self.set_config(q):
                        return True

            if stay_down:
                phi_down = phi_down - increment
                q = self.IK_config(phi_down)
                if q != None:
                    if self.set_config(q):
                        return True

            if not (stay_up or stay_down):             
                # Nothing found :-(
                return False
                
    def ik_direction(self, phi = None, optimize = False):
        '''
        Solves the position based inverse kinematics and returns a direction in the jointspace (joint correction)
        The configuration does not change
        '''
        q0 = np.copy(self.config.q)
        if self.inverse_update(phi = phi, optimize = optimize):
            q  = self.restore_config(q0)
            return trig.angles_standard_range(q - q0)
        else:
            return np.zeros(7)
    
    def feasible_joint_stepsize(self, direction, max_speed, ttr):
        q0        = np.copy(self.config.q)
        err       = self.pose_metric()
        (el, eh)  = self.config.joint_stepsize_interval(direction = direction, max_speed = max_speed, delta_t = ttr) 
        assert el < 1.0
        if eh > 1.0:
            eh = 1.0
        return eh

    def move_joints_towards(self, direction, max_speed, ttr):
        q = q0 + direction*self.feasible_joint_stepsize(direction, max_speed, ttr)
        return self.set_config(q)

    def move_towards_target(self, max_speed, ttr, phi = None, optimize = False, show = False):
        q0        = np.copy(self.config.q)
        err       = self.pose_metric()
        jdir      = self.ik_direction(phi = phi, optimize = optimize)
        # print "direction = ", jdir
        if np.linalg.norm(jdir) > 0.001:
            (el, eh)  = self.config.joint_stepsize_interval(direction = jdir, max_speed = max_speed, delta_t = ttr) 
            # assert el < 0.0
            if eh > 1.0:
                eh = 1.0
            q = q0 + eh*jdir
            if self.set_config(q):
                if self.pose_metric() < err:
                    return True
                else:
                    print "Error is not reduced"
            else:
                print "set config failed"
        else:
            return True
        if show:
            print "Moving towards target Failed:"
            print
            print "direction = ", jdir
            print "--------------------"
            print "Old q: ", q0
            print "New q: ", self.config.q
            print "--------------------"
            print "Old Error: ", err
            print "New Error: ", self.pose_metric()
            print "--------------------"

        assert self.set_config(q0)
        return False
        

    def inverse_update(self, phi = None, optimize = False, show = False):    
        '''
        Finds the inverse kinematic solution for the given redundant parameter phi
        is phi is not feasible, the solution corresponding to the closest phi is returned.
        If argument optimize is True, the solution will be optimized 
        so that the joint values will be as close as possible to self.config.qm
        If phi is not given, current q[0] will be selected as phi
        
        The new joint angles will be set if all the kinematic equations are satisfied. 
        All kinematic parameters will be updated.
        '''
        # Finding a feasible phi (theta0)
        if phi == None:
            phi     = self.config.q[0]

        PS = self.permission_set_position()
        if show:
            print "Permission Set for phi = ", PS
            print "Initial phi            = ", phi
        
        if len(PS) == 0:
            print "len(PS) = 0"
            print "Error from PR2_ARM.inverse_update(): The target is out of workspace! No solution found."
            return False
        else:
            if not (phi in PS):
                phi = gen.closest_border(phi, PS, k = 0.01)
                if show:
                    print "Phi is not in PS"
                    print "Closest phi in PS:", phi

            q = self.IK_config(phi) 
            if q == None:
                if show:
                    print phi, " is not a feasible phi. No solution found"
                if not self.closest_feasible_phi(phi, PS):
                    print "Error from PR2_ARM.inverse_update(): The target is out of workspace! No solution found."
                    return False
                if show:
                    print "Next phi: ", self.config.q[0]
            else:    
                if not self.set_config(q):
                    if show:
                        print "Not expected to see. Solution exists but not feasible!"
                    assert False

            # when you reach here, the feasible q has been set    
            
            if optimize:
                self.reduce_error()
             
        assert vecmat.equal(self.wrist_position(), self.xd)
        if self.orientation_respected:
            assert vecmat.equal(self.wrist_orientation(), self.Rd)

        return True
        
    def all_IK_solutions(self, phi):    
        '''
        Finds all the feasible solutions of the Inverse Kinematic problem for given redundant parameter "phi"
        "phi" is the value of the first joint angle "q[0]"
        This function does NOT set the configuration so the joints do not change
        '''
        if not self.config.joint_in_range(0, phi):
            print "IK_config error: Given theta0 out of feasible range"
            return []

        solution_set = []

        c0 = math.cos(phi)
        s0 = math.sin(phi)

        [Q, Q2, d42, d44, a00, d22_plus_d44, foura00d44, alpha] = self.additional_dims
        [r2, ro2, R2, T2, alpha, betta, gamma, sai] = self.target_parameters

        u  = c0*self.xd[0] + s0*self.xd[1]
        v  = (2*self.a0*u - R2)/Q

        v2 = v**2
        A  = self.d2 + v*self.d4

        if gen.equal(v, 1.0):
            #"Singular Point"
            return []
            '''
            In this case, a singularity happens
            '''
        elif (v > 1.0) or (v < -1.0): 
            #"Given pose out of workspace"
            return []
        else:
            i  = 0
            tt3 = trig.arccos(v)

            while (i < 2):
                theta3 = (2*i - 1)*tt3  # theta3 is certainly in standard range
                if self.config.joint_in_range(3,theta3):
                    s3     = math.sin(theta3)
                    c3     = v
                    c30    = c3*c0
                    B      = self.d4*s3
                    T34 = genkin.transfer_DH_standard( 0.0 , math.pi/2, 0.0, 0.0, theta3)
                    R34 = T34[0:3,0:3]

                    w2 = (alpha*v2 + betta*v + gamma)/(1 - v2)
                    if gen.equal(w2, 1.0):
                        w2 = 1.0
                    elif gen.equal(w2, 0.0):
                        w2 = 0.0
                    elif w2 < 0.0:
                        print "IK_config error: w^2 is negative, This should never happen! Something is wrong!"
                        assert False 

                    w  = math.sqrt(w2)
                    if (w < 1.0):
                        m = 0              
                        while (m < 2) and (not ((w == 0.0) and (m == 1))):  # beghole emam: intor nabashad ke ham w sefr bashad va ham m yek. 
                            s2  = (2*m - 1)*w
                            s20 = s2*s0 
                            c0s2= c0*s2  
                            
                            tt2 = trig.arcsin(s2)
                            j = 0
                            while (j < 2):
                                theta2 = trig.angle_standard_range(math.pi*(1 - j) + (2*j - 1)*tt2)
                                if self.config.joint_in_range(2, theta2):
                                    c2     = math.cos(theta2)
                                    c20    = c2*c0
                                    c2s0   = c2*s0
                                    E      = B*s2
                                    F      = B*c2
                                    R1     = math.sqrt(A**2 + F**2)
                                    sai1   = math.atan2(F,A)
                                    R1_nul = gen.equal(R1, 0)
                                    if not R1_nul:
                                        z_R1 = self.xd[2]/R1    
                                        flg  = (z_R1 < 1.0) and (z_R1 > - 1.0)
                                    else:
                                        flg = False

                                    if flg:
                                        tt1 = trig.arccos(self.xd[2]/R1)
                                        k = 0                
                                        while (k < 2):
                                            theta1 = (2*k - 1)*tt1 - sai1 
                                            if self.config.joint_in_range(1, theta1):
                                                s1   = math.sin(theta1)
                                                c1   = math.cos(theta1)
                                                
                                                As1Fc1 = self.a0 + A*s1 + F*c1
                                                X      = c0*As1Fc1 - E*s0
                                                Y      = s0*As1Fc1 + E*c0
                                                Z      = A*c1 - F*s1 

                                                u2 = s2*s3*self.d4
                                                u3 = c2*s3*self.d4
                                                u4 = self.d2+ c3*self.d4
                                                u1 = self.a0 + u3*c1 + u4*s1
                                                AA = np.array([[alpha*d44, d44*betta - 2*d42 , - self.d2**2 + d44*(gamma -1)],
                                                                   [0.0 , 2*self.xd[2]*self.d4 , 2*self.xd[2]*self.d2],   
                                                                   [- d44*(1+alpha) , -betta*d44 , - self.xd[2]**2 + d44*(1-gamma) ]])
                                                lnda = np.array([c1*c1, c1, 1.0])
                                                vvct = np.array([v*v, v, 1.0])

                                                if vecmat.equal(self.xd, [X,Y,Z]):
                                                    if self.orientation_respected:
                                                        R03 = np.array([[c20*c1 - s20, -c0*s1, -c2s0 - c1*c0*s2],
                                                                           [c0s2 + c1*c2*s0, -s1*s0, c20 - c1*s20],   
                                                                           [-c2*s1, -c1, s2*s1 ]])

                                                        R04 = np.dot(R03, R34)
                                                        R47 = np.dot(R04.T, self.Rd)
                                                        tt5 = trig.arccos(R47[2,2])
                                                        l = 0
                                                        while (l < 2):
                                                            theta5 = (2*l - 1)*tt5 # theta5 is certainly in standard range
                                                            if self.config.joint_in_range(5, theta5):
                                                                s5     = math.sin(theta5)
                                                                c5     = math.cos(theta5)
                                                                if gen.equal(s5,0):
                                                                    assert gen.equal(R47[2,0], 0)
                                                                    # "Singular Point"
                                                                    return []
                                                                    '''
                                                                    In this case, only sum of theta4 + theta6 is known 
                                                                    '''
                                                                else:
                                                                    c6     = - R47[2,0]/s5
                                                                    s6     =   R47[2,1]/s5
                                                                    c4     =   R47[0,2]/s5
                                                                    s4     =   R47[1,2]/s5

                                                                    theta6 = trig.arcsincos(s6, c6)
                                                                    theta4 = trig.arcsincos(s4, c4)

                                                                    assert gen.equal(R47[1,0] ,  c4*s6 + c5*c6*s4)
                                                                    assert gen.equal(R47[1,1] ,  c4*c6 - c5*s4*s6)
                                                                    assert gen.equal(R47[0,0] ,  -s4*s6 + c4*c5*c6)
                                                                    assert gen.equal(R47[0,1] ,  -c6*s4 - c4*c5*s6)

                                                                    assert self.config.joint_in_range(4, theta4)    
                                                                    assert self.config.joint_in_range(6, theta6)    

                                                                    solution_set.append(np.array([phi, theta1, theta2, theta3, theta4, theta5, theta6]))
                                                            l = l + 1
                                                    else:
                                                        solution_set.append(np.array([phi, theta1, theta2, theta3, self.config.q[4], self.config.q[5], self.config.q[6]]))
                                            k = k + 1
                                j = j + 1
                            m = m + 1
                i = i + 1 
        return solution_set

    def IK_config(self, phi):    
        '''
        Finds the solution of the Inverse Kinematic problem for given redundant parameter "phi"
        In case of redundant solutions, the one corresponding to the lowest objective function is selected.
        property ofuncode specifies the objective function:
            ofuncode = 0 (Default) the solution closest to current joint angles will be selected 
            ofuncode = 1 the solution corresponding to the lowest midrange distance is selected
        This function does NOT set the configuration so the joints do not change
        ''' 
        solution_set = self.all_IK_solutions(phi)

        if len(solution_set) == 0:
            # print "IK_config error: No solution found within the feasible joint ranges for given phi. Change the target or redundant parameter"
            print ".",
            return None

        delta_min = 1000
        for i in range(0, len(solution_set)):
            solution = solution_set[i]
            if self.ofuncode == 0:
                delta    = np.linalg.norm(trig.angles_standard_range(solution - self.config.q))
            elif self.ofuncode == 1:
                P = trig.angles_standard_range(solution - self.config.qm)*self.config.w
                delta = np.dot(P.T,P)
            else:
                print "IK_config error: Value ",self.ofuncode," for argument ofuncode is not supported"
                assert False
 
            if delta < delta_min:
                delta_min = delta
                i_min = i

        return solution_set[i_min]

    def __init__(self, a0 = 0.1, d2 = 0.4, d4 = 0.321, ql = default_ql, qh = default_qh, W = default_W, vts = False):

        if vts:
            self.velocity_based_ik_required = True
            # create an instance of PR2 geometry and configuration 
            pr2_geo    = maniplib.Manipulator_Geometry_PR2ARM()
            cs         = configlib.Joint_Configuration_Settings(default_joint_handling = 'No Mapping')
            pr2_config = maniplib.Manipulator_Configuration_PR2(cs)
            # create an instance of inverse kinematic solver for PR2
            iks = iklib.Inverse_Kinematics_Settings()
            self.ik = iklib.Inverse_Kinematics(pr2_geo, pr2_config, iks)
        else:
            self.velocity_based_ik_required = False

        self.orientation_respected = True
        self.config = PR2_ARM_Configuration(ql = ql, qh = qh, W = W)

        self.Rd = np.eye(3)    

        self.a0 = a0
        self.d2 = d2
        self.d4 = d4

        l2 = d2**2 + d4**2 - a0**2
        if l2 < 0:
            print "__init__ Error: Can not make the arm because the given dimensions are ill"
            return 0

        self.l = math.sqrt(l2)

        d42 = d4*d2
        Q   = -2*d42
        Q2  = Q**2
        d44 = d4**2
        a00 = a0**2

        d22_plus_d44 = d2*d2 + d44
        foura00d44   = 4*a00*d44 
        alpha        = - Q2/foura00d44

        self.additional_dims = [Q, Q2, d42, d44, a00, d22_plus_d44, foura00d44, alpha]


        self.l_se = [0.0, - d2, 0.0]
        self.l_ew = [0.0, 0.0, d4]

        self.ofuncode = 0

        self.wrist_position_vector    = None
        self.wrist_orientation_matrix = None
        self.JJ                       = None
        self.E                        = None
        self.F                        = None
        
        self.set_target(self.wrist_position(), self.wrist_orientation())

    '''
    def confidence_set_analytic(self):
        """
        This function finds and returns the confidence set for q0 so that joint angles q0 , q2 and q3 in the analytic solution to the inverse kinematic problem
        will be in their feasible range.
        For q0 being in the confidence set is a necessary and sufficient condition for three joints q0, q2 and q3 to be in their feasible range.
        "Confidence set" is a subset of "Permission set"
        The confidence set depends on the defined joint limits, the desired endeffector pose and current position of the joints (the quarter in which q2 and q3 are located).
        """
        s2_l  = math.sin(self.config.ql[2])
        s2_l2 = s2_l**2
        s2_h  = math.sin(self.config.qh[2])
        s2_h2 = s2_h**2

        # Finding wl, wh:

        qnl = trig.quarter_number(self.config.ql[2])
        qnh = trig.quarter_number(self.config.qh[2])
        qn  = trig.quarter_number(self.config.q[2])

        if qn == qnl:   # lower bound is in the same quarter as q2
            if (qn == qnh): # upper bound is in the same quarter as q2
                wl = min(s2_l2,s2_h2)
                wh = max(s2_l2,s2_h2)
            elif qn in [1,3]:
                (wl,wh) = (s2_l2, 1.0)
            else:
                (wl,wh) = (0.0, s2_l2)
        else:
            if (qn != qnh): # upper bound is not in the same quarter as q2
                (wl,wh) = (0.0, 1.0)
            elif qn in [1,3]:
                (wl,wh) = (0.0, s2_h2)
            else:
                (wl,wh) = (s2_h2, 1.0)

        # From here, copied from permission set
        #Finding Sl
        '''

    def project_to_ts(self,  js_traj, phi_start = 0.0, phi_end = None, delta_phi = 0.1):
        '''
        projects the given jointspace trajectory into the taskspace
        The phase starts from phi_start and added by delta_phi in each step.
        if at any time the joint values are not feasible, the process is stopped.
        '''
        
        if phi_end == None:
            phi_end = js_traj.phi_end

        ori_traj = trajlib.Orientation_Trajectory_Segment()
        ori_traj.capacity = 200
        pos_traj = trajlib.Polynomial_Trajectory()
        if phi_end > js_traj.phi_end:
            phi_end = js_traj.phi_end

        phi = phi_start
        js_traj.set_phi(phi)
        stay = True
        while stay and (self.set_config(js_traj.current_position)):
            if phi > phi_end:
                phi = phi_end
                stay = False
            pos_traj.add_point(phi - phi_start, self.wrist_position())
            ori_traj.add_point(phi - phi_start, self.wrist_orientation())
            phi = phi + delta_phi
            js_traj.set_phi(phi)
            
        pos_traj.add_point(phi - phi_start, self.wrist_position())
        ori_traj.add_point(phi - phi_start, self.wrist_orientation())
        return (pos_traj, ori_traj)
    """
    def project_to_js_vts(self, pos_traj, ori_traj = None, phi_start = 0.0, duration = 10.0, phi_dot = None, relative = True):
        '''
        projects the given taskspace pose trajectory into the jointspace using a combination of numeric and analytic inverse kinematics.
        The phase starts from phi_start increased by time with rate phi_dot.
        at any time, if a solution is not found, the process stops
        '''
        assert self.velocity_based_ik_required, "Error from PR2_ARM.project_to_js(): Velocity-Based mode is not active"
        tp = self.ik.endeffector.reference_positions[0]
        tf = self.ik.endeffector.reference_orientations[0]
        keep_config  = np.copy(self.config.q)
        if phi_dot   == None:
            phi_dot  = (pos_traj.phi_end - phi_start)/duration
        if ori_traj == None:
            ori_traj = trajlib.Orientation_Trajectory()
            ori_traj.current_orientation = self.wrist_orientation()
        
        jt           = jtrajlib.Joint_Trajectory(dof = 7)
        jt.add_point(phi = 0.0, pos = self.config.q, vel = np.zeros(7))

        tp.desired_trajectory    = pos_traj
        tf.desired_trajectory    = ori_traj

        pos_traj.set_phi(phi_start)
        ori_traj.set_phi(phi_start)
        if relative:
            tp.target_offset = self.wrist_position() - pos_traj.current_position
            tf.target_offset = np.dot(self.wrist_orientation(), ori_traj.current_orientation.T)  

        t0           = time.time()
        t            = 0.0
    
        while (t < duration + 0.00001):
            t        = time.time() - t0
            phi      = phi_start + phi_dot*t
            self.ik.endeffector.update_target(phi)
            '''
            self.ik.endeffector.update_pose_error()
            self.ik.endeffector.update_task_jacobian()
            self.ik.endeffector.update_error_jacobian(self.ik)
            '''
            self.ik.run()
            if self.ik.endeffector.in_target:
                print "In target: one point added :-)"
                if self.set_config(self.ik.configuration.q):
                    self.ofuncode = 1
                    self.qm = np.copy(self.config.q)
                    self.set_target(tp.rd, tf.rd)    
                    if self.inverse_update():
                        jt.add_point(phi = phi - phi_start, pos = self.config.q)

        jt.interpolate()
        self.set_config(keep_config)
        return jt
    """

    def project_to_js(self,  pos_traj, ori_traj = None, phi_start = 0.0, phi_end = None, delta_phi = 0.1, max_speed = 1.0, relative = True):
        '''
        projects the given taskspace pose trajectory into the jointspace using analytic inverse kinematics.
        The phase starts from phi_start and added by delta_phi in each step.
        at any time, if a solution is not found, the process stops
        '''
        keep_q = np.copy(self.config.q)

        if phi_end == None:
            phi_end = pos_traj.phi_end

        if ori_traj == None:
            ori_traj = trajlib.Orientation_Trajectory()
            ori_traj.current_orientation = self.wrist_orientation()

        if phi_end > pos_traj.phi_end:
            phi_end = pos_traj.phi_end

        jt          = trajlib.Polynomial_Trajectory(dimension = 7)
        jt.capacity = 2

        jt.add_point(phi = 0.0, pos = np.copy(self.config.q), vel = np.zeros(7))

        phi   = phi_start
        pos_traj.set_phi(phi)
        ori_traj.set_phi(phi)
        if relative:
            p0    = self.wrist_position() - pos_traj.current_position
            R0    = np.dot(self.wrist_orientation(), ori_traj.current_orientation.T)  
        else:
            p0    = np.zeros(3)
            R0    = np.eye(3)  
        
        phi       = phi + delta_phi
        stay      = True

        while stay:
            if phi > phi_end:
                phi = phi_end
            if phi == phi_end:
                stay = False
            pos_traj.set_phi(phi)
            ori_traj.set_phi(phi)
            p = p0 + pos_traj.current_position
            R = np.dot(R0, ori_traj.current_orientation)
            self.set_target(p, R)
            self.config.qm = np.copy(self.config.q)
            if self.move_towards_target(phi = self.config.q[0], optimize = True, max_speed = max_speed, ttr = delta_phi):
                jt.add_point(phi = phi - phi_start, pos = np.copy(self.config.q))
            else:
                print "Error is not reduced. Point is not Added"

            phi = phi + delta_phi

        jt.interpolate()
        self.config.qm = 0.5*(self.config.qh + self.config.ql)
        self.set_config(keep_q)

        return jt

    def project_to_js_vts(self,  pos_traj, ori_traj = None, phi_start = 0.0, phi_end = None, delta_phi = 0.1, relative = True, silent = True):
        '''
        projects the given taskspace pose trajectory into the jointspace using analytic inverse kinematics.
        The phase starts from phi_start and added by delta_phi in each step.
        at any time, if a solution is not found, the process stops
        '''
        if phi_end == None:
            phi_end = pos_traj.phi_end

        if ori_traj == None:
            ori_traj = trajlib.Orientation_Trajectory()
            ori_traj.current_orientation = self.wrist_orientation()

        if phi_end > pos_traj.phi_end:
            phi_end = pos_traj.phi_end

        jt          = jtrajlib.Joint_Trajectory(dof = 7)
        # jt          = trajlib.Polynomial_Trajectory(dimension = 7)

        # jt.capacity = 5
        qd          = trig.angles_standard_range(self.config.q)
        # jt.add_point(phi = 0.0, pos = qd, vel = np.zeros(7))
        jt.add_point(phi = 0.0, pos = self.config.q, vel = np.zeros(7))

        phi   = phi_start
        pos_traj.set_phi(phi)
        ori_traj.set_phi(phi)
        if relative:
            p0    = self.wrist_position() - pos_traj.current_position
            R0    = np.dot(self.wrist_orientation(), ori_traj.current_orientation.T)  
        else:
            p0    = np.zeros(3)
            R0    = np.eye(3)  
        
        phi       = phi + delta_phi
        stay      = True

        while (phi <= phi_end) and stay:
            if gen.equal(phi, phi_end):
                stay = False

            pos_traj.set_phi(phi)
            ori_traj.set_phi(phi)
            p = p0 + pos_traj.current_position
            R = np.dot(R0, ori_traj.current_orientation)
            self.set_target(p, R)
            self.config.qm = np.copy(self.config.q)
            self.ik.endeffector.reference_positions[0].rd = np.copy(self.xd)
            self.ik.endeffector.reference_orientations[0].rd = np.copy(self.Rd)
            err_old = self.ik.endeffector.error_norm
            q_dot   = self.ik.joint_speed()
            self.ik.configuration.q += q_dot
            if self.config.all_joints_in_range(self.ik.configuration.q):
                self.ik.forward_update()
                err_new = self.ik.endeffector.error_norm
                if err_new < err_old:
                    self.set_config(self.ik.configuration.q)
                    if self.inverse_update():
                        if not silent:
                            print
                            print "phi = ", phi, phi_end
                            print self.xd - self.wrist_position()
                            print self.Rd - self.wrist_orientation()
                            print self.ik.configuration
                            print self.config.q

                        jt.add_point(phi = phi - phi_start, pos = self.config.q)
                        #jt.plot()

            phi = phi + delta_phi
            if phi > phi_end:
                phi = phi_end
                stay = False

        jt.interpolate()

        return jt

    def project_to_js_vts_realtime(self,  pos_traj, ori_traj = None, phi_start = 0.0, duration = 10.0, phi_dot = None, max_speed = 1.0, relative = True, silent = True):
        '''
        projects the given taskspace pose trajectory into the jointspace using analytic inverse kinematics.
        The phase starts from phi_start and added by delta_phi in each step.
        at any time, if a solution is not found, the process stops
        '''
        keep_q = np.copy(self.config.q)

        phi_min = 5.0
        phi_max = 6.1
        if phi_dot == None:
            phi_dot = pos_traj.phi_end/duration

        if ori_traj == None:
            ori_traj = trajlib.Orientation_Trajectory()
            ori_traj.current_orientation = self.wrist_orientation()

        jt          = jtrajlib.Joint_Trajectory(dof = 7)
        # jt          = trajlib.Polynomial_Trajectory(dimension = 7)

        jt.capacity = 2
        qd          = trig.angles_standard_range(self.config.q)
        # jt.add_point(phi = 0.0, pos = qd, vel = np.zeros(7))
        jt.add_point(phi = 0.0, pos = np.copy(self.config.q), vel = np.zeros(7))
        if (not silent):
            print "Initial config:", (180.0/math.pi)*self.config.q


        phi   = phi_start
        pos_traj.set_phi(phi)
        ori_traj.set_phi(phi)
        if relative:
            p0    = self.wrist_position() - pos_traj.current_position
            R0    = np.dot(self.wrist_orientation(), ori_traj.current_orientation.T)  
        else:
            p0    = np.zeros(3)
            R0    = np.eye(3)  
        
        t0        = time.time()
        t         = 0.0
        tp        = 0.0   
        k         = 0.1      
        while (t < duration + 0.00001):
            t        = time.time() - t0
            dt       = t - tp
            tp       = t
            phi      = phi_start + phi_dot*t

            pos_traj.set_phi(phi)
            ori_traj.set_phi(phi)
            p = p0 + pos_traj.current_position
            R = np.dot(R0, ori_traj.current_orientation)
            self.set_target(p, R)
            self.ik.endeffector.reference_positions[0].rd    = np.copy(self.xd)
            self.ik.endeffector.reference_orientations[0].rd = np.copy(self.Rd)
            self.ik.endeffector.update_pose_error()            
            self.ik.endeffector.update_error_jacobian(self.ik)

            err_old = self.ik.endeffector.error_norm
            # q_dot   = self.ik.joint_speed()
            err = - k*self.ik.endeffector.pose_error + np.append(pos_traj.current_velocity, np.zeros(3))
            # err = - k*self.ik.endeffector.pose_error
            Je  =   self.ik.endeffector.EJ
            Je_dagger = np.linalg.pinv(Je)
            q_dot = np.dot(Je_dagger, err)

            etta    = self.feasible_joint_stepsize(direction = q_dot, max_speed = max_speed, ttr = dt)
            if (not silent) and (phi > phi_min) and (phi < phi_max):
                print
                print "phi = ", phi - phi_start
                print "q_dot: ", (180.0/math.pi)*q_dot
                print "etta:  ", etta
                
            self.ik.configuration.q += q_dot*etta
            assert self.config.all_joints_in_range(self.ik.configuration.q)
            self.ik.forward_update()
            err_new = self.ik.endeffector.error_norm
            if (not silent) and (phi > phi_min) and (phi < phi_max):
                print "I am here: joint are in range"
                print "Old Error = ", err_old
                print "New Error = ", err_new
            if err_new < err_old:
                self.set_config(self.ik.configuration.q)
                if (not silent) and (phi > phi_min) and (phi < phi_max):
                    print "I am here: IK could reduce error, Point Added."
                    print "ik config: ", self.ik.configuration
                    print self.xd - self.wrist_position()
                    print self.Rd - self.wrist_orientation()
                assert self.set_config(self.ik.configuration.q)
                jt.add_point(phi = phi - phi_start, pos = np.copy(self.config.q))
            else:
                if (not silent) and (phi > phi_min) and (phi < phi_max):
                    print "I am here: IK could not reduce error"
                self.config.qm = np.copy(self.ik.configuration.q)
                if self.move_towards_target(phi = self.config.q[0], optimize = True, max_speed = max_speed, ttr = dt):
                    self.ik.configuration.q = np.copy(self.config.q)
                    self.ik.forward_update()
                    if (not silent) and (phi > phi_min) and (phi < phi_max):
                        print
                        print "I am here: Analytic IK could get closer"
                        print "Final Config:", self.ik.configuration
                        print "Final Err=   ", self.ik.endeffector.error_norm
                        print self.xd - self.wrist_position()
                        print self.Rd - self.wrist_orientation()
                    jt.add_point(phi = phi - phi_start, pos = np.copy(self.config.q))
                else:
                    if (not silent) and (phi > phi_min) and (phi < phi_max):
                        print "I am here: Analytic IK could not get closer. Point not added :-("
               
        jt.interpolate()
        self.config.qm = 0.5*(self.config.qh + self.config.ql)
        self.set_config(keep_q)

        return jt

    def project_to_js_binary(self,  pos_traj, ori_traj, phi_start = 0.0, phi_end = 1.0, delta_phi = 0.1, k = 2.0, relative = True):
        '''
        projects the given taskspace pose trajectory into the jointspace using binary stepwise approach
        The phase starts from phi_start and added by delta_phi in each step.
        if a solution is not found, the phase is returned to the previous state (phi - d_phi) and 
        d_phi becomes half and is added to phi again
        if a solution is found, d_phi is multiplied by 2.0 provided it does not exceed given delta_phi
        The process continues until phi reaches phi_end and the corresponding jointspace trajectory is returned.
        '''
        if phi_end == None:
            phi_end = pos_traj.phi_end

        q_list     = [self.config.q]
        phi_list   = [0.0]

        d_phi = delta_phi
        phi   = phi_start
        pos_traj.set_phi(phi)
        ori_traj.set_phi(phi)
        if relative:
            p0    = self.wrist_position() - pos_traj.current_position
            R0    = np.dot(self.wrist_orientation(), ori_traj.current_orientation.T)  
        else:
            p0    = np.zeros(3)
            R0    = np.eye(3)  
        
        phi = phi + d_phi
        while (phi < phi_end) and (d_phi > 0.0001):
            pos_traj.set_phi(phi)
            ori_traj.set_phi(phi)
            p = p0 + pos_traj.current_position
            R = np.dot(R0, ori_traj.current_orientation)
            self.set_target(p, R)
            if self.inverse_update():
                q_list.append(self.config.q) 
                phi_list.append(phi - phi_start)
                d_phi = d_phi*k
                if d_phi > delta_phi:
                    d_phi = delta_phi
                phi = phi + d_phi
            else:
                phi   = phi - d_phi
                d_phi = d_phi/k            
                phi   = phi + d_phi
        if d_phi <= 0.0001:
            print "Warning from PR2_ARM.project_to_js(): The trajectory could not be completed!"
        
        # Create a joint trajectory by connecting the key points in the jointspace:
        n = len(q_list)
        q_dot_list      = [None for i in range(n)]
        q_dot_list[0]   = np.zeros(7)
        q_dot_list[n-1] = np.zeros(7)

        jt          = trajlib.Polynomial_Trajectory(dimension = 7)
        jt.capacity = 5
    
        for i in range(n):
            jt.add_point(phi = phi_list[i], pos = q_list[i], vel = q_dot_list[i])

        jt.interpolate()

        return jt

    
    def project_to_js_keypoints(self, ts_traj, num_key_points = 10, smooth = True, relative = True):
        '''
        ts_traj is a cartesian trajectory of the endeffector in the operational taskspace.
        this function projects the given trajectory into the jointspace of PR2 arm and returns a 7 dim trajectory 
        in the jointspace
        while the objective function is expected to be minimized in each key point.
        If there is no solution for any of the keypoints in the path(trajectory), then that point will be skipped.
        '''
        n          = num_key_points
        assert n > 1   # n must be at least 2 or greater

        jt = trajlib.Polynomial_Trajectory(dimension = 7)
        if relative:
            p0 = self.wrist_position()
        else:
            p0 = np.zeros(3)

        d_phi      = ts_traj.phi_end/(n - 1)
        for i in range(n):
            phi = i*d_phi
            ts_traj.set_phi(phi)
            pos = ts_traj.current_position
            self.set_target(p0 + pos, self.Rd)
            if self.inverse_update():
                jt.add_point(phi, self.config.q)
            else:
                print "Solution not found for key point number ", i, ". Point skipped!"

        if n == 0:
            print "All points skipped! No solution found for any of the key points"
            return False
    
        lsi = len(jt.segment) - 1
        lpi = len(jt.segment[lsi].point) - 1
        jt.segment[0].point[0].vel     = np.zeros(7)
        jt.segment[lsi].point[lpi].vel = np.zeros(7)

        jt.interpolate()
        if smooth:
            jt.consistent_velocities()
        
        return jt

    def permission_set_position(self):
        """
        This function finds and returns the set from which q0 is allowed to be chosen so that 
        joint angles q0 , q2 and q3 in the analytic solution to the inverse kinematic problem are in their range. 
        Consider that being q0 in the permission set, does not guarantee that all q0, q2 and q3 are in their ranges, but
        it means that if q0 is out of permission set, one of the joints q0, q2 or q3 will definitely be out of their 
        feasible range.
        In other words, q0 being in perm. set, is a necessary but not sufficient condition for three joints 
        q0, q2 and q3 to be in their range.
        Permission set is broader than "confidence set" which ensures all q0, q2 and q3 to be in range.
        (has both necessary and sufficient conditions)
        The output depends on the defined joint limits and the desired endeffector pose but does not depend 
        on the current position of the joints.
        """
        if self.Phi != None:
            return self.Phi

        [r2, ro2, R2, T2, alpha, betta, gamma, sai] = self.target_parameters
        [Q, Q2, d42, d44, a00, d22_plus_d44, foura00d44, alpha] = self.additional_dims

        # feasibility set for v imposed by theta1

        int_theta1 = interval([self.config.ql[1],self.config.qh[1]])
        int_lnda   = imath.cos(int_theta1)
        int_lnda2   = int_lnda**2

        AA = np.array([[alpha*d44, d44*betta - 2*d42 , - self.d2**2 + d44*(gamma -1)],
                          [0.0 , 2*self.xd[2]*self.d4 , 2*self.xd[2]*self.d2],   
                          [- d44*(1+alpha) , -betta*d44 , - self.xd[2]**2 + d44*(1-gamma) ]])

        int_alpha = interval(AA[0,0])*int_lnda2 + interval(AA[1,0])*int_lnda + interval(AA[2,0])
        int_betap = interval(AA[0,1])*int_lnda2 + interval(AA[1,1])*int_lnda + interval(AA[2,1])
        int_gamma = interval(AA[0,2])*int_lnda2 + interval(AA[1,2])*int_lnda + interval(AA[2,2])
    
        (alpha_l, alpha_h) = int_alpha[0]
        (betap_l, betap_h) = int_betap[0]
        (gamma_l, gamma_h) = int_gamma[0]

        Vp_1l = gen.solve_quadratic_inequality(- alpha_l, - betap_l, -gamma_l)
        Vp_1h = gen.solve_quadratic_inequality(  alpha_h,   betap_h,  gamma_h)
        Vn_1l = gen.solve_quadratic_inequality(- alpha_l, - betap_h, -gamma_l)
        Vn_1h = gen.solve_quadratic_inequality(  alpha_h,   betap_l,  gamma_h)

        V1 = (Vp_1l & Vp_1h & interval([0.0,1.0])) | (Vn_1l &  Vn_1h & interval([-1.0,0.0]))

        # Finding wh,wl:

        int_theta2 = interval([self.config.ql[2],self.config.qh[2]])
        int_w   = imath.sin(int_theta2)**2
        (wl, wh) = int_w[0]

        #Finding V2l, V2h

        V2l = gen.solve_quadratic_inequality(alpha + wl, betta, gamma - wl) & interval([-1.0, 1.0])
        V2h = gen.solve_quadratic_inequality(- alpha - wh, - betta, wh - gamma) & interval([-1.0, 1.0])

        #Finding V2

        V2 = V2l & V2h

        #Finding V3

        int_theta3 = interval([self.config.ql[3],self.config.qh[3]])
        V3         = imath.cos(int_theta3)

        #Finding V

        V = V3 & V2 & V1

        #Finding Ui

        denum = 2*self.a0*math.sqrt(r2)
        a     = R2/denum
        b     = 2*self.d2*self.d4/denum

        Phi1_3 = interval()
        nv = len(V)
        for i in range(0, nv):
            Ui = interval(a) - interval(b)*interval(V[i])
            (uli, uhi) = Ui[0]            

            zl = trig.arcsin(uli)
            zh = trig.arcsin(uhi)

            B1 = trig.standard_interval(zl - sai, zh - sai)
            B2 = trig.standard_interval(math.pi- zh - sai, math.pi- zl - sai)

            Phi1_3 = Phi1_3 | B1 | B2    

        #Finding P_phi

        Phi0 = interval([self.config.ql[0], self.config.qh[0]])
        
        self.Phi = gen.connect_interval(Phi0 & Phi1_3)

        return self.Phi


    def delta_phi_interval(self):
        '''
        Updates the feasible interval for the growth of the redundant parameter according to
        the specified joint limits and the current value of the joints
        '''
        if self.Delta == None:
            J    = self.joint_jacobian()
            self.Delta  = self.permission_set_position() - interval(self.config.q[0])  # set initial Delta based on the position permission set for phi

            for i in range(0, 7):
                if (not gen.equal(J[i], 0.0)) and (not gen.equal(self.config.w[i], 0.0)):  # if Ji and wi are not zero
                    d1  = (self.config.ql[i] - self.config.q[i])/J[i]    
                    d2  = (self.config.qh[i] - self.config.q[i])/J[i]    
                    dli = gen.binary_choice(d1,d2,J[i])
                    dhi = gen.binary_choice(d2,d1,J[i])

                    if gen.equal(dli, 0.0):
                        dli = 0.0
                    if gen.equal(dhi, 0.0):
                        dhi = 0.0
                    assert dli <= 0.0
                    assert dhi >= 0.0
                    self.Delta   = self.Delta & interval([dli, dhi])
                    if len(self.Delta) == 0:
                        print "Error: self.Delta is empty:"
                        print "Initial Delta : ", self.permission_set_position() - interval(self.config.q[0])
                        print "interval([dli, dhi]): ", interval([dli, dhi])
                            

        return self.Delta
        


