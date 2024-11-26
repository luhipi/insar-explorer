from qgis.core import QgsMapLayer


def checkVectorLayer(layer):
    """ check layer is a valid vector layer """

    if layer is None:
        message = '<span style="color:red;">Invalid Layer: Please select a valid layer.</span>'
        return False, message
    elif not layer.isValid():
        message = '<span style="color:red;">Invalid Layer: Please select a valid layer.</span>'
        return False, message
    elif not (layer.type() == QgsMapLayer.VectorLayer):
        message = '<span style="color:red;">Only vector layers supported: Please select a valid vector layer.</span>'
        return False, message
    elif not (layer.geometryType() == 0):
        message = '<span style="color:red;">Invalid Layer: Please select a valid point layer.</span>'
        return False, message
    else:
        return True, ""


def checkVectorLayerVelocity(layer):
    """ check layer is a valid vector with velocity """

    velocity_field_name_options = ['velocity', 'VEL']
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
    import re
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
        message = (f'<span style="color:red;">Invalid Layer: Please select a vector layer with valid timeseries fields,'
                   f'&nbsp;e.g., D20141201, D20220123, etc.')
        status = False

    return status, message
