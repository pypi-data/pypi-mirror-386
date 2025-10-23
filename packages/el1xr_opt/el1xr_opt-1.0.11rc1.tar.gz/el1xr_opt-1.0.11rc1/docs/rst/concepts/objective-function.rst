Objective Function
==================
The core purpose of the optimization model is to minimize the total system cost over a specified time horizon. This is achieved through an objective function that aggregates all relevant operational expenditures, as well as penalties for undesirable outcomes like unmet demand.

The main objective function is defined by the Pyomo constraint «``eTotalSCost``», which minimizes the variable «``vTotalSCost``» (:math:`\alpha`).

Total System Cost
-----------------
The total system cost is the sum of all discounted costs across every period (:math:`\periodindex`) and scenario (:math:`\scenarioindex`) in the model horizon. The objective function can be expressed conceptually as:

Total system cost («``eTotalSCost``»)

.. math::
   \min \alpha

And the total cost is the sum of all operational costs, discounted to present value («``eTotalTCost``»):

:math:`\alpha = \sum_{\periodindex \in \nP} \pdiscountrate_{\periodindex}
\sum_{\scenarioindex \in \nS}(\marketcost_{\periodindex,\scenarioindex} - \marketrevenue_{\periodindex,\scenarioindex})`

:math:`\marketcost_{\periodindex,\scenarioindex} = \underbrace{\elemarketcostgrid_{\periodindex,\scenarioindex}}_{\text{Network usage}}
\!+\! \underbrace{\elemarketcosttax_{\periodindex,\scenarioindex}}_{\text{Surcharges/taxes}}
\!+\! \sum_{\timeindex \in \nT} \ptimestepduration_{\periodindex,\scenarioindex,\timeindex}(\underbrace{\elemarketcost_{\periodindex,\scenarioindex,\timeindex}
\!+\! \hydmarketcost_{\periodindex,\scenarioindex,\timeindex}}_{\text{Market purchases}}
\!+\! \underbrace{\elemaintopercost_{\periodindex,\scenarioindex,\timeindex}
\!+\! \hydmaintopercost_{\periodindex,\scenarioindex,\timeindex}}_{\text{Generation/consumption}}
\!+\! \underbrace{\eledegradationcost_{\periodindex,\scenarioindex,\timeindex}
\!+\! \hyddegradationcost_{\periodindex,\scenarioindex,\timeindex}}_{\text{Degradation}})`

:math:`\marketrevenue_{\periodindex,\scenarioindex} = \underbrace{\elemarketrevenuetax_{\periodindex,\scenarioindex}}_{\text{Incentives}}
\!+\! \sum_{\timeindex \in \nT} \ptimestepduration_{\periodindex,\scenarioindex,\timeindex}(\underbrace{\elemarketrevenue_{\periodindex,\scenarioindex,\timeindex}
\!+\! \hydmarketrevenue_{\periodindex,\scenarioindex,\timeindex}}_{\text{Market purchases}}
\!+\! \underbrace{\elemarketrevenueancillary_{\periodindex,\scenarioindex,\timeindex}}_{\text{Ancillary services}})`

The total cost is broken down into several components, each represented by a specific variable. The model seeks to find the optimal trade-off between these costs.

Electricity Grid Usage
----------------------
This component models capacity-based and tariffs, and consider the power peak penalization cost.

:math:`\elemarketcostgrid_{\periodindex,\scenarioindex} = \elepeakdemandcost_{\periodindex,\scenarioindex} + \elenetusecost_{\periodindex,\scenarioindex} + \elecaptariffcost_{\periodindex,\scenarioindex}`

Peak Demand Cost
~~~~~~~~~~~~~~~~
This cost subcomponent is determined by the highest power peak registered during a specific billing period (e.g., a month). This incents the model to "shave" demand peaks to reduce costs.

The formulation is defined by «``eTotalElePeakCost``».

.. math::
    \elepeakdemandcost_{\periodindex,\scenarioindex} = \frac{1}{|\nKE|} \sum_{\traderindex \in \nRE} \ppeakdemandtariff_{\traderindex} \pfactorone \sum_{\monthindex \in \nM} \sum_{\peakindex \in \nKE} \velepeakdemand_{\periodindex,\scenarioindex,\monthindex,\traderindex,\peakindex}

Network Usage Cost
~~~~~~~~~~~~~~~~~~
This cost subcomponent captures the expenses associated with using the electricity distribution or transmission network. It is typically based on the amount of energy consumed or injected into the grid over a billing period.
The formulation is defined by «``eTotalEleNetUseCost``».

.. math::
    \elenetusecost_{\periodindex,\scenarioindex} = \sum_{\traderindex \in \nRE} \pelemarketnetfee_{\traderindex} \pfactorone \sum_{\monthindex \in \nM} \sum_{\timeindex \in \nT_{\monthindex}} \velemarketbuy_{\periodindex,\scenarioindex,\timeindex,\traderindex}

Capacity Tariff Cost
~~~~~~~~~~~~~~~~~~~~
This cost subcomponent represents fixed charges based on the capacity of the connection to the electricity network. It is usually a monthly fee that depends on the contracted capacity.
The formulation is defined by «``eTotalEleCapTariffCost``».

.. math::
    \elecaptariffcost_{\periodindex,\scenarioindex} = \sum_{\traderindex \in \nRE} \pelemarkettariff_{\traderindex} \pfactorone \sum_{\monthindex \in \nM} \sum_{\timeindex \in \nT_{\monthindex}} \pelecontractedcapacity_{\periodindex,\scenarioindex,\timeindex,\traderindex}

By minimizing the sum of these components, the model finds the most economically efficient way to operate the system's assets to meet energy demand reliably.

Market
------
This represents the costs and revenues in the electricity and hydrogen markets.

Electricity Market Costs
~~~~~~~~~~~~~~~~~~~~~~~~
The formulation is defined by «``eTotalEleMCost``».

:math:`\elemarketcost_{\periodindex,\scenarioindex,\timeindex} = \elemarketcostDA_{\periodindex,\scenarioindex,\timeindex} + \elemarketcostPPA_{\periodindex,\scenarioindex,\timeindex}`

#.  **Electricity Purchase**: The cost incurred from purchasing electricity from the market. This cost is defined by the constraint «``eTotalEleTradeCost``» and includes variable energy costs, taxes, and other fees.

    .. math::
       \elemarketcostDA_{\periodindex,\scenarioindex,\timeindex} = \sum_{\traderindex \in \nRE} \pelebuyprice_{\periodindex,\scenarioindex,\timeindex,\traderindex} \pelemarketbuyingratio_{\traderindex}\velemarketbuy_{\periodindex,\scenarioindex,\timeindex,\traderindex}

Electricity Market Revenues
~~~~~~~~~~~~~~~~~~~~~~~~~~~

:math:`\elemarketrevenue_{\periodindex,\scenarioindex,\timeindex} = \elemarketrevenueDA_{\periodindex,\scenarioindex,\timeindex} + \elemarketrevenuePPA_{\periodindex,\scenarioindex,\timeindex} + \elemarketrevenueancillary_{\periodindex,\scenarioindex,\timeindex}`

#.  **Electricity Sales**: The revenue generated from selling electricity to the market. This is defined by the constraint ``eTotalEleTradeProfit``.

    .. math::
       \elemarketrevenueDA_{\periodindex,\scenarioindex,\timeindex} = \sum_{\traderindex \in \nRE} \pelesellprice_{\periodindex,\scenarioindex,\timeindex,\traderindex} \pelemarketsellingratio_{\traderindex} \velemarketsell_{\periodindex,\scenarioindex,\timeindex,\traderindex}

Hydrogen Market Costs
~~~~~~~~~~~~~~~~~~~~~
The formulation is defined by «``eTotalHydMCost``».

:math:`\hydmarketcost_{\periodindex,\scenarioindex,\timeindex} = \hydmarketcostPPA_{\periodindex,\scenarioindex,\timeindex}`

#.  **Hydrogen Purchase**: The cost incurred from purchasing hydrogen from the market, as defined by ``eTotalHydTradeCost``.

    .. math::
       \hydmarketcostPPA_{\periodindex,\scenarioindex,\timeindex} = \sum_{\traderindex \in \nRH} (\phydbuyprice_{\periodindex,\scenarioindex,\timeindex,\traderindex} \vhydmarketbuy_{\periodindex,\scenarioindex,\timeindex,\traderindex})

Hydrogen Market Costs
~~~~~~~~~~~~~~~~~~~~~

:math:`\hydmarketrevenue_{\periodindex,\scenarioindex,\timeindex} = \hydmarketrevenuePPA_{\periodindex,\scenarioindex,\timeindex}`

#.  **Hydrogen Sales**: The revenue generated from selling hydrogen to the market, as defined by ``eTotalHydTradeProfit``.

    .. math::
       \hydmarketrevenuePPA_{\periodindex,\scenarioindex,\timeindex} = \sum_{\traderindex \in \nRH} (\phydsellprice_{\periodindex,\scenarioindex,\timeindex,\traderindex} \vhydmarketsell_{\periodindex,\scenarioindex,\timeindex,\traderindex})

Electricity Grid Services
-------------------------
This component captures revenues from providing ancillary services to the electricity grid, such as frequency regulation, spinning reserves, and voltage support.
The total revenue from ancillary services (:math:`\elemarketrevenueancillary_{\periodindex,\scenarioindex,\timeindex}`) is defined by the constraint «``eTotalEleAncillaryRevenue``».

:math:`\elemarketrevenueancillary_{\periodindex,\scenarioindex,\timeindex} = \freqcontdisturbrevenue_{\periodindex,\scenarioindex,\timeindex}`

Frequency Containment Reserve for Disturbance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This revenue subcomponent is earned by providing frequency containment reserves to manage disturbances in the grid.

.. math::
    \freqcontdisturbrevenue_{\periodindex,\scenarioindex,\timeindex} = \sum_{\genindex \in \nG} \pelefcrdupprice_{\periodindex,\scenarioindex,\timeindex} \velefcrdupbid_{\periodindex,\scenarioindex,\timeindex,\genindex} + \pelefcrddwprice_{\periodindex,\scenarioindex,\timeindex} \velefcrddwbid_{\periodindex,\scenarioindex,\timeindex,\genindex}

Taxes and Pass-Throughs
-----------------------
This component accounts for various taxes, surcharges, pass-through costs and incentives associated with electricity market transactions. These can include:

Tax Costs
~~~~~~~~~
The formulation is defined by «``eTotalEleTaxCost``».

.. math::
    \elemarketcosttax_{\periodindex,\scenarioindex} = \sum_{\traderindex \in \nRE} \pelemarketmoms_{\traderindex} \sum_{\timeindex \in \nT} (\pelebuyprice_{\periodindex,\scenarioindex,\timeindex,\traderindex} + \pelemarketpassthrough_{\traderindex}\pfactorone + \pelemarketnetfee_{\traderindex}\pfactorone)  \velemarketbuy_{\periodindex,\scenarioindex,\timeindex,\traderindex}

Incentives and Certificate Revenues
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The formulation is defined by «``eTotalEleIncentiveCost``».

.. math::
    \elemarketrevenuetax_{\periodindex,\scenarioindex} = \sum_{\traderindex \in \nRE} \pelemarketcertrevenue_{\traderindex} \pfactorone \sum_{\timeindex \in \nT} \velemarketsell_{\periodindex,\scenarioindex,\timeindex,\traderindex}

Operation and Maintenance
-------------------------
This is the operational cost of running the generation and production assets. It typically includes:

*   **Variable Costs**: Proportional to the energy produced (e.g., fuel costs).
*   **No-Load Costs**: The cost of keeping a unit online, even at minimum output.
*   **Start-up and Shut-down Costs**: Costs incurred when changing a unit's commitment state.

The cost is defined by ``eTotalEleGCost`` for electricity and ``eTotalHydGCost`` for hydrogen.

:math:`\elemaintopercost_{\periodindex,\scenarioindex,\timeindex} = \elegenerationcost_{\periodindex,\scenarioindex,\timeindex}
\!+\! \carboncost_{\periodindex,\scenarioindex,\timeindex}
\!+\! \eleconsumptioncost_{\periodindex,\scenarioindex,\timeindex}
\!+\! \eleunservedenergycost_{\periodindex,\scenarioindex,\timeindex}`

:math:`\hydmaintopercost_{\periodindex,\scenarioindex,\timeindex} = \hydgenerationcost_{\periodindex,\scenarioindex,\timeindex}
\!+\! \hydconsumptioncost_{\periodindex,\scenarioindex,\timeindex}
\!+\! \hydunservedenergycost_{\periodindex,\scenarioindex,\timeindex}`

Generation
~~~~~~~~~~

Electricity Generation Costs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The formulation is defined by «``eTotalEleGCost``».

.. math::
   \begin{aligned}
   \elegenerationcost_{\periodindex,\scenarioindex,\timeindex}
   = &\sum_{\genindex \in \nGE}
      \Big(
           \pvariablecost_{\genindex}\,\veleproduction_{\periodindex,\scenarioindex,\timeindex,\genindex}
         + \pmaintenancecost_{\genindex}\,\veleproduction_{\periodindex,\scenarioindex,\timeindex,\genindex}
      \Big) \\
   &
      + \sum_{\genindex \in \nGENR}
      \Big(
           \pfixedcost_{\genindex}\,\vcommitbin_{\periodindex,\scenarioindex,\timeindex,\genindex}
         \!+\! \pstartupcost_{\genindex}\,\vstartupbin_{\periodindex,\scenarioindex,\timeindex,\genindex}
         \!+\! \pshutdowncost_{\genindex}\vshutdownbin_{\periodindex,\scenarioindex,\timeindex,\genindex}
      \Big)
   \end{aligned}

Hydrogen Generation Costs
^^^^^^^^^^^^^^^^^^^^^^^^^
The formulation is defined by «``eTotalHydGCost``».

.. math::
   \begin{aligned}
   \hydgenerationcost_{\periodindex,\scenarioindex,\timeindex}
   = \sum_{\genindex \in \nGH}
      \Big(&
           \pvariablecost_{\genindex}\,\vhydproduction_{\periodindex,\scenarioindex,\timeindex,\genindex}
         + \pmaintenancecost_{\genindex}\,\vhydproduction_{\periodindex,\scenarioindex,\timeindex,\genindex}\\
   &
         + \pfixedcost_{\genindex}\,\vcommitbin_{\periodindex,\scenarioindex,\timeindex,\genindex}
         + \pstartupcost_{\genindex}\,\vstartupbin_{\periodindex,\scenarioindex,\timeindex,\genindex}
         + \pshutdowncost_{\genindex}\,\vshutdownbin_{\periodindex,\scenarioindex,\timeindex,\genindex}
      \Big)
   \end{aligned}

Emission Costs
~~~~~~~~~~~~~~
This component captures the cost of carbon emissions from fossil-fueled generators. It is calculated by multiplying the CO2 emission rate of each generator by its output and the carbon price (:math:`\pcarbonprice_{\genindex}`).
The formulation is defined by «``eTotalECost``».


.. math::
    \carboncost_{\periodindex,\scenarioindex,\timeindex} = \sum_{\genindex \in \nGENR} \pcarbonprice_{\genindex} \veleproduction_{\periodindex,\scenarioindex,\timeindex,\genindex}

Consumption
~~~~~~~~~~~
This represents the costs associated with operating energy consumers within the system, most notably the cost of power used to charge energy storage devices.

Electricity Consumption Costs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The formulation is defined by «``eTotalEleCCost``».

.. math::
    \eleconsumptioncost_{\periodindex,\scenarioindex,\timeindex} = \sum_{\storageindex \in \nEE} \pvariablecost_{\storageindex} \veleconsumption_{\periodindex,\scenarioindex,\timeindex,\storageindex}

Hydrogen Consumption Costs
^^^^^^^^^^^^^^^^^^^^^^^^^^
The formulation is defined by «``eTotalHydCCost``».

.. math::
    \hydconsumptioncost_{\periodindex,\scenarioindex,\timeindex} = \sum_{\storageindex \in \nEH} \pvariablecost_{\storageindex} \veleconsumption_{\periodindex,\scenarioindex,\timeindex,\storageindex}

Reliability
~~~~~~~~~~~
This is a penalty cost applied to any energy demand that cannot be met. It is calculated by multiplying the amount of unserved energy by a very high "value of lost load" (:math:`\ploadsheddingcost_{\demandindex}`), ensuring the model prioritizes meeting demand.
*   Associated variables: :math:`\veleloadshed` (Electricity Not Served), :math:`\vhydloadshed` (Hydrogen Not Served).

Electricity Energy-not-served Costs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The formulation is defined by «``eTotalEleRCost``».

.. math::
    \eleunservedenergycost_{\periodindex,\scenarioindex,\timeindex} = \sum_{\demandindex \in \nDE} \ploadsheddingcost_{\demandindex} \veleloadshed_{\periodindex,\scenarioindex,\timeindex,\demandindex}

Hydrogen Energy-not-served Costs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The formulation is defined by «``eTotalHydRCost``».

.. math::
    \hydunservedenergycost_{\periodindex,\scenarioindex,\timeindex} = \sum_{\demandindex \in \nDH} \ploadsheddingcost_{\demandindex} \vhydloadshed_{\periodindex,\scenarioindex,\timeindex,\demandindex}

Degradation
-----------
