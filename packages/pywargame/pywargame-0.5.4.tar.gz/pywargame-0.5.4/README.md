# Python utilities for Wargames 

This is a collection of various utilities to make things for Computer
Aided Wargaming (CAW). 

## Content

- [`pywargame`](pywargame) Top of package 
  - [`common`](pywargame/common) Common utilities used by other code.
  - [`vassal`](pywargame/vassal) Read or write 
    [VASSAL](https://vassalengine.org)
    ([GitHub](https://github.com/vassalengine/vassal)) modules,
    including
    - merging modules and extensions,
    - patching modules with a Python script, and 
    - inspecting content of save and log files.
  - [`cyberboard`](pywargame/cyberboard) Read
    [CyberBoard](http://cyberboard.norsesoft.com/)
    ([GitHub](https://github.com/CyberBoardPBEM/cbwindows)) GameBox
    and scenario files.
  - [`zuntzu`](pywargame/zuntzu) Convert [ZunTzu](https://zuntzu.com)
    ([GitHub](https://github.com/ZunTzu-Software/ZunTzu)) GameBox to
    VASSAL module.
  - [`latex`](pywargame/latex) Create (draft) VASSAL module from LaTeX
    sources using the package
    [`wargame`](https://gitlab.com/wargames_tex/wargame_tex).
  

## Changes 

- 0.5.3 
  - New script `vsavzero.py` to change users, passwords, and sides in
    Vassal save (`.vsav`) or logs (`.vlog`).  This script circumvents
    these measures in Vassal. 
  - In `LaTeXExporter`, avoid file names that may offend Windows
    sensibilities - sigh!
- 0.5.2
  - Fix to more f-strings
- 0.5.1
  - LaTeX exporter adds _Nearest unmoved unit_ and _Nearest unresolved
    combat_ tool-bar buttons. 
  - Fix to more f-strings
- 0.5.0
  - Added `ChangeProperty` sub-element of `GlobalProperty`
  - Added `MoveCamera` sub-element of `Map` 
  - Fix to `gsnexport.py` to call proper main function
  - Fix to some f-strings.
- 0.4.3 
  - Update for CI/CD
- 0.4.2 
  - Some fixes for imports 
  - Scripts done as entry points in `pip` install 
- 0.4.1 
  - Some fixes to `pip` releases 
- 0.4.0
  - First release via `pip` 
- 2nd of February, 2024
  - Fix problem with background of maps exported from CyberBoard
    gamebox.  Thanks to @zovs66 for pointing this out. 
  - `cyberboard.py` now supports file format version 4+ (but not 5, as
    that will introduce the saving for features and other stuff). 
    
## Scripts 

- [`vslmerge.py`](pywargame/vassal/merge.py) merges VASSAL modules and
  extensions together into one module.  This is work in progress.
  Please report any problems you see.
  
- [`vmodpatch.py`](pywargame/vassal/patch.py) patches a VASSAL modules
  by running a Python script on it.  The input module file is
  overwritten.
  
- [`vsavdump.py`](pywargame/vassal/dumpsave.py) dumps the content of a
  VASSAL save or log file to standard output.
  
- [`gbxextract.py`](pywargame/cyberboard/gbxext.py) reads in a
  CyberBoard GameBox file (`.gbx`) and writes out a ZIP file with
  images and a JSON file with information about the GameBox and the
  images.
  
  Pieces (units and markers) are saved as PNGs, while the boards are
  saves as SVGs. 
  
- [`gsnextract.py`](pywargame/cyberboard/gsnext.py) reads in a
  CyberBoard Scenario file (`.gsn`) and writes out a ZIP file with
  images and a JSON file with information about the Scenario, GameBox,
  and the images.
  
  Pieces (units and markers) are saved as PNGs, while the boards are
  saves as SVGs. 
  
- [`gsnexport.py`](pywargame/cyberboard/gsnexp.py) reads in a
  CyberBoard Scenario file (`.gsn`) and generates a (draft) VASSAL
  module. A Python script can be supplied to patch up the module.
  
- [`ztexport.py`](pywargame/zuntzu/ztexp.py) reads in a ZunTzu game
  box file (`.ztb`) and generates a (draft) VASSAL module. A Python
  script can be supplied to patch up the module.
  
- [`wgexport.py`](pywargame/latex/main.py) reads in a PDF and JSON
  file created from LaTeX sources using the
  [`wargame`](https://gitlab.com/wargames_tex/wargame_tex) package,
  and generates a (draft) VASSAL module. A Python script can be
  supplied to patch up the module.
  
## Installation via `pip` 

Just do 

```
$ pip install pywargame
```

## Download as scripts

You can get the scripts in ZIP file 

- [artifacts.zip][]

or individually 

- [vassal.py][]
- [vslmerge.py][]
- [vmodpatch.py][]
- [vsavdump.py][]
- [cyberboard.py][]
- [gbxextract.py][]
- [gsnextract.py][]
- [gsnexport.py][]
- [ztexport.py][]
- [wgexport.py][]
- [requirements.txt][]
- [README.md][]

or [browse][] the files.  Note that these scripts are _standalone_ and
does not require a module installation of `pywargame`. 

## Build 

You need 

- `numpy` - some numerics
- `pillow` - PNG image creation 
- `svgwrite` - SVG image creation
- `wand` - SVG rendering to PNG

for these scripts.  Do 

    pip install -r requirements.txt 
    
to ensure you have those installed. 

To generate these scripts, do

    cd pywargame/vassal     && ./collect.py
    cd pywargame/vassal     && ./collectmrg.py
    cd pywargame/vassal     && ./collectpatch.py
    cd pywargame/vassal     && ./collectdump.py
    cd pywargame/cyberboard && ./collect.py
    cd pywargame/cyberboard && ./collectgbxext.py
    cd pywargame/cyberboard && ./collectgsnext.py
    cd pywargame/cyberboard && ./collectgsnexp.py
    cd pywargame/zuntzu     && ./collect.py
    cd pywargame/latex      && ./collect.py
    cp pywargame/vassal/vassal.py .
    cp pywargame/vassal/vslmerge.py .
    cp pywargame/vassal/vmodpatch.py .
    cp pywargame/vassal/vsavdump.py .
    cp pywargame/cyberboard/gbxextract.py .
    cp pywargame/cyberboard/gsnextract.py .
    cp pywargame/cyberboard/gsnexport.py .
    cp pywargame/zuntzu/ztexport.py .
    cp pywargame/latex/wgexport.py .     
    
or simply, on most modern operating systems, 

    make 
    
### Usage 

    ./vslmerge.py <VMOD and VMDX files> [<OPTIONS>]
    ./vmodpath.py <VMOD> <SCRIPT> [<OPTIONS>]
    ./vsavdump.py <VSAV or VLOG> [<OPTIONS>]
    ./gbxextract.py <GBX> [<OPTIONS>]
    ./gsnextract.py <GSN> [<OPTIONS>]
    ./gsnexport.py <GSN> [<OPTIONS>]
    ./ztexport.py <ZTB> [<OPTIONS>]
    ./wgexport.py <PDF> <JSON> [<OPTIONS>]
    
    
Pass `-h` or `--help` as an option for a summery of available options 

### Note on `vslmerge.py` 

The _first_ input file should be a module (_not_ an extension). 

The script is _work-in-progress_ - please report any problems you may
have. 

### Note on `gsnexport.py`

Converting a CyberBoard scenario to a VASSAL module may take a _long_
time.  If you are not sure anything is happening, try passing the
option `-V` (or `--verbose`) to see what is going on.  The speed of
the conversion depends a lot on the graphics used in the game box. 

The default is to add pieces in their starting positions directly in
the module.  However, with the option `-S` the initial placement of
units will be put in a save file (`.vsav`).  This is useful if there
are two or more scenario files associated with a game box, and you
want to merge all these into a single module. 

The script can only convert one gamebox and scenario at a time.  As
mentioned above, without the `-S` option, all pieces are placed
directly in their starting position.  This makes for a nice standalone
module.   However, if the game box as two or more scenario files
associated with it, we should add the option `-S` and convert each
scenario by it self.   The generated module files - one for each
scenario - can then be merged into one using the
[`vslmerge.py`](vassal/merge.py) script. 

CyberBoard game boxes and scenarios made with CyberBoard prior to
version 3.0 are _not_ supported.  You may have some luck  first opening
the game box and then the scenario with `CBDesign.exe` and
`CBPlay.exe`, respectively, and saving anew.  Of course, this requires
an installation of CyberBoard (on Linux, use
[wine](https://winehq.org)). 

Some CyberBoard game boxes and scenarios do not define the title or
version of the game.  In that case, you may pass the options `--title`
and `--version` to set the title or version, respectively. 

If the game box file (`.gbx`) cannot directly be found, use the option
`--gamebox` to specify the game box file. 

Another common problem with Cyberboard scenarios is that they do not
specify a starting map, or that the starting map is not the actual
board.  In that case, one can write a small Python script that patches
up the VASSAL module.  For example, the file
[`misc/PortStanley.py`](misc/PortStanley.py) will patch up the
scenario [_Port
Stanley_](http://limeyyankgames.co.uk/cyberboard/port-stanley) game
box, so that the VASSAL module will show the right board.  Other
options for this patch script could be to change the piece names to
something more appropriate than the auto-generated names, add charts
and tables, set the splash image, and so on.  Please refer to the
[`vassal`](vassal) module API for more. 

If you find that the board SVGs are not rendering as expected, you may
want to run `gsnextract.py` first, and in turn run `gsnexport.py` as 

    ./gsnexport.py <ZIP FILE> [<OPTIONS>]
    
possibly after editing SVGs 

    ./gsnextract.py <GSN FILE> [<OPTIONS>]
    unzip <ZIP FILE> board_0_0,svg 
    <Edit board_0_0.svg> # E.g. using Inkscape
    zip -u <ZIP FILE> board_0_0.png 
    ./gsnexport.py <ZIP FILE> [<OPTIONS>]

A good SVG editor is [Inkscape](https://inkscape.org). 

### Note on `ztexport.py`

Converting a ZunTzu scenario to a VASSAL module may take a _some_
time.  If you are not sure anything is happening, try passing the
option `-V` (or `--verbose`) to see what is going on.  The speed of
the conversion depends a lot on the graphics used in the game box. 

If you get the error `cache resources exhausted` try lowering the
resolution (`-r`). 

If the ZunTzu gamebox does not use selectable boards, pass the option
`-a` to generate maps for all defined maps.  Otherwise, the script
will assume that all maps are alternatives for the default map. 

The generated VASSAL module is pretty close to the input, but should
be considered a draft.  Use the VASSAL editor to flesh out details.
For example, ZunTzu gameboxes has no notion of "sides" of play. 

The generated module contains the scenarios that are in the gamebox.
There's no provision for converting other saves.  However, you can
always add your favourite save the to game box, before conversion,
using your favourite ZIP-file manager. 

Terrain tiles (or counters) can be selected by Ctrl-click. 

The script is not omnipotent, and may fail on some ZunTzu gameboxes.
Open an Issue against this project, providing all the necessary
details, if that happens to you. 

## API 

The API documentation is available
[here](https://wargames_tex.gitlab.io/pywargame).

The module [`vassal`](vassal) allows one to generate a VASSAL module
programmatically, or to read in a VASSAL module and manipulate it
programmatically.  It also has features for defining a _save_
(`.vsav`) file programmatically.

The module [`cyberboard`](cyberboarxd) allows one to read in a
CyberBoard GameBox file and retrieve information from it - such as
piece and board images. 

## License 

This is distributed on the GPL-3 license. 

## A word about copyright 

Caveat: _I am not a lawyer_.

Note, if you use these tools to convert a CyberBoard or ZunTzu GameBox
to say a VASSAL module, then you are creating a derived product from
the originally copyrighted product (the GameBox).  Thus, if you want
to distribute, even to friends, the generated VASSAL module, you
_must_ make sure that you are licensed to do so.

If the GameBox is licensed under an 
[_Open Source_](https://opensource.org/) license, like
[Creative-Commons Attribution, Share-Alike](https://creativecommons.org/licenses/by-sa/4.0/), GPL-3,
or similar, you are explicitly permitted to distribute your derived
work. 

If, on the other hand, the license states _all rights reserved_ then
you cannot redistribute without explicit permission by the copyright
holder.

If no license is explicitly given, then the default is akin to 
_all rights reserved_. 

Note, if the converted data contains graphics or the like, it may not
be the module developer that holds the copyright to the materials.
The developer may (or may not) have obtained permission to distribute
the materials, but that does not imply that permission is given to
third party. 

However, what is copyrightable and what isn't [is not
obvious](https://boardgamegeek.com/thread/493249/).  Only _original_
and _artistic_ forms of _expression_ can be copyrighted.  Ideas, and
similar, cannot.  That means that the mechanics of a game cannot be
copyrighted.  The exact graphics and phrasing of the rules _can_.
However, if you make distinctive new graphics and rephrase the rules,
it is _not_ subject the original copyright.  Note, however, that it is
not enough to change a colour or font here or there - it has to be
_original_.

Note that you are free to make your own copy, as long as you obtained
the original legally.  Copyright only matters if you plan to
_redistribute_, irrespective of whether or not you monetise the
redistribution, or if the redistribution is private or public.

    
  
[artifacts.zip]: https://gitlab.com/wargames_tex/pywargame/-/jobs/artifacts/master/download?job=dist
[vassal.py]: https://gitlab.com/wargames_tex/pywargame/-/jobs/artifacts/master/file/public/vassal.py?job=dist
[vslmerge.py]: https://gitlab.com/wargames_tex/pywargame/-/jobs/artifacts/master/file/public/vslmerge.py?job=dist
[vmodpatch.py]: https://gitlab.com/wargames_tex/pywargame/-/jobs/artifacts/master/file/public/vmodpatch.py?job=dist
[vsavdump.py]: https://gitlab.com/wargames_tex/pywargame/-/jobs/artifacts/master/file/public/vsavdump.py?job=dist
[cyberboard.py]: https://gitlab.com/wargames_tex/pywargame/-/jobs/artifacts/master/file/public/cyberboard.py?job=dist
[gbxextract.py]: https://gitlab.com/wargames_tex/pywargame/-/jobs/artifacts/master/file/public/gbxextract.py?job=dist
[gsnextract.py]: https://gitlab.com/wargames_tex/pywargame/-/jobs/artifacts/master/file/public/gsnextract.py?job=dist
[gsnexport.py]: https://gitlab.com/wargames_tex/pywargame/-/jobs/artifacts/master/file/public/gsnexport.py?job=dist
[ztexport.py]: https://gitlab.com/wargames_tex/pywargame/-/jobs/artifacts/master/file/public/ztexport.py?job=dist
[wgexport.py]: https://gitlab.com/wargames_tex/pywargame/-/jobs/artifacts/master/file/public/wgexport.py?job=dist
[requirements.txt]: https://gitlab.com/wargames_tex/pywargame/-/jobs/artifacts/master/file/public/requirements.txt?job=dist
[README.md]: https://gitlab.com/wargames_tex/pywargame/-/jobs/artifacts/master/file/public/README.md?job=dist
[browse]: https://gitlab.com/wargames_tex/pywargame/-/jobs/artifacts/master/browse/public?job=dist



