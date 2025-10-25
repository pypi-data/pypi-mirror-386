pypi-AgEIcHlwaS5vcmcCJGFhYTk0MWNlLTVkN2QtNDI4MC05ZWM4LWFmNTFjYmM1YTkyNAACKlszLCI2Njg5Y2Y0MC0xODY1LTQxNDgtODAxZC0yNzQwYWMyMWVkNmEiXQAABiAlX5K37l1ujpn8vto1fr-PknJmxABGulXbyzTJHm8cJA


## Build sdist + wheel:

python -m build

## Clean any previous build artifacts:

rm -rf build dist *.egg-info

## Check built metadata / long description:

python -m twine check dist/*

## nstall from TestPyPI to verify (example):

python -m pip install --index-url https://test.pypi.org/simple/ sap

## UPLOAD 

python -m twine upload dist/*