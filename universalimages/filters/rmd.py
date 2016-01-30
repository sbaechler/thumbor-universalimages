# coding: utf-8
from __future__ import unicode_literals, absolute_import

import logging

from thumbor.filters import BaseFilter, filter_method, PHASE_AFTER_LOAD
from .xmp.v01 import Xmp_API   # Good enough for now.

logger = logging.getLogger('universalimages.filters')


class Filter(BaseFilter):
    """
    This filter crops images according to the rules defined in the XMP metadata.
    https://github.com/universalimages/rmd

    It sets the request.crop, request.should_crop and smart properties
    in the context.

    Once the crop values are set, the image is then cropped and resized by Thumbor.
    """

    phase = PHASE_AFTER_LOAD
    MIN_DPR = 0.5
    MAX_DPR = 4.0
    MIN_DOWNLINK = 1.0  # mbit/s

    def __init__(self, params, context=None):
        super(Filter, self).__init__(params, context)
        # TODO: Extract RMD version and import the correct API.
        self.xmp = Xmp_API()

    @filter_method()
    def rmd(self):
        """
        Main filter method. Sets the crop values in the request.
        :param initial_dpr: display resolution of the target device,
                    relative to the CSS pixel.
        :type initial_dpr: float
        """
        logger.debug('RMD Filter called')
        if not self.engine.metadata:
            logger.debug('No metadata found. Skipping RMD filter.')
            return False

        self.xmp.metadata = self.engine.metadata

        # check for rmd namespace

        if not self.xmp.check_valid(self.engine.size):
            logger.debug('XMP Data is invalid')
            return

        # initialize values
        min_area = None  #  x0, y0, x1, y1
        crop = (0, 0) + self.engine.size  #  x0, y0, x1, y1
        should_crop = False

        # target size is in display independent pixels
        target_width, target_height = \
            self.context.transformer.get_target_dimensions()
        interpolation = self.xmp.get_value_for(b'Xmp.rmd.Interpolation') or 'step'
        source_aspect = self.engine.size[1] / self.engine.size[0]

        # Get the pivot point
        pivot_point = self._get_pivot_point()
        # Check if a CropArea is defined:
        crop_area = self.xmp.get_area_values_for(b'Xmp.rmd.CropArea')
        if crop_area:
            crop, should_crop, commit = self._process_crop_area(
                crop_area=crop_area, context=self.context,
                target_width=target_width, target_height=target_height)
            if commit:
                logger.debug('Crop Area is defined and final.')
                return self._commit(crop, should_crop)

            # If no MinWidth is defined, check for a Safety Area. Use the CropArea
            # as the new reference width for the linear algorithm
            target_width, target_height = \
                self.context.transformer.get_target_dimensions()


        # Check if responsive Cropping is allowed
        if not self.xmp.check_allowed():
            self.context.request.fit_in = True
            logger.debug('Responsive Cropping is not allowed.')
            return self._commit(crop, False)

        # Calculate if cropping is needed
        crop_min_width = int(crop_area.get('MinWidth')) if crop_area else None

        # If crop_min_width is none, then just check the recommended
        # and the safety areas.



        # Check if the requested size is larger than the safety area
        safe_area = self.xmp.get_area_values_for(b'Xmp.rmd.SafeArea')

        if safe_area:
            target_aspect_ratio = float(target_width) / target_height
            for key in ['x', 'y', 'w', 'h', 'MaxWidth']:
                if not key in safe_area:
                    logger.debug('Safe Area Node is not valid. Skipping.')
                    return (0, 0) + self.engine.size, False, False

            safe_max_width = int(safe_area.get('MaxWidth')) if safe_area else None
            x0, y0, x1, y1 = self.xmp.stArea_to_absolute(
                safe_area, self.engine.size)
            safe_width = x1 - x0
            safe_height = y1 - y0
            safe_aspect_ratio = float(safe_width) / float(safe_height)
            if not pivot_point:
                # Use the center of the safe area
                pivot_point = x0 + safe_width / 2.0, y0 + safe_height / 2.0

            if target_width <= safe_max_width:
                # Very small target. Smaller or equal to the safety area.
                should_crop = True

                # if target height (dp) >= safe area height (dp), normalized to target width
                if target_height >= (target_width / safe_aspect_ratio) or target_width < safe_width:
                    # use the target aspect ratio and safety width
                    old_height = float(safe_height)
                    safe_height = safe_width / target_aspect_ratio
                    lower = (safe_height - old_height) * ((pivot_point[1]-y0) / old_height)
                    upper = safe_height - old_height - lower
                    crop = x0, y0 - upper, x1, y1 + lower

                else:
                    #  Widen the crop area to use the full safety height.
                    old_width = float(safe_width)
                    safe_width = safe_height * target_aspect_ratio
                    left = (safe_width - old_width) * ((pivot_point[0]-x0) / old_width)
                    right = safe_width - old_width - left
                    crop = x0 - left, y0, x1 + right, y1

        # Look for the ideal region.
        return self._commit(crop, should_crop)

    # Private methods

    def _commit(self, crop, should_crop):
        # Set the values and exit.
        self.context.request.crop = {
            'left': crop[0],
            'top': crop[1],
            'right': crop[2],
            'bottom': crop[3]
        }
        self.context.request.should_crop = should_crop
        return True

    def _get_pivot_point(self):
        # Get the pivot point from the XML
        pivot_point = self.xmp.get_absolute_area_for(b'Xmp.rmd.PivotPoint',
                                                     self.engine.size)
        if pivot_point[0] is None:
            # Use the center of the safe area
            x0, x1, y0, y1 = self.xmp.get_absolute_area_for(b'Xmp.rmd.SafeArea',
                                                     self.engine.size)
            try:
                pivot_point = (x0 + (x1 - x0) / 2.0, y0 + (y1 - y0) / 2.0)
            except TypeError:
                # Use the image center
                pivot_point = (self.engine.size[0] / 2.0, self.engine_size[1] / 2.0)

        return pivot_point

    def _process_crop_area(self, crop_area, context, target_width, target_height):
        for key in ['x', 'y', 'w', 'h']:
            if not key in crop_area:
                return (0, 0) + self.engine.size, False, False

        x0, y0, x1, y1 = crop = self.xmp.stArea_to_absolute(
                crop_area, self.engine.size)
        should_crop = True
        source_aspect = float(x1-x0) / float(y1-y0)

        # If only one dimension was passed in the request, then the aspect
        # ratio has to be adjusted for the crop area.
        if context.request.width and not context.request.height:
            if context.request.width == 'orig':
                context.transformer.target_height = int(
                        round(self.engine.size[0] / source_aspect))
            else:
                context.transformer.target_height = int(
                        round(float(context.request.width) / source_aspect))
        elif context.request.height and not context.request.width:
            if context.request.height == 'orig':
                context.transformer.target_width = int(
                    round(self.engine.size[1] * source_aspect ))
            else:
                context.transformer.target_width = int(
                    round(float(context.request.height * source_aspect)))
        elif not context.request.height and not context.request.width:
            context.transformer.target_width = x1 - x0
            context.transformer.target_height = y1 - y0

        if 'MinWidth' in crop_area:
            #  Check if the desired crop is larger than the min width.
            #  In this case, crop no further.
            if int(crop_area['MinWidth']) <= target_width:
                # Check if Cropping for layout purposes is allowed:
                if self.xmp.get_value_for(b'Xmp.rmd.AllowedDerivates/rmd:Crop') != 'all':
                    context.request.fit_in = True
                    return crop, should_crop, True

                # Check if the new image size needs to be cropped further
                if target_height == int(round(float(target_width) / source_aspect)):
                    # Aspect ratios match
                    return crop, should_crop, True

        return crop, should_crop, False


    def _get_dpr(self, initial_dpr, request_headers):
        """
        Returns the display resolution factor. The passed in values override
        the client hint values. A slow connection reduces the dpr to a minimum.
        :param initial_dpr: values from the URL
        :type initial_dpr: float
        :param request_headers: HTTP Request Headers
        :type request_headers: dict
        :return: Calculated values
        :rtype: float
        """
        dpr = 1.0

        # Check if the dpr was sent with HTTP Client Hints
        header_dpr = request_headers.get('Dpr')
        if header_dpr is not None:
            logger.debug('Dpr in header found. Using this value: %s'
                         % header_dpr)
            dpr = float(header_dpr)

        # args can override Headers
        if initial_dpr:
            if self.MIN_DPR <= initial_dpr <= self.MAX_DPR:
                dpr = initial_dpr
            else:
                logger.debug('Illegal dpr value: %s' % initial_dpr)

        # Check if the downlink speed is fast enough for retina images
        header_downlink = request_headers.get('Downlink')
        if header_downlink and float(header_downlink) < self.MIN_DOWNLINK:
            dpr = min(dpr, 1.0)

        return dpr

