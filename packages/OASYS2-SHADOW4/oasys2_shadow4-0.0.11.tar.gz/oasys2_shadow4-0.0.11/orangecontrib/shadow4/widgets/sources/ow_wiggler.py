from orangewidget import gui as orangegui
from orangewidget.settings import Setting

from oasys2.widget import gui as oasysgui
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module
from oasys2.widget.util import congruence

from syned.storage_ring.magnetic_structures.insertion_device import InsertionDevice

from shadow4.sources.wiggler.s4_wiggler import S4Wiggler
from shadow4.sources.wiggler.s4_wiggler_light_source import S4WigglerLightSource

from orangecontrib.shadow4.widgets.gui.ow_synchrotron_source import OWSynchrotronSource
from orangecontrib.shadow4.widgets.gui.plots import plot_data1D

class OWWiggler(OWSynchrotronSource):
    name = "Wiggler Light Source"
    description = "Wiggler Light Source"
    icon = "icons/wiggler.png"
    priority = 3

    magnetic_field_source = Setting(1)
    number_of_periods = Setting(1)
    k_value = Setting(10.0)
    id_period = Setting(0.010)
    file_with_b_vs_y = Setting("https://raw.githubusercontent.com/srio/shadow4/master/examples/sources/BM_multi.b")
    file_with_harmonics = Setting("tmp.h")

    shift_x_flag = Setting(0)
    shift_x_value =Setting(0.0)

    shift_betax_flag = Setting(0)
    shift_betax_value = Setting(0.0)

    e_min = Setting(0.4)
    e_max = Setting(0.4)
    number_of_rays = Setting(15000)
    seed = Setting(5676561)

    # number of points in advanced parameters
    ng_e = Setting(101)
    ng_j = Setting(501)
    psi_interval_number_of_points = Setting(101)

    flag_interpolation = Setting(0)

    plot_wiggler_graph = 1

    beam_out = None

    def __init__(self):
        super().__init__()

        tab_wiggler = oasysgui.createTabPage(self.tabs_control_area, "Wiggler Setting")

        # wiggler parameters box
        left_box_3 = oasysgui.widgetBox(tab_wiggler, "Wiggler Parameters", addSpace=False, orientation="vertical", height=200)

        orangegui.comboBox(left_box_3, self, "magnetic_field_source", tooltip="magnetic_field_source", label="Type", items=["conventional/sinusoidal", "B from file (y [m], Bz [T])", "B from harmonics"], callback=self.set_visibility, labelWidth=220, orientation="horizontal")

        oasysgui.lineEdit(left_box_3, self, "number_of_periods", "Number of Periods", tooltip="number_of_periods",labelWidth=260, valueType=int, orientation="horizontal")

        self.conventional_sinusoidal_box = oasysgui.widgetBox(left_box_3, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.conventional_sinusoidal_box, self, "k_value", "K value", labelWidth=260, tooltip="k_value", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.conventional_sinusoidal_box, self, "id_period", "ID period [m]", labelWidth=260, tooltip="id_period", valueType=float, orientation="horizontal")

        self.b_from_file_box = oasysgui.widgetBox(left_box_3, "", addSpace=False, orientation="vertical")

        file_box = oasysgui.widgetBox(self.b_from_file_box, "", addSpace=True, orientation="horizontal", height=25)

        self.le_file_with_b_vs_y = oasysgui.lineEdit(file_box, self, "file_with_b_vs_y", "File/Url with B vs Y", labelWidth=150, tooltip="file_with_b_vs_y", valueType=str, orientation="horizontal")

        orangegui.button(file_box, self, "...", callback=self.select_file_with_B_vs_Y)

        self.b_from_harmonics_box = oasysgui.widgetBox(left_box_3, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.b_from_harmonics_box, self, "id_period", "ID period [m]", labelWidth=260, tooltip="id_period", valueType=float, orientation="horizontal")

        file_box = oasysgui.widgetBox(self.b_from_harmonics_box, "", addSpace=True, orientation="horizontal", height=25)

        self.le_file_with_harmonics = oasysgui.lineEdit(file_box, self, "file_with_harmonics", "File/Url with harmonics", labelWidth=150, tooltip="file_with_harmonics", valueType=str, orientation="horizontal")

        orangegui.button(file_box, self, "...", callback=self.select_file_with_harmonics)

        # Electron initial conditions Box
        left_box_10 = oasysgui.widgetBox(tab_wiggler, "Electron Initial Condition", addSpace=False, orientation="vertical", height=200)

        orangegui.comboBox(left_box_10, self, "shift_betax_flag", tooltip="shift_betax_flag", label="Shift Transversal Velocity", items=["No shift", "Half excursion", "Minimum", "Maximum", "Value at zero", "User value"], callback=self.set_shift_beta_X_flag, labelWidth=260, orientation="horizontal")
        self.shift_betax_value_box = oasysgui.widgetBox(left_box_10, "", addSpace=False, orientation="vertical", height=25)
        self.shift_betax_value_box_hidden = oasysgui.widgetBox(left_box_10, "", addSpace=False, orientation="vertical", height=25)
        oasysgui.lineEdit(self.shift_betax_value_box, self, "shift_betax_value", "Value", tooltip="shift_betax_value", labelWidth=260, valueType=float, orientation="horizontal")

        orangegui.comboBox(left_box_10, self, "shift_x_flag", tooltip="shift_x_flag", label="Shift Transversal Coordinate", items=["No shift", "Half excursion", "Minimum", "Maximum", "Value at zero", "User value"], callback=self.set_shift_X_flag, labelWidth=260, orientation="horizontal")
        self.shift_x_value_box = oasysgui.widgetBox(left_box_10, "", addSpace=False, orientation="vertical", height=25)
        self.shift_x_value_box_hidden = oasysgui.widgetBox(left_box_10, "", addSpace=False, orientation="vertical", height=25)
        oasysgui.lineEdit(self.shift_x_value_box, self, "shift_x_value", "Value [m]", tooltip="shift_x_value", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_shift_X_flag()
        self.set_shift_beta_X_flag()

        # Calculation Box
        left_box_11 = oasysgui.widgetBox(tab_wiggler, "Sampling rays", addSpace=False, orientation="vertical", height=200)

        oasysgui.lineEdit(left_box_11, self, "e_min", "Min photon energy [eV]", tooltip="e_min", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_11, self, "e_max", "Max photon energy [eV]", tooltip="e_max", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_11, self, "number_of_rays", "Number of rays", tooltip="number_of_rays", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_11, self, "seed", "Seed", tooltip="seed", labelWidth=250, valueType=int, orientation="horizontal")

        self.set_shift_X_flag()
        self.set_shift_beta_X_flag()


        # wiggler adv settings
        tab_advanced = oasysgui.createTabPage(self.tabs_control_area, "Advanced Setting")
        left_box_adv = oasysgui.widgetBox(tab_advanced, "Advanced settings", addSpace=False, orientation="vertical", height=200)
        oasysgui.lineEdit(left_box_adv, self, "ng_e", "Number of Points in energy scan", labelWidth=260, tooltip="ng_e", valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_adv, self, "ng_j", "Number of Points in e trajectory (per period)", labelWidth=280, tooltip="ng_j", valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_adv, self, "psi_interval_number_of_points", "Number of Points in sampling vertical angle", labelWidth=280, tooltip="psi_interval_number_of_points", valueType=int, orientation="horizontal")

        orangegui.comboBox(left_box_adv, self, "flag_interpolation", tooltip="flag_interpolation", label="Sample psi via interpolation",
                           items=["No (accurate, exact Bessel)", "Yes (good for mono or quasi monochromatic)", "Yes (ray by ray)"], labelWidth=260, orientation="horizontal")


        # wiggler plots
        self.add_specific_wiggler_plots()

        self.set_visibility()

        orangegui.rubber(self.controlArea)

    def add_specific_wiggler_plots(self):
        wiggler_plot_tab = oasysgui.widgetBox(self.main_tabs, addToLayout=0, margin=4)

        self.main_tabs.insertTab(1, wiggler_plot_tab, "Wiggler Plots")

        view_box = oasysgui.widgetBox(wiggler_plot_tab, "Plotting Style", addSpace=False, orientation="horizontal")
        view_box_1 = oasysgui.widgetBox(view_box, "", addSpace=False, orientation="vertical", width=350)

        self.wiggler_view_type_combo = orangegui.comboBox(view_box_1, self,
                                            "plot_wiggler_graph",
                                                          label="Plot Graphs?",
                                                          labelWidth=220,
                                                          items=["No", "Yes"],
                                                          callback=self.refresh_specific_plots,
                                                          sendSelectedValue=False,
                                                          orientation="horizontal")

        self.wiggler_tab = []
        self.wiggler_tabs = oasysgui.tabWidget(wiggler_plot_tab)

        current_tab = self.wiggler_tabs.currentIndex()

        size = len(self.wiggler_tab)
        indexes = range(0, size)
        for index in indexes:
            self.wiggler_tabs.removeTab(size-1-index)

        self.wiggler_tab = [
            orangegui.createTabPage(self.wiggler_tabs, "Magnetic Field"),
            orangegui.createTabPage(self.wiggler_tabs, "Electron Curvature"),
            orangegui.createTabPage(self.wiggler_tabs, "Electron Velocity"),
            orangegui.createTabPage(self.wiggler_tabs, "Electron Trajectory"),
            orangegui.createTabPage(self.wiggler_tabs, "Wiggler Spectrum"),
            orangegui.createTabPage(self.wiggler_tabs, "Wiggler Spectral power")
        ]

        for tab in self.wiggler_tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

        self.wiggler_plot_canvas = [None, None, None, None, None, None]

        self.wiggler_tabs.setCurrentIndex(current_tab)

    def set_visibility(self):
        self.conventional_sinusoidal_box.setVisible(self.magnetic_field_source == 0)
        self.b_from_file_box.setVisible(self.magnetic_field_source == 1)
        self.b_from_harmonics_box.setVisible(self.magnetic_field_source == 2)

    def select_file_with_B_vs_Y(self):
        self.le_file_with_b_vs_y.setText(oasysgui.selectFileFromDialog(self, self.file_with_b_vs_y, "Open File With B vs Y"))

    def select_file_with_harmonics(self):
        self.le_file_with_harmonics.setText(oasysgui.selectFileFromDialog(self, self.file_with_harmonics, "Open File With Harmonics"))

    def set_shift_X_flag(self):
        self.shift_x_value_box.setVisible(self.shift_x_flag==5)
        self.shift_x_value_box_hidden.setVisible(self.shift_x_flag!=5)

    def set_shift_beta_X_flag(self):
        self.shift_betax_value_box.setVisible(self.shift_betax_flag==5)
        self.shift_betax_value_box_hidden.setVisible(self.shift_betax_flag!=5)

    def check_magnetic_structure(self):
        congruence.checkStrictlyPositiveNumber(self.k_value, "K Vertical")
        congruence.checkStrictlyPositiveNumber(self.number_of_periods, "Number of Periods")
        congruence.checkStrictlyPositiveNumber(self.id_period, "Period Length")

    def build_light_source(self, electron_beam, flag_emittance):
        if self.e_min == self.e_max: ng_e = 1
        else:                        ng_e = self.ng_e

        # S4Wiggler
        if self.magnetic_field_source == 0:
            sourcewiggler = S4Wiggler(
                    magnetic_field_periodic  = 1,   # 0=external, 1=periodic
                    file_with_magnetic_field = "",  # useful if magnetic_field_periodic=0
                    K_vertical                    = self.k_value,
                    period_length                 = self.id_period,
                    number_of_periods             = self.number_of_periods, # syned Wiggler pars: useful if magnetic_field_periodic=1
                    emin                          = self.e_min,     # Photon energy scan from energy (in eV)
                    emax                          = self.e_max,     # Photon energy scan to energy (in eV)
                    ng_e                          = ng_e,      # Photon energy scan number of points
                    ng_j                          = self.ng_j ,     # Number of points in electron trajectory (per period) for internal calculation only
                    psi_interval_number_of_points = self.psi_interval_number_of_points,
                    flag_interpolation            = self.flag_interpolation,  # Use intyerpolation to sample psi (0=No, 1=Yes)
                    flag_emittance                = flag_emittance, # Use emittance (0=No, 1=Yes)
                    shift_x_flag                  = 0,
                    shift_x_value                 = 0.0,
                    shift_betax_flag              = 0,
                    shift_betax_value             = 0.0,
                    )

        elif self.magnetic_field_source == 1:
            sourcewiggler = S4Wiggler(
                magnetic_field_periodic   = 0,
                file_with_magnetic_field  = self.file_with_b_vs_y,
                emin                      = self.e_min,
                emax                      = self.e_max,
                ng_e                      = ng_e,
                ng_j                      = self.ng_j,
                psi_interval_number_of_points = self.psi_interval_number_of_points,
                flag_interpolation        = self.flag_interpolation,  # Use intyerpolation to sample psi (0=No, 1=Yes)
                flag_emittance            = flag_emittance,  # Use emittance (0=No, 1=Yes)
                shift_x_flag              = 4,
                shift_x_value             = 0.0,
                shift_betax_flag          = 4,
                shift_betax_value         = 0.0,
            )
            sourcewiggler.set_electron_initial_conditions_by_label(
                position_label="value_at_zero",
                velocity_label="value_at_zero",
                )

        elif self.magnetic_field_source == 2:
            raise Exception(NotImplemented)

        if self.e_min == self.e_max:
            sourcewiggler.set_energy_monochromatic(self.e_min)

        sourcewiggler.set_electron_initial_conditions(
                        shift_x_flag=self.shift_x_flag,
                        shift_x_value=self.shift_x_value,
                        shift_betax_flag=self.shift_betax_flag,
                        shift_betax_value=self.shift_betax_value)

        print("***** \n\n S4Wiggler get_info: \n", sourcewiggler.get_info())

        # S4WigglerLightSource
        try:    name = self.getNode().title
        except: name = "Wiggler Light Source"

        light_source = S4WigglerLightSource(name=name,
                                           electron_beam=electron_beam,
                                           magnetic_structure=sourcewiggler,
                                           nrays=self.number_of_rays,
                                           seed=self.seed)

        print("\n\n***** S4WigglerLightSource info: \n", light_source.info())

        return light_source

    def refresh_specific_plots(self):
        if self.plot_wiggler_graph == 0:
            for wiggler_plot_slot_index in range(6):
                current_item = self.wiggler_tab[wiggler_plot_slot_index].layout().itemAt(0)
                self.wiggler_tab[wiggler_plot_slot_index].layout().removeItem(current_item)
                plot_widget_id = oasysgui.QLabel() # TODO: is there a better way to clean this??????????????????????
                self.wiggler_tab[wiggler_plot_slot_index].layout().addWidget(plot_widget_id)
        else:
            if self.light_source is None: return

            e, f, w    = self.light_source.calculate_spectrum()
            traj, pars = self.light_source.get_trajectory()

            self.plot_widget_item(traj[1, :],traj[7, :],0,
                                  title="Magnetic Field",xtitle="y [m]",ytitle="B [T]")

            self.plot_widget_item(traj[1, :],traj[6, :],1,
                                  title="Electron curvature",xtitle="y [m]",ytitle="curvature [m^-1]")

            self.plot_widget_item(traj[1, :],traj[3, :],2,
                                  title="Electron velocity",xtitle="y [m]",ytitle="BetaX")

            self.plot_widget_item(traj[1, :],traj[0, :],3,
                                  title="Electron trajectory",xtitle="y [m]",ytitle="x [m]")

            self.plot_widget_item(e,f,4,
                                  title="Wiggler spectrum (current = %5.1f)"%self.ring_current,
                                  xtitle="Photon energy [eV]",ytitle=r"Photons/s/0.1%bw")

            self.plot_widget_item(e,w,5,
                                  title="Wiggler spectrum (current = %5.1f)"%self.ring_current,
                                  xtitle="Photon energy [eV]",ytitle="Spectral power [W/eV]")

    def plot_widget_item(self,x,y,wiggler_plot_slot_index,title="",xtitle="",ytitle=""):
        self.wiggler_tab[wiggler_plot_slot_index].layout().removeItem(self.wiggler_tab[wiggler_plot_slot_index].layout().itemAt(0))
        plot_widget_id = plot_data1D(x.copy(),y.copy(),title=title,xtitle=xtitle,ytitle=ytitle,symbol='.')
        self.wiggler_tab[wiggler_plot_slot_index].layout().addWidget(plot_widget_id)

    def populate_fields_from_magnetic_structure(self, magnetic_structure, electron_beam):
        if isinstance(magnetic_structure, InsertionDevice):
            self.magnetic_field_source = 0
            self.set_visibility()

            self.number_of_periods = int(magnetic_structure.number_of_periods())
            self.id_period         = magnetic_structure.period_length()
            self.k_value           = magnetic_structure.K_vertical()

add_widget_parameters_to_module(__name__)


