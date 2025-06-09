Tags
====

.. versionadded:: 2.2.0
   This resource endpoint.

Resource description
--------------------

The tag resource contains the following fields (currently limited to organisers and reviewers):

.. rst-class:: rest-resource-table

===================================== ========================== =======================================================
Field                                 Type                       Description
===================================== ========================== =======================================================
tag                                   string                     The actual tag name.
description                           multi-lingual string       The description of the tag.
``color``                             string                     The tag’s colour as hex string.
``is_public``                         boolean                    Flag, ``True`` if the tag is intended to be public once pretalx supports public tags.
===================================== ========================== =======================================================

Endpoints
---------

.. raw:: html

   <redoc hide-download-button disable-search hide-loading json-sample-expand-level="3" id=redoc></redoc>
   <style>
   redoc .menu-content, redoc .api-info, redoc #tag\/api, redoc .api-content + div { display: none }
   redoc#redoc {
        display: block;
        max-width: calc(100% + 6em);
        margin-left: -2.5em;
   }
   redoc .api-content {
        margin-top: -80px;
        width: 100%;
   }
   redoc#redoc .api-content > div[data-section-id] > div[data-section-id] > :nth-child(1) {
        width: calc(50%);
   }
   redoc#redoc .api-content > div[data-section-id] > div[data-section-id] > :nth-child(2) {
        width: calc(50%);
        background: none;
        h3 {
            color: var(--text-color);
        }
   }
   redoc#redoc table {
    tr {
        background-color: transparent;
    }
    td, th {
        border-top: none;
        border-right: none;
        border-bottom: none;
    }
    tr > td:first-of-type {
        padding-top: 1em;
    }
    tr > td:not(:first-of-type) {
        border-left: none;
    }
   }
   </style>
   <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
   <script>
        var spec = "../../_specs/schema-tags.yml";
        Redoc.init(spec);
    </script>
