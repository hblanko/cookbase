The |cookbase_tm| Data Model
============================

The |cookbase_tm| **Data Model (CBDM)** is a suite of data format specifications aiming
to allow for a solution to represent the data involved in *the vast domain of cooking*.
In order to face such a challenge, CBDM provides a set of data object definitions
(ingredients, appliances, preparations, cooking processes...) and a model of the
interactions among these elements.

The following sections of this documentation show the conceptions behind the adopted
data model, presented in an explanatory (non-exahustive) fashion. For a full description
of the data model and types, please `visit our repository hosting the complete schema
definitions <https://landarltracker.com/schemas/>`_.

The |cookbase_tm| Data Model is organized into five main submodels:

- `Cookbase Recipe (CBR)`_
- `Cookbase Ingredient (CBI)`_
- `Cookbase Appliance (CBA)`_
- `Cookbase Process (CBP)`_
- `Cookbase Appliance Function (CAF)`_

=====================
Cookbase Recipe (CBR)
=====================

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
appliances and processes. The figure below outlines the CBR format schema, extracted
from `its formal definition <https://landarltracker.com/schemas/cbr.json>`_.

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
metadata and generic information about the recipe, `info`_, `yield`_; and the three
core parts of the document, describing the preparation flow and the elements involved
in, `ingredients`_, `appliances`_ and `preparation`_.


.. rst-class:: cbr-subsection-header

info
----

Metadata and basic information about the recipe –such as course types or cooking times–
are contained into the :term-mono:`info` object of the CBR document (`schema description
<https://landarltracker.com/schemas/info.json>`_).

.. code-block:: json
   :caption: **Example:** A typical :term-mono:`info` object.

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


.. rst-class:: cbr-subsection-header

yield
-----

The :term-mono:`yield` section (`schema description
<https://landarltracker.com/schemas/appliance.json>`_) contains information regarding
the form of the recipe output and the way it is to be served.

.. code-block:: json
   :caption: **Example:** A typical :term-mono:`yield` object.

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


.. rst-class:: cbr-subsection-header

ingredients
-----------

A collection of :term-mono:`ingredient` objects (`schema description
<https://landarltracker.com/schemas/ingredient.json>`_) is included in the CBR document,
each of them holding an identifier to a `Cookbase Ingredient (CBI)`_ object and the
specific information on the ingredient utilized for the recipe. Every ingredient is
characterized by the following properties:

- :code:`name`: The name given to an ingredient of the recipe
- :code:`cbiId`: The identifier to the base `Cookbase Ingredient (CBI)`_
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



.. rst-class:: cbr-subsection-header

appliances
----------

The list of :term-mono:`appliance` objects (`schema description
<https://landarltracker.com/schemas/appliance.json>`_) in the CBR document describes
all the kitchenware involved in the preparation of the given recipe.

Appliances can be defined in two different ways:

#. In association to a determined definition of a `Cookbase Appliance (CBA)`_

   - :code:`name`: The name given to an appliance used during the recipe preparation
   - :code:`cbaId`: The identifier to the base CBA document

#. Specifying the functions that the appliance is to be able to perform

   - :code:`functions`: An array containing the different functionalities required to
     the appliance

On top of the items involved on these two possible instantiation models, the following
also apply to any specified appliance:

- :code:`properties` *(optional)*: One or more specifications regarding physical
  properties that the appliance should fulfill, such as size, capacity...
- :code:`optional` *(optional)*: A boolean flag indicating whether the ingredient is
  optional
- :code:`notes` *(optional)*: Any comment on the ingredient that the author considered
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


.. rst-class:: cbr-subsection-header

preparation
-----------

The :term-mono:`preparation` section represents the sequence of steps that are required
to prepare the recipe expressed by the CBR document. It is constructed as a collection
of :term-mono:`process` objects (`schema description
<https://landarltracker.com/schemas/process.json>`_) that define the interactions
produced during the ellaboration of a recipe with the given ingredients and appliances.
The data contained in the :term-mono:`preparation` object (together with the
`ingredients`_ and `appliances`_ objects) is designed to allow for the representation
of a :doc:`Cookbase Recipe Graph <cbrg>`.

A process is

=========================
Cookbase Ingredient (CBI)
=========================

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


========================
Cookbase Appliance (CBA)
========================

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


======================
Cookbase Process (CBP)
======================

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


=================================
Cookbase Appliance Function (CAF)
=================================

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
