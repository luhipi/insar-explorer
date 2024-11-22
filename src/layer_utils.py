from qgis.core import QgsMapLayer


def checkVectorLayer(layer):
    """ check layer is a valid vector layer """

    if not (layer and layer.isValid()):
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

