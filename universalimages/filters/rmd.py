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
        target_aspect = float(target_width) / target_height
        interpolation = self.xmp.get_value_for(b'Xmp.rmd.Interpolation') or 'step'
        source_aspect = self.engine.size[1] / self.engine.size[0]

        # Get the pivot point
        pivot_point = self._get_pivot_point()
        # Check if a CropArea is defined:
        crop_area = self.xmp.get_area_values_for(b'Xmp.rmd.CropArea')
        crop_area_aspect_ratio = source_aspect
        if crop_area:
            crop, should_crop, commit, crop_area_aspect_ratio = self._process_crop_area(
                crop_area=crop_area, context=self.context,
                target_width=target_width, target_height=target_height)
            if commit:
                logger.debug('Crop Area is defined and final.')
                return self._commit(crop, should_crop)

            target_width, target_height = \
                self.context.transformer.get_target_dimensions()

        # Check if responsive Cropping is allowed
        if not self.xmp.check_allowed():
            self.context.request.fit_in = True
            logger.debug('Responsive Cropping is not allowed.')
            return self._commit(crop, False)

        # If no MinWidth is defined, check for a Safety Area. Use the CropArea
        # as the new reference width for the linear algorithm


        # If crop_min_width is none, then just check the recommended
        # and the safety areas.

        # Check if the requested size is larger than the safety area
        safe_area = self.xmp.get_area_values_for(b'Xmp.rmd.SafeArea')
        safe_area_absolute = None

        if safe_area:
            crop, should_crop, commit, safe_area_absolute = self._process_safe_area(
                crop, should_crop, safe_area, target_width, target_height, pivot_point)
            if commit:
                logger.debug('Image is smaller than the safe area.')
                return self._commit(crop, should_crop)

        # Look for the ideal region.

        if interpolation == 'linear':
            logger.debug('2-dimensional crop with linear interpolation')
            # Calculate if cropping is needed
            crop_min_width = int(crop_area.get('MinWidth')) if crop_area else None
            safe_max_width = int(safe_area.get('MaxWidth')) if safe_area else None
            if not (crop_min_width and safe_max_width):
                return crop, False, True

            crop_min_height = crop_min_width / crop_area_aspect_ratio
            x0, y0, x1, y1 = crop

            if target_height > crop_min_height:
                crop_height = y1 - y0
                crop_width = crop_height * target_aspect
            else:
                crop_width = (float(x1 - x0) / crop_min_width) * target_width
                crop_height = crop_width / target_aspect

            x_ratio = float(pivot_point.x - x0) / (x1 - pivot_point.x)
            y_ratio = float(pivot_point.y - y0) / (y1 - pivot_point.y)
            # b = relative distance from the the pivot point to the right crop.
            # This is more stable than calculating the left crop.

            b = crop_width / (1.0 + x_ratio)
            right = pivot_point.x + b
            left = right - crop_width

            # b = relative distance from the the pivot point to the bottom crop.

            b = crop_height / (1.0 + y_ratio)
            bottom = pivot_point.y + b
            top = bottom - crop_height

            # Check if the safe area is hit
            if safe_area_absolute:
                # TODO: Check if this is even possible
                if safe_area_absolute.x0 < left:
                    left = safe_area_absolute.x0
                    right = left + crop_width
                elif safe_area_absolute.x1 > right:
                    right = safe_area_absolute.x1
                    left = right - crop_width
                if safe_area_absolute.y0 < top:
                    top = safe_area_absolute.y0
                    bottom = top + crop_height
                elif safe_area_absolute.y1 > bottom:
                    bottom = safe_area_absolute.y1
                    top = bottom - crop_height

            crop = left, top, right, bottom

            # calculate new crop area

            pass
        else:
            # find recommended crop

            # check aspect ratio
            pass





        return self._commit(crop, should_crop)

    # Private methods

    def _commit(self, crop, should_crop):
        # Set the values and exit.
        self.context.request.crop = {
            'left': int(round(crop[0])),
            'top': int(round(crop[1])),
            'right': int(round(crop[2])),
            'bottom': int(round(crop[3]))
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
        crop_area_aspect = float(x1-x0) / float(y1-y0)

        # If only one dimension was passed in the request, then the aspect
        # ratio has to be adjusted for the crop area.
        if context.request.width and not context.request.height:
            if context.request.width == 'orig':
                context.transformer.target_height = target_height = int(
                        round(self.engine.size[0] / crop_area_aspect))
            else:
                context.transformer.target_height = target_height = int(
                        round(float(context.request.width) / crop_area_aspect))
        elif context.request.height and not context.request.width:
            if context.request.height == 'orig':
                context.transformer.target_width = target_width = int(
                    round(self.engine.size[1] * crop_area_aspect ))
            else:
                context.transformer.target_width = target_width = int(
                    round(float(context.request.height * crop_area_aspect)))
        elif not context.request.height and not context.request.width:
            context.transformer.target_width = target_width = x1 - x0
            context.transformer.target_height = target_height = y1 - y0

        if 'MinWidth' in crop_area:
            #  Check if the desired crop is larger than the min width.
            #  In this case, crop no further.
            if int(crop_area['MinWidth']) <= target_width:
                # Check if Cropping for layout purposes is allowed:
                if self.xmp.get_value_for(b'Xmp.rmd.AllowedDerivates/rmd:Crop') != 'all':
                    context.request.fit_in = True
                    return crop, should_crop, True, crop_area_aspect

                # Check if the new image size needs to be cropped further
                if target_height == int(round(float(target_width) / crop_area_aspect)):
                    # Aspect ratios match
                    return crop, should_crop, True, crop_area_aspect

        return crop, should_crop, False, crop_area_aspect

    def _process_safe_area(self, crop, should_crop, safe_area,
                           target_width, target_height, pivot_point):
        target_aspect_ratio = float(target_width) / target_height
        for key in ['x', 'y', 'w', 'h', 'MaxWidth']:
            if not key in safe_area:
                logger.debug('Safe Area Node is not valid. Skipping.')
                return crop, should_crop, False, None

        safe_max_width = int(safe_area.get('MaxWidth')) if safe_area else None
        x0, y0, x1, y1 = safe_area_absolute = self.xmp.stArea_to_absolute(
            safe_area, self.engine.size)
        safe_width = x1 - x0
        safe_height = y1 - y0
        safe_aspect_ratio = float(safe_width) / float(safe_height)

        if target_width <= safe_max_width:
            # Very small target. Smaller or equal to the safety area.
            should_crop = True
            # if target height (dp) >= safe area height (dp), normalized to target width
            if target_height >= (target_width / safe_aspect_ratio) or target_width < safe_width:

                # use the target aspect ratio and safety width
                crop_height = safe_width / target_aspect_ratio
                y_ratio = float(pivot_point.y - crop.y0) / (crop.y1 - pivot_point.y)
                b = crop_height / (y_ratio + 1)
                bottom = pivot_point.y + b
                top = bottom - crop_height

                # Check if the safe area is protected:
                if bottom < y1:
                    top = y0
                    bottom = top + crop_height
                elif top > y0:
                    bottom = y1
                    top = bottom - crop_height

                crop = x0, top, x1, bottom

            else:
                #  Widen the crop area to use the full safety height.
                crop_width = safe_height * target_aspect_ratio
                x_ratio = float(pivot_point.x - crop.x0) / (crop.x1 - pivot_point.x)

                b = crop_width / (1.0 + x_ratio)
                right = pivot_point.x + b
                left = right - crop_width

                if right < x1:
                    left = x0
                    right = left + crop_width
                elif left > x0:
                    right = x1
                    left = right - crop_width

                crop = left, y0, right, y1

            return crop, should_crop, True, None

        return crop, should_crop, False, safe_area_absolute

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

