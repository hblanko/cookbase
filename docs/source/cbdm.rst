.. |info| replace:: :term-mono:`info`
.. |yield| replace:: :term-mono:`yield`
.. |ingredients| replace:: :term-mono:`ingredients`
.. |appliances| replace:: :term-mono:`appliances`
.. |preparation| replace:: :term-mono:`preparation`

The |cookbase_tm| Data Model
============================

The |cookbase_tm| **Data Model (CBDM)** is a suite of data format specifications aiming
to allow for a solution to represent the data involved in *the vast domain of cooking*.
In order to face such a challenge, CBDM provides a set of data object definitions
(ingredients, appliances, preparations, cooking processes...) and a model of the
interactions among these elements.

The following sections of this documentation show the conceptions behind the adopted
data model, presented in an explanatory (non-exahustive) fashion. For a full description
of the data model and types, please :cbschema:`visit our repository hosting the complete
CBSchema definitions <>`.

The **CBDM** is organized into five main submodels:

- :ref:`Cookbase Recipe (CBR)<cbr>`
- :ref:`Cookbase Ingredient (CBI)<cbi>`
- :ref:`Cookbase Appliance (CBA)<cba>`
- :ref:`Cookbase Process (CBP)<cbp>`
- :ref:`Cookbase Appliance Function (CAF)<caf>`


.. _cbr:

===============
Cookbase Recipe
===============

The design goal of the |cookbase_tm| Data Model is to provide a clear, flexible and
scalable way to store food preparation data. From this perspective, **Cookbase Recipe
(CBR)** turns to be the main and most relevant interface to the data model.

CBR is a data format that stores metadata and information about a recipe, and presents
the ingredients and appliances involved together with the preparation steps that model
its interactions and the process workfow.

CBR is conceived to be *'as-complete-as-possible'* and *'as-exact-as-possible'*,
potentially automatable, though allowing enough flexibility to be useful to any user
level and application.

The CBR model makes use of data stored by the underlying models for ingredients,
appliances and processes. The figure below outlines the CBR Schema format, extracted
from :cbschema:`its formal CBSchema definition <cbr/cbr.json>`.

.. raw:: html

  <div class="figure align-center" id="cbr-uml">
      <p class="uml">
         <object class="uml-diagram" data="_static/images/cbr.svg" type="image/svg+xml">
            <img src="_static/images/cbr.png" alt="The Cookbase Recipe format diagram.">
         </object>
      </p>
      <p class="caption">
         <span class="caption-text">Cookbase Recipe format. <a href="_static/images/cbr.png">[View full-sized image]</a></span>
         <a class="headerlink" href="#cbr-uml" title="Permalink to this image">¶</a>
      </p>
   </div>

.. rst-class:: cbr-links-paragraph

Basically, a CBR document consists of five sections: two of them are focused on the
metadata and generic information about the recipe, |info|_, |yield|_; and the three
core parts of the document, describing the preparation flow and the elements involved
in, |ingredients|_, |appliances|_ and |preparation|_.


.. _cbr-info:
.. rst-class:: cbr-subsection-header

info
----

Metadata and basic information about the recipe –such as course types or cooking times–
are contained into the |info| object of the CBR document (see :cbschema:`CBSchema
<cbr/cbr-info.json>`).

.. code-block:: json
   :caption: **Example:** A typical |info| object.

   {
      "name": "Pizza mozzarella",
      "authorship": {
         "fullName": "Hernán Blanco",
         "version": "0.1"
      },
      "releaseDate": "2019-09-01",
      "cuisine": [
         "Argentine"
      ],
      "courseType": [
         "main dish"
      ],
      "preparationTime": {
         "value": 105,
         "measure": "min"
      },
      "cookingTime": {
         "value": 17,
         "measure": "min"
      },
      "servingTime": {
         "value": 1,
         "measure": "min"
      }
   }


.. _cbr-yield:
.. rst-class:: cbr-subsection-header

yield
-----

The |yield| section (see :cbschema:`CBSchema <cbr/cbr-yield.json>`) contains
information regarding the form of the recipe output and the way it is to be served.

.. code-block:: json
   :caption: **Example:** A typical |yield| object.

   {
      "servings": 8,
      "servingSize": {
         "descriptive": "medium",
         "weight": {
            "value": 160,
            "measure": "g"
         },
         "volume": {
            "value": 400,
            "measure": "ml"
         }
      },
      "servingFormat": "dinner plate"
   }


.. _cbr-ingredients:
.. rst-class:: cbr-subsection-header

ingredients
-----------

A collection of **CBR Ingredient** objects (see :cbschema:`CBSchema
<cbr/cbr-ingredient.json>`) is included in the CBR document, each of them holding an
identifier to a :ref:`cbi` object and the specific information on the ingredient
utilized for the recipe. Every ingredient is characterized by the following properties:

- :code:`name`: The name given to an ingredient of the recipe
- :code:`cbiId`: The identifier to the base :ref:`CBI <cbi>` document
- :code:`subdivision` *(optional)*: A name specifying a subsection of the recipe, into
  which a number of ingredients can be grouped
- :code:`amount` *(optional)*: Description on the ingredient's quantity applied to the
  recipe
- :code:`optional` *(optional)*: A boolean flag indicating whether the ingredient is
  optional
- :code:`notes` *(optional)*: Any comment on the ingredient that the author considered
  relevant to remark

.. code-block:: json
   :caption: **Example:** A non-optional ingredient *'tomato purée'*, associated to a
     determined Cookbase Ingredient, and making part of the *'sauce'* recipe
     subdivision.

   {
      "subdivision": "sauce",
      "name": {
         "text": "tomato purée",
         "language": "en"
      },
      "cbiId": 1978180615,
      "amount": {
         "value": 230,
         "measure": "g"
      }
   }


.. _cbr-appliances:
.. rst-class:: cbr-subsection-header

appliances
----------

The list of **CBR Appliance** objects (see :cbschema:`CBSchema
<cbr/cbr-appliance.json>`) in the CBR document describes all the kitchenware involved in
the preparation of the given recipe.

A **CBR Appliance** can be defined in two different ways:

#. In association to a determined definition of a :ref:`cba`

   - :code:`name`: The name given to an appliance used during the recipe preparation
   - :code:`cbaId`: The identifier to the base :ref:`CBA <cba>` document

#. Specifying the functions that the appliance is to be able to perform

   - :code:`functions`: An array containing the different functionalities required to
     the appliance

On top of the items involved on these two possible instantiation models, the following
also apply to any specified appliance:

- :code:`properties` *(optional)*: One or more specifications regarding physical
  properties that the appliance should fulfill, such as size, capacity...
- :code:`optional` *(optional)*: A boolean flag indicating whether the ingredient is
  optional
- :code:`notes` *(optional)*: Any comment on the appliance that the author considered
  relevant to remark

.. code-block:: json
   :caption: **Example:** A *'pizza tray'* appliance indicating its associated Cookbase
     Appliance, and conditions on its diameter and material.

     {
        "name": {
           "text": "pizza tray",
           "language": "en"
        },
        "cbaId": 1962226524,
        "properties": {
           "diameter": {
              "value": 32,
              "measure": "cm"
           },
           "preferredMaterial": "metal"
        }
     }


.. _cbr-preparation:
.. rst-class:: cbr-subsection-header

preparation
-----------

The |preparation| section represents the sequence of steps that are required
to prepare the recipe expressed by the CBR document. It is constructed as a collection
of **CBR Process** objects (see :cbschema:`CBSchema <cbr/cbr-process.json>`) that
define the interactions produced during the ellaboration of a recipe with the given
ingredients and appliances. The data contained in the |preparation| object
(together with the |ingredients|_ and |appliances|_ objects) is conceived to allow for
the representation of a :doc:`Cookbase Recipe Graph <cbrg>`. This imposes a number of
:ref:`assumptions and conditions <assumptions>` that any CBR document must follow to be
considered a valid CBR.

A **CBR Process** is a CBSchema representation of a :ref:`cbp`, where the
following properties are general present:

- :code:`name`: The name given to a process of the recipe
- :code:`cbpId`: The identifier to the base :ref:`CBP <cbp>` document
- :code:`parameters` *(optional)*: One or more specifications on process end conditions
  or other process-related attributes that should be taken into account: time,
  temperature, weight, position in the oven...
- :code:`foodstuff` *("abstract")*: One or more properties that provide references
  either to ingredients or to the product of a previously performed (and finished)
  process. Such references must be strings that match within the same CBR document to a
  definition of either a **CBR Ingredient** or a **CBR Process**.

  Different names can be given to a :code:`foodstuff` property, in order to provide a
  better insight of its role within the context of a concrete process. This
  specification is provided in the :ref:`CBP <cbp>` document.
- :code:`appliances`: A list of the appliances involved in the process, referred by
  strings that match within the same CBR document to a definition of a
  **CBR Appliance**. Each appliance is also kept with information on whether it remains
  used after the finalization of the process or, on the contrary, it is released for
  other potential uses.
- :code:`residuals` *(optional)*: A boolean flag indicating whether the process
  generates any kind of residual product
- :code:`return` *(optional)*: A boolean flag indicating whether the process provides
  any sort of informative feedback (e.g. a weight measurement)
- :code:`notes` *(optional)*: Any comment on the process that the author considered
  relevant to remark

.. code-block:: json
   :caption: **Example:** An *'adding'* process which is an instance of a given
     Cookbase Process. In this case, :code:`foodstuffsList` provides a reference list
     with the ingredients to be added, and the appliance that is used during the process
     (remaining used after the process is finished).

   {
      "name": {
         "text": "adding",
         "language": "en"
      },
      "cbpId": 3308424952,
      "foodstuffsList": [
         "ing1",
         "ing2",
         "ing3"
      ],
      "appliances": [
         {
            "appliance": "pot1",
            "usedAfter": true
         }
      ]
   }


.. _cbi:

===================
Cookbase Ingredient
===================

.. raw:: html

  <div class="figure align-center" id="cbi-uml">
      <p class="uml">
         <object class="uml-diagram" data="_static/images/cbi.svg" type="image/svg+xml">
            <img src="_static/images/cbi.png" alt="The Cookbase Ingredient format diagram.">
         </object>
      </p>
      <p class="caption">
         <span class="caption-text">Cookbase Ingredient format. <a href="_static/images/cbi.png">[View full-sized image]</a></span>
         <a class="headerlink" href="#cbi-uml" title="Permalink to this image">¶</a>
      </p>
   </div>


.. _cba:

==================
Cookbase Appliance
==================

.. raw:: html

  <div class="figure align-center" id="cba-uml">
      <p class="uml">
         <object class="uml-diagram" data="_static/images/cba.svg" type="image/svg+xml">
            <img src="_static/images/cba.png" alt="The Cookbase Appliance format diagram.">
         </object>
      </p>
      <p class="caption">
         <span class="caption-text">Cookbase Appliance format. <a href="_static/images/cba.png">[View full-sized image]</a></span>
         <a class="headerlink" href="#cba-uml" title="Permalink to this image">¶</a>
      </p>
   </div>


.. _cbp:

================
Cookbase Process
================

represents the minimal functional unit of a recipe preparation. It descr

.. raw:: html

  <div class="figure align-center" id="cbp-uml">
      <p class="uml">
         <object class="uml-diagram" data="_static/images/cbp.svg" type="image/svg+xml">
            <img src="_static/images/cbp.png" alt="The Cookbase Process format diagram.">
         </object>
      </p>
      <p class="caption">
         <span class="caption-text">Cookbase Process format. <a href="_static/images/cbp.png">[View full-sized image]</a></span>
         <a class="headerlink" href="#cbp-uml" title="Permalink to this image">¶</a>
      </p>
   </div>


.. _caf:

===========================
Cookbase Appliance Function
===========================

.. raw:: html

  <div class="figure align-center" id="caf-uml">
      <p class="uml">
         <object class="uml-diagram" data="_static/images/caf.svg" type="image/svg+xml">
            <img src="_static/images/caf.png" alt="The Cookbase Appliance Function format diagram.">
         </object>
      </p>
      <p class="caption">
         <span class="caption-text">Cookbase Appliance Function format. <a href="_static/images/caf.png">[View full-sized image]</a></span>
         <a class="headerlink" href="#caf-uml" title="Permalink to this image">¶</a>
      </p>
   </div>
