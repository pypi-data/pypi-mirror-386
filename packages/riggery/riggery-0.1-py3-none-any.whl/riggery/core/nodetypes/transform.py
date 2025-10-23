import re
from typing import Generator, Optional, Union, Literal

import maya.cmds as m
import maya.api.OpenMaya as om

from riggery.general.functions import short, resolve_flags
from riggery.general.iterables import expand_tuples_lists
from riggery.general.numbers import floatrange

from ..elem import Elem, ElemInstError
from ..nodetypes import __pool__ as nodes
from ..plugtypes import __pool__ as plugs
from ..datatypes import __pool__ as data
from ..lib.evaluation import cache_dg_output
from ..lib import controls as _c
from ..lib import names as _n, controlshapes as _cs
from ..lib import namespaces as _ns
from riggery.internal import str2api as _s2a


class Transform(nodes['DagNode']):

    #-----------------------------------------|    Constructor(s)

    @classmethod
    @short(name='n',
           matrix='m',
           parent='p',
           rotateOrder='ro',
           displayLocalAxis='dla',
           zeroChannels='zc',
           worldSpace='ws',
           displayHandle='dh')
    def create(cls, *,
               name:Optional[str]=None,
               matrix=None,
               parent=None,
               rotateOrder=None,
               displayLocalAxis:bool=False,
               displayHandle:bool=False,
               zeroChannels:bool=False,
               worldSpace:bool=False):
        """
        :param name/n: if omitted, defaults to Name blocks
        :param matrix/m: the initial node matrix; defaults to identity
        :param parent/p: a destination parent; defaults to None
        :param rotateOrder/ro: the initial rotate order; defaults to 'xyz'
        :param displayLocalAxis/dla: display the local transformation axes;
            defaults to False
        :param displayHandle/dh: displays a basic black crosshair; defaults to
            False
        :param zeroChannels/zc: don't apply *matrix* to SRT channels, but
            rather to 'offsetParentMatrix'; defaults to False
        :param worldSpace/ws: apply *matrix* in world-space; defaults to
            False
        :return: The transform node.
        """
        node = cls.createNode(name=name)

        if rotateOrder is not None:
            node.attr('ro').set(rotateOrder)

        if displayLocalAxis:
            node.attr('displayLocalAxis').set(True)

        if displayHandle:
            node.attr('displayHandle').set(True)

        if parent:
            node.setParent(parent)

        if matrix is None:
            matrix = data['Matrix']()
        else:
            matrix = data['Matrix'](matrix)

        node.setMatrix(matrix,
                       worldSpace=worldSpace,
                       zeroChannels=zeroChannels)

        return node

    @classmethod
    def createFromDagPath(cls, dagPath:str):
        """
        Creates, or retrieves, a group structure to match the specified the
        specified *dagPath*.

        :param dagPath: The DAG path to initialize, e.g. 'root|inner1|inner2'
        :return: The innermost (final) node.
        """
        elems = dagPath.split('|')
        num = len(elems)
        groups = []

        for i in range(num):
            theseElems = elems[:num-i]
            if theseElems == ['']:
                break
            thisPath = '|'.join(theseElems)
            try:
                thisGroup = Transform(thisPath)
            except ElemInstError:
                thisGroup = Transform(
                    m.group(empty=True, name=theseElems[-1])
                )
            groups.append(thisGroup)

        if len(groups) > 1:
            for thisGroup, nextGroup in zip(groups, groups[1:]):
                thisGroup.setParent(nextGroup)

        return groups[0]

    #-----------------------------------------|    Transformations

    @cache_dg_output
    def _getLocalRotateMatrixPlug(self):
        return self.attr('r'
                         ).asRotateMatrix(rotateOrder=self.attr('rotateOrder'))

    @cache_dg_output
    def _getWorldRotateMatrixPlug(self):
        return self._getLocalRotateMatrixPlug() \
            * self.attr('pm')[0].pick(t=False).withNormalizedAxes()

    @short(plug='p', worldSpace='ws')
    def getRotateMatrix(self, worldSpace:bool=False, plug:bool=False):
        """
        The advantage of this method is that the rotate matrix will be correct
        even if the transform's scale channels are collapsed.

        :param worldSpace/ws: return a world-space matrix; defaults to False
        :param plug/p: return an attribute rather than a value; defaults to
            False
        """
        if plug:
            if worldSpace:
                return self._getWorldRotateMatrixPlug()
            return self._getLocalRotateMatrixPlug()
        else:
            matrix = self.attr('r')().asRotateMatrix(
                rotateOrder=self.attr('rotateOrder')()
            )
            if worldSpace:
                matrix *= self.attr('pm')[0]()
            return matrix

    @short(plug='p')
    def localPosition(self, plug:bool=False):
        """
        Returns local translation ^ offset parent matrix.

        :param plug/p: return a live attribute rather than a value; defaults to
            False
        """
        if plug:
            if not self.hasAttr('_cachedLocalPosition'):
                self.addPointAttr('_cachedLocalPosition')
            attr = self.attr('_cachedLocalPosition')
            if not attr.inputs():
                attr.unlock(recurse=True)
                (self.attr('t') ^ self.attr('opm')) >> attr
                attr.lock(recurse=True)
            return attr
        return self.attr('t')() ^ self.attr('opm')()

    @short(plug='p')
    def worldPosition(self, plug:bool=False):
        """
        :param plug/p: return a live attribute rather than a value; defaults to
            False
        """
        return self.getPosition(worldSpace=True, plug=plug)

    @short(worldSpace='ws', plug='p')
    def getPosition(self, *, plug:bool=False, worldSpace:bool=False):
        """
        Returns this transform's position.

        :param plug/p: return a live output rather than a value; default to
            False
        :param worldSpace/ws: return a world-space output; defaults to False
        """
        if plug:
            if worldSpace:
                if not self.hasAttr('_cachedWorldPosition'):
                    plug = self.addPointAttr('_cachedWorldPosition')
                    inp = self.attr('t') * self.attr('pm')[0]
                    inp >> plug
                    plug.lock()
                    return plug
                plug = self.attr('_cachedWorldPosition')
                if not plug.inputs():
                    plug.unlock()
                    (self.attr('t') * self.attr('pm')[0]) >> plug
                    plug.lock()
                return plug
            return self.attr('t')

        out = self.attr('t').get()
        if worldSpace:
            out *= self.attr('pm')[0].get()
        return out

    @short(worldSpace='ws')
    def setPosition(self, position, worldSpace:bool=False):
        """
        :param position: the position values to set
        :param worldSpace/ws: apply position in world-space; defaults to False
        :return: self
        """
        m.xform(str(self), t=position, worldSpace=worldSpace, a=True)
        return self

    @short(worldSpace='ws')
    def getQuaternion(self, worldSpace:bool=False):
        """
        :param worldSpace/ws: return a world-space rotation; defaults to False
        :return: The rotation of this transform, as a quaternion.
        :rtype: :class:`~riggery.core.datatypes.quaternion.Quaternion`
        """
        mfn = om.MFnTransform(self.__apimdagpath__())
        if worldSpace:
            space = om.MSpace.kWorld
        else:
            space = om.MSpace.kTransform
        quat = mfn.rotation(space=space, asQuaternion=True)
        return data['Quaternion'](quat)

    @short(worldSpace='ws')
    def setQuaternion(self, quat, worldSpace:bool=False):
        """
        :param quat: the quaternion to use to set this transform's rotation
        :param worldSpace/ws: set the rotation in world-space; defaults to False
        :return: Self.
        """
        quat = om.MQuaternion(*quat)
        mfn = om.MFnTransform(self.__apimdagpath__())
        if worldSpace:
            space = om.MSpace.kWorld
        else:
            space = om.MSpace.kTransform
        mfn.setRotation(quat, space)
        return self

    @short(worldSpace='ws')
    def getScale(self, worldSpace:bool=False):
        """
        :param worldSpace/ws: return the scale in world space; defaults to False
        :return: The scale of this transform, as a vector.
        """
        return self.getMatrix(worldSpace=True).scale

    @short(worldSpace='ws')
    def setScale(self, scale, worldSpace:bool=False):
        """
        :param scale: the scale to set (sequence of three floats)
        :param worldSpace/ws: set the scale in world-space; defaults to False
        :return: Self
        """
        matrix = self.getMatrix(worldSpace=worldSpace)
        matrix.scale = scale
        self.setMatrix(matrix, worldSpace=worldSpace)
        return self

    @short(worldSpace='ws', plug='p')
    def getMatrix(self, *, worldSpace=False, plug=False):
        """
        :param worldSpace/ws: return a world-space matrix; defaults to False
        :param plug/p: return an attribute rather than a value; defaults to
            False
        """
        if plug:
            return self.attr('worldMatrix' if worldSpace else 'matrix')

        return data['Matrix'](m.xform(str(self),
                                      q=True,
                                      matrix=True,
                                      worldSpace=worldSpace))

    @short(translate='t',
           rotate='r',
           scale='s',
           shear='sh',
           worldSpace='ws',
           zeroChannels='zc',
           preserveChannels='pc')
    def setMatrix(self,
                  matrix, *,
                  translate=None,
                  rotate=None,
                  scale=None,
                  shear=None,
                  zeroChannels:bool=False,
                  preserveChannels:bool=False,
                  worldSpace:bool=False):
        """
        :param translate/t: edit translation (by omission)
        :param rotate/r: edit rotation (by omission)
        :param scale/s: edit scale (by omission)
        :param shear/sh: edit shear (by omission)
        :param worldSpace/ws: apply matrix in world space; defaults to False
        :param zeroChannels/zc: edit 'offsetParentMatrix', and zero-out the
            SRT channels; defaults to False
        :param preserveChannels/pc: edit 'offsetParentMatrix', and keep SRT
            channels at current values; defaults to False
        :return: self
        """
        translate, rotate, scale, shear = resolve_flags(
            translate, rotate, scale, shear
        )
        if not any([translate, rotate, scale, shear]):
            return self

        matrix = data['Matrix'](matrix)

        if not all([translate, rotate, scale, shear]):
            matrix = matrix.pick(translate=translate,
                                 rotate=rotate,
                                 scale=scale,
                                 shear=shear,
                                 default=self.getMatrix(worldSpace=False))

        if worldSpace:
            matrix *= self.attr('pim')[0].get()

        if zeroChannels:
            matrix *= self.attr('opm').get()
            self.setMatrix(data['Matrix']())
            self.attr('opm').set(matrix)
        elif preserveChannels:
            matrix *= self.attr('opm').get()
            matrix = self.attr('im').get() * matrix
            self.attr('opm').set(matrix)
        else:
            m.xform(str(self), matrix=matrix)

        return self

    def makeIdentity(self, *args, **kwargs):
        """
        Thin wrapper for :func:`maya.cmds.makeIdentity`.
        """
        m.makeIdentity(str(self), *args, **kwargs)
        return self

    @short(translate='t', rotate='r', scale='s', shear='sh')
    def resetSRT(self, translate=None, rotate=None, scale=None, shear=None):
        """
        Resets translate, rotate, scale and shear on this transform node.

        :param translate/t: reset translation
        :param rotate/r: reset translation
        :param scale/s: reset translation
        :param shear/sh: reset translation
        :return: Self.
        """
        translate, rotate, scale, shear = resolve_flags(
            translate, rotate, scale, shear
        )

        for chanName, state, defaults in zip(
                ('translate', 'rotate', 'scale', 'shear'),
                (translate, rotate, scale, shear),
                ([0, 0, 0], [0, 0, 0], [1, 1, 1], [0, 0, 0])
        ):
            if state:
                plug = self.attr(chanName)
                for child, default in zip(plug.children, defaults):
                    try:
                        child.set(default)
                    except:
                        continue

        return self

    @short(translate='t',
           rotate='r',
           scale='s',
           shear='sh',
           resetOffsetParentMatrix='rop')
    def resetMatrix(self, *,
                    translate=None,
                    rotate=None,
                    scale=None,
                    shear=None,
                    resetOffsetParentMatrix:bool=False):
        """
        Similar to ``makeIdentity(apply=False)``.

        :param translate/t: reset translation (by omission)
        :param rotate: reset rotation (by omission)
        :param scale: reset scale (by omission)
        :param shear: reset shear (by omission)
        :param resetOffsetParentMatrix/rop: set ``offsetParentMatrix`` to
            identity as well; defaults to False
        :return: self
        """
        translate, rotate, scale, shear = resolve_flags(
            translate, rotate, scale, shear
        )
        matrix = self.getMatrix().pick(translate=not translate,
                                       rotate=not rotate,
                                       scale=not scale,
                                       shear=not shear)
        m.xform(str(self), matrix=matrix)
        if resetOffsetParentMatrix:
            self.attr('opm').set(data['Matrix']())
        return self

    @classmethod
    def _guessSideFromPoint(cls, point) -> Optional[int]:
        point = data['Point'](point)
        if point[0] > 1e-8:
            return 1
        if point[0] < -1e-8:
            return -1

    @classmethod
    def _guessSideFromNameContext(cls) -> Optional[int]:
        if _n.Name.__elems__:
            side = _n.extractSide(_n.Name.__elems__[0])
            if side is not None:
                return side

        ns = _ns.Namespace.getCurrent()
        if not ns.isRoot():
            return _n.extractSide(str(ns))

    def guessSide(self, *,
                  usePosition:bool=True,
                  useName:bool=True) -> Optional[int]:
        """
        :param useName: look for ``L_`` or ``R_`` prefixes; defaults to True
        :param usePosition: look at the control's world position; defaults to
            True
        :return: 1 for left, -1 for right, otherwise None.
        """
        if useName:
            side = _n.extractSide(self.absoluteName())
            if side is not None:
                return side

        if usePosition:
            return self._guessSideFromPoint(self.worldPosition())

    #-----------------------------------------|    DAG

    def isTransform(self) -> bool:
        """
        :return: True if this is a transform node.
        """
        return True

    def toTransform(self):
        """
        :return: self
        """
        return self

    def toShape(self):
        """
        :return: This transform's first-listed shape.
        """
        return self.shape

    @short(name='n')
    def duplicate(self, *, name=None) -> list:
        """
        Thin wrapper for :func:`maya.cmds.duplicate`.

        :param name/n: an optional name for the copy; if omitted, Name blocks
            will be used
        :return: The duplicate, in a list, per PyMEL / Maya convention.
        """
        name = _n.resolveNameArg(name, typeSuffix=self.defaultTypeSuffix)
        return [nodes['DagNode'](m.duplicate(str(self), name=name)[0])]

    @short(type='typ',
           intermediate='i',
           ranked='ra')
    def iterShapes(self, *,
                   intermediate:Optional[bool]=None,
                   type=None,
                   ranked=True) -> Generator:
        """
        :param intermediate/i: if omitted, both intermediate and non-
            intermediate shapes will be returned; otherwise, if it's False,
            intermediate shapes will be omitted and, if it's True, non-
            intermediate shapes will be omitted; defaults to None
        :param type/typ: optional type filter(s); defaults to None
        :param ranked/ra: if intermediate is None, ensures that non-
            intermediate shapes are returned first; defaults to True
        """
        kwargs = {'path': True, 'shapes': True}

        intermediateOnly = nonIntermediateOnly = False

        if intermediate is not None:
            ranked = False
            if intermediate:
                intermediateOnly = True
            else:
                kwargs['noIntermediate'] = nonIntermediateOnly = True

        if type is not None:
            kwargs['type'] = type

        result = m.listRelatives(str(self), **kwargs)

        if result:
            if ranked:
                intermediate = []
                nonIntermediate = []
                for item in result:
                    if m.getAttr(f"{item}.intermediateObject"):
                        intermediate.append(item)
                    else:
                        nonIntermediate.append(item)
                result = nonIntermediate + intermediate
            elif intermediate:
                result = [item for item in result \
                          if m.getAttr(f"{item}.intermediateObject")]

            DagNode = nodes['DagNode']

            for item in result:
                yield DagNode(item)

    shapes = property(fget=iterShapes)

    def getShapes(self, **kwargs) -> list:
        """
        Flat version of :meth:`iterShapes`.
        """
        return list(self.iterShapes(**kwargs))

    @short(type='typ',
           intermediate='i',
           ranked='ra')
    def getShape(self, *,
                 intermediate:Optional[bool]=None,
                 ranked:bool=True,
                 type=None):
        """
        :param intermediate/i: if omitted, both intermediate and non-
            intermediate shapes will be returned; otherwise, if it's False,
            intermediate shapes will be omitted and, if it's True, non-
            intermediate shapes will be omitted; defaults to None
        :param ranked/ra: ensures that non-intermediate shapes are returned
            first; defaults to True
        :param type/typ: optional type filter; defaults to None
        :return: The first shape that matches the specified criteria, or None.
        """
        for x in self.iterShapes(intermediate=intermediate,
                                 ranked=ranked, type=type):
            return x

    shape = property(getShape)

    def getShapeNameTemplate(self) -> tuple[str, int]:
        """
        :return: A string that can be used to generate conformed shape names.
        """
        absName = self.absoluteName(short=True)
        mt = re.match(r"^(.*?)([0-9]+)$", absName)
        if mt:
            base, startNum = mt.groups()
            startNum = int(startNum)
            return base+'Shape{}', startNum
        return absName+'Shape{}', 0

    def conformShapeNames(self):
        """
        Fixes wonky shape names.
        :return: self
        """
        template, startNum = self.getShapeNameTemplate()
        shapes = self.getShapes(ranked=True)
        for shape in shapes:
            shape.name = '_tmpname'
        for i, shape in enumerate(shapes, start=startNum):
            shape.name = template.format(i if i else '')
        return self

    def getParent(self, index:int=1, /):
        return super().getParent(index)

    @short(addObject='add',
           relative='r')
    def setParent(self,
                  newParent, /,
                  relative=False,
                  addObject=False):
        """
        Sets this transform's parent.

        :param newParent: the parent
        :param relative/r: preserve relative transformations; defaults to
            False
        :param addObject/add: create an instance of this node rather than
            reparenting
        :return: Either ``self`` or, if *addObject* was requested, a new
            instance.
        """
        currentParent = self.parent
        if newParent is not None:
            newParent = Transform(newParent)

        sameParent = newParent == currentParent

        if sameParent and not addObject:
            return self

        args = [str(self)]
        kwargs = {}
        if newParent:
            args.append(str(newParent))
        else:
            kwargs['world'] = True

        if relative:
            kwargs['relative'] = True

        if addObject:
            kwargs['addObject'] = addObject

        result = m.parent(*args, **kwargs)[0]

        if addObject:
            return Transform(result)

        return self

    def clearParent(self):
        """
        Parents this node under the world.

        :return: self
        """
        self.setParent(None)
        return self

    parent = property(getParent, setParent, clearParent)

    def inWorld(self) -> bool:
        """
        :return: True if this transform has no parent.
        """
        return self.__apimfn__(dag=True).parent(0).apiType() == om.MFn.kWorld

    def __or__(self, other):
        args = other if isinstance(other, (list, tuple)) else [other]
        m.parent(list(map(str, args)), str(self))

    def __ror__(self, other):
        self.parent = other

    #-----------------------------------------|    Attributes

    def __getattr__(self, item):
        try:
            return self.attr(item)
        except AttributeError as exc:
            shape = self.shape
            if shape:
                return getattr(shape, item)
            raise exc

    def attr(self, attrName:str, *, checkShape:bool=True):
        """
        For parity with PyMEL, this does *not* auto-expand to element 0 on
        'multi' roots.

        :param attrName: the short or long name of the attribute
        :param checkShape: look for the attribute on the first shape under this
            transform too; defaults to ``True``
        """
        try:
            plug = _s2a.getMPlugOnNode(self.__apimobject__(),
                                       attrName,
                                       firstElem=False,
                                       checkShape=checkShape)
        except _s2a.Str2ApiNoMatchError:
            raise AttributeError(attrName)
        return plugs['Attribute'].fromMPlug(plug)

    def hasAttr(self, name:str, *, checkShape:bool=True):
        """
        :param name: the name of the attribute to look up
        :param checkShape: check on this transform's first shape too; defaults
            to True
        :return: True if the attribute can be accessed.
        """
        if super().hasAttr(name):
            return True

        if checkShape:
            shape = self.getShape()
            if shape is None:
                return False
            return shape.hasAttr(name)
        return False

    #-----------------------------------------|    Rigging

    @short(rotateOrder='ro')
    def createOffsetGroups(self, *suffixes) -> list['Transform']:
        """
        Creates offset groups for this transform node.
        :param \*suffixes: a suffix for each group; if omitted, defaults to
            'offset'
        :return: A list of the generated offset groups; the innermost (lower)
            one will be first.
        """
        rotateOrder = self.attr('rotateOrder').get()

        if suffixes:
            suffixes = expand_tuples_lists(*suffixes)
        else:
            suffixes = ['offset']

        out = []
        current = self

        base = self.shortName(stripTypeSuffix=True)
        matrix = current.getMatrix(worldSpace=True)
        out = []

        for suffix in suffixes:
            n = f"{base}_{suffix}_{Transform.__typesuffix__}"
            group = Transform.create(
                name=n,
                matrix=matrix,
                worldSpace=True,
                parent=current.getParent(),
                rotateOrder=rotateOrder
            )
            current.setParent(group)
            current = group
            out.append(group)

        return out

    @short(axisRemap='ar',
           scale='s')
    def setControlShape(self,
                        libraryKey:str,
                        color:Optional[int]=None,
                        axisRemap:Optional[list[str]]=None,
                        scale:Optional[float]=None) -> list['nodes.NurbsCurve']:
        if scale is None:
            scale = _cs.ShapeScale.__factor__

        out = list(map(nodes['DagNode'],
                       _cs.ControlShapeLibrary()[libraryKey].apply(
                           str(self),
                           applyColor=True,
                           axisRemap=axisRemap,
                           scale=scale
                       )))
        if color is not None:
            self.setControlColor(color)
        return out

    def setControlColor(self, color):
        _cs.setControlColor(color, self)
        return self

    @short(applyColor='ac',
           axisRemap='ar',
           scale='s',
           worldSpace='ws',
           worldMirrorAxis='wma')
    def copyControlShapeTo(
            self,
            *destControls,
            copyColor:bool=True,
            copyVisInput:bool=False,
            scale=None,
            worldSpace:bool=False,
            worldMirrorAxis:Optional[Literal['x', 'y', 'z']]=None
    ) -> list['nodes.NurbsCurve']:
        out =_cs.copyControlShapes(
            str(self),
            list(map(str, expand_tuples_lists(*destControls))),
            copyColor=copyColor,
            copyVisInput=copyVisInput,
            worldMirrorAxis=worldMirrorAxis,
            worldSpace=worldSpace,
            scale=scale
        )
        return list(map(nodes['DagNode'], out))

    #-----------------------------------------|    Layout utilities

    @short(translate='t',
           rotate='r',
           scale='s')
    def distribute(self,
                   *others,
                   translate:Optional[bool]=None,
                   rotate:Optional[bool]=None,
                   scale:Optional[bool]=None):
        """
        Blends transformations (non-dynamically) across transforms between this
        object and the last of \*others. Only the interceding nodes are
        transformed; the start and end nodes are mere references.

        This method will quietly do nothing if fewer than three transform nodes
        are involved, or if all transformation filters are set to False.

        :param \*others: the rest of the transforms in the span
        :param translate/t: modify translation; defaults to True
        :param rotate/r: modify rotation; defaults to True
        :param scale/s: modify scale; defaults to True
        :return: Self.
        """
        translate, rotate, scale = resolve_flags(translate, rotate, scale)
        if any((translate, rotate, scale)):
            span = [self] + list(map(Transform, expand_tuples_lists(others)))
            num = len(span)
            if num > 2:
                endXf = span[-1]
                tweenXfs = span[1:-1]
                weights = list(floatrange(0, 1, num))[1:-1]

                if translate:
                    startPoint = self.getPosition(worldSpace=True)
                    endPoint = endXf.getPosition(worldSpace=True)
                    tweenPoints = [startPoint.blend(
                        endPoint, weight) for weight in weights]

                    for xf, point in zip(tweenXfs, tweenPoints):
                        xf.setPosition(point, worldSpace=True)

                if rotate:
                    startQuat = self.getQuaternion(worldSpace=True)
                    endQuat = endXf.getQuaternion(worldSpace=True)
                    tweenQuats = [startQuat.slerp(endQuat,
                                                  weight) for weight in weights]

                    for xf, quat in zip(tweenXfs, tweenQuats):
                        xf.setQuaternion(quat, worldSpace=True)

                if scale:
                    startScale = self.getScale(worldSpace=True)
                    endScale = endXf.getScale(worldSpace=True)
                    tweenScales = [startScale.blend(
                        endScale, weight) for weight in weights]

                    for xf, scale in zip(tweenXfs, tweenScales):
                        xf.setScale(scale, worldSpace=True)

        return self

    #-----------------------------------------|    Repr

    @property
    def defaultTypeSuffix(self) -> str:
        """
        :return: The type suffix that this transform node would receive in block
        naming, based on its current shape.
        """
        if self.isControl:
            return _n.CONTROLSUFFIX

        shape = self.getShape(ranked=True)
        typeSuffix = None

        if shape:
            typeSuffix = shape.__typesuffix__

        if not typeSuffix:
            typeSuffix = self.__typesuffix__

        return typeSuffix