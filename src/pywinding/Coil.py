import logging
import numpy as np


class Coil:
    """
    Dimensions in millimetres
    ls  : length of the sensor coil
    ids : inner diameter of the sensor coil
    ods : outer diameter of the sensor coil
    lc  : length of the magnetic core
    idc : inner diameter of the magnetic core (typically 0)
    odc :  outer diameter of the magnetic core (typically same as ids)
    odw : outer diameter of the wire used to wind the sensor including
    insulation, as this is used to calculate the number of turns.
    pf : packing factor (0.9 for circular wire)
    ma : string representing the material of the core
    explicit_n : if False, n is computed internally, if integer value is provided, it is used as the number of turns.

    Default design is a very thin 1 meter diameter coil with an air core.
    The sensitivity of this coil should match the theoretical result of 4.9348 V/(T.Hz)
    """
    def __init__(self,ls=1,ids=999.9,ods=1000.1,lc=1,idc=0,odc=999.9,odw=1,pf=1,ma='Air',na='default_1meter_diameter_aircoil',odwc=1,explicit_n=1):
        if odc != ids:
            logging.error(f'Core outer diameter: {odc} and coil inner diameter: {ids} must match')
            raise ValueError('Core outer diameter and coil inner diameter must match')
        elif lc < ls:
            logging.error(f'Core length: {lc} must be greater than or equal to sensor length: {ls}')
            raise ValueError('Core length must be greater than or equal to sensor length')

        # !TODO add method to calculate N based on orthocyclic winding with kwarg : winding = "orthocyclic" , "linear"
        
        # Derive maximum number of turns possible in given geometry
        # Convert diameters to radial thickness of winding
        winding_thickness = (ods - ids)/2
        # Calculate the cross sectional area of the coil wire
        wire_cross_section = np.pi * (odw/2) ** 2

        # Number of turns to fit into a single layer
        single_layer_turns = np.floor(pf * (ls/odw))
        # Number of layers to fit in the given winding thickness
        radial_layer_turns = np.floor(pf * (winding_thickness/odw))
        # The maxmum number of turns that fit on the winding for the provided specification
        nmax = single_layer_turns * radial_layer_turns
        
        print('GENERATED COIL SPECIFICATIONS:')
        print(f'Maximum number of turns: {nmax}')
        print(f'Number of layers: {radial_layer_turns}')
        print(f'Number of calculated turns per layer: {single_layer_turns}')
        if explicit_n is not False:
            nmax = explicit_n
            print(f'Adjusted number of turns for simulation (Overridden by user): {nmax}')
        print(f'Applied number of turns for simulation: {nmax}\n')
        ## Cylindrical coordinates for the placement of the material labels in FEMM.
        # Labels are specified using r and z coordinates (cylindrical)
        # Label is in the middle of the sensor winding
        label_sen_r = 0.5*ids + 0.25*(ods - ids)
        label_sen_z = 0

        # Core label parameters
        # Label is in the middle of the core
        label_core_r = 0.5*idc + 0.25*(odc-idc)
        label_core_z = 0

        self.na = na
        self.ls = ls
        self.ids = ids
        self.ods = ods
        self.odw = odw
        self.odwc = odwc if odwc is not None else odw
        self.wt = winding_thickness
        self.n = nmax

        self.lc = lc
        self.idc = idc
        self.odc = odc
        self.ma = ma

        self.lasr = label_sen_r
        self.lasz = label_sen_z

        self.lacr = label_core_r
        self.lacz = label_core_z

        # see https://www.femm.info/wiki/pyfemm 'material' in the pdf for details each entry below
        self.material = ('Sensor',1,1,0,0,58,0,0,1,3,0,0,1, self.odw)

    def _label(self, canvas):
        canvas.mi.addblocklabel(self.lasr,self.lasz)
        canvas.mi.addblocklabel(self.lacr,self.lacz)

    def _draw(self, canvas):
        # Draw rectangles for the regions of material. Rectanges are specified with
        # two coordinates (r1,z1) [bottom-left coordinante] and (r2,z2) [upper-right]
        canvas.mi.drawrectangle(0.5*self.ids, -0.5*self.ls, 0.5*self.ods, 0.5*self.ls)
        canvas.mi.drawrectangle(0.5*self.idc, -0.5*self.lc, 0.5*self.odc, 0.5*self.lc)

    def _properties(self, canvas):
        # Set the block properties of the sensor winding.
        
        canvas.mi.selectlabel(self.lasr, self.lasz)
        canvas.mi.setblockprop('Sensor', 1, 1, 'icoil_sensor', 0, 0, self.n)
        canvas.mi.clearselected()
        canvas.mi.selectlabel(self.lacr, self.lacz)
        canvas.mi.getmaterial(self.ma)
        canvas.mi.setblockprop(self.ma, 1, 1, '<None>', 0, 0, 0)
        canvas.mi.clearselected()
    
    @property
    def material(self):
        return self.__material

    @material.setter
    def material(self, mat):
        self.__material = mat