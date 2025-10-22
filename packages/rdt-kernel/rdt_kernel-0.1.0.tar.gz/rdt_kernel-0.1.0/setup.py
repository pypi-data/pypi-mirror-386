from setuptools import setup
setup(
    name="rdt-kernel",
    py_modules=["rdt_kernel"],
    version="0.1.0",  # ⬅️ must match the version above
    description="Recursive-Depth Logarithmic Dissipation Kernel",
    author="Steven Reid",
    license="MIT",
    install_requires=["numpy>=1.24"],
)
