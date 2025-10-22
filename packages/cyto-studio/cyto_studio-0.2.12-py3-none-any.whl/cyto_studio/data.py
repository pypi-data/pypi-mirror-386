import random
import os
import xarray as xr
import colorsys
import vispy.color
import json
import psutil

try:
    from .utilities import parse_channel_input
except ImportError:
    from utilities import parse_channel_input

from napari.layers import Image
import gc
import numpy as np
import math
import SimpleITK as sitk
import pandas as pd
import cv2
from PySide2.QtCore import QTimer
from PySide2.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea,
                               QComboBox, QCheckBox, QListWidget, QListWidgetItem, QMessageBox, QFileDialog, QMainWindow)

class Data:
    def __init__(self):
        self.ds1 = None
        self.ds2 = None
        self.ds4 = None
        self.ds8 = None
        self.ds16 = None
        self.ds32 = None
        self.old_method = False
        self.spacing = None
        self.bscale = None
        self.bzero = None
        self.align_x = None
        self.align_y = None
        self.corrected_align_x = None
        self.corrected_align_y = None
        self.value_range = None
        self.optical_slices = None
        self.number_of_sections = None
        self.shape = None
        self.slice_spacing = None
        self.corrected_align_x = None
        self.corrected_align_y = None


        
    def Load2D(self, viewer, image_folder, comboBoxPath, selected_channels, default_contrast_limits, thresholdN, channels_start, axio, old_method, overall_brightness, scroll, scroll_overall_brightness):

        random.seed(42)
        
        color_number_offset = sum(isinstance(layer, Image) for layer in viewer.layers)
        print(f"color_number_offset {color_number_offset}")

        # Remove previous bounding box
        if any(i.name == 'bounding box' for i in viewer.layers):
            viewer.layers.remove('bounding box')

            
        file_name = image_folder + str(comboBoxPath) + '/mos'
        default_contrast_limits = [0,30000]
        thresholdN.setText("1000")
        channels_start = 0
        if not os.path.exists(file_name):
            file_name = image_folder + str(comboBoxPath) + '/mos.zarr'
            default_contrast_limits = [0,30]
            thresholdN.setText("0.3")
            channels_start = 1
        if not os.path.exists(file_name):
            file_name = image_folder + str(comboBoxPath) + '/'
            default_contrast_limits = [0,30000]
            thresholdN.setText("1000")
            channels_start = 0
            
        print(file_name)

        self.ds1 = xr.open_zarr(file_name)
        self.ds2 = xr.open_zarr(file_name, group='l.2')
        self.ds4 = xr.open_zarr(file_name, group='l.4')
        self.ds8 = xr.open_zarr(file_name, group='l.8')
        self.ds16 = xr.open_zarr(file_name, group='l.16')
        self.ds32 = xr.open_zarr(file_name, group='l.32')

        # Get number of sections
        if axio:
            number_of_sections = len(list(self.ds1))
            self.optical_slices_available = 1
            print(f"Number of sections1: {number_of_sections}")
        else:
            if old_method:
                number_of_sections = len(set(self.ds1.attrs['cube_reg']['slice']))
                print(f"Number of sections2: {number_of_sections}")
            else:
                try:
                    number_of_sections = int(json.loads(self.ds1.attrs['multiscale'])['metadata']['number_of_sections'])
                    print(f"Number of sections3: {number_of_sections}")
                except:
                    try:
                        number_of_sections = int(json.loads(self.ds1['S001'].attrs['raw_meta'])['sections'])
                        print(f"Number of sections4: {number_of_sections}")
                    except:
                        number_of_sections = len(list(self.ds1))
                        print(f"Number of sections5: {number_of_sections}")


            self.optical_slices_available = len(self.ds1.z)

        print(f"Number of sections: {number_of_sections}")
        print(f"optical slices available: {self.optical_slices_available}")


        channel_names = self.ds1.coords['channel'].values.tolist()
        channel_names = [str(name) if isinstance(name, int) else name for name in channel_names]
        print(f"channel_names: {channel_names}")



        scroll.setRange(1, (self.optical_slices_available*number_of_sections))
        optical_slice = 0
        scroll.setValue(1)
        z = 0
  
        if old_method:
            #Old method
            bscale = self.ds1.attrs['bscale']
            bzero = self.ds1.attrs['bzero']

            slice_names = self.ds1.attrs['cube_reg']['slice']

            scroll.setRange(1, len(slice_names))
            if z >= len(slice_names):
                z = len(slice_names)-1
                scroll.setValue(z)

            slice_name = slice_names[z]
        else:
            try:
                bscale = self.ds1['S001'].attrs['bscale']
                bzero = self.ds1['S001'].attrs['bzero']
            except:
                bscale = 1
                bzero = 0
            slice_name = f"S{(z+1):03d}"
                
        try:
            self.slice_names = list(self.ds1.keys())
            print(self.slice_names)
            slice_name = self.slice_names[z]
            
            try:
                bscale = self.ds1[slice_name].attrs['bscale']
                bzero = self.ds1[slice_name].attrs['bzero']
            except:
                pass
        except:
            pass

        print("slice_name: " + slice_name)
        
        # Read the image spacing
        if self.old_method:
            self.spacing = (self.ds1['S001'].attrs['scale'])
        else:
            self.spacing = [1,1]
            try:
                self.spacing[0] = float(json.loads(self.ds1.attrs['multiscale'])['metadata']['scale'][0])
                self.spacing[1] = float(json.loads(self.ds1.attrs['multiscale'])['metadata']['scale'][1])
            except:
                try:
                    self.spacing[0] = float(json.loads(self.ds1['S001'].attrs['scale'])["x"])
                    self.spacing[1] = float(json.loads(self.ds1['S001'].attrs['scale'])["y"])
                except:
                    print("spacing not defined")

        print(f"spacing: {self.spacing}")

        # Parse the selected channels
        #input_string = selected_slices
        #selected_channels = parse_channel_input(input_string)
        print("Selected channels:", selected_channels)

        number_of_channels = len(selected_channels)
        print("Number of channels:", number_of_channels)


        colors = []
        channel_names_used = []
        
        min_value = 65535
        max_value = -65535

        print(selected_channels)
        for chn in range(60):
            if chn in selected_channels:
                #print("loading")


                try:
                    im1 = (self.ds1[slice_name].sel(type='mosaic', z=optical_slice).data[chn] * bscale + bzero).squeeze()
                    im2 = (self.ds2[slice_name].sel(type='mosaic', z=optical_slice).data[chn] * bscale + bzero).squeeze()
                    im4 = (self.ds4[slice_name].sel(type='mosaic', z=optical_slice).data[chn] * bscale + bzero).squeeze()
                    im8 = (self.ds8[slice_name].sel(type='mosaic', z=optical_slice).data[chn] * bscale + bzero).squeeze()
                    im16 = (self.ds16[slice_name].sel(type='mosaic', z=optical_slice).data[chn] * bscale + bzero).squeeze()
                    im32 = (self.ds32[slice_name].sel(type='mosaic', z=optical_slice).data[chn] * bscale + bzero).squeeze()
                except:
                    try:
                        im1 = (self.ds1[slice_name].sel(z=optical_slice).data[chn] * bscale + bzero).squeeze()
                        im2 = (self.ds2[slice_name].sel(z=optical_slice).data[chn] * bscale + bzero).squeeze()
                        im4 = (self.ds4[slice_name].sel(z=optical_slice).data[chn] * bscale + bzero).squeeze()
                        im8 = (self.ds8[slice_name].sel(z=optical_slice).data[chn] * bscale + bzero).squeeze()
                        im16 = (self.ds16[slice_name].sel(z=optical_slice).data[chn] * bscale + bzero).squeeze()
                        im32 = (self.ds32[slice_name].sel(z=optical_slice).data[chn] * bscale + bzero).squeeze()
                    except:
                        try:
                            im1 = (self.ds1[slice_name].data[chn] * bscale + bzero).squeeze()
                            im2 = (self.ds2[slice_name].data[chn] * bscale + bzero).squeeze()
                            im4 = (self.ds4[slice_name].data[chn] * bscale + bzero).squeeze()
                            im8 = (self.ds8[slice_name].data[chn] * bscale + bzero).squeeze()
                            im16 = (self.ds16[slice_name].data[chn] * bscale + bzero).squeeze()
                            im32 = (self.ds32[slice_name].data[chn] * bscale + bzero).squeeze()
                        except:
                            print("skipping this channel since it can't be read")
                            continue


                if chn+color_number_offset == 0:
                    color_map = 'bop purple'
                    color_map_tuple = (128, 0, 128)  # Approximation for 'bop purple'
                elif chn+color_number_offset == 1:
                    color_map = 'red'
                    color_map_tuple = (255, 0, 0)  # Standard red
                elif chn+color_number_offset == 2:
                    color_map = 'green'
                    color_map_tuple = (0, 255, 0)  # Standard green
                elif chn+color_number_offset == 3:
                    color_map = 'blue'
                    color_map_tuple = (0, 0, 255)  # Standard blue
                elif chn+color_number_offset == 4:
                    color_map = 'yellow'
                    color_map_tuple = (255, 255, 0)  # Standard yellow
                elif chn+color_number_offset == 5:
                    color_map = 'magenta'
                    color_map_tuple = (255, 0, 255)  # Standard magenta
                elif chn+color_number_offset == 6:
                    color_map = 'cyan'
                    color_map_tuple = (0, 255, 255)  # Standard cyan
                elif chn+color_number_offset == 7:
                    color_map = 'bop orange'
                    color_map_tuple = (255, 165, 0)  # Approximation for 'bop orange', similar to standard web orange
                elif chn+color_number_offset == 8:
                    color_map='bop blue'
                    color_map_tuple = (31, 168, 241)
                else:
                    # Generate a random hue value between 0 and 1 (representing the entire spectrum)
                    random_hue = random.uniform(0, 1)

                    # Convert the hue value to an RGB color
                    rgb_color = colorsys.hsv_to_rgb(random_hue, 1, 1)

                    color_map = vispy.color.Colormap([[0.0, 0.0, 0.0], [rgb_color[0], rgb_color[1], rgb_color[2]]])
                    
                    color_map_tuple = tuple(int(c * 255) for c in rgb_color)
                    
                
                channel_name = str(channel_names[chn])
                
                
                colors.append(color_map_tuple)
                channel_names_used.append(channel_name)

                # if any(i.name == channel_name for i in viewer.layers):
                #     viewer.layers.remove(channel_name)


                min_value2 = im32.min().compute()
                #if min_value2 < 0:
                #    min_value2 = 0
                max_value2 = im32.max().compute()
                
                if min_value2 < min_value:
                    min_value = min_value2
                if max_value2 > max_value:
                    max_value = max_value2

                self.value_range = [min_value, max_value]
                
                self.overall_brightness = number_of_channels * (1.01 - (float(scroll_overall_brightness.value()) / 1000))
                contrast_limits = [self.value_range[0],self.value_range[1]*self.overall_brightness]

                
                
                if "IMC" in channel_name:
                    contrast_limits = [0,300*overall_brightness]
                elif "AXIO" in channel_name:
                    contrast_limits = [0,30000*overall_brightness]
                elif "STPT" in channel_name:
                    contrast_limits = [0,30000*overall_brightness]
                else:
                    contrast_limits = [0,30000*overall_brightness]

                layerC1 = viewer.add_image([im1, im2, im4, im8, im16, im32], multiscale=True,
                                      name=str(channel_name), blending='additive', colormap=color_map, contrast_limits=contrast_limits, scale=self.spacing)


        return self.optical_slices_available, self.value_range, number_of_sections, channel_names_used, colors
                
       

    def Align(self, volume, resolution, output_resolution, start_slice_number, current_spacing, sample_name):
        
        
        print("------------------------------------------------------------------------")
        print(f"spacing({self.spacing[0]}, {self.spacing[1]})")
        size_multiplier = (resolution*0.1*self.spacing[0])/output_resolution
        size = (volume.shape[0], int(size_multiplier*volume.shape[1]), int(size_multiplier*volume.shape[2]))
        aligned = np.zeros(size, dtype=np.float32)
        size2D = (int(size_multiplier*volume.shape[2]), int(size_multiplier*volume.shape[1]))

        z_size = volume.shape[0]
        
        for z in range(0, z_size):

            fixed = sitk.GetImageFromArray(volume[z, :, :])
            fixed.SetOrigin((0, 0))
            fixed.SetSpacing([resolution*0.1*current_spacing[1],resolution*0.1*current_spacing[0]])

            transform = sitk.Euler2DTransform()
            
            
            slice_name_stpt = f"S{(z+1):03d}"
            home_directory = os.path.expanduser('~')
            
            #file_path = home_directory + f"/Storage/imaxt/imaxt_reg.2023_v3/{sample_name}/{sample_name}_INT_STPT_STPT_all_reg.parquet"
            file_path = home_directory + f"/Storage/imaxt/imaxt_reg/{sample_name}/{sample_name}_INT_STPT_STPT_all_reg.parquet"
                        
            alignX = 0
            alignY = 0
            if False:
                if os.path.exists(file_path):
                    internal_df_stpt = pd.read_parquet(file_path, engine='pyarrow')
                    internal_filtered_df_stpt = internal_df_stpt[(internal_df_stpt['ranking'] == 1) & ((internal_df_stpt['FLAG'] == 1) | (internal_df_stpt['FLAG'] == 0))]
                    internal_row_stpt = internal_filtered_df_stpt[internal_filtered_df_stpt['S_S'] == slice_name_stpt]
                    M = np.array([[internal_row_stpt.iloc[0, 24], internal_row_stpt.iloc[0, 25], internal_row_stpt.iloc[0, 26]], [internal_row_stpt.iloc[0, 27], internal_row_stpt.iloc[0, 28], internal_row_stpt.iloc[0, 29]]])

                    #print(M)

                    #print(f"resolution*0.1*current_spacing[1] {0.1*current_spacing[1]}")
        #             align_pos = z + start_slice_number
        #             alignY = 0
        #             if not np.isnan(self.corrected_align_y[align_pos]):
        #                 alignY = -self.corrected_align_y[align_pos]*0.1*current_spacing[1]

        #             alignX = 0
        #             if not np.isnan(self.corrected_align_x[align_pos]):
        #                 alignX = -self.corrected_align_x[align_pos]*0.1*current_spacing[0]

                    alignX = -M[0, 2] * 0.1*current_spacing[0] # t_x
                    alignY = -M[1, 2] * 0.1*current_spacing[1]

            #print(f"alignX {alignX}")
            #print(f"alignY {alignY}")

            transform.SetTranslation([alignX, alignY])

            resampler = sitk.ResampleImageFilter()
            resampler.SetSize(size2D)
            resampler.SetOutputSpacing([output_resolution, output_resolution])
            resampler.SetOutputOrigin((0, 0))
            resampler.SetInterpolator(sitk.sitkLinear)
            resampler.SetDefaultPixelValue(0)
            resampler.SetTransform(transform)

            out = resampler.Execute(fixed)

            np_out = sitk.GetArrayFromImage(out)
            aligned[z, :, :] = np_out

        return aligned.astype(dtype=np.float32)

         
                
                
    def AlignAXIO(axio_volume, sample_name, slice_names, resolution, channel):

        sample_name = sample_name[:-5]

        new_volume = np.zeros(axio_volume.shape)

        # df = pd.read_parquet(f"/home/tristan/Shared/imaxt_reg/{sample_name}/{sample_name}_EXT_AXIO_STPT_all_reg.parquet", engine='pyarrow')
        df = pd.read_parquet(f"/storage/imaxt/imaxt_reg/{sample_name}/{sample_name}_EXT_AXIO_STPT_all_reg.parquet", engine='pyarrow')


        filtered_df = df[(df['ranking'] == 1) & ((df['FLAG'] == 1) | (df['FLAG'] == 0))]
        #filtered_df = df[(df['ranking'] == 1)]

        print(slice_names)

        axio_zoom = xr.open_zarr(f"/storage/processed.2022/axio/{sample_name}_Axio/mos", group='l.{0:d}'.format(resolution))

        for index, slice_name in enumerate(slice_names):

            row = filtered_df[filtered_df['D_S'] == slice_name]

            if not row.empty:

                axio_location = int(row.iloc[0, 4][1:]) - 1
                # print(row.iloc[0, 4])
                # print(axio_location)
                # print(row)
                # print(" ")

                axio_image = axio_zoom[slice_name].sel(channel=channel).data
                axio_image = axio_image.squeeze()

                #axio_image = axio_volume[index,:,:]

                #flip image
                if row.iloc[0, 8] == 0.0:
                    axio_image = axio_image[::-1,:]

                axio_image = np.asarray(axio_image)

                M = np.array([[row.iloc[0, 24], row.iloc[0, 25], row.iloc[0, 26]/resolution], [row.iloc[0, 27], row.iloc[0, 28], row.iloc[0, 29]/resolution]])
                # Expand the dimensions of M so that it can be multiplied by T.
                M = np.append(M, [[0, 0, 0]], axis=0)

                rows, cols = axio_image.shape
                affine_np_img = cv2.warpAffine(axio_image, M[:2,:], (cols, rows))
                if (axio_location < new_volume.shape[0]):
                    new_volume[axio_location,:,:] = affine_np_img


        return new_volume   
    
    
    
    
    
    
    
    
    

    def Load3D(self, viewer, image_folder, comboBoxPath, selected_channels, default_contrast_limits, thresholdN, channels_start, axio, old_method, overall_brightness, scroll, scroll_overall_brightness, pixel_size, m_slice_spacing, start_slice, end_slice, crop, crop_start_x, crop_end_x, crop_start_y, crop_end_y, origin_x, origin_y, use_mask):
        random.seed(42)
        
        color_number_offset = sum(isinstance(layer, Image) for layer in viewer.layers)
        print(f"color_number_offset {color_number_offset}")
        
        verbose = True

        # Clear memory
        gc.collect()

                  
        if verbose:
            print(f"folder location: " + image_folder)
            
        
        file_name = image_folder + str(comboBoxPath) + '/mos'
        default_contrast_limits = [0,30000]
        thresholdN.setText("1000")
        channels_start = 0
        if not os.path.exists(file_name):
            file_name = image_folder + str(comboBoxPath) + '/mos.zarr'
            default_contrast_limits = [0,30]
            thresholdN.setText("0.3")
            channels_start = 1

        # Try to read only the meta data using the consolidated flag as True
        # Currently not used
        try:
            self.ds1 = xr.open_zarr(file_name, consolidated=False)
            # print("not trying consolidated")
        except Exception:
            print("none-consolidated")
            self.ds1 = xr.open_zarr(file_name)
            
            
            
        channel_names = self.ds1.coords['channel'].values.tolist()
        if verbose:
            print(f"channel_names: {channel_names}")
        
        

        # Initialize spacing with default zeros
        self.spacing = [0, 0, 0]

        # Find available slice keys that start with 'S'
        available_slices = [key for key in self.ds1.data_vars.keys() if key.startswith("S")]

        if available_slices:
            # Sort the slices lexicographically to get the first one (or you can choose a different ordering)
            available_slices.sort()
            first_slice = available_slices[0]
            if verbose:
                print(f"Using first available slice: {first_slice}")
            try:
                scale_info = json.loads(self.ds1[first_slice].attrs['scale'])
                self.spacing[0] = float(scale_info["x"])
                self.spacing[1] = float(scale_info["y"])
                self.spacing[2] = float(scale_info["z"])
            except:
                try:
                    self.spacing = 0.1*(self.ds1[first_slice].attrs['scale'])
                except:
                    try:
                        self.spacing[0] = float(json.loads(self.ds1.attrs['multiscale'])['metadata']['scale'][0])
                        self.spacing[1] = float(json.loads(self.ds1.attrs['multiscale'])['metadata']['scale'][1])
                        self.spacing[2] = float(json.loads(self.ds1.attrs['multiscale'])['metadata']['scale'][2])
                    except:
                        print("No slice available; using default spacing.")
                        self.spacing = [1, 1, 1]
        else:
            print("No slice available; using default spacing.")
            self.spacing = [1, 1, 1]
            
            
            
        # Read the image spacing
        if self.old_method:
            self.spacing = (self.ds1['S001'].attrs['scale'])
        else:
            self.spacing = [1,1]
            try:
                self.spacing[0] = float(json.loads(self.ds1.attrs['multiscale'])['metadata']['scale'][0])
                self.spacing[1] = float(json.loads(self.ds1.attrs['multiscale'])['metadata']['scale'][1])
            except:
                try:
                    self.spacing[0] = float(json.loads(self.ds1['S001'].attrs['scale'])["x"])
                    self.spacing[1] = float(json.loads(self.ds1['S001'].attrs['scale'])["y"])
                except:
                    print("spacing not defined")

            
            
        if verbose:
            print(f"spacing ({self.spacing[0]}, {self.spacing[1]})")

        # Read the parameters to convert the voxel values (bscale and bzero)
        if self.old_method:
            self.bscale = self.ds1.attrs['bscale']
            self.bzero = self.ds1.attrs['bzero']
        else:
            try:
                self.bscale = self.ds1['S001'].attrs['bscale']
                self.bzero = self.ds1['S001'].attrs['bzero']
            except:
                self.bscale = 1
                self.bzero = 0

        if verbose:
            print(f"bscale {self.bscale}, bzero {self.bzero}")


        # Get number of sections
        if axio:
            self.number_of_sections = len(list(self.ds1))

        
        self.number_of_sections = len(list(self.ds1))
        if verbose:
            print(f"Number of sections: {self.number_of_sections}")
            

        # Read the translation values
        if self.old_method:
            self.align_x = self.ds1.attrs['cube_reg']['abs_dx']
            self.align_y = self.ds1.attrs['cube_reg']['abs_dy']
        else:
            self.align_x = []
            self.align_y = []

            for z in range(0, self.number_of_sections):
                # slice_name = f"S{(z+1):03d}"
                # self.align_x.append(self.ds1[slice_name].attrs['offsets']['x'])
                # self.align_y.append(self.ds1[slice_name].attrs['offsets']['y'])
                self.align_x.append(0)
                self.align_y.append(0)

        if verbose:
            print(f"align_x {self.align_x}")
            print(f"align_y {self.align_y}")
        

        # User defined output pixel size
        output_resolution = float(pixel_size)

        if verbose:
            print(f"output pixel size {output_resolution}")


        # Calculate at which resolution the image should be read based on the image spacing and output pixel size
        resolution = 32
        index = 5
        if (output_resolution / 0.5) < 32:
            resolution = 16
            index = 4
        if (output_resolution / 0.5) < 16:
            resolution = 8
            index = 3
        if (output_resolution / 0.5) < 8:
            resolution = 4
            index = 2
        if (output_resolution / 0.5) < 4:
            resolution = 2
            index = 1
        if (output_resolution / 0.5) < 2:
            resolution = 1
            index = 0

        if verbose:
            print(f"loading at resolution {resolution} with index {index}")
        
        try:
            gr = self.ds1.attrs["multiscale"]['datasets'][index]['path']
            ds = xr.open_zarr(file_name, group=gr)
        except:
            try:
                gr = json.loads(self.ds1.attrs["multiscale"])['datasets'][index]['path']
                ds = xr.open_zarr(file_name, group=gr)
            except:
                try:
                    ds = xr.open_zarr(file_name, group='l.{0:d}'.format(resolution))
                except:
                    print("could not read") 
                
        # Get the number of optical slices that are available
        if axio:
            self.optical_slices_available = 1
        else:
            self.optical_slices_available = len(ds.z)

        if verbose:
            print(f"optical slices available: {self.optical_slices_available}")
        
        # Slice spacing given by the user, which should be extracted from the file name
        self.slice_spacing = float(m_slice_spacing)

        # Get the optical slice spacing
        if self.old_method or axio:
            # assume that the optical slices do not overlap
            optical_section_spacing = self.slice_spacing / self.optical_slices_available
        else:
            try:
                optical_section_spacing = float(json.loads(self.ds1.attrs['multiscale'])['metadata']['optical_section_spacing'])
            except:
                try:
                    optical_section_spacing = float(json.loads(self.ds1['S001'].attrs['raw_meta'])['zres'])
                except:
                    print(f"Unknown optical slice thickness. Using default of 20um. Set manually if needed.")
                    optical_section_spacing = 20

        if verbose:
            print(f"optical_slices zres: {optical_section_spacing}")

        # Calculate how many optical slices to use
        if self.optical_slices_available > 1:
            expected_nr_of_slices = round(self.slice_spacing / optical_section_spacing)
            if self.optical_slices_available > expected_nr_of_slices:
                self.optical_slices = expected_nr_of_slices
            else:
                self.optical_slices = self.optical_slices_available
        else:
            self.optical_slices = 1


        # Get slice names
        if self.old_method:
            self.slice_names = self.ds1.attrs['cube_reg']['slice']
        else:
            self.slice_names = []
            for z in range(0, self.number_of_sections):
                slice_name = f"S{(z+1):03d}"
                for i in range(0, self.optical_slices):
                    self.slice_names.append(slice_name)
        
        if verbose:
            print(f"slice names: {self.slice_names}")


        if verbose:
            print(f"number of optical slices used: {self.optical_slices}")

        # Store the output resolution in which this volume was loaded
        self.current_output_resolution = float(pixel_size)

        # Define start slice
        if start_slice == "":
            start_slice_number = 0
            chop_bottom = 0
        else:
            start_slice_number = int(math.floor(float(start_slice)/float(self.optical_slices)))
            chop_bottom = int(start_slice) - (self.optical_slices * start_slice_number) 

        # Define end slice
        if end_slice == "":
            end_slice_number = self.number_of_sections-1
            chop_top = 0
        else:
            end_slice_number = int(math.floor(float(end_slice)/float(self.optical_slices)))
            chop_top = (self.optical_slices * (end_slice_number + 1) -1) - int(end_slice) 

        # Define number of slices
        number_of_slices = end_slice_number - start_slice_number + 1
        if verbose:
            print(f"number_of_slices {number_of_slices}")
            
            
        # Parse the selected channels
        # selected_channels = parse_channel_input(selected_slices)
        if verbose:
            print("Selected channels:", selected_channels)
            
        number_of_channels = len(selected_channels)
        if verbose:
            print("Number of channels:", number_of_channels)
            
        spacing_loaded = [float(self.slice_spacing)/float(self.optical_slices), output_resolution, output_resolution]
        
        # Extract directory and the parent folder name (one level above 'mos')
        file_dir = os.path.dirname(file_name)
        parent_folder = os.path.basename(file_dir)  # Get the folder name above 'mos'
        
        # print(file_dir)
        # print(parent_folder)

        # Construct the expected parquet file path
        parquet_file = os.path.join(file_dir, f"internal_reg/{parent_folder}_INT_STPT_STPT_all_reg.parquet")

        # Check if the parquet file exists
        use_registration = False
        if os.path.exists(parquet_file):
            print(f"Found registration file: {parquet_file}")
            df = pd.read_parquet(parquet_file, engine='pyarrow')
            use_registration = True  # Enable registration
            # print(df)
        else:
            print(f"Registration file not found: {parquet_file}")

        
        
        if start_slice == "":
            start_slice_number = 1
        else:
            start_slice_number = int(start_slice)
            
        if end_slice == "":
            end_slice_number = self.number_of_sections
        else:
            end_slice_number = int(end_slice)
             
        
        
        if crop:
            print(f"output_resolution: {output_resolution}")

            size_x = int(math.floor((crop_end_x - crop_start_x) / output_resolution))
            size_y = int(math.floor((crop_end_y - crop_start_y) / output_resolution))
            start_x = int(math.floor(crop_start_x / output_resolution))
            start_y = int(math.floor(crop_start_y / output_resolution))
            
            


        example_slice_name = self.slice_names[0]
        if example_slice_name not in ds:
            print(f"Can't find slice {example_slice_name} for memory estimate.")
        else:
            dummy_slice = ds[example_slice_name]
            shape_y = dummy_slice.sizes["y"]
            shape_x = dummy_slice.sizes["x"]

            bytes_per_voxel = 4  # float32
            voxels_in_one_slice = shape_y * shape_x
            estimated_slice_gb = (voxels_in_one_slice * bytes_per_voxel) / (1024 ** 3)

            print(f"[SINGLE SLICE MEMORY CHECK]")
            print(f"  Slice shape: {shape_y} x {shape_x}")
            print(f"  Estimated memory per slice: {estimated_slice_gb:.2f} GB")

            # Warn if a single slice is, say, > 5GB
            if estimated_slice_gb > 1:
                from PySide2.QtWidgets import QMessageBox
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("High Memory Warning")
                msg_box.setText(
                    f"⚠️ A single slice will use ~{estimated_slice_gb:.2f} GB of memory.\n"
                    "This could crash your system. Continue loading?"
                )

                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
                response = msg_box.exec_()

                # 🪄 This ensures the dialog is closed and UI is updated before proceeding
                QApplication.processEvents()

                if response == QMessageBox.Cancel:
                    print("User cancelled due to large single slice size.")
                    return None, None, None, None, None, None


                
        self._memory_warning_user_cancelled = False
        self._memory_warning_response_received = False
        for chn in range(60):
            if chn in selected_channels:
                if verbose:
                    print(f"loading channel {chn}")
                
                if False:
                    try:
                        volume_1_temp = (ds.sel(type='mosaic').to_array().data * self.bscale + self.bzero).astype(dtype=np.float32)
                        volume_1_temp = volume_1_temp[:,chn,:,:]
                    except Exception as e:
                        if verbose:
                            print("An error occurred:", str(e))
                        volume_1_temp = (ds.to_array().data * self.bscale + self.bzero).astype(dtype=np.float32)
                        volume_1_temp = volume_1_temp[:,chn,:,:]
                else:
                    slices = []
                    for section in range(start_slice_number,end_slice_number+1):
                    #for section in range(98,101):
                        for optical_slice in range(1,self.optical_slices+1):

                            slice_name = f"S{(section):03d}"
                            
                            if slice_name not in ds:
                                if verbose:
                                    print(f"Slice {slice_name} not found, skipping.")
                                continue
                            try:
                                slice_data = (ds[slice_name].sel(type='mosaic', z=optical_slice).data * self.bscale + self.bzero).squeeze()
                            except:
                                try:
                                    slice_data = (ds[slice_name].sel(z=optical_slice).data * self.bscale + self.bzero).squeeze()
                                except:
                                    try:
                                        slice_data = (ds[slice_name].data * self.bscale + self.bzero).squeeze()
                                    except:
                                        print("skipping this channel since it can't be read")
                                        continue      
                                       
                            
                            # print(f"slice_data.shape {slice_data.shape}")
                            #slice_data = slice_data[0]
                            #print(f"slice_data.shape {slice_data.shape}")
                                       
                            if slice_data.ndim == 4:
                                if axio:
                                    slice_data = slice_data[:,1,:,:]
                                else:
                                    slice_data = slice_data[0]
                                
                            if slice_data.ndim != 2:
                                slice_data = slice_data[chn]
                                
                            # print(f"slice_data.shape {slice_data.shape}")
                            
                            if use_registration:
                                
                                # Filter rows where 'S_S' matches the slice_name
                                matching_rows = df[df['S_S'] == slice_name]

                                # If at least one row matches, use the first match
                                if not matching_rows.empty:
                                    row = matching_rows.iloc[0]
                                    M_00 = row['M_00']
                                    M_01 = row['M_01']
                                    M_02 = row['M_02']
                                    M_10 = row['M_10']
                                    M_11 = row['M_11']
                                    M_12 = row['M_12']
                                else:
                                    # Handle the case where no rows match
                                    print(f"No matching row found for slice_name = {slice_name}")
                                    continue

                                # Create the 2x3 matrix:
                                M = np.array([[M_00, M_01, M_02],
                                              [M_10, M_11, M_12]], dtype=np.float32)

                                M_adj = M.copy()
                                M_adj[0, 2] = M_adj[0, 2] / resolution
                                M_adj[1, 2] = M_adj[1, 2] / resolution

                                rotation_rad = np.arctan2(M_10, M_00)
                                rotation_deg = np.degrees(rotation_rad)
                                translation = (M_02, M_12)
                                rows, cols = slice_data.shape
                                
                                try:
                                    slice_data = slice_data.compute()
                                except MemoryError:
                                    print("❌ MemoryError during Dask compute — image too large for memory.")
                                    return None, None, None, None, None, None
                                except Exception as e:
                                    print(f"❌ Exception during Dask compute: {e}")
                                    return None, None, None, None, None, None
                                
                                transformed_slice_data = cv2.warpAffine(slice_data, M_adj, (cols, rows), flags=cv2.INTER_LINEAR)
                                slice_data = transformed_slice_data


                            size_multiplier = (resolution*self.spacing[0])/output_resolution
                            size2D = (int(size_multiplier*slice_data.shape[1]), int(size_multiplier*slice_data.shape[0]))

                            fixed = sitk.GetImageFromArray(slice_data)
                            fixed.SetOrigin((0, 0))
                            fixed.SetSpacing([resolution*self.spacing[1],resolution*self.spacing[0]])

                            transform = sitk.Euler2DTransform()

                            resampler = sitk.ResampleImageFilter()
                            resampler.SetSize(size2D)
                            resampler.SetOutputSpacing([output_resolution, output_resolution])
                            resampler.SetOutputOrigin((0, 0))
                            resampler.SetInterpolator(sitk.sitkLinear)
                            resampler.SetDefaultPixelValue(0)
                            resampler.SetTransform(transform)

                            out = resampler.Execute(fixed)

                            resampled_slice = sitk.GetArrayFromImage(out)
                            
                            
                            
                            if use_mask:
                                mask_file_name = image_folder + str(comboBoxPath) + "/bead/mask/mask_" + slice_name + "_z" + str(optical_slice - 1) + ".npz"
                                if verbose:
                                    print(f"mask_file_name {mask_file_name}")

                                # Load the mask file if it exists
                                if os.path.exists(mask_file_name):
                                    try:
                                        with np.load(mask_file_name) as data:
                                            mask = data["arr_0"]  # most .npz single-array files store data as arr_0
                                    except Exception as e:
                                        print(f"Could not load mask {mask_file_name}: {e}")
                                        mask = None

                                    if mask is not None:
                                        # Rescale the mask to match resampled_slice dimensions using nearest neighbor
                                        mask_resized = cv2.resize(
                                            mask.astype(np.uint8), 
                                            (resampled_slice.shape[1], resampled_slice.shape[0]),  # width, height
                                            interpolation=cv2.INTER_NEAREST
                                        )

                                        # Apply the mask: set pixels outside the mask to 0
                                        resampled_slice[mask_resized == 0] = 0

                                else:
                                    if verbose:
                                        print(f"Mask file not found: {mask_file_name}")
                            
                            
                            
                            if crop:
                                resampled_slice = resampled_slice[int(start_x):int(start_x+size_x), int(start_y):int(start_y+size_y)]

                            slices.append(resampled_slice)
                            
                            if len(slices) == 1 and not self._memory_warning_user_cancelled:
                                first_slice_shape = slices[0].shape  # (Y, X)
                                bytes_per_voxel = 4  # float32

                                total_voxels = number_of_channels * number_of_slices * self.optical_slices * first_slice_shape[0] * first_slice_shape[1]
                                estimated_volume_size = total_voxels * bytes_per_voxel
                                estimated_volume_gb = estimated_volume_size / (1024 ** 3)

                                print("[MEMORY CHECK]")
                                print(f"  Slice shape: {first_slice_shape[0]} x {first_slice_shape[1]}")
                                print(f"  Channels: {number_of_channels}")
                                print(f"  Slices: {number_of_slices}")
                                print(f"  Optical slices per section: {self.optical_slices}")
                                print(f"  Estimated memory usage: {estimated_volume_gb:.2f} GB")

                                if estimated_volume_gb > 200:

                                    # Define flags to store response
                                    self._memory_warning_user_cancelled = False
                                    self._memory_warning_response_received = False

                                    def show_memory_warning_dialog():
                                        msg_box = QMessageBox()
                                        msg_box.setIcon(QMessageBox.Warning)
                                        msg_box.setWindowTitle("Memory Usage Warning")
                                        msg_box.setText(
                                            f"⚠️ Estimated memory usage is {estimated_volume_gb:.2f} GB.\n"
                                            f"This may be too large to handle reliably.\n\n"
                                            "Do you want to continue loading the volume?"
                                        )
                                        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
                                        response = msg_box.exec_()
                                        
                                        # 🪄 This ensures the dialog is closed and UI is updated before proceeding
                                        QApplication.processEvents()

                                        if response == QMessageBox.Cancel:
                                            self._memory_warning_user_cancelled = True
                                        self._memory_warning_response_received = True

                                    # Defer dialog to the Qt main thread
                                    QTimer.singleShot(0, show_memory_warning_dialog)

                                    # Wait until user responds
                                    while not self._memory_warning_response_received:
                                        QApplication.processEvents()

                                    if self._memory_warning_user_cancelled:
                                        print("User cancelled due to memory warning.")
                                        return None, None, None, None, None, None

                                self._memory_warning_user_cancelled = True  # Prevent repeated prompts

                    # Stack the 2D slices (each now with shape (Y, X)) into a 3D volume.
                    volume_1_temp = np.stack(slices, axis=0)
                    # print("Volume shape:", volume_1_temp.shape)

                self.shape = volume_1_temp.shape

                if verbose:
                    print(f"self.shape {self.shape}")

                if chn+color_number_offset==0:
                    color_map='bop purple'
                elif chn+color_number_offset==1:
                    color_map='red'
                elif chn+color_number_offset==2:
                    color_map='green'
                elif chn+color_number_offset==3:
                    color_map='blue'
                elif chn+color_number_offset==4:
                    color_map='yellow'
                elif chn+color_number_offset==5:
                    color_map='magenta'
                elif chn+color_number_offset==6:
                    color_map='cyan'
                elif chn+color_number_offset==7:
                    color_map='bop orange'
                elif chn+color_number_offset==8:
                    color_map='bop blue'
                elif chn+color_number_offset==9:
                    color_map='bop purple'
                else:
                    # Generate a random hue value between 0 and 1 (representing the entire spectrum)
                    random_hue = random.uniform(0, 1)

                    # Convert the hue value to an RGB color
                    rgb_color = colorsys.hsv_to_rgb(random_hue, 1, 1)

                    color_map= vispy.color.Colormap([[0.0, 0.0, 0.0], [rgb_color[0], rgb_color[1], rgb_color[2]]])

                channel_name = channel_names[chn]

                # if any(i.name == channel_name for i in viewer.layers):
                #     viewer.layers.remove(channel_name)
                    
                
                min_val = volume_1_temp.min()
                if hasattr(min_val, 'compute'):
                    min_value = float(min_val.compute())
                else:
                    min_value = float(min_val)

                if min_value < 0:
                    min_value = 0

                max_val = volume_1_temp.max()
                if hasattr(max_val, 'compute'):
                    max_value = float(max_val.compute())
                else:
                    max_value = float(max_val)
                
                self.value_range = [min_value, max_value]
                
                self.overall_brightness = number_of_channels * (1.01 - (float(scroll_overall_brightness.value()) / 1000))
                contrast_limits = [self.value_range[0],self.value_range[1]*self.overall_brightness]
                

                print(f"scale= {(float(self.slice_spacing)/float(self.optical_slices), output_resolution, output_resolution)}")

                viewer.add_image([volume_1_temp], name=channel_name, scale=(float(self.slice_spacing)/float(self.optical_slices), output_resolution, output_resolution), 
                                      blending='additive', colormap=color_map, contrast_limits=contrast_limits)

                self.shape = volume_1_temp.shape

        
        return self.optical_slices_available, self.value_range, self.shape, self.slice_spacing, self.optical_slices, output_resolution
    