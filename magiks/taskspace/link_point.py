
# HEADER
'''   
@file:          link_point.py
@brief:    	    This module provides a class representing the position of a point on a link
                This point can be the proximal or distal joint centers or center of mass, or any other point on the local coordinate system of the link
@author:        Nima Ramezani Taghiabadi
                PhD Researcher
                Faculty of Engineering and Information Technology
                University of Technology Sydney
                Broadway, Ultimo, NSW 2007
                Room No.: CB10.03.512
                Phone:    02 9514 4621
                Mobile:   04 5027 4611
                Email(1): Nima.RamezaniTaghiabadi@student.uts.edu.au 
                Email(2): nima.ramezani@gmail.com
                Email(3): nima_ramezani@yahoo.com
                Email(4): ramezanitn@alum.sharif.edu
@version:	    0.3
Last Revision:  23 October 2011
'''
# BODY

class Link_Point :
    '''
    A Link point is a point defined on a link or frame of any moving mechanism.
    only a position reference
    
    This record should be defined in association with a Reference_Position
    '''
    def __init__(self, link_number, weight, position_vector):
        '''
        @param "ln" represents the number of link in a model on which the point is located
        @param "pv" represents the position vector of the refered point in the local coordinate system of the specified link.
                    The local coordinates system is specified by DH standard:
                    Axis z (k): is the rotation axis of the proximal joint center.
                    Axis x (i) : is in the direction of the vector moving from proximal towards distal joint center
                    Axis y (j) : is generated by: j = k X i
                    The origin of the frame is located on the distal joint center
                    
                    i.e: For introducing the proximal joint center select: pv = [-a_i*cos(teta_i) , -a_i*sin(teta_i), -d_i]
                    where: "a_i" and "d_i" are read from DH parameters of link i, and "teta_i" is the initial joint angle of the proximal joint
                    i.e: For introducing the distal joint center, select: pv = [0, 0, 0]
                    
        @param "w" is a weight coefficient. It is used when a reference position is defined as a linear combination of some link points
        '''
        self.ln = link_number
        self.pv = position_vector
        self.w  = weight
