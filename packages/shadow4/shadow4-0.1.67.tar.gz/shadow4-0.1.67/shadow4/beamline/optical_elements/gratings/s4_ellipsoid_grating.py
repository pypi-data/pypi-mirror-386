import numpy

from syned.beamline.shape import Convexity, Direction

from shadow4.beam.s4_beam import S4Beam
from shadow4.beamline.s4_optical_element_decorators import SurfaceCalculation, S4EllipsoidOpticalElementDecorator
from shadow4.beamline.optical_elements.gratings.s4_grating import S4GratingElement, S4Grating, ElementCoordinates
from shadow4.beamline.s4_beamline_element_movements import S4BeamlineElementMovements


class S4EllipsoidGrating(S4Grating, S4EllipsoidOpticalElementDecorator):
    """
    Constructor.

    Parameters
    ----------
    name :  str, optional
        A name for the crystal
    boundary_shape : instance of BoundaryShape, optional
        The information on the crystal boundaries.
    is_cylinder : int, optional
        flag:
            0=No (there is revolution symmetry along Y)
            1=Yes (flat surface along X or Y).
    cylinder_direction : int (as defined by Direction), optional
        NONE = -1, UPWARD = 0, DOWNWARD = 1.
    convexity : int (as defined by Convexity), optional
        NONE = -1, UPWARD = 0, DOWNWARD = 1.
    min_axis : float, optional
        For surface_calculation=0, The minor axis of the ellipsoid (2a).
    maj_axis : float, optional
        For surface_calculation=0, The major axis of the ellipsoid (2b)
    pole_to_focus : float, optional
        For surface_calculation=0, the p or q distance (from focus to center of the optical element).
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
    instance of S4EllipsoidGrating.
    """
    def __init__(self,
                 name="Ellipsoid Grating",
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
                 #
                 min_axis=0.0,
                 maj_axis=0.0,
                 pole_to_focus=0.0,  # for external calculation
                 is_cylinder=False,
                 cylinder_direction=Direction.TANGENTIAL,
                 convexity=Convexity.DOWNWARD,
                 ):
        p_focus, q_focus, grazing_angle = 1.0, 1.0, 1e-3
        S4EllipsoidOpticalElementDecorator.__init__(self, SurfaceCalculation.EXTERNAL, is_cylinder, cylinder_direction, convexity,
                                                 min_axis, maj_axis, pole_to_focus, p_focus, q_focus, grazing_angle)
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
            # "surface_shape": surface_shape,
            "boundary_shape": boundary_shape,
            "ruling": ruling,
            "ruling_coeff_linear": ruling_coeff_linear,
            "ruling_coeff_quadratic": ruling_coeff_quadratic,
            "ruling_coeff_cubic": ruling_coeff_cubic,
            "ruling_coeff_quartic": ruling_coeff_quartic,
            "order": order,
            "f_ruling": f_ruling,
            "min_axis": min_axis,
            "maj_axis": maj_axis,
            "pole_to_focus": pole_to_focus,
            "is_cylinder": is_cylinder,
            "cylinder_direction": cylinder_direction,
            "convexity": convexity,
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
        txt += "\nfrom shadow4.beamline.optical_elements.gratings.s4_ellipsoid_grating import S4EllipsoidGrating"

        txt_pre = """\noptical_element = S4EllipsoidGrating(name='{name}',
    boundary_shape=None, f_ruling={f_ruling}, order={order},
    ruling={ruling}, ruling_coeff_linear={ruling_coeff_linear}, 
    ruling_coeff_quadratic={ruling_coeff_quadratic}, ruling_coeff_cubic={ruling_coeff_cubic},
    ruling_coeff_quartic={ruling_coeff_quartic},
    min_axis={min_axis:f}, maj_axis={maj_axis:f}, pole_to_focus={pole_to_focus:f}, is_cylinder={is_cylinder:d}, cylinder_direction={cylinder_direction:d}, convexity={convexity:d},
    )"""
        txt += txt_pre.format(**self.__inputs)

        return txt

class S4EllipsoidGratingElement(S4GratingElement):
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
                 optical_element : S4EllipsoidGrating = None,
                 coordinates : ElementCoordinates = None,
                 movements: S4BeamlineElementMovements = None,
                 input_beam : S4Beam = None):
        super().__init__(optical_element=optical_element if optical_element is not None else S4EllipsoidGrating(),
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
        txt += "\nfrom shadow4.beamline.optical_elements.gratings.s4_ellipsoid_grating import S4EllipsoidGratingElement"
        txt += "\nbeamline_element = S4EllipsoidGratingElement(optical_element=optical_element, coordinates=coordinates, movements=movements, input_beam=beam)"
        txt += "\n\nbeam, footprint = beamline_element.trace_beam()"
        return txt

    # def apply_grating_diffraction(self, beam):
    #     return self.get_optical_element().apply_grating_diffraction(beam)

if __name__ == "__main__":

    from shadow4.sources.source_geometrical.source_geometrical import SourceGeometrical
    from shadow4.tools.graphics import plotxy

    #
    # source
    #
    src = SourceGeometrical(spatial_type="Point",
                    angular_distribution = "Flat",
                    energy_distribution = "Uniform",
                    nrays = 5000,
                            )

    src.set_angular_distribution_flat(0,0,0,0)

    src.set_energy_distribution_uniform(value_min=999.8,value_max=1000.2,unit='eV')

    # print(src.info())

    beam = src.get_beam()


    print(beam.info())

    # plotxy(Beam3.initialize_from_shadow4_beam(beam),1,3,nbins=100,title="SOURCE")

    #
    # grating
    #
    g = S4EllipsoidGrating(
        name = "my_grating",
        boundary_shape = None, # BoundaryShape(),
        ruling = 800.0e3,
        ruling_coeff_linear = 0,
        ruling_coeff_quadratic = 0,
        ruling_coeff_cubic = 0,
        ruling_coeff_quartic = 0,
        coating = None,
        coating_thickness = None,
        order=1,
        maj_axis=20.0,
        min_axis=0.418848,
        pole_to_focus=10.0
        )

    coordinates_syned = ElementCoordinates(p = 30.0,
                                           q = 9.93427,
                                           angle_radial = 87.29533343 * numpy.pi / 180,
                                           angle_radial_out= 89.10466657 * numpy.pi / 180,
                                           angle_azimuthal = 0.0)



    ge = S4EllipsoidGratingElement(optical_element=g, coordinates=coordinates_syned, input_beam=beam)

    print(ge.info())

    beam_out = ge.trace_beam()

    plotxy(beam_out[0], 1, 3, title="Image 0", nbins=201)

    s4 = S4EllipsoidGrating()
    print(ge.to_python_code())
