import sys, numpy

from AnyQt.QtWidgets import QMessageBox

from matplotlib import rcParams

from silx.gui.plot import Plot2D

from orangewidget import gui
from orangewidget.settings import Setting
from orangewidget.widget import Input, Output

from oasys2.widget.widget import OWAction
from oasys2.widget import gui as oasysgui
from oasys2.widget.util import congruence
from oasys2.widget.util.widget_util import EmittingStream
from oasys2.widget.util.widget_objects import TriggerIn
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from syned.beamline.element_coordinates import ElementCoordinates

from orangecontrib.shadow4.util.shadow4_objects import ShadowData
from orangecontrib.shadow4.util.shadow4_util import ShadowCongruence, TriggerToolsDecorator
from orangecontrib.shadow4.widgets.gui.ow_generic_element import GenericElement

from shadow4_advanced.fresnel_zone_plate.s4_fresnel_zone_plate import (S4FresnelZonePlate, S4FresnelZonePlateElement,
                                                                       FZPCalculationInputParameters, FZPAttributes, FZPSimulatorOptions, FZPCalculationResult)
GOOD = 1

COLLIMATED_SOURCE_LIMIT = 1e4 #m

class FresnelZonePlate(GenericElement, TriggerToolsDecorator):
    name = "Hybrid Fresnel Zone Plate"
    description = "Advanced: Fresnel Zone Plate"
    icon = "icons/zone_plate.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 4
    category = "Optical Elements"
    keywords = ["data", "file", "load", "read"]

    class Inputs:
        shadow_data = Input("Shadow Data", ShadowData, default=True, auto_summary=False)
        trigger     = TriggerToolsDecorator.get_trigger_input()

    class Outputs:
        shadow_data = Output("Shadow Data", ShadowData, default=True, auto_summary=False)
        trigger     = TriggerToolsDecorator.get_trigger_output()

    input_data = None
    output_data = None

    NONE_SPECIFIED = "NONE SPECIFIED"

    ONE_ROW_HEIGHT = 65
    TWO_ROW_HEIGHT = 110
    THREE_ROW_HEIGHT = 170

    INNER_BOX_WIDTH_L3=322
    INNER_BOX_WIDTH_L2=335
    INNER_BOX_WIDTH_L1=358
    INNER_BOX_WIDTH_L0=375

    source_plane_distance = Setting(10.0)
    image_plane_distance  = Setting(20.0)

    height = Setting(400.0) # nm
    diameter = Setting(50.0) # um
    b_min = Setting(50.0) # nm
    zone_plate_material = Setting('Au')
    template_material = Setting('SiO2')

    zone_plate_type = Setting(0)
    width_coating = Setting(20) # nm
    height1_factor = Setting(0.33)
    height2_factor = Setting(0.67)

    with_central_stop = Setting(0)
    cs_diameter = Setting(10.0) # um

    with_order_sorting_aperture = Setting(0)

    osa_position = Setting(10.0) # user units
    osa_diameter =  Setting(30.0) # um

    source_distance_flag = Setting(0)
    source_distance = Setting(0.0)

    image_distance_flag = Setting(1)
    image_distance = Setting(0.0)

    multipool = Setting(1)

    with_multi_slicing = Setting(0)
    n_slices = Setting(100)

    increase_resolution = Setting(1)
    increase_points = Setting(200)

    n_points = Setting(5000)
    last_index = Setting(100)

    ##################################################

    avg_energy = 0.0
    number_of_zones = 0
    focal_distance = 0.0
    efficiency = 0.0

    def __init__(self):
        super(FresnelZonePlate, self).__init__(show_automatic_box=True, has_footprint=False)

        self.runaction = OWAction("Run Shadow4/Trace", self)
        self.runaction.triggered.connect(self.run_shadow4)
        self.addAction(self.runaction)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run Shadow4/Trace", callback=self.run_shadow4)
        button.setStyleSheet("color: darkblue; font-weight: bold; height: 45px;")

        button = gui.button(button_box, self, "Reset Fields", callback=self.callResetSettings)
        button.setStyleSheet("color: darkred; font-weight: bold; font-style: italic; height: 45px; width: 150px;")

        gui.separator(self.controlArea)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_pos = oasysgui.createTabPage(tabs_setting, "Position")

        upper_box = oasysgui.widgetBox(tab_pos, "Optical Element Orientation", addSpace=True, orientation="vertical")

        self.le_source_plane_distance = oasysgui.lineEdit(upper_box, self, "source_plane_distance", "Source Plane Distance [m]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_image_plane_distance  = oasysgui.lineEdit(upper_box, self, "image_plane_distance", "Image Plane Distance [m]", labelWidth=260, valueType=float, orientation="horizontal")

        tab_bas = oasysgui.createTabPage(tabs_setting, "Settings")

        ##########################################
        ##########################################
        # BASIC SETTINGS
        ##########################################
        ##########################################

        tabs_basic_setting = oasysgui.tabWidget(tab_bas)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT-5)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_zone_plate_1 = oasysgui.createTabPage(tabs_basic_setting, "Input Parameters")
        tab_zone_plate_2 = oasysgui.createTabPage(tabs_basic_setting, "Propagation Parameters")
        tab_zone_plate_3 = oasysgui.createTabPage(tabs_basic_setting, "Output Parameters")

        zp_box = oasysgui.widgetBox(tab_zone_plate_1, "F.Z.P. Parameters", addSpace=False, orientation="vertical", height=475)

        oasysgui.lineEdit(zp_box, self, "b_min",  "Outermost Zone Width/Period [nm]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(zp_box, self, "diameter", "F.Z.P. Diameter [" + u"\u03BC" + "m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(zp_box, self, "height",  "F.Z.P. Height [nm]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(zp_box, self, "zone_plate_type", label="Type of F.Z.P.", labelWidth=350,
                     items=["Ordinary", "Zone-Doubled", "Zone-Filled", "Two-Level"],
                     callback=self.set_FZPType, sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(zp_box, self, "zone_plate_material",  "F.Z.P. Material", labelWidth=160, valueType=str, orientation="horizontal")

        self.ord_box = oasysgui.widgetBox(zp_box, "", addSpace=False, orientation="vertical", height=60)

        self.zd_box = oasysgui.widgetBox(zp_box, "", addSpace=False, orientation="vertical", height=60)
        oasysgui.lineEdit(self.zd_box, self, "template_material",  "Template Material", labelWidth=160, valueType=str, orientation="horizontal")
        oasysgui.lineEdit(self.zd_box, self, "width_coating",  "Coating Width [nm]", labelWidth=260, valueType=float, orientation="horizontal")

        self.zf_box = oasysgui.widgetBox(zp_box, "", addSpace=False, orientation="vertical", height=60)
        oasysgui.lineEdit(self.zf_box, self, "template_material", "Template Material", labelWidth=160, valueType=str, orientation="horizontal")
        oasysgui.lineEdit(self.zf_box, self, "width_coating", "Coating Width [nm]", labelWidth=260, valueType=float, orientation="horizontal")

        self.tl_box = oasysgui.widgetBox(zp_box, "", addSpace=False, orientation="vertical", height=60)
        oasysgui.lineEdit(self.tl_box, self, "height1_factor",  "Height 1 Factor", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.tl_box, self, "height2_factor",  "Height 2 Factor", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_FZPType()

        gui.comboBox(zp_box, self, "with_central_stop", label="With Central Stop", labelWidth=350,
                     items=["No", "Yes"],
                     callback=self.set_WithCentralStop, sendSelectedValue=False, orientation="horizontal")

        self.cs_box_1 = oasysgui.widgetBox(zp_box, "", addSpace=False, orientation="vertical", height=30)
        self.cs_box_2 = oasysgui.widgetBox(zp_box, "", addSpace=False, orientation="vertical", height=30)

        oasysgui.lineEdit(self.cs_box_1, self, "cs_diameter", "C.S. Diameter [" + u"\u03BC" + "m]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_WithCentralStop()

        gui.comboBox(zp_box, self, "with_order_sorting_aperture", label="With Order Sorting Aperture", labelWidth=350,
                     items=["No", "Yes"],
                     callback=self.set_WithOrderSortingAperture, sendSelectedValue=False, orientation="horizontal")

        self.osa_box_1 = oasysgui.widgetBox(zp_box, "", addSpace=False, orientation="vertical", height=60)
        self.osa_box_2 = oasysgui.widgetBox(zp_box, "", addSpace=False, orientation="vertical", height=60)

        self.le_osa_position = oasysgui.lineEdit(self.osa_box_1, self, "osa_position", "O.S.A. position [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.osa_box_1, self, "osa_diameter", "O.S.A. Diameter [" + u"\u03BC" + "m]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_WithOrderSortingAperture()

        gui.comboBox(zp_box, self, "source_distance_flag", label="Source Distance", labelWidth=350,
                     items=["Same as Source Plane", "Different"],
                     callback=self.set_SourceDistanceFlag, sendSelectedValue=False, orientation="horizontal")

        self.zp_box_1 = oasysgui.widgetBox(zp_box, "", addSpace=False, orientation="vertical", height=30)
        self.zp_box_2 = oasysgui.widgetBox(zp_box, "", addSpace=False, orientation="vertical", height=30)

        self.le_source_distance = oasysgui.lineEdit(self.zp_box_1, self, "source_distance", "Source Distance [m]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_SourceDistanceFlag()

        gui.comboBox(zp_box, self, "image_distance_flag", label="Image Distance [m]", labelWidth=350,
                     items=["Image Plane Distance", "F.Z.P. Image Distance"],
                     callback=self.set_ImageDistanceFlag, sendSelectedValue=False, orientation="horizontal")

        self.set_ImageDistanceFlag()

        prop_box = oasysgui.widgetBox(tab_zone_plate_2, "Propagation Parameters", addSpace=False, orientation="vertical", height=270)

        oasysgui.lineEdit(prop_box, self, "n_points", "Nr. Sampling Points", labelWidth=260, valueType=int, orientation="horizontal")

        oasysgui.lineEdit(prop_box, self, "last_index", "Last Index of Focal Image", labelWidth=260, valueType=int, orientation="horizontal")

        gui.separator(prop_box)

        gui.comboBox(prop_box, self, "increase_resolution", label="Increase Resolution in Focal Image", labelWidth=350,
                     items=["No", "Yes"],
                     callback=self.set_IncreaseResolution, sendSelectedValue=False, orientation="horizontal")

        self.res_box_1 = oasysgui.widgetBox(prop_box, "", addSpace=False, orientation="vertical", height=30)
        self.res_box_2 = oasysgui.widgetBox(prop_box, "", addSpace=False, orientation="vertical", height=30)

        oasysgui.lineEdit(self.res_box_1, self, "increase_points", "Nr. Points", labelWidth=260, valueType=int, orientation="horizontal")

        self.set_IncreaseResolution()

        gui.separator(prop_box)

        gui.comboBox(prop_box, self, "multipool", label="Parallel Computing", labelWidth=350,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")


        zp_out_box = oasysgui.widgetBox(tab_zone_plate_3, "Output Parameters", addSpace=False, orientation="vertical", height=270)

        read_only_style = "color: darkblue; background-color: rgb(243, 240, 160); font-weight: bold;"

        self.le_avg_wavelength = oasysgui.lineEdit(zp_out_box, self, "avg_energy", "Average Energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_avg_wavelength.setReadOnly(True)
        self.le_avg_wavelength.setStyleSheet(read_only_style)

        self.le_number_of_zones = oasysgui.lineEdit(zp_out_box, self, "number_of_zones", "Number of Zones", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_number_of_zones.setReadOnly(True)
        self.le_number_of_zones.setStyleSheet(read_only_style)

        self.le_focal_distance = oasysgui.lineEdit(zp_out_box, self, "focal_distance", "Focal Distance [m]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_focal_distance.setReadOnly(True)
        self.le_focal_distance.setStyleSheet(read_only_style)

        self.le_image_distance = oasysgui.lineEdit(zp_out_box, self, "image_distance", "Image Distance (Q) [m]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_image_distance.setReadOnly(True)
        self.le_image_distance.setStyleSheet(read_only_style)

        self.le_efficiency = oasysgui.lineEdit(zp_out_box, self, "efficiency", "Efficiency % (Avg. Wavelength)", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_efficiency.setReadOnly(True)
        self.le_efficiency.setStyleSheet(read_only_style)


        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)

        propagation_plot_tab = oasysgui.widgetBox(self.main_tabs, addToLayout=0, margin=4)

        self.main_tabs.insertTab(1, propagation_plot_tab, "TEMP")
        self.main_tabs.setTabText(0, "Shadow Plot")
        self.main_tabs.setTabText(1, "F.Z.P. Simulator Plot")

        self.prop_tabs = oasysgui.tabWidget(propagation_plot_tab)
        self.prop_tab = [oasysgui.createTabPage(self.prop_tabs, "Radial Intensity"),
                         oasysgui.createTabPage(self.prop_tabs, "Generated 2D distribution")]
        self.prop_plot_canvas = [None, None]

    def run_shadow4(self, scanning_data: ShadowData.ScanningData = None):
        if self.input_data is None:
            self.prompt_exception(ValueError("No input beam"))
            return
        if not scanning_data: scanning_data = None

        try:
            self.setStatusMessage("")
            self.progressBarInit()

            if ShadowCongruence.check_empty_data(self.input_data):
                if ShadowCongruence.check_good_beam(self.input_data.beam):
                    self.checkFields()

                    sys.stdout = EmittingStream(textWritten=self._write_stdout)

                    beamline = self.input_data.beamline.duplicate()

                    self.progressBarSet(10)

                    if self.source_distance_flag == 0: self.source_distance = self.source_plane_distance

                    input_parameters = FZPCalculationInputParameters(source_distance=self.source_distance,
                                                                     image_distance=self.image_plane_distance if self.image_distance_flag==0 else None,
                                                                     n_points=self.n_points,
                                                                     multipool=self.multipool==1,
                                                                     profile_last_index=self.last_index,
                                                                     increase_resolution=self.increase_resolution==1,
                                                                     increase_points=self.increase_points)
                    options = FZPSimulatorOptions(with_central_stop=self.with_central_stop==1,
                                                  cs_diameter=round(self.cs_diameter*1e-6, 7),
                                                  with_order_sorting_aperture=self.with_order_sorting_aperture==1,
                                                  osa_position=self.osa_position,
                                                  osa_diameter=round(self.osa_diameter*1e-6, 7),
                                                  zone_plate_type=self.zone_plate_type,
                                                  width_coating=round(self.width_coating*1e-9, 10),
                                                  height1_factor=self.height1_factor,
                                                  height2_factor=self.height2_factor,
                                                  with_range=False,
                                                  with_multi_slicing=self.with_multi_slicing==1,
                                                  n_slices=self.n_slices,
                                                  with_complex_amplitude=False,
                                                  store_partial_results=False)
                    attributes = FZPAttributes(height=round(self.height*1e-9, 10),
                                               diameter=round(self.diameter*1e-6, 7),
                                               b_min=round(self.b_min*1e-9, 10),
                                               zone_plate_material=self.zone_plate_material,
                                               template_material=self.template_material)

                    self.progressBarSet(30)

                    element = S4FresnelZonePlateElement(optical_element=S4FresnelZonePlate(input_parameters=input_parameters,
                                                                                           options=options,
                                                                                           attributes=attributes),
                                                        coordinates=ElementCoordinates(p=self.source_distance, q=self.image_distance),
                                                        input_beam=self.input_data.beam)
                    #element.set_movements(self.get_movements_instance()) for the future

                    print(element.info())

                    output_beam, calculation_result = element.trace_beam()

                    zone_plate_out = element.get_optical_element()

                    self.avg_energy      = 1e3*zone_plate_out.get_energy_in_KeV()
                    self.image_distance  = round(zone_plate_out.zp_image_distance, 6)
                    self.number_of_zones = zone_plate_out.get_n_zones()
                    self.focal_distance  = round(zone_plate_out.zp_focal_distance, 6)
                    self.efficiency      = round(calculation_result.efficiency*100, 2)

                    self.plot_propagation_results(calculation_result)

                    self.progressBarSet(80)

                    self.setStatusMessage("Plotting Results")

                    self._plot_results(output_beam, None)

                    self.setStatusMessage("")

                    beamline.append_beamline_element(element)

                    script = beamline.to_python_code()
                    script += "\n\n\n# test plot"
                    script += "\nif True:"
                    script += "\n   from srxraylib.plot.gol import plot_scatter"
                    script += "\n   plot_scatter(beam.get_photon_energy_eV(nolost=1), beam.get_column(23, nolost=1), title='(Intensity,Photon Energy)', plot_histograms=0)"
                    script += "\n   plot_scatter(1e6 * beam.get_column(1, nolost=1), 1e6 * beam.get_column(3, nolost=1), title='(X,Z) in microns')"
                    self.shadow4_script.set_code(script)

                    #
                    # send beam and trigger
                    #
                    output_data = ShadowData(beam=output_beam, beamline=beamline)
                    output_data.scanning_data = scanning_data

                    self.Outputs.shadow_data.send(output_data)
                    self.Outputs.trigger.send(TriggerIn(new_object=True))
                else:
                    raise Exception("Input Beam with no good rays")
            else:
                raise Exception("Empty Input Beam")

        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

        self.progressBarFinished()

    @Inputs.trigger
    def set_trigger_parameters_for_optics(self, trigger):
        super(FresnelZonePlate, self).set_trigger_parameters_for_optics(trigger)

    @Inputs.shadow_data
    def set_input_data(self, shadow_data):
        if ShadowCongruence.check_empty_data(shadow_data):
            self.input_data = shadow_data

            if self.is_automatic_run:
                self.run_shadow4()

    def checkFields(self):
        self.source_plane_distance = congruence.checkNumber(self.source_plane_distance, "Source plane distance")
        self.image_plane_distance = congruence.checkNumber(self.image_plane_distance, "Image plane distance")

    def callResetSettings(self):
        super()._call_reset_settings()

    def set_SourceMovement(self):
        self.sou_mov_box_1.setVisible(self.source_movement == 1)

    def set_MirrorMovement(self):
        self.mir_mov_box_1.setVisible(self.mirror_movement == 1)

    def set_FZPType(self):
        self.ord_box.setVisible(self.zone_plate_type == 0)
        self.zd_box.setVisible(self.zone_plate_type == 1)
        self.zf_box.setVisible(self.zone_plate_type == 2)
        self.tl_box.setVisible(self.zone_plate_type == 3)

    def set_SourceDistanceFlag(self):
        self.zp_box_1.setVisible(self.source_distance_flag == 1)
        self.zp_box_2.setVisible(self.source_distance_flag == 0)

    def set_WithCentralStop(self):
        self.cs_box_1.setVisible(self.with_central_stop == 1)
        self.cs_box_2.setVisible(self.with_central_stop == 0)

    def set_WithOrderSortingAperture(self):
        self.osa_box_1.setVisible(self.with_order_sorting_aperture == 1)
        self.osa_box_2.setVisible(self.with_order_sorting_aperture == 0)

    def set_WithMultislicing(self):
        self.ms_box_1.setVisible(self.with_multi_slicing == 1)
        self.ms_box_2.setVisible(self.with_multi_slicing == 0)

    def set_IncreaseResolution(self):
        self.res_box_1.setVisible(self.increase_resolution == 1)
        self.res_box_2.setVisible(self.increase_resolution == 0)

    def set_ImageDistanceFlag(self):
        self.le_image_plane_distance.setEnabled(self.image_distance_flag==0)

    def plot_propagation_results(self, calculation_result : FZPCalculationResult):
        self.plot_1D(0, calculation_result.radius*1e6, calculation_result.intensity_profile)
        self.plot_2D(1, calculation_result.xp * 1e6, calculation_result.zp * 1e6, calculation_result.dif_xpzp)

    def plot_1D(self, index, radius, profile_1D, replace=True, profile_name="z pos #1", control=False, color='blue'):
        if self.prop_plot_canvas[index] is None:
            self.prop_plot_canvas[index] = oasysgui.plotWindow(parent=None,
                                                               backend=None,
                                                               resetzoom=True,
                                                               autoScale=True,
                                                               logScale=True,
                                                               grid=True,
                                                               curveStyle=True,
                                                               colormap=False,
                                                               aspectRatio=False,
                                                               yInverted=False,
                                                               copy=True,
                                                               save=True,
                                                               print_=True,
                                                               control=control,
                                                               position=True,
                                                               roi=False,
                                                               mask=False,
                                                                fit=True)

            self.prop_plot_canvas[index].setDefaultPlotLines(True)
            self.prop_plot_canvas[index].setActiveCurveStyle(color="#00008B")
            self.prop_tab[index].layout().addWidget(self.prop_plot_canvas[index])

        title  = "Radial Intensity Profile"
        xtitle = "Radius [\u03bcm]"
        ytitle = "Intensity [A.U.]"

        self.prop_plot_canvas[index].setGraphTitle(title)
        self.prop_plot_canvas[index].setGraphXLabel(xtitle)
        self.prop_plot_canvas[index].setGraphYLabel(ytitle)

        rcParams['axes.formatter.useoffset']='False'

        self.prop_plot_canvas[index].addCurve(radius, profile_1D, profile_name, symbol='', color=color, xlabel=xtitle, ylabel=ytitle, replace=replace) #'+', '^', ','

        self.prop_plot_canvas[index].setInteractiveMode('zoom', color='orange')
        self.prop_plot_canvas[index].resetZoom()
        self.prop_plot_canvas[index].replot()

        self.prop_plot_canvas[index].setActiveCurve("Radial Intensity Profile")

    def plot_2D(self, index, dataX, dataY, data2D):
        origin = (dataX[0], dataY[0])
        scale = (dataX[1] - dataX[0], dataY[1] - dataY[0])

        colormap = {"name": "temperature", "normalization": "linear", "autoscale": True, "vmin": 0, "vmax": 0, "colors": 256}

        if self.prop_plot_canvas[index] is None:
            self.prop_plot_canvas[index] = Plot2D()

            self.prop_plot_canvas[index].resetZoom()
            self.prop_plot_canvas[index].setXAxisAutoScale(True)
            self.prop_plot_canvas[index].setYAxisAutoScale(True)
            self.prop_plot_canvas[index].setGraphGrid(False)
            self.prop_plot_canvas[index].setKeepDataAspectRatio(True)
            self.prop_plot_canvas[index].yAxisInvertedAction.setVisible(False)

            self.prop_plot_canvas[index].setXAxisLogarithmic(False)
            self.prop_plot_canvas[index].setYAxisLogarithmic(False)

            self.prop_plot_canvas[index].getMaskAction().setVisible(False)
            self.prop_plot_canvas[index].getRoiAction().setVisible(False)
            self.prop_plot_canvas[index].getColormapAction().setVisible(True)
            self.prop_plot_canvas[index].setKeepDataAspectRatio(False)

            self.prop_tab[index].layout().addWidget(self.prop_plot_canvas[index])
            
        self.prop_plot_canvas[index].clear()
        self.prop_plot_canvas[index].addImage(numpy.array(data2D),
                                              legend="rotated",
                                              scale=scale,
                                              origin=origin,
                                              colormap=colormap,
                                              replace=True)

        self.prop_plot_canvas[index].setActiveImage("rotated")
        self.prop_plot_canvas[index].setGraphXLabel("X' [\u03bcrad]")
        self.prop_plot_canvas[index].setGraphYLabel("Z' [\u03bcrad]")
        self.prop_plot_canvas[index].setGraphTitle("2D Divergence Profile")

add_widget_parameters_to_module(__name__)