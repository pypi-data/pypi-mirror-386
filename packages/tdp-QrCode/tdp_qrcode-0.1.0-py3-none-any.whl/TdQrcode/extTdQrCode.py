'''Info Header Start
Name : extTdQrCode
Author : Wieland PlusPlusOne@AMB-ZEPH15
Saveorigin : Project.toe
Saveversion : 2023.12000
Info Header End'''

from qrcode import QRCode, constants
import io

class extTdQrCode:
	"""
	extTdQrCode description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		

	def Generate_QrCodeBytes(self, target):

		qr_maker = QRCode(
			border		= self.ownerComp.par.Bordersize.eval(),
			box_size	= self.ownerComp.par.Fieldsize.eval(),
			version		= self.ownerComp.par.Version.eval(),
			error_correction = getattr( constants, f"ERROR_CORRECT_{self.ownerComp.par.Errorcorrection.eval()}" ),
		)
		qr_maker.add_data( self.ownerComp.par.Text.eval() )
		qr_maker.make(fit=True)
		qr_image = qr_maker.make_image()

		byteIO = io.BytesIO()
		qr_image.save( byteIO, format = "PNG")
		
		return bytearray( byteIO.getvalue() )
