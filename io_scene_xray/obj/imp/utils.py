import os.path

import bpy

from ... import version_utils, log, context


class ImportObjectMeshContext(context.ImportMeshContext):
    def __init__(self):
        context.ImportMeshContext.__init__(self)
        self.soc_sgroups = None
        self.split_by_materials = None
        self.objects_folder = None

    def before_import_file(self):
        self.loaded_materials = {}

    def image(self, relpath):
        relpath = relpath.lower().replace('\\', os.path.sep)
        if not self.textures_folder:
            result = bpy.data.images.new(os.path.basename(relpath), 0, 0)
            result.source = 'FILE'
            result.filepath = relpath + '.dds'
            return result

        filepath = os.path.abspath(
            os.path.join(self.textures_folder, relpath + '.dds')
        )
        result = None
        for i in bpy.data.images:
            if bpy.path.abspath(i.filepath) == filepath:
                result = i
                break
        if result is None:
            try:
                result = bpy.data.images.load(filepath)
            except RuntimeError as ex:  # e.g. 'Error: Cannot read ...'
                log.warn(ex)
                result = bpy.data.images.new(os.path.basename(relpath), 0, 0)
                result.source = 'FILE'
                result.filepath = filepath
        return result


class ImportObjectAnimationContext(context.ImportAnimationContext):
    def __init__(self):
        context.ImportAnimationContext.__init__(self)


class ImportObjectContext(
        ImportObjectMeshContext, ImportObjectAnimationContext
    ):
    def __init__(self):
        ImportObjectMeshContext.__init__(self)
        ImportObjectAnimationContext.__init__(self)
