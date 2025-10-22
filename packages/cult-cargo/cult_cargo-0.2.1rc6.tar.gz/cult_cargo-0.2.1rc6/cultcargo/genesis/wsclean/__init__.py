from scabha.cargo import Parameter
from typing import Dict, Any

def img_output(imagetype, desc, path, glob=True, must_exist=False):
    # reamp image type to output filename component
    if imagetype == "restored":
        imagetype = "image"
    implicit = f"{{current.prefix}}{path}-{imagetype}.fits"
    if glob:
        implicit = f"=GLOB({implicit})"
    return Parameter(
        info=f"{imagetype.capitalize()} {desc}",
        dtype="List[File]" if glob else "File",
        mkdir=True,
        implicit=implicit,
        must_exist=must_exist)   


def make_stimela_schema(params: Dict[str, Any], inputs: Dict[str, Parameter], outputs: Dict[str, Parameter]):
    """Augments a schema for stimela based on wsclean settings"""

    # predict mode has no outputs
    if params.get('predict'):
        return inputs, outputs

    outputs = outputs.copy()

    # nchan -- if not an integer, assume runtime evaluation and >=2 then
    nchan  = params.get('nchan', 1)
    multichan = params.get('multi.chan', not isinstance(nchan, int) or nchan > 1)
    
    stokes = params.get('pol')

    if stokes is None:
        stokes = ["I"]  # shouldn't matter, multistokes will be False unless explicit
    elif isinstance(stokes, str):
        stokes = stokes.upper()
        # if just IQUV characters, break apart into list
        if all(p in "IQUV" for p in stokes):
            stokes = list(stokes)
        else:
            stokes = [stokes]
    # multi.stokes can be set explicitly
    multistokes = params.get('multi.stokes', False) or len(stokes) > 1

    # ntime -- if not an integer, assume runtime evaluation and >=2 then
    ntime  = params.get('intervals-out', 1)
    multitime = params.get('multi.interval', False) or not isinstance(ntime, int) or ntime > 1

    # make list of image types which will be generated according to settings
    imagetypes = []
    if params.get("make-psf-only", False):
        imagetypes.append("psf")
    else: 
        if not params.get("no-dirty", False):
            imagetypes.append("dirty") 
        if params.get("make-psf", False):
            imagetypes.append("psf")
        imagetypes += ["restored", "residual", "model"]

    # now create outputs for all expected image types
    for imagetype in imagetypes:
        # dirty, restored and psf will be generated whether cleaning or not
        if imagetype in ("dirty", "restored", "psf"):
            must_exist = True
        # residual and model images only generated when cleaning 
        else:
            must_exist = params.get('niter', 0) > 0
        # psf images are not per-Stokes, all others are
        for st in (stokes if imagetype != "psf" else ["I"]):
            # define name/description/filename components for this Stokes 
            if multistokes and imagetype != "psf":
                st_name = f"{st.lower()}."
                st_name1 = f".{st.lower()}"
                st_desc = f"Stokes {st} "
                st_fname = f"-{st}"
            else:
                st_name = st_name1 = st_desc = st_fname = ""
            # now form up outputs
            if multitime:
                if multichan:
                    outputs[f"{imagetype}.{st_name}per-interval.per-band"] = img_output(imagetype,
                        f"{st_desc} images per time interval and band",
                        f"-t[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]{st_fname}", 
                        must_exist=must_exist)
                    outputs[f"{imagetype}.{st_name}per-interval.mfs"] = img_output(imagetype,
                        f"{st_desc} MFS image per time interval",
                        f"-t[0-9][0-9][0-9][0-9]-MFS{st_fname}",
                        must_exist=must_exist)
                else:
                    outputs[f"{imagetype}.{st_name}per-interval"] = img_output(imagetype,
                        f"{st_desc} image per time interval",
                        f"-t[0-9][0-9][0-9][0-9]{st_fname}",
                        must_exist=must_exist)

            else:
                if multichan:
                    outputs[f"{imagetype}.{st_name}per-band"] = img_output(imagetype,
                        f"{st_desc} images per band",
                        f"-[0-9][0-9][0-9][0-9]{st_fname}",
                        must_exist=must_exist)
                    outputs[f"{imagetype}.{st_name}mfs"] = img_output(imagetype,
                        f"{st_desc} MFS image",
                        f"-MFS{st_fname}", glob=False,
                        must_exist=must_exist)
                else:
                    outputs[f"{imagetype}{st_name1}"] = img_output(imagetype,
                        f"{st_desc} image",
                        f"{st_fname}", glob=False,
                        must_exist=must_exist)

    return inputs, outputs
