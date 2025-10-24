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

""" Provides h5py file writer """

import h5py
import numpy as np
import os
import sys
import io

from . import filewriter
# from .Types import nptype

try:
    sver = h5py.__version__.split(".", 2)
    h5maj = int(sver[0])
    h5min = int(sver[1])
    h5ver = h5maj * 1000 + h5min
except Exception:
    h5ver = 1000


if sys.version_info > (3,):
    unicode = str
else:
    bytes = str


def _slice2selection(t, shape):
    """ converts slice(s) to selection

    :param t: slice tuple
    :type t: :obj:`tuple`
    :param shape: field shape
    :type shape: :obj:`list` < :obj:`int` >
    :returns: hyperslab selection
    :rtype: :class:`h5cpp.dataspace.Hyperslab`
    """
    if isinstance(t, filewriter.FTHyperslab):
        offset = list(t.offset or [])
        block = list(t.block or [])
        count = list(t.count or [])
        stride = list(t.stride or [])
        slices = []
        for dm, sz in enumerate(shape):
            if len(offset) > dm:
                if offset[dm] is None:
                    offset[dm] = 0
            else:
                offset.append(0)
            if len(block) > dm:
                if block[dm] is None:
                    block[dm] = 1
            else:
                block.append(1)
            if len(count) > dm:
                if count[dm] is None:
                    count[dm] = sz
            else:
                count.append(sz)
            if len(stride) > dm:
                if stride[dm] is None:
                    stride[dm] = 1
            else:
                stride.append(1)
            slices.append(
                h5py.MultiBlockSlice(
                    start=offset[dm], count=count[dm],
                    stride=stride[dm], block=block[dm]))
        return tuple(slices)
    return t


def unlimited_selection(sel, shape):
    """ checks if hyperslab is unlimited

    :param sel: hyperslab selection
    :type sel: :class:`filewriter.FTHyperslab`
    :param shape: give shape
    :type shape: :obj:`list`
    :returns: if hyperslab is unlimited list
    :rtype: :obj:`list` <:obj:`bool`>
    """
    res = None
    if isinstance(sel, tuple):
        res = []
        for sl in sel:
            if hasattr(sl, "stop"):
                res.append(True if sl.stop in [unlimited()] else False)
            elif hasattr(sl, "count"):
                res.append(True if sl.count in [unlimited()] else False)
            else:
                res.append(True if sl in [unlimited()] else False)

    elif hasattr(sel, "count"):
        res = []
        for ct in sel.count():
            res.append(True if ct in [unlimited()] else False)
    elif isinstance(sel, slice):
        res = [True if sel.stop in [unlimited()] else False]

    elif sel in [unlimited()]:
        res = [True]
    lsh = len(shape)
    lct = len(res)
    ln = max(lsh, lct)
    if res and any(t is True for t in res):
        slices = []
        for ii in range(ln):
            offset = 0
            # block = 1
            # stride = 1
            if ii < lsh:
                count = shape[ii]
            else:
                count = 1
            if ii < lct and res[ii]:
                count = unlimited()
            # print("Hyperslab %s %s %s %s" % (offset, block, count, stride))
            slices.append(
                slice(offset, count, None)
                # h5py.MultiBlockSlice(
                #     start=offset, count=count,
                #     stride=stride, block=block)
            )
        return tuple(slices)
    else:
        return None


def _selection2slice(t, shape):
    """ converts selection to slice(s)

    :param t: slice tuple
    :type t: :obj:`tuple`
    :return shape: field shape
    :type shape: :obj:`list` < :obj:`int` >
    :returns: tuple of slices
    :rtype: :obj:`tuple`<>
    """
    if isinstance(t, filewriter.FTHyperslab):
        offset = list(t.offset or [])
        block = list(t.block or [])
        count = list(t.count or [])
        stride = list(t.stride or [])
        slices = []
        for dm, sz in enumerate(shape):
            if len(offset) > dm:
                if offset[dm] is None:
                    offset[dm] = 0
            else:
                offset.append(0)
            if len(block) > dm:
                if block[dm] is None:
                    block[dm] = 1
            else:
                block.append(1)
            if len(count) > dm:
                if count[dm] is None:
                    count[dm] = sz
            else:
                count.append(sz)
            if len(stride) > dm:
                if stride[dm] is None:
                    stride[dm] = 1
            else:
                block.append(1)
            if len(stride) > dm:
                if stride[dm] is None:
                    stride[dm] = 1
            else:
                stride.append(1)
            if block[dm] == 1 and count[dm] == 1 and stride[dm] == 1:
                slices.append(offset[dm])
            elif stride[dm] == 1:
                slices.append(slice(
                    offset[dm], offset[dm] + block[dm] * count[dm], None))
            elif stride[dm] != 1 and block[dm] == 1:
                slices.append(slice(offset[dm],
                                    offset[dm] + count[dm] * stride[dm],
                                    stride[dm]))
            elif stride[dm] != 1 and count[dm] == 1:
                slices.append(slice(offset[dm],
                                    offset[dm] + block[dm] * stride[dm],
                                    stride[dm]))
            else:
                slices.append(Ellipsis)
        return tuple(slices)
    return t


def nptype(dtype):
    """ converts to numpy types

    :param dtype: h5 writer type type
    :type dtype: :obj:`str`
    :returns: nupy type
    :rtype: :obj:`str`
    """
    if str(dtype) in ['string', b'string']:
        return 'str'
    return dtype


def is_image_file_supported():
    """ provides if loading of image files are supported

    :retruns: if loading of image files are supported
    :rtype: :obj:`bool`
    """
    return h5ver >= 2009


def is_vds_supported():
    """ provides if VDS are supported

    :retruns: if VDS are supported
    :rtype: :obj:`bool`
    """
    return h5ver >= 2009


def is_mbs_supported():
    """ provides if MultiBlockSlice are supported

    :retruns: if MultiBlockSlice are supported
    :rtype: :obj:`bool`
    """
    return h5ver >= 3000


def is_unlimited_vds_supported():
    """ provides if unlimited vds are supported

    :retruns: if unlimited vds are supported
    :rtype: :obj:`bool`
    """
    return h5ver >= 3000


def is_strings_as_bytes():
    """ provides if string read to bytes

    :retruns: if string read to bytes
    :rtype: :obj:`bool`
    """
    return h5ver >= 3000


def unlimited(parent=None):
    """ return dataspace UNLIMITED variable for the current writer module

    :param parent: parent object
    :type parent: :class:`FTObject`
    :returns:  dataspace UNLIMITED variable
    :rtype: :class:`h5py.h5s.UNLIMITED`
    """
    try:
        return h5py.h5s.UNLIMITED
    except Exception:
        return h5py.UNLIMITED


def load_file(membuffer, filename=None, readonly=False, **pars):
    """ load a file from memory byte buffer

    :param membuffer: memory buffer
    :type membuffer: :obj:`bytes` or :obj:`io.BytesIO`
    :param filename: file name
    :type filename: :obj:`str`
    :param readonly: readonly flag
    :type readonly: :obj:`bool`
    :param pars: parameters
    :type pars: :obj:`dict` < :obj:`str`, :obj:`str`>
    :returns: file object
    :rtype: :class:`H5PYFile`
    """
    if not is_image_file_supported():
        raise Exception("Loading a file from a memory buffer not supported")
    if not hasattr(membuffer, 'read') or not hasattr(membuffer, 'seek'):
        if hasattr(membuffer, "tobytes"):
            membuffer = membuffer.tobytes()
        membuffer = io.BytesIO(membuffer)
    if readonly:
        fobj = h5py.File(membuffer, "r", **pars)
    else:
        fobj = h5py.File(membuffer, "r+", **pars)
    return H5PYFile(fobj, filename)


def open_file(filename, readonly=False, **pars):
    """ open the new file

    :param filename: file name
    :type filename: :obj:`str`
    :param readonly: readonly flag
    :type readonly: :obj:`bool`
    :param pars: parameters
    :type pars: :obj:`dict` < :obj:`str`, :obj:`str`>
    :returns: file object
    :rtype: :class:`H5PYFile`
    """
    if readonly:
        return H5PYFile(h5py.File(filename, "r", **pars), filename)
    else:
        return H5PYFile(h5py.File(filename, "r+", **pars), filename)


def create_file(filename, overwrite=False, **pars):
    """ create a new file

    :param filename: file name
    :type filename: :obj:`str`
    :param overwrite: overwrite flag
    :type overwrite: :obj:`bool`
    :param pars: parameters
    :type pars: :obj:`dict` < :obj:`str`, :obj:`str`>
    :returns: file object
    :rtype: :class:`H5PYFile`
    """
    fl = h5py.File(filename, "w" if overwrite else "w-", **pars)
    fl.attrs["file_time"] = unicode(H5PYFile.currenttime())
    fl.attrs["HDF5_Version"] = str(h5py.version.hdf5_version)
    fl.attrs["NX_class"] = u"NXroot"
    # fl.attrs["NeXus_version"] = u"4.3.0"
    fl.attrs["file_name"] = unicode(filename)
    fl.attrs["file_update_time"] = unicode(H5PYFile.currenttime())
    return H5PYFile(fl, filename)


def link(target, parent, name):
    """ create link

    :param target: file name
    :type target: :obj:`str`
    :param parent: parent object
    :type parent: :class:`FTObject`
    :param name: link name
    :type name: :obj:`str`
    :returns: link object
    :rtype: :class:`H5PYLink`
    """
    localfname = H5PYLink.getfilename(parent)
    if ":/" in target:
        filename, path = target.split(":/")

        if os.path.abspath(filename) != os.path.abspath(localfname):
            parent.h5object[name] = h5py.ExternalLink(filename, path)
        else:
            parent.h5object[name] = h5py.SoftLink(path)

    else:
        parent.h5object[name] = h5py.SoftLink(target)
    return H5PYLink(
        parent.h5object.get(name, getlink=True), parent).setname(name)


def get_links(parent):
    """ get links

    :param parent: parent object
    :type parent: :class:`FTObject`
    :returns: list of link objects
    :returns: link object
    :rtype: :obj: `list` <:class:`H5PYLink`>
    """

    return [H5PYLink(
        parent.h5object.get(name, getlink=True), parent).setname(name)
        for name in parent.names()]


def data_filter(filterid=None, name=None, options=None, availability=None,
                shuffle=None, rate=None):
    """ create data filter

    :param filterid: hdf5 filter id
    :type filterid: :obj:`int`
    :param name: filter name
    :type name: :obj:`str`
    :param options: filter cd values
    :type options: :obj:`tuple` <:obj:`int`>
    :param availability: filter availability i.e. 'optional' or 'mandatory'
    :type availability: :obj:`str`
    :param shuffle: filter shuffle
    :type shuffle: :obj:`bool`
    :param rate: filter shuffle
    :type rate: :obj:`bool`
    :returns: deflate filter object
    :rtype: :class:`H5PYDataFilter`
    """
    dtf = H5PYDataFilter()
    if filterid:
        dtf.filterid = filterid
    if name:
        dtf.name = name
    if shuffle:
        dtf.shuffle = shuffle
    if rate:
        dtf.rate = rate
    if options:
        dtf.options = options
    if availability:
        dtf.availability = availability
    return dtf


def deflate_filter(rate=None, shuffle=None, availability=None):
    """ create data filter

    :param rate: filter shuffle
    :type rate: :obj:`bool`
    :param shuffle: filter shuffle
    :type shuffle: :obj:`bool`
    :returns: deflate filter object
    :rtype: :class:`H5PYDataFilter`
    """
    dtf = H5PYDataFilter()
    dtf.filterid = 1
    dtf.name = "deflate"
    if shuffle:
        dtf.shuffle = shuffle
    dtf.rate = rate or 2
    if availability:
        dtf.availability = availability
    return dtf


def target_field_view(filename, fieldpath, shape,
                      dtype=None, maxshape=None):
    """ create target field view for VDS

    :param filename: file name
    :type filename: :obj:`str`
    :param fieldpath: nexus field path
    :type fieldpath: :obj:`str`
    :param shape: shape
    :type shape: :obj:`list` < :obj:`int` >
    :param dtype: attribute type
    :type dtype: :obj:`str`
    :param maxshape: shape
    :type maxshape: :obj:`list` < :obj:`int` >
    :returns: target field view object
    :rtype: :class:`FTTargetFieldView`
    """
    if not is_vds_supported():
        raise Exception("VDS not supported")
    if shape:
        maxshape = maxshape or [None for _ in shape]
    vs = h5py.VirtualSource(
        filename, fieldpath,
        tuple(shape or []), dtype, tuple(maxshape or []))
    return H5PYTargetFieldView(vs, tuple(shape or []))


def virtual_field_layout(shape, dtype, maxshape=None, parent=None):
    """ creates a virtual field layout for a VDS file

    :param shape: shape
    :type shape: :obj:`list` < :obj:`int` >
    :param dtype: attribute type
    :type dtype: :obj:`str`
    :param maxshape: shape
    :type maxshape: :obj:`list` < :obj:`int` >
    :returns: virtual layout
    :rtype: :class:`FTVirtualFieldLayout`
    """
    if not is_vds_supported():
        raise Exception("VDS not supported")
    maxshape = maxshape or [None for _ in shape]
    return H5PYVirtualFieldLayout(
        h5py.VirtualLayout(tuple(shape), dtype, tuple(maxshape or [])),
        tuple(shape), dtype, tparent=parent
    )


class H5PYFile(filewriter.FTFile):

    """ file tree file
    """

    def __init__(self, h5object, filename):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param filename:  file name
        :type filename: :obj:`str`
        """
        filewriter.FTFile.__init__(self, h5object, filename)
        #: (:obj:`str`) object nexus path
        self.path = None

    def root(self):
        """ root object

        :returns: parent object
        :rtype: :class:`H5PYGroup`
        """
        g = H5PYGroup(self._h5object, self)
        g.name = u"/"
        g.path = u"/"
        return g

    def flush(self):
        """ flash the data
        """
        if self._h5object.mode in ["r+"]:
            self._h5object.attrs["file_update_time"] = \
                unicode(self.currenttime())
        return self._h5object.flush()

    def close(self):
        """ close file
        """
        filewriter.FTFile.close(self)
        if self._h5object.mode in ["r+"]:
            self._h5object.attrs["file_update_time"] = \
                unicode(self.currenttime())
        return self._h5object.close()

    @property
    def is_valid(self):
        """ check if group is valid

        :returns: valid flag
        :rtype: :obj:`bool`
        """
        return self._h5object.name is not None

    @property
    def readonly(self):
        """ check if file is readonly

        :returns: readonly flag
        :rtype: :obj:`bool`
        """
        isvalid = self.is_valid
        return self._h5object.mode in ["r"] if isvalid else None

    def reopen(self, readonly=False, swmr=False, libver=None):
        """ reopen file

        :param readonly: readonly flag
        :type readonly: :obj:`bool`
        :param swmr: swmr flag
        :type swmr: :obj:`bool`
        :param libver:  library version, default: 'latest'
        :type libver: :obj:`str`
        """
        libver = libver or 'latest'
        isvalid = self.is_valid
        lreadonly = self._h5object.mode in ["r"] if isvalid else None

        if (not isvalid or lreadonly != readonly or
           self._h5object.libver != libver):
            if isvalid:
                self.close()
            self._h5object = h5py.File(
                self.name, "r" if readonly else "r+", libver=libver)
            filewriter.FTFile.reopen(self)
        if hasattr(self._h5object, "swmr_mode") and swmr:
            self._h5object.swmr_mode = swmr
        elif swmr:
            raise Exception("SWMR not supported")

    def hasswmr(self):
        """ if has swmr_mode

        :returns: has swmr_mode
        :rtype: :obj:`bool`
        """
        return hasattr(self._h5object, "swmr_mode")


class H5PYGroup(filewriter.FTGroup):

    """ file tree group
    """

    def __init__(self, h5object, tparent=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param tparent: tree parent
        :type tparent: :obj:`FTObject`
        """
        filewriter.FTGroup.__init__(self, h5object, tparent)
        self.path = u""
        self.name = None
        if hasattr(h5object, "name"):
            name = h5object.name
            self.name = name.split("/")[-1]
            if tparent and tparent.path:
                if tparent.path == u"/":
                    self.path = u"/" + self.name
                else:
                    self.path = tparent.path + u"/" + self.name
            if ":" not in self.name:
                if u"NX_class" in h5object.attrs:
                    clss = filewriter.first(h5object.attrs["NX_class"])
                else:
                    clss = ""
                if clss:
                    self.path += u":" + str(clss)

    def open(self, name):
        """ open a file tree element

        :param name: element name
        :type name: :obj:`str`
        :returns: file tree object
        :rtype: :class:`FTObject`
        """
        if name not in self._h5object:
            at = self._h5object.attrs[name]
            if at is None:
                raise Exception("Empty attriibute")
            return H5PYAttribute((self._h5object.attrs, name), self)

        itm = self._h5object.get(name)
        if isinstance(itm, h5py._hl.dataset.Dataset):
            el = H5PYField(itm, self)
        elif isinstance(itm, h5py._hl.group.Group):
            el = H5PYGroup(itm, self)
        else:
            itm = self._h5object.get(name, getlink=True)
            el = H5PYLink(itm, self).setname(name)
        return el

    def open_link(self, name):
        """ open a file tree element as link

        :param name: element name
        :type name: :obj:`str`
        :returns: file tree object
        :rtype: :class:`FTObject`
        """
        itm = self._h5object.get(name, getlink=True)
        return H5PYLink(itm, self).setname(name)

    class H5PYGroupIter(object):

        def __init__(self, group):
            """ constructor

            :param group: group object
            :type manager: :obj:`H5PYGroup`
            """

            self.__group = group
            self.__names = sorted(self.__group._h5object.keys()) or []

        def __next__(self):
            """ the next attribute

            :returns: attribute object
            :rtype: :class:`FTAtribute`
            """
            if self.__names:
                return self.__group.open(self.__names.pop(0))
            else:
                raise StopIteration()

        next = __next__

        def __iter__(self):
            """ attribute iterator

            :returns: attribute iterator
            :rtype: :class:`H5PYAttrIter`
            """
            return self

    def __iter__(self):
        """ attribute iterator

        :returns: attribute iterator
        :rtype: :class:`H5PYAttrIter`
        """
        return self.H5PYGroupIter(self)

    def close(self):
        """ close group
        """
        filewriter.FTGroup.close(self)
        self._h5object = None

    def create_group(self, n, nxclass=""):
        """ open a file tree element

        :param n: group name
        :type n: :obj:`str`
        :param nxclass: group type
        :type nxclass: :obj:`str`
        :returns: file tree group
        :rtype: :class:`H5PYGroup`
        """
        grp = self._h5object.create_group(n)
        if nxclass:
            grp.attrs["NX_class"] = unicode(nxclass)
        return H5PYGroup(grp, self)

    def create_virtual_field(self, name, layout, fillvalue=None):
        """ creates a virtual filed tres element

        :param name: group name
        :type name: :obj:`str`
        :param layout: virual field layout
        :type layout: :class:`H5PYFieldLayout`
        :param fillvalue:  fill value
        :type fillvalue: :obj:`int`
        """
        if not is_vds_supported():
            raise Exception("VDS not supported")
        return H5PYField(
            self._h5object.create_virtual_dataset(
                name, layout._h5object, fillvalue),
            self)

    def create_field(self, name, type_code,
                     shape=None, chunk=None, dfilter=None):
        """ creates a field tree element

        :param name: group name
        :type name: :obj:`str`
        :param type_code: nexus field type
        :type type_code: :obj:`str`
        :param shape: shape
        :type shape: :obj:`list` < :obj:`int` >
        :param chunk: chunk
        :type chunk: :obj:`list` < :obj:`int` >
        :param dfilter: filter deflater
        :type dfilter: :class:`H5PYDataFilter`
        :returns: file tree field
        :rtype: :class:`H5PYField`
        """
        if type_code in ['string', b'string']:
            type_code = h5py.special_dtype(vlen=unicode)
            # type_code = h5py.special_dtype(vlen=bytes)
        if type_code == h5py.special_dtype(vlen=unicode) and \
           shape is None and chunk is None:
            return H5PYField(
                self._h5object.create_dataset(name,  (), type_code), self)

        shape = shape or [1]
        f = None
        mshape = [None for _ in shape] or (None,)
        if dfilter:
            if isinstance(dfilter, list):
                if len(dfilter) == 2 and dfilter[0] and \
                   (dfilter[0].shuffle or dfilter[0].name == "shuffle"
                        or dfilter[0].filterid == 4) \
                        and not dfilter[0].rate:
                    dfilter = dfilter[1]
                    dfilter.shuffle = True
                elif len(dfilter) == 1:
                    dfilter = dfilter[0]
                else:
                    raise Exception("Filter pipes not supported by h5py. "
                                    "Please change to h5cpp")
            if dfilter.filterid == 1 or dfilter.name == "deflate" or \
               dfilter.rate:
                if dfilter.options and dfilter.options[0]:
                    dfilter.rate = dfilter.options[0]
                f = H5PYField(
                    self._h5object.create_dataset(
                        name, shape, type_code,
                        chunks=(tuple(chunk)
                                if chunk is not None else None),
                        compression="gzip",
                        compression_opts=(
                            dfilter.options[0]
                            if dfilter.options
                            else dfilter.rate),
                        shuffle=dfilter.shuffle, maxshape=mshape
                    ),
                    self)
            elif dfilter.filterid == 0 or dfilter.name == 'shuffle':
                f = H5PYField(
                    self._h5object.create_dataset(
                        name, shape, type_code,
                        chunks=(tuple(chunk)
                                if chunk is not None else None),
                        shuffle=True, maxshape=mshape
                    ),
                    self)
            elif dfilter.filterid > 0 or dfilter.name:
                f = H5PYField(
                    self._h5object.create_dataset(
                        name, shape, type_code,
                        chunks=(tuple(chunk)
                                if chunk is not None else None),
                        compression=(dfilter.filterid or dfilter.name),
                        compression_opts=tuple(dfilter.options),
                        shuffle=dfilter.shuffle, maxshape=mshape
                    ),
                    self)
        if not f:
            f = H5PYField(
                self._h5object.create_dataset(
                    name, shape, type_code,
                    chunks=(tuple(chunk)
                            if chunk is not None else None),
                    maxshape=mshape
                ),
                self)
        return f

    @property
    def attributes(self):
        """ return the attribute manager

        :returns: attribute manager
        :rtype: :class:`H5PYAttributeManager`
        """
        return H5PYAttributeManager(self._h5object.attrs, self)

    @property
    def size(self):
        """ group size

        :returns: group size
        :rtype: :obj:`int`
        """
        return len(list(self._h5object.keys()))

    def exists(self, name):
        """ if child exists

        :param name: child name
        :type name: :obj:`str`
        :returns: existing flag
        :rtype: :obj:`bool`
        """
        return name in self._h5object.keys()

    def names(self):
        """ read the child names

        :returns: h5 object
        :rtype: :obj:`list` <`str`>
        """
        return list(self._h5object.keys())

    @property
    def is_valid(self):
        """ check if group is valid

        :returns: valid flag
        :rtype: :obj:`bool`
        """
        try:
            return self._h5object.name is not None
        except Exception:
            return False

    def reopen(self):
        """ reopen file
        """
        if isinstance(self._tparent, H5PYFile):
            self._h5object = self._tparent.h5object
        else:
            self._h5object = self._tparent.h5object.get(self.name)
        filewriter.FTGroup.reopen(self)


class H5PYField(filewriter.FTField):

    """ file writer field
    """

    def __init__(self, h5object, tparent=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param tparent: tree parent
        :type tparent: :obj:`FTObject`
        """
        filewriter.FTField.__init__(self, h5object, tparent)
        self.path = ''
        self.name = None
        if hasattr(h5object, "name"):
            name = h5object.name
            self.name = name.split("/")[-1]
            if tparent and tparent.path:
                if tparent.path == "/":
                    self.path = "/" + self.name
                else:
                    self.path = tparent.path + "/" + self.name

    @property
    def attributes(self):
        """ return the attribute manager

        :returns: attribute manager
        :rtype: :class:`H5PYAttributeManager`
        """
        return H5PYAttributeManager(self._h5object.attrs, self)

    def reopen(self):
        """ reopen field
        """
        self._h5object = self._tparent.h5object.get(self.name)
        filewriter.FTField.reopen(self)

    def refresh(self):
        """ refresh the field

        :returns: refreshed
        :rtype: :obj:`bool`
        """
        if hasattr(self._h5object, "id"):
            if hasattr(self._h5object.id, "refresh"):
                self._h5object.id.refresh()
                return True
        return False

    def grow(self, dim=0, ext=1):
        """ grow the field

        :param dim: growing dimension
        :type dim: :obj:`int`
        :param dim: size of the grow
        :type dim: :obj:`int`
        """
        shape = list(self._h5object.shape)
        if shape:
            shape[dim] += ext
            return self._h5object.resize(shape)
        else:
            return self._h5object

    def read(self):
        """ read the field value

        :returns: h5 object
        :rtype: :obj:`any`
        """
        fl = self._h5object[...]
        if hasattr(fl, "decode") and not isinstance(fl, unicode):
            fl = fl.decode(encoding="utf-8")
        if is_strings_as_bytes() and hasattr(fl, "astype") and \
           self.dtype in ['string', b'string']:
            try:
                fl = fl.astype('str')
            except Exception:
                # print(str(e))
                pass
        return fl

    def write(self, o):
        """ write the field value

        :param o: h5 object
        :type o: :obj:`any`
        """
        self._h5object[...] = o

    def __setitem__(self, t, o):
        """ set value

        :param t: slice tuple
        :type t: :obj:`tuple`
        :param o: h5 object
        :type o: :obj:`any`
        """
        if isinstance(o, np.ndarray):
            hsh = self._h5object.shape
            if t is Ellipsis:
                tsz = [i for i in range(len(hsh))]
            elif isinstance(t, slice):
                tsz = [i for i in range(len(hsh))]
            else:
                tsz = [i for (i, s) in enumerate(t) if isinstance(s, slice)]
            osz = len(o.shape)
            if len(tsz) > osz and len(hsh) > max(tsz):
                shape = tuple([hsh[e] for e in tsz])
                o = o.reshape(shape)
        return self._h5object.__setitem__(t, o)

    def __getitem__(self, t):
        """ get value

        :param t: slice tuple
        :type t: :obj:`tuple`
        :returns: h5 object
        :rtype: :obj:`any`
        """
        fl = self._h5object.__getitem__(t)
        if hasattr(fl, "decode") and not isinstance(fl, unicode):
            fl = fl.decode(encoding="utf-8")
        if is_strings_as_bytes() and hasattr(fl, "astype") and \
           self.dtype in ['string', b'string']:
            try:
                fl = fl.astype('str')
            except Exception:
                # print(str(e))
                pass
        return fl

    @property
    def is_valid(self):
        """ check if group is valid

        :returns: valid flag
        :rtype: :obj:`bool`
        """
        try:
            return self._h5object.name is not None
        except Exception:
            return False

    def close(self):
        """ close field
        """
        filewriter.FTField.close(self)
        self._h5object = None

    @property
    def dtype(self):
        """ field data type

        :returns: field data type
        :rtype: :obj:`str`
        """

        if self._h5object.dtype.kind == 'O':
            return "string"

        return str(self._h5object.dtype)

    @property
    def shape(self):
        """ field shape

        :returns: field shape
        :rtype: :obj:`list` < :obj:`int` >
        """
        return self._h5object.shape

    @property
    def size(self):
        """ field size

        :returns: field size
        :rtype: :obj:`int`
        """
        return self._h5object.size


class H5PYLink(filewriter.FTLink):

    """ file tree link
    """

    def __init__(self, h5object, tparent=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param tparent: tree parent
        :type tparent: :obj:`FTObject`
        """
        filewriter.FTLink.__init__(self, h5object, tparent)
        self.path = ''
        self.name = None
        if tparent and tparent.path:
            self.path = tparent.path
        if not self.path.endswith("/"):
            self.path += "/"

    def setname(self, name):
        self.name = name
        self.path += self.name
        return self

    @property
    def is_valid(self):
        """ check if link is valid

        :returns: valid flag
        :rtype: :obj:`bool`
        """
        try:
            obj = self._h5object
            if obj is None:
                raise Exception("Empty object")

            self.parent.h5object[self.name]
            return True
        except Exception:
            return False

    def refresh(self):
        """ refresh the field

        :returns: refreshed
        :rtype: :obj:`bool`
        """
        if hasattr(self._h5object, "id"):
            if hasattr(self._h5object.id, "refresh"):
                self._h5object.id.refresh()
                return True
        return False

    def read(self):
        """ read object value

        :returns: valid flag
        :rtype: :obj:`bool`
        """
        fl = self.parent.h5object[self.name][...]
        if hasattr(fl, "decode") and not isinstance(fl, unicode):
            return fl.decode(encoding="utf-8")
        else:
            return fl

    @classmethod
    def getfilename(cls, obj):
        """ provides a filename from h5 node

        :param obj: h5 node
        :type obj: :class:`FTObject`
        :returns: file name
        :rtype: :obj:`str`
        """
        filename = ""
        while not filename:
            par = obj.parent
            if par is None:
                break
            if isinstance(par, H5PYFile):
                filename = par.name
                break
            else:
                obj = par
        return filename

    @property
    def target_path(self):
        """ target path

        :returns: target path
        :rtype: :obj:`str`
        """
        filename = self.getfilename(self)
        try:
            path = self.h5object.path
        except Exception:
            path = self.path

        if filename and ":/" not in path:
            path = "/".join([gr.split(":")[0] for gr in path.split("/")])
            path = filename + ":/" + path
        return path

    def reopen(self):
        """ reopen field
        """
        self._h5object = self._tparent.h5object.get(self.name, getlink=True)
        filewriter.FTLink.reopen(self)

    def close(self):
        """ close group
        """
        filewriter.FTLink.close(self)
        self._h5object = None


class H5PYDataFilter(filewriter.FTDataFilter):

    """ file tree data filter
    """


class H5PYVirtualFieldLayout(filewriter.FTVirtualFieldLayout):

    """ virtual field layout """

    def __init__(self, h5object, shape, dtype=None, tparent=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param shape: shape
        :type shape: :obj:`list` < :obj:`int` >
        """
        filewriter.FTVirtualFieldLayout.__init__(self, h5object, tparent)
        #: (:obj:`str`): data type
        self.dtype = dtype
        #: (:obj:`list`<:obj:`dict`>) list of virtual map description
        self.__vmaps = []

    @property
    def shape(self):
        return list(self._h5object.shape)

    @shape.setter
    def shape(self, shape):
        if isinstance(shape, int):
            self._h5object.shape = tuple(shape,)
        else:
            self._h5object.shape = tuple(shape)

    @classmethod
    def cure_keys(cls, key):
        """ cure keys

        :param key: field key
        :type key: :class:`FTHyperslab` or :obj:`tuple` or :obj:`list`
        :          or :obj:`int`
        :returns: field key
        :rtype: :class:`FTHyperslab` or :obj:`tuple`
        """
        tkey = []
        if isinstance(key, list):
            try:
                sk = list(set([len(ky) for ky in key]))
            except Exception:
                sk = []
            if len(sk) == 1 and sk[0] == 4:
                offset, block, count, stride = map(list, zip(*key))
                return filewriter.FTHyperslab(offset, block, count, stride)
            for ky in key:
                if isinstance(ky, list) and len(ky) > 0 and len(ky) < 4:
                    tkey.append(slice(*ky))
                else:
                    if ky is None:
                        ky = slice(None)
                    tkey.append(ky)

            return tuple(tkey)
        return key

    @classmethod
    def cure_shape(cls, vmaps, shape):
        """ cure shape from virtual map elements

        :param vmaps: list of virtual map description
        :type vmaps: :obj:`list`<:obj:`dict`>
        :param shape: field shape
        :type shape: :obj:`list` < :obj:`int` >
        :returns: field shape
        :rtype: :obj:`list` < :obj:`int` >
        """
        # print("vmaps", vmaps, shape)
        if shape is None:
            return shape
        sizes = [(sh if sh > 1 else 0) for sh in shape]
        for vmap in vmaps:
            if "key" in vmap:
                key = vmap["key"]
                try:
                    sk = list(set([len(ky) for ky in key]))
                except Exception:
                    sk = []
                if len(sk) == 1 and sk[0] == 4:
                    offset, block, count, stride = map(list, zip(*key))
                    for si, sh in enumerate(shape):
                        if sh < 2:
                            if block[si] != unlimited() \
                                    and count[si] != unlimited() \
                                    and count[si] and block[si] and stride[si]:
                                sizes[si] = max(
                                    sizes[si],
                                    offset[si] + stride[si] * [count[si] - 1]
                                    + block[si])
                            else:
                                sizes[si] = max(
                                    sizes[si], 1)
                else:
                    eshape = vmap["shape"] if "shape" in vmap else []

                    for si, sh in enumerate(shape):
                        if sh < 2:
                            if isinstance(key, list) and len(key) > si \
                                    and isinstance(key[si], list) \
                                    and len(key[si]) > 0 and len(key[si]) < 4:
                                sky = slice(*key[si])
                                if sky.stop != unlimited():
                                    start = sky.start or 0
                                    stop = sky.stop or 0
                                    step = sky.step or 1
                                    size = (step * ((stop - start - 1) // step)
                                            + start) + 1
                                    sizes[si] = max(sizes[si], size)
                                else:
                                    if si:
                                        sizes[si] = max(
                                            sizes[si],
                                            eshape[si]
                                            if len(eshape) > si else 1, 1)
                                    else:
                                        sizes[si] += max(
                                            eshape[si]
                                            if len(eshape) > si else 1, 1)
                            else:
                                if si:
                                    sizes[si] = max(
                                        sizes[si],
                                        eshape[si]
                                        if len(eshape) > si else 1, 1)
                                else:
                                    sizes[si] += max(
                                        eshape[si]
                                        if len(eshape) > si else 1, 1)
            else:
                eshape = vmap["shape"] if "shape" in vmap else []
                for si, sh in enumerate(shape):
                    if sh < 2:
                        if si:
                            sizes[si] = max(
                                sizes[si],
                                eshape[si] if len(eshape) > si else 1, 1)
                        else:
                            sizes[si] += max(
                                eshape[si] if len(eshape) > si else 1, 1)
        return sizes

    def process_target_field_views(self, parent=None):
        """ process target fields views to virtual field layout

        :param parent: parent object
        :type parent: :class:`FTObject`
        """
        if self.__vmaps is not None:
            self.shape = self.cure_shape(self.__vmaps, self.shape)
        counter = 0
        for vmap in self.__vmaps:
            edtype = vmap["dtype"] \
                if "dtype" in vmap else self.dtype
            key = vmap["key"] if "key" in vmap else counter
            key = self.cure_keys(key)
            if "shape" in vmap:
                eshape = vmap["shape"]
            elif isinstance(key, int):
                eshape = list(self.shape)
                eshape[0] = 1
            else:
                eshape = [0] * len(self.shape)

            fieldpath = vmap["fieldpath"] \
                if "fieldpath" in vmap else "/data"
            filename = vmap["filename"] if "filename" in vmap else None
            if "target" in vmap:
                target = vmap["target"]
                if target.startswith("h5file:/"):
                    target = target[8:]
                if "::" in target:
                    filename, fieldpath = target.split("::")
                elif ":/" in target:
                    filename, fieldpath = target.split(":/")
                else:
                    fieldpath = target
            if self._tparent is None and parent is not None:
                self._tparent = parent
            obj = self._tparent
            while filename is None:
                par = obj.parent
                if par is None:
                    break
                if hasattr(par, "root") and hasattr(par, "name"):
                    filename = par.name
                    break
                else:
                    obj = par
            sourceshape = vmap["sourceshape"] \
                if "sourceshape" in vmap else None
            sourcekey = vmap["sourcekey"] \
                if "sourcekey" in vmap else None
            sourcekey = self.cure_keys(sourcekey)
            if not any(eshape):
                eshape = self.find_shape(key, eshape, change_unlimited=False)
            ef = target_field_view(
                filename, fieldpath, eshape, edtype)
            if eshape:
                counter += eshape[0]
            else:
                counter += 1
            # print("KEY", key, sourcekey, sourceshape, eshape)
            self.add(key, ef, sourcekey, sourceshape)

    @classmethod
    def find_shape(cls, key, eshape=None, change_unlimited=True):
        """ find a layout shape from elemnt keys and shape
        :param key: field key
        :type key: :class:`FTHyperslab` o :obj:`tuple`
        :param eshape: element shape
        :type eshape: ::obj:`list`
        :param change_unlimited: change_unlimited flag
        :type change_unlimited: ::obj:`bool`
        :returns: layout shape
        :rtype: :obj:`list` < :obj:`int` >
        """

        if isinstance(key, filewriter.FTHyperslab):
            if not change_unlimited:
                count = [(ct if ct != unlimited() else 1) for ct in key.count]
                block = [(ct if ct != unlimited() else 1) for ct in key.block]
            else:
                count = key.count
                block = key.block
            eshape = [bl * count[hi] for hi, bl in enumerate(block)]
        if isinstance(key, tuple):
            eshape = []
            for ky in key:
                if not change_unlimited and ky.stop == unlimited():
                    eshape.append(1)
                elif isinstance(ky, slice) and ky.stop > 0:
                    start = ky.start if ky.start is not None else 0
                    step = ky.step if ky.step is not None else 1
                    eshape.append((ky.stop - start) // step)
                else:
                    eshape.append(1)
        return eshape

    def __len__(self):
        """ provides virtual map list length

        :rtype: :obj:`int`
        :returns:  virtual map list length
        """
        return (len(self.__vmaps))

    def append_vmap(self, vmap, strategy=None):
        """ appends virtual map description into vmap list

        :param vmap: virtual map description
        :type vmap: :obj:`dict`
        :param strategy: datasource strategy i.e. INIT or FINAL
        :type strategy: :obj:`str`
        """
        self.__vmaps.append(vmap)

    def __setitem__(self, key, source):
        """ add target field to layout

        :param key: slide
        :type key: :obj:`tuple`
        :param source: target field view
        :type source: :class:`H5PYTargetFieldView`
        """
        #: (:obj:`list` < :obj:`int` >) shape
        self._h5object.__setitem__(key, source._h5object)

    def add(self, key, source, sourcekey=None, shape=None):
        """ add target field to layout

        :param key: slide
        :type key: :obj:`tuple`
        :param source: target field view
        :type source: :class:`H5PYTargetFieldView`
        :param sourcekey: slide or selection
        :type sourcekey: :obj:`tuple`
        :param shape: target shape in the layout
        :type shape: :obj:`tuple`
        """
        if shape is None:
            shape = list(source.shape or [])
            if hasattr(key, "__len__"):
                size = len(key)
                while len(shape) < size:
                    shape.insert(0, 1)
        # # if is_mbs_supported():
        #     key = _slice2selection(key, tuple(shape))
        # else:
        key = _selection2slice(key, tuple(shape))
        if sourcekey is not None and sourcekey != filewriter.FTHyperslab():
            if is_mbs_supported():
                sourcekey = _slice2selection(sourcekey, source.shape)
            else:
                sourcekey = _selection2slice(sourcekey, source.shape)
            self._h5object.__setitem__(key, source._h5object[sourcekey])
        elif key is not None and not isinstance(key, int):
            try:
                usel = unlimited_selection(key, shape)
            except Exception:
                usel = None
            if usel is not None:
                self._h5object[key] = source._h5object[usel]
            else:
                self._h5object.__setitem__(key, source._h5object)
        else:
            self._h5object.__setitem__(key, source._h5object)


class H5PYTargetFieldView(filewriter.FTTargetFieldView):

    """ target field view for VDS """

    def __init__(self, h5object, shape):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param shape: shape
        :type shape: :obj:`list` < :obj:`int` >
        """
        filewriter.FTTargetFieldView.__init__(self, h5object)
        #: (:obj:`list` < :obj:`int` >) shape
        self.shape = shape


class H5PYDeflate(H5PYDataFilter):
    pass


class H5PYAttributeManager(filewriter.FTAttributeManager):

    """ file tree attribute
    """

    def __init__(self, h5object, tparent=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param tparent: tree parent
        :type tparent: :obj:`FTObject`
        """
        filewriter.FTAttributeManager.__init__(self, h5object, tparent)
        #: (:obj:`str`) object nexus path
        self.path = ''
        #: (:obj:`str`) object name
        self.name = None
        if hasattr(h5object, "name"):
            self.path = h5object.name
            self.name = self.path.split("/")[-1]

    def create(self, name, dtype, shape=None, overwrite=False):
        """ create a new attribute

        :param name: attribute name
        :type name: :obj:`str`
        :param dtype: attribute type
        :type dtype: :obj:`str`
        :param shape: attribute shape
        :type shape: :obj:`list` < :obj:`int` >
        :param overwrite: overwrite flag
        :type overwrite: :obj:`bool`
        :returns: attribute object
        :rtype: :class:`H5PYAtribute`
        """

        if not overwrite and name in self.h5object.keys():
            raise Exception("Attribute %s exists" % name)

        shape = shape or []
        if shape:
            if isinstance(shape, list):
                shape = tuple(shape)
            if dtype in ['string', b'string']:
                dtype = h5py.special_dtype(vlen=unicode)
                if is_strings_as_bytes():
                    etype = 'str'
                else:
                    etype = dtype
                self._h5object.create(
                    name, np.empty(shape, dtype=etype),
                    shape=shape, dtype=nptype(dtype))
            else:
                self._h5object.create(
                    name, np.zeros(shape, dtype=dtype),
                    shape, dtype)
        else:
            if dtype in ['string', b'string']:
                dtype = h5py.special_dtype(vlen=unicode)
                self._h5object.create(
                    name, np.array(u"", dtype=dtype),
                    dtype=dtype)
            else:
                self._h5object.create(
                    name, np.array(0, dtype=dtype), (1,), dtype)
        at = H5PYAttribute((self._h5object, name), self.parent)
        return at

    def __len__(self):
        """ number of attributes

        :returns: number of attributes
        :rtype: :obj:`int`
        """
        return len(list(self._h5object.keys()))

    class H5PYAttrIter(object):

        def __init__(self, manager):
            """ constructor

            :param manager: attribute manager
            :type manager: :obj:`H5PYAttributeManager`
            """

            self.__manager = manager
            self.__iter = self.__manager._h5object.__iter__()

        def __next__(self):
            """ the next attribute

            :returns: attribute object
            :rtype: :class:`FTAtribute`
            """
            name = next(self.__iter)
            if name is None:
                return None
            return H5PYAttribute((self.__manager._h5object, name),
                                 self.__manager.parent)

        next = __next__

        def __iter__(self):
            """ attribute iterator

            :returns: attribute iterator
            :rtype: :class:`H5PYAttrIter`
            """
            return self

    def __iter__(self):
        """ attribute iterator

        :returns: attribute iterator
        :rtype: :class:`H5PYAttrIter`
        """
        return self.H5PYAttrIter(self)

    def __getitem__(self, name):
        """ get value

        :param name: attribute name
        :type name: :obj:`str`
        :returns: attribute object
        :rtype: :class:`FTAtribute`
        """
        return H5PYAttribute((self._h5object, name), self.parent)

    def names(self):
        """ key values

        :returns: attribute names
        :rtype: :obj:`list` <:obj:`str`>
        """
        return self._h5object.keys()

    def reopen(self):
        """ reopen field
        """
        self._h5object = self._tparent.h5object.attrs
        filewriter.FTAttributeManager.reopen(self)

    def close(self):
        """ close attribure manager
        """
        filewriter.FTAttributeManager.close(self)

    @property
    def is_valid(self):
        """ check if link is valid

        :returns: valid flag
        :rtype: :obj:`bool`
        """
        return self.parent.is_valid


class H5PYAttribute(filewriter.FTAttribute):

    """ file tree attribute
    """

    def __init__(self, h5object, tparent=None):
        """ constructor

        :param h5object: h5 object
        :type h5object: :obj:`any`
        :param tparent: tree parent
        :type tparent: :obj:`FTObject`
        """
        filewriter.FTAttribute.__init__(self, h5object, tparent)
        self.name = h5object[1]

        self.path = tparent.path
        self.path += "@%s" % self.name

    def read(self):
        """ read attribute value

        :returns: python object
        :rtype: :obj:`any`
        """
        at = self._h5object[0][self.name]
        if hasattr(at, "decode") and not isinstance(at, unicode):
            return at.decode(encoding="utf-8")
        else:
            return at

    def write(self, o):
        """ write attribute value

        :param o: python object
        :type o: :obj:`any`
        """
        if self.dtype in ['string', b'string']:
            if isinstance(o, str):
                self._h5object[0][self.name] = unicode(o)
            else:
                dtype = h5py.special_dtype(vlen=unicode)
                self._h5object[0][self.name] = np.array(o, dtype=dtype)
        else:
            self._h5object[0][self.name] = np.array(o, dtype=self.dtype)

    def __setitem__(self, t, o):
        """ write attribute value

        :param t: slice tuple
        :type t: :obj:`tuple`
        :param o: python object
        :type o: :obj:`any`
        """
        if t is Ellipsis or t == slice(None, None, None) or \
           t == (slice(None, None, None), slice(None, None, None)) or \
           (hasattr(o, "__len__") and t == slice(0, len(o), None)):
            if self.dtype in ['string', b'string']:
                if isinstance(o, str):
                    self._h5object[0][self.name] = unicode(o)
                else:
                    dtype = h5py.special_dtype(vlen=unicode)
                    self._h5object[0][self.name] = np.array(o, dtype=dtype)
            else:
                self._h5object[0][self.name] = np.array(o, dtype=self.dtype)
        elif isinstance(t, slice):
            var = self._h5object[0][self.name]
            if self.dtype not in ['string', b'string']:
                var[t] = np.array(o, dtype=self.dtype)
            else:
                dtype = h5py.special_dtype(vlen=unicode)
                var[t] = np.array(o, dtype=dtype)
                var = var.astype(dtype)
            try:
                self._h5object[0][self.name] = var
            except Exception:
                dtype = h5py.special_dtype(vlen=unicode)
                tvar = np.array(var, dtype=dtype)
                self._h5object[0][self.name] = tvar

        elif isinstance(t, tuple):
            var = self._h5object[0][self.name]
            if self.dtype not in ['string', b'string']:
                var[t] = np.array(o, dtype=self.dtype)
            else:
                dtype = h5py.special_dtype(vlen=unicode)
                if hasattr(var, "flatten"):
                    vv = var.flatten().tolist() + \
                        np.array(o, dtype=dtype).flatten().tolist()
                    nt = np.array(vv, dtype=dtype)
                    var = np.array(var, dtype=nt.dtype)
                    var[t] = np.array(o, dtype=dtype)
                elif hasattr(var, "tolist"):
                    var = var.tolist()
                    var[t] = np.array(o, dtype=self.dtype).tolist()
                else:
                    var[t] = np.array(o, dtype=self.dtype).tolist()
                var = var.astype(dtype)
            self._h5object[0][self.name] = var
        else:
            if isinstance(o, str) or isinstance(o, unicode):
                self._h5object[0][self.name] = unicode(o)
            else:
                self._h5object[0][self.name] = np.array(o, dtype=self.dtype)

    def __getitem__(self, t):
        """ read attribute value

        :param t: slice tuple
        :type t: :obj:`tuple`
        :returns: python object
        :rtype: :obj:`any`
        """
        if not isinstance(t, int):
            if t is Ellipsis:
                at = self._h5object[0][self.name]
            else:
                at = self._h5object[0][self.name][t]
        else:
            at = self._h5object[0][self.name].__getitem__(t)
        if hasattr(at, "decode") and not isinstance(at, unicode):
            return at.decode(encoding="utf-8")
        else:
            return at

    @property
    def is_valid(self):
        """ check if field is valid

        :returns: valid flag
        :rtype: :obj:`bool`
        """
        try:
            return self.name in self._h5object[0].keys()
        except Exception:
            return False

    @property
    def dtype(self):
        """ attribute data type

        :returns: attribute data type
        :rtype: :obj:`str`
        """
        dt = type(self._h5object[0][self.name]).__name__
        if dt == "ndarray":
            dt = str(self._h5object[0][self.name].dtype)
        if dt.endswith("_"):
            dt = dt[:-1]
        if dt == "bytes":
            dt = "string"
        if dt == "unicode":
            dt = "string"
        if dt == "str":
            dt = "string"
        if dt == "object":
            dt = "string"
        if dt.startswith("|S"):
            dt = "string"
        return dt

    @property
    def shape(self):
        """ attribute shape

        :returns: attribute shape
        :rtype: :obj:`list` < :obj:`int` >
        """
        if hasattr(self._h5object[0][self.name], "shape"):
            return self._h5object[0][self.name].shape
        else:
            return ()

    def reopen(self):
        """ reopen attribute
        """
        self._h5object = (self._tparent.h5object.attrs, self.name)
        filewriter.FTAttribute.reopen(self)

    def close(self):
        """ close attribute
        """
        filewriter.FTAttribute.close(self)
        self._h5object = None
