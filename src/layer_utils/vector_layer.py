import re
from datetime import datetime
import numpy as np
from qgis.core import QgsMapLayer, QgsFeature
from qgis.PyQt.QtCore import QVariant


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


def getVectorVelocityFieldName(layer):
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
    pattern_options = [r'^D(\d{8})$', r'(\d{8})$', r'^D_(\d{8})$']
    date_field_patterns = [re.compile(pattern) for pattern in pattern_options]

    count = 0
    message = ""

    status, message = checkVectorLayer(layer)
    if status is False:
        return status, message

    for field in layer.fields():
        match = [pattern.match(field.name()) for pattern in date_field_patterns]
        if any(match):
            count += 1

    if count > 0:
        status = True
    else:
        message = ('<span style="color:red;">Invalid Layer: Please select a vector or raster layer with valid '
                   'timeseries data.')
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
    Extract attributes with keys in the format 'DYYYYMMDD' or 'YYYYMMDD' and return a list of tuples with datetime and
    float value.
    :param attributes: Dictionary of feature attributes
    :return: List of tuples (datetime, float)
    """
    pattern_options = [r'^D(\d{8})$', r'(\d{8})$', r'^D_(\d{8})$']
    date_value_patterns = [re.compile(pattern) for pattern in pattern_options]
    date_value_list = []

    for key, value in attributes.items():
        match = [pattern.match(key) for pattern in date_value_patterns]
        if any(match):
            date_str = next(m.group(1) for m in match if m)
            date_obj = datetime.strptime(date_str, '%Y%m%d')

            # check if field value is NULL
            if isinstance(value, QVariant):
                if value.isNull():
                    value = np.nan

            date_value_list.append((date_obj, value))

    return np.array(date_value_list, dtype=object)


def getVectorFields(layer):
    """ get field names from vector layer"""
    fields = [field.name() for field in layer.fields()]
    return fields
