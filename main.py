from flask import Flask
from flask_restful import Api, Resource
from flask_cors import CORS, cross_origin

import pandas as pd
import geopandas as gpd
import folium
import matplotlib
import mapclassify
import math

ages = [
    "https://kart.trondheim.kommune.no/levekar2020/personer0_17/2018.js",  # 8.5
    "https://kart.trondheim.kommune.no/levekar2020/personer18_34/2018.js",  # 26
    "https://kart.trondheim.kommune.no/levekar2020/personer35_66/2018.js",  # 50.5
    "https://kart.trondheim.kommune.no/levekar2020/personer67/2018.js",  # 83.5
]

# Instead use this we should maybe use "columnName" property of sheets
finalNames = ["Andel", "Antall", "Gjennomsnittspris"]  # , 'Konfidensintervall']

properties = {
    "Levekårsone-nummer": [],
    "Levekårsnavn": [],
    "Ages": [],
    "Price": [],
    "Nærmiljø": [],
    "geometry": []
}

# Values for distribution : quantity | proportion | average | median | quintiles

BEFOLKNING = "120UjUkUfX5is20D_SX3z99vfuCHOVuN8RI1yE3-L4OM"
BOLIGOGNÆRMILJØ = "1pU_p7FToI3VerocJXSp1-zMtWNk9SsKL_Tv7nImiXF8"
NÆRMILJØ = '1s51rcfCGPpjc1hx-6B7IqC6IfBjgSR2JAwOsW9ykI3U'

sheets = {
    "Ages": {
        "key": BEFOLKNING,
        "values": {
            "underage (0-17)": "1-10",
            "young adult (18-34)": "1-40",
            "adult (35-66)": "1-70",
            "senior (67+)": "1-100",
        },
        "distribution": "proportion",
        "inputForValues": "slider",
        "inputSelectionValues": None,
        "columnName": "Andel"
    },
    "Price": {
        "key": BOLIGOGNÆRMILJØ,
        "values": {
            "small": "2-220",
            "medium": "2-240",
            "large": "2-260",
        },
        "distribution": "average",
        "inputForValues": "slider",
        "inputSelectionValues": "checkbox",
        "columnName": "Gjennomsnittspris"
    },
    "Nærmiljø": {
        "key": NÆRMILJØ,
        "values": {
            "trivsel-kvinner": "10-10",
            "trivsel-menn": "10-20",
            "trygghet-kvinner": "10-30",
            "trygghet-menn": "10-40",
            "tilgjengelighet kultur-kvinner": "10-50",
            "tilgjengelighet kultur-menn": "10-60",
            "tilgjengelighet friluftsområder-kvinner": "10-90",
            "tilgjengelighet friluftsområder-menn": "10-100",
            "tilgjengelighet offentlig transport-kvinner": "10-110",
            "tilgjengelighet offentlig transport-menn": "10-120",
            "tilgjengelighet friluftsområder-kvinner": "10-90",
            "tilgjengelighet friluftsområder-menn": "10-100",
            "tilgjengelighet butikker-kvinner": "10-130",
            "tilgjengelighet butiker-menn": "10-140",
            "tilgjengelighet gang og sykkelvei-kvinner": "10-150",
            "tilgjengelighet gang og sykkelvei-menn": "10-160",
            "plaget av trafikk støy-kvinner": "10-170",
            "plaget av trafikk støy-menn": "10-180",
            "plaget av annen støy-kvinner": "10-190",
            "plaget av annen støy-menn": "10-200",

        },
        "distribution": "proportion",
        "inputForValues": "slider",
        "inputSelectionValues": None,
        "columnName": "Andel"
    },
}

converters = {
    'Andel': lambda s: percent_to_float(s),
    'Gjennomsnittspris': lambda s: string_to_int(s)
}


def percent_to_float(s: str) -> float:
    if s == "":
        return 0.0
    s = s.strip("%")
    s = s.replace(',', '.')
    return round(float(s) / 100, 2)


def string_to_int(s: str) -> int:
    res = s.replace("\xa0", '')
    if not res.isdigit(): return None
    return int(res)


def data_from_sheet(key: str, sheet: str, startColumn: chr, startLine: int, endColumn: chr, endLine: int,
                    names: list = None, converters: dict = None) -> pd.DataFrame:
    df = pd.read_csv('https://docs.google.com/spreadsheets/d/' +
                     key +
                     '/gviz/tq?tqx=out:csv&range=' + startColumn + str(startLine) + ':' + endColumn + str(endLine) +
                     '&sheet=' +
                     sheet,
                     names=names,
                     converters=converters
                     )
    df.columns = df.columns.str.replace('\n', '')
    return df


def add_properties(properties: dict, dataframe: pd.DataFrame, subject: str, subSubject: str,
                   finalNames: list = []) -> dict:
    """Add data from DataFrame to the argument `properties`, e.g.: properties.subject.subSubject

    A `properties` dictionary like this:
    properties = {
        "id": [],
        "name": [],
        "A_Subject": [],
        "geometry": []
    }

    A DataFrame like this:
    index |   id,   name,   average,   useless_data|
    -----------------------------------------------|
        0 | id_0, name_0, average_0, useless_data_0|
        1 | id_1, name_1, average_1, useless_data_1|
        2 | id_2, name_2, average_2, useless_data_2|
        3 | id_3, name_3, average_3, useless_data_3|

    Call the function like this: add_properties(properties, dataframe, "A_Subject", "A_Subsubject", ["average"] )

    Result:
    properties = {
        "id": [id_0, id_1, id_2, id_3],
        "name": [name_0, name_1, name_2, name_3],
        "A_Subject": [
            {
                "A_Subsubject": {"average": average_0}
            },
            {
                "A_Subsubject": {"average": average_1}
            },
            {
                "A_Subsubject": {"average": average_2}
            },
            {
                "A_Subsubject": {"average": average_3}
            }
        ],
        "geometry": []
    }

    Parameters
        ----------
        properties : dict
            Dictionary used for generate the GeoDataFrame, it contains all data and the `geometry` column
        dataframe : pandas.DataFrame
            Data to add to the `properties` dictionary
        subject : str
            Subject used as name of column (e.g. Befolkning)
        subSubject : str
            Subsbuject used to categorize subjects within a larger
        finalNames : list
            The final data to keep

    Return
        ---------
        A Dictionary fill with data
    """

    for columnName in dataframe:
        if columnName in properties.keys():
            if len(properties[columnName]) == 0: properties[columnName] = dataframe[columnName].to_list()
        elif len(finalNames) == 0 or columnName in finalNames:
            values = dataframe[columnName].to_list()
            for i in range(len(values)):
                if len(properties[subject]) <= i:
                    properties[subject].append({subSubject: {columnName: values[i]}})
                elif subSubject not in properties[subject][i].keys():
                    properties[subject][i][subSubject] = {columnName: values[i]}
                else:
                    properties[subject][i][subSubject][columnName] = values[i]
    return properties


def add_geometry_column(properties: dict, geodataframe: gpd.GeoDataFrame, idProperty: str = "Levekårsnavn",
                        idGeo: str = "levekårsone") -> dict:
    """Add data to `geometry` column

    Fill the `geometry` column of the `properties` dictionary with the geometry data of `geodataframe`.
    Use the `idProperty` and `idGeo` to match data and geometry

    A `properties` dictionary like this:
    properties = {
        "id": [id_0, id_1, id_2, id_3],
        "geometry": []
    }

    A GeoDataFrame like this:
    index | special_id, ...data...,   geometry|
    ------------------------------------------|
        0 |       id_0, ...data..., geometry_0|
        1 |       id_1, ...data..., geometry_1|
        2 |       id_2, ...data..., geometry_2|
        3 |       id_3, ...data..., geometry_3|

    Call the function like this: add_geometry_column(properties, geodataframe, "id", "special_id" )

    Result:
    properties = {
        "id": [id_0, id_1, id_2, id_3],
        "geometry": [geometry_0, geometry_1, geometry_2, geometry_3]
    }

    Parameters
        ----------
        properties : dict
            Dictionary used for generate the GeoDataFrame, it contains all data and the `geometry` column
        geodataframe : geopandas.GeoDataFrame
            GeoDataFrame with all data for the `geometry` column
        idProperty : str, optional
            The id column used in the `properties` dictionary
        idGeo : str, optional
            The id column used in the GeoDataFrame object
    Return
        ---------
        A Dictionary fill with geometry data
    """
    for name in properties[idProperty]:
        for j in range(len(geodataframe[idGeo])):
            if name == geodataframe[idGeo][j]:
                properties["geometry"].append(geodataframe["geometry"][j])
    return properties


def create_geojson_file(properties: dict, sheets: dict, geodataframe: gpd.GeoDataFrame, finalNames: list[str],
                        converters: dict) -> gpd.GeoDataFrame:
    for subject in sheets.keys():
        for subSubject, page in sheets[subject]["values"].items():
            dataframe = data_from_sheet(sheets[subject]["key"], page, 'A', 9, 'G', 69, converters=converters)
            properties = add_properties(properties, dataframe, subject, subSubject, finalNames)
    properties = add_geometry_column(properties, geodataframe)
    return gpd.GeoDataFrame(properties, crs="urn:ogc:def:crs:OGC:1.3:CRS84")


app = Flask(__name__)
api = Api(app)
CORS(app)


class HelloWorld(Resource):
    def get(self):
        age0_17 = gpd.read_file(ages[0])
        gdf = create_geojson_file(properties, sheets, age0_17, finalNames, converters)
        gdf.to_file("data2.geojson", driver='GeoJSON')
        return gdf.to_json()

    def post(self):
        return gpd.read_file('data2.geojson').to_json()


api.add_resource(HelloWorld, "/helloworld")
if __name__ == "__main__":
    print(gpd.read_file("data2.geojson"))
    app.run(debug=True)
