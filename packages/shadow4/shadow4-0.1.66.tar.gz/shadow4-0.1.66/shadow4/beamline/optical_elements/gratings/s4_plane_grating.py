"""
The s4 plane grating (optical element and beamline element).
"""
import numpy

from syned.beamline.element_coordinates import ElementCoordinates

from shadow4.beam.s4_beam import S4Beam
from shadow4.beamline.optical_elements.gratings.s4_grating import S4GratingElement, S4Grating
from shadow4.beamline.s4_optical_element_decorators import S4PlaneOpticalElementDecorator
from shadow4.beamline.s4_beamline_element_movements import S4BeamlineElementMovements

class S4PlaneGrating(S4Grating, S4PlaneOpticalElementDecorator):
    """
    Constructor.

    Parameters
    ----------
    name :  str, optional
        A name for the crystal
    boundary_shape : instance of BoundaryShape, optional
        The information on the crystal boundaries.
    ruling : float, optional
        The constant term of the ruling in lines/m.
    ruling_coeff_linear : float, optional
        The linear term of the ruling in lines/m^2.
    ruling_coeff_quadratic : float, optional
        The quadratic term of the ruling in lines/m^3.
    ruling_coeff_cubic : float, optional
        The cubic term of the ruling in lines/m^4.
    ruling_coeff_quartic : float, optional
        The quartic term of the ruling in lines/m^5.
    coating : str, optional
        The identified if the coating material (not used, passed to syned).
    coating_thickness : float, optional
        The thickness of the coating in m (not used, passed to syned).
    order : int, optional
        The diffraction order.
    f_ruling : int, optional
        A flag to define the type of ruling:
            - (0) constant on X-Y plane (0)
            - (1) polynomial line density (5 in shadow3).

    Returns
    -------
    instance of S4PlaneGrating.
    """
    def __init__(self,
                 name="Undefined",
                 boundary_shape=None,
                 ruling=800e3,
                 ruling_coeff_linear=0.0,
                 ruling_coeff_quadratic=0.0,
                 ruling_coeff_cubic=0.0,
                 ruling_coeff_quartic=0.0,
                 coating=None,
                 coating_thickness=None,
                 order=0,
                 f_ruling=0,
                 ):

        S4PlaneOpticalElementDecorator.__init__(self)
        S4Grating.__init__(self,
                           name=name,
                           surface_shape=self.get_surface_shape_instance(),
                           boundary_shape=boundary_shape,
                           ruling=ruling,
                           ruling_coeff_linear=ruling_coeff_linear,
                           ruling_coeff_quadratic=ruling_coeff_quadratic,
                           ruling_coeff_cubic=ruling_coeff_cubic,
                           ruling_coeff_quartic=ruling_coeff_quartic,
                           coating=coating,
                           coating_thickness=coating_thickness,
                           order=order,
                           f_ruling=f_ruling,
                           )

        self.__inputs = {
            "name": name,
            "boundary_shape": boundary_shape,
            "ruling": ruling,
            "ruling_coeff_linear": ruling_coeff_linear,
            "ruling_coeff_quadratic": ruling_coeff_quadratic,
            "ruling_coeff_cubic": ruling_coeff_cubic,
            "ruling_coeff_quartic": ruling_coeff_quartic,
            "order": order,
            "f_ruling": f_ruling,
        }

    def to_python_code(self, **kwargs):
        """
        Creates the python code for defining the element.

        Parameters
        ----------
        **kwargs

        Returns
        -------
        str
            Python code.
        """
        txt = self.to_python_code_boundary_shape()
        txt += "\nfrom shadow4.beamline.optical_elements.gratings.s4_plane_grating import S4PlaneGrating"

        txt_pre = """\noptical_element = S4PlaneGrating(name='{name}',
    boundary_shape=None, f_ruling={f_ruling}, order={order},
    ruling={ruling}, ruling_coeff_linear={ruling_coeff_linear}, 
    ruling_coeff_quadratic={ruling_coeff_quadratic}, ruling_coeff_cubic={ruling_coeff_cubic},
    ruling_coeff_quartic={ruling_coeff_quartic},
    )"""
        txt += txt_pre.format(**self.__inputs)

        return txt

    # def get_optical_surface_instance(self):
    #     return S4Conic.initialize_as_plane()

class S4PlaneGratingElement(S4GratingElement):
    """
    Constructor.

    Parameters
    ----------
    optical_element : instance of OpticalElement, optional
        The syned optical element.
    coordinates : instance of ElementCoordinates, optional
        The syned element coordinates.
    movements : instance of S4BeamlineElementMovements, optional
        The S4 element movements.
    input_beam : instance of S4Beam, optional
        The S4 incident beam.
    """
    def __init__(self,
                 optical_element : S4PlaneGrating = None,
                 coordinates : ElementCoordinates = None,
                 movements: S4BeamlineElementMovements = None,
                 input_beam : S4Beam = None):
        super().__init__(optical_element=optical_element if optical_element is not None else S4PlaneGrating(),
                         coordinates=coordinates if coordinates is not None else ElementCoordinates(),
                         movements=movements,
                         input_beam=input_beam)

    def to_python_code(self, **kwargs):
        """
        Creates the python code for defining the element.

        Parameters
        ----------
        **kwargs

        Returns
        -------
        str
            Python code.
        """
        txt = "\n\n# optical element number XX"
        txt += self.get_optical_element().to_python_code()
        txt += self.to_python_code_coordinates()
        txt += self.to_python_code_movements()
        txt += "\nfrom shadow4.beamline.optical_elements.gratings.s4_plane_grating import S4PlaneGratingElement"
        txt += "\nbeamline_element = S4PlaneGratingElement(optical_element=optical_element, coordinates=coordinates, movements=movements, input_beam=beam)"
        txt += "\n\nbeam, footprint = beamline_element.trace_beam()"
        return txt

if __name__ == "__main__":

    from shadow4.sources.source_geometrical.source_gaussian import SourceGaussian
    from shadow4.beam.s4_beam import S4Beam
    from shadow4.tools.graphics import plotxy

    #
    # source
    #
    src = SourceGaussian(
                 nrays=10000,
                 sigmaX=1.0e-6,
                 sigmaY=0.0,
                 sigmaZ=1.0e-6,
                 sigmaXprime=0.0002,
                 sigmaZprime=0.0002,
                 real_space_center=[0.0,0.0,0.0],
                 direction_space_center=[0.0,0.0]
                                 )
    beam = S4Beam()

    beam.generate_source(src)
    beam.set_photon_energy_eV(1000.0)

    print(beam.info())

    # plotxy(Beam3.initialize_from_shadow4_beam(beam),1,3,nbins=100,title="SOURCE")

    #
    # grating
    #
    g = S4PlaneGrating(
        name = "my_grating",
        boundary_shape = None, # BoundaryShape(),
        ruling = 600000.0,
        ruling_coeff_linear = 260818.35944225,
        ruling_coeff_quadratic = 260818.35944225,
        ruling_coeff_cubic = 13648.21037618,
        ruling_coeff_quartic = 0.0,
        coating = None,
        coating_thickness = None,
        order=0,
        f_ruling=0,
        )

    coordinates_syned = ElementCoordinates(p = 10.0,
                                           q = 6.0,
                                           angle_radial = 88.840655 * numpy.pi / 180,
                                           angle_radial_out= 87.588577 * numpy.pi / 180,
                                           angle_azimuthal = 0.0)



    ge = S4PlaneGratingElement(optical_element=g, coordinates=coordinates_syned, input_beam=beam)

    print(ge.info())

    beam_out = ge.trace_beam()
    plotxy(beam_out[0], 1, 3, title="Image 0", nbins=201)


    s4 = S4PlaneGrating()

