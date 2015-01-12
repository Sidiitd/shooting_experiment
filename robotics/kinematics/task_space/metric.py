## @file        	metric.py
## @brief:    	    This module provides a class representing the residual error between 
#                   the actual and desired endeffector poses including methods for calculating residual functions based on various conventions for 
#                   both position and orientation.
#  @author      	Nima Ramezani Taghiabadi 
#
#               	PhD Researcher 
#               	Faculty of Engineering and Information Technology 
#               	University of Technology Sydney (UTS) 
#               	Broadway, Ultimo, NSW 2007, Australia 
#               	Phone No. :   04 5027 4611 
#               	Email(1)  : nima.ramezani@gmail.com 
#               	Email(2)  : Nima.RamezaniTaghiabadi@uts.edu.au 
#  @version     	1.0
# 
#  Last Revision:  	11 January 2015

import numpy, math

from packages.nima.mathematics import vectors_and_matrices as vecmat
from packages.nima.mathematics import quaternions
from packages.nima.mathematics import rotation
from packages.nima import general as gen

key_dic = {
    'DiRoMa'        : 'Difference of Rotation Matrices',
    'DiQu'          : 'Difference of Quaternions',
    'DiNoQu'        : 'Non-redundant Difference of Quaternions',
    'DiOrVe'        : 'Difference of Orientation Vectors',
    'ReRoMa'        : 'Trace of Relative Rotation Matrix',
    'ReRoMaTr'      : 'Trace of Relative Rotation Matrix',
    'AxInPr     '   : 'Axis Inner Product',
    'ReQu'          : 'Relative Orientation Vector',
    'ReOrVe'        : 'Relative Orientation Vector',
    'ReRoAn'        : 'Relative Rotation Angle'}

type_dic = {
    'DiRoMa'        : 'matrix',
    'DiQu'          : 'quaternion',
    'DiNoQu'        : 'quaternion',
    'DiOrVe'        : 'vector',
    'ReRoMa'        : 'matrix',
    'ReRoMaTr'      : 'matrix',
    'ReQu'          : 'quaternion',
    'ReOrVe'        : 'vector',
    'ReRoAn'        : 'angle'}

## Class Constructor:
class Metric_Settings():
    '''
    '''
    def __init__(self, representation = "Cartesian Coordinates", metric_type = "differential"):
    
        self.metric_type = metric_type

        self.representation = representation
        
        self.generating_function = 'phi/m'
    
        '''
        Property "power" determines the power of elements of basis error in the final vector of errors:
        Please refer to the comments of property: "W" in this file.

            0: Not considered for the corresponding coordinate
            1:  rd - ra
            2: (rd - ra)^2
            3: (rd - ra)^3
            .
            .
            .
            
         where:
            "ra" is the actual position
            "rd" is the desired position

        and r can be replaced by: X, Y or Z
        '''
        self.power   = numpy.array([1, 1, 1])
        
        '''
        property "W" is a 3 X 3 Weighting matrix. This matrix will be multiplied by the basis error and basis jacobian.  
    
        Matrix W is by default the identity matrix defining 3 constraints as:

            Xd - X = 0
            Yd - Y = 0
            Zd - Z = 0

        Example 1:
    
        "power" array = [1, 1, 1] and "W" is a (3 X 3) matrix
    
                                      X   Y   Z

        1st Row of "W":               1   0   0       (Xd - Xa) = 0
        2nd Row of "W":               0   1   0       (Yd - Ya) = 0
        3rd Row of "W":               0   0   1       (Zd - Za) = 0

        Example 2:
        
        "power" array = [2, 2, 1] and "W" is a (2 X 3) matrix
        
                                    X   Y   Z
    
        1st Row of "W":             1   1   0       (Xd - Xa)^2 + (Yd - Ya)^2 = 0
        2nd Row of "W":             0   0   1       (Zd - Za) = 0
    
        Example 3: (When only two coordinations "X" and "Z" are important to be identical)
        In this example, it is important to also set the property "required_identical_coordinate" to: [True, False, True] 
        Please refer to the of comments for property "required_identical_coordinate".

        "power" array = [1, 0, 1] and "W" is a (2 X 3) matrix
        
                                      X   Y   Z
    
        1st Row of "W":               1   0   0       (Xd - Xa) = 0
        2nd Row of "W":               0   0   1       (Zd - Za) = 0
    
        the same for the orientation ...    
            
        '''
        self.weight  = numpy.eye(3)

        self.offset  = numpy.zeros((3))

        '''
        "self.required_identical_coordinate" is an array of booleans and indicates which coordinates (x, y ,z) should be considered
        as a criteria in determining the confirmity of the actual and desired positions and orientations.
        For example if "required_identical_coordinate" = [True, False, True] the actual and desired positions are considered as identical only when 
        their  "x" and "z" coordinates are equal.
        (the "y" coordinate will be neglected)
        Please refer to "example 3" of the comments provided for property: "W" in this file.
        '''
        self.required_identical_coordinate = [True, True, True]

        '''
        set "precision" or termination criteria by default as: 2 cm. It means actual and desired positions are considered "identical" 
        if for each position coordinate (x, y, z), the absolute value of the difference of current and desired, does not exceed: 2 cm.
        '''
        self.precision            = 0.01
        self.precision_base       = "Coordinate Difference"
    
class Metric:
    '''
    Metric includes everything regarding the error between two positions or orientations.
    '''    
    def __init__(self, settings = Metric_Settings()):
        '''    
        '''
        self.settings = settings

        # "error.value" is a 3 X 1 vector which represents the value of the error function or error between actual and desired positions.
        # Elements of "value" can be calculated according to various formulation depending on the values of "W" property

        self.value = numpy.zeros((3))
        self.rate  = numpy.zeros((3))

        # property "in_target" is True when the actual and desired task points are fully or partially identical according to the defined weighting matrix and power array
        self.in_target = False
    
    def basis_error(self, current, target ) : 
        '''
        return the distance between current and target 
    
        excluding weighting stuff         
        abstract method 
        '''
        return None 
    
    def update(self, current, target ) : 
        '''       
        change the "weighted distance" of current and target; 
        save it in the class property "value" 
        
        abstract method 
        '''
        return None 

class Position_Metric(Metric):
    '''
    includes everything regarding the error between two positions
    '''
    def __init__(self, settings = Metric_Settings()):
        '''
        '''
        Metric.__init__(self, settings = settings)
        #set "Cartesian Coordinates" as default representation for position        
        self.settings = settings

    def basis_error(self, current, target ) :
        func_name = ".basis_error()"    
        # def basis_position_error(self, current, target):
        '''
        return the value of basis_position_error
        '''
        if self.settings.representation == 'Cartesian Coordinates':
            err = current - target
            f   = err**self.settings.power    
        elif self.settings.representation == 'Cylindrical_Coordinates':
            p = 3
            assert len(self.power) == p
            f = numpy.zeros((p))
            assert False
        elif self.settings.representation == 'Spherical_Coordinates':
            p = 3
            assert len(self.power) == p
            f = numpy.zeros((p))
            assert False
        else:
            assert False, 'Error from: ' + __name__ + func_name + ": " + self.settings.representation + " is an invalid representation"

        return f

    """
    def basis_error_rate(self, x, xd, x_dot, xd_dot) : 
        '''
        return the rate of basis_position_error
        '''
        if self.basis_error_function == 'differential_cartesian_coordinates':
            p = 3
            assert len(self.power) == p
            f_dot = numpy.zeros((p))
            for k in range (0,p):
                if self.power[k] == 0:
                    f_dot[k] = 0
                else:
                    if self.power[k] == 1:
                        f[k] = x_dot[k] - xd_dot[k]
                    else:            
                        err  = x[k] - xd[k]
                        f[k] = self.power[k]*(err**(self.power[k] - 1))*(x_dot[k] - xd_dot[k])

        elif self.basis_error_function == 'differential_cylindrical_coordinates':
            p = 3
            assert len(self.power) == p
            f_dot = numpy.zeros((p))
            assert False
        elif self.basis_error_function == 'differential_spherical_coordinates':
            p = 3
            assert len(self.power) == p
            f_dot = numpy.zeros((p))
            assert False
        else:
            print 'Wrong basis error function: ' + self.basis_error_function
            assert False

        return f_dot

    def update_rate(self, x, xd, x_dot, xd_dot):
        '''
        Calculates the error rate vector between the actual and desired positions of the corresponding taskpoint
        '''
        ber = self.basis_error(x, xd, x_dot, xd_dot)
        assert self.W.shape[1] == len(ber)
        self.rate = numpy.dot(self.W, ber)
    """
        
    def update(self, current, target ) : 
        # def update_for_position(self,actual_position, target):
        '''
        Calculates the error vector between the actual and desired positions of the corresponding taskpoint
        '''
        be = self.basis_error(current, target)
        assert self.settings.weight.shape[1] == len(be)
        self.value = numpy.dot(self.settings.weight, be)
        self.in_target = True
        for k in range(0,3):
            if self.settings.required_identical_coordinate[k]:
                deviation = abs(target[k] - current[k])
                self.in_target = self.in_target and (deviation < self.precision) 


class Orientation_Metric(Metric):
    '''
    includes everything regarding the error between two orientations
    '''
    
    def __init__(self, settings = Metric_Settings(representation = 'diag', metric_type = 'relative')):
        Metric.__init__(self, settings = settings)
        #set "Axis Inner Product" as default basis error function for orientation error        
        '''
        set "precision" or termination criteria by default as: 2.0 degrees. It means actual and desired orientations are considered "identical" 
        if for each frame axis (i, j, k), the absolute value of the angle between current and desired frames, does not exceed: 2.0 degrees.
        '''
        self.settings.precision_base = 'Axis Angle'
        self.precision               = 1.0

        if self.settings.representation == 'diag':
            self.offset = numpy.array([-1.0, -1.0, -1.0])
        elif self.settings.representation in ['trace', 'angle']:
            self.weight   = numpy.array([[1]])
            ms.power      = numpy.array([1])
            if self.settings.representation == 'trace':
                self.offset   = numpy.array([-3.0])
            else:    
                self.offset   = numpy.array([0.0])
        else:
            self.offset   = numpy.zeros(3)
        

    def basis_error(self, current, target ) : 
        
        # def basis_orientation_error(self, current, target):
        rpn =  self.settings.representation
        if rpn == 'vector':
            current.set_generating_function( self.settings.generating_function )
            target.set_generating_function( self.settings.generating_function )
        '''
        '''
        if self.settings.metric_type == 'relative':
            Oe   = current/target
            e    = Oe[rpn]
        elif self.settings.metric_type == 'differential':
            e  = current[rpn] - target[rpn]

        elif self.settings.metric_type == 'special':
            if self.settings.representation == 'AxInPr':
                p = 3
                assert len(self.settings.power) == p
                f = numpy.zeros((p))
                for k in range (0,p):
                    if self.settings.power[k] == 0:
                        err = 0
                        f[k] = 1
                    else:
                        err = numpy.dot(target.frame_axis(k), current.frame_axis(k))
                        if self.settings.power[k] == 1 :
                            f[k] = err
                        else:            
                            f[k] = err**self.settings.power[k]
            if self.settings.representation == 'AxInPr + DiNoQu':
                p = 6
                assert len(self.settings.power) == p
                f = numpy.zeros((p))
                for k in range (0,3):
                    if self.settings.power[k] == 0:
                        err = 0
                        f[k] = 1
                    else:
                        err = numpy.dot(target.frame_axis(k), current.frame_axis(k))
                        if self.settings.power[k] == 1 :
                            f[k] = err
                        else:            
                            f[k] = err**self.settings.power[k]
                qn  = current['quaternion']
                qnd = target['quaternion']
                for k in range (3,6):
                    z    = - qnd[0]*qn[k-2] + qn[0]*qnd[k-2]    
                    f[k] = z**self.settings.power[k]
            else:
                assert False
            return f        
        else:
            assert False, gen.err_str(__name__, "basis_error", self.settings.metric_type + " is an invalid metric type")
        if self.settings.representation == 'matrix':
            e = e.flatten()

        f  = e**self.settings.power 
        return f
    """
    def basis_error_rate(self, R, Rd, R_dot, Rd_dot ) : 
        '''
        '''
        if self.basis_error_function == 'Axis Inner Product':
            p = 3
            assert len(self.power) == p
            f_dot = numpy.zeros((p))
            for k in range (0,p):
                if self.power[k] == 0:
                    f_dot[k] = 0
                else:
                    err_rate = numpy.dot(vecmat.uvect(Rd_dot, k), vecmat.uvect(R, k)) + numpy.dot(vecmat.uvect(Rd, k), vecmat.uvect(R_dot, k))
                    if self.power[k] == 1 :
                        f_dot[k] = err_rate
                    else:            
                        err = numpy.dot(vecmat.uvect(Rd, k), vecmat.uvect(R, k))
                        f_dot[k] = self.power[k]*err_rate*(err**(self.power[k]-1))

        else:
            assert False

        return f_dot

    """
    def update(self, current, target ) : 
        '''
        Calculates the error vector between the actual and desired orientations of the corresponding taskframe
        '''
        be = self.basis_error(current, target)

        assert self.settings.weight.shape[1] == len(be)
        
        self.value = numpy.dot(self.settings.weight, be) + self.settings.offset

        if self.precision_base == 'Axis Angle':
        
            self.in_target = True
            for k in range(0,3):
                if self.settings.required_identical_coordinate[k]:
                    cos_teta = numpy.dot(target.frame_axis(k), current.frame_axis(k))
                    if (cos_teta < 1.00000) and (cos_teta > -1.00000):
                        deviation = abs((180.0/math.pi)*math.acos(cos_teta))
                        self.in_target = self.in_target and (deviation < self.precision) 

                    self.in_target =  self.in_target and (cos_teta > -1.00000)
        elif self.precision_base == 'Error Function':
            self.in_target = (numpy.linalg.norm(self.value) < self.precision)
        else:
            assert False

    """
    def update_rate(self, R, Rd, R_dot, Rd_dot ) : 
        '''
        Calculates the error rate vector between the actual and desired orientations of the corresponding taskframe
        '''
        ber = self.basis_error(R, Rd, R_dot, Rd_dot)
        assert self.W.shape[1] == len(ber)
        self.rate = numpy.dot(self.W, ber)
    """


class Pose_Metric(Metric):
    '''
    (outlook)
    '''
        
    def __init__(self):
        '''
        '''
        self.orientation_metric = Orientation_Metric() 
        self.position_metric = Position_Metric() 
        
        Metric.__init__(self)

    
    def basis_error(self, current, target ) : 
        '''
        '''
        self.orientation_metric.basis_error() 
        
        
        self.position_metric.basis_error() 
        
    
    
    def update(self, current, target ) : 
        '''
        '''
        self.orientation_metric.update() 
        self.position_metric.update() 
        

