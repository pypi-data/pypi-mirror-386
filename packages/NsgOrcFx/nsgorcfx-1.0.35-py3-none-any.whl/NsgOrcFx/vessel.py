import math
from typing import TextIO
import os
import OrcFxAPI as _ofx
import pandas as pd
from . import utils as _utils

from dataclasses import dataclass
@dataclass
class VesselResponseDofSet:
    surge: float|None = None
    sway: float|None = None
    heave: float|None = None
    roll: float|None = None
    pitch: float|None = None
    yaw: float|None = None
    extreme_result: str|None = None # e.g., 'Significant Amplitude', 'Maximum Amplitude', 'Average Period'

    @staticmethod
    def header_list(translation_unit: str, rotation_unit: str) -> list[str]:
        """
        Returns the header list in the order: Surge,Sway,Heave,Roll,Pitch,Yaw
        """
        return [
            f'Surge [{translation_unit}]',
            f'Sway [{translation_unit}]',
            f'Heave [{translation_unit}]',
            f'Roll [{rotation_unit}]',
            f'Pitch [{rotation_unit}]',
            f'Yaw [{rotation_unit}]'
        ]

    def values_to_list(self) -> list[float]:
        """
        Returns the values as a list in the order: Surge,Sway,Heave,Roll,Pitch,Yaw
        """
        return [
            self.surge,
            self.sway,
            self.heave,
            self.roll,
            self.pitch,
            self.yaw
        ]

    @staticmethod
    def from_str(line: str, extreme_result: str) -> 'VesselResponseDofSet':
        """
        Import the values assuming the current line is:
        ',value,value,value,value,value,value,value'
        where the values are in the order: Surge,Sway,Heave,Roll,Pitch,Yaw,Z above wave
        """
        values = line.strip().split(',')

        def parse_value(val: str) -> float|None:
            val = val.strip()
            if val == '':
                return None
            if val.lower() == 'n/a':
                return 0.0
            return float(val)

        return VesselResponseDofSet(
            surge=parse_value(values[2]),
            sway=parse_value(values[3]),
            heave=parse_value(values[4]),
            roll=parse_value(values[5]),
            pitch=parse_value(values[6]),
            yaw=parse_value(values[7]),
            extreme_result=extreme_result
        )
    
    def rotation_combined(self) -> float|None:
        """
        Returns the combined roll + pitch value
        """
        if self.roll is None or self.pitch is None:
            raise Exception('Error! Cannot compute combined roll + pitch because one of the values is None.')
        return (self.roll**2 + self.pitch**2)**0.5

@dataclass
class VesselSignificantAmpVelocityAvePeriod:
    significant_amp: VesselResponseDofSet
    maximum_amp: VesselResponseDofSet
    average_period: VesselResponseDofSet
    translation_unit: str = 'm'
    rotation_unit: str = 'deg'   
    point_coords: list[float]|None = None
    extreme_quantity: str|None = None # e.g., 'Position', 'Velocity', 'Acceleration'

    def to_multiheader_list(self) -> list[tuple[str, str, str]]:
        """
        Returns the values as a list of tuples with multi-header info
        Each tuple contains: (extreme quantity, result, dof [unit]):
        * extreme quantity: 'Position', 'Velocity', 'Acceleration' with the point coordinates if available
        * result: 'Significant Amplitude', 'Maximum Amplitude', 'Average Period'
        * dof [unit]: 'Surge [m]', 'Sway [m]', 'Heave [m]', 'Roll [deg]', 'Pitch [deg]', 'Yaw [deg]'
        """
        headers = []
        title = f'{self.extreme_quantity} of point {tuple(self.point_coords)}'

        for respSet in [self.significant_amp, self.maximum_amp, self.average_period]:
            if respSet is None:
                raise Exception('Error! Cannot export to multi-header list because one of the response sets is None.')
            
            for dof_header in VesselResponseDofSet.header_list(
                    self.translation_unit, 
                    self.rotation_unit
                    ):
                headers.append( (title, respSet.extreme_result, dof_header) )

        return headers
    
    def values_to_list(self) -> list[float]:
        """
        Returns the values as a list in the order:
        Significant Amplitude (Surge,Sway,Heave,Roll,Pitch,Yaw),
        Maximum Amplitude (Surge,Sway,Heave,Roll,Pitch,Yaw),
        Average Period (Surge,Sway,Heave,Roll,Pitch,Yaw)
        """
        values = []
        for respSet in [self.significant_amp, self.maximum_amp, self.average_period]:
            if respSet is None:
                raise Exception('Error! Cannot export values to list because one of the response sets is None.')
            values.extend( respSet.values_to_list() )
        return values    

    @staticmethod
    def from_file(file: TextIO, extreme_quantity: str) -> 'VesselSignificantAmpVelocityAvePeriod':
        """
        Import the values assuming the current line is ',,Surge,Sway,Heave,Roll,Pitch,Yaw,Z above wave'
        the next line is expected to be:
        ',,(translation unit),(translation unit),(translation unit),(rotation unit),(rotation unit),(rotation unit),(rotation unit)'
        then the next line is expected to be the significant amplitudes:
        ',Significant amplitude,value,value,value,value,value,value,value'
        then the next is expected to be the max. amplitude for the defined storm duration (e.g., 3 hours):
        ',3 hour max amplitude,value,value,value,value,value,value,value'
        finally the next line is expected to be the average period
        ',Average period (s),value,value,value,value,value,value,value'
        """
        # read relevant lines

        # get coords from title line:
        # ,"Position of point (310.1,0,0) (m)"     
        title = file.readline() 
        if 'of point' in title:
            coord_str = title.split('(')[1].split(')')[0]
            point_coords = [float(c) for c in coord_str.split(',')]

        header = file.readline() # skip header line
        unitsLine = file.readline() # read units line
        significanAmpValues = file.readline()
        maxAmpValues = file.readline()
        averagePeriodValues = file.readline()

        newObj = VesselSignificantAmpVelocityAvePeriod(None, None, None, extreme_quantity=extreme_quantity)
        newObj.point_coords = point_coords

        # set units
        units = unitsLine.strip().split(',')
        newObj.translation_unit = units[2].replace('(', '').replace(')', '')
        newObj.rotation_unit = units[5].replace('(', '').replace(')', '')


        # set significant amplitudes, maximum amplitudes, and average periods
        newObj.significant_amp = VesselResponseDofSet.from_str(significanAmpValues, 'Significant Amplitude')
        newObj.maximum_amp = VesselResponseDofSet.from_str(maxAmpValues, 'Maximum Amplitude')
        newObj.average_period = VesselResponseDofSet.from_str(averagePeriodValues, 'Average Period')

        return newObj

@dataclass
class VesselResponses:
    positionExtremes: VesselSignificantAmpVelocityAvePeriod
    velocityExtremes: VesselSignificantAmpVelocityAvePeriod
    accelerationExtremes: VesselSignificantAmpVelocityAvePeriod
    draught: str
    waveDir: str
    Hs: float
    Tp: float

    def to_multiheader_list(self) -> list[tuple[str, str, str]]:
        """
        Returns the values as a list of tuples with multi-header info
        Each tuple contains: (extreme quantity, result, dof [unit]):
        * extreme quantity: 'Position', 'Velocity', 'Acceleration' with the point coordinates if available
        * result: 'Significant Amplitude', 'Maximum Amplitude', 'Average Period'
        * dof [unit]: 'Surge [m]', 'Sway [m]', 'Heave [m]', 'Roll [deg]', 'Pitch [deg]', 'Yaw [deg]'
        """
        headers = []
        for resp in [self.positionExtremes, self.velocityExtremes, self.accelerationExtremes]:
            headers.extend( resp.to_multiheader_list() )
        return headers
    
    def values_to_list(self) -> list[float]:
        """
        Returns the values as a list in the order:
        Position Extremes (Significant Amplitude, Maximum Amplitude, Average Period),
        Velocity Extremes (Significant Amplitude, Maximum Amplitude, Average Period),
        Acceleration Extremes (Significant Amplitude, Maximum Amplitude, Average Period)
        """
        values = []
        for resp in [self.positionExtremes, self.velocityExtremes, self.accelerationExtremes]:
            values.extend( resp.values_to_list() )
        return values

    @staticmethod
    def from_file(path: str, draught: str, waveDir: str, Hs: float, Tp: float) -> 'VesselResponses':
        """
        Import the values from the specified file path
        """

        with open(path, 'r') as file:
            # skip header lines
            file.readline() # skip first header line
            file.readline() # skip empty line
            file.readline() # skip wave direction line
            file.readline() # skip line containing "Amplitudes are reported as single amplitudes, i.e. the motion is +/- the value reported."

            # position extremes
            file.readline() # skip empty line
            # file.readline() # skip Position header line
            positionExtremes = VesselSignificantAmpVelocityAvePeriod.from_file(file, 'Position')

            # velocity extremes
            file.readline() # skip empty line
            # file.readline() # skip Velocity header line
            velocityExtremes = VesselSignificantAmpVelocityAvePeriod.from_file(file, 'Velocity')

            # acceleration extremes
            file.readline() # skip empty line
            # file.readline() # skip Acceleration header line
            accelerationExtremes = VesselSignificantAmpVelocityAvePeriod.from_file(file, 'Acceleration')

        newObj = VesselResponses(
            positionExtremes, velocityExtremes, accelerationExtremes, 
            draught=draught, waveDir=waveDir, Hs=Hs, Tp=Tp)
        
        return newObj


class VesselResponseList(dict[str, VesselResponses]):
    def add_from_file(
            self, 
            path: str, 
            loadCase: str,
            draught: str,
            waveDir: str,
            Hs: float,
            Tp: float
            ) -> None:
        self[loadCase] = VesselResponses.from_file(path, draught, waveDir, Hs, Tp)

    def to_excel(
            self, 
            path: str,
            waveDirs: list[str]
            ) -> None:
        df_all = self.all_results_to_df()
        df_critical = self.critical_lcs_df(df_all, waveDirs)

        # write to excel
        with pd.ExcelWriter(path, mode='w') as writer:
            df_critical.to_excel(writer, sheet_name='Critical LCs')
            df_all.to_excel(writer, sheet_name='All results')

    def critical_lcs_df(self, all_df: pd.DataFrame, waveDirs: list[str]) -> pd.DataFrame:
        """
        Returns a dataframe with the critical load cases for each direction (columns)
        and each extreme quantity (rows).
        """
        rowTitles = list(all_df.columns[1:]) # skip first column (Load Case)

        resultsByDir: dict[str, list[tuple[float, tuple[str, float, float], str]]] = {}
        for wa in waveDirs:
            df_dir = all_df.xs(wa, level='Wave dir. (from)', axis=0)

            # iterate columns to find the max value and the corresponding load case
            resultsByDir[wa] = []
            for col in df_dir.columns[1:]: # skip first column (Load Case)
                max_value = df_dir[col].max()
                max_row = df_dir[col].idxmax()
                loadCase = df_dir.loc[max_row].iloc[0]
                resultsByDir[wa].append((max_value, max_row, loadCase))


        # create dataframe
        index = pd.MultiIndex.from_tuples(rowTitles, names=all_df.columns.names)
        data = []
        cols = []
        for wa, cell in resultsByDir.items():
            if wa == 'Extreme Quantity':
                continue
            for rst in ['Max. Value', 'Draught', 'Dir.', 'Hs', 'Tp', 'Load Case']:
                cols.append((wa, rst))
            rows = [[],[],[],[],[],[]]
            for item in cell:
                rows[0].append(item[0]) # max value
                draught, Hs, Tp = item[1]
                rows[1].append(draught)
                rows[2].append(wa)
                rows[3].append(Hs)
                rows[4].append(Tp)
                rows[5].append(item[2]) # load case

            data.extend(rows) # max values
        headers = pd.MultiIndex.from_tuples(cols, names=['Direction', 'Parameter'])
        df = pd.DataFrame(data, index=headers, columns=index).T
        
        return df

    def all_results_to_df(self) -> pd.DataFrame:
        """
        Export the response list to an Excel file
        """
        import pandas as pd        
        headers = list(self.values())[0].to_multiheader_list()     
        row1stCol = []   
        headers.insert(0, ('Load Case', '', '')) # include load case name as first column

        # include columns for rotation results
        rot_unit = list(self.values())[0].positionExtremes.rotation_unit
        headers.append(('Rotation', 'Significant Amplitude', f'Roll+Pitch [{rot_unit}]'))
        headers.append(('Rotation', 'Maximum Amplitude', f'Roll+Pitch [{rot_unit}]'))

        # create multi-index for columns
        colHeaders = pd.MultiIndex.from_tuples(headers, names=['Extreme Quantity', 'Result', 'DOF [Unit]'])

        data = []
        LCs = []
        for lc, resp in self.items():
            values = resp.values_to_list()            
            values.insert(0, lc) # include load case name            

            # add rotation combined results
            values.append(resp.positionExtremes.significant_amp.rotation_combined())
            values.append(resp.positionExtremes.maximum_amp.rotation_combined())

            LCs.append(lc)
            row1stCol.append((resp.draught, resp.waveDir, resp.Hs, resp.Tp))
            data.append(values)

        # add first column (Load Case info)
        rowHeaders = pd.MultiIndex.from_tuples(
            row1stCol,
            names=['Draught', 'Wave dir. (from)', 'Hs [m]', 'Tp [s]']
            )

        # create dataframe
        df = pd.DataFrame(data, columns=colHeaders, index=rowHeaders)
        return df
        

    def ProcessExtremeResponses(
            self,
            model: _ofx.Model,
            vesselName: str,
            position: list[float],
            waveDirsHsTp: dict[str, list[tuple[float, float]]],
            outFile: str,
            outFolderLCs: str|None = None,
            stormDuration: float = 3.0,
            northDir: float|None = None,
            waveTrainIndex: int|None = None,
            ):
        """
        Process extreme responses for the vessel.
        * model: OrcaFlex model object
        * position: list with the [x,y,z] coordinates of the response output point,
            relative to the vessel origin
        * vesselName: name of the vessel in the model
        * waveDirsHsTp: dictionary with the wave directions (coming from) as keys,
            and a list of (Hs,Tp) tuples as values
        * outFile: path to the output Excel file
        * outFolderLCs: folder to save the load case files. If None, load case files are not saved.
        * stormDuration: duration of the storm for extreme response calculations (hours)
        * northDir: North direction from the x-axis, as defined by the OrcaFlex convention.
            If None, use the model definition.
        * waveTrainIndex: index of the wave train to use. If None, use the model definition.
        """

        if waveTrainIndex is not None:
            model.environment.SelectedWaveIndex = waveTrainIndex

        from src.NsgOrcFx.auxfuncs import isRegularWave
        if isRegularWave(model.environment.WaveType):
            raise Exception('This script is only for irregular waves (e.g., JONSWAP).')

        vessel: _ofx.OrcaFlexVesselObject = model[vesselName]
        if northDir is None:
            if model.general.NorthDirectionDefined == 'No':
                raise Exception('Error! The model North Direction is not defined, so it must be provided when running this script.')
            northDir = model.general.NorthDirection

        # set the response output points and storm duration
        vessel.ResponseNumberOfOutputPoints = 1
        vessel.ResponseOutputPointx[0] = position[0]
        vessel.ResponseOutputPointy[0] = position[1]
        vessel.ResponseOutputPointz[0] = position[2]
        # print('Storm duration = ' + str(vessel.ResponseStormDuration))
        vessel.ResponseStormDuration = stormDuration


        vesselType = model[vessel.VesselType]
        draughts = list(vesselType.DraughtName).copy()
        for dd in draughts:
            print(f'Processing load cases for vessel "{vesselName}", draught "{dd}"', end='')
            vessel.Draught = dd # set vessel draught
            for waName, hs_tp_list in waveDirsHsTp.items():
                # set wave direction
                waveAzimuth = _utils.angleFromDirName(waName)
                waveDir = (northDir - waveAzimuth + 180) % 360 # wave direction (going to)
                model.environment.WaveDirection = waveDir

                for hs, tp in hs_tp_list:
                    caseName = f'{vesselName}_Draught-{dd}_{waName}_Hs{hs:.1f}m_Tp{tp:.1f}s'
                    # print(f'Generating load case: {caseName}')

                    # set wave parameters
                    model.environment.WaveHs = hs
                    model.environment.WaveTp = tp

                    # save files
                    tmpFileName = _utils.getAvailableFileName(caseName, '.csv')
                    # outPath = os.path.join(outFolderLCs, tmpFileName)
                    vessel.SaveSpectralResponseSpreadsheet(tmpFileName)

                    # read results
                    self.add_from_file(tmpFileName, caseName, dd, waName, hs, tp)

                    # cleanup temporary file
                    os.remove(tmpFileName)

                    # outPath = os.path.join(outFolderLCs, caseName + '.xlsx')
                    # vessel.SaveSpectralResponseSpreadsheet(outPath)
                    if outFolderLCs is not None:
                        outPath = os.path.join(outFolderLCs, caseName + '.dat')
                        model.SaveData(outPath)

                    print('.', end='', flush=True) # just to show progress

            print(' done.')


        # export results to excel
        print(f'Exporting results to Excel file: "{outFile}" ...', end='', flush=True)
        self.to_excel(outFile, waveDirsHsTp.keys())
        print(' done.')