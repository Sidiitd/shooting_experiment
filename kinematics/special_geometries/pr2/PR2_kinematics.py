'''   Header
@file:          PR2_kinematics.py
@brief:    	    Contains specific functions that define all geometric and kinematic parameters for PR2 robot

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
@version:	    0.5
Last Revision:  14 November 2012
References:     
                [1] Jabref Key: 2008_arti_Shimizu.Kakuya.ea_Analyticala
'''

import __init__
__init__.set_file_path( False )


from sympy import Symbol, simplify
import numpy, math
import packages.nima.robotics.kinematics.kinematicpy.manipulator_library as mnlib
import packages.nima.robotics.kinematics.kinematicpy.inverse_kinematics  as iklib 
import packages.nima.mathematics.trigonometry as trig
import packages.nima.mathematics.vectors_and_matrices as vecmat


epsilon = 0.0000001
drc     = math.pi/180.00


def link_T(theta,alpha,a,d):

    T_theta = numpy.array([ [ math.cos(theta), -math.sin(theta), 0.0, 0.0 ],
                       [ math.sin(theta),  math.cos(theta), 0.0, 0.0 ],
                       [    0.0,             0.0,     1.0, 0.0 ],
                       [    0.0,             0.0,     0.0, 1.0 ] ])

    T_alpha = numpy.array([ [ 1.0,     0.0,            0.0,     0.0 ],
                       [ 0.0, math.cos(alpha), -math.sin(alpha), 0.0 ],
                       [ 0.0, math.sin(alpha),  math.cos(alpha), 0.0 ],
                       [ 0.0,     0.0,            0.0,     1.0 ] ])

    T_trans = numpy.array([ [ 1.0, 0.0, 0.0, a ],
                       [ 0.0, 1.0, 0.0, 0.0 ],
                       [ 0.0, 0.0, 1.0, d ],
                       [ 0.0, 0.0, 0.0, 1.0 ] ])

    return numpy.dot(numpy.dot(T_theta, T_trans), T_alpha)


def round(x):
    
    if abs(x) < epsilon:
        y = 0
    elif abs(x - 1) < epsilon:
        y = 1
    elif abs(x + 1) < epsilon:
        y = -1
    else:
        y = x    
    return y    

def assert_equality(x,y):
    '''
    checks if x and y are equal removing the machine error
    '''
    assert (abs(x-y) < epsilon)


def transfer_DH_standard(theta, alpha, a, d, q):
    s  = math.sin(theta + q)
    c  = math.cos(theta + q)
    sa = math.sin(alpha)
    ca = math.cos(alpha)
    
    return numpy.array([[  c, -ca*s,  sa*s, a*c ],
                        [  s,  ca*c, -sa*c, a*s ],
                        [  0,  sa  ,  ca  , d   ],
                        [  0,  0   ,  0   , 1   ]])

def rot_z(q):
    # Return a transfer matrix corresponding to rotation around z axis
    c = math.cos(q)
    s = math.sin(q)
    return numpy.array([[  c, -s, 0, 0 ],
                        [  s,  c, 0, 0 ],
                        [  0,  0, 1, 0 ],
                        [  0,  0, 0, 1 ]])


class PR2_ARM():

    def forward_update(self):        
        self.A = []
        '''        
        self.A.append(transfer_DH_standard( 0.0       , - math.pi/2, 0.0, 0.0       ,   self.qr[0]))
        self.A.append(transfer_DH_standard( 0.0       ,   math.pi/2, 0.0, 0.0       ,   self.qr[1]))
        self.A.append(transfer_DH_standard( 0.0       , - math.pi/2, 0.0, self.d2   ,   self.qr[2]))
        self.A.append(transfer_DH_standard( 0.0       ,   math.pi/2, 0.0, 0.0       ,   self.qr[3]))
        self.A.append(transfer_DH_standard( 0.0       , - math.pi/2, 0.0, self.d4   ,   self.qr[4]))
        self.A.append(transfer_DH_standard( 0.0       ,   math.pi/2, 0.0, 0.0       ,   self.qr[5]))
        self.A.append(transfer_DH_standard( 0.0       ,   0.0      , 0.0, 0.0       ,   self.qr[6]))
        '''        

        self.A.append(link_T( self.qr[0]       , - math.pi/2, self.a0, 0.0 ))
        self.A.append(link_T( self.qr[1]       ,   math.pi/2, 0.0, 0.0       ))
        self.A.append(link_T( self.qr[2]       , - math.pi/2, 0.0, self.d2   ))
        self.A.append(link_T( self.qr[3]       ,   math.pi/2, 0.0, 0.0       ))
        self.A.append(link_T( self.qr[4]       , - math.pi/2, 0.0, self.d4   ))
        self.A.append(link_T( self.qr[5]       ,   math.pi/2, 0.0, 0.0       ))
        self.A.append(link_T( self.qr[6]       ,   0.0      , 0.0, 0.0       ))

        T = numpy.eye(4)
        # T Transfer matrix of the Arm (from base of arm to tip)
        for X in self.A:
            T = numpy.dot(T, X)
        
        self.end_right_arm = numpy.copy(T)


    def inverse_update(self, T_d):
        '''
        Corrects the joint angles to fulfil kinematic constraints (T6 = T_d) 
        The new joint angles will be as close as possible to the current joint angles: (self.qr)
        '''
        tt0 = self.qr[0] 
        tt3 = self.qr[3] 



    def solve_inverse_kinematics(self, T_d, tt0): 
     
        '''
        Finds all the solutions of the Inverse Kinematic problem where theta0 = tt0
        theta0 is the redundancy parameter

        Provides a solution set for PR2 arm for the desired pose given by T_d
        tt0 is the redundancy parameter and can be arbitrary chosen.
        ''' 
        solution_set = []

        x_d = T_d[0:3,3]
        R_d = T_d[0:3,0:3]

        x_sw = x_d - [self.a0*math.cos(tt0), self.a0*math.sin(tt0), 0]  

        u    = x_sw/numpy.linalg.norm(x_sw)
        u_X  = vecmat.skew(u)


        c3 = (numpy.linalg.norm(x_sw)**2 - self.d2**2 - self.d4**2)/(2*self.d2*self.d4) # According to: ref[1].eq.12

        A  = self.d2 + c3*self.d4

        i = 0
        while i < 2:
            theta3 = (2*i-1)*trig.arccos(c3)
            s3     = math.sin( theta3)
            B = self.d4*s3
            sol1 = trig.solve_system(1, A, B, x_sw[0], x_sw[1], x_sw[2])
            if len(sol1) > 0:
                (theta0_ref, theta1_ref) = sol1[0]
                c0_ref = math.cos(theta0_ref)
                s0_ref = math.sin(theta0_ref)
                c1_ref = math.cos(theta1_ref)
                s1_ref = math.sin(theta1_ref)
            
                T01_ref = transfer_DH_standard( 0.0       , - math.pi/2, 0.0, 0.0     ,   theta0_ref)
                T12_ref = transfer_DH_standard( 0.0       ,   math.pi/2, 0.0, 0.0     ,   theta1_ref)
                T23_ref = transfer_DH_standard( 0.0       , - math.pi/2, 0.0, self.d2 ,   0         )

                R01_ref = T01_ref[0:3,0:3]
                R12_ref = T12_ref[0:3,0:3]
                R23_ref = T23_ref[0:3,0:3]

                R03_ref = numpy.dot(numpy.dot(R01_ref,R12_ref),R23_ref)

                As = numpy.dot(u_X, R03_ref)
                Bs = - numpy.dot(numpy.dot(u_X, u_X), R03_ref)
                Cs =   - Bs + R03_ref

                #finding phi according to the given theta0
                s00 = math.sin(tt0)
                c00 = math.cos(tt0)

                AA = As[0,1]*s00 - As[1,1]*c00
                BB = Bs[0,1]*s00 - Bs[1,1]*c00         
                CC = Cs[0,1]*s00 - Cs[1,1]*c00         

                sol2 = trig.solve_equation(1, [BB,AA,CC])  # returns the solution set for phi
                k = 0
                while k < len(sol2):
                    phi = sol2[k]

                    R_sai = numpy.eye(3) + math.sin(phi)*u_X + (1 - math.cos(phi))*numpy.dot(u_X, u_X)  
                    R03 = numpy.dot(R_sai, R03_ref)

                    t0 = R03[1,1]/R03[0,1]    
                    c1 = - R03[2,1]
                    t2 = - R03[2,2]/R03[2,0]
                
                    theta0 = tt0 
                    s0 = math.sin(theta0)
                    c0 = math.cos(theta0)
                    m = 0
                    while m < 2:
                        theta1 = (2*m - 1)*math.acos(c1) 
                        s1    = math.sin(theta1)
                        s10   = s1*s0  
                        c1    = math.cos(theta1)
                        c10   = c1*c0
                        c0s1  = c0*s1

                        c30s1 = c3*c0s1 
                        c31   = c3*c1      
                        c3s10 = c3*s10

                        n = 0
                        while n < 2:
                            theta2 = math.atan(t2) + n*math.pi
                            s2     = math.sin(theta2)
                            s20    = s2*s0
                            s21    = s2*s1
                            s320   = s3*s20

                            c0s2   = c0*s2
                            c0s32  = c0s2*s3
                            c10s2  = c10*s2
                            c1s20  = c1*s20
                            c2     = math.cos(theta2)
                            c20    = c2*c0
                            c21    = c2*c1
                            c210   = c21*c0
                            c210s3 = c210*s3
                            c21s0  = c21*s0
                            c21s20 = c21*s20
                            c21s30 = c21s0*s3
                            c2s0   = c2*s0
                            c2s1   = c2*s1
                            c2s31  = c2s1*s3
    
                            X =  c0*self.a0 + c0s1*self.d2 + (c30s1 + c210s3 - s320)*self.d4

                            Y =  s0*self.a0 + s10*self.d2 + (c3s10 + c0s32 + c21s30)*self.d4

                            Z =  c1*self.d2 + (c31 - c2s31)*self.d4
                                        
                            '''
                            R03_2 = numpy.array([[-s20 + c210  , -c0s1 , -c2s0 - c10s2],
                                                 [ c0s2 + c21s0, -s10  ,  c20 - c1s20 ],
                                                 [ -c2s1       , -c1   ,  s21         ]])    

                            if vecmat.equal(R03, R03_2):

                            '''

                            if vecmat.equal([X, Y, Z], x_d):
                                T34 = transfer_DH_standard( 0.0       ,   math.pi/2, 0.0, 0.0   ,   theta3)
                                R34 = T34[0:3,0:3]

                                Aw = numpy.dot(numpy.dot(R34.T, As.T), R_d)
                                Bw = numpy.dot(numpy.dot(R34.T, Bs.T), R_d)
                                Cw = numpy.dot(numpy.dot(R34.T, Cs.T), R_d)
                                R47 = math.sin(phi)*Aw + math.cos(phi)*Bw + Cw

                                t4 = R47[1,2]/ R47[0,2]
                                c5 = R47[2,2]
                                t6 = - R47[2,1]/R47[2,0]
                                o = 0
                            else:
                                o = 2

                            while o < 2:
                                theta4 = math.atan(t4) + o*math.pi
                                p = 0
                                while p < 2:
                                    theta5 = (2*p - 1)*math.acos(c5) 
                                    q = 0
                                    while q < 2:
                                        theta6 = math.atan(t6) + q*math.pi 

                                        #Check Ref.1.eq.11

                                        T45 = transfer_DH_standard( 0.0       , - math.pi/2, 0.0, self.d4 ,   theta4)
                                        T56 = transfer_DH_standard( 0.0       ,   math.pi/2, 0.0, 0.0     ,   theta5)
                                        T67 = transfer_DH_standard( 0.0       ,   0.0      , 0.0, 0.0 ,   theta6)

                                        R45 = T45[0:3,0:3]
                                        R56 = T56[0:3,0:3]
                                        R67 = T67[0:3,0:3]

                                        R47_2 = numpy.dot(numpy.dot(R45, R56), R67)

                                        if vecmat.equal(R47, R47_2) :
                                            solution_set.append([theta0, theta1, theta2, theta3, theta4, theta5, theta6])

                                        q = q + 1
                                    p = p + 1
                                o = o + 1
                            n = n + 1
                        m = m + 1
                    k = k + 1

            i = i + 1    

        return solution_set


    def __init__(self, a0 = 0.1, d2 = 0.4, d4 = 0.321):

        self.qt = numpy.zeros((4))
        self.qt[1] = drc*140.0    
        self.qt[2] = drc*140.0    

        self.qr = numpy.zeros((7))
        self.ql = numpy.zeros((7))
    
        self.a0 = a0
        self.d2 = d2
        self.d4 = d4

        self.l_se = [0.0, - self.d2, 0.0]
        self.l_ew = [0.0, 0.0, self.d4]

       
class PR2_Arm_Symbolic():
    def __init__(self):

        n = 7

        c = [Symbol('c' + str(i)) for i in range(n)]
        s = [Symbol('s' + str(i)) for i in range(n)]
        a = [Symbol('a0'), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        d = [0.0, 0.0, Symbol('d2'), 0.0, Symbol('d4'), 0.0, 0.0]
        alpha = [- math.pi/2, math.pi/2, - math.pi/2, math.pi/2, - math.pi/2, math.pi/2, 0.0]    
        
        ca    = [math.cos(alpha[i]) for i in range(n)]
        sa    = [math.sin(alpha[i]) for i in range(n)]

        for i in range(len(ca)):
            ca[i] = round(ca[i])
            sa[i] = round(sa[i])
        
        # A[i] transfer matrix from link i-1 to i  according to standard DH parameters:
        self.A = [numpy.array([[ c[i],  -ca[i]*s[i],  sa[i]*s[i], a[i]*c[i] ], 
                               [ s[i],   ca[i]*c[i], -sa[i]*c[i], a[i]*s[i] ],
                               [ 0   ,   sa[i]     ,  ca[i]     , d[i]      ],
                               [ 0   ,   0         ,  0         , 1         ]]) for i in range(n)]
                               
        # B[i] transfer matrix from link i to i-1 or B[i] = inv(A[i])
        self.B = [numpy.array([[        c[i],         s[i], 0     ,  0          ], 
                               [ -ca[i]*s[i],   ca[i]*c[i], sa[i] , -d[i]*sa[i] ],
                               [  ca[i]*s[i],  -sa[i]*c[i], ca[i] , -d[i]*ca[i] ],
                               [  0         ,   0         , 0     ,  1          ]]) for i in range(n)]

        # R[i] rotation matrix from link i-1 to i  according to standard DH parameters:
        self.R = [numpy.array([[ c[i],  -ca[i]*s[i],  sa[i]*s[i]], 
                               [ s[i],   ca[i]*c[i], -sa[i]*c[i]],
                               [ 0   ,   sa[i]     ,  ca[i]     ]]) for i in range(n)]

        # T[i] transfer matrix from link -1(ground) to i
        self.T = numpy.copy(self.A)
        for i in range(n-1):
            self.T[i + 1] = numpy.dot(self.T[i],self.A[i + 1])

        # Desired Pose:
        T_d = numpy.array([[ Symbol('nx'), Symbol('sx') , Symbol('ax') , Symbol('px') ], 
                           [ Symbol('ny'), Symbol('sy') , Symbol('ay') , Symbol('py') ],
                           [ Symbol('nz'), Symbol('sz') , Symbol('az') , Symbol('pz') ],
                           [ 0           , 0            ,  0           , 1            ]])

        self.x_d = T_d[0:3, 3]
        self.R_d = T_d[0:3, 0:3]

        self.T7 = self.T[6]
        self.x7 = self.T7[0:3, 3]
        self.R7 = self.T7[0:3, 0:3]
    
        self.H = numpy.copy(self.T)
        self.H[n - 1] = numpy.copy(T_d)
        
        # H[i] transfer matrix from link -1(ground) to i calculated from inverse transform
        for i in range(n-1):
            self.H[n - i - 2] = numpy.dot(self.H[n - i - 1], self.B[n - i - 1])

        
def symbolic_help(code):
    '''
    This function applies symbolic PR2 Arm to state (Reference[1] eq. 14) in terms of geometric papameters.
    This helps to find a parametric formulation for the reference joint angles theta1 and theta2  
    '''
    arm = PR2_Arm_Symbolic()

    #x_sw1 = arm.x_d - arm.l_bs - numpy.dot(arm.R_d, arm.l_wt)

    R23 = arm.R[2]

    if code == 1:
        # substituting theta3 = 0 to find the reference rotation matrix R23
        R23[0,0] = R23[0,0].subs('c2',1)
        R23[0,2] = R23[0,2].subs('s2',0)
        R23[1,0] = R23[1,0].subs('s2',0)
        R23[1,2] = R23[1,2].subs('c2',1)
        
        R02 = numpy.dot(arm.R[0],arm.R[1])
        R03 = numpy.dot(R02, R23)
        x_sw2 = numpy.dot(R03, arm.l_se + numpy.dot(arm.R[3], arm.l_ew))

        print 
        print " The following equations help you to find theta0 and theta1 in the reference posture."
        print " s0,c0,s1 and c1 represent sine and cosine of theta0 and theta1 respectively "
        print 

        print x_sw1[0]," = ", x_sw2[0]
        print x_sw1[1]," = ", x_sw2[1]
        print x_sw1[2]," = ", x_sw2[2]

    if code == 2:

        # This code gives you matricres As, Bs and Cs

        R23[0,0] = R23[0,0].subs('c2',1)
        R23[0,2] = R23[0,2].subs('s2',0)
        R23[1,0] = R23[1,0].subs('s2',0)
        R23[1,2] = R23[1,2].subs('c2',1)
        
        R02 = numpy.dot(arm.R[0],arm.R[1])
        R03 = numpy.dot(R02, R23)
        x_sw2 = numpy.dot(R03, arm.l_se + numpy.dot(arm.R[3], arm.l_ew))

        print 
        print " The following equations help you to find As, Bs and Cs matrices according to Ref.1.eq.15"
        print " as a symbolic formulation in terms of the input parameters"
        print 
        u_sw = numpy.array([Symbol('ux'), Symbol('uy'), Symbol('uz')])
        
        uX = vecmat.skew(u_sw)
        # According to Ref.1.eq.15
        As =   numpy.dot(uX, R03)   
        Bs = - numpy.dot(numpy.dot(uX,uX), R03)
        Cs = - Bs + R03
        print 
        print 'As[1,1] = ', As[1,1]
        print 'Bs[1,1] = ', Bs[1,1]
        print 'Cs[1,1] = ', Cs[1,1]
        print 
        print 'As[0,1] = ', As[0,1]
        print 'Bs[0,1] = ', Bs[0,1]
        print 'Cs[0,1] = ', Cs[0,1]
        print 
        print 'As[2,1] = ', As[2,1]
        print 'Bs[2,1] = ', Bs[2,1]
        print 'Cs[2,1] = ', Cs[2,1]
        print 
        print 'As[2,2] = ', As[2,2]
        print 'Bs[2,2] = ', Bs[2,2]
        print 'Cs[2,2] = ', Cs[2,2]
        print 
        print 'As[2,0] = ', As[2,0]
        print 'Bs[2,0] = ', Bs[2,0]
        print 'Cs[2,0] = ', Cs[2,0]

    if code == 3:
        
       
        x70 = [arm.x7[i].subs('c0*c1*c2','c210').subs('c0*c3*s1','c30s1').subs('s0*s2','s20').subs('c1*s0*s3','c1s30') for i in range(0,3)]
        x71 = [x70[i].subs('c2*s0','c2s0').subs('c0*c1*c2','c210').subs('c0*c3*s1','c30s1').subs('s0*s2','s20') for i in range(0,3)]
        x72 = [x71[i].subs('c1*s0*s3','c1s30').subs('c1*c2s0','c21s0').subs('c3*s0*s1','c3s10').subs('c1*c2s0','c21s0') for i in range(0,3)]
        x73 = [x72[i].subs('c0*s2','c0s2').subs('s0*s1*s3','s310').subs('c0*c2','c20').subs('c1*s20','c1s20') for i in range(0,3)]
        x74 = [x73[i].subs('c0*s1*s3','c0s31').subs('c2*c3*s1','c32s1').subs('c2*s1*s3','c2s31').subs('c1*c3','c31') for i in range(0,3)]
        x75 = [x74[i].subs('s1*s2*s4','s421').subs('c1*s3','c1s3').subs('c0s2*c1','c10s2').subs('s0*s1','s10') for i in range(0,3)]
        

        print 'X = ', x75[0]
        print
        print 'Y = ', x75[1]
        print
        print 'Z = ', x75[2]
        print
        '''
        Now we simplify them:
        '''
        x76 = [simplify(x75[i]) for i in range(0,3)]

        print 'X = ', x76[0]
        print
        print 'Y = ', x76[1]
        print
        print 'Z = ', x76[2]

        '''
        Formulations are finally simplified to:

        X =  c0*a0 + c0s1*d2 + (c30s1 + c210s3 - s320)*d4

        Y =  s0*a0 + s10*d2 + (c3s10 + c0s32 + c21s30)*d4

        Z =  c1*d2 + (c31 - c2s31)*d4
        

        '''


    if code == 4:
        '''
        We try to find the formulations for R03 and x03, R47 and x47
        '''
        T03 = arm.T[2]
        R03 = T03[0:3,0:3]
        x03 = T03[0:3,3]

        print 'X = ', x03[0]
        print
        print 'Y = ', x03[1]
        print
        print 'Z = ', x03[2]
        print
        '''
        For X03 The output must be:
        
        X =  a0*c0 + c0*d2*s1

        Y =  a0*s0 + d2*s0*s1

        Z =  c1*d2


        And for R03 we have:
        '''

        print 'R03[0,0] = ', R03[0,0]
        print 'R03[0,1] = ', R03[0,1]
        print 'R03[0,2] = ', R03[0,2]
        print 
        print 'R03[1,0] = ', R03[1,0]
        print 'R03[1,1] = ', R03[1,1]
        print 'R03[1,2] = ', R03[1,2]
        print 
        print 'R03[2,0] = ', R03[2,0]
        print 'R03[2,1] = ', R03[2,1]
        print 'R03[2,2] = ', R03[2,2]


        '''
        For R03 The output must be simplified to:
        
        R03[0,0] =  -s20 + c210
        R03[0,1] =  -c0s1
        R03[0,2] =  -c2s0 - c10s2

        R03[1,0] =  c0s2 + c21s0
        R03[1,1] =  -s10
        R03[1,2] =  c20 - c1s20

        R03[2,0] =  -c2s1
        R03[2,1] =  -c1
        R03[2,2] =  s21
        '''    

        """
        '''
        Now we simplify them:
        '''
        x76 = [simplify(x75[i]) for i in range(0,3)]

        print 'X = ', x76[0]
        print
        print 'Y = ', x76[1]
        print
        print 'Z = ', x76[2]

        '''
        Formulations are finally simplified to:

        X =  c0*a0 + c0s1*d2 + (c30s1 + c210s3 - s320)*d4

        Y =  s0*a0 + s10*d2 + (c3s10 + c0s32 + c21s30)*d4

        Z =  c1*d2 + (c31 - c2s31)*d4
        

        '''
        """


def main():

    srs = PR2_ARM(a0=0)

    srs.qr = numpy.array([-0.5, 0.5 + math.pi/2, 0.5, -0.5, 0.5, -0.5, 0.5])
    srs.qr = drc*numpy.array([-45, 7, -51, -22, -90, 80, 15])
    
    srs.forward_update()

    #srs.end_right_arm[1,3] = srs.end_right_arm[1,3] - 0.188 
    
    srs.solve_inverse_kinematics_explained(srs.end_right_arm, srs.qr[0])

    print srs.end_right_arm
    '''
    srs.solve_inverse_kinematics_explained(srs.end_right_arm, phi = 0.1801855)
    print "End of Right Arm:"
    print srs.end_right_arm
    '''

def main_2():

    #srs = PR2_ARM(a0 = 0.1, d2 = 0.4, d4 = 0.321)
    srs = PR2_ARM(a0 = 0.5, d2 = 1.4, d4 = 8.21)
    #srs = SRS_ARM()

    srs.qr = drc*numpy.array([45, -10, 30, -45, 20, 15, -10])
    #srs.qr = drc*numpy.array([-45, 7, -51, -22, -90, 80, 15])
    print 'q1 = ', srs.qr
    
    srs.forward_update()
    end_right_arm = numpy.copy(srs.end_right_arm)


    all_solutions = srs.solve_inverse_kinematics(srs.end_right_arm, tt0 = 45*drc)

    for i in range(0 ,len(all_solutions)):
        print all_solutions[i]
        srs.qr = all_solutions[i]

        srs.forward_update()
        print 
        '''
        print "End of Right Arm:"
        print 
        print srs.end_right_arm
        print 
        print end_right_arm
        '''
        if vecmat.equal(srs.end_right_arm, end_right_arm):
            print "Successful :-)"
        else:
            print "Failed :-("

def main_3():
    symbolic_help(4)    
     
if __name__ == "__main__" :
    
    main_2()

