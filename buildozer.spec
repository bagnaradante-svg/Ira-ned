[app]
title = IRA NED
package.name = iraned
package.domain = org.iraned
source.dir = .
source.include_exts = py,png,jpg,kv
version = 0.1.0
requirements = python3,kivy,pyjnius,plyer
orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/icon.png
android.api = 35
android.minapi = 24
android.ndk = 28c
android.archs = arm64-v8a

# Correccion publicada por los desarrolladores para el fallo
# "cannot import name BuildDependencyInstallError" al compilar.
p4a.branch = develop
p4a.commit = 0382d27de2f7315ed98e74884bafb30365decdee

# Solo responde dentro de la app. No requiere permiso directo de microfono,
# acceso a archivos ni control de otras aplicaciones.
# android.permissions =

[buildozer]
log_level = 2
warn_on_root = 1
