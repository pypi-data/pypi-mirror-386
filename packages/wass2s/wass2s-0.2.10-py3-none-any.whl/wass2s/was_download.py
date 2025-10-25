from __future__ import annotations
import logging
import os
import cdsapi
import urllib3
import calendar
from calendar import month_abbr
import xarray as xr
import zipfile
import io
import pandas as pd
from pathlib import Path
import xarray as xr
from datetime import timedelta
from datetime import date
from datetime import datetime
import gc
from dask.diagnostics import ProgressBar
import cdsapi
import netCDF4
import h5netcdf
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import requests
from tqdm import tqdm
from wass2s.utils import *
import rioxarray as rioxr
import datetime as dt
import time as _time
from typing import List, Tuple, Sequence, Optional


# Suppress warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger("cdsapi").setLevel(logging.ERROR)


class WAS_Download:
    def __init__(self):
        """Initialize the WAS_Download class."""
        pass

    def ModelsName(
        self,
        centre={
            "BOM_2": "bom",
            "ECMWF_51": "ecmwf",
            "UKMO_604": "ukmo",
            "UKMO_603": "ukmo",
            "METEOFRANCE_8": "meteo_france",
            "METEOFRANCE_9": "meteo_france",
            "DWD_21": "dwd", # month of initialization available for forecast are Jan to Mar
            "DWD_22": "dwd", # month of initialization available for forecast are Apr to __ 
            "CMCC_35": "cmcc",
            # "CMCC_3": "cmcc",
            "NCEP_2": "ncep",
            "JMA_3": "jma",
            "ECCC_4": "eccc",
            "ECCC_5": "eccc",
            # "CFSV2": "CFS",
            # "CMC1": "cmc1",
            # "CMC2": "cmc2",
            # "GFDL": "gfdl",
            # "NASA": "nasa",
            # "NCAR_CCSM4": "ncar",
            # "NMME" : "nmme"
            "CFSV2_1": "cfsv2",
            "CMC1_1": "cmc1",
            "CMC2_1": "cmc2",
            "GFDL_1": "gfdl",
            "NASA_1": "nasa",
            "NCAR_CCSM4_1": "ncar_ccsm4",
            "NMME_1" : "nmme"
        },
        variables_1={
            "PRCP":  "total_precipitation",
            "TEMP":  "2m_temperature",
            "TDEW": "2m_dewpoint_temperature",
            "TMAX":  "maximum_2m_temperature_in_the_last_24_hours",
            "TMIN":  "minimum_2m_temperature_in_the_last_24_hours",
            "UGRD10":"10m_u_component_of_wind",
            "VGRD10":"10m_v_component_of_wind",
            "SST":   "sea_surface_temperature",
            "SLP": "mean_sea_level_pressure",
            "DSWR": "surface_solar_radiation_downwards",
            "DLWR": "surface_thermal_radiation_downwards",
            "NOLR": "top_net_thermal_radiation",
        },
        variables_2={
            "HUSS_1000": "specific_humidity",
            "HUSS_925": "specific_humidity",
            "HUSS_850": "specific_humidity",
            "UGRD_1000": "u_component_of_wind",
            "UGRD_925": "u_component_of_wind",
            "UGRD_850": "u_component_of_wind",
            "VGRD_1000": "v_component_of_wind",
            "VGRD_925": "v_component_of_wind",
            "VGRD_850": "v_component_of_wind",
        },
    ):
        """
        Generate a combined dictionary of model names and variables. 
        For more information on C3S, browse the `MetaData <https://confluence.ecmwf.int/display/CKB/Description+of+the+C3S+seasonal+multi-system>`_.
        For more information on NMME, browse the `MetaData <https://confluence.ecmwf.int/display/CKB/Description+of+the+C3S+seasonal+multi-system>`_.

        Parameters:
            centre (dict): Mapping of model identifiers to model names.
            variables_1 (dict): Mapping of variable short names to full names for category 1.
            variables_2 (dict): Mapping of variable short names to full names for category 2.

        Returns:
            dict: A combined dictionary with keys as model.variable combinations and values as tuples (model name, variable name).
        """
        combined_dict1 = {
            f"{c}.{v}": (centre[c], variables_1[v]) for c in centre for v in variables_1
        }
        combined_dict2 = {
            f"{c}.{v}": (centre[c], variables_2[v]) for c in centre for v in variables_2
        }
        combined_dict = {**combined_dict1, **combined_dict2}
        return combined_dict

    def ReanalysisName(
        self,
        centre={"ERA5": "reanalysis ERA5", "NOAA": "NOAA ERSST"},
        variables_1={
            "PRCP": "total_precipitation",
            "TEMP": "2m_temperature",
            "UGRD10": "10m_u_component_of_wind",
            "VGRD10": "10m_v_component_of_wind",
            "SST": "sea_surface_temperature",
            "SLP": "mean_sea_level_pressure",
            "DSWR": "surface_solar_radiation_downwards",
            "DLWR": "surface_thermal_radiation_downwards",
            "NOLR": "top_thermal_radiation",
        },
        variables_2={
            "HUSS_1000": "specific_humidity",
            "HUSS_925": "specific_humidity",
            "HUSS_850": "specific_humidity",
            "UGRD_1000": "u_component_of_wind",
            "UGRD_925": "u_component_of_wind",
            "UGRD_850": "u_component_of_wind",
            "VGRD_1000": "v_component_of_wind",
            "VGRD_925": "v_component_of_wind",
            "VGRD_850": "v_component_of_wind",
        },
    ):
        """
        Generate a combined dictionary of reanalysis names and variables.

        Parameters:
            centre (dict): Mapping of reanalysis identifiers to reanalysis names.
            variables_1 (dict): Mapping of variable short names to full names for category 1.
            variables_2 (dict): Mapping of variable short names to full names for category 2.

        Returns:
            dict: A combined dictionary with keys as reanalysis.variable combinations and values as tuples (reanalysis name, variable name).
        """
        combined_dict1 = {
            f"{c}.{v}": (centre[c], variables_1[v]) for c in centre for v in variables_1
        }
        combined_dict2 = {
            f"{c}.{v}": (centre[c], variables_2[v]) for c in centre for v in variables_2
        }
        combined_dict = {**combined_dict1, **combined_dict2}
        return combined_dict

    def AgroObsName(
        self,
        variables={
            "AGRO.PRCP": ("precipitation_flux", None),
            "AGRO.TMAX": ("2m_temperature", "24_hour_maximum"),
            "AGRO.TEMP": ("2m_temperature", "24_hour_mean"),
            "AGRO.TMIN": ("2m_temperature", "24_hour_minimum"),
            "AGRO.TMIN": ("2m_temperature", "24_hour_minimum"),
            "AGRO.DSWR": ("solar_radiation_flux", None),
            "AGRO.ETP": ("reference_evapotranspiration", None),
            "AGRO.WFF": ("10m_wind_speed", "24_hour_mean"),
            "AGRO.HUMAX": ("2m_relative_humidity_derived", "24_hour_maximum"),
            "AGRO.HUMIN": ("2m_relative_humidity_derived", "24_hour_minimum"),
        },
    ):
        # 1 W m-2 = 0.0864 MJ m-2 day-1
        """
        Generate a dictionary for agrometeorological observation variables.

        Parameters:
            variables (dict): Mapping of agro variable short names to full names.

        Returns:
            dict: A dictionary mapping agro variables to their corresponding full names.
        """
        return variables

    # def download_nmme_txt_with_progress(self, url, file_path, chunk_size=1024):
    #     file_path = Path(file_path)
    #     response = requests.get(url, stream=True)
    #     total_size = int(response.headers.get('content-length', 0))
        
    #     with open(file_path, "wb") as f, tqdm(
    #         total=total_size, unit="B", unit_scale=True, desc=file_path.name
    #     ) as progress:
    #         for data in response.iter_content(chunk_size):
    #             progress.update(len(data))
    #             f.write(data)

    def download_nmme_txt_with_progress(self, url, file_path, chunk_size=1024):   
        # Check if the URL exists using a HEAD request
        try:
            head = requests.head(url)
            if head.status_code != 200:
                print(f"URL returned status code {head.status_code}. Skipping download.")
                return
        except Exception as e:
            print(f"Error checking URL: {e}. Skipping download.")
            return
    
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(file_path, "wb") as f, tqdm(
            total=total_size, unit="B", unit_scale=True, desc=file_path.name
        ) as progress:
            for data in response.iter_content(chunk_size):
                progress.update(len(data))
                f.write(data)

    
    def days_in_month(self, year, month):
        a = calendar.monthrange(year, month)[1]
        return a
         
    def parse_cpt_data_optimized(self, file_path):
        from datetime import datetime
        
        times = []
        times_start = []
        data_list = []
        lons = None
        lats = None
        days_in_month_values = []
    
        # Read all lines into memory once
        with open(file_path, 'r') as f:
            lines = f.readlines()
    
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('cpt:field'):
                # Parse metadata (e.g., time)
                while i < len(lines) and lines[i].startswith('cpt:'):
                    if 'cpt:T=' in lines[i]:
                        t_str = lines[i].split('cpt:T=')[1].split()[0]
                        year, pot_months = t_str.split('-')
                        if '/' in pot_months:
                            start_str, end_str = pot_months.split("/")
                            start_month = int(start_str)
                            end_month = int(end_str[0:2])
                            if start_month <= end_month:
                                months = list(range(start_month, end_month + 1))
                            else:
                                # Wrap around: from start_month to December, then January to end_month
                                months = list(range(start_month, 13)) + list(range(1, end_month + 1))
                            month = months[1]
                            days_in_mon = self.days_in_month(int(year), months[0]) + self.days_in_month(int(year), months[1]) + self.days_in_month(int(year), months[2])
                        else:
                            month = int(pot_months[0:2])
                            days_in_mon = self.days_in_month(int(year), month)
                        
                        days_in_month_values.append(days_in_mon)
                        times.append(datetime(int(year), int(month), 1))
                        
                        #### Retrieve init start
                        start_str = lines[i].split('cpt:S=')[1].split()[0]
                        yearstart, monthstart, daystart = start_str.split('-')
                        times_start.append(datetime(int(yearstart), int(monthstart), 1))
                    i += 1
                # Parse longitudes (assumed to be the next line)
                if i < len(lines):
                    lons = np.array([float(x) for x in lines[i].split()])
                    i += 1
                # Read the next 181 lines as a data block
                if i + 181 <= len(lines):
                    # Join the 181 lines into a single string
                    data_block = '\n'.join(lines[i:i + 181])
                    # Parse the block into a 2D array using np.loadtxt
                    data_array = np.loadtxt(io.StringIO(data_block), dtype=float)
                    if data_array.shape[1] == 361:  # 1 latitude + 360 longitudes
                        # Extract latitudes only once (assuming they’re consistent)
                        if lats is None:
                            lats = data_array[:, 0]
                        # Extract data (excluding latitude column)
                        data = data_array[:, 1:]
                        # Replace missing values (e.g., -999.0) with NaN
                        data[data == -999.0] = np.nan
                        data_list.append(data)
                        i += 181
                    else:
                        raise ValueError("Unexpected number of columns in data block")
                else:
                    break
            else:
                i += 1
                

        # Stack data into a 3D array (time, latitude, longitude)
        data_3d = np.stack(data_list, axis=0)
    
        # Create an xarray DataArray for convenient analysis
        da = xr.DataArray(
            data_3d,
            dims=['T', 'Y', 'X'],
            coords={
                'T': times,
                'Y': lats,
                'X': lons
            },
            # attrs={
            #     'units': 'mm/day',
            #     'long_name': 'precipitation'
            # }
        )

        days_in_month_da = xr.DataArray(
            days_in_month_values,
            dims=['T'],
            coords={'T': da['T']}
        ) 
        return da, days_in_month_da, times_start
    
    def WAS_Download_Models(
        self,
        dir_to_save,
        center_variable,
        month_of_initialization,
        lead_time,
        year_start_hindcast,
        year_end_hindcast,
        area,
        year_forecast=None,
        ensemble_mean=None,
        force_download=False,
    ):
        """
        Download seasonal forecast model data for specified center-variable combinations, initialization month, lead times, and years.

        Parameters:
            dir_to_save (str): Directory to save the downloaded files.
            center_variable (list): List of center-variable identifiers (e.g., ["ECMWF_51.PRCP", "UKMO_602.TEMP"]).
            month_of_initialization (int): Initialization month as an integer (1-12).
            lead_time (list): List of lead times in months.
            year_start_hindcast (int): Start year for hindcast data.
            year_end_hindcast (int): End year for hindcast data.
            area (list): Bounding box as [North, West, South, East] for clipping.
            year_forecast (int, optional): Forecast year if downloading forecast data. Defaults to None.
            ensemble mean (str,optional): it's can be median, mean or None. Defaults to None. 
            force_download (bool): If True, forces download even if file exists.
        """
        years = (
            [str(year) for year in range(year_start_hindcast, year_end_hindcast + 1)]
            if year_forecast is None
            else [str(year_forecast)]
        )

        center = [item.split(".")[0] for item in center_variable]
        variables = [item.split(".")[1] for item in center_variable]

        centre = {
            "BOM_2": "bom",
            "ECMWF_51": "ecmwf",
            "UKMO_604": "ukmo", # month of initialization available for forecast are Apr to __
            "UKMO_603": "ukmo", # month of initialization available for forecast are Jan to Mar
            "METEOFRANCE_8": "meteo_france",
            "METEOFRANCE_9": "meteo_france", 
            "DWD_21": "dwd", # month of initialization available for forecast are Jan to Mar
            "DWD_22": "dwd", # month of initialization available for forecast are Apr to __ 
            "CMCC_35": "cmcc",
            # "CMCC_3": "cmcc",
            "NCEP_2": "ncep",
            "JMA_3": "jma",
            "ECCC_4": "eccc",
            "ECCC_5": "eccc",
            # "CFSV2": "cfsv2",
            # "CMC1": "cmc1",
            # "CMC2": "cmc2",
            # "GFDL": "gfdl",
            # "NASA": "nasa",
            # "NCAR_CCSM4": "ncar_ccsm4",
            # "NMME" : "nmme"
            "CFSV2_1": "cfsv2",
            "CMC1_1": "cmc1",
            "CMC2_1": "cmc2",
            "GFDL_1": "gfdl",
            "NASA_1": "nasa",
            "NCAR_CCSM4_1": "ncar_ccsm4",
            "NMME_1" : "nmme"
        }

        variables_1 = {
            "PRCP": "total_precipitation",
            "TEMP": "2m_temperature",
            "TMAX": "maximum_2m_temperature_in_the_last_24_hours",
            "TMIN": "minimum_2m_temperature_in_the_last_24_hours",
            "UGRD10": "10m_u_component_of_wind",
            "VGRD10": "10m_v_component_of_wind",
            "SST": "sea_surface_temperature",
            "SLP": "mean_sea_level_pressure",
            "DSWR": "surface_solar_radiation_downwards",
            "DLWR": "surface_thermal_radiation_downwards",
            "NOLR": "top_thermal_radiation",
            "RUNOFF":"mean_surface_runoff_rate"
        }

        variables_2 = {
            "HUSS_1000": "specific_humidity",
            "HUSS_925": "specific_humidity",
            "HUSS_850": "specific_humidity",
            "UGRD_1000": "u_component_of_wind",
            "UGRD_925": "u_component_of_wind",
            "UGRD_850": "u_component_of_wind",
            "VGRD_1000": "v_component_of_wind",
            "VGRD_925": "v_component_of_wind",
            "VGRD_850": "v_component_of_wind",
        }

        system = {
            "BOM_2": "2",
            "ECMWF_51": "51",
            "UKMO_604": "604",
            "UKMO_603": "603",
            "METEOFRANCE_8": "8",
            "METEOFRANCE_9": "9",
            "DWD_21": "21",
            "DWD_22": "22",
            # "DWD_2": "2",
            "CMCC_35": "35",
            # "CMCC_3": "3",
            "NCEP_2": "2",
            "JMA_3": "3",
            "ECCC_4": "4",
            "ECCC_5": "5",
            # "CFSV2": "1",
            # "CMC1": "1",
            # "CMC2": "1",
            # "GFDL": "1",
            # "NASA": "1",
            # "NCAR_CCSM4": "1",
            # "NMME" : "1"
            "CFSV2_1": "1",
            "CMC1_1": "1",
            "CMC2_1": "1",
            "GFDL_1": "1",
            "NASA_1": "1",
            "NCAR_CCSM4_1": "1",
            "NMME_1" : "1"

        }
        
        nmme = ["cfsv2", "cmc1", "cmc2", "gfdl",  "nasa", "ncar_ccsm4", "nmme"]
        
        selected_centre = [centre[k] for k in center]
        selected_system = [system[k] for k in center]
        selected_var = [k for k in variables]

        dir_to_save = Path(dir_to_save)
        os.makedirs(dir_to_save, exist_ok=True)
        
        abb_mont_ini = calendar.month_abbr[int(month_of_initialization)]
        season_months = [((int(month_of_initialization) + int(l) - 1) % 12) + 1 for l in lead_time]
        season = "".join([calendar.month_abbr[month] for month in season_months])
        
        
        store_file_path = {}
        for cent, syst, k in zip(selected_centre, selected_system, selected_var):
            file_prefix = "forecast" if year_forecast else "hindcast"

            if cent in nmme: #### Reconsider an option to download other variable than PRCP, TEMP, and SST from IRIDL "code already available"      

                file_path = f"{dir_to_save}/{file_prefix}_{cent.replace('_', '')}{syst}_{k}_{abb_mont_ini}Ic_{season}_{lead_time[0]}.nc"
                init_str = f"{abb_mont_ini}ic"
                tag = "fcst" if year_forecast else "hcst"
                k = "precip" if k=="PRCP" else k
                k = "tmp2m" if k=="TEMP" else k
                k = "sst" if k=="SST" else k
                if not force_download and os.path.exists(file_path):
                    print(f"{file_path} already exists. Skipping download.")
                    store_file_path[f"{cent}_{syst}"] = file_path                   
                else:
                    try:
                        # Choose base URL depending on forecast/hindcast and temporal resolution.
                        if len(lead_time) == 3:
                            # Build lead time string using min and max lead time values.
                            lead_str = f"{season_months[0]}-{season_months[-1]}"
                            
                            if year_forecast:
                                base_url = "https://ftp.cpc.ncep.noaa.gov/International/nmme/seasonal_nmme_forecast_in_cpt_format/"
                                year_range = f"{year_forecast}-{year_forecast}"
                            else:
                                base_url = "https://ftp.cpc.ncep.noaa.gov/International/nmme/seasonal_nmme_hindcast_in_cpt_format/"
                                year_range = f"{1991}-{2020}"
                            file_name = f"{cent}_{k}_{tag}_{init_str}_{lead_str}_{year_range}.txt"
                            full_url = base_url + file_name
                            file_txt_path = dir_to_save / file_name
                            if os.path.exists(file_txt_path):
                                da, number_day, times_start = self.parse_cpt_data_optimized(file_txt_path)
                            else:
                                self.download_nmme_txt_with_progress(full_url, file_txt_path)
                                da, number_day, times_start = self.parse_cpt_data_optimized(file_txt_path)
    
                            if k == "precip":
                                da = da * number_day
                            da = da.assign_coords(T=times_start)
                            if year_forecast:
                                da = da.sel(T=str(year_forecast))
                            else:
                                da = da.sel(T=slice(str(year_start_hindcast),str(year_end_hindcast)))
                            ds = da.to_dataset(name=k)
                            ds = ds.isel(Y=slice(None, None, -1))
                            ds = ds.assign_coords(X=((ds.X + 180) % 360 - 180))
                            ds = ds.sortby("X")
                            ds = ds.sel(X=slice(area[1],area[3]),Y=slice(area[2], area[0])).transpose('T', 'Y', 'X') 
                            ds.to_netcdf(file_path)
                            print(f"Download finished for {cent} {syst} {k} to {file_path}")
                            ds.close()
                            store_file_path[f"{cent}_{syst}"] = file_path
                            
                        else:
                            if year_forecast:
                                base_url = "https://ftp.cpc.ncep.noaa.gov/International/nmme/monthly_nmme_forecast_in_cpt_format/"
                                year_range = f"{year_forecast}"
                            else:
                                base_url = "https://ftp.cpc.ncep.noaa.gov/International/nmme/monthly_nmme_hindcast_in_cpt_format/"
                                year_range = f"{1991}"
                            all_da = []
                            for i in season_months:
                                file_name = f"{cent}_{k}_{tag}_{init_str}_{i}_{year_range}.txt"
                                full_url = base_url + file_name
                                file_txt_path = dir_to_save / file_name
                                
                                if os.path.exists(file_txt_path):
                                    da_, number_day, times_start = self.parse_cpt_data_optimized(file_txt_path)
                                else:
                                    self.download_nmme_txt_with_progress(full_url, file_txt_path)
                                    da_, number_day, times_start = self.parse_cpt_data_optimized(file_txt_path)
                            
                                if k == "precip":
                                    da_ = da_ * number_day
                                                            
                                
                                all_da.append(da_)
                            da = xr.concat(all_da, dim="T").sortby("T")
                           
                            if k == "precip":
                                da = da.resample(T="YE").sum()
                            else:
                                da = da.resample(T="YE").mean()
                            da = da.assign_coords(T=times_start)    
       
                            if year_forecast:
                                da = da.sel(T=str(year_forecast))
                            else:
                                da = da.sel(T=slice(str(year_start_hindcast),str(year_end_hindcast)))
                            ds = da.to_dataset(name=k)
                            ds = ds.isel(Y=slice(None, None, -1))
                            ds = ds.assign_coords(X=((ds.X + 180) % 360 - 180))
                            ds = ds.sortby("X")
                            ds = ds.sel(X=slice(area[1],area[3]),Y=slice(area[2], area[0])).transpose('T', 'Y', 'X') 
                            ds.to_netcdf(file_path)
                            print(f"Download finished for {cent} {syst} {k} to {file_path}")
                            ds.close()
                            store_file_path[f"{cent}_{syst}"] = file_path  
                    except:
                        pass
            else:
                file_path = f"{dir_to_save}/{file_prefix}_{cent.replace('_', '')}{syst}_{k}_{abb_mont_ini}Ic_{season}_{lead_time[0]}.nc"
                if not force_download and os.path.exists(file_path):
                    print(f"{file_path} already exists. Skipping download.")
                    store_file_path[f"{cent}_{syst}"] = file_path
                else:                
                    try:
                        if k in variables_2:
                            press_level = k.split("_")[1]
                            dataset = "seasonal-monthly-pressure-levels"
                            request = {
                                "originating_centre": cent,
                                "system": syst,
                                "variable": variables_2[k],
                                "pressure_level": press_level,
                                "product_type": ["monthly_mean"],
                                "year": years,
                                "month": month_of_initialization,
                                "leadtime_month": lead_time,
                                "data_format": "netcdf",
                                "area": area,
                            }
                        else:
                            dataset = "seasonal-monthly-single-levels"
                            request = {
                                "originating_centre": cent,
                                "system": syst,
                                "variable": variables_1[k],
                                "product_type": ["monthly_mean"],
                                "year": years,
                                "month": month_of_initialization,
                                "leadtime_month": lead_time,
                                "data_format": "netcdf",
                                "area": area,
                            }
        
                        client = cdsapi.Client()
                        client.retrieve(dataset, request).download(file_path)
                        print(f"Downloaded: {file_path}")
    
        
                        # Load the NetCDF file and apply area selection if specified
                        ds = xr.open_dataset(file_path)
            
                        if k in ["TMIN","TEMP","TMAX","SST"]:
                            ds = ds - 273.15
                            ds = getattr(ds,ensemble_mean)(dim="number") if ensemble_mean != None else ds 
                            ds = ds.mean(dim="forecastMonth").isel(latitude=slice(None, None, -1))
                            if "indexing_time" in ds.coords: 
                                ds = ds.rename({"latitude":"lat","longitude":"lon","indexing_time":"time"})
                            else:
                                ds = ds.rename({"latitude":"lat","longitude":"lon","forecast_reference_time":"time"})
                        if k =="PRCP":
                            ds = getattr(ds,ensemble_mean)(dim="number") if ensemble_mean != None else ds
                            ds = (1000*30*24*60*60*ds).sum(dim="forecastMonth").isel(latitude=slice(None, None, -1))
                            ds = ds.where(lambda x: x >= 0, other=0)
                            if "indexing_time" in ds.coords: 
                                ds = ds.rename({"latitude":"lat","longitude":"lon","indexing_time":"time"})
                            else:
                                ds = ds.rename({"latitude":"lat","longitude":"lon","forecast_reference_time":"time"})

                        if k =="RUNOFF":
                            ds = getattr(ds,ensemble_mean)(dim="number") if ensemble_mean != None else ds
                            ds = ds.mean(dim="forecastMonth").isel(latitude=slice(None, None, -1))
                            ds = ds.where(lambda x: x >= 0, other=0)
                            if "indexing_time" in ds.coords: 
                                ds = ds.rename({"latitude":"lat","longitude":"lon","indexing_time":"time"})
                            else:
                                ds = ds.rename({"latitude":"lat","longitude":"lon","forecast_reference_time":"time"})
                            lat = ds.lat
                            lon = ds.lon
                            dlon = np.deg2rad(0.1)
                            dlat = np.deg2rad(0.1)
                            r = 6371000 # Earth radius in meters
                            # Area for each grid cell
                            area_ = (r ** 2) * dlon * np.cos(np.deg2rad(lat)) * dlat
                            # Perform the conversion to m^3/s
                            ds = (ds * area_) 
                        

                        if k == "SLP":
                            ds = ds/100
                            ds = getattr(ds,ensemble_mean)(dim="number") if ensemble_mean != None else ds 
                            ds = ds.mean(dim="forecastMonth").isel(latitude=slice(None, None, -1))
                            if "indexing_time" in ds.coords: 
                                ds = ds.rename({"latitude":"lat","longitude":"lon","indexing_time":"time"})
                            else:
                                ds = ds.rename({"latitude":"lat","longitude":"lon","forecast_reference_time":"time"})

                        if k in ["UGRD10","VGRD10"]:
                            ds = getattr(ds,ensemble_mean)(dim="number") if ensemble_mean != None else ds
                            ds = ds.mean(dim="forecastMonth").isel(latitude=slice(None, None, -1))
                            if "indexing_time" in ds.coords: 
                                ds = ds.rename({"latitude":"lat","longitude":"lon","indexing_time":"time"})
                            else:
                                ds = ds.rename({"latitude":"lat","longitude":"lon","forecast_reference_time":"time"})

                        if k in ["DSWR","DLWR", "NOLR"]:
                            ds = getattr(ds,ensemble_mean)(dim="number") if ensemble_mean != None else ds
                            ds = ds.sum(dim="forecastMonth").isel(latitude=slice(None, None, -1))
                            if "indexing_time" in ds.coords: 
                                ds = ds.rename({"latitude":"lat","longitude":"lon","indexing_time":"time"})
                            else:
                                ds = ds.rename({"latitude":"lat","longitude":"lon","forecast_reference_time":"time"})

                        if k not in ["TMIN","TEMP","TMAX","SST","UGRD10","VGRD10", "PRCP","SLP","DSWR","DLWR","NOLR"]:
                            ds = getattr(ds,ensemble_mean)(dim="number") if ensemble_mean != None else ds
                            ds = ds.drop_vars("pressure_level").squeeze().mean(dim="forecastMonth").isel(latitude=slice(None, None, -1))
                            if "indexing_time" in ds.coords: 
                                ds = ds.rename({"latitude":"lat","longitude":"lon","indexing_time":"time"})
                            else:
                                ds = ds.rename({"latitude":"lat","longitude":"lon","forecast_reference_time":"time"})
            
                        os.remove(file_path)
                        print(f"Deleted not process file: {file_path}")
                            
                        ds = ds.rename({"lon":"X","lat":"Y","time":"T"})    
                        output_path = f"{dir_to_save}/{file_prefix}_{cent.replace('_', '')}{syst}_{k}_{abb_mont_ini}Ic_{season}_{lead_time[0]}.nc"
                        
                        # Save the combined dataset for the center-variable combination
                        ds.to_netcdf(output_path)
                        print(f"Download finished, combined dataset for {cent} {syst} {k} to {output_path}")
                        ds.close()
                        store_file_path[f"{cent}_{syst}"] = file_path
                    except Exception as e:
                        print(f"Failed to download data for {k}: {e}")
        return store_file_path

    def WAS_Download_AgroIndicators_daily(
            self,
            dir_to_save,
            variables,
            year_start,
            year_end,
            area,
            force_download=False,
            max_retries=3,
            retry_delay=5,
        ):
        """
        Download daily agro-meteorological indicators from the Copernicus Data Store (CDS)
        for specified variables and years, with retries for failed downloads.

        Parameters
        ----------
        dir_to_save : str or pathlib.Path
            Directory path where the downloaded NetCDF files will be saved.
            The directory will be created if it does not exist.
        variables : list of str
            List of variable shorthand names to download. Valid options are:
            ["AGRO.PRCP", "AGRO.TMAX", "AGRO.TEMP", "AGRO.TMIN", "AGRO.DSWR",
            "AGRO.ETP", "AGRO.WFF", "AGRO.HUMAX", "AGRO.HUMIN"].
            Each variable corresponds to a CDS variable and optional statistic
            (e.g., "AGRO.PRCP" maps to "precipitation_flux").
        year_start : int
            Start year for the data to download (inclusive).
        year_end : int
            End year for the data to download (inclusive).
        area : list of float
            Bounding box for spatial subsetting in the format [North, West, South, East].
            Example: [50, -10, 40, 10] for a region in Europe.
        force_download : bool, optional
            If True, forces download even if the output file exists. Default is False.
        max_retries : int, optional
            Maximum number of retry attempts for failed downloads. Default is 3.
        retry_delay : int, optional
            Seconds to wait between retry attempts. Default is 5.

        Returns
        -------
        None
            The function saves NetCDF files to `dir_to_save` but does not return a value.
            Output files are named as `Daily_<variable>_<year_start>_<year_end>.nc`.

        Notes
        -----
        - The function downloads data from the CDS dataset "sis-agrometeorological-indicators".
        - Data is downloaded year-by-year as ZIP files containing NetCDF files, which are
        extracted, concatenated, and saved as a single NetCDF file per variable.
        - Temperature variables ("AGRO.TMIN", "AGRO.TEMP", "AGRO.TMAX") are converted
        from Kelvin to Celsius.
        - Solar radiation ("AGRO.DSWR") is converted from J/m^2/day to W/m^2.
        - Coordinates are renamed to "X" (longitude), "Y" (latitude), and "T" (time),
        with latitude flipped to ascending order.
        - The function requires a valid CDS API key configured in `~/.cdsapirc`.
        - Downloads are skipped for a variable if any year's data fails to download
        after `max_retries` attempts to ensure data completeness.
        """
        dir_to_save = Path(dir_to_save)
        dir_to_save.mkdir(parents=True, exist_ok=True)
        days = [f"{day:02}" for day in range(1, 32)]
        months = [f"{month:02}" for month in range(1, 13)]
        version = "2_0"

        variable_mapping = {
            "AGRO.PRCP": ("precipitation_flux", None),
            "AGRO.TMAX": ("2m_temperature", "24_hour_maximum"),
            "AGRO.TEMP": ("2m_temperature", "24_hour_mean"),
            "AGRO.TMIN": ("2m_temperature", "24_hour_minimum"),
            "AGRO.DSWR": ("solar_radiation_flux", None),
            "AGRO.ETP": ("reference_evapotranspiration", None),
            "AGRO.WFF": ("10m_wind_speed", "24_hour_mean"),
            "AGRO.HUMAX": ("2m_relative_humidity_derived", "24_hour_maximum"),
            "AGRO.HUMIN": ("2m_relative_humidity_derived", "24_hour_minimum")
        }

        for var in variables:
            if var not in variable_mapping:
                print(f"Unknown variable: {var}. Skipping.")
                continue

            cds_variable, statistic = variable_mapping[var]
            output_path = dir_to_save / f"Daily_{var.split('.')[1]}_{year_start}_{year_end}.nc"

            if not force_download and output_path.exists():
                print(f"{output_path} already exists. Skipping download.")
                continue

            combined_datasets = []
            all_years_downloaded = True

            for year in range(year_start, year_end + 1):
                zip_file_path = dir_to_save / f"Daily_{var.split('.')[1]}_{year}.zip"
                success = False
                retries = 0

                while retries < max_retries and not success:
                    try:
                        client = cdsapi.Client()
                        dataset = "sis-agrometeorological-indicators"
                        request = {
                            "variable": cds_variable,
                            "year": str(year),
                            "month": months,
                            "day": days,
                            "version": version,
                            "area": area,
                        }
                        if statistic:
                            request["statistic"] = [statistic]

                        print(f"Attempt {retries + 1}/{max_retries}: Downloading {cds_variable} ({statistic}) data for {year}...")
                        client.retrieve(dataset, request).download(str(zip_file_path))
                        print(f"Downloaded: {zip_file_path}")
                        success = True

                    except Exception as e:
                        retries += 1
                        print(f"Attempt {retries}/{max_retries} failed for {cds_variable} ({statistic}) data for {year}: {e}")
                        if retries < max_retries:
                            print(f"Retrying after {retry_delay} seconds...")
                            _time.sleep(retry_delay)
                        if zip_file_path.exists():
                            os.remove(zip_file_path)
                            print(f"Deleted incomplete ZIP file: {zip_file_path}")

                if not success:
                    print(f"Failed to download {cds_variable} ({statistic}) data for {year} after {max_retries} attempts.")
                    all_years_downloaded = False
                    continue

                try:
                    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                        for netcdf_file_name in zip_ref.namelist():
                            with zip_ref.open(netcdf_file_name) as file:
                                ds = xr.open_dataset(io.BytesIO(file.read()))
                                combined_datasets.append(ds)
                except Exception as e:
                    print(f"Failed to extract/process {zip_file_path}: {e}")
                    all_years_downloaded = False
                    if zip_file_path.exists():
                        os.remove(zip_file_path)
                        print(f"Deleted ZIP file due to processing error: {zip_file_path}")
                    continue

                if zip_file_path.exists():
                    os.remove(zip_file_path)
                    print(f"Deleted ZIP file: {zip_file_path}")

            if combined_datasets and all_years_downloaded:
                try:
                    combined_ds = xr.concat(combined_datasets, dim="time").drop_vars('crs')

                    if var in ["AGRO.TMIN", "AGRO.TEMP", "AGRO.TMAX"]:
                        combined_ds = combined_ds - 273.15
                    if var == "AGRO.DSWR":
                        combined_ds = combined_ds / 86400

                    combined_ds = combined_ds.rename({"lon": "X", "lat": "Y", "time": "T"})
                    combined_ds = combined_ds.isel(Y=slice(None, None, -1))

                    combined_ds.to_netcdf(output_path)
                    combined_ds.close()
                    print(f"Combined dataset for {var} saved to {output_path}")
                except Exception as e:
                    print(f"Failed to process or save combined dataset for {var}: {e}")
            else:
                print(f"Skipping save for {var} due to incomplete year downloads.")


    def WAS_Download_Models_Daily(
        self,
        dir_to_save,
        center_variable,         # e.g. ["ECMWF_51.PRCP", "UKMO_603.TEMP", ...]
        month_of_initialization, # int: e.g. 2 for February
        day_of_initialization,   # int: e.g. 1 for the 1st day
        leadtime_hour,           # list of strings: e.g. ["24","48",..., "5160"]
        year_start_hindcast,
        year_end_hindcast,
        area,
        year_forecast=None,
        ensemble_mean=None,
        force_download=False,
    ):
        """
        Download daily/sub-daily seasonal forecast model data (original)
        using 'seasonal-original-single-levels' from the CDS.
    
        Parameters:
            dir_to_save (str or Path): Directory to save the downloaded files.
            center_variable (list): Each element e.g. "ECMWF_51.PRCP"
                - left side of '.' is model (ECMWF_51),
                - right side is variable short code (PRCP).
            month_of_initialization (int): Initialization month (1-12).
            day_of_initialization (int): Initialization day (1-31).
            leadtime_hour (list of str): e.g. ["24", "48", ..., "5160"].
            year_start_hindcast (int): Start year for hindcast data.
            year_end_hindcast (int): End year for hindcast data.
            area (list): Bounding box as [North, West, South, East].
            year_forecast (int, optional): If provided, downloads that single
                forecast year. Otherwise downloads hindcast for the specified range.
            ensemble_mean (str, optional): e.g. "mean", "median", or None.
            force_download (bool): Force download if True, even if file exists.
        """
    
        # 1. Determine whether we are downloading hindcast or forecast.
        if year_forecast is None:
            # Hindcast range
            years = [str(y) for y in range(year_start_hindcast, year_end_hindcast + 1)]
            file_prefix = "hindcast"
        else:
            # Single forecast year
            years = [str(year_forecast)]
            file_prefix = "forecast"
    
        # 2. Build standard dictionaries for center/system/variables
        centre = {
            "BOM_2": "bom",
            "ECMWF_51": "ecmwf",
            "UKMO_604": "ukmo", # month of initialization available for forecast are Apr to __
            "UKMO_603": "ukmo", # month of initialization available for forecast are Jan to Mar
            "METEOFRANCE_8": "meteo_france",
            "METEOFRANCE_9": "meteo_france",
            "DWD_21": "dwd",
            "DWD_22": "dwd",
            # "DWD_2": "dwd",
            "CMCC_35": "cmcc",
            # "CMCC_3": "cmcc",
            "NCEP_2": "ncep",
            "JMA_3": "jma",
            "ECCC_4": "eccc",
            "ECCC_5": "eccc",
        }
    
        system = {
            "BOM_2": "2",
            "ECMWF_51": "51",
            "UKMO_604": "604",
            "UKMO_603": "603",
            "METEOFRANCE_8": "8",
            "METEOFRANCE_9": "9",
            "DWD_21": "21",
            "DWD_22": "22",
            # "DWD_2": "2",
            "CMCC_35": "35",
            # "CMCC_3": "3",
            "NCEP_2": "2",
            "JMA_3": "3",
            "ECCC_4": "4",
            "ECCC_5": "5",
        }
    
        variables_1 = {
            "PRCP":  "total_precipitation",
            "TEMP":  "2m_temperature",
            "TDEW": "2m_dewpoint_temperature",
            "TMAX":  "maximum_2m_temperature_in_the_last_24_hours",
            "TMIN":  "minimum_2m_temperature_in_the_last_24_hours",
            "UGRD10":"10m_u_component_of_wind",
            "VGRD10":"10m_v_component_of_wind",
            "SST":   "sea_surface_temperature",
            "SLP": "mean_sea_level_pressure",
            "DSWR": "surface_solar_radiation_downwards",
            "DLWR": "surface_thermal_radiation_downwards",
            "NOLR": "top_net_thermal_radiation",
            "RUNOFF": "surface_runoff"
            
        }
        variables_2 = {
            "HUSS_1000": "specific_humidity",
            "HUSS_925":  "specific_humidity",
            "HUSS_850":  "specific_humidity",
            "UGRD_1000": "u_component_of_wind",
            "UGRD_925":  "u_component_of_wind",
            "UGRD_850":  "u_component_of_wind",
            "VGRD_1000": "v_component_of_wind",
            "VGRD_925":  "v_component_of_wind",
            "VGRD_850":  "v_component_of_wind",
        }

        ### Particularity for day of initialization NCEP and JMA
        init_day_dict_jma = {
            "01":16, "02":10, "03":12, "04":11, "05":16, "06":15,
            "07":15, "08":14, "09":13, "10":13, "11":12, "12":12
        }

        init_day_dict_ncep = {
            "01":1, "02":5, "03":2, "04":1, "05":1, "06":5,
            "07":5, "08":4, "09":3, "10":3, "11":2, "12":2
        }
        
    
        # 3. Ensure the output directory exists
        dir_to_save = Path(dir_to_save)
        dir_to_save.mkdir(parents=True, exist_ok=True)
        store_file_path = {}
        client = cdsapi.Client()        
        # 4. Loop over each center-variable combination
        for cv in center_variable:
            # Example: "ECMWF_51.PRCP"
            c = cv.split(".")[0]  # e.g. "ECMWF_51"
            v = cv.split(".")[1]  # e.g. "PRCP"
    
            # Map to the Copernicus naming
            cent = centre[c]
            syst = system[c]
            # if v in variables_1:
            #     var_cds = variables_1[v]
            # elif v in variables_2:
            #     var_cds = variables_2[v]
            # else:
            #     print(f"Unknown variable code: {v}, skipping.")
            #     continue

            if cent == "jma" and year_forecast is None:
                day_of_initialization = init_day_dict_jma[month_of_initialization]
            if cent == "ncep" and year_forecast is None:
                day_of_initialization = init_day_dict_ncep[month_of_initialization]

            # Build a single output path
            abb_mont_ini = month_abbr[int(month_of_initialization)]
            
            # E.g. "hindcast_ecmwf51_PRCP_Feb01_1981-2016_24-5160.nc"
            years_str = f"{years[0]}_{years[-1]}" if len(years) > 1 else years[0]
            lead_str  = f"{leadtime_hour[0]}-{leadtime_hour[-1]}" if len(leadtime_hour) > 1 else leadtime_hour[0]
    
            output_file = (
                dir_to_save /
                f"{file_prefix}_{cent}{syst}_{v}_{abb_mont_ini}01_{years_str}_{lead_str}.nc"
            )

            # output_file = (
            #     dir_to_save /
            #     f"{file_prefix}_{cent}{syst}_{v}_{abb_mont_ini}{day_of_initialization}_{years_str}_{lead_str}.nc"
            # )
            

            if not force_download and output_file.exists():
                print(f"{output_file} already exists. Skipping download.")
                store_file_path[f"{cent}{syst}"] = output_file
            
            else:

                try:
                    # Temporary file to download
                    temp_file = dir_to_save / f"temp_{cent}{syst}_{v}.nc"

                    if v in variables_2:
                        press_level = v.split("_")[1]        
                        # 5. Prepare the request for 'seasonal-original-pressure-levels'
                        dataset = "seasonal-original-pressure-levels"
                        request = {
                            "originating_centre": cent,
                            "system": syst,
                            "variable": [variables_2[v]],
                            "pressure_level": press_level,
                            "year": years,  # list of strings
                            "month": [f"{int(month_of_initialization):02}"],
                            "day":   [f"{int(day_of_initialization):02}"],
                            "leadtime_hour": leadtime_hour,  # e.g. ["24","48",..., "5160"]
                            "data_format": "netcdf",
                            "area": area,   # e.g. [90, -180, -90, 180]
                        }
                    else:
                        dataset = "seasonal-original-single-levels"
                        request = {
                            "originating_centre": cent,
                            "system": syst,
                            "variable": [variables_1[v]],
                            "year": years,  # list of strings
                            "month": [f"{int(month_of_initialization):02}"],
                            "day":   [f"{int(day_of_initialization):02}"],
                            "leadtime_hour": leadtime_hour,  # e.g. ["24","48",..., "5160"]
                            "data_format": "netcdf",
                            "area": area,   # e.g. [90, -180, -90, 180]                    
                        }
                    # print(request, temp_file, dataset, cent, syst, [variables_1[v]], v, years, month_of_initialization, day_of_initialization, leadtime_hour, area)    
                    # 6. Download from CDS
                    print(f"Requesting data from '{dataset}' for {cv}...")
                    client.retrieve(dataset, request).download(str(temp_file))
                    print(f"Downloaded: {temp_file}")

                    # 7. Post-process with xarray
                    ##########################################################
                    # Take in account level pressure for some variables in this part
                    ##########################################################
                    
                    ds = xr.open_dataset(temp_file)
                    if 'forecast_reference_time' in ds.coords:                     
                        time = (ds['forecast_reference_time'][0] + ds['forecast_period']).data
                        ds = ds.isel(forecast_reference_time=0)
                        ds['forecast_period'] = time
                        ds = ds.rename({"forecast_period":"time"})
                        ds = ds.drop_vars(['forecast_reference_time', 'valid_time', 'number'])

                    # elif 'forecast_reference_time' in ds.coords:
                    #     time = (ds['forecast_reference_time'] + ds['forecast_period']).data
                    #     ds = ds.assign_coords(time=(('forecast_reference_time', 'forecast_period'), time))
                    #     ds = ds.stack(time=('forecast_reference_time', 'forecast_period'))
                    #     ds = ds.drop_vars(['forecast_reference_time', 'forecast_period'])
                    #     ds = ds.rename({"valid_time":"time"})

                    else:
                        time = (ds['indexing_time'][0] + ds['forecast_period']).data
                        ds = ds.isel(forecast_reference_time=0)
                        ds['forecast_period'] = time
                        ds = ds.rename({"forecast_period":"time"})
                        ds = ds.drop_vars(['indexing_time', 'valid_time', 'number'])
                        
                        # time = (ds['indexing_time']  + ds['forecast_period']).data
                        # ds = ds.assign_coords(time=(('indexing_time', 'forecast_period'), time)).isel(indexing_time=0)
                        # ds = ds.stack(time=('indexing_time', 'forecast_period'))
                        # ds = ds.drop_vars(['indexing_time', 'forecast_period'])
                        # ds = ds.rename({"valid_time":"time"})                    
        
                    # If there's an ensemble dimension, apply ensemble mean/median if requested
                    if ensemble_mean in ["mean", "median"] and "number" in ds.dims:
                        ds = getattr(ds, ensemble_mean)(dim="number")
        
                    # Flip latitude
                    if "latitude" in ds.coords:
                        ds = ds.isel(latitude=slice(None, None, -1))

                    if v in ["TMIN","TEMP","TMAX","SST", "TDEW"]:
                        ds = ds - 273.15
                    if v =="SLP":
                        ds = ds / 100
                    if v =="PRCP":
                        ds['time'] = ds['time'].to_index()
                        years_ = ds['time'].dt.year
                        tampon = []
                        for year_ in np.unique(years_):
                            
                            # Select the data for the specific year
                            yearly_ds = ds.sel(time=ds['time'].dt.year == year_)
                            
                            # Calculate differences for the year
                            differences = [yearly_ds.isel(time=i) - yearly_ds.isel(time=i-1) for i in range(1, len(yearly_ds['time']))]
                            differences = xr.concat(differences, dim="time")
                            differences['time'] = yearly_ds['time'].isel(time=slice(1,None))
                            tampon.append(differences)
                        ds = (xr.concat(tampon, dim="time") * 1000).where(lambda x: x >= 0, other=0)

                    if v=="RUNOFF":
                        ds['time'] = ds['time'].to_index()
                        diffs = ds.groupby('time.year').apply(lambda x: x.diff('time'))
                        ds = diffs.where(lambda x: x >= 0, other=0)
                        lat = ds.latitude
                        lon = ds.longitude
                        dlon = np.deg2rad(0.1)
                        dlat = np.deg2rad(0.1)
                        r = 6371000 # Earth radius in meters
                        # Area for each grid cell
                        area_= (r ** 2) * dlon * np.cos(np.deg2rad(lat)) * dlat
                        # Perform the conversion to m^3/s
                        ds = (ds * area_) / 86400                        

                    if v in ["DSWR","DLWR","OLR"]:
                        ds['time'] = ds['time'].to_index()
                        years_ = ds['time'].dt.year
                        tampon = []
                        for year_ in np.unique(years_):
                            
                            # Select the data for the specific year
                            yearly_ds = ds.sel(time=ds['time'].dt.year == year_)
                            
                            # Calculate differences for the year
                            differences = [yearly_ds.isel(time=i) - yearly_ds.isel(time=i-1) for i in range(1, len(yearly_ds['time']))]
                            differences = xr.concat(differences, dim="time")
                            differences['time'] = yearly_ds['time'].isel(time=slice(1,None))
                            tampon.append(differences)
                        ds = xr.concat(tampon, dim="time")/(24*60*60)

                    # Finally, rename the coords to X, Y, T to match my style
                    if "longitude" in ds.coords:
                        ds = ds.rename({"longitude": "X"})
                    if "latitude" in ds.coords:
                        ds = ds.rename({"latitude": "Y"})
                    if "time" in ds.coords:
                        ds = ds.rename({"time": "T"})
        
                    # 8. Save the processed data
                    ds.to_netcdf(output_file)
                    print(f"Saved processed data to: {output_file}")
                    ds.close()
                    store_file_path[f"{cent}{syst}"] = output_file
                    os.remove(temp_file)
                    print(f"Deleted temp file: {temp_file}")
                    del request, ds        
                    gc.collect()  
                except Exception as e:
                    print(f"Failed to download data for {cv}: {e}")  
            _time.sleep(1)  # Sleep to avoid overwhelming the server
        return store_file_path

    def WAS_Download_AgroIndicators(
            self,
            dir_to_save,
            variables,
            year_start,
            year_end,
            area,
            seas=["01", "02", "03"],  # e.g. NDJ = ["11","12","01"]
            force_download=False,
            max_retries=3,
            retry_delay=5,
        ):
        """
        Download agro-meteorological indicators for specified variables, years, and months,
        handling cross-year seasons (e.g., NDJ) with retries for failed downloads.

        Parameters:
            dir_to_save (str): Directory to save the downloaded files.
            variables (list): List of shorthand variables (e.g., ["AGRO.PRCP", "AGRO.TMAX"]).
            year_start (int): Start year for the data.
            year_end (int): End year for the data.
            area (list): Bounding box as [North, West, South, East].
            seas (list): List of months (e.g., ["11","12","01"] for NDJ).
            force_download (bool): If True, forces download even if file exists.
            max_retries (int): Maximum number of retry attempts for failed downloads (default: 3).
            retry_delay (int): Seconds to wait between retry attempts (default: 5).
        """
        dir_to_save = Path(dir_to_save)
        dir_to_save.mkdir(parents=True, exist_ok=True)

        # Convert season months to integers (e.g., ["11","12","01"] -> [11,12,1])
        season_months = [int(m) for m in seas]
        # Identify the pivot = the first month in your `seas` list
        pivot = season_months[0]

        # Basic mapping
        variable_mapping = {
            "AGRO.PRCP": ("precipitation_flux", None),
            "AGRO.TMAX": ("2m_temperature", "24_hour_maximum"),
            "AGRO.TEMP": ("2m_temperature", "24_hour_mean"),
            "AGRO.TMIN": ("2m_temperature", "24_hour_minimum"),
            "AGRO.DSWR": ("solar_radiation_flux", None),
            "AGRO.ETP": ("reference_evapotranspiration", None),
            "AGRO.WFF": ("10m_wind_speed", "24_hour_mean"),
            "AGRO.HUMAX": ("2m_relative_humidity_derived", "24_hour_maximum"),
            "AGRO.HUMIN": ("2m_relative_humidity_derived", "24_hour_minimum"),
        }

        version = "2_0"
        days = [f"{day:02d}" for day in range(1, 32)]

        # Build a season string for naming (e.g., NDJ)
        season_str = "".join([calendar.month_abbr[m] for m in season_months])

        def month_str(m):
            """Return a zero-padded string month from int."""
            return f"{m:02d}"

        for var in variables:
            if var not in variable_mapping:
                print(f"Unknown variable: {var}. Skipping.")
                continue

            cds_variable, statistic = variable_mapping[var]
            var_short = var.split(".")[1]  # e.g., "PRCP" from "AGRO.PRCP"

            # Output path for the combined dataset across all years
            output_path = dir_to_save / f"Obs_{var_short}_{year_start}_{year_end}_{season_str}.nc"
            if not force_download and output_path.exists():
                print(f"{output_path} already exists. Skipping download.")
                continue

            # Accumulate all partial datasets
            all_years_datasets = []
            all_years_downloaded = True

            # Loop over each year in the requested range
            for year in range(year_start, year_end + 1):
                # Split the months into those belonging to "base" year vs "next" year
                base_months = [m for m in season_months if m >= pivot]
                next_months = [m for m in season_months if m < pivot]

                # 1) Download part A (base-year months), if any
                if base_months:
                    months_base = [month_str(m) for m in base_months]
                    zip_file_path = dir_to_save / f"Obs_{var_short}_{year}_{season_str}_partA.zip"
                    success = False
                    retries = 0

                    while retries < max_retries and not success:
                        try:
                            client = cdsapi.Client()
                            request = {
                                "variable": cds_variable,
                                "year": str(year),
                                "month": months_base,
                                "day": days,
                                "version": version,
                                "area": area,
                            }
                            if statistic:
                                request["statistic"] = [statistic]

                            print(f"Attempt {retries + 1}/{max_retries}: Downloading {cds_variable} for {year} months={months_base}")
                            client.retrieve("sis-agrometeorological-indicators", request).download(str(zip_file_path))
                            success = True
                        except Exception as e:
                            retries += 1
                            print(f"Attempt {retries}/{max_retries} failed for {cds_variable} year={year} Part A: {e}")
                            if retries < max_retries:
                                print(f"Retrying after {retry_delay} seconds...")
                                _time.sleep(retry_delay)
                            if zip_file_path.exists():
                                os.remove(zip_file_path)
                                print(f"Deleted incomplete ZIP file: {zip_file_path}")

                    if not success:
                        print(f"Failed to download {cds_variable} year={year} Part A after {max_retries} attempts.")
                        all_years_downloaded = False
                        continue

                    # Unzip each netCDF and append
                    try:
                        with zipfile.ZipFile(zip_file_path, 'r') as z:
                            for nc_name in z.namelist():
                                with z.open(nc_name) as f:
                                    ds = xr.open_dataset(io.BytesIO(f.read()))
                                    all_years_datasets.append(ds)
                        os.remove(zip_file_path)
                        print(f"Deleted ZIP file: {zip_file_path}")
                    except Exception as e:
                        print(f"Failed to extract/process {zip_file_path}: {e}")
                        all_years_downloaded = False
                        if zip_file_path.exists():
                            os.remove(zip_file_path)
                            print(f"Deleted ZIP file due to processing error: {zip_file_path}")
                        continue

                # 2) Download part B (next-year months), if any and if we have a next year
                if next_months and (year < year_end + 1):
                    year_next = year + 1
                    months_next = [month_str(m) for m in next_months]
                    zip_file_path = dir_to_save / f"Obs_{var_short}_{year}_{season_str}_partB_{year_next}.zip"
                    success = False
                    retries = 0

                    while retries < max_retries and not success:
                        try:
                            client = cdsapi.Client()
                            request = {
                                "variable": cds_variable,
                                "year": str(year_next),
                                "month": months_next,
                                "day": days,
                                "version": version,
                                "area": area,
                            }
                            if statistic:
                                request["statistic"] = [statistic]

                            print(f"Attempt {retries + 1}/{max_retries}: Downloading {cds_variable} for {year_next} months={months_next}")
                            client.retrieve("sis-agrometeorological-indicators", request).download(str(zip_file_path))
                            success = True
                        except Exception as e:
                            retries += 1
                            print(f"Attempt {retries}/{max_retries} failed for {cds_variable} year={year_next} Part B: {e}")
                            if retries < max_retries:
                                print(f"Retrying after {retry_delay} seconds...")
                                _time.sleep(retry_delay)
                            if zip_file_path.exists():
                                os.remove(zip_file_path)
                                print(f"Deleted incomplete ZIP file: {zip_file_path}")

                    if not success:
                        print(f"Failed to download {cds_variable} year={year_next} Part B after {max_retries} attempts.")
                        all_years_downloaded = False
                        continue

                    # Unzip each netCDF and append
                    try:
                        with zipfile.ZipFile(zip_file_path, 'r') as z:
                            for nc_name in z.namelist():
                                with z.open(nc_name) as f:
                                    ds = xr.open_dataset(io.BytesIO(f.read()))
                                    all_years_datasets.append(ds)
                        os.remove(zip_file_path)
                        print(f"Deleted ZIP file: {zip_file_path}")
                    except Exception as e:
                        print(f"Failed to extract/process {zip_file_path}: {e}")
                        all_years_downloaded = False
                        if zip_file_path.exists():
                            os.remove(zip_file_path)
                            print(f"Deleted ZIP file due to processing error: {zip_file_path}")
                        continue

            # Post-process & combine all partial years
            if all_years_datasets and all_years_downloaded:
                try:
                    combined_ds = xr.concat(all_years_datasets, dim="time").drop_vars('crs')

                    # Unit conversions
                    if var in ["AGRO.TMIN", "AGRO.TEMP", "AGRO.TMAX"]:
                        combined_ds = combined_ds - 273.15  # Kelvin to Celsius

                    # Aggregate for cross-year seasons
                    combined_ds = self._aggregate_crossyear(
                        ds=combined_ds,
                        season_months=season_months,
                        var_name=var
                    )

                    if var == "AGRO.DSWR":
                        combined_ds = combined_ds / 86400  # J/m^2/day to W/m^2

                    # Rename dimensions
                    if "lon" in combined_ds.dims:
                        combined_ds = combined_ds.rename({"lon": "X"})
                    if "lat" in combined_ds.dims:
                        combined_ds = combined_ds.rename({"lat": "Y"})
                    combined_ds = combined_ds.isel(Y=slice(None, None, -1))

                    # Adjust time coordinate
                    combined_ds["time"] = [f"{year}-{seas[1]}-01" for year in combined_ds["time"].astype(str).values]
                    combined_ds["time"] = combined_ds["time"].astype("datetime64[ns]")
                    combined_ds = combined_ds.rename({"time": "T"})

                    # Save to NetCDF
                    combined_ds.to_netcdf(output_path)
                    combined_ds.close()
                    print(f"Saved final dataset for {var} to: {output_path}")
                except Exception as e:
                    print(f"Failed to process or save combined dataset for {var}: {e}")
            else:
                print(f"No data downloaded for {var} in {season_str}.")
   
    # -------------------------------------------------------------------------
    # Helper for Reanalysis cross-year post-processing (optional)
    # -------------------------------------------------------------------------
    def _postprocess_reanalysis(self, ds, var_name):
        """
        Drop extra coords, rename dims, flip lat, etc.
        Adjust as needed for ERA5 quirks.
        """
        # Drop some known extraneous coords
        drop_list = []
        for extra in ["number", "expver", "pressure_level"]:
            if extra in ds.coords or extra in ds.variables:
                drop_list.append(extra)

        ds = ds.drop_vars(drop_list, errors="ignore").squeeze()

        # Flip latitude if it exists
        if "latitude" in ds.coords:
            ds = ds.isel(latitude=slice(None, None, -1))
            # rename directly to X, Y
            ds = ds.rename({"latitude": "Y", "longitude": "X"})

        # If "valid_time" is present, rename it to "time"
        if "valid_time" in ds.coords:
            ds = ds.assign_coords(valid_time=pd.to_datetime(ds.valid_time.values))
            ds = ds.rename({"valid_time": "time"})

        return ds

    def _postprocess_reanalysis_ersst(self, ds, var_name):       
        # Drop unnecessary variables
        ds = ds.drop_vars('zlev').squeeze()
        keep_vars = [var_name, 'T', 'X', 'Y']
        drop_vars = [v for v in ds.variables if v not in keep_vars]
        return ds.drop_vars(drop_vars, errors="ignore")

    def _aggregate_crossyear(self, ds, season_months, var_name):
        """
        Group ds by a custom 'season_year' coordinate so that all months
        in 'season_months' belong to one group that may cross Dec→Jan.
    
        Parameters:
            ds (xarray.Dataset or DataArray): The data to aggregate (daily, monthly, etc.).
            season_months (list[int]): e.g. [11,12,1] for NDJ.
            var_name (str): e.g. "AGRO.PRCP", "TEMP", "TMIN", etc. 
                           Used to decide 'mean' vs 'sum'.
    
        Returns:
            ds_out (xarray.Dataset or DataArray): Aggregated by season, 
                          dimension renamed from 'season_year' to 'time'.
        """

        if "time" not in ds.coords:
            raise ValueError("Dataset must have a 'time' dimension for aggregation.")
    
        pivot = season_months[0]
    
        # 1) Tag each time with the "season_year"
        # If month >= pivot => same year's label, else => year - 1
        season_year = ds["time"].dt.year.where(ds["time"].dt.month >= pivot,
                                               ds["time"].dt.year - 1)
    
        ds = ds.assign_coords(season_year=season_year)
        
        # 2) Keep only the months we actually want
        ds = ds.where(ds["time"].dt.month.isin(season_months), drop=True)
    
        # 3) Decide mean or sum based on var_name 

        if any(x in var_name for x in ["TEMP","TMIN","TMAX","SST","SLP"]):
            ds_out = ds.groupby("season_year").mean("time")
        elif any(x in var_name for x in ["PRCP","DSWR","DLWR","NOLR","RUNOFF"]):
            # For precipitation and radiation, we sum over time
            # ds_out = ds.groupby("season_year").sum("time")
            ds_out = ds.groupby("season_year").mean("time")
        # elif var_name == "RUNOFF":
        #     ds_out = xr.diff(ds, dim="time").mean("time")
        else:
            ds_out = ds.groupby("season_year").mean("time")
    
        # 4) Rename "season_year" to "time", 
        #    so we end up with a time dimension (representing each seasonal year).
        ds_out = ds_out.rename({"season_year": "time"})
    
        return ds_out


    def WAS_Download_Reanalysis(
        self,
        dir_to_save,
        center_variable,
        year_start,
        year_end,
        area,
        seas=["01", "02", "03"],  # e.g. NDJ = ["11","12","01"]
        force_download=False,
        run_avg=3
    ):
        """
        Download reanalysis data for specified center-variable combinations, years, and months,
        handling cross-year seasons (e.g., NDJ).
        """
        dir_to_save = Path(dir_to_save)
        dir_to_save.mkdir(parents=True, exist_ok=True)

        # Parse center and variable strings
        centers = [cv.split(".")[0] for cv in center_variable]
        vars_   = [cv.split(".")[1] for cv in center_variable]

        # Example reanalysis centers
        centre_dict = {"ERA5": "ERA5", "MERRA2": "MERRA2"}

        # Single-level monthly means
        variables_1 = {
            "PRCP": "total_precipitation",
            "TEMP": "2m_temperature",
            "TMAX": "maximum_2m_temperature_in_the_last_24_hours",
            "TMIN": "minimum_2m_temperature_in_the_last_24_hours",
            "UGRD10": "10m_u_component_of_wind",
            "VGRD10": "10m_v_component_of_wind",
            "SST": "sea_surface_temperature",
            "SLP": "mean_sea_level_pressure",
            "DSWR": "surface_solar_radiation_downwards",
            "DLWR": "surface_thermal_radiation_downwards",
            "NOLR": "top_net_thermal_radiation",

        }
        # Pressure-level monthly means
        variables_2 = {
            "HUSS_1000": "specific_humidity",
            "HUSS_925": "specific_humidity",
            "HUSS_850": "specific_humidity",
            "UGRD_1000": "u_component_of_wind",
            "UGRD_925": "u_component_of_wind",
            "UGRD_850": "u_component_of_wind",
            "VGRD_1000": "v_component_of_wind",
            "VGRD_925": "v_component_of_wind",
            "VGRD_850": "v_component_of_wind",
        }
        
        # Helper for zero-padded month strings
        def m2str(m: int):
            return f"{m:02d}"

        # Convert months to integers (e.g. ["11","12","01"] -> [11,12,1])
        season_months = [int(m) for m in seas]
        pivot = season_months[0]
        # For naming
        season_str = "".join([calendar.month_abbr[m] for m in season_months])

        for c, v in zip(centers, vars_):
            # =================================================================
            # Special Case: NOAA ERSST from IRIDL
            # =================================================================
            if c == "NOAA" and v == "SST":
                out_file = dir_to_save / f"{c}_{v}_{year_start}_{year_end}_{season_str}.nc"
                if not force_download and out_file.exists():
                    print(f"{out_file} exists. Skipping.")
                    continue
        
                try:
                    # Build IRIDL URL using bounding box [N, W, S, E]
                    url = build_iridl_url_ersst(
                        year_start=year_start,
                        year_end=year_end,
                        bbox=area,     # e.g. [10, -15, -5, 15]
                        run_avg=run_avg,
                        month_start="Jan",
                        month_end="Dec"
                    )
                    print(f"Using IRIDL URL: {url}")
                    
                    # 2) Open dataset with manual processing
                    ds = xr.open_dataset(url, decode_times=False)
                    ds = decode_cf(ds, "T").rename({"T":"time"}).convert_calendar("proleptic_gregorian", align_on="year").rename({"time":"T"})

                    ds = ds.rename({
                            'sst': 'SST',  # Rename variable to match expected name
                        })
                                                                                                               
                    # 6) Post-process
                    ds = self._postprocess_reanalysis_ersst(ds, v)
                    ds['T'] = ds['T'].astype('datetime64[ns]')                   
                    
                    # 7) Final formatting
                    ds_agg = ds.where(ds.T.dt.month == int(seas[1]), drop=True)
                    ds_agg = fix_time_coord(ds_agg,seas)
                    ds_agg = ds_agg.rename({
                            'SST': 'sst',  # Rename variable to match expected name
                        })
                    # 8) Save
                    ds_agg.to_netcdf(out_file)
                    print(f"Saved NOAA ERSST data to {out_file}")
        
                except Exception as e:
                    print(f"Failed to download {c}/{v}: {str(e)}")
                continue

        # # Loop over each reanalysis center/var
        # for c, v in zip(centers, vars_):
        #     # e.g. ERA5, PRCP
            if c not in centre_dict:
                print(f"Unknown center: {c}, skipping.")
                continue

            rean = centre_dict[c]
            out_file = dir_to_save / f"{c}_{v}_{year_start}_{year_end}_{season_str}.nc"
            if (not force_download) and out_file.exists():
                print(f"{out_file} already exists. Skipping.")
                continue

            # List to accumulate partial downloads
            combined_datasets = []

            # Iterate over each year in [year_start..year_end]
            for year in range(year_start, year_end + 1):
                # Split months
                base_months = [m for m in season_months if m >= pivot]
                next_months = [m for m in season_months if m < pivot]

                # (A) Base-year
                if base_months:
                    base_str = [m2str(m) for m in base_months]
                    partA = dir_to_save / f"{c}_{v}_{year}_{season_str}_partA.nc"

                    # Decide dataset + request
                    if v in variables_2:
                        press_level = v.split("_")[1]  # e.g. 925 from "HUSS_925"
                        dataset = "reanalysis-era5-pressure-levels-monthly-means"
                        request = {
                            "product_type": ["monthly_averaged_reanalysis"],
                            "variable": variables_2[v],
                            "pressure_level": press_level,
                            "year": str(year),
                            "month": base_str,
                            "time": ["00:00"],
                            "area": area,
                            "data_format": "netcdf",
                        }
                    else:
                        dataset = "reanalysis-era5-single-levels-monthly-means"
                        request = {
                            "product_type": ["monthly_averaged_reanalysis"],
                            "variable": variables_1.get(v),
                            "year": str(year),
                            "month": base_str,
                            "time": ["00:00"],
                            "area": area,
                            "data_format": "netcdf",
                        }

                    # Download
                    try:
                        client = cdsapi.Client()
                        print(f"Downloading {c}/{v}: {year}, months={base_str}")
                        client.retrieve(dataset, request).download(str(partA))
                    except Exception as e:
                        print(f"Download error for {c}/{v}, year={year} partA: {e}")
                        continue

                    with xr.open_dataset(partA) as dsA:
                        dsA = dsA.load()
                        dsA = self._postprocess_reanalysis(dsA, v)
                        combined_datasets.append(dsA)
                    os.remove(partA)

                # (B) Next-year
                if next_months and (year < year_end+1):
                    year_next = year + 1
                    next_str = [m2str(m) for m in next_months]
                    partB = dir_to_save / f"{c}_{v}_{year}_{season_str}_partB_{year_next}.nc"

                    if v in variables_2:
                        press_level = v.split("_")[1]
                        dataset = "reanalysis-era5-pressure-levels-monthly-means"
                        request = {
                            "product_type": ["monthly_averaged_reanalysis"],
                            "variable": variables_2[v],
                            "pressure_level": press_level,
                            "year": str(year_next),
                            "month": next_str,
                            "time": ["00:00"],
                            "area": area,
                            "data_format": "netcdf",
                        }
                    else:
                        dataset = "reanalysis-era5-single-levels-monthly-means"
                        request = {
                            "product_type": ["monthly_averaged_reanalysis"],
                            "variable": variables_1.get(v),
                            "year": str(year_next),
                            "month": next_str,
                            "time": ["00:00"],
                            "area": area,
                            "data_format": "netcdf",
                            
                        }

                    # Download
                    try:
                        client = cdsapi.Client()
                        print(f"Downloading {c}/{v}: {year_next}, months={next_str}")
                        client.retrieve(dataset, request).download(str(partB))
                    except Exception as e:
                        print(f"Download error for {c}/{v}, year={year_next} partB: {e}")
                        continue

                    with xr.open_dataset(partB) as dsB:
                        dsB = dsB.load()
                        dsB = self._postprocess_reanalysis(dsB, v)
                        combined_datasets.append(dsB)
                    os.remove(partB)

            if combined_datasets:
                dsC = xr.concat(combined_datasets, dim="time")
            
                # If T variable -> K to °C
                if v in ["TMIN","TEMP","TMAX","SST"]:
                    dsC = dsC - 273.15
                
                # For precipitation or others, the aggregator decides sum vs mean
                dsC = self._aggregate_crossyear(
                    ds=dsC,
                    season_months=season_months,
                    var_name=v
                )
                
                if v == "PRCP":
                    nbjour = len(season_months)*30
                    dsC = 1000*ds*nbjour  # !!!!! Convert to mm/month
                
                if v in ["DSWR", "DLWR","NOLR"]:
                    dsC = dsC/86400  # Convert to W/m2

                if v == "SLP":
                    dsC = dsC / 100  # Convert to hPa(mb)

                dsC["time"] = [f"{year}-{seas[1]}-01" for year in dsC["time"].astype(str).values]
                dsC["time"] = dsC["time"].astype("datetime64[ns]")
                dsC = dsC.rename({"time": "T"})
                
                # Save final
                dsC.to_netcdf(out_file)
                print(f"Saved final reanalysis file: {out_file}")
            else:
                print(f"No data found for {c}/{v}.")

    def WAS_Download_ERA5Land(
        self,
        dir_to_save,
        center_variable,
        year_start,
        year_end,
        area,
        seas=["01", "02", "03"],  # e.g. NDJ = ["11","12","01"]
        force_download=False,
    ):
        """
        Download ERA5-Land reanalysis data for specified variable combinations, years, and months,
        handling cross-year seasons (e.g., NDJ).
        Parameters:
            dir_to_save (str): Directory to save the downloaded files.
            center_variable (list): List of center-variable identifiers (e.g., ["ERA5Land.PRCP", "ERA5Land.TEMP"]).
            year_start (int): Start year for the data.
            year_end (int): End year for the data.
            area (list): Bounding box as [North, West, South, East].
            seas (list): List of months (e.g., ["11","12","01"] for NDJ).
            force_download (bool): If True, forces download even if file exists.
        """
        dir_to_save = Path(dir_to_save)
        dir_to_save.mkdir(parents=True, exist_ok=True)
        # Parse center and variable strings
        centers = [cv.split(".")[0] for cv in center_variable]
        vars_ = [cv.split(".")[1] for cv in center_variable]
        # ERA5-Land does not have pressure levels, only single-level variables
        variables_1 = {
            "PRCP": "total_precipitation",
            "TEMP": "2m_temperature",
            "TDEW": "2m_dewpoint_temperature",
            "UGRD10": "10m_u_component_of_wind",
            "VGRD10": "10m_v_component_of_wind",
            "DSWR": "surface_solar_radiation_downwards",
            "DLWR": "surface_thermal_radiation_downwards",
            "NOLR": "surface_net_thermal_radiation_downwards",  # Adjusted for ERA5-Land
            "RUNOFF": "surface_runoff"
            
        }
        # Helper for zero-padded month strings
        def m2str(m: int):
            return f"{m:02d}"
        # Convert months to integers
        season_months = [int(m) for m in seas]
        pivot = season_months[0]
        # For naming
        season_str = "".join([calendar.month_abbr[m] for m in season_months])
        for c, v in zip(centers, vars_):
            if c != "ERA5Land":
                print(f"This function is for ERA5Land only. Skipping {c}.")
                continue
            if v not in variables_1:
                print(f"Unknown variable for ERA5Land: {v}. Skipping.")
                continue
            cds_var = variables_1[v]
            # if cds_var == "surface_runoff":
            #     pivot_int = pivot
            #     previous = pivot_int - 1
            #     previous = str(previous).zfill(2) if previous > 0 else 12
            #     season_months = [previous] + season_months
            #     pivot = previous
            
            out_file = dir_to_save / f"{c}_{v}_{year_start}_{year_end}_{season_str}.nc"
            if not force_download and out_file.exists():
                print(f"{out_file} already exists. Skipping.")
                continue
            combined_datasets = []
            for year in range(year_start, year_end + 1):
                base_months = [m for m in season_months if m >= pivot]
                next_months = [m for m in season_months if m < pivot]
                # (A) Base-year
                if base_months:
                    base_str = [m2str(m) for m in base_months]
                    partA = dir_to_save / f"{c}_{v}_{year}_{season_str}_partA.nc"
                    dataset = "reanalysis-era5-land-monthly-means"
                    request = {
                        "product_type": "monthly_averaged_reanalysis",
                        "variable": cds_var,
                        "year": str(year),
                        "month": base_str,
                        "time": "00:00",
                        "area": area,
                        "data_format": "netcdf",
                    }
                    try:
                        client = cdsapi.Client()
                        print(f"Downloading {c}/{v}: {year}, months={base_str}")
                        client.retrieve(dataset, request).download(str(partA))
                    except Exception as e:
                        print(f"Download error for {c}/{v}, year={year} partA: {e}")
                        continue
                    with xr.open_dataset(partA) as dsA:
                        dsA = dsA.load()
                        dsA = self._postprocess_reanalysis(dsA, v)
                        combined_datasets.append(dsA)
                    os.remove(partA)
                # (B) Next-year
                if next_months and (year < year_end + 1):
                    year_next = year + 1
                    next_str = [m2str(m) for m in next_months]
                    partB = dir_to_save / f"{c}_{v}_{year}_{season_str}_partB_{year_next}.nc"
                    request["year"] = str(year_next)
                    request["month"] = next_str
                    try:
                        client = cdsapi.Client()
                        print(f"Downloading {c}/{v}: {year_next}, months={next_str}")
                        client.retrieve(dataset, request).download(str(partB))
                    except Exception as e:
                        print(f"Download error for {c}/{v}, year={year_next} partB: {e}")
                        continue
                    with xr.open_dataset(partB) as dsB:
                        dsB = dsB.load()
                        dsB = self._postprocess_reanalysis(dsB, v)
                        combined_datasets.append(dsB)
                    os.remove(partB)
            if combined_datasets:
                dsC = xr.concat(combined_datasets, dim="time")
                # Unit conversions
                if v in ["TEMP", "TDEW"]:
                    dsC = dsC - 273.15
                # Aggregate
                dsC = self._aggregate_crossyear(
                    ds=dsC,
                    season_months=season_months,
                    var_name=v
                )
                if v == "PRCP":
                    dsC = 1000 * dsC * len(season_months) * 30  # Convert to mm (approximate, as in existing code)
                if v == "RUNOFF":
                    #dsC = dsC * len(season_months) * 30 # Convert to mm (approximate, as in existing code)
                    lat = dsC.Y
                    lon = dsC.X
                    dlon = np.deg2rad(0.1)
                    dlat = np.deg2rad(0.1)
                    r = 6371000 # Earth radius in meters
                    # Area for each grid cell
                    area_ = (r ** 2) * dlon * np.cos(np.deg2rad(lat)) * dlat
                    # Perform the conversion to m^3/s
                    dsC = (dsC * area_) / 86400
                    
                if v in ["DSWR", "DLWR", "NOLR"]:
                    # nbjour = len(season_months) * 30
                    dsC = dsC / 86400  # Convert to W/m2 (approximate)
                dsC["time"] = [f"{year}-{seas[1]}-01" for year in dsC["time"].astype(str).values]
                dsC["time"] = dsC["time"].astype("datetime64[ns]")
                dsC = dsC.rename({"time": "T"})
                # Save final
                dsC.to_netcdf(out_file)
                print(f"Saved final ERA5-Land file: {out_file}")
            else:
                print(f"No data found for {c}/{v}.")

    def WAS_Download_ERA5Land_daily(
            self,
            dir_to_save,
            center_variable,
            year_start,
            year_end,
            area,
            force_download=False,
            max_retries=3,
            retry_delay=5,
        ):
        """
        Download daily ERA5-Land reanalysis data from the Copernicus Data Store (CDS)
        for specified variables and years, with retries for failed downloads.
        Parameters
        ----------
        dir_to_save : str or pathlib.Path
            Directory path where the downloaded NetCDF files will be saved.
            The directory will be created if it does not exist.
        center_variable : list of str
            List of center-variable identifiers (e.g., ["ERA5Land.PRCP", "ERA5Land.TEMP"]).
        year_start : int
            Start year for the data to download (inclusive).
        year_end : int
            End year for the data to download (inclusive).
        area : list of float
            Bounding box for spatial subsetting in the format [North, West, South, East].
        force_download : bool, optional
            If True, forces download even if the output file exists. Default is False.
        max_retries : int, optional
            Maximum number of retry attempts for failed downloads. Default is 3.
        retry_delay : int, optional
            Seconds to wait between retry attempts. Default is 5.
        Returns
        -------
        None
            The function saves NetCDF files to `dir_to_save` but does not return a value.
            Output files are named as `Daily_<variable>_<year_start>_<year_end>.nc`.
        Notes
        -----
        - The function downloads hourly data from the CDS dataset "reanalysis-era5-land" 
          and aggregates it to daily resolution.
        - Aggregation: sum for accumulative variables (e.g., PRCP, radiation), mean for others (e.g., TEMP).
        - Unit conversions: PRCP to mm/day, TEMP to °C, radiation to W/m² (daily average).
        - Coordinates are renamed to "X" (longitude), "Y" (latitude), and "T" (time),
          with latitude flipped.
        - Downloads are performed month-by-month due to API limitations.
        - Requires a valid CDS API key configured in `~/.cdsapirc`.
        """
        dir_to_save = Path(dir_to_save)
        dir_to_save.mkdir(parents=True, exist_ok=True)
        days = [f"{day:02}" for day in range(1, 32)]
        months = [f"{month:02}" for month in range(1, 13)]
        hours = [f"{h:02}:00" for h in range(24)]
        variables_1 = {
            "PRCP": "total_precipitation",
            "TEMP": "temperature_2m",
            "TDEW": "dewpoint_temperature_2m",
            "UGRD10": "u_component_of_wind_10m",
            "VGRD10": "v_component_of_wind_10m",
            "DSWR": "surface_solar_radiation_downwards",
            "DLWR": "surface_thermal_radiation_downwards",
            "NOLR": "surface_net_thermal_radiation_downwards",
            "RUNOFF": "surface_runoff",
        }
        centers = [cv.split(".")[0] for cv in center_variable]
        vars_short = [cv.split(".")[1] for cv in center_variable]
        for c, v in zip(centers, vars_short):
            if c != "ERA5Land":
                print(f"Invalid center for this function: {c}. Must be 'ERA5Land'. Skipping.")
                continue
            if v not in variables_1:
                print(f"Unknown variable: {v}. Skipping.")
                continue
            cds_variable = variables_1[v]
            output_path = dir_to_save / f"Daily_{v}_{year_start}_{year_end}.nc"
            if not force_download and output_path.exists():
                print(f"{output_path} already exists. Skipping download.")
                continue
            combined_datasets = []
            all_years_downloaded = True
            for year in range(year_start, year_end + 1):
                for month in range(1, 13):
                    nc_file_path = dir_to_save / f"hourly_{v}_{year}_{month:02d}.nc"
                    success = False
                    retries = 0
                    while retries < max_retries and not success:
                        try:
                            client = cdsapi.Client()
                            dataset = "reanalysis-era5-land"
                            request = {
                                "variable": cds_variable,
                                "year": str(year),
                                "month": f"{month:02}",
                                "day": days,
                                "time": hours,
                                "area": area,
                                "data_format": "netcdf",
                                "download_format": "unarchived"
                            }
                            print(f"Attempt {retries + 1}/{max_retries}: Downloading {cds_variable} data for {year}-{month:02d}...")
                            client.retrieve(dataset, request).download(str(nc_file_path))
                            print(f"Downloaded: {nc_file_path}")
                            success = True
                        except Exception as e:
                            retries += 1
                            print(f"Attempt {retries}/{max_retries} failed for {cds_variable} data for {year}-{month:02d}: {e}")
                            if retries < max_retries:
                                print(f"Retrying after {retry_delay} seconds...")
                                _time.sleep(retry_delay)
                            if nc_file_path.exists():
                                os.remove(nc_file_path)
                                print(f"Deleted incomplete file: {nc_file_path}")
                    if not success:
                        print(f"Failed to download {cds_variable} data for {year}-{month:02d} after {max_retries} attempts.")
                        all_years_downloaded = False
                        continue
                    try:
                        ds_month = xr.open_dataset(nc_file_path)
                        ds_daily = self._postprocess_reanalysis(ds_month, v)
                        if v == "PRCP":
                            ds_daily = ds_daily.sel(time=ds_daily.time.dt.hour == 0) * 1000
                            ds_daily_0 = ds_daily.isel(time=0)
                            ds_daily_0.coords['time'] = pd.Timestamp(f"{year}-{month}-{calendar.monthrange(year, month)[1]}")
                            ds_daily = ds_daily.shift(time=-1).dropna(dim="time")
                            ds_daily = xr.concat([ds_daily_0, ds_daily], dim="time")
                        if v == "RUNOFF":
                            ds_daily = ds_daily.sel(time=ds_daily.time.dt.hour == 0)
                            ds_daily_0 = ds_daily.isel(time=0)
                            ds_daily_0.coords['time'] = pd.Timestamp(f"{year}-{month}-{calendar.monthrange(year, month)[1]}")
                            ds_daily = ds_daily.shift(time=-1).dropna(dim="time")
                            ds_daily = xr.concat([ds_daily_0, ds_daily], dim="time")
                            lat = ds_daily.Y
                            lon = ds_daily.X
                            dlon = np.deg2rad(0.1)
                            dlat = np.deg2rad(0.1)
                            r = 6371000 # Earth radius in meters
                            # Area for each grid cell
                            area_= (r ** 2) * dlon * np.cos(np.deg2rad(lat)) * dlat
                            # Perform the conversion to m^3/s
                            ds_daily = (ds_daily * area_) / 86400
                        if v in ["DSWR", "DLWR", "NOLR"]:
                            ds_daily = ds_daily.sel(time=ds_daily.time.dt.hour == 0) / 86400
                            ds_daily_0 = ds_daily.isel(time=0)
                            ds_daily_0.coords['time'] = pd.Timestamp(f"{year}-{month}-{calendar.monthrange(year, month)[1]}")
                            ds_daily = ds_daily.shift(time=-1).dropna(dim="time")
                            ds_daily = xr.concat([ds_daily_0, ds_daily], dim="time")
                        if v in ["TEMP", "TDEW"]:
                            ds_daily = ds_daily - 273.15  # K to °C
                        combined_datasets.append(ds_daily)
                    except Exception as e:
                        print(f"Failed to process {nc_file_path}: {e}")
                        all_years_downloaded = False
                    if nc_file_path.exists():
                        os.remove(nc_file_path)
                        print(f"Deleted hourly file: {nc_file_path}")
            if combined_datasets and all_years_downloaded:
                try:
                    combined_ds = xr.concat(combined_datasets, dim="time")
                    combined_ds = combined_ds.rename({"time": "T"})
                    combined_ds.to_netcdf(output_path)
                    combined_ds.close()
                    print(f"Combined dataset for ERA5Land.{v} saved to {output_path}")
                except Exception as e:
                    print(f"Failed to process or save combined dataset for ERA5Land.{v}: {e}")
            else:
                print(f"Skipping save for ERA5Land.{v} due to incomplete downloads.")

    def WAS_Download_CHIRPSv3_Daily(
            self,
            dir_to_save,
            year_start,
            year_end,
            blend_type="ERA5",
            area=None,
            force_download=False,
            max_retries=3,
            retry_delay=5,
        ):
        """
        Download daily CHIRPS v3.0 precipitation (blended with ERA5 or IMERGlate-v07) from the Copernicus Data Store (CDS)
        for specified years, with retries for failed downloads.
        Parameters
        ----------
        dir_to_save : str or pathlib.Path
            Directory path where the downloaded NetCDF files will be saved.
            The directory will be created if it does not exist.
        year_start : int
            Start year for the data to download (inclusive).
        year_end : int
            End year for the data to download (inclusive).
        blend_type : str
            Blend type, either "ERA5" or "IMERGlate-v07" (default: "ERA5").
            Note: IMERGlate-v07 availability starts from ~2000; earlier years may fail.
        area : list of float
            Bounding box for spatial subsetting in the format [North, West, South, East].
        force_download : bool, optional
            If True, forces download even if the output file exists. Default is False.
        max_retries : int, optional
            Maximum number of retry attempts for failed downloads. Default is 3.
        retry_delay : int, optional
            Seconds to wait between retry attempts. Default is 5.
        Returns
        -------
        None
            The function saves NetCDF files to `dir_to_save` but does not return a value.
            Output files are named as `Daily_PRCP_{blend_type}_{year_start}_{year_end}.nc`.
        Notes
        -----
        - Downloads individual daily TIFF files, processes them with rioxarray, clips if area specified,
          and combines into a single NetCDF with daily time dimension.
        - Units: precipitation in mm/day.
        - Coordinates renamed to "X" (longitude), "Y" (latitude), "T" (time), with Y flipped if needed.
        - Deletes temporary TIFF files after processing.
        - Skips invalid dates (e.g., Feb 30) automatically.
        """
        dir_to_save = Path(dir_to_save)
        dir_to_save.mkdir(parents=True, exist_ok=True)

        output_path = dir_to_save / f"Daily_PRCP_{year_start}_{year_end}.nc"
        if not force_download and output_path.exists():
            print(f"{output_path} already exists. Skipping download.")
            
        combined_datasets = []
        all_years_downloaded = True
        for year in range(year_start, year_end + 1):
            for month in range(1, 13):
                ndays = calendar.monthrange(year, month)[1]
                for day in range(1, ndays + 1):
                    tif_file_path = dir_to_save / f"chirps-v3.0.{year}.{month:02d}.{day:02d}.tif"
                    success = False
                    retries = 0
                    while retries < max_retries and not success:
                        try:
                            da = self._fetch_chirps_daily(
                                year=year,
                                month=month,
                                day=day,
                                dir_to_save=dir_to_save,
                                blend_type=blend_type,
                                force_download=force_download,
                                area=area
                            )
                            if da is not None:
                                combined_datasets.append(da)
                                success = True
                        except Exception as e:
                            retries += 1
                            print(f"Attempt {retries}/{max_retries} failed for {year}-{month:02d}-{day:02d}: {e}")
                            if retries < max_retries:
                                print(f"Retrying after {retry_delay} seconds...")
                                _time.sleep(retry_delay)
                            if tif_file_path.exists():
                                os.remove(tif_file_path)
                                print(f"Deleted incomplete TIFF: {tif_file_path}")
                    if not success:
                        print(f"Failed to download/process {year}-{month:02d}-{day:02d} after {max_retries} attempts.")
                        # Continue to next day; don't set all_years_downloaded=False to allow partial data
                    if tif_file_path.exists():
                        os.remove(tif_file_path)
                        print(f"Deleted TIFF: {tif_file_path}")
        if combined_datasets:
            try:
                combined_ds = xr.concat(combined_datasets, dim="time").to_dataset(name="precip")
                combined_ds = combined_ds.rename({"x": "X", "y": "Y", "time": "T"})
                combined_ds = combined_ds.isel(Y=slice(None, None, -1))
                combined_ds.to_netcdf(output_path)
                combined_ds.close()
                print(f"Combined daily dataset for CHIRPS ({blend_type}) saved to {output_path}")
            except Exception as e:
                print(f"Failed to process or save combined dataset for CHIRPS ({blend_type}): {e}")
        else:
            print(f"No data downloaded for CHIRPS ({blend_type}).")
    
    def _fetch_chirps_daily(self, year, month, day, dir_to_save, blend_type, force_download, area):
            """
            Construct the CHIRPS v3.0 daily TIF URL for (year, month, day),
            download if needed, open as xarray, and optionally clip to 'area'.
           
            File format is: chirps-v3.0.YYYY.MM.DD.tif
            """
            base_url = f"https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/{blend_type}/{year}"
            fname = f"chirps-v3.0.{year}.{month:02d}.{day:02d}.tif"
            url = f"{base_url}/{fname}"
            local_path = Path(dir_to_save) / fname
            if not local_path.exists() or force_download:
                try:
                    with requests.get(url, stream=True, timeout=120) as r:
                        r.raise_for_status()
                        with open(local_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                except Exception as e:
                    print(f"[ERROR] Could not download {url}: {e}")
                    return None
            else:
                print(f"[SKIP] {fname} is already present. (Use force_download=True to overwrite)")
            # Open as xarray via rioxarray
            try:
                da = rioxr.open_rasterio(local_path, masked=True).squeeze()
                time_coord = pd.to_datetime(f"{year}-{month:02d}-{day:02d}")
                da = da.expand_dims(time=[time_coord])
                da.name = "precip"
                # If area is provided, clip
                if area and len(area) == 4:
                    north, west, south, east = area
                    da = da.rio.clip_box(
                        minx=west,
                        miny=south,
                        maxx=east,
                        maxy=north
                    )
                return da
            except Exception as e:
                print(f"[ERROR] Could not open/parse {local_path}: {e}")
                return None
                

    def WAS_Download_CHIRPSv3_Seasonal(
        self,
        dir_to_save,
        variables,
        year_start,
        year_end,
        region="africa",
        area=None,
        season_months=["03", "04", "05"],
        force_download=False        
    ):
        """
        Download CHIRPS v3.0 monthly precipitation for a specified cross-year season
        from year_start to year_end, optionally clipped to 'area',
        and aggregate them into a single NetCDF file.
        Parameters:
            dir_to_save (str): Directory to save the downloaded files.
            variables (list): List of variables to download (e.g., ["PRCP"]).
            year_start (int): Start year for the data.
            year_end (int): End year for the data.
            region (str): CHIRPS region (default: "africa").
            area (list): Bounding box as [North, West, South, East] (optional).
            season_months (list): List of months as strings (e.g., ["03", "04", "05"]).
            force_download (bool): If True, forces download even if file exists.
        Returns:
            None: Saves the aggregated seasonal data to a NetCDF file.  
        """
        dir_to_save = Path(dir_to_save)
        dir_to_save.mkdir(parents=True, exist_ok=True)
        season_months = [int(m) for m in season_months]
        variables = variables
        # Example: "MAM"
        season_str = "".join([calendar.month_abbr[m] for m in season_months])
        pivot = season_months[0]

        out_nc = dir_to_save / f"Obs_PRCP_{year_start}_{year_end}_{season_str}.nc"
        if out_nc.exists() and not force_download:
            print(f"[INFO] {out_nc} already exists. Skipping.")
            return

        # We'll store monthly DataArrays here
        all_data_arrays = []

        # Loop over years
        for year in range(year_start, year_end + 1):
            # Base-year months (>= pivot)
            base_months = [m for m in season_months if m >= pivot]
            # Next-year months (< pivot)
            next_months = [m for m in season_months if m < pivot]

            # Part A: Base-year months
            for m in base_months:
                da = self._fetch_chirps_monthly(
                    year=year,
                    month=m,
                    dir_to_save=dir_to_save,
                    region=region,
                    force_download=force_download,
                    area=area
                )
                if da is not None:
                    all_data_arrays.append(da)

            # Part B: Next-year months
            if next_months and (year < year_end + 1):
                year_next = year + 1
                for m in next_months:
                    da = self._fetch_chirps_monthly(
                        year=year_next,
                        month=m,
                        dir_to_save=dir_to_save,
                        region=region,
                        force_download=force_download,
                        area=area
                    )
                    if da is not None:
                        all_data_arrays.append(da)

        if len(all_data_arrays) == 0:
            print("[WARNING] No CHIRPS data arrays were opened/downloaded.")
            return

        # Concatenate along time
        ds_all = xr.concat(all_data_arrays, dim="time").to_dataset(name="precip")

        # Aggregate across the cross-year season (summing monthly precipitation)
        ds_season = self._aggregate_chirps(ds_all, season_months)

        # Rename dims if desired
        if "x" in ds_season.dims:
            ds_season = ds_season.rename({"x": "X"})
        if "y" in ds_season.dims:
            ds_season = ds_season.rename({"y": "Y"})
        if "time" in ds_season.dims:
            ds_season = ds_season.rename({"time": "T"})
        # Write to NetCDF
        ds_season.to_netcdf(out_nc)
        print(f"[INFO] Saved seasonal CHIRPS data to {out_nc}")
        # Delete individual monthly TIF files
        for tif_file in dir_to_save.glob("chirps-v3.0.*.tif"):
            try:
                os.remove(tif_file)
                print(f"[CLEANUP] Deleted {tif_file}")
            except Exception as e:
                print(f"[ERROR] Could not delete {tif_file}: {e}")



    def _fetch_chirps_monthly(self, year, month, dir_to_save, region, force_download, area):
        """
        Construct the CHIRPS v3.0 monthly TIF URL for (year, month), 
        download if needed, open as xarray, and optionally clip to 'area'.
        
        File format is: chirps-v3.0.YYYY.MM.tif
        """
        base_url = f"https://data.chc.ucsb.edu/products/CHIRPS/v3.0/monthly/{region}/tifs"
        fname = f"chirps-v3.0.{year}.{month:02d}.tif"
        url = f"{base_url}/{fname}"

        local_path = Path(dir_to_save) / fname
        download_file(url, local_path, force_download=force_download, chunk_size=8192, timeout=120)
        
        # # Download if needed
        # if (not local_path.exists()) or force_download:
        #     print(f"[DOWNLOAD] {url}")
        #     try:
        #         with requests.get(url, stream=True, timeout=120) as r:
        #             r.raise_for_status()
        #             with open(local_path, "wb") as f:
        #                 for chunk in r.iter_content(chunk_size=8192):
        #                     f.write(chunk)
        #     except Exception as e:
        #         print(f"[ERROR] Could not download {url}: {e}")
        #         return None
        # else:
        #     print(f"[SKIP] {fname} is already present. (Use force_download=True to overwrite)")

        # Open as xarray via rioxarray
        try:
            da = rioxr.open_rasterio(local_path, masked=True).squeeze()
            time_coord = pd.to_datetime(f"{year}-{month:02d}-01")
            da = da.expand_dims(time=[time_coord])
            da.name = "precip"

            # If area is provided, clip
            if area and len(area) == 4:
                north, west, south, east = area
                da = da.rio.clip_box(
                    minx=west,
                    miny=south,
                    maxx=east,
                    maxy=north
                )

            return da

        except Exception as e:
            print(f"[ERROR] Could not open/parse {local_path}: {e}")
            return None

    def _aggregate_chirps(self, ds, season_months):
        """
        Sum monthly precipitation across the cross-year season.
        """
        if "time" not in ds.coords:
            raise ValueError("Dataset must have a 'time' dimension.")

        pivot = season_months[0]
        # Label each time with 'season_year'
        season_year = ds["time"].dt.year.where(ds["time"].dt.month >= pivot,
                                               ds["time"].dt.year - 1)
        ds = ds.assign_coords(season_year=season_year)

        # Keep only the months we want
        ds = ds.where(ds["time"].dt.month.isin(season_months), drop=True)

        # Sum across the months for precipitation
        ds_out = ds.groupby("season_year").sum("time", skipna=True)

        # Rename season_year -> time
        ds_out = ds_out.rename({"season_year": "time"})

        # Optionally make the new time coordinate more descriptive:
        new_times = []
        for sy in ds_out.coords["time"].values:
            new_times.append(f"{sy}-{pivot:02d}-01")
        ds_out = ds_out.assign_coords(time=pd.to_datetime(new_times))

        return ds_out
####
    def WAS_Download_TAMSAT_Seasonal(
            self,
            dir_to_save: Union[str, Path],
            product: Literal["rfe", "soil_moisture"] = "rfe",
            variables: Optional[Sequence[str]] = None,
            year_start: int = 1983,
            year_end: int = 2025,
            area: Optional[List[float]] = None,
            season_months: List[str] = ["03", "04", "05"],
            version: Optional[str] = None,
            force_download: bool = False,
            agg: Optional[Literal["sum", "mean"]] = None,
        ) -> Path:
            """
            Download and aggregate TAMSAT monthly data (RFE v3.1 or Soil Moisture v2.3.1) for a specified season.
            Parameters
            ----------
            dir_to_save : str | Path
                Directory where monthly files and the seasonal output will be saved.
            product : {"rfe", "soil_moisture"}, default "rfe"
                Dataset to download: "rfe" (precipitation) or "soil_moisture".
            variables : sequence of str, optional
                Names of variables to extract from NetCDF. If None, chosen by product.
                - rfe: defaults to ("rfe",)
                - soil_moisture: defaults to ("sm",)
            year_start : int, default 1983
                First seasonal year (pivot year) to include.
            year_end : int, default 2025
                Last year for which data is included (inclusive). For seasons spanning calendar years, the last pivot year processed will be year_end - 1 to ensure no data from year_end + 1 is fetched.
            area : list[float], optional
                Bounding box [north, west, south, east] in degrees.
            season_months : sequence[str], default ("03","04","05")
                Months defining the season, e.g. ("11","12","01") for NDJ.
            version : str, optional
                Product version. Defaults to:
                - rfe: "v3.1"
                - soil_moisture: "v2.3.1"
            force_download : bool, default False
                Re-download monthly files even if present locally.
            agg : {"sum","mean"}, optional
                Seasonal aggregation. Defaults to:
                - rfe: "sum"
                - soil_moisture: "mean"
            Returns
            -------
            Path
                Path to the seasonal aggregated NetCDF file.
            """
            dir_to_save = Path(dir_to_save)
            dir_to_save.mkdir(parents=True, exist_ok=True)
            season_months = tuple(season_months)
            # ---- sensible defaults by product ----
            if product == "rfe":
                variables = variables or ("rfe")
                version = version or "v3.1"
                agg = agg or "sum"
                std_name = "precip"
            elif product == "soilmoisture":
                variables = variables or ("smc_avail_top",)
                version = version or "v2.3.1"
                agg = agg or "mean"
                std_name = "soil_moisture"
            else:
                raise ValueError("product must be 'rfe' or 'soilmoisture'")
            # ---- validate inputs ----
            if year_start > year_end:
                raise ValueError("year_start must be <= year_end.")
            season_months_int: List[int] = [int(m) for m in season_months]
            if not all(1 <= m <= 12 for m in season_months_int):
                raise ValueError("Season months must be valid month numbers (1-12).")
            area_tuple: Optional[Tuple[float, float, float, float]] = (
                tuple(map(float, area)) if area else None
            )
            season_str = "".join(calendar.month_abbr[m] for m in season_months_int)
            pivot = season_months_int[0]
            # ---- output filename ----
            out_nc = dir_to_save / f"Obs_{product.upper()}_{year_start}_{year_end}_{season_str}.nc"
            if out_nc.exists() and not force_download:
                print(f"[INFO] {out_nc} already exists – skip download.")
                return out_nc
            # ---- determine if season spans years ----
            spanning = any(m < pivot for m in season_months_int)
            last_season_year = year_end if not spanning else year_end - 1
            if year_start > last_season_year:
                raise ValueError("No seasons to process based on year_start and year_end.")
            # ---- build seasonal series (aggregate per season_year then stack) ----
            seasonal_list: List[xr.DataArray] = []
            for season_year in range(year_start, last_season_year + 1):
                monthly_das: List[xr.DataArray] = []
                # Part A: base-year months (>= pivot)
                for m in (m for m in season_months_int if m >= pivot):
                    da = self._fetch_tamsat_monthly(
                        product=product,
                        version=version,
                        year=season_year,
                        month=m,
                        dir_to_save=dir_to_save,
                        force_download=force_download,
                        area=area_tuple,
                        keep_vars=variables,
                        std_name=std_name,
                    )
                    if da is not None:
                        monthly_das.append(da)
                # Part B: next-year months (< pivot)
                if spanning:
                    next_year = season_year + 1
                    for m in (m for m in season_months_int if m < pivot):
                        da = self._fetch_tamsat_monthly(
                            product=product,
                            version=version,
                            year=next_year,
                            month=m,
                            dir_to_save=dir_to_save,
                            force_download=force_download,
                            area=area_tuple,
                            keep_vars=variables,
                            std_name=std_name,
                        )
                        if da is not None:
                            monthly_das.append(da)
                if not monthly_das:
                    # nothing for this season_year → skip
                    continue
                # stack months then aggregate for this season
                season_stack = xr.concat(monthly_das, dim="time")
                if agg == "sum":
                    season_da = season_stack.sum(dim="time", keep_attrs=True)
                elif agg == "mean":
                    season_da = season_stack.mean(dim="time", keep_attrs=True)
                else:
                    raise ValueError("agg must be 'sum' or 'mean'.")
                # give a representative time stamp (pivot-year)
                season_time = pd.to_datetime(f"{season_year}-{pivot:02d}-15")
                season_da = season_da.expand_dims(time=[season_time])
                seasonal_list.append(season_da)
            if not seasonal_list:
                raise RuntimeError("No TAMSAT files were downloaded or opened for any season.")
            # ---- concat seasons and save ----
            da_all = xr.concat(seasonal_list, dim="time")
            ds_out = da_all.to_dataset(name=std_name)

            # harmonize dims if needed
            rename_dict = {k: v for k, v in {"lon": "X", "lat": "Y", "time": "T"}.items() if k in ds_out.dims}
            ds_out = ds_out.rename(rename_dict)
            ds_out.to_netcdf(out_nc)
            print(f"[INFO] Saved seasonal {product.upper()} data → {out_nc}")
            return out_nc
    def _fetch_tamsat_monthly(
        self,
        product: Literal["rfe", "soilmoisture"],
        version: str,
        year: int,
        month: int,
        dir_to_save: Path,
        force_download: bool,
        area: Optional[Tuple[float, float, float, float]],
        keep_vars: Sequence[str],
        std_name: str,
    ) -> Optional[xr.DataArray]:
        """
        Download & open a single monthly TAMSAT file (RFE v3.1 or Soil Moisture v2.3.1),
        clip to bbox if provided, and return a standardized DataArray.
        Returns
        -------
        xr.DataArray | None
        """
        if product == "rfe":
            # e.g. .../tamsat/rfe/data/v3.1/monthly/1983/01/rfe1983_01.v3.1.nc
            base = (
                "https://gws-access.jasmin.ac.uk/public/tamsat/rfe/data/"
                f"{version}/monthly/{{year}}/{{month:02d}}/rfe{{year}}_{{month:02d}}.{version}.nc"
            )
        else: # soil_moisture
            # e.g. .../tamsat/soil_moisture/data/v2.3.1/monthly/1983/01/sm1983_01.v2.3.1.nc
            base = (
                "https://gws-access.jasmin.ac.uk/public/tamsat/soil_moisture/data/"
                f"{version}/monthly/{{year}}/{{month:02d}}/sm{{year}}_{{month:02d}}.{version}.nc"
            )
        url = base.format(year=year, month=month)
        fname = dir_to_save / url.split("/")[-1]
        # download if needed
        if not fname.exists() or force_download:
            try:
                print(f"[DL ] {url}")
                with requests.get(url, stream=True, timeout=180) as r:
                    r.raise_for_status()
                    with open(fname, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
            except Exception as exc:
                print(f"[ERR] Download failed: {exc}")
                return None
        else:
            print(f"[SKP] {fname.name} already present.")
        # open & standardize
        try:
            ds = xr.open_dataset(fname)
            var = next((v for v in keep_vars if v in ds.data_vars), None)
            if var is None:
                raise KeyError(f"None of {keep_vars} found in {fname.name}; available: {list(ds.data_vars)}")
            # make a 1-step time axis for this month
            da = ds[var].assign_coords(time=[pd.to_datetime(f"{year}-{month:02d}-01")]).astype("float32")
            # spatial clip if requested
            if area:
                n, w, s, e = area
                # TAMSAT is lat/lon naming; ensure correct orientation
                latn = "lat" if "lat" in da.coords else "latitude"
                lonn = "lon" if "lon" in da.coords else "longitude"
                da = da.where(
                    (da[latn] <= n) & (da[latn] >= s) & (da[lonn] >= w) & (da[lonn] <= e),
                    drop=True,
                )
            da.name = std_name
            return da
        except Exception as exc:
            print(f"[ERR] Failed to open dataset: {exc}")
            return None


    def WAS_Download_TAMSAT_Daily(
            self,
            dir_to_save: Union[str, Path],
            product: Literal["rfe", "soilmoisture"] = "rfe",
            variables: Optional[Sequence[str]] = None,
            year_start: str = "1983",
            year_end: str = "2024",
            area: Optional[List[float]] = None,
            version: Optional[str] = None,
            force_download: bool = False,
        ) -> Path:
            """
            Download TAMSAT daily data (RFE v3.1 or Soil Moisture v2.3.1) and combine into a single NetCDF file.
            Parameters
            ----------
            dir_to_save : str | Path
                Directory where daily files and the combined output will be saved.
            product : {"rfe", "soil_moisture"}, default "rfe"
                Dataset to download: "rfe" (precipitation) or "soil_moisture".
            variables : sequence of str, optional
                Names of variables to extract from NetCDF. If None, chosen by product.
                - rfe: defaults to ("rfe",)
                - soil_moisture: defaults to ("sm",)
            start_date : str, default "1983-01-01"
                Start date in "YYYY-MM-DD" format.
            end_date : str, default "2025-10-20"
                End date in "YYYY-MM-DD" format (inclusive).
            area : list[float], optional
                Bounding box [north, west, south, east] in degrees.
            version : str, optional
                Product version. Defaults to:
                - rfe: "v3.1"
                - soil_moisture: "v2.3.1"
            force_download : bool, default False
                Re-download daily files even if present locally.
            Returns
            -------
            Path
                Path to the combined daily NetCDF file.
            """
            dir_to_save = Path(dir_to_save)
            dir_to_save.mkdir(parents=True, exist_ok=True)
            start_date = f"{year_start}-01-01"
            end_date = f"{year_end}-12-31"
            # ---- sensible defaults by product ----
            if product == "rfe":
                variables = variables or ("rfe",)
                version = version or "v3.1"
                prefix = "rfe"
                std_name = "precip"
            elif product == "soilmoisture":
                variables = variables or ("smc_avail_top",)
                version = version or "v2.3.1"
                prefix = "sm"
                std_name = "soil_moisture"
            else:
                raise ValueError("product must be 'rfe' or 'soilmoisture'")
            # ---- validate inputs ----
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            if start_dt > end_dt:
                raise ValueError("start_date must be <= end_date.")
            dates = pd.date_range(start_dt, end_dt, freq="D")
            area_tuple: Optional[Tuple[float, float, float, float]] = (
                tuple(map(float, area)) if area else None
            )
            # ---- output filename ----
            sdate_str = start_date.replace("-", "")
            edate_str = end_date.replace("-", "")
            out_nc = dir_to_save / f"Obs_{product.upper()}_daily_{sdate_str}_{edate_str}.nc"
            if out_nc.exists() and not force_download:
                print(f"[INFO] {out_nc} already exists – skip download.")
                return out_nc
            # ---- build daily series ----
            daily_list: List[xr.DataArray] = []
            for date in dates:
                y = date.year
                m = date.month
                d = date.day
                da = self._fetch_tamsat_daily(
                    product=product,
                    version=version,
                    year=y,
                    month=m,
                    day=d,
                    dir_to_save=dir_to_save,
                    force_download=force_download,
                    area=area_tuple,
                    keep_vars=variables,
                    std_name=std_name,
                    prefix=prefix,
                )
                if da is not None:
                    daily_list.append(da)
            if not daily_list:
                raise RuntimeError("No TAMSAT files were downloaded or opened.")
            # ---- concat days and save ----
            da_all = xr.concat(daily_list, dim="time")
            ds_out = da_all.to_dataset(name=std_name)

            # harmonize dims if needed
            rename_dict = {k: v for k, v in {"lon": "X", "lat": "Y", "time": "T"}.items() if k in ds_out.dims}
            ds_out = ds_out.rename(rename_dict)
            ds_out.to_netcdf(out_nc)
            print(f"[INFO] Saved daily {product.upper()} data → {out_nc}")
            return out_nc
    def _fetch_tamsat_daily(
        self,
        product: Literal["rfe", "soilmoisture"],
        version: str,
        year: int,
        month: int,
        day: int,
        dir_to_save: Path,
        force_download: bool,
        area: Optional[Tuple[float, float, float, float]],
        keep_vars: Sequence[str],
        std_name: str,
        prefix: str,
    ) -> Optional[xr.DataArray]:
        """
        Download & open a single daily TAMSAT file (RFE v3.1 or Soil Moisture v2.3.1),
        clip to bbox if provided, and return a standardized DataArray.
        Returns
        -------
        xr.DataArray | None
        """
        if product == "soilmoisture":
            product_ = "soil_moisture"
        else:
            product_ = product
        base = (
            f"https://gws-access.jasmin.ac.uk/public/tamsat/{product_}/data/"
            f"{version}/daily/{{year}}/{{month:02d}}/{prefix}{{year}}_{{month:02d}}_{{day:02d}}.{version}.nc"
        )
        url = base.format(year=year, month=month, day=day)
        fname = dir_to_save / url.split("/")[-1]
        # download if needed
        if not fname.exists() or force_download:
            try:
                print(f"[DL ] {url}")
                with requests.get(url, stream=True, timeout=180) as r:
                    r.raise_for_status()
                    with open(fname, "wb") as f:
                        for chunk in r.iter_content(8192):
                            if chunk:
                                f.write(chunk)
            except Exception as exc:
                print(f"[ERR] Download failed: {exc}")
                return None
        else:
            print(f"[SKP] {fname.name} already present.")
        # open & standardize
        try:
            ds = xr.open_dataset(fname)
            var = next((v for v in keep_vars if v in ds.data_vars), None)
            if var is None:
                raise KeyError(f"None of {keep_vars} found in {fname.name}; available: {list(ds.data_vars)}")
            # make a 1-step time axis for this day
            da = ds[var].assign_coords(time=[pd.to_datetime(f"{year}-{month:02d}-{day:02d}")]).astype("float32")
            # spatial clip if requested
            if area:
                n, w, s, e = area
                # TAMSAT is lat/lon naming; ensure correct orientation
                latn = "lat" if "lat" in da.coords else "latitude"
                lonn = "lon" if "lon" in da.coords else "longitude"
                da = da.where(
                    (da[latn] <= n) & (da[latn] >= s) & (da[lonn] >= w) & (da[lonn] <= e),
                    drop=True,
                )
            da.name = std_name
            return da
        except Exception as exc:
            print(f"[ERR] Failed to open dataset: {exc}")
            return None




#####

def plot_map(extent, title="Map"): # [west, east, south, north]
    """
    Plots a map with specified geographic extent.

    Parameters:
    - extent: list of float, specifying [west, east, south, north]
    - title: str, title of the map
    """
    # Create figure and axis for the map
    fig, ax = plt.subplots(subplot_kw={"projection": ccrs.PlateCarree()}, figsize=(3, 2))

    # Set the geographic extent
    ax.set_extent(extent) 
    
    # Add map features
    ax.coastlines()
    ax.add_feature(cfeature.BORDERS, linestyle=":")
    ax.add_feature(cfeature.LAND, edgecolor="black")
    ax.add_feature(cfeature.OCEAN, facecolor="lightblue")
    
    # Set title
    ax.set_title(title)
    
    # Show plot
    plt.tight_layout()
    plt.show()



