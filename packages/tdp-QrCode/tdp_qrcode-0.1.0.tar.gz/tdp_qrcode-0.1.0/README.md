# TDP QR-CodeGenerator
Fully implements the TDP Structure.

```uv add tdp-QrCode``` or ```pip install tdp-QrCode```

Use ```mod.TdQrcode.ToxFile``` as refference to implement the external tox.

## Parameters
__Text:__ The text of the qrcode.

__Fieldsize:__ Currently has no effect.
__Bordersize:__ The width of the border of the qrcode.
__Version:__ The size and repetition.
__Errorcorrection:__ Level of errorcorrection,

## Inputs
__colorLookup:__ A ramp to define the black and white value.

## Outputs
__original_out:__ The top in the original, generated resolution.
__rescaled_top:__ The QRCode crispy rescaled to 256*256.