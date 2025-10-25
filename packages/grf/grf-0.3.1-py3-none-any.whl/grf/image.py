import numpy as np
from PIL import Image


class LayeredImage:
	def __init__(self, rgb=None, alpha=None, mask=None):
		if isinstance(rgb, Image):
			assert alpha is None
			assert mask is None
			img = rgb
	        npimg = np.asarray(img)
	        if img.mode == 'P':
	            rgb = alpha = None
	            mask = npimg
	            self._is_rgba_image = False
	        elif img.mode == 'RGB':
	            rgb = npimg
	            alpha = mask = None
	            self._is_rgba_image = False
	        else:
	            if img.mode != 'RGBA':
	                img = img.convert('RGBA')
	            rgb = npimg[:, :, :3]
	            alpha = npimg[:, :, 3]
	            mask = None
	            self._is_rgba_image = True
	        self.w, self.h = img.size
		else:
			assert rgb or alpha or mask is not None
			self._rgb = rgb
			self._mask = mask
			self._alpha = alpha
			self._is_rgba_image = False
			self.h, self.w = (rgb or alpha or mask).shape
		# self._has_layers = False

	@property
	def mask(self):
		self._make_layers()
		return self._mask

	@property
	def rgb(self):
		self._make_layers()
		return self._rgb

	@property
	def alpha(self):
		self._make_layers()
		return self.alpha

	# def _make_layers(self):
	# 	if self._has_layers:
	# 		return

