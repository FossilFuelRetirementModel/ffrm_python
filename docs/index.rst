.. FFRM documentation master file, created by
   sphinx-quickstart on Wed Mar 26 16:59:17 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

 
.. _welcome:

===========================================
Welcome to the documentation of ``FFRM``!
===========================================

.. image:: _static/FFRMWorkflow.jpg
   :width: 80%
   :alt: FFRMWorkflow
   :align: center

**F**\ossil **F**\uel **R**\etirement **M**\odel (FFRM) is an open-source Python-based fossil fuel retirement model. It was originally developed by the `World Bank <https://www.worldbank.org/>`_ as a coal retirement optimisation model. It can be used to estimate the stranded cost associated with retiring fossil fuel power plants.

The model utilises a `Pyomo-based optimisation framework <http://www.pyomo.org>`_ to endogenously calculate stranded cost, taking into consideration commercial and market issues. It uses projections for capacity and production of fossil fuel power plants to explore their retirement profile under three types of price regimes: **PPA**, **Market Price regime** and **Cost of Service Regime**.

The model assesses at what capacity fossil fuel power plants become stranded and explores how this influences total compensation for stranded plants. The model is designed to complement more detailed long-term capacity expansion models, such as OSeMOSYS, TIMES, LEAP, and others, but can also be used as a standalone retirement model.


Background
==========

A model was developed by the World Bank to assess stranded cost under various defined scenarios.
The model defines stranded cost as the difference in plant revenue. In particular, the foregone revenue
of plants that reach the end of their economic life in the decarbonisation scenarios, relative to the baseline scenario.
A recent application of the tool by Suski et al (2022) can be found `here <https://www.sciencedirect.com/science/article/abs/pii/S0973082622002022>`_, in which a GAMS-based version of FFRM was applied to the power sectors of India and the Philippines to calculate the stranded cost implications of early retirement of its coal fleet.


Aims
====

The objective function of the model is set as maximisation of the net revenue at the fleet, based on either under the following regimes:

- **Power Purchase Agreements (PPAs)**: Revenues are based on known contractual terms specific to each plant.
- **Market Price Regime**: Revenues are linked to variable, market-determined electricity prices.
- **Cost of Service Regime**: Revenues are set to recover allowable costs through regulated electricity tariffs.

The difference in net revenue between the BAU and a decarbonization scenario is used as a measure of forgone revenue.


Electricity Market Structures Map
=================================

This map provides an indicative classification of electricity market structures for emerging markets and developing economies (EMDEs). Each country has a classified **market structure** used in FFRM: market-based, PPA-based, or cost of service.

In reality, many countries operate mixed systems (for example, regulated tariffs alongside IPP PPAs and short-term power markets). This mix is captured in the underlying data through separate flags (``Has_Market``, ``Has_PPA``, ``Has_Regulated``) and a mixed-system indicator.

.. raw:: html

   <div style="width: 100%; max-width: 1100px; margin: 0 auto;">
     <iframe
       src="_static/emde_regime_map.html"
       width="100%"
       height="600"
       style="border: none;"
     ></iframe>
   </div>


Contents
========

.. toctree::
   :maxdepth: 1

   Install <install>
   Structure <structure>
   Run Options <RunOptions>
   Examples <examples>
   Contributors <contributors>
   License <License>
   Change Log <ChangeLog>
   Key Publications <KeyPublications>


Search
======

* :ref:`search`
