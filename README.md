# floodrisk
FloodRisk- QGIS plugin that provides the assessment of flood consequences,in terms of loss of life and direct economic damages.
# The tool
The tool performs a simple risk assessment in which it consider fixed event scenarios where the probability of each scenario is estimated separately and it calculates the consequences deterministically.
# Direct flood impact
- Direct economic damages estimation.

  The damage to residential, commercial and industrial property is assessed using depth–damage curves, which describe the relationship between levels of inundation and damage incurred
- Population at Risk and Loss of Life estimation

  In "FloodRisk" the first step for the loss of life estimation is to obtain the map of the population at risk by superimposing the inundation map and the population density map.
  Once calculated the map of the population at risk, the number of potential fatalities is obtained by multiplying population at risk time the fatality rate.
  The tool allows the user the choice of the fatality rate between two of the available scientific methods:
  - US Department of Homeland Security (DHS 2011)
  - SUFRI Methodology for pluvial and river flooding risk assessment (Escuder Bueno et al, 2011

(1) *US Departement of Homeland Security (DHS). Dams Sector. Estimating Loss of Life for Dam Failure Scenarios, September 2011*

(2) *SUFRI Methodology for pluvial and river flooding risk assessment in urban areas to inform decision-making. 2nd ERA-NET CRUE Research Funding Initiative Flood resilient communities – managing the consequences of flooding. Report, July 2011*
