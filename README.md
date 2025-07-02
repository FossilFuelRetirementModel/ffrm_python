# Welcome to the FFRM(Preview) Documentation

Fossil Fuel Retirement Model (FFRM) is an open-source python based fossil fuel retirement model. It was originally developed by the [World Bank](https://www.worldbank.org/ext/en/home) as a coal retirement optimisation model. It can be used to estimate the stranded cost associated with retiring fossil fuel power plants.

The model utilises a Pyomo-based optimisation framework to endogenously calculate stranded cost taking into consideration commercial and market issues. It uses projections for capacity and production of fossil fuel power plants to explore their retirement profile under two types of price regimes, PPA and market price regime to assess at what capacity does fossil fuel power plants become stranded and explores how this influences total compensation for stranded plants.  
 
## Features

- Multi-scenario analysis (Business As Usual, Accelerated Decarbonisation)
- Multiple price scenario support (Market Price, Average PPA Price)
- Flexible solver options (Gurobi, CPLEX, GLPK, CBC)
- Comprehensive result processing and Excel output
- Command-line interface for easy configuration
 
## **Installation**
Installation steps can be found on the FFRM Readthedoc [Documentation](https://ffrm-python.readthedocs.io/en/latest/index.html). 
 
## Contributing to FFRM
We are very grateful that you are looking into how you can contribute to FFRM.

Contributing to FFRM is open to everyone who is interested, and we adopt an inclusive and open policy which is described in our code of conduct. If you have general questions or comments on the project, please submit them to our community discussion board or our Discord forum is a great place to ask general FFRM questions.

If you are experiencing issues please submit a new issue.  
 
## Dependencies
FFRM relies on numerous open-source community supported tools. Below is a list of the heavily used packages.

[Python](https://www.python.org/): All data processing is written in the Python programming language

[GLPK](https://www.gnu.org/software/glpk/): Open-source linear programming toolkit

[CBC](https://github.com/coin-or/Cbc):Open-source linear program solver 

## Key publications
Suski, A., Hong, L., and Chattopadhyay, D. (2022) 'Modeling coal plant stranded costs for decarbonization pathway analyses', Energy for Sustainable Development, 71, pp. 480-489. Available at: https://www.sciencedirect.com/science/article/pii/S0973082622002022 
