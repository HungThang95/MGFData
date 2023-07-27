import streamlit as st
import pandas as pd
import geopandas as gpd
import mercantile
import os
import fiona
from shapely.geometry import Polygon, shape
from pathlib import Path
from zipfile import ZipFile
import tempfile

## set up Layout
st.set_page_config(
     page_title="MICROSOFT OPEN GLOBAL FOOTPRINT DATA",
     layout="wide",
     initial_sidebar_state="expanded",)
prmsContainer = st.experimental_get_query_params()

## Def lưu file
def Save_Uploaded_File (Uploadedfile, save_folder):
    save_path = Path(save_folder,File.name)
    with open(save_path, mode='wb') as w:
            w.write(File.getbuffer())
    return
## Def tải file
def save_shapefile_with_bytesio(dataframe,directory):
    dataframe.to_file(f"{directory}/Footprint.shp",  driver='ESRI Shapefile')
    zipObj = ZipFile(f"{directory}/Footprint.zip", 'w')
    zipObj.write(f"{directory}/Footprint.shp",arcname = 'Footprint.shp')
    zipObj.write(f"{directory}/Footprint.cpg",arcname = 'Footprint.cpg')
    zipObj.write(f"{directory}/Footprint.dbf",arcname = 'Footprint.dbf')
    zipObj.write(f"{directory}/Footprint.prj",arcname = 'Footprint.prj')
    zipObj.write(f"{directory}/Footprint.shx",arcname = 'Footprint.shx')
    zipObj.close()
    
    
Main = st.container()

col1, col2 = st.columns((5,5))

Main.header("GET FOOTPRINT GLOBAL DATA FORM MICROSOFT OPEN SOURCE")

if len (prmsContainer) != 0:
    Files = prmsContainer['file'][0]
else:
    Files = col1.file_uploader("Import Research Boundary: ",accept_multiple_files=True)

if list (Files) == []: col1.write("Import Your Boundary (*.shp) !")
else:
    with tempfile.TemporaryDirectory() as tmp1: 
        if len(prmsContainer) == 0:
            for File in Files:
                Save_Uploaded_File(File, tmp1)
            Name = File.name[0:File.name.find(".")]
            End = File.name[File.name.find(".")+1:len(File.name)]
            geoFileName = Name + ".shp"
        else: geoFileName =  Files    
        geoFile = f"{tmp1}/{geoFileName}"
        
        Ranh =  gpd.read_file(geoFile)

        minx = Ranh.bounds.minx[0]
        miny = Ranh.bounds.miny[0]
        maxx = Ranh.bounds.maxx[0]
        maxy = Ranh.bounds.maxy[0]

        Ranhbuffer = gpd.GeoDataFrame(geometry = Ranh.geometry.buffer(0.001),crs="EPSG:4326")
        st.write("Boundary coordinates:", minx, miny, maxx, maxy)  

    
        if col2.button ("Get data"):
            quad_keys = set()
            
            for tile in list(mercantile.tiles(minx, miny, maxx, maxy, zooms=9)):
                quad_keys.add(int(mercantile.quadkey(tile)))
            quad_keys = list(quad_keys)
            dataset_links = pd.read_csv("https://raw.githubusercontent.com/HungThang95/MGFData/main/dataset-links.csv")
            links = dataset_links[dataset_links.QuadKey.isin (quad_keys)]

            geotemp = []
            for _, row in links.iterrows():
                df = pd.read_json(row.Url, lines=True)
                df['geometry'] = df['geometry'].apply(shape)
                gdf = gpd.GeoDataFrame(df, crs=4326)
                gdf1 = gpd.overlay(gdf,Ranhbuffer,how='intersection')
                
                for i in range(0,len(gdf1.geometry)):
                    newrow = gpd.GeoSeries([gdf1.loc[i].geometry])
                    if newrow.within(Ranh.geometry).values[0] == True:
                        geotemp.append(newrow.values[0])
                        
            CT = gpd.GeoDataFrame(geometry=geotemp, crs="EPSG:4326")
            col2.write(len(CT.geometry))
            col2.success('Success!!', icon="✅")
            with tempfile.TemporaryDirectory() as tmp:
                save_shapefile_with_bytesio(CT,tmp)
                with open(f"{tmp}/Footprint.zip", "rb") as file:
                    col2.download_button(
                        label="Download data",
                        data=file,
                        file_name='Footprint.zip',
                        mime='application/zip',
                    )
