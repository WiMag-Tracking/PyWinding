from scipy.constants import mu_0
import numpy as np

MATERIAL = ('Transmitter', 1, 1, 0, 0, 58*0.65, 0, 0, 1, 0, 0, 0)

class Helmholtz:
    def __init__(self, rad, B, f, lsec, n):
        self.lsec = lsec
        self.f = f
        self.B = B
        self.r = rad
        self.n = n
        self.i = self.current()
        self.lar = self.r
        self.laz = self.r / 2

        self.material = MATERIAL

    def current(self):
        r = self.r / 1000 # convert millimetres to metres
        
        i = self.B * r / (mu_0 * self.n * (4/5)**(3/2) )

        return i

    def field(self,r,i,n):
        mu_0 = 4e-7 * np.pi
        r = r/1000 # Convert millimeters to meter.

        B = (4/5)^(3/2) * (mu_0*n*i/r)
        return B

    @property
    def i(self):
        return self.__i

    @i.setter
    def i(self, current):
        self.__i = current

    def _label(self, canvas):
        # Add block labels for the Helmholtz coil.
        canvas.mi.addblocklabel(self.lar, self.laz)
        canvas.mi.addblocklabel(self.lar, - self.laz)
        canvas.mi.addblocklabel(self.lar/2, self.lar/2)
        
    def _draw(self, canvas):
        # Draw rectangles for the transmitter helmholtz coil windings;
        # Size of coil section square; Define square edge length of 10mm
        th_helm = 5 # total thickness is 2 x 5mm = 10mm
        coilcoord1 = [-self.lsec + self.r,-self.lsec + self.r/2, self.lsec + self.r, self.lsec + self.r/2]
        coilcoord2 = [-self.lsec + self.r,-self.lsec -  self.r/2, self.lsec +  self.r, self.lsec -  self.r/2]
        canvas.mi.drawrectangle( * coilcoord1 )
        canvas.mi.drawrectangle( * coilcoord2 )
        
    def _properties(self, canvas):
        # Add a "circuit property" so that we can calculate the properties of the
        # coil as seen from the terminals.
        # Here icoil_sensor is set to zero (Sensor is open circuit)
        # Here icoil_transmitter is set to 1 Ampere (This is modified later to achieve a field of 1 uT)
        # The last '1' arguement in each case indicates 'Series' is selected.
        canvas.mi.addcircprop('icoil_sensor', 0, 1)
        # Set the block properties of the Helmholtz windings.
        canvas.mi.addcircprop('icoil_transmitter', self.i, 1)
        canvas.mi.selectlabel(self.lar, self.laz)
        canvas.mi.setblockprop('Transmitter', 1, 1, 'icoil_transmitter', 0, 0, self.n)
        canvas.mi.clearselected()
        canvas.mi.selectlabel(self.lar, -self.laz)
        canvas.mi.setblockprop('Transmitter', 1, 1, 'icoil_transmitter', 0, 0, self.n)
        canvas.mi.clearselected()
        # Set the block properties of the air
        canvas.mi.selectlabel(self.lar/2, self.lar/2)
        canvas.mi.setblockprop('Air', 1, 1, '<None>', 0, 0, 0)
        canvas.mi.clearselected()

    @property
    def material(self):
        return self.__material

    @material.setter
    def material(self, mat):
        self.__material = mat