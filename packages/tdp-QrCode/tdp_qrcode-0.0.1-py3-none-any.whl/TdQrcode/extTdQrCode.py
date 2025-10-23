'''Info Header Start
Name : extTdQrCode
Author : Wieland PlusPlusOne@AMB-ZEPH15
Saveorigin : Project.toe
Saveversion : 2023.12000
Info Header End'''

import qrcode
import io

class extTdQrCode:
	"""
	extTdQrCode description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		

	def Generate_QrCodeBytes(self, target):
		qr_image = qrcode.make( 	target, 
									box_size = self.ownerComp.par.Fieldsize.eval(), 
									border = self.ownerComp.par.Bordersize.eval() 
								)
		byteIO = io.BytesIO()
		qr_image.save( byteIO, format = "PNG")
		return bytearray( byteIO.getvalue() )
