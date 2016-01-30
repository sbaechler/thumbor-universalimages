# coding: utf-8

import logging
from collections import namedtuple

logger = logging.getLogger('universalimages.filters')

Area = namedtuple('Area', ['x0', 'y0', 'x1', 'y1'])
Point = namedtuple('Point', ['x', 'y'])


class Xmp_API(object):
    """
    XMP API for the RMD Standard in version 0.1.
    """

    def __init__(self, metadata=None):
        self.metadata = metadata

    def check_valid(self, image_size):
        """
        Checks, if the XMP data are valid for the current image.
        :param image_size: Size of the original image in physical pixels
        :type image_width: tuple: (int, int)
        :return: True if it is valid.
        :rtype: Boolean
        """
        if not 'Xmp.rmd.AppliedToDimensions' in self.metadata.xmp_keys:
            logger.debug('No RMD metadata found')
            return False

        # Check if the dimensions are valid
        width = int(self.metadata.get(b'Xmp.rmd.AppliedToDimensions/stDim:w').value)
        height = int(self.metadata.get(b'Xmp.rmd.AppliedToDimensions/stDim:h').value)

        if (width, height) != image_size:
            logger.debug('Metadata has been applied to a different image size.'
                         ' ({}x{}, but current image is {}x{}.)'.format(
                width, height, *image_size
            ))
            return False

        # everything OK
        return True

    def get_value_for(self, node):
        """
        Gets the value for the given simple type node
        :param node: The full path to the node.
        :type node: Basestring
        :return: The value of the node or None
        """
        if type(node) == unicode:
            node = node.encode('utf-8')
        if node not in self.metadata.xmp_keys:
            return None

        return self.metadata[node].value

    def get_area_values_for(self, node):
        """
        Gets the XMP values for the given Area Node.
        :param node: The full path to the node.
        :type node: Basestring
        :return: A dictionary with the filled in values or None if the node
                 does not exist.
        :rtype: dict or None
        """
        if node not in self.metadata.xmp_keys:
            return None

        node_keys = [n.encode('utf-8') for n in self.metadata.xmp_keys
                     if n.startswith(node) and n != node]
        values = dict((k.split(':')[-1], float(self.get_value_for(k)))
                      for k in node_keys)
        return values

    def get_area_values_for_array(self, node):
        """
        Gets the XMP values for nodes which are an array (RecommendedAreas)
        :param node: The full path tho the node without the Array selector
        :type node: Basestring
        :return: A list of dictionaries
        :rtype: list
        """
        if type(node) == unicode:
            node = node.encode('utf-8')
        i = 1
        result = []
        while True:
            test_node = b'%s[%i]' % (node, i)
            if test_node in self.metadata.xmp_keys:
                result.append(self.get_area_values_for(test_node))
                i += 1
            else:
                break
        return result

    def check_allowed(self):
        """
        Check, if cropping for art direction is allowed by the copyright holder.
        :rtype: Boolean
        """

        if 'Xmp.rmd.AllowedDerivates/rmd:Crop' in self.metadata.xmp_keys:
            crop_allowed =self.metadata.get(
                    b'Xmp.rmd.AllowedDerivates/rmd:Crop').value
            if crop_allowed not in ['visibilityOnly', 'all']:
                logger.debug('Allowed Derivates disallow cropping: %s'
                             % crop_allowed)
                return False
        return True

    def stArea_to_absolute(self, stArea_values, image_size):
        """
        Converts the relative stArea values to absolute coordinates.

        :param stArea_values: dictionary with CenterX, CenterY, Width, Height
        :type stArea_values: dict
        :param image_size: Tuple with the target size (width, height)
        :type image_size: tuple (int, int)
        :return: Named Tuple with the coordinates of the upper left and lower right
                 point (x0, y0, x1, y1) or x and y coordinates (x, y)
        :rtype: namedtuple (x:float, y:float) or (x0:float, y0:float, x1:float, y1:float)
        """
        if not stArea_values:
            return None

        area = 'w' in stArea_values

        if area:
            # Area
            source = (x, y, w, h) = (stArea_values['x'], stArea_values['y'],
                                     stArea_values['w'], stArea_values['h'])
        else:
            # Point
            source = (x, y) = (stArea_values['x'], stArea_values['y'])

        width, height = image_size

        for value in source:
            if 0 > value > 1:
                raise AttributeError('Invalid Area values.')

        if area:
            x0, y0 = (x - w/2.0) * width, (y - h/2.0) * height
            x1, y1 = (x + w/2.0) * width, (y + h/2.0) * height

            return Area(x0, y0, x1, y1)
        else:
            return Point(x * width, y * height)


    def get_absolute_area_for(self, node, image_size):
        """
        Shorthand property for the above methods.
        """
        return self.stArea_to_absolute(
                self.get_area_values_for(node), image_size)