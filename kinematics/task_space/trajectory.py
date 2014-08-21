'''   Header
@file:          trajectory.py
@brief:    	    This module provides a class containing a trajectory in the taskspace.
                The path is generated by a number of key points containing poses, twists and corresponding phase phi
                
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
@version:	    4

Last Revision:  22 August 2014

Major changes from version 3:
    1- Trajectories now comprise of "segments" and "key_points". each segment, contains a number of key points.
       if the interpolation is "velocity_consistent" then the velocity in the sharing key_points must be eual
    2- In this stage, two segments can and must only have one keypoint in commomn.  

'''
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import copy, math

from packages.nima.mathematics import polynomials as pl
from packages.nima.mathematics import general as gen
from mpl_toolkits.mplot3d import Axes3D

class Key_Point(object):
   def __init__(self, phi, pos, vel=None, acc=None):
       self.dim     = len(pos) 
       self.phi     = phi
       self.pos     = pos
       self.vel     = vel
       self.acc     = acc  
 
   def __str__( self ):
       s  = "Point Dimension: " + str(self.dim) + '\n' 
       s += "Phase       : " + str(self.phi) + '\n'
       s += "Position    : " + str(self.pos) + '\n'
       s += "Velocity    : " + str(self.vel) + '\n'
       s += "Acceleration: " + str(self.acc) + '\n'
       return s

   def value(self, field_name = 'position', axis = 0):
       if field_name == 'position':
           return self.pos[axis]
       elif field_name == 'velocity':
           return self.vel[axis]
       elif field_name == 'acceleration':
           return self.acc[axis]
       else:
           print "Error from Key_Point.value(): Given field_name is not valid"

class Key_Point_Orientation(object):
   def __init__(self, phi, pos, vel=None, acc=None):
       self.phi     = phi
       self.pos     = pos
       self.vel     = vel
       self.acc     = acc  
 
   def __str__( self ):
       s  = "3D Orientation Point: " + '\n' 
       s += "Phase       : " + str(self.phi) + '\n'
       s += "Position    : \n" + str(self.pos) + '\n'
       s += "Velocity    : \n" + str(self.vel) + '\n'
       s += "Acceleration: \n" + str(self.acc) + '\n'
       return s

class Trajectory_Segment(object):
    
    def __init__(self, dimension = 3):
        # By default, initially the trajectory is a constant position at [0,0,0] (not changing)
        # You should add points to it to make your trajectory

        self.current_phi            = 0.0
        self.phi_end                = 0.0
        self.capacity               = 3 # determines how many key points can it hold
        self.interpolated           = False

        self.dim                    = dimension
        self.current_position       = np.zeros(self.dim)
        self.current_velocity       = np.zeros(self.dim)
        self.current_acceleration   = np.zeros(self.dim)

        self.point = []

    def __str__( self ):
        s  = "Phase Length     : " + str(self.phi_end) + '\n' 
        s += "Number of Points : " + str(len(self.point)) + '\n'
        s += "Segment Starting Point: " + '\n'
        s += str(self.point[0]) + '\n'
        s += "Segment End Point: " + '\n'
        s += str(self.point[len(self.point) - 1]) + '\n'
        return s

    def add_point(self, phi, pos, vel = None, acc = None):
        '''
        Adds a point to the list of key points
        '''
        n = len(self.point)
        if n > 0:
            assert phi >= self.point[n-1].phi

        nn  = np.array([None for j in range(self.dim)])

        if pos == None:
            pos = np.copy(nn)
        else:
            assert len(pos) == self.dim 
        if vel == None:
            vel = np.copy(nn)
        else:
            assert len(vel) == self.dim 
        if acc == None:
            acc = np.copy(nn)
        else:
            assert len(acc) == self.dim 

        if n < self.capacity:
            self.point.append(Key_Point(phi, pos, vel, acc))
            self.phi_end = phi
            self.interpolated = False
        else:
            print "Error from Trajectory_Segment.add_point(): Can not take more points than its capacity"
        
    def set_phi(self, phi):
        if not self.interpolated:
            self.interpolate()
        self.current_phi = phi
        self.current_position = np.zeros(self.dim)
        self.current_velocity = np.zeros(self.dim)
        self.current_acceleration = np.zeros(self.dim)
        for j in range(self.dim):
            self.current_position[j]     = self.traj[j].position( t = phi )
            self.current_velocity[j]     = self.traj[j].velocity( t = phi )
            self.current_acceleration[j] = self.traj[j].acceleration( t = phi )

    def current_value(self, field_name= 'position', axis = 0):

        if field_name == 'position':
            return self.current_position[axis]
        elif field_name == 'velocity':
            return self.current_velocity[axis]
        elif field_name == 'acceleration':
            return self.current_acceleration[axis]
        else:
            print "Error from Trajectory_Segment.current_value(): Given field_name is not valid"
    
    def plot(self, axis = 0, n = 100, y_text = "", wtp = 'position', show_points = False):
        if y_text == "":
            s = wtp + " of Axis " + str(axis)
        else:
            s = wtp + " of " + y_text

        x = np.append(np.arange(0.0, self.phi_end, self.phi_end/n), self.phi_end)
        y = []
        for t in x:
            self.set_phi(t)
            y.append(self.current_value(field_name = wtp, axis = axis))

        if show_points:
            px = []
            py = []
            for pnt in self.point:
                px.append(pnt.phi)
                py.append(pnt.value(field_name = wtp, axis = axis))

            plt.plot(x, y, px, py, 'o') 
        else:
            plt.plot(x, y) 

        plt.ylabel(s)
        plt.xlabel('phi')
        plt.show()

    def scatter_plot(self, wtp = 'position', axis_x = 0, axis_y = 1, n = 100, y_text = "", show_points = False):

        t = np.append(np.arange(0.0, self.phi_end, self.phi_end/n), self.phi_end)
        x = []
        y = []
        for ph in t:
            self.set_phi(ph)
            x.append(self.current_value(field_name = wtp, axis = axis_x))
            y.append(self.current_value(field_name = wtp, axis = axis_y))

        if show_points:
            px = []
            py = []
            for pnt in self.point:
                px.append(pnt.value(field_name = wtp, axis = axis_x))
                py.append(pnt.value(field_name = wtp, axis = axis_y))

            plt.plot(x, y, px, py, 'o') 
        else:
            plt.plot(x, y) 

        plt.ylabel('Y')
        plt.xlabel('X')
        plt.show()

class Polynomial_Trajectory_Segment(Trajectory_Segment):
    def __init__(self, dimension = 3):
        super(Polynomial_Trajectory_Segment, self).__init__(dimension = dimension)            
        self.traj = [pl.Polynomial() for j in range(self.dim)] 

    def interpolate(self):
        '''
        specifies the coefficients of the trajectory_tbc_path which passes through a number of poses
        At least one position and one phi is required.
        phi[0] must be zero.
        '''
        if not self.interpolated:
            n = len(self.point)
            if n == 0:
                print "Error from Polynomial_Trajectory_Segment.interpolate(): No key points defined !"
                return False 

            pnt = [[] for j in range(self.dim)]

            for i in range(n):
                for j in range(self.dim):
                    pnt[j].append(pl.Point(t = self.point[i].phi, x = self.point[i].pos[j], v = self.point[i].vel[j], a = self.point[i].acc[j]))

            for j in range(self.dim):
                self.traj[j].interpolate_smart(pnt[j])

            self.phi_end = self.point[n-1].phi
            self.interpolated = True
            return True

class Trajectory(object):

    def __init__(self, dimension = 3):
        self.dim     = dimension
        self.segment = []
        self.segment_start = []
        self.phi_end = 0.0

    def __str__( self ):
        s  = "Trajectory Phase Length : " + str(self.phi_end) + '\n' 
        s += "Number of Segments      : " + str(len(self.segment)) + '\n'
        for i in range(len(self.segment)):
            s += "Segment Number " + str(i) + " starting at phi = " + str(self.segment_start[i]) + ': \n'
            s += str(self.segment[i])
            s += "****************************************** \n" 
        return s

    def current_value(self, field_name= 'position', axis = 0):

        if field_name == 'position':
            return self.current_position[axis]
        elif field_name == 'velocity':
            return self.current_velocity[axis]
        elif field_name == 'acceleration':
            return self.current_acceleration[axis]
        else:
            print "Error from Trajectory_Segment.current_value(): Given field_name is not valid"

    def add_segment(self, new_seg):

        self.segment.append(new_seg)
        self.segment_start.append(self.phi_end)
        self.phi_end = self.phi_end + new_seg.phi_end

    def new_segment(self):
        nn   = np.array([None for j in range(self.dim)])
        lsi  = len(self.segment) - 1
        seg  = Polynomial_Trajectory_Segment(dimension = self.dim) 
        lslp = self.segment[lsi].point[len(self.segment[lsi].point) - 1] # last_seg_last_point
        seg.add_point(0.0, lslp.pos, nn, np.copy(nn))
        self.add_segment(seg)

    def set_phi(self, phi):

        if phi > self.phi_end:
            phi = self.phi_end

        self.current_phi = phi

        lsi     = len(self.segment)  - 1 # last segment index

        i = 0
        while (phi > self.segment_start[i] + self.segment[i].phi_end) and (i <= lsi):
            i += 1
        
        self.segment[i].set_phi(phi - self.segment_start[i])
        self.current_position = self.segment[i].current_position
        self.current_velocity = self.segment[i].current_velocity
        self.current_acceleration = self.segment[i].current_acceleration
       
    def interpolate(self):
        for seg in self.segment:
            seg.interpolate()

    def plot(self, axis = 0, n = 100, y_text = "", wtp = 'position', show_points = False):
        if y_text == "":
            s = wtp + " of Axis " + str(axis)
        else:
            s = wtp + " of: " + y_text

        x = np.append(np.arange(0.0, self.phi_end, self.phi_end/n), self.phi_end)
        y = []
        for t in x:
            self.set_phi(t)
            y.append(self.current_value(field_name = wtp, axis = axis))

        if show_points:
            px = []
            py = []
            for i in range(len(self.segment)):
                for pnt in self.segment[i].point:
                    px.append(self.segment_start[i] + pnt.phi)
                    py.append(pnt.value(field_name = wtp, axis = axis))

            plt.plot(x, y, px, py, 'o') 
        else:
            plt.plot(x, y) 

        plt.ylabel(s)
        plt.xlabel('phi')
        plt.show()

    def plot2d(self, wtp = 'position', axis_x = 0, axis_y = 1, n = 100, y_text = "", show_points = False):

        t = np.append(np.arange(0.0, self.phi_end, self.phi_end/n), self.phi_end)
        x = []
        y = []
        for ph in t:
            self.set_phi(ph)
            x.append(self.current_value(field_name = wtp, axis = axis_x))
            y.append(self.current_value(field_name = wtp, axis = axis_y))

        if show_points:
            px = []
            py = []
            for i in range(len(self.segment)):
                for pnt in self.segment[i].point:
                    px.append(pnt.value(field_name = wtp, axis = axis_x))
                    py.append(pnt.value(field_name = wtp, axis = axis_y))

            plt.plot(x, y, px, py, 'o') 
        else:
            plt.plot(x, y) 

        plt.ylabel('Y')
        plt.xlabel('X')
        plt.show()

    def plot3d(self, wtp = 'position', axis_x = 0, axis_y = 1, axis_z = 2, n = 100, label = "", show_points = False):

        t = np.append(np.arange(0.0, self.phi_end, self.phi_end/n), self.phi_end)
        mpl.rcParams['legend.fontsize'] = 10
        fig = plt.figure()
        ax = fig.gca(projection='3d')

        x = []
        y = []
        z = []
        for ph in t:
            self.set_phi(ph)
            x.append(self.current_value(field_name = wtp, axis = axis_x))
            y.append(self.current_value(field_name = wtp, axis = axis_y))
            z.append(self.current_value(field_name = wtp, axis = axis_z))

        ax.plot(x, y, z, label = label)
        ax.legend()
        plt.show()

class Polynomial_Trajectory(Trajectory):
    def __init__(self, dimension=3):
        super(Polynomial_Trajectory, self).__init__(dimension = dimension)

    def add_point(self, phi, pos, vel = None, acc = None):
        '''
        Adds a point to the end of the trajectory with desired position, velocity and acceleration
        '''
        lsi = len(self.segment) - 1

        if lsi < 0:
            assert gen.equal(phi, 0.0)
            seg = Polynomial_Trajectory_Segment(dimension = self.dim) 
            seg.add_point(0.0, pos, vel, acc)
            self.add_segment(seg)
        elif len(self.segment[lsi].point) < self.segment[lsi].capacity:
            assert phi >= self.phi_end
            phi0 = self.segment_start[lsi]
            self.segment[lsi].add_point(phi - phi0, pos, vel, acc)
        else:
            assert phi >= self.phi_end
            self.new_segment()
            self.segment[lsi+1].add_point(phi-self.phi_end, pos, vel, acc)

        lsi = len(self.segment) - 1
        self.phi_end = self.segment_start[lsi] + self.segment[lsi].phi_end
        self.interpolated = False

    def add_vector(self, delta_phi, delta_pos, vel = None, acc = None):
        assert delta_phi > 0
        phi  = self.phi_end + delta_phi
        lsi  = len(self.segment) - 1
        lslp = self.segment[lsi].point[len(self.segment[lsi].point) - 1] # last_seg_last_point

        pos = lslp.pos + delta_pos
        self.add_point(phi, pos, vel, acc)

    def consistent_velocities(self):
        if not self.interpolated:
            self.interpolate()
        lsi = len(self.segment) - 1

        for i in range(lsi + 1):
            lp  = self.segment[i].point[len(self.segment[i].point) - 1]  # last point
            ip1 = i + 1
            if ip1 > lsi:
                ip1 = 0 
            for j in range(self.dim):
                self.segment[i].set_phi(lp.phi)
                self.segment[ip1].set_phi(0.0)
                if lp.vel[j] == None:
                    if self.segment[ip1].point[0].vel[j] == None:
                        v = 0.5*(self.segment[i].current_velocity[j] + self.segment[ip1].current_velocity[j])
                        lp.vel[j] = v
                        self.segment[ip1].point[0].vel[j] = v
                    else:
                        lp.vel[j] = self.segment[ip1].point[0].vel[j]
                elif self.segment[ip1].point[0].vel[j] == None:
                    self.segment[ip1].point[0].vel[j] = lp.vel[j]
                elif not gen.equal(lp.vel[j], self.segment[ip1].point[0].vel[j]):
                    v = 0.5*(lp.vel[j] + self.segment[ip1].point[0].vel[j])
                    lp.vel[j] = v
                    self.segment[ip1].point[0].vel[j] = v
                else:
                    # Already Consistent! Do nothing
                    assert True
    
        for seg in self.segment:
            seg.interpolated = False

        self.interpolate()         

class Orientation_Trajectory_Segment(object):
    def __init__(self):
        self.current_orientation    = np.eye(3)
        self.current_phi            = 0.0
        self.phi_end                = 0.0
        self.capacity               = 3 # determines how many key points can it hold
        self.interpolated           = False

        self.current_angular_velocity       = np.zeros((3,3))
        self.current_angular_acceleration   = np.zeros((3,3))

        self.point = []

    def __str__( self ):
        s  = "Phase Length     : " + str(self.phi_end) + '\n' 
        s += "Number of Points : " + str(len(self.point)) + '\n'
        s += "Segment Starting Point: " + '\n'
        s += str(self.point[0]) + '\n'
        s += "Segment End Point: " + '\n'
        s += str(self.point[len(self.point) - 1]) + '\n'
        return s

    def set_phi(self, phi):
        self.current_phi = phi 

    def add_point(self, phi, pos, vel = None, acc = None):
        '''
        Adds a point to the list of key points
        '''
        n = len(self.point)
        if n > 0:
            assert phi > self.point[n-1].phi

        if n < self.capacity:
            self.point.append(Key_Point_Orientation(phi, pos, vel, acc))
            self.phi_end = phi
            self.interpolated = False
        else:
            print "Error from Orientation_Trajectory_Segment.add_point(): Can not take more points than its capacity"

class Orientation_Trajectory(object):

    def __init__(self):
        self.current_phi            = 0.0
        self.phi_end                = 0.0
        self.segment                = []
        self.segment_start          = []
        self.interpolated           = False

        self.current_orientation            = np.eye(3)
        self.current_orientation_rate       = np.zeros((3,3))
        self.current_angular_acceleration   = np.zeros((3,3))


    def __str__( self ):
        s  = "Orientation Trajectory Phase Length : " + str(self.phi_end) + '\n' 
        s += "Number of Segments      : " + str(len(self.segment)) + '\n'
        for i in range(len(self.segment)):
            s += "Segment Number " + str(i) + " starting at phi = " + str(self.segment_start[i]) + ': \n'
            s += str(self.segment[i])
            s += "****************************************** \n" 
        return s

    def set_phi(self, phi):
        '''
        if not self.interpolated:
            self.interpolate()
        '''
        self.current_phi = phi
        
