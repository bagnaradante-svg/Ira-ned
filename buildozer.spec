[app]
title = IRA NED
package.name = iraned
package.domain = org.iraned
source.dir = .
source.include_exts = py,png,jpg,kv
version = 0.2.0
requirements = python3,kivy,pyjnius,plyer
orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/icon.png
android.api = 35
android.minapi = 24
android.ndk = 28c
android.archs = arm64-v8a

# La revision de python-for-android incorpora la correccion oficial
# del error de ruedas Android "not a supported wheel" (#3366).
# Tambien conserva la solucion anterior para el entorno de pip (#3360).
p4a.branch = develop
p4a.commit = 5865575d81d53617784428ee29f57be2716311ea

# Solo responde dentro de la app. No requiere permiso directo de microfono,
# acceso a archivos ni control de otras aplicaciones.
# android.permissions =

[buildozer]
log_level = 2
warn_on_root = 1
