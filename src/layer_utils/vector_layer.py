import re
from datetime import datetime
import numpy as np
from qgis.core import QgsMapLayer, QgsFeature


def checkVectorLayer(layer):
    """ check layer is a valid vector layer """

    if layer is None:
        message = '<span style="color:red;">Invalid Layer: Please select a valid vector layer.</span>'
        return False, message
    elif not layer.isValid():
        message = '<span style="color:red;">Invalid Layer: Please select a valid vector layer.</span>'
        return False, message
    elif not (layer.type() == QgsMapLayer.VectorLayer):
        message = '<span style="color:red;">This is not a vector layer: Please select a valid vector layer.</span>'
        return False, message
    elif not (layer.geometryType() == 0):
        message = '<span style="color:red;">Invalid Layer: Please select a valid point layer.</span>'
        return False, message
    else:
        return True, ""


def checkVectorLayerVelocity(layer):
    """ check layer is a valid vector with velocity """

    velocity_field_name_options = ['velocity', 'VEL', 'mean_velocity']
    field_name = None
    message = ""
    for velocity_field in velocity_field_name_options:
        if layer.fields().lookupField(velocity_field) != -1:
            field_name = velocity_field
            break

    if field_name is None:
        joined_names = ',&nbsp;'.join(velocity_field_name_options)
        message = (f'<span style="color:red;">Invalid Layer: Please select a vector layer with valid velocity field.'
                   f'.&nbsp;Supported field names: [{joined_names}].</span>')

    return field_name, message


def checkVectorLayerTimeseries(layer):
    """ check layer is a valid vector with velocity """
    date_field_pattern = re.compile(r'^D\d{8}$')
    count = 0
    message = ""

    status, message = checkVectorLayer(layer)
    if status is False:
        return status, message

    for field in layer.fields():
        if date_field_pattern.match(field.name()):
            count += 1

    if count >0:
        status = True
    else:
        message = (f'<span style="color:red;">Invalid Layer: Please select a vector or raster layer with valid timeseries data.')
        status = False

    return status, message


def getFeatureAttributes(feature: QgsFeature) -> dict:
    """
    Get the attributes of a feature as a dictionary.
    :param feature: QgsFeature
    :return: Dictionary of feature attributes
    """
    return {field.name(): feature[field.name()] for field in feature.fields()}


def extractDateValueAttributes(attributes: dict) -> list:
    """
    Extract attributes with keys in the format 'DYYYYMMDD' and return a list of tuples with datetime and float value.
    :param attributes: Dictionary of feature attributes
    :return: List of tuples (datetime, float)
    """
    date_value_pattern = re.compile(r'^D(\d{8})$')
    date_value_list = []

    for key, value in attributes.items():
        match = date_value_pattern.match(key)
        if match:
            date_str = match.group(1)
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            date_value_list.append((date_obj, float(value)))

    return np.array(date_value_list, dtype=object)