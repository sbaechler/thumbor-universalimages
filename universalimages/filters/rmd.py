# coding: utf-8
from __future__ import unicode_literals, absolute_import

import logging

from thumbor.filters import BaseFilter, filter_method, PHASE_AFTER_LOAD

logger = logging.getLogger(__name__)


class Filter(BaseFilter):
    """
    This filter crops images according to the rules defined in the XMP metadata.
    https://github.com/universalimages/rmd
    """
    MIN_DPR = 0.5
    MAX_DPR = 4.0
    MIN_DOWNLINK = 1.0  # mbit/s
    phase = PHASE_AFTER_LOAD

    def _check_valid(self):
        metadata = self.engine.metadata
        if not metadata:
            logger.debug('No metadata found. Skipping RMD filter.')
            return False

        if not 'Xmp.rmd.AppliedToDimensions' in metadata.xmp_keys:
            logger.debug('No RMD metadata found')
            return False

        # Check if the dimensions are valid
        width = int(metadata.get(b'Xmp.rmd.AppliedToDimensions/stDim:w').value)
        height = int(metadata.get(b'Xmp.rmd.AppliedToDimensions/stDim:h').value)

        if (width, height) != self.engine.size:
            logger.debug('Metadata has been applied to a different image size.'
                         ' ({}x{}, but current image is {}x{}.)'.format(
                width, height, *self.engine.size
            ))
            return False

        # everything OK
        return True

    def _get_dpr(self, initial_dpr):
        # Returns the display resolution factor.
        request = self.context.request
        dpr = 1.0

        # Check if the dpr was sent with HTTP Client Hints
        header_dpr = request.headers.get('Dpr')
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
        header_downlink = request.headers.get('Downlink')
        if header_downlink and float(header_downlink) < self.MIN_DOWNLINK:
            dpr = min(dpr, 1.0)

        return dpr

    def _check_allowed(self):
        metadata = self.engine.metadata

        if 'Xmp.rmd.AllowedDerivates/rmd:Crop' in metadata.xmp_keys:
            crop_allowed = metadata.get(
                    b'Xmp.rmd.AllowedDerivates/rmd:Crop').value
            if crop_allowed not in ['visibilityOnly', 'all']:
                logger.debug('Allowed Derivates disallow cropping: %s'
                             % crop_allowed)
                return False
        return True


    @filter_method(BaseFilter.DecimalNumber)
    def rmd(self, initial_dpr=None):
        """
        Main filter method. Sets the crop values in the request.
        :param initial_dpr: display resolution of the target device,
                    relative to the CSS pixel.
        :type initial_dpr: float
        """
        logger.debug('RMD Filter called')

        if not self._check_valid():
            return

        if not self._check_allowed():
            return

        dpr = self._get_dpr(initial_dpr)


