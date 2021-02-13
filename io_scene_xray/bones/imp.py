# blender modules
import bpy

# addon modules
from .. import utils, xray_io, log
from ..obj import fmt
from ..obj.imp import bone as imp_bone
from ..obj.imp.main import read_v3f


@log.with_context(name='bones-partitions')
def _import_partitions(data, arm_obj, bpy_bones):
    packed_reader = xray_io.PackedReader(data)
    partitions_count = packed_reader.int()
    current_mode = arm_obj.mode
    bpy.ops.object.mode_set(mode='POSE')
    try:
        for partition_id in range(partitions_count):
            partition_name = packed_reader.gets()
            bone_group = arm_obj.pose.bone_groups.get(partition_name, None)
            if not bone_group:
                bpy.ops.pose.group_add()
                bone_group = arm_obj.pose.bone_groups.active
                bone_group.name = partition_name
            bones_count = packed_reader.int()
            for bone_id in range(bones_count):
                bone_name = packed_reader.gets()
                bpy_bone = bpy_bones.get(bone_name, None)
                if not bpy_bone:
                    log.warn(
                        'partition "{}" contains missing bone'.format(
                            partition_name
                        ),
                        bone=bone_name
                    )
                else:
                    arm_obj.pose.bones[bone_name].bone_group = bone_group
    finally:
        bpy.ops.object.mode_set(mode=current_mode)


@log.with_context(name='bone')
def _import_bone_data(data, arm_obj_name, bpy_bones, bone_index):
    chunked_reader = xray_io.ChunkedReader(data)
    chunks = fmt.Chunks.Bone
    # bone name
    packed_reader = xray_io.PackedReader(chunked_reader.next(chunks.DEF))
    name = packed_reader.gets().lower()
    log.update(name=name)
    bpy_bone = bpy_bones.get(name, None)
    if not bpy_bone:
        log.warn(
            'Armature object "{}" has no bone'.format(arm_obj_name),
            bone=name
        )
        return
    xray = bpy_bone.xray
    for chunk_id, chunk_data in chunked_reader:
        packed_reader = xray_io.PackedReader(chunk_data)
        if chunk_id == chunks.MATERIAL:
            xray.gamemtl = packed_reader.gets()
        elif chunk_id == chunks.SHAPE:
            shape_type = packed_reader.getf('H')[0]
            imp_bone._safe_assign_enum_property(
                xray.shape,
                'type',
                str(shape_type),
                'bone shape'
            )
            xray.shape.flags = packed_reader.getf('H')[0]
            xray.shape.box_rot = packed_reader.getf('fffffffff')
            xray.shape.box_trn = packed_reader.getf('fff')
            xray.shape.box_hsz = packed_reader.getf('fff')
            xray.shape.sph_pos = packed_reader.getf('fff')
            xray.shape.sph_rad = packed_reader.getf('f')[0]
            xray.shape.cyl_pos = packed_reader.getf('fff')
            xray.shape.cyl_dir = packed_reader.getf('fff')
            xray.shape.cyl_hgh = packed_reader.getf('f')[0]
            xray.shape.cyl_rad = packed_reader.getf('f')[0]
            xray.shape.set_curver()
        elif chunk_id == chunks.IK_JOINT:
            ik = xray.ikjoint
            joint_type = str(packed_reader.int())
            imp_bone._safe_assign_enum_property(
                ik, 'type', joint_type, 'bone ikjoint'
            )
            # limit x
            ik.lim_x_min, ik.lim_x_max = packed_reader.getf('ff')
            ik.lim_x_spr, ik.lim_x_dmp = packed_reader.getf('ff')
            # limit y
            ik.lim_y_min, ik.lim_y_max = packed_reader.getf('ff')
            ik.lim_y_spr, ik.lim_y_dmp = packed_reader.getf('ff')
            # limit z
            ik.lim_z_min, ik.lim_z_max = packed_reader.getf('ff')
            ik.lim_z_spr, ik.lim_z_dmp = packed_reader.getf('ff')
            # spring and damping
            ik.spring = packed_reader.getf('f')[0]
            ik.damping = packed_reader.getf('f')[0]
        elif chunk_id == chunks.MASS_PARAMS:
            xray.mass.value = packed_reader.getf('f')[0]
            xray.mass.center = read_v3f(packed_reader)
        elif chunk_id == chunks.IK_FLAGS:
            xray.ikflags = packed_reader.int()
        elif chunk_id == chunks.BREAK_PARAMS:
            xray.breakf.force = packed_reader.getf('f')[0]
            xray.breakf.torque = packed_reader.getf('f')[0]
        elif chunk_id == chunks.FRICTION:
            xray.friction = packed_reader.getf('f')[0]
        else:
            log.debug('unknown chunk', chunk_id=chunk_id)


def _import_main(data, import_context):
    chunked_reader = xray_io.ChunkedReader(data)
    chunks = fmt.Chunks.Object
    arm_obj = import_context.bpy_arm_obj
    bpy_bones = {}
    for bpy_bone in arm_obj.data.bones:
        bpy_bones[bpy_bone.name.lower()] = bpy_bone
    for chunk_id, chunk_data in chunked_reader:
        if chunk_id == chunks.PARTITIONS1:
            if import_context.import_bone_parts:
                _import_partitions(chunk_data, arm_obj, bpy_bones)
        else:
            if not import_context.import_bone_properties:
                continue
            bone_index = chunk_id
            _import_bone_data(chunk_data, arm_obj.name, bpy_bones, bone_index)


def import_file(import_context):
    with open(import_context.filepath, 'rb') as file:
        data = file.read()
    _import_main(data, import_context)
