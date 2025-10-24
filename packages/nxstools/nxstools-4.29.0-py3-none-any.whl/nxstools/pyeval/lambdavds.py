#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2018 DESY, Jan Kotanski <jkotan@mail.desy.de>
#
#    nexdatas is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    nexdatas is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with nexdatas.  If not, see <http://www.gnu.org/licenses/>.
#

"""  pyeval helper functions for lambdavds """

import json

try:
    from . import common
except Exception:
    import common


def nm_triggermode_cb(commonblock, name, triggermode,
                      translations, saveallimages,
                      filepostfix, framenumbers,
                      height, width, opmode,
                      savefilename, filename, entryname,
                      insname="instrument",
                      shortdetpath=None):
    """ code for triggermode_cb  datasource

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param name: component name
    :type name: :obj:`str`
    :param triggermode:  trigger mode
    :type triggermode: :obj:`int` or :obj:`str`
    :param translations: json dictionary with translations
    :type translations: :obj:`str`
    :param saveallimages: save all images flag
    :type saveallimages: :obj:`int` or :obj:`bool`
    :param filepostfix: filename postfix
    :type filepostfix:  :obj:`str`
    :param framenumbers: a number of frames
    :type framenumbers: :obj:`int`
    :param height: height of the image
    :type height: :obj:`int`
    :param width: width of the image
    :type width: :obj:`int`
    :param opmode: operation mode,
                   i.e. 1="int8", 6="int8", 12="int16", 24="int32"
    :type opmode:  :obj:`int`
    :param savefilename: savefilename
    :type savefilename: :obj:`str`
    :param filename: master file name
    :type filename: :obj:`str`
    :param entryname: entry name
    :type entryname: :obj:`str`
    :param shortdetpath: shortdetpath
    :type shortdetpath: :obj:`bool`
    :returns:  triggermode
    :rtype: :obj:`str` or :obj:`int`
    """
    if saveallimages:
        if "__root__" in commonblock.keys():
            root = commonblock["__root__"]
        dtm = {1: "int8", 6: "int8", 12: "int16", 24: "int32"}
        try:
            dtype = dtm[opmode]
        except Exception:
            dtype = "int32"

        modoffsets = json.loads(translations)
        totalheight = 0
        totalwidth = 0
        totalframenumbers = 0
        modsize = len(list(modoffsets.keys()))
        for offset in modoffsets.values():
            totalframenumbers = max(
                totalframenumbers, framenumbers + offset[0])
            totalheight = max(totalheight, height + offset[1])
            totalwidth = max(totalwidth, width + offset[2])
        unlimited = False
        if totalframenumbers == framenumbers:
            unlimited = True

        path = ""
        if filename:
            sfname = (filename).split("/")
            path = sfname[-1].split(".")[0] + "/"
            if shortdetpath is None and \
                    len(sfname) > 1 and sfname[-2] == path[:-1]:
                path = ""
            elif shortdetpath:
                path = ""

        if "__root__" in commonblock.keys():
            root = commonblock["__root__"]
            if root.h5object.__class__.__name__ == "File":
                import nxstools.h5pywriter as nxw
            else:
                import nxstools.h5cppwriter as nxw
        else:
            raise Exception("Writer cannot be found")

        en = root.open(entryname)
        ins = en.open(insname)
        det = ins.open(name)
        npath = "/entry/instrument/detector/data"
        vfl = nxw.virtual_field_layout(
            [totalframenumbers, totalheight, totalwidth], dtype)
        for modulename, offset in modoffsets.items():
            mfilename = path + name + "/" + str(savefilename)
            if modsize != 1:
                mfilename += "_" + modulename
            mfilename += "." + str(filepostfix)
            ef = nxw.target_field_view(
                mfilename, npath, [framenumbers, height, width], dtype)
            if unlimited:
                vfl.add(
                    (slice(None, nxw.unlimited()),
                     slice(offset[1], height + offset[1]),
                     slice(offset[2], width + offset[2])),
                    ef,
                    (slice(None, nxw.unlimited()),
                     slice(None), slice(None)))
            else:
                vfl.add(
                    (slice(offset[0], framenumbers + offset[0]),
                     slice(offset[1], height + offset[1]),
                     slice(offset[2], width + offset[2])),
                    ef,
                    (slice(None), slice(None), slice(None)))
        det.create_virtual_field("data", vfl)
    return triggermode


def savefilename_cb(commonblock, savefilename, savefilename_str):
    """ code for savefilename_cb  datasource

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param savefilename:  name of saved file
    :type savefilename: :obj:`str`
    :param savefilename_str: name of savefilename datasource
    :type savefilename_str: :obj:`str`
    :returns:   name of saved file
    :rtype: :obj:`str`
    """
    return common.blockitem_add(
        commonblock, savefilename_str, savefilename)


def framenumbers_cb(commonblock, framenumbers, framenumbers_str):
    """ code for triggermode_cb  datasource

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param framenumbers:  number of frames
    :type framenumbers: :obj:`str` or :obj:`int`
    :param framenumbers_str: name of framenumbers datasource
    :type framenumbers_str: :obj:`str`
    :returns:  number of frames
    :rtype: :obj:`str` or :obj:`int`
    """
    return common.blockitem_addint(
        commonblock, framenumbers_str, framenumbers)


def triggermode_cb(commonblock, name, triggermode, saveallimages,
                   framesperfile, height, width, opmode,
                   filepostfix, savefilename_str, framenumbers_str,
                   filename_str, entry_str,
                   shortdetpath=None):
    """ code for triggermode_cb  datasource

    :param commonblock: commonblock of nxswriter
    :type commonblock: :obj:`dict`<:obj:`str`, `any`>
    :param name: component name
    :type name: :obj:`str`
    :param triggermode:  trigger mode
    :type triggermode: :obj:`int` or :obj:`str`
    :param saveallimages: save all images flag
    :type saveallimages: :obj:`int` or :obj:`bool`
    :param height: height of the image
    :type height: :obj:`int`
    :param framesperfile: a number of frames per fiel
    :type framesperfile: :obj:`int`
    :param height: height of the image
    :type height: :obj:`int`
    :param width: width of the image
    :type width: :obj:`int`
    :param opmode: operation mode,
                   i.e. 1="int8", 6="int8", 12="int16", 24="int32"
    :type opmode:  :obj:`int`
    :param filepostfix: filename postfix
    :type filepostfix:  :obj:`str`
    :param savefilename_str: name of savefilename datasource
    :type savefilename_str: :obj:`str`
    :param framenumbers_str: name of framenumbers datasource
    :type framenumbers_str: :obj:`str`
    :param filename_str: file name
    :type filename_str: :obj:`str`
    :param entry_str: entry name
    :type entry_str: :obj:`str`
    :param shortdetpath: shortdetpath
    :type shortdetpath: :obj:`bool`
    :returns:  triggermode
    :rtype: :obj:`str` or :obj:`int`
    """

    if saveallimages:

        if "__root__" in commonblock.keys():
            root = commonblock["__root__"]
        filenames = []
        framesnumbers = []
        if savefilename_str in commonblock:
            filenames = commonblock[savefilename_str]
        if framenumbers_str in commonblock:
            framesnumbers = commonblock[framenumbers_str]
        fln = min(len(framesnumbers), len(filenames))

        filesframes = []
        lastfile = None
        totalframenumbers = 0
        for fi in range(fln):
            if lastfile != filenames[fi]:
                filesframes.append((filenames[fi], framesnumbers[fi]))
                lastfile = filenames[fi]
                totalframenumbers += framesnumbers[fi]
        dtm = {1: "int8", 6: "int8", 12: "int16", 24: "int32"}
        try:
            dtype = dtm[opmode]
        except Exception:
            dtype = "int32"

        path = ""
        if filename_str:
            sfname = (filename_str).split("/")
            path = sfname[-1].split(".")[0] + "/"
            if shortdetpath is None and \
                    len(sfname) > 1 and sfname[-2] == path[:-1]:
                path = ""
            elif shortdetpath:
                path = ""

        if "__root__" in commonblock.keys():
            root = commonblock["__root__"]
            if root.h5object.__class__.__name__ == "File":
                import nxstools.h5pywriter as nxw
            else:
                import nxstools.h5cppwriter as nxw
        else:
            raise Exception("Writer cannot be found")

        en = root.open(entry_str)
        ins = en.open("instrument")
        det = ins.open(name)
        npath = "/entry/instrument/detector/data"

        vfl = nxw.virtual_field_layout(
            [totalframenumbers, height, width], dtype)

        foffset = 0
        for savefilename, framenumbers in filesframes:
            if framenumbers > 0 and framesperfile > 10:
                nbfiles = (framenumbers - 1) // framesperfile + 1
                lastfilenbframes = framenumbers - (nbfiles - 1) * framesperfile
            elif framenumbers > 0:
                nbfiles = 1
                lastfilenbframes = framenumbers
            else:
                nbfiles = 0
                lastfilenbframes = 0

            if nbfiles > 0:
                for nbf in range(0, nbfiles):
                    if framenumbers > framesperfile and framesperfile > 10:
                        connector = "_part%05d." % nbf
                    else:
                        connector = "."
                    filename = path + name + "/" + str(savefilename) \
                        + connector + str(filepostfix)
                    ln = framesperfile if nbf + 1 != nbfiles \
                        else lastfilenbframes
                    ef = nxw.target_field_view(
                        filename, npath, [ln, height, width], dtype)
                    vfl[
                        (foffset + nbf * framesperfile):
                        (foffset + nbf * framesperfile + ln), :, :] = ef
                foffset += framenumbers
        det.create_virtual_field("data", vfl)
    return triggermode
