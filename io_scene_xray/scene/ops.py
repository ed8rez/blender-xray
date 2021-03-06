import bpy
from bpy_extras import io_utils

from .. import utils, plugin
from ..utils import AppError
from .. import plugin_prefs
from ..obj.imp import props as obj_imp_props
from .imp import import_file
from ..version_utils import get_import_export_menus, assign_props, IS_28


filename_ext = '.level'
op_export_level_scene_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext, options={'HIDDEN'}
    ),
}


class OpExportLevelScene(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = 'xray_export.scene'
    bl_label = 'Export .level'

    filename_ext = '.level'

    if not IS_28:
        for prop_name, prop_value in op_export_level_scene_props.items():
            exec('{0} = op_export_level_scene_props.get("{0}")'.format(prop_name))

    @utils.set_cursor_state
    def execute(self, context):

        try:
            self.export(self.objs, context)
        except utils.AppError as err:
            self.report({'ERROR'}, str(err))
            return {'CANCELLED'}

        return {'FINISHED'}

    def export(self, bpy_objs, context):

        from .exp import export_file

        export_file(bpy_objs, self.filepath)

    def invoke(self, context, event):

        self.objs = context.selected_objects

        if not self.objs:
            self.report({'ERROR'}, 'Cannot find selected object')
            return {'CANCELLED'}

        return super().invoke(context, event)


filename_ext = '.level'
op_import_level_scene_props = {
    'filepath': bpy.props.StringProperty(subtype="FILE_PATH"),
    'filter_glob': bpy.props.StringProperty(
        default='*'+filename_ext, options={'HIDDEN'}
    ),
    'mesh_split_by_materials': obj_imp_props.PropObjectMeshSplitByMaterials(),
    'shaped_bones': obj_imp_props.PropObjectBonesCustomShapes(),
    'fmt_version': plugin_prefs.PropSDKVersion()
}


class OpImportLevelScene(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = 'xray_import.scene'
    bl_label = 'Import .level'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    filename_ext = '.level'

    if not IS_28:
        for prop_name, prop_value in op_import_level_scene_props.items():
            exec('{0} = op_import_level_scene_props.get("{0}")'.format(prop_name))

    def draw(self, _context):
        layout = self.layout

        row = layout.split()
        row.label(text='Format Version:')
        row.row().prop(self, 'fmt_version', expand=True)

        layout.prop(self, 'mesh_split_by_materials')

    @utils.execute_with_logger
    @utils.set_cursor_state
    def execute(self, context):
        try:
            import_file(self.filepath, self)
        except AppError as ex:
            self.report({'ERROR'}, str(ex))
            return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        prefs = plugin_prefs.get_preferences()
        self.mesh_split_by_materials = prefs.object_mesh_split_by_mat
        self.shaped_bones = prefs.object_bones_custom_shapes
        self.fmt_version = prefs.sdk_version
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


assign_props([
    (op_export_level_scene_props, OpExportLevelScene),
    (op_import_level_scene_props, OpImportLevelScene)
])


def menu_func_export(self, context):
    icon = plugin.get_stalker_icon()
    self.layout.operator(
        OpExportLevelScene.bl_idname,
        text='X-Ray scene selection (.level)',
        icon_value=icon
    )


def menu_func_import(self, context):
    icon = plugin.get_stalker_icon()
    self.layout.operator(
        OpImportLevelScene.bl_idname,
        text='X-Ray scene selection (.level)',
        icon_value=icon
    )


def register_operators():
    bpy.utils.register_class(OpExportLevelScene)
    bpy.utils.register_class(OpImportLevelScene)


def unregister_operators():
    import_menu, export_menu = get_import_export_menus()
    export_menu.remove(menu_func_export)
    import_menu.remove(menu_func_import)
    bpy.utils.unregister_class(OpExportLevelScene)
    bpy.utils.unregister_class(OpImportLevelScene)
