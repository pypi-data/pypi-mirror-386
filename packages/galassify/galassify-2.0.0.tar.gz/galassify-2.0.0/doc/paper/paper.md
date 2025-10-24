---
title: 'GALAssify: A Python package for visually classifying astronomical objects'
tags:
  - Python
  - astronomy
  - classification
authors:
  - name: Manuel Alcázar-Laynez
    orcid: 0009-0007-0717-5283
    affiliation: 1
    corresponding: true # (This is how to denote the corresponding author)
  - name: Andoni Jimenez
    orcid: 0000-0002-5236-9278
    affiliation: 1
  - name: Salvador Duarte Puertas
    orcid: 0000-0002-5542-1940
    affiliation: "1, 2, 3" # (Multiple affiliations must be quoted)
  - name: Cristian Pozo González
    affiliation: 1
  - name: Jesús Domínguez-Gómez
    orcid: 0000-0003-1781-795X
    affiliation: 1
  - name: Guillermo Blázquez-Calero
    orcid: 0000-0002-7078-2373
    affiliation: 4
  - name: Maria del Carmen Argudo-Fernández
    orcid: 0000-0002-0789-2326
    affiliation: "1, 2"
  - name: Simon Verley
    orcid: 0000-0002-0684-9115
    affiliation: "1, 2"
  - name: Daniel Espada
    orcid: 0000-0002-8726-7685
    affiliation: "1, 2"
  - name: Estrella Florido
    orcid: 0000-0002-2982-9424
    affiliation: "1, 2"
  - name: Isabel Pérez
    orcid: 0000-0003-1634-4628
    affiliation: "1, 2"
  - name: Tomás Ruiz-Lara
    orcid: 0000-0001-6984-4795
    affiliation: "1, 2"
  - name: Laura Sánchez-Menguiano
    orcid: 0000-0003-1888-6578
    affiliation: "1, 2"
  - name: Almudena Zurita
    orcid: 0000-0001-6928-6367
    affiliation: "1, 2"

affiliations:
 - name: Departamento de Física Teórica y del Cosmos, Campus de Fuentenueva, Universidad de Granada, 18071 Granada, Spain
   index: 1
 - name: Instituto Carlos I de Física Teórica y Computacional, Spain
   index: 2
 - name: Département de Physique, de Génie Physique et d'Optique, Université Laval, et Centre de Recherche en Astrophysique du Québec (CRAQ), Québec, QC, G1V 0A6, Canada
   index: 3
 - name: Instituto de Astrofísica de Andalucía, CSIC, Glorieta de la Astronomía s/n, E-18008 Granada, Spain.
   index: 4
date: 6 Oct 2023
bibliography: paper.bib

# Optional fields if submitting to a AAS journal too, see this blog post:
# https://blog.joss.theoj.org/2018/12/a-new-collaboration-with-aas-publishing
aas-doi: 10.3847/xxxxx
aas-journal: Astrophysical Journal
---

# Summary

The visual classification of astronomical objects requires the use of tools that are simple and easily adaptable to the requirements of the user. In this context, we present `GALAssify`, a graphical tool that allows the user to visually inspect and characterise properties of astronomical objects in a simple way. In addition, `GALAssify` allows the user to save the results of the visual classification into a file using a list of previously defined tags based on the user's interests. `GALAssify` is available on GitLab (<https://gitlab.com/astrogal/GALAssify>).

For many classification problems faced in astrophysics, a graphical interface greatly facilitates the job. In the present work we focus on the classification of galaxies to present a software that helps in a customised and simple way to do this classification. `GALAssify` has been developed in Python using PyQt5 libraries. A priori, it has been initially developed to tackle astrophysical problems but, due to its versatility, it could be easily adapted. For instance, this tool can be used to classify microscopy images from biological studies or be used in any other discipline.

We provide instructions for the installation, usage and basic examples of how to use `GALAssify`. In the `GALAssify`'s GitLab we show the use of `GALAssify` for visual classification of galaxy morphology. However, the user can extrapolate this visual study to any image.

# Statement of need

Python is currently one of the most widely used programming languages in the scientific community, particularly in astrophysics. We have developed `GALAssify` with the aim of facilitating scientists and collaborators the task of visually classify the desired properties of astronomical objects. Additionally, the results can be easily shared between collaborators for analysis and comparisons and can be used for scientific reporting.

`GALAssify` interface was initially designed to perform the galaxy sample selection in the [CAVITY](<https://cavity.caha.es/>) (Calar Alto Void Integral-field Treasury surveY) project. CAVITY is a survey aimed to study galaxies in voids using Integral Field Unit data (Pérez et al. 2024, submitted).

# Usage

`GALAssify` is a tool to classify images from a list of user-defined tags. As an example, in \autoref{fig:fig1}, we show an image of a galaxy from Sloan Digital Sky Survey [SDSS, @2000AJ.120.1579Y] in order to classify their morphology visually. To do so, we provide a list of galaxies, the equatorial coordinates right ascension and declination (ra and dec, respectively), the path to the figures, and the relevant tags for the classification. There are three types of buttons that can be selected, *radiobutton* (only one of the options in the list can be selected), *checkbox* (the desired number of options can be selected) and *comments*. This particular usage has been widely used and tested within the CAVITY collaboration.

In the example shown in \autoref{fig:fig1} we considered a sample of galaxies assignation. The left panel of the figure shows the list of galaxies, which is a table with the following columns: assignation, the name of the galaxy, an icon indicating whether it has been processed, and the coordinates ra and dec for each galaxy.  In the upper part of the right panel, the image of the selected galaxy is displayed. Optionally, this panel can also display the corresponding FITS image of the selected galaxy, specified by the user. In the case of galaxies observed in the SDSS, the algorithm allows the user to provide a path to the figure (if the image is located on their computer) or download it from the SDSS website given its coordinates. The lower part of the right panel is divided into three sections, where we show the different classifying options. The classification of each galaxy can be edited or reset at any time. In the left section we can choose between the main morphological types: elliptical, spiral, irregular, or other in case it does not fit clearly into these categories. In the central section the tags considered in order to do the classification are shown. In our example we considered the following tags: large, tiny, face-on, edge-on, star, calibration, recentre, duplicated, member, HII regions, and finally a pair of tags "Yes" and "No" to choose if we want to consider or exclude the galaxy for our study, respectively. In the lower right section, comments can be added to each of the galaxies. Finally, to save the selection, one can simply click the "Save and next button" or press the "enter" key. The entire classification is saved in a comma-separated values (CSV) file, easily readable with any text editor, spreadsheet program or database manager.

We also provide additional support tools to:

* Download images from SDSS catalogue.
* Create an instructions pdf document to guide the user through the graphical user interface (GUI).

![Interactive GUI: `GALAssify`.\label{fig:fig1}](images/GALAssify.png){ width=100% }

# Documentation

Package documentation is available on the `GALAssify`'s' GitLab page (<https://gitlab.com/astrogal/GALAssify>).

# Software Citations
`GALAssify` should work with `python >= 3.9` and makes use of the following packages:

* Pyqt5 (<https://www.riverbankcomputing.com/static/Docs/PyQt5/>)
* Pandas [@mckinneyprocscipy2010]
* NumPy [@5725236; @2020Natur.585.357H]
* Matplotlib [@Hunter:2007]
* requests (<https://requests.readthedocs.io/en/latest/>)
* Pillow (<https://python-pillow.org/>)
* Astropy [@astropy; @2018AJ.156.123A; @2022ApJ.935.167A]
* pyds9 (<https://github.com/ericmandel/pyds9>)
* PyConsoleMenu (<https://github.com/BaggerFast/PyConsoleMenu>)

Only in case the user wants to display the images in fits format, it is necessary to have ds9 installed on the system.

The code is licensed under MIT License (MIT, <https:/opensource.org/licenses/MIT>) and is available on GitLab (<https://gitlab.com/astrogal/GALAssify>).

# Acknowledgements
We acknowledge financial support by the research projects AYA2017-84897-P, PID2020-113689GB-I00, and PID2020-114414GB-I00,
financed by MCIN/AEI/10.13039/501100011033, the project A-FQM-510-UGR20 financed from FEDER/Junta de Andalucía-Consejería de Transforamción Económica, Industria, Conocimiento y Universidades/Proyecto and by the grants P20_00334 and FQM108, financed by the Junta de Andalucía
(Spain).

M.A-F. acknowledges support from the Emergia program (EMERGIA20_38888) from Junta de Andaluc\'ia.

G.B-C acknowledges financial support from grants PID2020-114461GB-I00
and CEX2021-001131-S, funded by MCIN/AEI/10.13039/501100011033, from
Junta de Andalucía (Spain) grant P20-00880 (FEDER, EU) and from grant
PRE2018-086111 funded by MCIN/AEI/10.13039/501100011033 and by 'ESF
Investing in your future'.

SDP acknowledges financial support from Juan de la Cierva Formación fellowship (FJC2021-047523-I) financed by MCIN/AEI/10.13039/501100011033 and by the European Union `NextGenerationEU'/PRTR, Ministerio de Economía y Competitividad under grants PID2019-107408GB-C44 and PID2020-113689GB-I00, from Junta de Andalucía Excellence Project P18-FR-2664, and SDP is grateful to the Natural Sciences and Engineering Research Council of Canada, the Fonds de Recherche du Québec, and the Canada Foundation for Innovation for funding.

TRL acknowledges support from Juan de la Cierva fellowship (IJC2020-043742-I), financed by MCIN/AEI/10.13039/501100011033.

# References
