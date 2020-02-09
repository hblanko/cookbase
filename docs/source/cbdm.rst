The Cookbase Data Model
=======================

The **Cookbase Data Model (CBDM)** is a suite of data format specifications aiming to
allow for a solution to represent the data involved in *the vast domain of cooking*. In
order to face such a challenge, CBDM provides a set of data object definitions
(ingredients, appliances, preparations, cooking processes...) and a model of the
interactions among these elements.

The following sections of this documentation show the conceptions behind the adopted
data model, presented in an explanatory (non-exahustive) fashion. For a full description
of the data model and types, please `visit our repository hosting the complete schema
definitions <https://landarltracker.com/schemas/>`_.

The Cookbase Data Model is organized into five main submodels:

- `Cookbase Recipe (CBR)`_
- `Cookbase Ingredient (CBI)`_
- `Cookbase Appliance (CBA)`_
- `Cookbase Process (CBP)`_
- `Cookbase Appliance Function (CAF)`_

=====================
Cookbase Recipe (CBR)
=====================

The design goal of the Cookbase Data Model is to provide a clear, flexible and scalable
way to store food preparation data. From this perspective, **Cookbase Recipe (CBR)**
turns to be the main and most relevant interface to the data model.

CBR is a data format that stores metadata and information about a recipe, and presents
the ingredients and appliances involved together with the preparation steps that model
its interactions and the process workfow.

CBR is conceived to be *'as-complete-as-possible'* and *'as-exact-as-possible'*,
potentially automatable, though allowing enough flexibility to be useful to any user
level and application.

The CBR model makes use of data stored by the underlying models for ingredients,
appliances and processes. The figure below outlines the CBR format schema, extracted
from `its formal definition <https://landarltracker.com/schemas/cbr.json>`_.

.. raw:: html

  <div class="figure align-center" id="uml-cbr">
      <p class="uml">
         <object class="uml-diagram" data="_static/images/cbr.svg" type="image/svg+xml">
            <img src="_static/images/cbr.png" alt="The Cookbase Recipe format diagram.">
         </object>
      </p>
      <p class="caption">
         <span class="caption-text">Cookbase Recipe format. <a href="_static/images/cbr.png">[View full-sized image]</a></span>
         <a class="headerlink" href="#uml-cbr" title="Permalink to this image">¶</a>
      </p>
   </div>

.. rst-class:: cbr-links-paragraph

Basically, a CBR document consists of five core sections: `info`_, `yield`_,
`ingredients`_, `appliances`_ and `preparation`_.

.. rst-class:: cbr-subsection-header

info
----




.. rst-class:: cbr-subsection-header

yield
-----




.. rst-class:: cbr-subsection-header

ingredients
-----------




.. rst-class:: cbr-subsection-header

appliances
----------




.. rst-class:: cbr-subsection-header

preparation
-----------




=========================
Cookbase Ingredient (CBI)
=========================

.. raw:: html

  <div class="figure align-center" id="uml-cbi">
      <p class="uml">
         <object class="uml-diagram" data="_static/images/cbi.svg" type="image/svg+xml">
            <img src="_static/images/cbi.png" alt="The Cookbase Ingredient format diagram.">
         </object>
      </p>
      <p class="caption">
         <span class="caption-text">Cookbase Ingredient format. <a href="_static/images/cbi.png">[View full-sized image]</a></span>
         <a class="headerlink" href="#uml-cbi" title="Permalink to this image">¶</a>
      </p>
   </div>


========================
Cookbase Appliance (CBA)
========================

.. raw:: html

  <div class="figure align-center" id="uml-cba">
      <p class="uml">
         <object class="uml-diagram" data="_static/images/cba.svg" type="image/svg+xml">
            <img src="_static/images/cba.png" alt="The Cookbase Appliance format diagram.">
         </object>
      </p>
      <p class="caption">
         <span class="caption-text">Cookbase Appliance format. <a href="_static/images/cba.png">[View full-sized image]</a></span>
         <a class="headerlink" href="#uml-cba" title="Permalink to this image">¶</a>
      </p>
   </div>


======================
Cookbase Process (CBP)
======================

.. raw:: html

  <div class="figure align-center" id="uml-cbp">
      <p class="uml">
         <object class="uml-diagram" data="_static/images/cbp.svg" type="image/svg+xml">
            <img src="_static/images/cbp.png" alt="The Cookbase Process format diagram.">
         </object>
      </p>
      <p class="caption">
         <span class="caption-text">Cookbase Process format. <a href="_static/images/cbp.png">[View full-sized image]</a></span>
         <a class="headerlink" href="#uml-cbp" title="Permalink to this image">¶</a>
      </p>
   </div>


=================================
Cookbase Appliance Function (CAF)
=================================

.. raw:: html

  <div class="figure align-center" id="uml-caf">
      <p class="uml">
         <object class="uml-diagram" data="_static/images/caf.svg" type="image/svg+xml">
            <img src="_static/images/caf.png" alt="The Cookbase Appliance Function format diagram.">
         </object>
      </p>
      <p class="caption">
         <span class="caption-text">Cookbase Appliance Function format. <a href="_static/images/caf.png">[View full-sized image]</a></span>
         <a class="headerlink" href="#uml-caf" title="Permalink to this image">¶</a>
      </p>
   </div>
