import os, sys, numpy

from AnyQt.QtCore import Qt
from AnyQt.QtWidgets import QLabel, QApplication, QMessageBox, QSizePolicy
from AnyQt.QtGui import QTextCursor, QPixmap

import orangecanvas.resources as resources

from orangewidget import gui
from orangewidget.settings import Setting
from orangewidget.widget import Output

from oasys2.widget.widget import OWWidget, OWAction
from oasys2.widget import gui as oasysgui
from oasys2.widget.util import congruence
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from oasys2.widget.util.widget_util import EmittingStream

from orangecontrib.shadow4.util.shadow4_objects import VlsPgmPreProcessorData
from orangecontrib.shadow4.util.shadow4_util import ShadowPhysics # todo change

class OWVlsPgmCoefficientsCalculator(OWWidget):
    name = "VLS PGM Coefficients Calculator"
    id = "VlsPgmCoefficientsCalculator"
    description = "Calculation of coefficients for VLS PGM"
    icon = "icons/vls_pgm.png"
    author = "Luca Rebuffi"
    maintainer_email = "lrebuffi@anl.gov"
    priority = 100
    category = ""
    keywords = ["oasys", "vls", "pgm"]

    class Outputs:
        preprocessor_data = Output("VLS-PGM PreProcessor Data", VlsPgmPreProcessorData, default=True, auto_summary=False)

    want_main_area = True

    last_element_distance = Setting(0.0)

    r_a = Setting(0.0)
    r_b = Setting(0.0)
    k = Setting(1000)

    h = Setting(20)

    units_in_use = Setting(0)
    photon_wavelength = Setting(25.0)
    photon_energy = Setting(500.0)

    c = Setting(1.2)
    grating_diffraction_order = Setting(-1)

    new_units_in_use = Setting(0)
    new_photon_wavelength = Setting(25.0)
    new_photon_energy = Setting(500.0)
    new_c_value = Setting(1.2222)
    new_c_flag = Setting(0)

    image_path = os.path.join(resources.package_dirname("orangecontrib.shadow4.widgets.gui"), "misc", "vls_pgm_layout.png")
    usage_path = os.path.join(resources.package_dirname("orangecontrib.shadow4.widgets.gui"), "misc", "vls_pgm_usage.png")

    design_alpha = 0.0
    design_beta = 0.0

    b2 = 0.0
    b3 = 0.0
    b4 = 0.0

    shadow_coeff_0 = 0.0
    shadow_coeff_1 = 0.0
    shadow_coeff_2 = 0.0
    shadow_coeff_3 = 0.0

    d_source_to_mirror = 0.0
    d_source_plane_to_mirror = 0.0
    d_mirror_to_grating = 0.0

    raytracing_alpha = 0.0
    raytracing_beta = 0.0


    def __init__(self):

        super().__init__()

        self.runaction = OWAction("Compute", self)
        self.runaction.triggered.connect(self.compute)
        self.addAction(self.runaction)

        self.setFixedWidth(1170)
        self.setFixedHeight(500)

        gui.separator(self.controlArea)

        box0 = oasysgui.widgetBox(self.controlArea, "", orientation="horizontal")
        #widget buttons: compute, set defaults, help
        button = gui.button(box0, self, "Compute", callback=self.compute)
        button.setFixedHeight(45)
        button = gui.button(box0, self, "Defaults", callback=self.defaults)
        button.setFixedHeight(45)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(425)

        tab_step_1 = oasysgui.createTabPage(tabs_setting, "Line Density Calculation")
        tab_step_2 = oasysgui.createTabPage(tabs_setting, "Angles Calculation")
        tab_usa = oasysgui.createTabPage(tabs_setting, "Use of the Widget")
        tab_usa.setStyleSheet("background-color: white;")

        usage_box = oasysgui.widgetBox(tab_usa, "", addSpace=True, orientation="horizontal")

        label = QLabel("")
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setPixmap(QPixmap(self.usage_path))

        usage_box.layout().addWidget(label)

        box = oasysgui.widgetBox(tab_step_1, "VLS-PGM Layout Parameters", orientation="vertical")

        oasysgui.lineEdit(box, self, "r_a", "Distance Source-Grating [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box, self, "r_b", "Distance Grating-Exit Slits [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box, self, "h", "Vertical Distance Mirror-Grating [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box, self, "last_element_distance", "Distance Source-Last Image Plane\nbefore Mirror (if present) [m]", labelWidth=260, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(box, self, "k", "Line Density (0th coeff.) [Lines/m]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.separator(box)

        box_2 = oasysgui.widgetBox(tab_step_1, "Grating Design Parameters", orientation="vertical")

        gui.comboBox(box_2, self, "units_in_use", label="Units in use", labelWidth=260,
                     items=["eV", "Angstroms"],
                     callback=self.set_UnitsInUse, sendSelectedValue=False, orientation="horizontal")

        self.autosetting_box_units_1 = oasysgui.widgetBox(box_2, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.autosetting_box_units_1, self, "photon_energy", "Photon energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")

        self.autosetting_box_units_2 = oasysgui.widgetBox(box_2, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.autosetting_box_units_2, self, "photon_wavelength", "Wavelength [Å]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_UnitsInUse()

        oasysgui.lineEdit(box_2, self, "c", "C factor for optimized energy", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_2, self, "grating_diffraction_order", "Diffraction Order (- for inside orders)", labelWidth=260, valueType=int, orientation="horizontal")

        ##################################


        box_3 = oasysgui.widgetBox(tab_step_2, "Ray-Tracing Parameter", orientation="vertical")

        gui.comboBox(box_3, self, "new_units_in_use", label="Units in use", labelWidth=260,
                     items=["eV", "Angstroms"],
                     callback=self.set_UnitsInUse2, sendSelectedValue=False, orientation="horizontal")

        self.autosetting_box_units_3 = oasysgui.widgetBox(box_3, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.autosetting_box_units_3, self, "new_photon_energy", "New photon energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")

        self.autosetting_box_units_4 = oasysgui.widgetBox(box_3, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.autosetting_box_units_4, self, "new_photon_wavelength", "New wavelength [Å]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_UnitsInUse2()


        gui.comboBox(box_3, self, "new_c_flag", label="C factor for angles calculation", labelWidth=260,
                     items=["the same as for line density", "new one"],
                     callback=self.set_CfactorNew, sendSelectedValue=False, orientation="horizontal")

        self.c_box_new = oasysgui.widgetBox(box_3, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.c_box_new, self, "new_c_value", "new C for angles calculation", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_CfactorNew()


        tabs_out = oasysgui.tabWidget(self.mainArea)

        tab_out_1 = oasysgui.createTabPage(tabs_out, "Calculation Results")
        tab_out_2 = oasysgui.createTabPage(tabs_out, "Output")

        figure_box_1 = oasysgui.widgetBox(tab_out_1, "", addSpace=True, orientation="horizontal")

        label = QLabel("")
        label.setPixmap(QPixmap(self.image_path))

        figure_box_1.layout().addWidget(label)

        output_box = oasysgui.widgetBox(tab_out_1, "", addSpace=True, orientation="horizontal")

        output_box_1 = oasysgui.widgetBox(output_box, "Design Ouput", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(output_box_1, self, "design_alpha", "Alpha [deg]", labelWidth=220, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(output_box_1, self, "design_beta", "Beta [deg]", labelWidth=220, valueType=float, orientation="horizontal")
        gui.separator(output_box_1)
        oasysgui.lineEdit(output_box_1, self, "shadow_coeff_0", "Line Density 0-coeff. [Lines/m]", labelWidth=220, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(output_box_1, self, "shadow_coeff_1", "Line Density 1-coeff. [Lines/m\u00b2]", labelWidth=220, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(output_box_1, self, "shadow_coeff_2", "Line Density 2-coeff. [Lines/m\u00b3]", labelWidth=220, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(output_box_1, self, "shadow_coeff_3", "Line Density 3-coeff. [Lines/m\u00b4]", labelWidth=220, valueType=float, orientation="horizontal")

        output_box_2 = oasysgui.widgetBox(output_box, "Ray-Tracing Ouput", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(output_box_2, self, "raytracing_alpha", "Alpha [deg]", labelWidth=220, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(output_box_2, self, "raytracing_beta", "Beta [deg]", labelWidth=220, valueType=float, orientation="horizontal")
        gui.separator(output_box_2)
        oasysgui.lineEdit(output_box_2, self, "d_source_to_mirror", "Source to Mirror distance [m]", labelWidth=230, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(output_box_2, self, "d_source_plane_to_mirror", "Source Plane to Mirror distance [m]", labelWidth=230, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(output_box_2, self, "d_mirror_to_grating", "Mirror to Grating distance [m]", labelWidth=230, valueType=float, orientation="horizontal")


        self.shadow_output = oasysgui.textArea()

        out_box = oasysgui.widgetBox(tab_out_2, "System Output", addSpace=True, orientation="horizontal", height=400)
        out_box.layout().addWidget(self.shadow_output)

        gui.rubber(self.controlArea)

    def set_UnitsInUse(self):
        self.autosetting_box_units_1.setVisible(self.units_in_use == 0)
        self.autosetting_box_units_2.setVisible(self.units_in_use == 1)

    def set_UnitsInUse2(self):
        self.autosetting_box_units_3.setVisible(self.new_units_in_use == 0)
        self.autosetting_box_units_4.setVisible(self.new_units_in_use == 1)

    def set_CfactorNew(self):
        self.c_box_new.setVisible(self.new_c_flag == 1)

    @classmethod
    def calculate_vls_parameters(cls,
                                 m=-1,
                                 wavelength=1e-10,
                                 newwavelength=1e-10,
                                 k=0.0,
                                 c=1.0,
                                 r_a=0.0,
                                 r_b=0.0,
                                 h=0.0,
                                 new_c_flag=0,
                                 new_c_value=1.0,
                                 last_element_distance=0.0,
                                 verbose=1):

        sin_alpha = (-m * k * wavelength / (c ** 2 - 1)) + \
                    numpy.sqrt(1 + (m * m * c * c * k * k * wavelength * wavelength) / (
                                (c ** 2 - 1) ** 2))
        alpha = numpy.arcsin(sin_alpha)
        beta = numpy.arcsin(sin_alpha - m * k * wavelength)

        design_alpha = numpy.degrees(alpha)
        design_beta  = numpy.degrees(beta)

        if verbose:
            print("####################################################")
            print("# DESIGN PHASE")
            print("####################################################\n")

            print("Photon Wavelength [m]:", wavelength)
            print("Design ALPHA [deg]    :", round(design_alpha, 3))
            print("Design BETA [deg]     :", round(design_beta, 3))

        b2 = (((numpy.cos(alpha)**2) / r_a) + ((numpy.cos(beta)**2) / r_b)) / (-2 * m * k * wavelength)
        b3 = ((numpy.sin(alpha) * numpy.cos(alpha)**2) / r_a**2 - \
                  (numpy.sin(beta) * numpy.cos(beta)**2) / r_b**2) / (-2 * m * k * wavelength)
        b4 = (((4 * numpy.sin(alpha)**2 - numpy.cos(alpha)**2) * numpy.cos(alpha)**2) / r_a**3 + \
                  ((4 * numpy.sin(beta)**2 - numpy.cos(beta)**2) * numpy.cos(beta)**2) / r_b**3) / (-8 * m * k * wavelength)
        if verbose:
            print("\nb2:", b2)
            print("b3:",   b3)
            print("b4:",   b4)

        shadow_coeff_0 = k
        shadow_coeff_1 = -2 * k * b2
        shadow_coeff_2 = 3 * k * b3
        shadow_coeff_3 = -4 * k * b4

        if verbose:
            print("\nshadow_coeff_0:", round(shadow_coeff_0, 8))
            print("shadow_coeff_1:",   round(shadow_coeff_1, 8))
            print("shadow_coeff_2:",   round(shadow_coeff_2, 8))
            print("shadow_coeff_3:",   round(shadow_coeff_3, 8))

        ############################################
        #
        # 1 - in case of mirror recalculate real ray tracing distance (r_a') from initial r_a and vertical distance
        #     between grating and mirror (h)
        #

        gamma = (alpha + beta) / 2

        d_source_to_mirror = r_a - (h / numpy.abs(numpy.tan(numpy.pi - 2 * gamma)))
        d_mirror_to_grating = h / numpy.abs(numpy.sin(numpy.pi - 2 * gamma))

        r_a_first = d_source_to_mirror + d_mirror_to_grating

        if verbose:
            print("\ngamma [deg]                 :", numpy.degrees(gamma), "deg")
            print("Source to Mirror distance [m] :", d_source_to_mirror)
            print("Mirror to Grating distance [m]:", d_mirror_to_grating)
            print("R_a' [m]                      :", r_a_first)

        ############################################

        r = r_b / r_a_first

        A0 = k * newwavelength
        A2 = k * newwavelength * r_b * b2

        new_c_num = 2 * A2 + 4 * (A2 / A0)**2 + \
                    (4 + 2 * A2 - A0**2) * r - \
                    4 * (A2 / A0) * numpy.sqrt((1 + r)**2 + 2 * A2 * (1 + r) - r * A0**2)

        new_c_den = -4 + A0**2 - 4 * A2 + 4 * (A2 / A0)**2

        new_c = numpy.sqrt(new_c_num / new_c_den)

        if new_c_flag == 1:
            new_c = new_c_value

        new_sin_alpha = (-m * k * newwavelength / (new_c**2 - 1)) + \
                    numpy.sqrt(1 + (m * m * new_c * new_c * k * k * newwavelength * newwavelength) / ((new_c**2 - 1)**2))

        new_alpha =  numpy.arcsin(new_sin_alpha)
        new_beta  = numpy.arcsin(new_sin_alpha-m * k * newwavelength)

        raytracing_alpha = numpy.degrees(new_alpha)
        raytracing_beta  = numpy.degrees(new_beta)

        if verbose:

            #_new_beta = numpy.arccos(new_c*numpy.cos(new_alpha))

            print("####################################################")
            print("# RAY-TRACING PHASE")
            print("####################################################\n")

            print("Ray-Tracing Wavelength [m]:", newwavelength)
            print("Ray-Tracing Wavelength [A]:", newwavelength * 1e10)
            print("Ray-Tracing C         :", new_c)
            print("Ray-Tracing ALPHA     :", round(raytracing_alpha, 6), "deg")
            print("Ray-Tracing BETA      :", round(raytracing_beta, 6), "deg")

        gamma = (new_alpha + new_beta) / 2

        d_source_to_mirror  = r_a - (h / numpy.abs(numpy.tan(numpy.pi - 2 * gamma)))
        d_mirror_to_grating = h / numpy.abs(numpy.sin(numpy.pi - 2 * gamma))

        r_a_first = d_source_to_mirror + d_mirror_to_grating

        d_source_plane_to_mirror = d_source_to_mirror - last_element_distance
        if verbose:
            print("\ngamma [deg]                       :", numpy.degrees(gamma))
            print("Source to Mirror distance [m]       :", round(d_source_to_mirror, 3))
            print("Source Plane to Mirror distance [m] :", round(d_source_plane_to_mirror, 3))
            print("Mirror to Grating distance [m]      :", round(d_mirror_to_grating, 3))
            print("R_a' [m]                            :", r_a_first)

        return(
            shadow_coeff_0,
            shadow_coeff_1,
            shadow_coeff_2,
            shadow_coeff_3,
            d_source_to_mirror,
            d_source_plane_to_mirror,
            d_mirror_to_grating,
            design_alpha,
            design_beta,
            raytracing_alpha,
            raytracing_beta)




    def compute(self):
        try:
            self.shadow_output.setText("")

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.checkFields()

            m = -self.grating_diffraction_order

            if self.units_in_use == 0:
                wavelength =  ShadowPhysics.getWavelengthFromEnergy(self.photon_energy) * 1e-10
            elif self.units_in_use == 1:
                wavelength = self.photon_wavelength * 1e-10

            if self.new_units_in_use == 0:
                newwavelength =  ShadowPhysics.getWavelengthFromEnergy(self.new_photon_energy) * 1e-10
            elif self.new_units_in_use == 1:
                newwavelength = self.new_photon_wavelength * 1e-10


            shadow_coeff_0, shadow_coeff_1, shadow_coeff_2, shadow_coeff_3, \
            d_source_to_mirror, d_source_plane_to_mirror, d_mirror_to_grating, \
            design_alpha, design_beta, raytracing_alpha, raytracing_beta = \
                self.calculate_vls_parameters(
                    m=m,
                    wavelength=wavelength,
                    newwavelength=newwavelength,
                    k=self.k,
                    c=self.c,
                    r_a=self.r_a,
                    r_b=self.r_b,
                    h=self.h,
                    new_c_flag=self.new_c_flag,
                    new_c_value=self.new_c_value,
                    last_element_distance=self.last_element_distance,
                    verbose=1)

            self.shadow_coeff_0           = round(shadow_coeff_0, 3)
            self.shadow_coeff_1           = round(shadow_coeff_1, 3)
            self.shadow_coeff_2           = round(shadow_coeff_2, 3)
            self.shadow_coeff_3           = round(shadow_coeff_3, 3)
            self.d_source_plane_to_mirror = round(d_source_plane_to_mirror, 6)
            self.d_source_to_mirror       = round(d_source_to_mirror, 6)
            self.d_mirror_to_grating      = round(d_mirror_to_grating, 6)
            self.design_alpha             = round(design_alpha, 6)
            self.design_beta              = round(design_beta, 6)
            self.raytracing_alpha         = round(raytracing_alpha, 6)
            self.raytracing_beta          = round(raytracing_beta, 6)

            self.Outputs.preprocessor_data.send(VlsPgmPreProcessorData(shadow_coeff_0=self.shadow_coeff_0,
                                                                          shadow_coeff_1=self.shadow_coeff_1,
                                                                          shadow_coeff_2=self.shadow_coeff_2,
                                                                          shadow_coeff_3=self.shadow_coeff_3,
                                                                          d_source_plane_to_mirror=self.d_source_plane_to_mirror,
                                                                          d_mirror_to_grating=self.d_mirror_to_grating,
                                                                          d_grating_to_exit_slits=self.r_b,
                                                                          alpha=self.raytracing_alpha,
                                                                          beta=self.raytracing_beta))

        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)
            if self.IS_DEVELOP: raise exception

    def checkFields(self):
        self.r_a = congruence.checkPositiveNumber(self.r_a, "Distance Source-Grating")
        self.r_b = congruence.checkPositiveNumber(self.r_b, "Distance Grating-Exit Slits")
        self.last_element_distance = congruence.checkPositiveNumber(self.last_element_distance, "Distance Source-Last Image Plane before Mirror")
        congruence.checkLessOrEqualThan(self.last_element_distance, self.r_a, "Distance Source-Last Image Plane before Mirror", "Distance Source-Grating")
        self.k = congruence.checkStrictlyPositiveNumber(self.k, "Line Density")

        if self.units_in_use == 0:
            self.photon_energy = congruence.checkPositiveNumber(self.photon_energy, "Photon Energy")
        elif self.units_in_use == 1:
            self.photon_wavelength = congruence.checkPositiveNumber(self.photon_wavelength, "Photon Wavelength")

    def defaults(self):
         self._reset_settings()

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

add_widget_parameters_to_module(__name__)